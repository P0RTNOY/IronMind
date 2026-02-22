"""
Test: PayPlus verify_webhook mapping + signature verification.

Creates PayPlusProvider directly (not via registry) to test webhook parsing
in isolation. Overrides secret_key and verify_mode after construction.
"""

import hashlib
import hmac as hmac_mod
import json
import os
import pytest

# Set env BEFORE importing app modules
os.environ.setdefault("PAYPLUS_API_KEY", "test_api_key")
os.environ.setdefault("PAYPLUS_SECRET_KEY", "test_secret_key")
os.environ.setdefault("PAYPLUS_PAYMENT_PAGE_UID_ONE_TIME", "test_page_uid")
os.environ.setdefault("PAYPLUS_PAYMENT_PAGE_UID_SUBSCRIPTION", "test_sub_page_uid")
os.environ.setdefault("PAYPLUS_WEBHOOK_VERIFY_MODE", "log_only")

from app.payments.errors import WebhookVerificationError  # noqa: E402
from app.payments.providers.payplus import PayPlusProvider  # noqa: E402
from app.payments import events  # noqa: E402

# The secret key used for signing in tests
SECRET_KEY = "test_secret_key"


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch):
    """Ensure settings are correct even when running with Phase 0 tests."""
    from app.config import settings
    monkeypatch.setattr(settings, "PAYPLUS_API_KEY", "test_api_key")
    monkeypatch.setattr(settings, "PAYPLUS_SECRET_KEY", SECRET_KEY)
    monkeypatch.setattr(settings, "PAYPLUS_WEBHOOK_VERIFY_MODE", "log_only")
    monkeypatch.setattr(settings, "PAYPLUS_ENV", "sandbox")
    monkeypatch.setattr(settings, "PAYPLUS_TIMEOUT_SECONDS", 15)
    monkeypatch.setattr(settings, "PUBLIC_WEBHOOK_BASE_URL", "http://localhost:8080")
    monkeypatch.setattr(settings, "PAYPLUS_PAYMENT_PAGE_UID_ONE_TIME", "test_page_uid")
    monkeypatch.setattr(settings, "PAYPLUS_PAYMENT_PAGE_UID_SUBSCRIPTION", "test_sub_page_uid")


def _make_payload(**overrides) -> dict:
    """Build a minimal PayPlus-style webhook payload."""
    base = {
        "payment_request_uid": "pp_req_test_123",
        "transaction": {
            "uid": "txn_456",
            "status_code": "000",
            "status": "approved",
            "payment_request_uid": "pp_req_test_123",
        },
    }
    base.update(overrides)
    return base


def _sign_body(body: bytes, secret: str) -> str:
    """Generate valid HMAC-SHA256 hex signature."""
    return hmac_mod.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _make_provider(verify_mode: str = "log_only") -> PayPlusProvider:
    """Create a PayPlusProvider with overridden verify mode and secret."""
    provider = PayPlusProvider()
    provider.verify_mode = verify_mode
    provider.secret_key = SECRET_KEY
    return provider


# ── Tests ───────────────────────────────────────────────────────────

class TestVerifyWebhookSignature:
    def test_log_only_invalid_signature_accepted(self):
        provider = _make_provider("log_only")
        body = json.dumps(_make_payload()).encode()
        headers = {"hash": "invalid_signature", "content-type": "application/json"}

        result = provider.verify_webhook(body, headers)

        assert result.provider == "payplus"
        assert result.event_id == "pp_req_test_123:txn_456"
        assert result.payload["provider_ref"] == "pp_req_test_123"

    def test_enforce_invalid_signature_raises(self):
        provider = _make_provider("enforce")
        body = json.dumps(_make_payload()).encode()
        headers = {"hash": "invalid_signature", "content-type": "application/json"}

        with pytest.raises(WebhookVerificationError):
            provider.verify_webhook(body, headers)

    def test_enforce_valid_signature_accepted(self):
        provider = _make_provider("enforce")
        body = json.dumps(_make_payload()).encode()
        sig = _sign_body(body, SECRET_KEY)
        headers = {"hash": sig, "content-type": "application/json"}

        result = provider.verify_webhook(body, headers)

        assert result.provider == "payplus"
        assert result.event_type == events.PAYMENT_SUCCEEDED


class TestEventTypeMapping:
    def test_status_code_000_maps_to_succeeded(self):
        provider = _make_provider("log_only")
        body = json.dumps(_make_payload()).encode()
        headers = {"hash": "anything"}

        result = provider.verify_webhook(body, headers)
        assert result.event_type == events.PAYMENT_SUCCEEDED

    def test_declined_status_maps_to_failed(self):
        provider = _make_provider("log_only")
        payload = _make_payload()
        payload["transaction"]["status_code"] = "999"
        payload["transaction"]["status"] = "declined"
        body = json.dumps(payload).encode()
        headers = {"hash": "anything"}

        result = provider.verify_webhook(body, headers)
        assert result.event_type == events.PAYMENT_FAILED


class TestPayloadNormalization:
    def test_provider_ref_always_set(self):
        provider = _make_provider("log_only")
        body = json.dumps(_make_payload()).encode()
        headers = {"hash": "anything"}

        result = provider.verify_webhook(body, headers)
        assert result.payload["provider_ref"] == "pp_req_test_123"

    def test_event_id_combines_request_and_transaction(self):
        provider = _make_provider("log_only")
        body = json.dumps(_make_payload()).encode()
        headers = {"hash": "anything"}

        result = provider.verify_webhook(body, headers)
        assert result.event_id == "pp_req_test_123:txn_456"
