from app.domain.payments.enums import PaymentStatus
from app.repositories.payments.payment_repo import PaymentRepository
from app.repositories.payments.stripe_event_repo import StripeEventRepository
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc


class WebhookService:
    """
    Service responsible for processing Stripe webhook events.

    This service treats webhooks as delivery signals, not as a source of truth.
    All state updates are derived from Stripe's current PaymentIntent state to
    ensure correctness under retries, delays, and out-of-order delivery.
    """

    def __init__(
        self,
        *,
        payment_repo: PaymentRepository,
        event_repo: StripeEventRepository,
        session,
    ) -> None:
        """
        Initialize the webhook processing service.

        Args:
            payment_repo: Repository for accessing and mutating payment records.
            event_repo: Repository for persisting processed Stripe event metadata.
            session: Database session used for transactional consistency.
        """
        self._payments = payment_repo
        self._events = event_repo
        self._session = session

    async def handle_event(self, *, event_id: str, event_type: str, payload: dict) -> None:
        """
        Process a Stripe webhook event.

        Events are recorded for idempotency, then the related Stripe
        PaymentIntent is fetched and reconciled against the internal
        payment state. Event ordering is not trusted.
        """
        try:
            async with self._session.begin():
                await self._events.record(
                    event_id=event_id,
                    event_type=event_type,
                )

                pi_id = payload["data"]["object"]["id"]

                stripe_pi = await self._payments.fetch_stripe_payment_intent(pi_id)
                if not stripe_pi:
                    return

                await self._reconcile_payment_state(stripe_pi)

        except IntegrityError as e:
            if isinstance(e.orig, exc.IntegrityError) or "23505" in str(e.orig):
                return
            raise

    async def _reconcile_payment_state(self, stripe_pi) -> None:
        """
        Reconcile internal payment state with Stripe's PaymentIntent state.

        The Stripe object is treated as authoritative. Internal state is
        updated only to match the current Stripe status.
        """
        payment = await self._payments.get_by_stripe_payment_intent_id(stripe_pi.id)
        if not payment:
            return

        status_map = {
            "succeeded": PaymentStatus.succeeded,
            "canceled": PaymentStatus.canceled,
            "requires_payment_method": PaymentStatus.failed,
            "payment_failed": PaymentStatus.failed,
            "processing": PaymentStatus.processing,
        }

        target_status = status_map.get(stripe_pi.status)
        if not target_status:
            return

        if payment.status == target_status:
            return

        await self._payments.update_status(
            payment_id=payment.id,
            status=target_status,
        )
