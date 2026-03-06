# PaymentFlow

PaymentFlow is a payment processing backend built with **Stripe** API.

The project explores payment lifecycle management, state transitions, Stripe integration, and webhook processing using a layered backend architecture.

## Core Features

### 1. Payment State Management

Payments move through a predefined set of states instead of being updated arbitrarily.

```text
PENDING
   │
   ▼
REQUIRES_ACTION
   │
   ▼
PROCESSING
   │
   ▼
SUCCEEDED
   ├── REFUNDED
   └── FAILED
```

Every status change is validated before being applied, helping prevent invalid payment states.

### 2. Stripe Payment Intents

Payments are created through Stripe Payment Intents.

The application stores its own payment records while tracking the corresponding Stripe Payment Intent for synchronization and reconciliation.

### 3. Webhook Processing

Stripe webhooks are used to receive asynchronous payment updates.

Incoming events are:

- Signature verified
- Stored in the database
- Processed by the webhook service
- Used to update local payment status

This allows the application to stay synchronized with Stripe even when payment updates happen outside the initial request flow.

### 4. Service and Repository Layers

Business logic is kept inside services while database operations are handled by repositories.

```text
Route
  ↓
Service
  ↓
Repository
  ↓
Database
```

This keeps route handlers small and separates application logic from persistence logic.

### 5. Dependency Injection

Services and repositories are created through FastAPI dependencies.

```text
Request
  ↓
Dependency
  ↓
Service
  ↓
Repository
```

This makes components easier to replace and test independently.

---

## Project Structure

```text
api/
├── routes/
│   ├── payments.py
│   ├── refunds.py
│   └── stripe_webhooks.py
│
services/
├── payment_service.py
├── refund_service.py
└── webhook_service.py
│
repositories/
├── payment_repository.py
└── stripe_event_repository.py
│
models/
├── payment.py
└── stripe_event.py
```

---

## What This Project Focuses On

- Payment creation.
- Stripe Payment Intent integration
- Webhook handling
- Payment state transitions
- Service and repository patterns
- Async database access with SQLAlchemy

---

## What This Project Does Not Cover

Some concerns that would exist in a production payment system are intentionally simplified or omitted:

- Fraud detection
- Distributed transactions
- Multi-provider payment routing
- PCI compliance requirements
- Settlement and accounting systems

---

## API Documentation

Live at:

```text
https://async-payments-service.onrender.com/docs
```

---

## License

This project is licensed under the Apache License 2.0.