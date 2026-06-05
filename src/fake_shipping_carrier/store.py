"""In-memory shipment store for the fake shipping carrier.

The point of the Idempotency-Key is that retries return the same
shipment -- same tracking number, same estimated delivery. We record
the shipment on the first call and replay it verbatim afterwards.

Single-process state. The fake stands in for a third party in a single
test container; it is deliberately not built for horizontal scaling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Shipment:
    tracking_number: str
    carrier_reference: str
    estimated_delivery_at: datetime


@dataclass
class Store:
    shipments: dict[str, Shipment] = field(default_factory=dict)

    def get(self, key: str) -> Shipment | None:
        return self.shipments.get(key)

    def put(self, key: str, shipment: Shipment) -> None:
        self.shipments[key] = shipment
