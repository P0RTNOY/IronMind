"""
Unit tests for Vimeo admin verification (Phase 2.7).
Mocks outer httpx calls to ensure no real network traffic.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.config import settings
from app.services import vimeo_client, vimeo_verify

client = TestClient(app)

MOCK_VIDEO_ID = "123456789"
MOCK_LESSON_ID = "lesson_123"

@pytest.fixture(autouse=True)
def _setup_env():
    # Force enable verify and set mock token
    settings.VIMEO_VERIFY_ENABLED = True
    settings.VIMEO_ACCESS_TOKEN = "test_token"
    settings.VIMEO_REQUIRED_EMBED_ORIGINS = ["ironmind.app", "www.ironmind.app"]
    yield
    settings.VIMEO_VERIFY_ENABLED = False


# Admin headers
HEADERS = {"X-Debug-Admin": "1", "X-Debug-Uid": "admin_uid"}
USER_HEADERS = {"X-Debug-Uid": "user_uid"}


def test_admin_auth_required():
    # Non-admin request
    response = client.post(f"/admin/vimeo/lessons/{MOCK_LESSON_ID}/verify", headers=USER_HEADERS)
    assert response.status_code == 403

def test_verification_disabled():
    settings.VIMEO_VERIFY_ENABLED = False
    response = client.post(f"/admin/vimeo/lessons/{MOCK_LESSON_ID}/verify", headers=HEADERS)
    assert response.status_code == 501
    assert response.json() == {"detail": "vimeo_verify_disabled"}


@patch("app.routers.admin_vimeo.lessons_repo")
@patch("app.services.vimeo_verify.vimeo_client.get_embed_domains")
@patch("app.services.vimeo_verify.vimeo_client.get_video")
def test_verify_success(mock_get_video, mock_get_domains, mock_repo):
    # Mock Lesson Repo
    mock_repo.get_lesson_admin.return_value = {"id": MOCK_LESSON_ID, "vimeoVideoId": MOCK_VIDEO_ID}
    
    # Mock Vimeo API Success
    mock_get_video.return_value = {"privacy": {"embed": "whitelist"}}
    mock_get_domains.return_value = ["ironmind.app", "www.ironmind.app", "other.app"]

    response = client.post(f"/admin/vimeo/lessons/{MOCK_LESSON_ID}/verify", headers=HEADERS)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["missing_domains"] == []
    assert data["embed_mode"] == "whitelist"
    
    # Assert DB update was called
    mock_repo.update_lesson_verification.assert_called_once()
    args, _ = mock_repo.update_lesson_verification.call_args
    assert args[0] == MOCK_LESSON_ID
    assert args[1]["vimeoVerifyOk"] is True


@patch("app.routers.admin_vimeo.lessons_repo")
@patch("app.services.vimeo_verify.vimeo_client.get_embed_domains")
@patch("app.services.vimeo_verify.vimeo_client.get_video")
def test_verify_missing_domains(mock_get_video, mock_get_domains, mock_repo):
    # Mock Lesson Repo
    mock_repo.get_lesson_admin.return_value = {"id": MOCK_LESSON_ID, "vimeoVideoId": MOCK_VIDEO_ID}
    
    # Mock Vimeo API missing domains
    mock_get_video.return_value = {"privacy": {"embed": "whitelist"}}
    mock_get_domains.return_value = ["ironmind.app"]

    response = client.post(f"/admin/vimeo/lessons/{MOCK_LESSON_ID}/verify", headers=HEADERS)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["missing_domains"] == ["www.ironmind.app"]
    
    mock_repo.update_lesson_verification.assert_called_once()


@patch("app.routers.admin_vimeo.lessons_repo")
@patch("app.services.vimeo_verify.vimeo_client.get_embed_domains")
@patch("app.services.vimeo_verify.vimeo_client.get_video")
def test_verify_bad_embed_mode(mock_get_video, mock_get_domains, mock_repo):
    # Mock Lesson Repo
    mock_repo.get_lesson_admin.return_value = {"id": MOCK_LESSON_ID, "vimeoVideoId": MOCK_VIDEO_ID}
    
    # Mock Vimeo API bad mode
    mock_get_video.return_value = {"privacy": {"embed": "public"}}
    mock_get_domains.return_value = ["ironmind.app", "www.ironmind.app"]

    response = client.post(f"/admin/vimeo/lessons/{MOCK_LESSON_ID}/verify", headers=HEADERS)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Unexpected embed mode: public" in data["warnings"]


def test_normalize_video_id():
    assert vimeo_client._normalize_video_id("123456789") == "123456789"
    assert vimeo_client._normalize_video_id(" /videos/123456789 ") == "123456789"
    assert vimeo_client._normalize_video_id("https://vimeo.com/123456789") == "123456789"
    assert vimeo_client._normalize_video_id("https://player.vimeo.com/video/123456789") == "123456789"

def test_normalize_domain():
    assert vimeo_verify._normalize_domain("http://IronMind.app") == "ironmind.app"
    assert vimeo_verify._normalize_domain("https://www.ironmind.app/") == "www.ironmind.app"
    assert vimeo_verify._normalize_domain("ironmind.app:8080") == "ironmind.app"

@patch("app.routers.admin_vimeo.lessons_repo")
@patch("app.services.vimeo_verify.vimeo_client.get_video")
def test_verify_api_error(mock_get_video, mock_repo):
    # Mock Lesson Repo
    mock_repo.get_lesson_admin.return_value = {"id": MOCK_LESSON_ID, "vimeoVideoId": MOCK_VIDEO_ID}
    
    # Mock Vimeo API exception
    from app.services import vimeo_client
    mock_get_video.side_effect = vimeo_client.VimeoAPIError("Invalid token", status_code=401)

    response = client.post(f"/admin/vimeo/lessons/{MOCK_LESSON_ID}/verify", headers=HEADERS)
    
    assert response.status_code == 403
    assert "Vimeo API Error" in response.json()["detail"]
