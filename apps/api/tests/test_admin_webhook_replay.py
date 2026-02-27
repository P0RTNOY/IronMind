import pytest
import copy
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.deps import require_admin
from app.payments import service

client = TestClient(app)

@pytest.fixture
def override_admin_auth():
    """Bypasses Firebase to force admin status for testing."""
    def mock_require_admin():
        return {"uid": "test_admin", "is_admin": True}
        
    app.dependency_overrides[require_admin] = mock_require_admin
    yield
    app.dependency_overrides.clear()

def test_webhook_replay_requires_admin():
    """Ensure non-admins get 403 Forbidden."""
    res = client.post("/admin/payments/replay", json={
        "provider": "payplus",
        "payload": {"test": "data"}
    })
    
    assert res.status_code == 401

def test_webhook_replay_success(override_admin_auth, monkeypatch):
    """Ensure an admin can replay a valid webhook and results propagate."""
    def mock_handle_webhook(raw_body, headers):
        assert b"test_payload" in raw_body
        assert headers["hash"] == "replay"
        return {"ok": True, "duplicate": False, "ignored": True}

    monkeypatch.setattr(service, "handle_webhook", mock_handle_webhook)
    
    res = client.post("/admin/payments/replay", json={
        "provider": "payplus",
        "payload": {"test_payload": True}
    })
    
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["result"]["ignored"] is True
    assert "payload_size_bytes=" in data["notes"][0]

def test_webhook_replay_too_large(override_admin_auth):
    """Ensure payloads > 50KB are rejected with HTTP 413."""
    huge_payload = {"data": "x" * 60_000}
    
    res = client.post("/admin/payments/replay", json={
        "provider": "payplus",
        "payload": huge_payload
    })
    
    assert res.status_code == 413
    assert "too large" in res.json()["detail"].lower()

def test_webhook_replay_force_log_only_restores_setting(override_admin_auth, monkeypatch):
    """Ensure force_log_only temporarily modifies the setting and restores it."""
    
    original = getattr(settings, "PAYPLUS_WEBHOOK_VERIFY_MODE", "log_only")
    settings.PAYPLUS_WEBHOOK_VERIFY_MODE = "enforce"
    
    settings_during_call = []

    def mock_handle_webhook(raw_body, headers):
        settings_during_call.append(settings.PAYPLUS_WEBHOOK_VERIFY_MODE)
        return {"ok": True}

    monkeypatch.setattr(service, "handle_webhook", mock_handle_webhook)
    
    try:
        res = client.post("/admin/payments/replay", json={
            "provider": "payplus",
            "force_log_only": True,
            "payload": {"test": True}
        })
        
        assert res.status_code == 200
        assert settings_during_call[0] == "log_only"
        
        # Must be restored!
        assert settings.PAYPLUS_WEBHOOK_VERIFY_MODE == "enforce"
    finally:
        settings.PAYPLUS_WEBHOOK_VERIFY_MODE = original


def test_webhook_replay_intent_lookup(override_admin_auth, monkeypatch):
    """Ensure intent lookup works and classifies mutation risk correctly."""
    from tests.helpers.fixture_loader import load_json_fixture
    approved_payload = load_json_fixture("payplus/approved.json")
    unmapped_payload = load_json_fixture("payplus/unmapped.json")

    # Mock handle_webhook to simulate real behavior
    def mock_handle_webhook(raw_body, headers):
        if b"txn_unmapped_001" in raw_body:
            return {"ok": True, "duplicate": False, "ignored": True, "unmapped": True}
        return {"ok": True, "duplicate": False}
    
    monkeypatch.setattr(service, "handle_webhook", mock_handle_webhook)

    class MockIntentsRepo:
        def find_by_provider_ref(self, provider, provider_ref):
            if provider_ref == "pp_req_ok_001":
                return {"id": "pi_123", "status": "pending"}
            return None

    class MockRepos:
        intents = MockIntentsRepo()

    monkeypatch.setattr("app.routers.admin_webhook_replay.get_repos", lambda: MockRepos())

    # Replay approved fixture
    res = client.post("/admin/payments/replay", json={
        "provider": "payplus",
        "payload": approved_payload
    })
    
    assert res.status_code == 200
    data = res.json()
    assert data["intent_found"] is True
    assert data["intent_id"] == "pi_123"
    assert data["mutation_risk"] == "may_mutate"
    assert data["provider_ref"] == "pp_req_ok_001"
    
    # Replay unmapped fixture
    res2 = client.post("/admin/payments/replay", json={
        "provider": "payplus",
        "payload": unmapped_payload
    })
    
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["mutation_risk"] == "safe"
    assert data2["provider_ref"] == "pp_req_unmapped_001"
