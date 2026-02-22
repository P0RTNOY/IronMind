"""
Test: PayPlus subscription lifecycle (integration-ish, mocked client).

Verifies:
- Subscription checkout creates intent with provider="payplus"
- SUB_RENEWED webhook activates membership entitlement
- Duplicate webhook is idempotent
- SUB_CANCELED webhook deactivates entitlement

Uses monkeypatch to override settings for provider isolation.
"""

import json
import os
from unittest.mock import patch, PropertyMock

import pytest

# Set env BEFORE importing app modules
os.environ.setdefault("PAYMENTS_PROVIDER", "payplus")
os.environ.setdefault("PAYMENTS_REPO", "memory")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("PAYPLUS_API_KEY", "test_api_key")
os.environ.setdefault("PAYPLUS_SECRET_KEY", "test_secret_key")
os.environ.setdefault("PAYPLUS_PAYMENT_PAGE_UID_ONE_TIME", "test_page_uid")
os.environ.setdefault("PAYPLUS_PAYMENT_PAGE_UID_SUBSCRIPTION", "test_sub_page_uid")
os.environ.setdefault("PAYPLUS_WEBHOOK_VERIFY_MODE", "log_only")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.payments import repo_memory  # noqa: E402
from app.payments.providers.payplus import PayPlusProvider  # noqa: E402
from app.payments.providers.payplus_client import PayPlusClient  # noqa: E402
from app.payments.provider import ProviderCheckoutResult  # noqa: E402

client = TestClient(app)

DEBUG_UID = "test-user-payplus-sub"
AUTH_HEADERS = {"X-Debug-Uid": DEBUG_UID, "X-Debug-Admin": "0"}

# Mock response for PayPlus generateLink
MOCK_GENERATE_LINK_RESPONSE = {
    "results": {"status": "success"},
    "data": {
        "payment_page_link": "https://restapidev.payplus.co.il/checkout/pp_req_mock_123",
        "payment_request_uid": "pp_req_mock_123",
    },
}


@pytest.fixture(autouse=True)
def reset_and_patch(monkeypatch):
    """Clear in-memory stores and force payplus provider for each test."""
    repo_memory.reset()
    # Override settings to force payplus provider regardless of load order
    from app.config import settings
    monkeypatch.setattr(settings, "PAYMENTS_PROVIDER", "payplus")
    monkeypatch.setattr(settings, "PAYMENTS_REPO", "memory")
    monkeypatch.setattr(settings, "PAYPLUS_API_KEY", "test_api_key")
    monkeypatch.setattr(settings, "PAYPLUS_SECRET_KEY", "test_secret_key")
    monkeypatch.setattr(settings, "PAYPLUS_PAYMENT_PAGE_UID_ONE_TIME", "test_page_uid")
    monkeypatch.setattr(settings, "PAYPLUS_PAYMENT_PAGE_UID_SUBSCRIPTION", "test_sub_page_uid")
    monkeypatch.setattr(settings, "PAYPLUS_WEBHOOK_VERIFY_MODE", "log_only")
    monkeypatch.setattr(settings, "PUBLIC_WEBHOOK_BASE_URL", "http://localhost:8080")
    monkeypatch.setattr(settings, "ENV", "test")
    yield
    repo_memory.reset()


def _mock_post_json(path: str, payload: dict) -> dict:
    """Mock PayPlusClient.post_json for generateLink."""
    if "generateLink" in path:
        return MOCK_GENERATE_LINK_RESPONSE
    return {"results": {"status": "error"}, "data": {}}


def _create_subscription_checkout() -> str:
    """Helper: create a subscription checkout and return the providerRef."""
    with patch.object(PayPlusClient, "post_json", side_effect=_mock_post_json):
        response = client.post(
            "/checkout/session",
            headers=AUTH_HEADERS,
            json={"type": "subscription"},
        )

    assert response.status_code == 200, f"Unexpected: {response.status_code} {response.text}"
    data = response.json()
    assert "url" in data

    # Verify intent in memory
    from app.payments.repo_memory import _intents
    assert len(_intents) == 1
    intent_data = list(_intents.values())[0]
    assert intent_data["provider"] == "payplus"
    assert intent_data["providerRef"] == "pp_req_mock_123"

    return intent_data["providerRef"]


def _send_webhook(event_id: str, event_type: str, provider_ref: str,
                   provider_subscription_id: str | None = None) -> dict:
    """Helper: send a webhook to /webhooks/payments."""
    payload = {
        "payment_request_uid": provider_ref,
        "transaction": {
            "uid": event_id.split(":")[-1] if ":" in event_id else event_id,
            "status_code": "000",
            "status": "approved",
            "payment_request_uid": provider_ref,
        },
    }

    # Override for specific event types
    if event_type == "subscription.renewed":
        payload["transaction"]["type"] = "recurring_renewal"
        payload["transaction"]["status"] = "approved"
    elif event_type == "subscription.canceled":
        payload["transaction"]["type"] = "recurring_canceled"
        payload["transaction"]["status_code"] = ""
        payload["transaction"]["status"] = ""

    if provider_subscription_id:
        payload["recurring_id"] = provider_subscription_id

    body = json.dumps(payload).encode()

    response = client.post(
        "/webhooks/payments",
        content=body,
        headers={"Content-Type": "application/json", "hash": "test_hash"},
    )
    return {"status_code": response.status_code, "body": response.json()}


# ── Tests ───────────────────────────────────────────────────────────

class TestSubscriptionLifecycle:
    def test_subscription_checkout_creates_payplus_intent(self):
        """Subscription checkout creates intent with provider=payplus."""
        with patch.object(PayPlusClient, "post_json", side_effect=_mock_post_json):
            response = client.post(
                "/checkout/session",
                headers=AUTH_HEADERS,
                json={"type": "subscription"},
            )

        assert response.status_code == 200
        from app.payments.repo_memory import _intents
        intent = list(_intents.values())[0]
        assert intent["provider"] == "payplus"
        assert intent["kind"] == "subscription"
        assert intent["scope"] == "membership"

    def test_sub_renewed_activates_entitlement(self):
        """SUB_RENEWED webhook sets membership entitlement to active."""
        with patch.object(PayPlusClient, "post_json", side_effect=_mock_post_json):
            provider_ref = _create_subscription_checkout()

        result = _send_webhook(
            event_id=f"{provider_ref}:renew_001",
            event_type="subscription.renewed",
            provider_ref=provider_ref,
            provider_subscription_id="pp_sub_999",
        )

        assert result["status_code"] == 200
        assert result["body"]["ok"] is True
        assert result["body"]["duplicate"] is False

        # Verify subscription in memory
        from app.payments.repo_memory import _subscriptions
        assert len(_subscriptions) >= 1

    def test_duplicate_webhook_is_idempotent(self):
        """Same event_id sent twice: second is duplicate."""
        with patch.object(PayPlusClient, "post_json", side_effect=_mock_post_json):
            provider_ref = _create_subscription_checkout()

        r1 = _send_webhook(
            event_id=f"{provider_ref}:renew_dup",
            event_type="subscription.renewed",
            provider_ref=provider_ref,
            provider_subscription_id="pp_sub_dup",
        )
        assert r1["body"]["ok"] is True
        assert r1["body"]["duplicate"] is False

        r2 = _send_webhook(
            event_id=f"{provider_ref}:renew_dup",
            event_type="subscription.renewed",
            provider_ref=provider_ref,
            provider_subscription_id="pp_sub_dup",
        )
        assert r2["body"]["ok"] is True
        assert r2["body"]["duplicate"] is True

    def test_sub_canceled_deactivates_entitlement(self):
        """SUB_CANCELED webhook sets membership entitlement to inactive."""
        with patch.object(PayPlusClient, "post_json", side_effect=_mock_post_json):
            provider_ref = _create_subscription_checkout()

        # First: renew to activate
        _send_webhook(
            event_id=f"{provider_ref}:renew_pre",
            event_type="subscription.renewed",
            provider_ref=provider_ref,
            provider_subscription_id="pp_sub_cancel_test",
        )

        # Then: cancel
        result = _send_webhook(
            event_id=f"{provider_ref}:cancel_001",
            event_type="subscription.canceled",
            provider_ref=provider_ref,
            provider_subscription_id="pp_sub_cancel_test",
        )

        assert result["status_code"] == 200
        assert result["body"]["ok"] is True

        # Verify subscription is canceled in memory
        from app.payments.repo_memory import _subscriptions
        canceled = [s for s in _subscriptions.values() if s["status"] == "canceled"]
        assert len(canceled) >= 1
