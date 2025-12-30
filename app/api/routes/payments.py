from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.schemas.payments import (
    CreatePaymentRequest,
    PaymentResponse,
    RefundPaymentRequest,
)
from app.api.http.dependency import (
    get_payment_service,
    get_refund_service,
)
from app.core.idempotency import IdempotencyKey
from services.payments.payment_service import PaymentService
from services.payments.refund_service import RefundService

router = APIRouter()


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    payload: CreatePaymentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    service: PaymentService = Depends(get_payment_service),
):
    result = await service.create_payment(
        user_id=payload.user_id,
        amount=payload.amount,
        currency=payload.currency,
        external_reference=payload.external_reference,
        idempotency_key=IdempotencyKey(idempotency_key),
    )

    return result


@router.post("/refund")
async def refund_payment(
    payload: RefundPaymentRequest,
    service: RefundService = Depends(get_refund_service),
):
    await service.refund_payment(
        payment_id=payload.payment_id,
        amount=payload.amount,
    )
    return {"status": "ok"}
