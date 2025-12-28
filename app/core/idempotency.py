class IdempotencyKey(str):
    """
    Placeholder for type hinting idempotency keys.
    Could be a UUID or hash of (user_id + external_reference)
    """
    pass
