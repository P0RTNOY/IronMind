"""
Stub payment provider for deterministic testing.

Returns predictable redirect URLs and provider refs.
verify_webhook parses JSON directly — no signature check.
"""

import json
from typing import Mapping

from app.payments import events
from app.payments.models import PaymentIntent
from app.payments.provider import (
    PaymentProvider,
    ProviderCheckoutResult,
    VerifiedWebhook,
)

PROVIDER_NAME = "stub"


class StubProvider:
    """Stub implementation of PaymentProvider for Phase 0 testing."""

    def create_one_time_checkout(self, intent: PaymentIntent) -> ProviderCheckoutResult:
        return ProviderCheckoutResult(
            redirect_url=f"/stub-checkout/redirect/{intent.id}",
            provider_ref=f"stub:{intent.id}",
        )

    def create_subscription_checkout(self, intent: PaymentIntent) -> ProviderCheckoutResult:
        return ProviderCheckoutResult(
            redirect_url=f"/stub-checkout/redirect/{intent.id}",
            provider_ref=f"stub:{intent.id}",
        )

    def verify_webhook(
        self,
        raw_body: bytes,
        headers: Mapping[str, str],
    ) -> VerifiedWebhook:
        """
        Parse JSON body directly. No signature verification.

        Expected body shape:
        {
            "event_id": "evt_xxx",
            "event_type": "payment.succeeded",
            "provider_ref": "stub:pi_xxx",
            "payload": { ... }
        }
        """
        try:
            data = json.loads(raw_body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"Invalid webhook body: {exc}") from exc

        event_id = data.get("event_id")
        event_type = data.get("event_type")
        if not event_id or not event_type:
            raise ValueError("Webhook body must include event_id and event_type")

        # Validate canonical event types — accept but flag unknown ones
        # (In Phase 1, providers should map native events to canonical types.
        #  Accept-and-ignore prevents retry storms from providers.)
        # The service layer will handle unrecognized types gracefully.

        # Extract provider_ref: top-level first, then fallback to payload
        provider_ref = data.get("provider_ref")
        payload = data.get("payload", {})
        if not provider_ref:
            provider_ref = payload.get("provider_ref")
        if provider_ref:
            payload["provider_ref"] = provider_ref

        return VerifiedWebhook(
            provider=PROVIDER_NAME,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
        )
