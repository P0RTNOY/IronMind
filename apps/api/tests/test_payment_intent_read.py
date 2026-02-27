import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.payments.repo import RepoContainer

# Create a test client
client = TestClient(app)

class FakeIntentsRepo:
    def __init__(self):
        self.intents = {
            "pi_owner": {
                "id": "pi_owner",
                "uid": "test_user_1",
                "kind": "charge",
                "scope": "course",
                "courseId": "test_course_1",
                "tier": "basic",
                "status": "succeeded",
                "updatedAt": "2024-01-01T12:00:00Z",
                "providerRef": "ch_secret_123", # Should be hidden
                "raw": {"some": "data"} # Should be hidden
            },
            "pi_other": {
                "id": "pi_other",
                "uid": "test_user_2",
                "kind": "charge",
                "scope": "course",
                "courseId": "test_course_2",
                "tier": "basic",
                "status": "pending",
                "updatedAt": "2024-01-01T12:00:00Z"
            }
        }
    
    def get_intent(self, intent_id: str):
        # Return a mock object mimicking the firestore document structure
        # In the real code, get_intent returns a dict or similar object
        # Based on how get_intent is typed, let's create a dummy class
        data = self.intents.get(intent_id)
        if not data:
            return None
            
        class MockIntent:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)
        return MockIntent(data)

class FakeRepoContainer:
    def __init__(self):
        self.intents = FakeIntentsRepo()

@pytest.fixture
def mock_repos(monkeypatch):
    """Replaces the real RepoContainer with a fake one for testing."""
    fake_container = FakeRepoContainer()
    monkeypatch.setattr("app.routers.payments.get_repos", lambda: fake_container)
    return fake_container

def test_owner_can_read_intent(mock_repos):
    response = client.get(
        "/payments/intents/pi_owner",
        headers={"X-Debug-Uid": "test_user_1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "pi_owner"
    assert data["status"] == "succeeded"
    # Ensure sensitive fields are NOT in the response
    assert "providerRef" not in data
    assert "raw" not in data

def test_non_owner_forbidden(mock_repos):
    response = client.get(
        "/payments/intents/pi_owner",
        headers={"X-Debug-Uid": "test_user_2"} # Different user
    )
    # As per requested design, returns 404 to non-owners to prevent leaking intent existence
    assert response.status_code == 404

def test_admin_can_read_any(mock_repos):
    response = client.get(
        "/payments/intents/pi_other",
        headers={"X-Debug-Uid": "test_user_1", "X-Debug-Admin": "1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "pi_other"
    assert data["status"] == "pending"

def test_missing_intent_404(mock_repos):
    response = client.get(
        "/payments/intents/pi_does_not_exist",
        headers={"X-Debug-Uid": "test_user_1"}
    )
    assert response.status_code == 404
