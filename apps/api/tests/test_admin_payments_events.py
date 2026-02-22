import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Helper mock for doc.to_dict()
class MockDoc:
    def __init__(self, data):
        self._data = data
        self.id = data.get("id", "doc_123")
    
    def to_dict(self):
        return self._data

@pytest.fixture
def mock_firestore_events(monkeypatch):
    """Mocks repos.events.db.collection(...).limit(...).stream() for the events endpoint."""
    
    # We need to mock get_repos globally or at least the db layer
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_query = MagicMock()
    
    mock_db.collection.return_value = mock_collection
    mock_collection.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    
    # Setup test data
    test_docs = [
        MockDoc({
            "id": "evt_1",
            "provider": "payplus",
            "type": "payment.succeeded",
            "receivedAt": "2026-02-22T12:00:00Z",
            "payload_raw_redacted": {"email": "***redacted***"},
            "payload": {"email": "secret@test.com"} # this should be stripped by the route
        }),
        MockDoc({
            "id": "evt_2",
            "provider": "payplus", 
            "type": "payment.failed",
            "receivedAt": "2026-02-22T11:00:00Z",
            "payload_raw_redacted": {"card": "***redacted***"}
        })
    ]
    
    mock_query.stream.return_value = test_docs
    mock_collection.limit.return_value = mock_query # For the fallback path
    
    # Monkeypatch the get_repos dependency used inside the route
    from app.payments.repo import RepoContainer
    
    def mock_get_repos():
        repos = MagicMock(spec=RepoContainer)
        repos.events = MagicMock()
        repos.events.db = mock_db
        repos.events.collection_name = "payment_events"
        return repos

    monkeypatch.setattr("app.routers.admin_payments.get_repos", mock_get_repos)

def test_admin_payments_events_requires_admin(user_headers):
    # No auth header
    resp = client.get("/admin/payments/events")
    assert resp.status_code == 401

    # Normal user header
    resp = client.get("/admin/payments/events", headers=user_headers)
    assert resp.status_code == 403

def test_admin_payments_events_success(admin_headers, mock_firestore_events):
    # Admin header
    resp = client.get("/admin/payments/events", headers=admin_headers)
    
    assert resp.status_code == 200
    data = resp.json()
    
    # Assert docs returned
    assert len(data) == 2
    
    # Assert sorting (first doc should be newest)
    assert data[0]["id"] == "evt_1"
    assert data[1]["id"] == "evt_2"
    
    # Assert unredacted 'payload' is explicitly removed
    assert "payload" not in data[0]
    assert "payload" not in data[1]
    
    # Assert redacted data remains intact
    assert data[0]["payload_raw_redacted"]["email"] == "***redacted***"

