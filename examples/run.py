"""Run the constructed examples: python -m examples.run [--output-dir results]."""

import argparse
import inspect
import json
import platform
import random
import textwrap
import zlib

from ancd import ncd, normalize
from pathlib import Path
from typing import Callable

from examples import refactoring as r
from examples import testing as t


def source(function: Callable[..., object]) -> str:
    return textwrap.dedent(inspect.getsource(function))


def raw_ncd(left: bytes, right: bytes) -> float:
    compress = lambda value: len(zlib.compress(value, level=9))
    a, b = compress(left), compress(right)
    return (min(compress(left + right), compress(right + left)) - min(a, b)) / max(a, b)


def scores() -> dict[str, object]:
    rng = random.Random(20260923)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    padding = "".join("# " + "".join(rng.choices(alphabet, k=72)) + "\n" for _ in range(48))
    original = source(t.shipping_fee)
    padded = original + padding
    pairs = {
        "renamed_aggregation": (source(r.invoice_subtotal), source(r.shipment_weight)),
        "renamed_resource_protocol": (source(r.render_invoice), source(r.render_label)),
        "boundary_regression": (source(t.shipping_fee), source(t.shipping_fee_boundary_fault)),
        "mirrored_faulty_oracle": (source(t.shipping_fee_boundary_fault), source(t.mirrored_fee_oracle)),
        "contract_derived_oracle": (source(t.shipping_fee), source(t.contract_fee_oracle)),
        "padded_comments": (original, padded),
        "padded_oracle_comments": (source(t.fee_examples), source(t.fee_examples) + padding),
        "padded_oracle_computation": (source(t.fee_examples), source(t.fee_examples_with_irrelevant_work)),
    }
    entries: dict[str, object] = {}
    for name, (left, right) in pairs.items():
        left_source, right_source = left.encode(), right.encode()
        left_normalized, right_normalized = normalize(left), normalize(right)
        entries[name] = {
            "raw_ncd": raw_ncd(left_source, right_source),
            "normalized_ncd": ncd(left_normalized, right_normalized),
            "source_bytes": [len(left_source), len(right_source)],
            "source_compressed_bytes": [len(zlib.compress(data, level=9)) for data in (left_source, right_source)],
            "normalized_bytes": [len(left_normalized), len(right_normalized)],
            "normalized_compressed_bytes": [len(zlib.compress(data, level=9))
                                            for data in (left_normalized, right_normalized)],
        }
    return {"status": "measured", "runtime": {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
        "zlib_compile_version": zlib.ZLIB_VERSION,
        "compression_level": 9,
        "wbits": 15,
        "normalization": "ancd-single-function-ast-v1",
        "ncd_concatenation": "min(C(x+y), C(y+x))",
    }, "pairs": entries}


def refactoring_checks() -> dict[str, bool]:
    invoice_rows = [{"units": 2, "price": 7}, {"price": 99}, {"units": 0, "price": 5}]
    shipment_rows = [{"parcels": 3, "grams": 12}, {"grams": 99}]
    aggregations = (
        r.invoice_subtotal(invoice_rows) == r.invoice_subtotal_after(invoice_rows) == 14
        and r.shipment_weight(shipment_rows) == r.shipment_weight_after(shipment_rows) == 36
    )

    def error(function: Callable[..., object], rows: list[dict[str, int]]) -> tuple[type[Exception], str] | None:
        try:
            function(rows)
        except ValueError as raised:
            return type(raised), str(raised)
        return None

    validation = (
        error(r.invoice_subtotal, [{"units": -1, "price": 2}])
        == error(r.invoice_subtotal_after, [{"units": -1, "price": 2}])
        == (ValueError, "negative invoice line")
        and error(r.shipment_weight, [{"parcels": -1, "grams": 2}])
        == error(r.shipment_weight_after, [{"parcels": -1, "grams": 2}])
        == (ValueError, "negative shipment line")
    )

    def observe(function: Callable[..., str], payload: str) -> tuple[str, list[str]]:
        events: list[str] = []
        value = function(lambda: r.Resource(events), payload)
        return value, events

    protocol = (
        observe(r.render_invoice, "Ab") == observe(r.render_invoice_after, "Ab") == ("AB", ["invoice", "close"])
        and observe(r.render_label, "Ab") == observe(r.render_label_after, "Ab") == ("ab", ["label", "close"])
    )

    def failing_protocol(function: Callable[..., object]) -> list[str]:
        events: list[str] = []

        def open_resource() -> r.Resource:
            return r.Resource(events)

        def fail(resource: r.Resource) -> None:
            events.append("effect")
            raise ValueError("effect failed")

        try:
            function(open_resource, fail)
        except ValueError as raised:
            if str(raised) == "effect failed":
                return events
        return events + ["missing failure"]

    class FailingPayload:
        def upper(self) -> str:
            raise ValueError("transform failed")

        def lower(self) -> str:
            raise ValueError("transform failed")

    def observe_failure(function: Callable[..., str]) -> list[str]:
        events: list[str] = []
        try:
            function(lambda: r.Resource(events), FailingPayload())
        except ValueError as raised:
            if str(raised) == "transform failed":
                return events
        return events + ["missing failure"]

    cleanup = (failing_protocol(r.with_resource) == ["effect", "close"]
               and observe_failure(r.render_invoice) == observe_failure(r.render_invoice_after)
               == ["invoice", "close"]
               and observe_failure(r.render_label) == observe_failure(r.render_label_after)
               == ["label", "close"])
    return {"aggregation_values": aggregations, "aggregation_policy_errors": validation,
            "resource_values_and_effects": protocol, "resource_failure_cleanup": cleanup}


def mutation_results() -> dict[str, object]:
    cases = {
        "boundary_greater_or_equal": {
            "baseline": t.shipping_fee,
            "fault": t.shipping_fee_boundary_fault,
            "tests": {"independent_nonboundary_examples": t.fee_nonboundary_examples,
                "independent_boundary_examples": t.fee_examples,
                "contract_derived_oracle": t.contract_derived_fee_test},
        },
        "constant_canonicalizer": {
            "baseline": t.canonicalize,
            "fault": t.canonicalize_constant_fault,
            "tests": {"idempotence": t.canonical_idempotence, "anchored_example": t.canonical_anchor},
        },
        "missing_failure_cleanup": {
            "baseline": t.publish,
            "fault": t.publish_cleanup_fault,
            "tests": {"successful_effects": t.successful_publish_test,
                      "failure_cleanup_and_exception_identity": t.failure_cleanup_contract},
        },
    }
    matrix: dict[str, object] = {}
    for name, case in cases.items():
        baseline = case["baseline"]
        fault = case["fault"]
        tests = case["tests"]
        observations = {test_name: {"baseline_passes": check(baseline), "fault_passes": check(fault)}
                        for test_name, check in tests.items()}
        if not all(item["baseline_passes"] for item in observations.values()):
            raise AssertionError(f"Invalid baseline in {name}")
        matrix[name] = {"tests": observations, "killed": sum(not item["fault_passes"] for item in observations.values()),
                        "applicable_tests": len(observations)}
    return {
        "matrix": matrix,
        "totals": {"killed_observations": sum(item["killed"] for item in matrix.values()),
                   "applicable_observations": sum(item["applicable_tests"] for item in matrix.values()),
                   "faults_detected": sum(item["killed"] > 0 for item in matrix.values()),
                   "faults_injected": len(matrix)},
        "irrelevant_novelty": {
            name: {"original_passes": t.fee_examples(candidate),
                   "padded_passes": t.fee_examples_with_irrelevant_work(candidate)}
            for name, candidate in (("baseline", t.shipping_fee),
                                    ("boundary_fault", t.shipping_fee_boundary_fault))
        },
        "shared_fault_boundary": {
            "weight": 10,
            "faulty_implementation": t.shipping_fee_boundary_fault(10),
            "mirrored_faulty_oracle": t.mirrored_fee_oracle(10),
            "mirrored_test_accepts_fault": t.mirrored_fee_test(t.shipping_fee_boundary_fault),
            "independent_contract": 5,
        },
    }


def render_summary(result: dict[str, object]) -> str:
    checks = result["refactoring_checks"]
    mutations = result["mutations"]
    similarity = result["similarity"]
    lines = ["# Constructed examples", "", "These are illustrative fixtures, not empirical validation of NCD as a quality metric.",
             "Low structural distance is an attention signal; only the explicit behavior contracts justify a refactor or regression test.", "",
             "## Refactoring contracts", ""]
    runtime = similarity["runtime"]
    lines[2:2] = [f"Measured with {runtime['python_implementation']} {runtime['python_version']}, "
                  f"zlib {runtime['zlib_runtime_version']}, level 9, wbits=15; "
                  "symmetric minimum-concatenation NCD, unclipped.", ""]
    lines.extend(f"- {name.replace('_', ' ')}: {'pass' if passed else 'FAIL'}" for name, passed in checks.items())
    lines += ["", "## Similarity (zlib level 9)", "", "| Pair | Raw NCD | Alpha-normalized NCD |",
              "| --- | ---: | ---: |"]
    for name, pair in similarity["pairs"].items():
        lines.append(f"| {name.replace('_', ' ')} | {pair['raw_ncd']:.4f} | {pair['normalized_ncd']:.4f} |")
    lines += ["", "The comments pair adds only textual surprise; the padded-oracle pair adds retained"
              " but candidate-irrelevant literals and computation, increasing measured structural distance"
              " without changing verdicts. The boundary pair changes `>` to `>=`; the independent"
              " integer-contract oracle uses `>= 11` and rejects that fault despite structural resemblance.", "",
              "## Three independent-contract mutation scenarios", "",
              "| Fault | Test | Baseline | Fault |", "| --- | --- | --- | --- |"]
    for name, case in mutations["matrix"].items():
        for test, observation in case["tests"].items():
            lines.append(f"| {name.replace('_', ' ')} | {test.replace('_', ' ')} | {'pass' if observation['baseline_passes'] else 'FAIL'} | "
                         f"{'survived' if observation['fault_passes'] else 'killed'} |")
    totals = mutations["totals"]
    lines += ["", "### Irrelevant novelty: identical verdicts", "",
              "| Candidate | Original oracle | Padded oracle |", "| --- | --- | --- |"]
    for candidate, verdicts in mutations["irrelevant_novelty"].items():
        lines.append(f"| {candidate.replace('_', ' ')} | {'pass' if verdicts['original_passes'] else 'reject'} | "
                     f"{'pass' if verdicts['padded_passes'] else 'reject'} |")
    lines += ["", f"{totals['faults_detected']}/{totals['faults_injected']} injected faults detected; "
              f"{totals['killed_observations']}/{totals['applicable_observations']} applicable test/fault observations killed.",
              "Outside the independent-contract matrix, an intentionally unsound mirrored oracle and faulty implementation *agree* at weight 10 (both return 8); the external contract says 5.",
              "Idempotence alone admits a constant function; the anchor excludes it. Success-only testing misses cleanup after a failed send.",
              "", "The test fixtures are intentionally small and selected. Neither these ratios nor NCD scores estimate field defect rates.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    result = {"kind": "constructed_demonstration", "refactoring_checks": refactoring_checks(),
              "mutations": mutation_results(), "similarity": scores()}
    if not all(result["refactoring_checks"].values()):
        raise AssertionError("refactoring contract violated")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output_dir / "summary.md").write_text(render_summary(result), encoding="utf-8")
    print(f"Wrote {args.output_dir / 'results.json'} and {args.output_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
