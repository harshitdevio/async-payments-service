# Async Payments Service 💳

An Async Payment Service built to model the failure modes that most payment tutorials quietly skip - out-of-order webhooks, duplicate delivery, crash-between-transactions.
This covers real failure modes of async payments like webhook deduplication, race-safe idempotency, and strict state machine transitions.

This service assumes failure as the default, not the edge case!

---

It intentionally assumes that:
- webhook callbacks are duplicated
- events arrive out of order
- networks fail mid-operation
- external providers are eventually consistent

The goal is **correctness and consistency**, not happy-path demos or synchronous illusions.


## Features
- Explicit State Machine
- Idempotent by default
- Atomic Database Transactions
- Race conditions handled
- Webhook-driven Architecture
- Stripe Signature Verification
- Idempotent Webhook Processing
- Provider Abstraction (Stripe-specific details are isolated in the infrastructure layer. The domain layer has zero knowledge of Stripe.)
- Layered Architecture

---


## High-level architecture 🏗️

```text
Client App
   │
   │  (create payment)
   ▼
Payment API
   │
   │  (initiate intent)
   ▼
Payment Provider (Stripe-like)
   │
   │  (async webhooks)
   ▼
Webhook Handler
   │
   │  (validated state transitions)
   ▼
Payment State Store (DB)
```

## Payment state model

Payments move through a strict state machine.

Example states:
- CREATED
- PROCESSING
- SUCCEEDED
- FAILED
- CANCELED

Rules:
- Invalid or out-of-order transitions are rejected
- Duplicate webhook events are safely ignored
- Final states are immutable

## Webhook handling & idempotency

Webhook events:
- may be delivered multiple times
- may arrive before previous events
- may arrive after database retries

This service:
- verifies webhook signatures
- stores processed event IDs
- guarantees idempotent processing
- enforces valid state transitions only

## Failure scenarios handled

- Duplicate webhook delivery
- Out-of-order events
- Network timeouts during state updates
- Webhooks arriving before initial payment commit
- Client retries creating payments
- Provider retries callbacks

## Live API (Hosted) 🌐

A hosted instance is available for **API contract inspection and behavioral reference**.

- **Swagger UI:** (https://async-payments-service.onrender.com/docs) 
- **Base URL:** (https://async-payments-service.onrender.com)

This deployment exists to expose:
- endpoint contracts
- request / response shapes
- validation rules
- state transition behavior

It is **not intended** to represent a complete end-to-end payment flow or
a production-ready environment.


## Tech stack

- Python
- FastAPI
- PostgreSQL
- Stripe (as payment provider)
- Redis (optional, for idempotency helpers)

Infrastructure choices are intentionally minimal.
Correctness does not depend on queues or distributed systems.


