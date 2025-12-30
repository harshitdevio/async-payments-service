from typing import Optional

from app.domain.payments.enums import PaymentStatus, Currency
from app.domain.payments.state_machine import assert_transition_allowed
from app.services.payments.stripe_gateway import StripeGateway
from app.repositories.payments.payment_repo import PaymentRepository
from app.core.idempotency import IdempotencyKey


class PaymentService:
    def __init__(
        self,
        *,
        stripe: StripeGateway,
        repo: PaymentRepository,
    ) -> None:
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
        Creates a payment in PENDING state and returns client_secret.
        Idempotent by business key.
        """

        # 1. Idempotency check (business-level)
        existing = await self._repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return {
                "payment_id": existing.id,
                "status": existing.status,
                "client_secret": existing.client_secret,
            }

        # 2. Create Stripe PaymentIntent
        stripe_pi = await self._stripe.create_payment_intent(
            amount=amount,
            currency=currency.value,
            metadata={
                "user_id": user_id,
                "external_reference": external_reference,
            },
        )

        # 3. Persist internal payment (domain state = pending)
        payment = await self._repo.create(
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.pending,
            stripe_payment_intent_id=stripe_pi.id,
            client_secret=stripe_pi.client_secret,
            external_reference=external_reference,
            idempotency_key=idempotency_key,
        )

        return {
            "payment_id": payment.id,
            "status": payment.status,
            "client_secret": payment.client_secret,
        }

    async def mark_payment_succeeded(self, *, payment_id: str) -> None:
        payment = await self._repo.get_by_id(payment_id)
        assert_transition_allowed(
            current=payment.status,
            target=PaymentStatus.succeeded,
        )

        await self._repo.update_status(
            payment_id=payment.id,
            status=PaymentStatus.succeeded,
        )

    async def mark_payment_failed(self, *, payment_id: str) -> None:
        payment = await self._repo.get_by_id(payment_id)
        assert_transition_allowed(
            current=payment.status,
            target=PaymentStatus.failed,
        )

        await self._repo.update_status(
            payment_id=payment.id,
            status=PaymentStatus.failed,
        )
