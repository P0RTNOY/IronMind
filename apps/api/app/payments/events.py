"""
Canonical event types used across all payment providers.

Every provider MUST map its native event names to these canonical types.
Phase 0 implements only PAYMENT_SUCCEEDED and PAYMENT_FAILED.
"""

PAYMENT_SUCCEEDED = "payment.succeeded"
PAYMENT_FAILED = "payment.failed"

# Phase 1+
SUB_RENEWED = "subscription.renewed"
SUB_CANCELED = "subscription.canceled"
SUB_PAST_DUE = "subscription.past_due"

# Provider-specific: unmapped/unknown events (stored, never routed)
PAYPLUS_UNMAPPED = "payplus.unmapped"

ALL_TYPES = frozenset({
    PAYMENT_SUCCEEDED,
    PAYMENT_FAILED,
    SUB_RENEWED,
    SUB_CANCELED,
    SUB_PAST_DUE,
})
