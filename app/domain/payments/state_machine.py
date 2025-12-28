"""
Payment domain state machine.

Defines all legal payment lifecycle transitions independently
of any payment provider (e.g. Stripe).

This module is the single source of truth for validating
payment state changes. No service or webhook handler should
mutate payment status without passing through this validation.

Reasons:
- Prevent illegal state transitions caused by retries or out-of-order events
- Keep business rules isolated from infrastructure concerns
- Make payment behavior auditable and testable
"""

from app.domain.payments.enums import PaymentStatus

class InvalidPaymentTransition(Exception):
    pass


# Explicit, auditable state graph
_ALLOWED_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.pending: {
        PaymentStatus.succeeded,
        PaymentStatus.failed,
        PaymentStatus.canceled,
    },
    PaymentStatus.succeeded: {
        PaymentStatus.refunded,
    },
    PaymentStatus.failed: set(),      
    PaymentStatus.canceled: set(),    
    PaymentStatus.refunded: set(),   
}


def assert_transition_allowed(
    *, current: PaymentStatus, target: PaymentStatus
) -> None:
    """
    Validate whether a payment can transition from `current` to `target`.

    This function is intentionally side-effect free.
    Persistence and external effects are handled by services.

    Raises:
        InvalidPaymentTransition: if the transition is not allowed.
    """
    if current == target:
        return

    allowed = _ALLOWED_TRANSITIONS.get(current)
    if not allowed or target not in allowed:
        raise InvalidPaymentTransition(
            f"Illegal payment transition: {current} -> {target}"
        )
