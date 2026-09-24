"""Executable oracles, metamorphic properties, and effect contracts."""

from collections.abc import Callable


def shipping_fee(weight):
    if weight < 0:
        raise ValueError("negative weight")
    return 8 if weight > 10 else 5


def shipping_fee_boundary_fault(weight):
    if weight < 0:
        raise ValueError("negative weight")
    return 8 if weight >= 10 else 5


def contract_fee_oracle(weight: int) -> int:
    # Integer weights: the upper tier starts at the first integer after 10.
    if weight < 0:
        raise ValueError("negative weight")
    return 8 if weight >= 11 else 5


def mirrored_fee_oracle(weight: int) -> int:
    if weight < 0:
        raise ValueError("negative weight")
    return 8 if weight >= 10 else 5


def fee_examples(candidate: Callable[[int], int]) -> bool:
    # These are contract values, not a second copy of the branch expression.
    return candidate(0) == 5 and candidate(10) == 5 and candidate(11) == 8


def fee_nonboundary_examples(candidate: Callable[[int], int]) -> bool:
    return candidate(0) == 5 and candidate(11) == 8


def fee_examples_with_irrelevant_work(candidate: Callable[[int], int]) -> bool:
    # The calibration is retained computation, but contributes no information about the candidate.
    calibration = (17 * 23 + 41, 101 ** 2 - 97, 13 * 31 + 71)
    offsets = {"north": 83, "south": 149, "west": 211, "east": 277}
    checksum = (calibration[0] * 3) % 257 + (calibration[1] * 4) % 257
    checksum += (calibration[2] * 5) % 257 + sum(offsets.values())
    assert checksum >= 0
    return candidate(0) == 5 and candidate(10) == 5 and candidate(11) == 8


def contract_derived_fee_test(candidate: Callable[[int], int]) -> bool:
    return all(candidate(weight) == contract_fee_oracle(weight) for weight in (0, 10, 11))


def mirrored_fee_test(candidate: Callable[[int], int]) -> bool:
    # A test duplicating the faulty rule will ACCEPT a broken boundary.
    return all(candidate(weight) == mirrored_fee_oracle(weight) for weight in (0, 10, 11))


def canonicalize(value: str) -> str:
    return " ".join(value.lower().split())


def canonicalize_constant_fault(value: str) -> str:
    return ""


def canonical_idempotence(candidate: Callable[[str], str]) -> bool:
    return all(candidate(candidate(value)) == candidate(value) for value in (" A  B ", "X", ""))


def canonical_anchor(candidate: Callable[[str], str]) -> bool:
    return candidate(" A  B ") == "a b"


def publish(open_resource: Callable[[], object], send: Callable[[object], None]) -> None:
    resource = open_resource()
    try:
        send(resource)
    finally:
        resource.close()


def publish_cleanup_fault(open_resource: Callable[[], object], send: Callable[[object], None]) -> None:
    resource = open_resource()
    send(resource)
    resource.close()


def successful_publish_test(candidate: Callable[..., None]) -> bool:
    events: list[str] = []

    class Connection:
        def close(self) -> None:
            events.append("close")

    def open_resource() -> Connection:
        events.append("open")
        return Connection()

    def send(resource: object) -> None:
        events.append("send")

    candidate(open_resource, send)
    return events == ["open", "send", "close"]


def failure_cleanup_contract(candidate: Callable[..., None]) -> bool:
    events: list[str] = []
    failure = RuntimeError("send failed")

    class Connection:
        def close(self) -> None:
            events.append("close")

    def open_resource() -> Connection:
        events.append("open")
        return Connection()

    def send(resource: object) -> None:
        events.append("send")
        raise failure

    try:
        candidate(open_resource, send)
    except RuntimeError as error:
        return error is failure and events == ["open", "send", "close"]
    return False
