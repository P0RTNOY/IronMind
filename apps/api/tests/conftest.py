import os
import uuid
import pytest
import httpx
from datetime import datetime, timezone

from google.cloud import firestore

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080")
PROJECT_ID = os.environ.get("PROJECT_ID", "ironmind-486909")  # Default to project from .env

@pytest.fixture(scope="session")
def client():
    return httpx.Client(base_url=API_BASE_URL, timeout=20.0)

@pytest.fixture
def user_headers():
    return {"X-Debug-Uid": "test-user"}

@pytest.fixture
def admin_headers():
    return {"X-Debug-Uid": "test-admin", "X-Debug-Admin": "1"}

@pytest.fixture(scope="session")
def db():
    # Uses GOOGLE_APPLICATION_CREDENTIALS set in env
    if PROJECT_ID:
        return firestore.Client(project=PROJECT_ID)
    return firestore.Client()

@pytest.fixture
def run_id():
    return uuid.uuid4().hex[:10]

@pytest.fixture
def cleanup_docs(db):
    """
    Track created docs and delete them at end of test.
    """
    created = []

    def track(ref):
        created.append(ref)
        return ref

    yield track

    # cleanup
    for ref in reversed(created):
        try:
            ref.delete()
        except Exception:
            pass

@pytest.fixture
def seed_course(db, cleanup_docs, run_id):
    """
    Create an UNPUBLISHED course doc (admin can see it; public can't).
    """
    ref = cleanup_docs(db.collection("courses").document(f"test_course_{run_id}"))
    now = datetime.now(timezone.utc)
    ref.set({
        "titleHe": "קורס בדיקה",
        "descriptionHe": "תיאור בדיקה",
        "type": "one_time",
        "published": False,
        "tags": ["test"],
        "createdAt": now,
        "updatedAt": now,
    })
    return ref.id
