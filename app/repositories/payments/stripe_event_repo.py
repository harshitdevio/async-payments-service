from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment import StripeWebhookEvent


class StripeEventRepository:
    """
    Stores processed Stripe event IDs to guarantee webhook idempotency.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists(self, event_id: str) -> bool:
        result = await self._session.execute(
            select(StripeWebhookEvent.id).where(
                StripeWebhookEvent.event_id == event_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def record(self, *, event_id: str, event_type: str) -> None:
        event = StripeWebhookEvent(
            event_id=event_id,
            event_type=event_type,
        )
        self._session.add(event)
        await self._session.commit()
