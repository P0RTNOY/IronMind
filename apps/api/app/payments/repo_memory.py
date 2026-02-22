"""
In-memory repository implementations for testing.

Used when PAYMENTS_REPO=memory. All stores are module-level dicts
so the singleton in repo.py returns the same data across calls.
"""

from datetime import datetime, timezone
from typing import Optional

from app.payments.models import PaymentIntent, Subscription


# ── Module-level stores (shared singleton state) ────────────────────

_intents: dict[str, dict] = {}
_events: dict[str, dict] = {}
_subscriptions: dict[str, dict] = {}


def reset() -> None:
    """Clear all in-memory stores. Called between tests."""
    _intents.clear()
    _events.clear()
    _subscriptions.clear()


# ── Intents ─────────────────────────────────────────────────────────

class MemoryIntentsRepo:
    @staticmethod
    def create_intent(intent: PaymentIntent) -> None:
        _intents[intent.id] = intent.model_dump()

    @staticmethod
    def get_intent(intent_id: str) -> Optional[PaymentIntent]:
        data = _intents.get(intent_id)
        return PaymentIntent(**data) if data else None

    @staticmethod
    def update_intent(intent_id: str, patch: dict) -> None:
        if intent_id not in _intents:
            raise KeyError(f"Intent {intent_id} not found")
        patch["updatedAt"] = datetime.now(timezone.utc)
        _intents[intent_id].update(patch)

    @staticmethod
    def find_by_provider_ref(provider: str, provider_ref: str) -> Optional[PaymentIntent]:
        for data in _intents.values():
            if data.get("provider") == provider and data.get("providerRef") == provider_ref:
                return PaymentIntent(**data)
        return None


# ── Events ──────────────────────────────────────────────────────────

class MemoryEventsRepo:
    @staticmethod
    def create_event_if_absent(provider: str, event_id: str, event_doc: dict) -> bool:
        doc_id = f"{provider}:{event_id}"
        if doc_id in _events:
            return False
        event_doc["id"] = doc_id
        event_doc["receivedAt"] = datetime.now(timezone.utc)
        _events[doc_id] = event_doc
        return True


# ── Subscriptions ───────────────────────────────────────────────────

class MemorySubscriptionsRepo:
    @staticmethod
    def upsert_subscription(sub: Subscription) -> None:
        _subscriptions[sub.id] = sub.model_dump()
