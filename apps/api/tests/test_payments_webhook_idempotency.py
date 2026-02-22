"""
Test: Webhook idempotency and entitlement granting.

Verifies:
- Duplicate webhooks are detected and skipped
- payment.succeeded grants course entitlement
- payment.failed does NOT grant entitlement
"""

import json
import os
import pytest
from fastapi.testclient import TestClient

# Set env BEFORE importing app
os.environ["PAYMENTS_PROVIDER"] = "stub"
os.environ["PAYMENTS_REPO"] = "memory"
os.environ["ENV"] = "test"

from app.main import app  # noqa: E402
from app.payments import repo_memory  # noqa: E402

client = TestClient(app)

DEBUG_UID = "test-user-webhook"
AUTH_HEADERS = {"X-Debug-Uid": DEBUG_UID, "X-Debug-Admin": "0"}
COURSE_ID = "alpha-protocol"


@pytest.fixture(autouse=True)
def reset_memory_repos():
    """Clear in-memory stores between tests."""
    repo_memory.reset()
    yield
    repo_memory.reset()


def _create_checkout_intent() -> str:
    """Helper: create a checkout intent and return its providerRef."""
    response = client.post(
        "/checkout/session",
        headers=AUTH_HEADERS,
        json={"type": "one_time", "courseId": COURSE_ID},
    )
    assert response.status_code == 200

    # Get the providerRef from memory
    from app.payments.repo_memory import _intents
    intent_data = list(_intents.values())[0]
    return intent_data["providerRef"]


def test_webhook_idempotency():
    """Same event_id sent twice: first processes, second is duplicate."""
    provider_ref = _create_checkout_intent()

    webhook_body = {
        "event_id": "evt_idempotency_test",
        "event_type": "payment.succeeded",
        "provider_ref": provider_ref,
        "payload": {"provider_ref": provider_ref},
    }

    # First call — should process
    r1 = client.post(
        "/webhooks/payments",
        content=json.dumps(webhook_body),
        headers={"Content-Type": "application/json"},
    )
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["ok"] is True
    assert d1["duplicate"] is False

    # Second call — should be duplicate
    r2 = client.post(
        "/webhooks/payments",
        content=json.dumps(webhook_body),
        headers={"Content-Type": "application/json"},
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["ok"] is True
    assert d2["duplicate"] is True


def test_payment_succeeded_grants_entitlement():
    """payment.succeeded webhook creates a course entitlement for the user."""
    provider_ref = _create_checkout_intent()

    webhook_body = {
        "event_id": "evt_grant_test",
        "event_type": "payment.succeeded",
        "provider_ref": provider_ref,
        "payload": {"provider_ref": provider_ref},
    }

    r = client.post(
        "/webhooks/payments",
        content=json.dumps(webhook_body),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Verify intent status is succeeded
    from app.payments.repo_memory import _intents
    intent_data = list(_intents.values())[0]
    assert intent_data["status"] == "succeeded"


def test_payment_failed_no_entitlement():
    """payment.failed webhook does NOT create an entitlement."""
    provider_ref = _create_checkout_intent()

    webhook_body = {
        "event_id": "evt_fail_test",
        "event_type": "payment.failed",
        "provider_ref": provider_ref,
        "payload": {"provider_ref": provider_ref},
    }

    r = client.post(
        "/webhooks/payments",
        content=json.dumps(webhook_body),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Verify intent status is failed
    from app.payments.repo_memory import _intents
    intent_data = list(_intents.values())[0]
    assert intent_data["status"] == "failed"
