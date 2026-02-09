from typing import List, Optional
from datetime import datetime, timezone
from app.repos.firestore import get_db
from app.models import LessonPublic

def search_published_lessons(query_text: str, limit: int = 50) -> List[LessonPublic]:
    # Using client-side filter for broad search in v1
    # If dataset grows, we need specific indexes or external search.
    
    if not query_text:
        return []
        
    db = get_db()
    
    # Optimization: If searching by tag, we could use array-contains
    # But for generic text search, we'll fetch published lessons.
    # WARNING: This might scale poorly. Limit to strict subset or use a dedicated collection for search if needed.
    # For now, let's fetch a reasonable batch or rely on specific field queries if possible.
    
    # Strategy: Fetch published lessons (capped)
    query = db.collection("lessons").where("published", "==", True).limit(200)
    
    docs = query.stream()
    q = query_text.lower()
    results = []
    
    for doc in docs:
        data = doc.to_dict()
        # Safe match
        title = data.get("titleHe", "").lower()
        desc = data.get("descriptionHe", "").lower()
        tags = [t.lower() for t in data.get("tags", [])]
        category = data.get("movementCategory", "").lower()
        
        if (q in title or 
            q in desc or 
            q in category or 
            any(q in t for t in tags)):
            results.append(LessonPublic(id=doc.id, **data))
            
    return results[:limit]

# --- Admin CRUD ---

def get_lesson_admin(lesson_id: str) -> Optional[dict]:
    db = get_db()
    snap = db.collection("lessons").document(lesson_id).get()
    if not snap.exists:
        return None
    return {"id": snap.id, **snap.to_dict()}

def list_lessons_by_course_admin(course_id: str) -> List[dict]:
    db = get_db()
    # v1: Sort in Python to avoid complex index requirement (courseId + orderIndex)
    query = db.collection("lessons").where("courseId", "==", course_id)
    docs = query.stream()
    items = [{"id": d.id, **d.to_dict()} for d in docs]
    items.sort(key=lambda x: x.get("orderIndex", 0))
    return items

def create_lesson(data: dict) -> str:
    db = get_db()
    now = datetime.now(timezone.utc)
    payload = {
        "courseId": data["courseId"],
        "titleHe": data["titleHe"],
        "descriptionHe": data["descriptionHe"],
        "movementCategory": data["movementCategory"],
        "tags": data.get("tags") or [],
        "vimeoVideoId": data.get("vimeoVideoId"),
        "orderIndex": data.get("orderIndex", 0),
        "published": bool(data.get("published", False)),
        "createdAt": now,
        "updatedAt": now,
    }
    ref = db.collection("lessons").document()
    ref.set(payload)
    return ref.id

def update_lesson(lesson_id: str, data: dict) -> None:
    db = get_db()
    ref = db.collection("lessons").document(lesson_id)
    if not ref.get().exists:
        raise KeyError("Lesson not found")

    updates = {
        "courseId": data["courseId"],
        "titleHe": data["titleHe"],
        "descriptionHe": data["descriptionHe"],
        "movementCategory": data["movementCategory"],
        "tags": data.get("tags") or [],
        "vimeoVideoId": data.get("vimeoVideoId"),
        "orderIndex": data.get("orderIndex", 0),
        "updatedAt": datetime.now(timezone.utc),
    }
    if data.get("published") is not None:
        updates["published"] = bool(data["published"])
        
    ref.update(updates)

def delete_lesson(lesson_id: str) -> None:
    db = get_db()
    ref = db.collection("lessons").document(lesson_id)
    if not ref.get().exists:
        raise KeyError("Lesson not found")
    ref.delete()
