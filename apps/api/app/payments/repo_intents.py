"""
Firestore repository for payment intents.
Collection: payment_intents
"""

from datetime import datetime, timezone
from typing import Optional

from app.payments.models import PaymentIntent
from app.repos.firestore import get_db

COLLECTION = "payment_intents"


def create_intent(intent: PaymentIntent) -> None:
    db = get_db()
    db.collection(COLLECTION).document(intent.id).set(intent.model_dump())


def get_intent(intent_id: str) -> Optional[PaymentIntent]:
    db = get_db()
    doc = db.collection(COLLECTION).document(intent_id).get()
    if not doc.exists:
        return None
    return PaymentIntent(**doc.to_dict())


def update_intent(intent_id: str, patch: dict) -> None:
    db = get_db()
    patch["updatedAt"] = datetime.now(timezone.utc)
    db.collection(COLLECTION).document(intent_id).update(patch)


def find_by_provider_ref(provider: str, provider_ref: str) -> Optional[PaymentIntent]:
    """Find an intent by its provider reference. Used by webhooks."""
    db = get_db()
    query = (
        db.collection(COLLECTION)
        .where("provider", "==", provider)
        .where("providerRef", "==", provider_ref)
        .limit(1)
    )
    for doc in query.stream():
        return PaymentIntent(**doc.to_dict())
    return None
