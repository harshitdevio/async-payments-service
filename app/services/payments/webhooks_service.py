from app.domain.payments.enums import PaymentStatus
from app.domain.payments.state_machine import assert_transition_allowed
from app.repositories.payments.payment_repo import PaymentRepository
from app.repositories.payments.stripe_event_repo import StripeEventRepository
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc


class WebhookService:
    """
    Service responsible for processing Stripe webhook events.

    This class handles deduplication of incoming events, enforces
    atomic updates, and applies valid state transitions to internal
    payment records based on Stripe event payloads.
    """

    def __init__(
        self,
        *,
        payment_repo: PaymentRepository,
        event_repo: StripeEventRepository,
        session,
    ) -> None:
        """
        Create a new WebhookService instance.

        Args:
            payment_repo: Repository used to fetch and update payment entities.
            event_repo: Repository used to persist processed Stripe event metadata.
            session: Database session used to ensure atomic operations.
        """
        self._payments = payment_repo
        self._events = event_repo
        self._session = session

    async def handle_event(self, *, event_id: str, event_type: str, payload: dict) -> None:
        """
        Handle a single Stripe webhook event.

        The event is first recorded using a database-enforced uniqueness
        constraint to guarantee idempotent processing. If the event has
        already been handled, it is safely ignored.

        Supported payment intent events trigger a corresponding payment
        state transition within the same database transaction.
        """
        try:
            async with self._session.begin():

                await self._events.record(
                    event_id=event_id,
                    event_type=event_type,
                )

                if event_type == "payment_intent.succeeded":
                    await self._handle_payment_succeeded(payload)

                elif event_type == "payment_intent.payment_failed":
                    await self._handle_payment_failed(payload)

                elif event_type == "payment_intent.canceled":
                    await self._handle_payment_canceled(payload)

        except IntegrityError as e:
            if isinstance(e.orig, exc.IntegrityError) or "23505" in str(e.orig):
                return
            raise

    async def _handle_payment_succeeded(self, payload: dict) -> None:
        """
        Apply a successful payment intent update.

        Locates the internal payment associated with the Stripe payment
        intent and transitions it to a succeeded state, provided the
        transition is allowed by the domain state machine.
        """
        pi_id = payload["data"]["object"]["id"]

        payment = await self._payments.get_by_stripe_payment_intent_id(pi_id)
        if not payment:
            return

        assert_transition_allowed(
            current=payment.status,
            target=PaymentStatus.succeeded,
        )

        await self._payments.update_status(
            payment_id=payment.id,
            status=PaymentStatus.succeeded,
        )

    async def _handle_payment_failed(self, payload: dict) -> None:
        """
        Apply a failed payment intent update.

        Marks the corresponding internal payment as failed after
        validating that the transition is permitted.
        """
        pi_id = payload["data"]["object"]["id"]

        payment = await self._payments.get_by_stripe_payment_intent_id(pi_id)
        if not payment:
            return

        assert_transition_allowed(
            current=payment.status,
            target=PaymentStatus.failed,
        )

        await self._payments.update_status(
            payment_id=payment.id,
            status=PaymentStatus.failed,
        )

    async def _handle_payment_canceled(self, payload: dict) -> None:
        """
        Apply a canceled payment intent update.

        Updates the payment status to canceled if the current state
        allows the transition.
        """
        pi_id = payload["data"]["object"]["id"]

        payment = await self._payments.get_by_stripe_payment_intent_id(pi_id)
        if not payment:
            return

        assert_transition_allowed(
            current=payment.status,
            target=PaymentStatus.canceled,
        )

        await self._payments.update_status(
            payment_id=payment.id,
            status=PaymentStatus.canceled,
        )
