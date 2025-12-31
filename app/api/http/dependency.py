from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from app.db.sessions import get_session

from app.repositories.payments.payment_repo import PaymentRepository
from app.repositories.payments.stripe_event_repo import StripeEventRepository
from app.services.payments.payment_service import PaymentService
from app.services.payments.refund_service import RefundService
from app.services.payments.webhooks_service import WebhookService
from app.services.payments.stripe_gateway import StripeGateway
from app.config.settings import Settings

settings = Settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session() as session:
        yield session


def get_stripe_gateway() -> StripeGateway:
    return StripeGateway(api_key=settings.STRIPE_API_KEY)


async def get_payment_service(
    db: AsyncSession = Depends(get_db),
    stripe: StripeGateway = Depends(get_stripe_gateway),
) -> PaymentService:
    repo = PaymentRepository(session=db)
    return PaymentService(stripe=stripe, repo=repo)


async def get_refund_service(
    db: AsyncSession = Depends(get_db),
) -> RefundService:
    repo = PaymentRepository(session=db)
    return RefundService(repo=repo)


async def get_webhook_service(
    db: AsyncSession = Depends(get_db),
) -> WebhookService:
    payment_repo = PaymentRepository(session=db)
    event_repo = StripeEventRepository(session=db)
    return WebhookService(payment_repo=payment_repo, event_repo=event_repo)
