"""Two duplicate structures with explicit policy preserved during extraction."""

from collections.abc import Callable, Iterable
from typing import TypeVar

T = TypeVar("T")


def invoice_subtotal(rows):
    total = 0
    for row in rows:
        if row.get("units") is None:
            continue
        amount = row["units"] * row["price"]
        if amount < 0:
            raise ValueError("negative invoice line")
        total += amount
    return total


def shipment_weight(rows):
    total = 0
    for row in rows:
        if row.get("parcels") is None:
            continue
        amount = row["parcels"] * row["grams"]
        if amount < 0:
            raise ValueError("negative shipment line")
        total += amount
    return total


def sum_lines(rows: Iterable[dict[str, int]], count: str, rate: str, label: str) -> int:
    total = 0
    for row in rows:
        if row.get(count) is None:
            continue
        amount = row[count] * row[rate]
        if amount < 0:
            raise ValueError(f"negative {label} line")
        total += amount
    return total


def invoice_subtotal_after(rows: Iterable[dict[str, int]]) -> int:
    return sum_lines(rows, "units", "price", "invoice")


def shipment_weight_after(rows: Iterable[dict[str, int]]) -> int:
    return sum_lines(rows, "parcels", "grams", "shipment")


class Resource:
    def __init__(self, events: list[str]):
        self.events = events

    def close(self) -> None:
        self.events.append("close")


def render_invoice(open_resource, payload):
    resource = open_resource()
    try:
        resource.events.append("invoice")
        return payload.upper()
    finally:
        resource.close()


def render_label(open_resource, payload):
    resource = open_resource()
    try:
        resource.events.append("label")
        return payload.lower()
    finally:
        resource.close()


def with_resource(open_resource: Callable[[], Resource], effect: Callable[[Resource], T]) -> T:
    resource = open_resource()
    try:
        return effect(resource)
    finally:
        resource.close()


def render_invoice_after(open_resource: Callable[[], Resource], payload: str) -> str:
    def effect(resource: Resource) -> str:
        resource.events.append("invoice")
        return payload.upper()

    return with_resource(open_resource, effect)


def render_label_after(open_resource: Callable[[], Resource], payload: str) -> str:
    def effect(resource: Resource) -> str:
        resource.events.append("label")
        return payload.lower()

    return with_resource(open_resource, effect)
