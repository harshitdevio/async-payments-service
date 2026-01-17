# Payment Orchestration Service 💳

A backend payment orchestration service designed to handle **asynchronous payments,
webhook-driven state transitions, retries, and partial failures** — the way real
production payment systems actually behave.

This service assumes failure as the default, not the edge case.

---

## What is this? 🚨 (Read this first)

This is a backend system component responsible for **correct and reliable payment
state management** in the presence of unreliable external systems.

It intentionally assumes that:
- webhook callbacks are duplicated
- events arrive out of order
- networks fail mid-operation
- external providers are eventually consistent

The goal is **correctness and consistency**, not happy-path demos or synchronous illusions.

If this paragraph makes sense to you, the rest of the README will too.

---

## Why payment systems are hard in production 🧠

Payments are **not synchronous**.

A `200 OK` response only means *“request accepted”* — not *“money moved”*.

Final payment state arrives later via webhooks that are:
- retried
- duplicated
- delivered at-least-once
- potentially delayed or reordered

Most demo systems quietly assume these problems away.
This service is designed assuming **these problems are guaranteed to happen**.

---

## What this service is NOT ❌ (Explicit non-goals)

This service is intentionally scoped.

It is **not**:
- ❌ A frontend checkout flow
- ❌ A Stripe SDK wrapper
- ❌ A synchronous “payment succeeded” API
- ❌ A tutorial-style happy-path demo
- ❌ A standalone end-user product

This is a **backend reliability and orchestration component**.

Clear boundaries are a feature, not a limitation.

---

## Core design principles 🧩

These principles drive all design decisions in this service:

- Webhooks are the **source of truth**
- Payment state is managed via an **explicit state machine**
- Idempotency is enforced by default
- Duplicate and out-of-order events are expected
- Controllers are thin; domain logic owns correctness
- Provider-specific details do not leak into core domain logic

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

