"""
Test: Content protection — entitlement-gated plan PDF downloads.

Verifies:
1) Unauthenticated → 401
2) Non-entitled user → 403
3) Entitled user (course) → 200 + signed URL
4) Entitled user (membership) → 200
5) Missing plan → 404
6) Plan without pdfPath → 404
7) Invalid pdfPath (traversal) → 400

All dependencies (plan repo, access service, storage) are mocked.
"""

import os
from unittest.mock import patch

import pytest

# Set env BEFORE importing app modules

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

DEBUG_UID = "test-user-content"
AUTH_HEADERS = {"X-Debug-Uid": DEBUG_UID, "X-Debug-Admin": "0"}

MOCK_SIGNED_URL = "https://storage.googleapis.com/test-bucket/plans/test.pdf?X-Goog-Signature=abc123"

# Fake plan data
PLAN_WITH_PDF = {
    "id": "plan-abc",
    "courseId": "course-101",
    "titleHe": "תוכנית אימון",
    "descriptionHe": "תוכנית בסיסית",
    "tags": [],
    "pdfPath": "plans/course-101/test.pdf",
    "published": True,
}

PLAN_WITHOUT_PDF = {
    "id": "plan-no-pdf",
    "courseId": "course-101",
    "titleHe": "ללא PDF",
    "descriptionHe": "תוכנית ללא קובץ",
    "tags": [],
    "pdfPath": None,
    "published": True,
}

PLAN_WITH_BAD_PATH = {
    "id": "plan-bad-path",
    "courseId": "course-101",
    "titleHe": "נתיב רע",
    "descriptionHe": "נתיב לא חוקי",
    "tags": [],
    "pdfPath": "../secret/passwords.pdf",
    "published": True,
}


def _mock_get_plan(plan_id: str):
    """Mock plan lookup."""
    plans = {
        "plan-abc": PLAN_WITH_PDF,
        "plan-no-pdf": PLAN_WITHOUT_PDF,
        "plan-bad-path": PLAN_WITH_BAD_PATH,
    }
    return plans.get(plan_id)


def _mock_access_granted(uid: str, course_id: str) -> bool:
    return True


def _mock_access_denied(uid: str, course_id: str) -> bool:
    return False


def _mock_signed_url(blob_name: str, ttl_seconds=None, bucket_name=None) -> str:
    return MOCK_SIGNED_URL


# ── Tests ───────────────────────────────────────────────────────────

class TestContentPlanDownload:

    def test_unauthenticated_returns_401(self):
        """No auth headers → 401."""
        response = client.get("/content/plans/plan-abc/download")
        assert response.status_code == 401

    def test_non_entitled_returns_403(self):
        """User has no entitlement → 403."""
        with patch("app.routers.content.plans_repo.get_plan_admin", side_effect=_mock_get_plan), \
             patch("app.routers.content.access_service.can_access_course", side_effect=_mock_access_denied):
            response = client.get(
                "/content/plans/plan-abc/download",
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 403

    def test_entitled_returns_signed_url_200(self):
        """User with course entitlement → 200 + signed URL."""
        with patch("app.routers.content.plans_repo.get_plan_admin", side_effect=_mock_get_plan), \
             patch("app.routers.content.access_service.can_access_course", side_effect=_mock_access_granted), \
             patch("app.routers.content.generate_signed_download_url", side_effect=_mock_signed_url):
            response = client.get(
                "/content/plans/plan-abc/download",
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == MOCK_SIGNED_URL
        assert data["expiresIn"] == 900  # default TTL

    def test_membership_grants_access_200(self):
        """User with membership (can_access_course returns True) → 200."""
        with patch("app.routers.content.plans_repo.get_plan_admin", side_effect=_mock_get_plan), \
             patch("app.routers.content.access_service.can_access_course", return_value=True), \
             patch("app.routers.content.generate_signed_download_url", side_effect=_mock_signed_url):
            response = client.get(
                "/content/plans/plan-abc/download",
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 200
        assert "url" in response.json()

    def test_missing_plan_returns_404(self):
        """Plan ID doesn't exist → 404."""
        with patch("app.routers.content.plans_repo.get_plan_admin", return_value=None):
            response = client.get(
                "/content/plans/nonexistent/download",
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 404

    def test_plan_without_pdf_returns_404(self):
        """Plan exists but has no pdfPath → 404."""
        with patch("app.routers.content.plans_repo.get_plan_admin", side_effect=_mock_get_plan), \
             patch("app.routers.content.access_service.can_access_course", side_effect=_mock_access_granted):
            response = client.get(
                "/content/plans/plan-no-pdf/download",
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 404

    def test_invalid_pdf_path_returns_400(self):
        """Plan with traversal path → 400."""
        with patch("app.routers.content.plans_repo.get_plan_admin", side_effect=_mock_get_plan), \
             patch("app.routers.content.access_service.can_access_course", side_effect=_mock_access_granted):
            response = client.get(
                "/content/plans/plan-bad-path/download",
                headers=AUTH_HEADERS,
            )
        assert response.status_code == 400
