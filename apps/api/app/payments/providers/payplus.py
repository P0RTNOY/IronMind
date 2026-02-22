"""
PayPlus payment provider.

Implements PaymentProvider protocol for PayPlus hosted checkout + webhook verification.
Uses PayPlusClient for HTTP transport — no direct httpx calls here.
"""

import base64
import hashlib
import hmac
import json
import logging
from typing import Mapping

from app.config import settings
from app.payments import events
from app.payments.errors import WebhookPayloadError, WebhookVerificationError
from app.payments.models import PaymentIntent
from app.payments.provider import (
    PaymentProvider,
    ProviderCheckoutResult,
    VerifiedWebhook,
)
from app.payments.providers.payplus_client import PayPlusClient

logger = logging.getLogger(__name__)

PROVIDER_NAME = "payplus"


class PayPlusProvider:
    """PayPlus implementation of PaymentProvider."""

    def __init__(self):
        self.client = PayPlusClient(
            env=settings.PAYPLUS_ENV,
            api_key=settings.PAYPLUS_API_KEY,
            secret_key=settings.PAYPLUS_SECRET_KEY,
            timeout=settings.PAYPLUS_TIMEOUT_SECONDS,
        )
        self.secret_key = settings.PAYPLUS_SECRET_KEY
        self.verify_mode = settings.PAYPLUS_WEBHOOK_VERIFY_MODE
        self.callback_url = f"{settings.PUBLIC_WEBHOOK_BASE_URL}/webhooks/payments"

    # ── Checkout ────────────────────────────────────────────────────

    def create_one_time_checkout(self, intent: PaymentIntent) -> ProviderCheckoutResult:
        body = self._build_generate_link_body(
            payment_page_uid=settings.PAYPLUS_PAYMENT_PAGE_UID_ONE_TIME,
            intent=intent,
        )
        return self._call_generate_link(body)

    def create_subscription_checkout(self, intent: PaymentIntent) -> ProviderCheckoutResult:
        body = self._build_generate_link_body(
            payment_page_uid=settings.PAYPLUS_PAYMENT_PAGE_UID_SUBSCRIPTION,
            intent=intent,
        )
        body["create_token"] = True
        return self._call_generate_link(body)

    def _build_generate_link_body(
        self, payment_page_uid: str, intent: PaymentIntent
    ) -> dict:
        body = {
            "payment_page_uid": payment_page_uid,
            "refURL_callback": self.callback_url,
            "more_info": intent.id,  # tracing only — lookup uses provider_ref
        }
        # Only include redirect URLs if FRONTEND_ORIGIN is configured
        frontend = getattr(settings, "FRONTEND_ORIGIN", None)
        if frontend:
            body["refURL_success"] = f"{frontend}/success"
            body["refURL_failure"] = f"{frontend}/cancel"
        return body

    def _call_generate_link(self, body: dict) -> ProviderCheckoutResult:
        resp = self.client.post_json("/api/v1.0/PaymentPages/generateLink", body)
        data = resp.get("data", resp)

        payment_page_link = data.get("payment_page_link", "")
        payment_request_uid = data.get("payment_request_uid", "")

        if not payment_page_link or not payment_request_uid:
            raise RuntimeError(
                f"PayPlus generateLink response missing required fields: {list(data.keys())}"
            )

        return ProviderCheckoutResult(
            redirect_url=payment_page_link,
            provider_ref=payment_request_uid,
        )

    # ── Webhook verification ────────────────────────────────────────

    def verify_webhook(
        self,
        raw_body: bytes,
        headers: Mapping[str, str],
    ) -> VerifiedWebhook:
        """Parse and verify PayPlus IPN/callback webhook."""

        # 1. Parse JSON body (explicit UTF-8 decode for correctness)
        try:
            text = raw_body.decode("utf-8")
            data = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WebhookPayloadError(f"Invalid webhook JSON: {exc}") from exc

        # 2. Verify signature
        sig_valid = self._verify_signature(raw_body, headers)

        if not sig_valid:
            if self.verify_mode == "enforce":
                raise WebhookVerificationError(
                    "PayPlus webhook signature verification failed"
                )
            # log_only: already logged in _verify_signature, continue

        # 3. Extract required fields
        transaction = data.get("transaction", data)
        payment_request_uid = (
            data.get("payment_request_uid")
            or transaction.get("payment_request_uid")
            or ""
        )
        transaction_uid = (
            transaction.get("uid")
            or transaction.get("transaction_uid")
            or data.get("transaction_uid")
            or ""
        )

        if not payment_request_uid:
            raise WebhookPayloadError(
                "PayPlus webhook missing payment_request_uid"
            )

        # 4. Build stable event_id (unique per transaction attempt)
        event_id = f"{payment_request_uid}:{transaction_uid}" if transaction_uid else payment_request_uid

        # 5. Map to canonical event type
        event_type = self._map_event_type(data if "status_code" in data else transaction)

        # 6. Normalize payload
        payload = {
            "provider_ref": payment_request_uid,
            "transaction_uid": transaction_uid,
            "raw_status_code": transaction.get("status_code", data.get("status_code", "")),
            "raw_status": transaction.get("status", data.get("status", "")),
        }

        # Include provider_subscription_id if available (for recurring)
        recurring_id = (
            data.get("recurring_id")
            or transaction.get("recurring_id")
            or data.get("token_uid")
            or transaction.get("token_uid")
        )
        if recurring_id:
            payload["provider_subscription_id"] = str(recurring_id)

        # Store raw payload for debugging and Phase 1.5 token discovery
        payload["raw"] = {
            "transaction": transaction,
            "payment_request_uid": payment_request_uid,
            "top_level_keys": list(data.keys()),
        }

        return VerifiedWebhook(
            provider=PROVIDER_NAME,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
        )

    def _verify_signature(
        self, raw_body: bytes, headers: Mapping[str, str]
    ) -> bool:
        """
        Verify HMAC-SHA256 signature per PayPlus docs.
        Case-insensitive header lookup, hex + base64 tolerance.
        """
        # Normalize headers to lowercase
        lower_headers = {k.lower(): v for k, v in headers.items()}

        # Probe known header names
        signature = None
        for name in ("hash", "x-payplus-hash", "x-payplus-signature"):
            signature = lower_headers.get(name)
            if signature:
                break

        if not signature:
            logger.warning("No signature header found in PayPlus webhook")
            return False

        signature = signature.strip()  # some providers include trailing whitespace

        # Compute expected HMAC-SHA256
        mac = hmac.new(self.secret_key.encode(), raw_body, hashlib.sha256)

        # Try hex comparison first
        if hmac.compare_digest(mac.hexdigest(), signature):
            return True

        # Fallback: try base64 comparison
        expected_b64 = base64.b64encode(mac.digest()).decode()
        if hmac.compare_digest(expected_b64, signature):
            return True

        # Mismatch — log details in log_only mode
        if self.verify_mode == "log_only":
            logger.warning(
                "PayPlus signature mismatch (log_only mode)",
                extra={
                    "sig_len": len(signature),
                    "expected_hex_len": len(mac.hexdigest()),
                    "looks_base64": signature.endswith("="),
                },
            )

        return False

    def _map_event_type(self, data: dict) -> str:
        """
        Map PayPlus status fields to canonical event types.

        Priority:
        1. Explicit recurring lifecycle fields
        2. Standard payment approval/decline
        3. Unknown → service ignores
        """
        status_code = str(data.get("status_code", ""))
        status = str(data.get("status", "")).lower()
        transaction_type = str(data.get("type", "")).lower()

        # 1. Recurring lifecycle (secondary until confirmed from sandbox)
        if transaction_type in ("recurring_renewal",) and status in ("approved", "success"):
            return events.SUB_RENEWED
        if transaction_type in ("recurring_canceled", "recurring_expired"):
            return events.SUB_CANCELED
        if transaction_type in ("recurring_renewal",) and status in ("declined", "failed"):
            return events.SUB_PAST_DUE

        # 2. Standard payment approval/decline (primary for Phase 1)
        if status_code == "000" or status in ("approved", "success"):
            return events.PAYMENT_SUCCEEDED
        if status in ("declined", "failed", "error") or (status_code and status_code != "000"):
            return events.PAYMENT_FAILED

        # 3. Unknown → service returns {"ignored": true}
        return f"payplus.unknown.{status_code or status or 'none'}"
