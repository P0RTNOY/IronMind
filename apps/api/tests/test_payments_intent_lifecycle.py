"""
Test: Payment intent lifecycle.

Verifies that creating a checkout session:
- Returns a redirect URL
- Creates a pending intent in the repo
- Sets providerRef starting with "stub:"
"""

import json
import os
import pytest
from fastapi.testclient import TestClient

# Set env BEFORE importing app

from app.main import app  # noqa: E402
from app.payments.repo import get_repos  # noqa: E402
from app.payments import repo_memory  # noqa: E402

client = TestClient(app)

DEBUG_UID = "test-user-lifecycle"
AUTH_HEADERS = {"X-Debug-Uid": DEBUG_UID, "X-Debug-Admin": "0"}


@pytest.fixture(autouse=True)
def reset_memory_repos():
    """Clear in-memory stores between tests."""
    repo_memory.reset()
    yield
    repo_memory.reset()


def test_checkout_creates_pending_intent():
    """POST /checkout/session creates a pending intent and returns a redirect URL."""
    response = client.post(
        "/checkout/session",
        headers=AUTH_HEADERS,
        json={"type": "one_time", "courseId": "alpha-protocol"},
    )

    assert response.status_code == 200, f"Unexpected status: {response.status_code} {response.text}"
    data = response.json()

    # Response contains redirect URL
    assert "url" in data
    assert "/stub-checkout/redirect/pi_" in data["url"]

    # Intent exists in memory repo
    repos = get_repos()
    # Find the intent by scanning (memory repo is small in tests)
    from app.payments.repo_memory import _intents
    assert len(_intents) == 1

    intent_data = list(_intents.values())[0]
    assert intent_data["status"] == "pending"
    assert intent_data["uid"] == DEBUG_UID
    assert intent_data["scope"] == "course"
    assert intent_data["courseId"] == "alpha-protocol"
    assert intent_data["providerRef"].startswith("stub:")


def test_checkout_subscription():
    """POST /checkout/session with subscription type creates a membership intent."""
    response = client.post(
        "/checkout/session",
        headers=AUTH_HEADERS,
        json={"type": "subscription"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "url" in data

    from app.payments.repo_memory import _intents
    assert len(_intents) == 1

    intent_data = list(_intents.values())[0]
    assert intent_data["kind"] == "subscription"
    assert intent_data["scope"] == "membership"


def test_checkout_requires_course_id_for_one_time():
    """POST /checkout/session with one_time but no courseId returns 422."""
    response = client.post(
        "/checkout/session",
        headers=AUTH_HEADERS,
        json={"type": "one_time"},
    )

    assert response.status_code == 422
