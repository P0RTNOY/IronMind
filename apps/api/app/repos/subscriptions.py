from datetime import datetime, timezone
from typing import Optional
from app.repos.firestore import get_db

def upsert_subscription(
# ... (args same)
) -> None:
    """
    Update subscription status and details.
    """
    db = get_db()
    doc_ref = db.collection("subscriptions").document(uid)
    
    data = {
        "uid": uid,
        "stripeSubscriptionId": stripe_subscription_id,
        "status": status,
        "updatedAt": datetime.now(timezone.utc)
    }
    
    if current_period_end:
        data["currentPeriodEnd"] = current_period_end
    if stripe_customer_id:
        data["stripeCustomerId"] = stripe_customer_id
        
    doc_ref.set(data, merge=True)

def get_uid_by_subscription_id(stripe_subscription_id: str) -> Optional[str]:
    """
    Find user ID by stripe subscription ID.
    Important for webhooks where metadata might be missing.
    """
    db = get_db()
    # Standard query
    query = db.collection("subscriptions").where("stripeSubscriptionId", "==", stripe_subscription_id).limit(1)
    docs = query.stream()
    
    for doc in docs:
        return doc.id # The doc id is the uid
        
    return None
