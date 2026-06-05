"""FastAPI app for the fake shipping carrier.

Implements POST /v1/shipments matching the contract consumed by the
Sales shipping_carrier_client. The fake is intentionally thin: no DB,
no domain model. It is a third party, not a totality.

Idempotent per Idempotency-Key (the order id): the first call records a
deterministic shipment and stores it; subsequent calls with the same
key replay the recorded shipment byte-for-byte. Estimated delivery is
captured at first-call time and never recomputed.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from typing import Annotated

from fastapi import FastAPI, Header
from pydantic import BaseModel, Field

from fake_shipping_carrier.store import Shipment, Store


class ShipmentItem(BaseModel):
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)


class ShipmentRequest(BaseModel):
    order_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    items: list[ShipmentItem] = Field(min_length=1)


class ShipmentResponse(BaseModel):
    tracking_number: str
    carrier_reference: str
    estimated_delivery_at: datetime


app = FastAPI(title="fake-shipping-carrier", version="0.1.0")
app.state.store = Store()


def _store() -> Store:
    return app.state.store  # type: ignore[no-any-return]


def _suffix(idempotency_key: str) -> str:
    """Stable, readable suffix derived from the idempotency key.

    The order id is a UUID string, so the first segment is unique enough
    for human-readable tracking numbers in fixtures and logs.
    """
    return idempotency_key.split("-", 1)[0]


def _build_shipment(idempotency_key: str, now: datetime) -> Shipment:
    suffix = _suffix(idempotency_key)
    estimated = datetime.combine(now.date(), time(10, 0), tzinfo=UTC) + timedelta(days=3)
    return Shipment(
        tracking_number=f"TRK-{suffix}",
        carrier_reference=f"carrier-ref-{suffix}",
        estimated_delivery_at=estimated,
    )


@app.post("/v1/shipments", response_model=ShipmentResponse)
def arrange_shipment(
    body: ShipmentRequest,  # noqa: ARG001 -- body is validated; carrier ignores address by design
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1)],
) -> Shipment:
    store = _store()
    existing = store.get(idempotency_key)
    if existing is not None:
        return existing
    shipment = _build_shipment(idempotency_key, datetime.now(UTC))
    store.put(idempotency_key, shipment)
    return shipment


@app.get("/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
