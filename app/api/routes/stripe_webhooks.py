from fastapi import APIRouter, Depends, Request, Header, HTTPException

from app.api.http.dependency import get_webhook_service
from app.services.payments.webhooks_service import WebhookService
from app.services.payments.stripe_gateway import verify_stripe_signature

router = APIRouter()


@router.post("")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
    service: WebhookService = Depends(get_webhook_service),
):
    raw_body = await request.body()

    event = verify_stripe_signature(
        payload=raw_body,
        sig_header=stripe_signature,
    )

    await service.handle_event(
        event_id=event["id"],
        event_type=event["type"],
        payload=event,
    )

    return {"status": "ok"}
