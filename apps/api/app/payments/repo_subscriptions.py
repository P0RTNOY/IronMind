"""
Firestore repository for subscriptions.
Collection: subscriptions
"""

from app.payments.models import Subscription
from app.repos.firestore import get_db

COLLECTION = "subscriptions"


def upsert_subscription(sub: Subscription) -> None:
    db = get_db()
    db.collection(COLLECTION).document(sub.id).set(sub.model_dump(), merge=True)
