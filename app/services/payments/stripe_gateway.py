from fastapi import HTTPException
import stripe
from app.config.settings import Settings

settings = Settings()

def verify_stripe_signature(payload: bytes, sig_header: str) -> dict:
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

from app.infrastructure.stripe.client import StripeGateway

