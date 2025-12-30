from typing import Optional, Annotated
from pydantic import BaseModel, Field
from enum import Enum


class Currency(str, Enum):
    INR = "INR"
    USD = "USD"


class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"
    refunded = "refunded"


PositiveInt = Annotated[int, Field(gt=0)]


class CreatePaymentRequest(BaseModel):
    user_id: str
    amount: PositiveInt
    currency: Currency
    external_reference: Optional[str] = None


class RefundPaymentRequest(BaseModel):
    payment_id: str
    amount: Optional[PositiveInt] = None
    reason: Optional[str] = None


class PaymentResponse(BaseModel):
    payment_id: str
    status: PaymentStatus
    amount: int
    currency: Currency
    client_secret: Optional[str] = None


class RefundResponse(BaseModel):
    refund_id: str
    payment_id: str
    amount: int
    status: PaymentStatus
