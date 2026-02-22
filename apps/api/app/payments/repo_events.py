"""
Firestore repository for payment events.
Collection: payment_events

Doc IDs are provider-namespaced: "{provider}:{event_id}"
to prevent cross-provider collisions.
"""

from datetime import datetime, timezone

from app.repos.firestore import get_db

COLLECTION = "payment_events"


def create_event_if_absent(provider: str, event_id: str, event_doc: dict) -> bool:
    """
    Atomically create an event document if it doesn't exist.
    Returns True if created (new event), False if already exists (duplicate).
    """
    db = get_db()
    doc_id = f"{provider}:{event_id}"
    doc_ref = db.collection(COLLECTION).document(doc_id)

    # Use a transaction for atomicity
    transaction = db.transaction()

    from google.cloud import firestore as fs

    @fs.transactional
    def txn_fn(txn: fs.Transaction) -> bool:
        snapshot = doc_ref.get(transaction=txn)
        if snapshot.exists:
            return False

        event_doc["id"] = doc_id
        event_doc["receivedAt"] = datetime.now(timezone.utc)
        txn.create(doc_ref, event_doc)
        return True

    return txn_fn(transaction)
