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

    return False

def grant_course(uid: str, course_id: str, source: str = "manual") -> dict:
    """
    Grant access to a course. 
    If active, idempotent. 
    If inactive, reactivates.
    Returns the entitlement dict.
    """
    db = get_db()
    ent_id = _get_course_entitlement_id(uid, course_id)
    doc_ref = db.collection("entitlements").document(ent_id)
    
    now = datetime.now(timezone.utc)
    
    # Transactional update might be safer but for MVP admin override, set w/ merge is fine.
    # We want to ensure we return the final state.
    
    data = {
        "id": ent_id,
        "uid": uid,
        "kind": "course",
        "courseId": course_id,
        "status": "active",
        "source": source,
        "updatedAt": now
    }
    
    # If new, add createdAt
    doc = doc_ref.get()
    if not doc.exists:
        data["createdAt"] = now
    
    doc_ref.set(data, merge=True)
    
    # Return fresh state
    return doc_ref.get().to_dict()

def set_status(ent_id: str, status: Literal["active", "inactive"]) -> dict:
    """
    Set entitlement status (e.g. revoke).
    Returns the updated dictionary.
    Raises KeyError if not found.
    """
    db = get_db()
    doc_ref = db.collection("entitlements").document(ent_id)
    
    doc = doc_ref.get()
    if not doc.exists:
        raise KeyError(f"Entitlement {ent_id} not found")
        
    update_data = {
        "status": status,
        "updatedAt": datetime.now(timezone.utc)
    }
    
    doc_ref.update(update_data)
    
    # Return updated
    return doc_ref.get().to_dict()

def list_entitlements(uid: str) -> list[dict]:
    """
    Read all entitlements for a user.
    """
    db = get_db()
    # Simple query
    query = db.collection("entitlements").where("uid", "==", uid)
    return [doc.to_dict() for doc in query.stream()]
