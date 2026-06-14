# fake-shipping-carrier

Deterministic in-memory fake of the external shipping carrier, consumed
by the Sales totality over HTTP. **The carrier is a third party, not a
Sales-internal totality**, so this service has no database and no domain
model. The asymmetry with the real `catalog` and `identity` services is
intentional.

## About this reference

This repository is part of a reference implementation accompanying a
six-article series on distributed systems architecture by Alberto Casado
Martin. The series argues that most distributed systems are *attributive
totalities* — their parts only acquire meaning in relation to the whole — and
that the canonical microservices reparto routinely confuses them with
*distributive totalities* (sets of independent peers). The full list of
articles is at the bottom of this README; the fourth article in particular
gives the framing that explains why this repository looks the way it does.

### Where this repo sits in that frame

A real shipping carrier — FedEx, UPS, DHL — is itself an attributive totality
at its own level, with a domain of its own. From the cut at which we are
designing the e-commerce, the carrier is **not a totality of ours**. It is a
**material part** of the e-commerce: it sustains the totality (an order
ultimately needs to be physically shipped) but does not constitute its
identity (the same carrier could equally serve any commerce). Per the fourth
article, the carrier enters our system through *determination* — our contract
defines how we consume it, what we send, what we expect back.

The consequence is that there is **nothing of ours to implement** inside this
repository. A real carrier is someone else's totality; a faithful stub of the
contract is the correct and complete thing to build. The poverty of this fake
is the argument, not a shortcoming: dressing it up with a fake domain model
or a fake "totality shape" would betray the cut.

What this fake **does** model precisely is the contract Sales relies on at
this boundary: the **idempotency key** (the order id). The Sales
`shipping-dispatcher` sends one per shipment request; the fake records the
shipment per key (tracking number, carrier reference, estimated delivery) and
replays it byte-for-byte on retries. This is what makes the boundary safe to
retry — and per the fifth and sixth articles, the presence of idempotency at
a boundary is the canonical sign that the boundary is real.

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

## Article series

URLs will be filled in once each article is published; placeholders below are
search-and-replaceable.

1. [The Illusion of Microservices Independence](TODO-article-1-url)
2. [Is Going Back to Monoliths Really the Solution?](TODO-article-2-url)
3. [The Forgotten Transition: From Analysis to Design, in a Field That Stopped Asking](TODO-article-3-url)
4. [The Illusion of Method: How Domain-Driven Design Hides the Question It Claims to Answer](TODO-article-4-url)
5. [Place Order: Anatomy of a Bad Cut](TODO-article-5-url)
6. [Place Order: A Cut That Holds](TODO-article-6-url)
