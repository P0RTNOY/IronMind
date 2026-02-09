from datetime import datetime, timezone
from typing import Optional, Literal
from app.repos.firestore import get_db

def _get_course_entitlement_id(uid: str, course_id: str) -> str:
    return f"ent_course_{uid}_{course_id}"

def _get_membership_entitlement_id(uid: str) -> str:
    return f"ent_membership_{uid}"

def upsert_course_entitlement(
    uid: str,
    course_id: str,
    source: str = "one_time"
) -> None:
    """
    Grant access to a specific course.
    """
    db = get_db()
    ent_id = _get_course_entitlement_id(uid, course_id)
    doc_ref = db.collection("entitlements").document(ent_id)
    
    data = {
        "id": ent_id,
        "uid": uid,
        "kind": "course",
        "courseId": course_id,
        "status": "active",
        "source": source,
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }
    
    # Merge=True to avoid overwriting unrelated fields if schema evolves, 
    # though for course entitlement, simple set is usually fine.
    doc_ref.set(data, merge=True)

def upsert_membership_entitlement(
    uid: str,
    stripe_subscription_id: str,
    status: Literal["active", "inactive"],
    expires_at: Optional[datetime],
    source: str = "subscription"
) -> None:
    """
    Update membership entitlement status.
    """
    db = get_db()
    ent_id = _get_membership_entitlement_id(uid)
    doc_ref = db.collection("entitlements").document(ent_id)
    
    data = {
        "id": ent_id,
        "uid": uid,
        "kind": "membership",
        "status": status,
        "source": source,
        "stripeSubscriptionId": stripe_subscription_id,
        "updatedAt": datetime.now(timezone.utc)
    }
    
    if expires_at is not None:
        data["expiresAt"] = expires_at
        
    # If creating for the first time, we want createdAt
    # We can use set(..., merge=True). 
    # Note: If doc doesn't exist, merge=True creates it.
    
    # Firestore doesn't have a simple "set if missing" for fields inside merge except via transform
    # simpler to just write createdAt if it's likely new, or accept it updates.
    # For robust createdAt, we'd check existence, but for this portfolio speed, we set it if missing (not easily done in one shot without read).
    # We'll just write it.
    
    doc_ref.set(data, merge=True)

def get_membership_entitlement(uid: str) -> Optional[dict]:
    db = get_db()
    ent_id = _get_membership_entitlement_id(uid)
    doc = db.collection("entitlements").document(ent_id).get()
    return doc.to_dict() if doc.exists else None

def get_course_entitlement(uid: str, course_id: str) -> Optional[dict]:
    db = get_db()
    ent_id = _get_course_entitlement_id(uid, course_id)
    doc = db.collection("entitlements").document(ent_id).get()
    return doc.to_dict() if doc.exists else None

def list_entitlements(uid: str) -> list[dict]:
    """
    Read all entitlements for a user.
    """
    db = get_db()
    query = db.collection("entitlements").where("uid", "==", uid)
    return [doc.to_dict() for doc in query.stream()]

def is_entitlement_active(entitlement: dict) -> bool:
    """
    Check if an entitlement is active.
    Rule: status == 'active' AND (expiresAt is None OR now < expiresAt)
    """
    if not entitlement:
        return False
        
    if entitlement.get("status") != "active":
        return False
        
    expires_at = entitlement.get("expiresAt")
    if not expires_at:
        return True
        
    now = datetime.now(timezone.utc)
    
    # Handle potentially naive datetime (though Firestore client usually returns aware)
    if isinstance(expires_at, datetime):
         if expires_at.tzinfo is None:
             expires_at = expires_at.replace(tzinfo=timezone.utc)
         return now < expires_at
    
    # If for some reason it's not a datetime (e.g. string), we fail open or closed?
    # Fail closed for security.
    return False
