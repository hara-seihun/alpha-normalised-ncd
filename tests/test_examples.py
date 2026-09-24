"""Contract checks for the deliberately constructed examples and their report."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from examples import refactoring as r
from examples import run
from examples import testing as t


class ExampleContracts(unittest.TestCase):
    def test_refactoring_preserves_explicit_policies(self) -> None:
        self.assertTrue(all(run.refactoring_checks().values()))
        self.assertEqual(r.invoice_subtotal_after([{"units": 2, "price": 3}]), 6)
        self.assertEqual(r.shipment_weight_after([{"parcels": 2, "grams": 3}]), 6)

    def test_mirrored_oracle_can_agree_with_a_fault(self) -> None:
        self.assertEqual(t.shipping_fee_boundary_fault(10), t.mirrored_fee_oracle(10))
        self.assertNotEqual(t.shipping_fee_boundary_fault(10), t.shipping_fee(10))
        self.assertFalse(t.fee_examples(t.shipping_fee_boundary_fault))
        self.assertFalse(t.mirrored_fee_test(t.shipping_fee))
        self.assertTrue(t.mirrored_fee_test(t.shipping_fee_boundary_fault))
        self.assertTrue(t.contract_derived_fee_test(t.shipping_fee))
        self.assertFalse(t.contract_derived_fee_test(t.shipping_fee_boundary_fault))
        for candidate in (t.shipping_fee, t.shipping_fee_boundary_fault):
            self.assertEqual(t.fee_examples(candidate), t.fee_examples_with_irrelevant_work(candidate))

    def test_metamorphic_property_needs_anchor(self) -> None:
        self.assertTrue(t.canonical_idempotence(t.canonicalize_constant_fault))
        self.assertFalse(t.canonical_anchor(t.canonicalize_constant_fault))

    def test_failure_path_needs_effect_contract(self) -> None:
        self.assertTrue(t.successful_publish_test(t.publish_cleanup_fault))
        self.assertFalse(t.failure_cleanup_contract(t.publish_cleanup_fault))

    def test_report_is_deterministic_and_counts_applicable_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first"
            second = Path(directory) / "second"
            for destination in (first, second):
                subprocess.run([sys.executable, "-m", "examples.run", "--output-dir", str(destination)],
                               check=True, capture_output=True, text=True)
            for filename in ("results.json", "summary.md"):
                self.assertEqual((first / filename).read_bytes(), (second / filename).read_bytes())
            report = json.loads((first / "results.json").read_text())
            self.assertEqual(report["mutations"]["totals"], {
                "killed_observations": 4, "applicable_observations": 7,
                "faults_detected": 3, "faults_injected": 3,
            })
            self.assertEqual(report["mutations"]["shared_fault_boundary"]["independent_contract"], 5)
            self.assertEqual(report["similarity"]["status"], "measured")
            pairs = report["similarity"]["pairs"]
            for name in ("renamed_aggregation", "renamed_resource_protocol",
                         "boundary_regression", "contract_derived_oracle", "padded_comments",
                         "padded_oracle_comments", "padded_oracle_computation"):
                self.assertIsInstance(pairs[name]["normalized_ncd"], float)
                for prefix in ("source", "normalized"):
                    self.assertEqual(len(pairs[name][f"{prefix}_bytes"]), 2)
                    self.assertEqual(len(pairs[name][f"{prefix}_compressed_bytes"]), 2)
            self.assertLess(pairs["contract_derived_oracle"]["normalized_ncd"], 0.2)
            self.assertEqual(pairs["padded_oracle_comments"]["normalized_bytes"][0],
                             pairs["padded_oracle_comments"]["normalized_bytes"][1])
            self.assertGreater(pairs["padded_oracle_computation"]["normalized_ncd"],
                               pairs["padded_oracle_comments"]["normalized_ncd"])
            self.assertGreater(pairs["padded_oracle_computation"]["normalized_compressed_bytes"][1],
                               pairs["padded_oracle_computation"]["normalized_compressed_bytes"][0])
            self.assertEqual(report["similarity"]["runtime"]["compression_level"], 9)
            self.assertTrue(report["similarity"]["runtime"]["python_version"])
            self.assertTrue(report["similarity"]["runtime"]["zlib_runtime_version"])


if __name__ == "__main__":
    unittest.main()
