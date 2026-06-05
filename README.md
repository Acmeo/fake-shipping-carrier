# fake-shipping-carrier

Deterministic in-memory fake of the external shipping carrier, consumed
by the Sales totality over HTTP. **The carrier is a third party, not a
Sales-internal totality**, so this service has no database and no domain
model. The asymmetry with the real `catalog` and `identity` services is
intentional.

## HTTP contract

```
POST /v1/shipments
  headers: Idempotency-Key: <order_id-string>
  body:    { "order_id": "<uuid-string>", "customer_id": "<str>",
             "items": [ { "product_id": "<str>", "quantity": <int> }, ... ] }
  200 -> { "tracking_number", "carrier_reference",
           "estimated_delivery_at": "<ISO-8601 datetime>" }
  5xx -> service unavailable
```

- The Sales client treats `>= 500` as `ShippingCarrierUnavailable` and
  any other non-`200` as `ShippingCarrierProtocolError`. So the fake
  only ever responds `200` in normal operation.
- The carrier resolves the delivery address from `customer_id`
  internally, so the fake does **not** model an address. The shipping
  address is, by design, not part of this contract.

## Behaviour

The fake has only one path: 200 happy, idempotent per Idempotency-Key
(which is the `order_id`). The first call for a key creates a
deterministic shipment record and stores it; subsequent calls with the
same key replay the same record byte-for-byte, including the same
`tracking_number` and the same `estimated_delivery_at`.

- `tracking_number = "TRK-<order_id-suffix>"` (stable per key).
- `carrier_reference = "carrier-ref-<order_id-suffix>"` (stable per key).
- `estimated_delivery_at`: the UTC date of the first call truncated to
  midnight, plus 3 days, at 10:00:00+00:00. Recorded with the shipment
  and replayed verbatim on retries -- not recomputed.

The carrier does not validate stock; that lives in Sales. The fake only
requires a well-formed body.

## Running

```
uv sync
uv run uvicorn fake_shipping_carrier.app:app --host 0.0.0.0 --port 8004
```

## Validation

```
uv run ruff check .
uv run mypy src
uv run pytest
```
