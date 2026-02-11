from typing import Optional

from app.domain.payments.enums import PaymentStatus, Currency
from app.domain.payments.state_machine import assert_transition_allowed
from app.services.payments.stripe_gateway import StripeGateway
from app.repositories.payments.payment_repo import PaymentRepository
from app.core.idempotency import IdempotencyKey
from app.domain.exceptions.exceptions import OrphanPaymentEvent


class PaymentService:
    """
    Application service responsible for orchestrating the payment lifecycle.

    This service coordinates between the Stripe gateway and the persistence
    layer to create and update payments while enforcing domain rules such as
    valid status transitions and idempotency guarantees.

    It does not expose Stripe directly to higher layers of the application.
    Instead, it encapsulates all payment-related workflows behind a clear
    service boundary.
    """

    def __init__(
        self,
        *,
        stripe: StripeGateway,
        repo: PaymentRepository,
    ) -> None:
        """
        Initialize the PaymentService.

        Args:
            stripe: Gateway responsible for interacting with Stripe APIs.
            repo: Repository handling persistence and retrieval of payment records.
        """
        self._stripe = stripe
        self._repo = repo

    async def create_payment(
        self,
        *,
        user_id: str,
        amount: int,
        currency: Currency,
        external_reference: Optional[str],
        idempotency_key: IdempotencyKey,
    ) -> dict:
        """
        Create a new payment and corresponding Stripe PaymentIntent.

        This method enforces idempotency at the application level. If a payment
        already exists for the provided idempotency key, the existing record
        is returned instead of creating a new one.

        The flow is:
        1. Check for an existing payment using the idempotency key.
        2. If found, return its details.
        3. Otherwise, create a new payment record in the database (PENDING).
        4. Create a PaymentIntent in Stripe linked to the internal payment ID.
        5. Update the payment record with Stripe identifiers.
        6. Return the payment identifier, status, and Stripe client secret.

        Args:
            user_id: Identifier of the user initiating the payment.
            amount: Payment amount in the smallest currency unit (e.g., cents).
            currency: Currency of the payment.
            external_reference: Optional business reference (e.g., order ID).
            idempotency_key: Unique key used to prevent duplicate payment creation.

        Returns:
            A dictionary containing:
                - payment_id: Internal payment identifier.
                - status: Current payment status.
                - client_secret: Stripe client secret used by the frontend
                  to complete the payment confirmation.

        Raises:
            Any exception propagated from the Stripe gateway or repository layer.
        """

        existing = await self._repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return {
                "payment_id": existing.id,
                "status": existing.status,
                "client_secret": existing.client_secret,
            }
        
        payment = await self._repo.create(
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.pending,
            stripe_payment_intent_id=None,
            client_secret=None,
            external_reference=external_reference,
            idempotency_key=idempotency_key,
        )

        stripe_pi = await self._stripe.create_payment_intent(
        amount=amount,
        currency=currency.value,
        metadata={
            "user_id": user_id,
            "external_reference": external_reference,
            "payment_id": payment.id,
        },
    )
        
        await self._repo.update_stripe_fields(
        payment_id=payment.id,
        stripe_payment_intent_id=stripe_pi.id,
        client_secret=stripe_pi.client_secret,
    )
        return {
            "payment_id": payment.id,
            "status": payment.status,
            "client_secret": payment.client_secret,
        }

    async def mark_payment_succeeded_by_stripe(self, *, stripe_payment_intent_id: str) -> None:
        """
        Mark a payment as succeeded using a Stripe PaymentIntent identifier.

        This method resolves the internal payment record using the provided
        Stripe `payment_intent_id`, validates that the transition to the
        SUCCEEDED state is allowed by the domain state machine, and persists
        the state change.

        If no internal payment is found for the given Stripe identifier,
        the event is treated as an orphan payment event.

        Args:
            stripe_payment_intent_id: Stripe PaymentIntent ID received from
                webhook events.

        Raises:
            OrphanPaymentEvent: If no internal payment record exists for the
                given Stripe PaymentIntent ID.
            AssertionError or domain-specific exception: If the state transition
                is not allowed by the domain state machine.
            Any exception raised by the repository layer.
        """

        payment = await self._repo.get_by_stripe_payment_intent_id(
            stripe_payment_intent_id
        )
        
        if not payment:
            raise OrphanPaymentEvent(stripe_payment_intent_id)

        assert_transition_allowed(
            current=PaymentStatus(payment.status),
            target=PaymentStatus.succeeded,
        )

        await self._repo.update_status(
            payment_id=payment.id,
            status=PaymentStatus.succeeded,
        )

    async def mark_payment_failed_by_stripe(
        self, *, stripe_payment_intent_id: str
    ) -> None:
        """
        Mark a payment as failed using a Stripe PaymentIntent identifier.

        Resolves the internal payment record using the Stripe
        `payment_intent_id`, validates the transition to FAILED via the domain
        state machine, and persists the state change.

        If no internal payment exists for the given Stripe identifier, the
        event is treated as an orphan payment event.

        Args:
            stripe_payment_intent_id: Stripe PaymentIntent ID received from
                webhook events.

        Raises:
            OrphanPaymentEvent: If no internal payment record exists for the
                given Stripe PaymentIntent ID.
            AssertionError or domain-specific exception: If the state transition
                is not allowed.
            Any exception raised by the repository layer.
        """
        payment = await self._repo.get_by_stripe_payment_intent_id(
            stripe_payment_intent_id
        )

        if not payment:
            raise OrphanPaymentEvent(stripe_payment_intent_id)

        assert_transition_allowed(
            current=PaymentStatus(payment.status),
            target=PaymentStatus.failed,
        )

        await self._repo.update_status(
            payment_id=payment.id,
            status=PaymentStatus.failed,
        )
