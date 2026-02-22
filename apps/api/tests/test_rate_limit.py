import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.security.rate_limit import limiter
from app.deps import get_db, get_current_user_cookie
from app.models import UserContext

client = TestClient(app)

@pytest.fixture
def mock_db():
    mock = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock
    yield mock
    app.dependency_overrides.clear()

def test_rate_limit_auth_ip(mock_db):
    headers = {"X-Forwarded-For": "192.168.1.5, 10.0.0.1"}
    
    # Auth route is limited to 5 per 60s
    for _ in range(5):
        res = client.post("/auth/request", json={"email": "test@ironmind.app"}, headers=headers)
        assert res.status_code == 204
    
    # 6th request from the same 'real' IP
    res = client.post("/auth/request", json={"email": "test@ironmind.app"}, headers=headers)
    assert res.status_code == 429
    assert res.json() == {"detail": "rate_limited"}
    assert "Retry-After" in res.headers
    assert res.headers["X-RateLimit-Limit"] == "5"
    assert res.headers["X-RateLimit-Remaining"] == "0"
    assert "X-RateLimit-Reset" in res.headers

def test_rate_limit_ip_separates_ips(mock_db):
    for i in range(5):
        res = client.post("/auth/request", json={"email": "test@ironmind.app"}, headers={"X-Forwarded-For": "IP_1"})
        assert res.status_code == 204
        
    for i in range(5):
        res = client.post("/auth/request", json={"email": "test@ironmind.app"}, headers={"X-Forwarded-For": "IP_2"})
        assert res.status_code == 204
        
    res = client.post("/auth/request", json={"email": "test@ironmind.app"}, headers={"X-Forwarded-For": "IP_1"})
    assert res.status_code == 429

def test_rate_limit_uid_mock_content():
    # Playback route is limited to 60 per 60s
    mock_uid = "limit_user_123"
    
    def override_get_current_user():
        return UserContext(uid=mock_uid, email="u@x.com", name="U", is_admin=False)
    
    app.dependency_overrides[get_current_user_cookie] = override_get_current_user
    
    try:
        for _ in range(60):
            res = client.get("/content/lessons/lesson_99/playback")
            # We don't care what the route actually does (404/403), just not 429
            assert res.status_code != 429
            
        res = client.get("/content/lessons/lesson_99/playback")
        assert res.status_code == 429
        assert res.json() == {"detail": "rate_limited"}
        assert "Retry-After" in res.headers
        assert res.headers["X-RateLimit-Limit"] == "60"
        assert res.headers["X-RateLimit-Remaining"] == "0"
        assert "X-RateLimit-Reset" in res.headers
    finally:
        app.dependency_overrides.clear()

def test_webhook_rate_limit_can_be_disabled(monkeypatch):
    from unittest.mock import MagicMock
    import app.security.rate_limit
    
    mock_settings = MagicMock()
    mock_settings.WEBHOOK_RATE_LIMIT_ENABLED = False
    monkeypatch.setattr(app.security.rate_limit, "settings", mock_settings)
    
    # The webhook route limits to 600 per 60s
    # If disabled, we should be able to blast 601 requests and get no 429.
    for _ in range(601):
        # We expect a 400/401 webhook signature error, not 429
        res = client.post("/webhooks/payments", data=b"{}", headers={"X-Forwarded-For": "WEBHOOK_IP"})
        assert res.status_code != 429
