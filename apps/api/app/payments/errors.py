"""
Typed webhook exceptions for correct HTTP status mapping.

WebhookVerificationError → 401 (signature/auth invalid)
WebhookPayloadError      → 400 (malformed JSON / missing fields)
WebhookProcessingError   → 500 (internal failure)
"""


class WebhookVerificationError(Exception):
    """Signature/hash invalid or authenticity check failed."""


class WebhookPayloadError(Exception):
    """Malformed JSON or missing required fields."""


class WebhookProcessingError(Exception):
    """Internal processing failure (DB, unexpected)."""
