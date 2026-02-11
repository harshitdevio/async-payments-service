class OrphanPaymentEvent(Exception):
    def __init__(self, stripe_payment_intent_id: str):
        super().__init__(
            f"Orphan Stripe event for payment_intent_id={stripe_payment_intent_id}"
        )
        self.stripe_payment_intent_id = stripe_payment_intent_id
