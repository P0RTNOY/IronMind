from datetime import datetime, timezone
from google.cloud import firestore
from google.api_core import exceptions
from app.repos.firestore import get_db

def create_event_if_absent(event_id: str, event_type: str) -> bool:
    """
    Atomically try to create an event document with status='processing'.
    If event exists but status='failed', marks as 'processing' and returns True (retry).
    Returns True if created/retrying, False if already exists/processed.
    """
    db = get_db()
    transaction = db.transaction()
    doc_ref = db.collection("stripe_events").document(event_id)
    now = datetime.now(timezone.utc)

    @firestore.transactional
    def txn_fn(txn: firestore.Transaction) -> bool:
        snapshot = doc_ref.get(transaction=txn)
        if snapshot.exists:
            status = snapshot.get("status")
            if status == "failed":
                txn.update(doc_ref, {"status": "processing", "retriedAt": now})
                return True
            return False
        
        txn.create(doc_ref, {
            "createdAt": now,
            "type": event_type,
            "status": "processing"
        })
        return True

    return txn_fn(transaction)

def update_event_status(event_id: str, status: str, error: str = None) -> None:
    """
    Update the status of an event (processed, failed).
    """
    db = get_db()
    doc_ref = db.collection("stripe_events").document(event_id)
    
    data = {
        "status": status,
        "processedAt": datetime.now(timezone.utc)
    }
    if error:
        data["error"] = error
        
    doc_ref.set(data, merge=True)
