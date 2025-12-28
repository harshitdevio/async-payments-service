import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(String, nullable=False)

    amount = Column(Integer, nullable=False)  # minor units only
    currency = Column(String(3), nullable=False)

    status = Column(String, nullable=False)

    stripe_payment_intent_id = Column(String, nullable=False, unique=True)
    client_secret = Column(String, nullable=False)

    external_reference = Column(String, nullable=True)

    idempotency_key = Column(String, nullable=False, unique=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class StripeWebhookEvent(Base):
    __tablename__ = "stripe_webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    event_id = Column(String, nullable=False, unique=True)
    event_type = Column(String, nullable=False)

    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
