from datetime import datetime, timezone
from typing import Optional, Tuple, Any, Dict, List
from app.repos import entitlements

def _to_utc_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    # Firestore Timestamp often has .to_datetime()
    if hasattr(value, "to_datetime"):
        dt = value.to_datetime()
    elif hasattr(value, "ToDatetime"): # Protobuf fallback
        dt = value.ToDatetime()
    else:
        dt = value
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return None

def is_active_entitlement(ent: Optional[Dict[str, Any]]) -> bool:
    if not ent:
        return False
    if ent.get("status") != "active":
        return False
    expires_at = _to_utc_datetime(ent.get("expiresAt"))
    if expires_at is None:
        return True
    return datetime.now(timezone.utc) < expires_at

def has_active_membership(uid: str) -> Tuple[bool, Optional[datetime]]:
    memb = entitlements.get_membership_entitlement(uid)
    expires_at = _to_utc_datetime(memb.get("expiresAt")) if memb else None
    return is_active_entitlement(memb), expires_at

def can_access_course(uid: str, course_id: str) -> bool:
    active, _ = has_active_membership(uid)
    if active:
        return True
    course_ent = entitlements.get_course_entitlement(uid, course_id)
    return is_active_entitlement(course_ent)

def get_access_summary(uid: str) -> dict:
    memb = entitlements.get_membership_entitlement(uid)
    membership_active = is_active_entitlement(memb)
    membership_expires_at = _to_utc_datetime(memb.get("expiresAt")) if memb else None

    all_ents = entitlements.list_entitlements(uid)
    entitled_course_ids: List[str] = []
    for ent in all_ents:
        if ent.get("kind") == "course" and is_active_entitlement(ent):
            cid = ent.get("courseId")
            if cid:
                entitled_course_ids.append(cid)

    # de-dup + stable ordering
    entitled_course_ids = sorted(set(entitled_course_ids))

    return {
        "membershipActive": membership_active,
        "membershipExpiresAt": membership_expires_at,
        "entitledCourseIds": entitled_course_ids,
    }
