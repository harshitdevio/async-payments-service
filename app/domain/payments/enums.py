from enum import Enum


class Currency(str, Enum):
    INR = "INR"
    USD = "USD"


class PaymentStatus(str, Enum):
    """
    Internal payment lifecycle.

    This is NOT a mirror of Stripe statuses.
    This is what the business understands.
    """

    pending = "pending"      
    succeeded = "succeeded"    
    failed = "failed"         
    canceled = "canceled"     
    refunded = "refunded"      


class RefundStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
