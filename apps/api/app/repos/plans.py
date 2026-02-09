from typing import List, Optional
from datetime import datetime, timezone
from app.repos.firestore import get_db
from app.models import PlanPublic

def search_published_plans(query_text: str, limit: int = 50) -> List[PlanPublic]:
    if not query_text:
        return []
        
    db = get_db()
    
    # Similar strategy to lessons: Fetch published and filter client-side
    query = db.collection("plans").where("published", "==", True).limit(100)
    
    docs = query.stream()
    q = query_text.lower()
    results = []
    
    for doc in docs:
        data = doc.to_dict()
        title = data.get("titleHe", "").lower()
        desc = data.get("descriptionHe", "").lower()
        tags = [t.lower() for t in data.get("tags", [])]
        
        if (q in title or 
            q in desc or 
            any(q in t for t in tags)):
            results.append(PlanPublic(id=doc.id, **data))
            
    return results[:limit]

# --- Admin CRUD ---

def get_plan_admin(plan_id: str) -> Optional[dict]:
    db = get_db()
    snap = db.collection("plans").document(plan_id).get()
    if not snap.exists:
        return None
    return {"id": snap.id, **snap.to_dict()}

def list_plans_by_course_admin(course_id: str) -> List[dict]:
    db = get_db()
    query = db.collection("plans").where("courseId", "==", course_id)
    docs = query.stream()
    items = [{"id": d.id, **d.to_dict()} for d in docs]
    # v1: Sort in Python to avoid complex index requirement (courseId + createdAt)
    # Sort descending (newest first)
    items.sort(key=lambda x: str(x.get("createdAt", "")), reverse=True)
    return items

def create_plan(data: dict) -> str:
    db = get_db()
    now = datetime.now(timezone.utc)
    payload = {
        "courseId": data.get("courseId"),
        "titleHe": data["titleHe"],
        "descriptionHe": data["descriptionHe"],
        "tags": data.get("tags") or [],
        "pdfPath": data.get("pdfPath"),
        "published": bool(data.get("published", False)),
        "createdAt": now,
        "updatedAt": now,
    }
    ref = db.collection("plans").document()
    ref.set(payload)
    return ref.id

def update_plan(plan_id: str, data: dict) -> None:
    db = get_db()
    ref = db.collection("plans").document(plan_id)
    if not ref.get().exists:
        raise KeyError("Plan not found")

    updates = {
        "courseId": data.get("courseId"),
        "titleHe": data["titleHe"],
        "descriptionHe": data["descriptionHe"],
        "tags": data.get("tags") or [],
        "pdfPath": data.get("pdfPath"),
        "updatedAt": datetime.now(timezone.utc),
    }
    if data.get("published") is not None:
        updates["published"] = bool(data["published"])
        
    ref.update(updates)

def delete_plan(plan_id: str) -> None:
    db = get_db()
    ref = db.collection("plans").document(plan_id)
    if not ref.get().exists:
        raise KeyError("Plan not found")
    ref.delete()
