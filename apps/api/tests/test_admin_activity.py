"""
Tests for the admin activity endpoint — deterministic.

Uses Starlette TestClient (in-process) so we can monkeypatch
the activity_events repo at the router layer. No real Firestore.
"""

import pytest
from starlette.testclient import TestClient
from app.main import app
from app.routers import admin_activity


FAKE_EVENTS = [
    {
        "id": "evt_1",
        "type": "access_check",
        "uid": "test-user",
        "courseId": "course_1",
        "lessonId": None,
        "planId": None,
        "createdAt": "2025-01-01T00:00:00Z",
    },
    {
        "id": "evt_2",
        "type": "content_playback",
        "uid": "test-user",
        "courseId": "course_1",
        "lessonId": "lesson_1",
        "planId": None,
        "createdAt": "2025-01-01T01:00:00Z",
    },
]


@pytest.fixture
def test_client():
    """In-process test client — monkeypatching works here."""
    return TestClient(app)


def test_activity_forbidden_for_non_admin(test_client):
    """GET /admin/activity requires admin auth."""
    r = test_client.get("/admin/activity", headers={"X-Debug-Uid": "test-user"})
    assert r.status_code == 403, r.text


def test_activity_returns_list_for_admin(test_client, monkeypatch):
    """GET /admin/activity returns a list of events for admin users."""
    monkeypatch.setattr(
        admin_activity.activity_events, "list_recent",
        lambda limit=50: FAKE_EVENTS,
    )

    r = test_client.get(
        "/admin/activity",
        headers={"X-Debug-Uid": "test-admin", "X-Debug-Admin": "1"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["type"] == "access_check"
    assert data[1]["type"] == "content_playback"


def test_activity_empty_when_no_events(test_client, monkeypatch):
    """GET /admin/activity returns empty list when no events exist."""
    monkeypatch.setattr(
        admin_activity.activity_events, "list_recent",
        lambda limit=50: [],
    )

    r = test_client.get(
        "/admin/activity",
        headers={"X-Debug-Uid": "test-admin", "X-Debug-Admin": "1"},
    )
    assert r.status_code == 200, r.text
    assert r.json() == []


def test_activity_respects_limit(test_client, monkeypatch):
    """GET /admin/activity rejects limit > 200."""
    r = test_client.get(
        "/admin/activity?limit=300",
        headers={"X-Debug-Uid": "test-admin", "X-Debug-Admin": "1"},
    )
    assert r.status_code == 422, r.text
