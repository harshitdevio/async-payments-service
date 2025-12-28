import stripe
from typing import Any


class StripeGateway:
    """
    Thin wrapper around Stripe SDK.
    No business logic here.
    """

    def __init__(self, *, api_key: str) -> None:
        stripe.api_key = api_key

    async def create_payment_intent(
        self,
        *,
        amount: int,
        currency: str,
        metadata: dict[str, Any],
    ):
        """
        Returns raw Stripe PaymentIntent object.
        Services decide what to extract.
        """
        return stripe.PaymentIntent.create(
            amount=amount,
            currency=currency.lower(),
            metadata=metadata,
        )
