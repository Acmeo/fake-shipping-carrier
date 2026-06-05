"""HTTP-level tests for POST /v1/shipments.

Verify byte-for-byte conformance with the Sales shipping_carrier_client
contract and the idempotency semantics: the same key returns the same
shipment, including the same estimated delivery.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient


def _body(order_id: str) -> dict[str, Any]:
    return {
        "order_id": order_id,
        "customer_id": "cust-integration-001",
        "items": [{"product_id": "prod-001", "quantity": 2}],
    }


def _post(client: TestClient, order_id: str) -> Any:
    return client.post(
        "/v1/shipments",
        headers={"Idempotency-Key": order_id},
        json=_body(order_id),
    )


def test_happy_path_returns_200_with_expected_fields(client: TestClient) -> None:
    order_id = str(uuid4())
    response = _post(client, order_id)
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"tracking_number", "carrier_reference", "estimated_delivery_at"}
    assert body["tracking_number"].startswith("TRK-")
    assert body["carrier_reference"].startswith("carrier-ref-")
    # estimated_delivery_at must parse as ISO-8601 with tz info.
    parsed = datetime.fromisoformat(body["estimated_delivery_at"])
    assert parsed.tzinfo is not None


def test_tracking_number_is_stable_per_order_id(client: TestClient) -> None:
    order_id = str(uuid4())
    first = _post(client, order_id)
    second = _post(client, order_id)
    assert first.status_code == second.status_code == 200
    assert first.json()["tracking_number"] == second.json()["tracking_number"]


def test_estimated_delivery_at_is_replayed_not_recomputed(client: TestClient) -> None:
    # The full body must be identical on replay -- including the timestamp,
    # which would drift if it were recomputed on each call.
    order_id = str(uuid4())
    first = _post(client, order_id)
    second = _post(client, order_id)
    assert first.json() == second.json()


def test_distinct_order_ids_get_distinct_tracking_numbers(client: TestClient) -> None:
    a = _post(client, str(uuid4()))
    b = _post(client, str(uuid4()))
    assert a.json()["tracking_number"] != b.json()["tracking_number"]
