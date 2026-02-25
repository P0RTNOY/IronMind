"""
Tests for the dev seed module.

All tests monkeypatch get_db() IN THE SEED MODULE to use a fake Firestore client.
No real Firestore is hit — deterministic and CI-friendly.
"""

import pytest
from unittest.mock import MagicMock


# ── Fake Firestore ──────────────────────────────────────────────────

class FakeDocumentRef:
    """Minimal Firestore document reference backed by a dict store."""
    def __init__(self, store: dict, collection_name: str, doc_id: str):
        self._store = store
        self._key = f"{collection_name}/{doc_id}"
        self.id = doc_id

    def get(self):
        snap = MagicMock()
        snap.exists = self._key in self._store
        snap.to_dict.return_value = self._store.get(self._key, {})
        snap.id = self.id
        return snap

    def set(self, data, merge=False):
        if merge and self._key in self._store:
            self._store[self._key].update(data)
        else:
            self._store[self._key] = dict(data)


class FakeCollectionRef:
    def __init__(self, store: dict, name: str):
        self._store = store
        self._name = name

    def document(self, doc_id: str):
        return FakeDocumentRef(self._store, self._name, doc_id)


class FakeFirestoreClient:
    def __init__(self):
        self._store: dict = {}

    def collection(self, name: str):
        return FakeCollectionRef(self._store, name)


# ── Tests ───────────────────────────────────────────────────────────

@pytest.fixture
def fake_db():
    return FakeFirestoreClient()


@pytest.fixture
def patched_seed(fake_db, monkeypatch):
    """
    Import seed module with get_db monkeypatched WHERE IT IS USED.
    
    Key: we must patch app.dev.seed.get_db (where the import lands),
    not app.repos.firestore.get_db (the source module).
    """
    import app.dev.seed as seed_mod
    monkeypatch.setattr(seed_mod, "get_db", lambda: fake_db)
    # Patch entitlements to avoid hitting real Firestore
    monkeypatch.setattr(
        seed_mod.entitlements, "upsert_course_entitlement",
        lambda **kw: None
    )
    return seed_mod.seed_demo_data


def test_seed_blocked_in_prod(patched_seed, monkeypatch):
    """seed_demo_data raises RuntimeError when ENV=prod."""
    from app.config import settings
    monkeypatch.setattr(settings, "ENV", "prod")
    with pytest.raises(RuntimeError, match="seeding_disabled_in_prod"):
        patched_seed()


def test_seed_creates_docs(patched_seed, fake_db):
    """First seed run creates all demo docs."""
    result = patched_seed()

    assert isinstance(result, dict)
    assert len(result["created"]) > 0
    assert len(result["skipped"]) == 0
    assert len(result["updated"]) == 0

    # Verify expected course IDs
    created_ids = result["created"]
    assert "course_demo_one_time" in created_ids
    assert "course_demo_sub" in created_ids

    # Verify lessons were created (3 per course = 6 total)
    lesson_ids = [x for x in created_ids if x.startswith("lesson_demo_")]
    assert len(lesson_ids) == 6

    # Verify plans were created (2 per course = 4 total)
    plan_ids = [x for x in created_ids if x.startswith("plan_demo_")]
    assert len(plan_ids) == 4

    # Verify docs exist in fake store
    assert "courses/course_demo_one_time" in fake_db._store
    assert "courses/course_demo_sub" in fake_db._store


def test_seed_idempotent_skips(patched_seed, fake_db):
    """Second seed without force skips all existing docs."""
    # First seed
    first = patched_seed()
    assert len(first["created"]) > 0

    # Second seed (no force)
    second = patched_seed(force=False)
    assert len(second["created"]) == 0
    assert len(second["updated"]) == 0
    assert len(second["skipped"]) > 0
    assert "course_demo_one_time" in second["skipped"]


def test_seed_force_updates(patched_seed, fake_db):
    """Seed with force=True updates existing docs."""
    # First seed
    first = patched_seed()
    assert len(first["created"]) > 0

    # Force re-seed
    second = patched_seed(force=True)
    assert len(second["created"]) == 0
    assert len(second["updated"]) > 0
    assert "course_demo_one_time" in second["updated"]
    assert len(second["skipped"]) == 0
