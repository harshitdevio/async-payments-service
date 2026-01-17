from app.domain.payments.enums import PaymentStatus
from app.domain.payments.state_machine import assert_transition_allowed
from app.repositories.payments.payment_repo import PaymentRepository


class RefundService:
    def __init__(self, *, repo: PaymentRepository) -> None:
        self._repo = repo

    async def refund_payment(
        self,
        *,
        payment_id: str,
        amount: int | None = None,
    ) -> None:
        payment = await self._repo.get_by_id(payment_id)

        # Only succeeded payments can be refunded
        assert_transition_allowed(
            current=payment.status,
            target=PaymentStatus.refunded,
        )

        # NOTE: Partial refund tracking intentionally skipped
        # This is an MVP payment core, not Stripe Billing

        await self._repo.update_status(
            payment_id=payment.id,
            status=PaymentStatus.refunded,
        )
