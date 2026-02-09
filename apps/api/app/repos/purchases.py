from datetime import datetime, timezone
from typing import Optional
from app.repos.firestore import get_db

def create_purchase(
# ... (args same)
    course_id: Optional[str] = None
) -> None:
    """
    Record a purchase.
    """
    db = get_db()
    # Use stripe session id as doc id for idempotency (or part of it)
    doc_ref = db.collection("purchases").document(stripe_session_id)
    
    data = {
        "uid": uid,
        "stripeSessionId": stripe_session_id,
        "amount": amount,
        "currency": currency,
        "purchaseType": purchase_type,
        "createdAt": datetime.now(timezone.utc)
    }
    
    if course_id:
        data["courseId"] = course_id
        
    doc_ref.set(data, merge=True)
