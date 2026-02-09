from typing import List, Optional
from datetime import datetime, timezone
from google.cloud import firestore
from app.repos.firestore import get_db
from app.models import CoursePublic

def list_published_courses(limit: int = 100) -> List[CoursePublic]:
    db = get_db()
    
    # Standard syntax for pinned google-cloud-firestore
    query = (
        db.collection("courses")
        .where("published", "==", True)
        .limit(limit)
    )
    
    docs = query.stream()
    return [CoursePublic(id=doc.id, **doc.to_dict()) for doc in docs]

def get_published_course(course_id: str) -> Optional[CoursePublic]:
    db = get_db()
    doc = db.collection("courses").document(course_id).get()
    
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    if not data.get("published"):
        return None
        
    return CoursePublic(id=doc.id, **data)

def search_published_courses(query_text: str) -> List[CoursePublic]:
    # Basic client-side search for v1
    # Fetch all published courses (dataset is small)
    all_courses = list_published_courses(limit=200)
    
    if not query_text:
        return []
        
    q = query_text.lower()
    results = []
    for c in all_courses:
        if (q in c.titleHe.lower()) or (q in c.descriptionHe.lower()):
            results.append(c)
    return results

# --- Admin CRUD ---

def get_course_admin(course_id: str) -> Optional[dict]:
    db = get_db()
    snap = db.collection("courses").document(course_id).get()
    if not snap.exists:
        return None
    return {"id": snap.id, **snap.to_dict()}

def list_courses_admin(limit: int = 200) -> List[dict]:
    db = get_db()
    # Order by createdAt DESC
    docs = db.collection("courses").order_by("createdAt", direction=firestore.Query.DESCENDING).limit(limit).stream()
    out = []
    for d in docs:
        data = d.to_dict()
        out.append({"id": d.id, **data})
    return out

def create_course(data: dict) -> str:
    db = get_db()
    now = datetime.now(timezone.utc)
    payload = {
        "titleHe": data["titleHe"],
        "descriptionHe": data["descriptionHe"],
        "type": data["type"],
        "published": bool(data.get("published", False)),
        "coverImageUrl": data.get("coverImageUrl"),
        "tags": data.get("tags") or [],
        "createdAt": now,
        "updatedAt": now,
    }
    ref = db.collection("courses").document()
    ref.set(payload)
    return ref.id

def update_course(course_id: str, data: dict) -> None:
    db = get_db()
    ref = db.collection("courses").document(course_id)
    # Check existence to ensure we don't create phantom doc on merge if id is wrong?
    # But for firestore update() it fails if not exists.
    # set(..., merge=True) creates if not exists.
    # User requested: raise KeyError if not found.
    snap = ref.get()
    if not snap.exists:
        raise KeyError("Course not found")

    updates = {
        "titleHe": data["titleHe"],
        "descriptionHe": data["descriptionHe"],
        "type": data["type"],
        "coverImageUrl": data.get("coverImageUrl"),
        "tags": data.get("tags") or [],
        "updatedAt": datetime.now(timezone.utc),
    }
    # allow published in update request if present
    if data.get("published") is not None:
        updates["published"] = bool(data["published"])

    ref.update(updates)

def delete_course(course_id: str) -> None:
    db = get_db()
    ref = db.collection("courses").document(course_id)
    if not ref.get().exists:
        raise KeyError("Course not found")
    ref.delete()

def set_course_published(course_id: str, published: bool) -> None:
    db = get_db()
    ref = db.collection("courses").document(course_id)
    if not ref.get().exists:
        raise KeyError("Course not found")
    ref.update({"published": published, "updatedAt": datetime.now(timezone.utc)})
