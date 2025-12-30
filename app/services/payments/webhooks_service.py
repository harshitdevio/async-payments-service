from app.domain.payments.enums import PaymentStatus
from app.domain.payments.state_machine import assert_transition_allowed
from app.repositories.payments.payment_repo import PaymentRepository
from app.repositories.payments.stripe_event_repo import StripeEventRepository


class WebhookService:
    def __init__(
        self,
        *,
        payment_repo: PaymentRepository,
        event_repo: StripeEventRepository,
    ) -> None:
        self._payments = payment_repo
        self._events = event_repo

    async def handle_event(self, *, event_id: str, event_type: str, payload: dict) -> None:
        """
        Stripe webhook entrypoint.
        This method must be:
        - idempotent
        - order-independent
        - side-effect safe
        """

        # 1. Deduplicate Stripe events 
        if await self._events.exists(event_id):
            return

        await self._events.record(event_id=event_id, event_type=event_type)

        # 2. Route event types we care about
        if event_type == "payment_intent.succeeded":
            await self._handle_payment_succeeded(payload)

        elif event_type == "payment_intent.payment_failed":
            await self._handle_payment_failed(payload)

        elif event_type == "payment_intent.canceled":
            await self._handle_payment_canceled(payload)

        # Ignore everything else 

    async def _handle_payment_succeeded(self, payload: dict) -> None:
        pi_id = payload["data"]["object"]["id"]

        payment = await self._payments.get_by_stripe_payment_intent_id(pi_id)
        if not payment:
            return  # out of order or irrelevant

        assert_transition_allowed(
            current=payment.status,
            target=PaymentStatus.succeeded,
        )

        await self._payments.update_status(
            payment_id=payment.id,
            status=PaymentStatus.succeeded,
        )

    async def _handle_payment_failed(self, payload: dict) -> None:
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
