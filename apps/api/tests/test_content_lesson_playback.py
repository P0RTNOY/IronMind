"""
Test: Video protection — entitlement-gated lesson playback.

Verifies:
1) Unauthenticated → 401
2) Non-entitled user → 403
3) Entitled user → 200 + provider + embedUrl
4) Missing lesson → 404
5) Lesson without video → 404

All dependencies (lesson repo, access service) are mocked.
"""

import os
from unittest.mock import patch

import pytest

# Set env BEFORE importing app modules
os.environ.setdefault("PAYMENTS_PROVIDER", "stub")
os.environ.setdefault("PAYMENTS_REPO", "memory")
os.environ.setdefault("ENV", "test")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

DEBUG_UID = "test-user-video"
AUTH_HEADERS = {"X-Debug-Uid": DEBUG_UID, "X-Debug-Admin": "0"}

# Fake lesson data
LESSON_WITH_VIDEO = {
    "id": "lesson-abc",
    "courseId": "course-101",
    "titleHe": "שיעור ראשון",
    "descriptionHe": "תיאור השיעור",
    "movementCategory": "squat",
    "tags": [],
    "vimeoVideoId": "123456789",
    "orderIndex": 1,
    "published": True,
}

LESSON_NO_VIDEO = {
    "id": "lesson-no-vid",
    "courseId": "course-101",
    "titleHe": "ללא וידאו",
    "descriptionHe": "שיעור ללא וידאו",
    "movementCategory": "hinge",
    "tags": [],
    "vimeoVideoId": None,
    "orderIndex": 2,
    "published": True,
}


def _mock_get_lesson(lesson_id: str):
    lessons = {
        "lesson-abc": LESSON_WITH_VIDEO,
        "lesson-no-vid": LESSON_NO_VIDEO,
    }
    return lessons.get(lesson_id)


def _mock_access_granted(uid: str, course_id: str) -> bool:
    return True


def _mock_access_denied(uid: str, course_id: str) -> bool:
    return False


# ── Tests ───────────────────────────────────────────────────────────

class TestContentLessonPlayback:

    def test_unauthenticated_returns_401(self):
        """No auth headers → 401."""
        response = client.get("/content/lessons/lesson-abc/playback")
        assert response.status_code == 401

    def test_non_entitled_returns_403(self):
        """User has no entitlement → 403."""
        with patch("app.routers.content.lessons_repo.get_lesson_admin", side_effect=_mock_get_lesson), \
             patch("app.routers.content.access_service.can_access_course", side_effect=_mock_access_denied):
            response = client.get(
                "/content/lessons/lesson-abc/playback",
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 403

    def test_entitled_returns_playback_200(self):
        """User with entitlement → 200 + provider + embedUrl."""
        with patch("app.routers.content.lessons_repo.get_lesson_admin", side_effect=_mock_get_lesson), \
             patch("app.routers.content.access_service.can_access_course", side_effect=_mock_access_granted):
            response = client.get(
                "/content/lessons/lesson-abc/playback",
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "vimeo"
        assert "player.vimeo.com/video/123456789" in data["embedUrl"]
        assert data["expiresIn"] is None

    def test_missing_lesson_returns_404(self):
        """Lesson ID doesn't exist → 404."""
        with patch("app.routers.content.lessons_repo.get_lesson_admin", return_value=None):
            response = client.get(
                "/content/lessons/nonexistent/playback",
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 404

    def test_lesson_without_video_returns_404(self):
        """Lesson exists but has no vimeoVideoId → 404."""
        with patch("app.routers.content.lessons_repo.get_lesson_admin", side_effect=_mock_get_lesson), \
             patch("app.routers.content.access_service.can_access_course", side_effect=_mock_access_granted):
            response = client.get(
                "/content/lessons/lesson-no-vid/playback",
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 404
