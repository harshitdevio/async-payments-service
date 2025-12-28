from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment import Payment
from app.domain.payments.enums import PaymentStatus, Currency


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, payment_id: str) -> Payment:
        result = await self._session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise ValueError("Payment not found")
        return payment

    async def get_by_stripe_payment_intent_id(
        self, stripe_payment_intent_id: str
    ) -> Optional[Payment]:
        result = await self._session.execute(
            select(Payment).where(
                Payment.stripe_payment_intent_id == stripe_payment_intent_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[Payment]:
        result = await self._session.execute(
            select(Payment).where(Payment.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        user_id: str,
        amount: int,
        currency: Currency,
        status: PaymentStatus,
        stripe_payment_intent_id: str,
        client_secret: str,
        external_reference: Optional[str],
        idempotency_key: str,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency=currency.value,
            status=status.value,
            stripe_payment_intent_id=stripe_payment_intent_id,
            client_secret=client_secret,
            external_reference=external_reference,
            idempotency_key=idempotency_key,
        )

        self._session.add(payment)
        await self._session.commit()
        await self._session.refresh(payment)
        return payment

    async def update_status(
        self,
        *,
        payment_id: str,
        status: PaymentStatus,
    ) -> None:
        payment = await self.get_by_id(payment_id)
        payment.status = status.value
        await self._session.commit()
