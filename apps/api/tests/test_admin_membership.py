import pytest
from starlette.testclient import TestClient
from app.main import app
from datetime import datetime, timezone

client = TestClient(app)

MOCK_UID = "test_user_123"

# We use debug headers in the tests to simulate admin auth

@pytest.fixture
def mock_entitlements_repo(monkeypatch):
    """
    Mocks the get_membership_entitlement and upsert_membership_entitlement calls 
    so we don't hit real Firestore.
    """
    class RepoState:
        last_upsert_kwargs = None
        current_entitlement = None

    state = RepoState()

    def mock_upsert(*args, **kwargs):
        state.last_upsert_kwargs = kwargs

    def mock_get(uid):
        return state.current_entitlement

    monkeypatch.setattr("app.repos.entitlements.upsert_membership_entitlement", mock_upsert)
    monkeypatch.setattr("app.repos.entitlements.get_membership_entitlement", mock_get)
    
    # Also mock audit log to prevent hits
    monkeypatch.setattr("app.repos.admin_audit.write_audit", lambda *a, **k: None)

    return state

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def test_activate_membership(mock_entitlements_repo):
    """Test activating a membership, ensuring active status and manual source are passed."""
    resp = client.post(
        f"/admin/users/{MOCK_UID}/membership/activate", 
        json={},
        headers={"X-Debug-Uid": "admin-uid", "X-Debug-Admin": "1"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert data["uid"] == MOCK_UID
    assert data["expiresAt"] is None

    # Check that repo was called correctly
    kwargs = mock_entitlements_repo.last_upsert_kwargs
    assert kwargs["uid"] == MOCK_UID
    assert kwargs["status"] == "active"
    assert kwargs["source"] == "manual"
    assert kwargs["expires_at"] is None

def test_activate_with_expiry(mock_entitlements_repo):
    """Test activating with an explicit expiry date."""
    future_date = "2030-01-01T23:59:59.999Z"
    resp = client.post(
        f"/admin/users/{MOCK_UID}/membership/activate", 
        json={"expiresAt": future_date},
        headers={"X-Debug-Uid": "admin-uid", "X-Debug-Admin": "1"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert future_date.replace("Z", "") in data["expiresAt"] # JSON serialization replaces Z with +00:00

    kwargs = mock_entitlements_repo.last_upsert_kwargs
    assert kwargs["status"] == "active"
    assert kwargs["expires_at"] is not None

def test_deactivate_membership(mock_entitlements_repo):
    """
    Test deactivating a membership. 
    Per requirements, it should explicitly clear the expiry date.
    """
    resp = client.post(
        f"/admin/users/{MOCK_UID}/membership/deactivate",
        headers={"X-Debug-Uid": "admin-uid", "X-Debug-Admin": "1"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "inactive"
    assert data["expiresAt"] is None

    kwargs = mock_entitlements_repo.last_upsert_kwargs
    assert kwargs["uid"] == MOCK_UID
    assert kwargs["status"] == "inactive"
    assert kwargs["source"] == "manual"
    assert kwargs["expires_at"] is None

def test_set_expiry_preserves_status_when_exists(mock_entitlements_repo):
    """Test setting expiry when user already has an active entitlement."""
    mock_entitlements_repo.current_entitlement = {"status": "active"}
    
    future_date = "2025-12-31T23:59:59.000Z"
    resp = client.post(
        f"/admin/users/{MOCK_UID}/membership/set-expiry", 
        json={"expiresAt": future_date},
        headers={"X-Debug-Uid": "admin-uid", "X-Debug-Admin": "1"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active" # Preserved

    kwargs = mock_entitlements_repo.last_upsert_kwargs
    assert kwargs["status"] == "active"
    assert kwargs["expires_at"] is not None

def test_set_expiry_defaults_inactive_when_missing(mock_entitlements_repo):
    """Test setting expiry when user has NO entitlement. Should default to inactive."""
    mock_entitlements_repo.current_entitlement = None
    
    future_date = "2025-12-31T23:59:59.000Z"
    resp = client.post(
        f"/admin/users/{MOCK_UID}/membership/set-expiry", 
        json={"expiresAt": future_date},
        headers={"X-Debug-Uid": "admin-uid", "X-Debug-Admin": "1"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "inactive" # Defaulted safely

    kwargs = mock_entitlements_repo.last_upsert_kwargs
    assert kwargs["status"] == "inactive"

def test_activate_non_admin_forbidden(monkeypatch):
    """Test that a non-admin cannot access the endpoint."""
    resp = client.post(
        f"/admin/users/{MOCK_UID}/membership/activate", 
        json={},
        headers={"X-Debug-Uid": "user-uid"} # No admin header
    )
    assert resp.status_code == 403
