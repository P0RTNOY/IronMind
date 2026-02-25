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
            has_pdf = bool(data.get("pdfPath"))
            safe_data = {k: v for k, v in data.items() if k != "pdfPath"}
            results.append(PlanPublic(
                id=doc.id,
                pdfPath=None,  # NEVER expose raw GCS path
                hasPdf=has_pdf,
                pdfDownloadEndpoint=f"/content/plans/{doc.id}/download" if has_pdf else None,
                **safe_data,
            ))
            
    return results[:limit]

def list_published_plans_by_course(course_id: str, limit: int = 200) -> List[PlanPublic]:
    db = get_db()
    query = db.collection("plans").where("published", "==", True).where("courseId", "==", course_id).limit(limit)
    docs = query.stream()
    
    raw_results = []
    for doc in docs:
        raw_results.append({"id": doc.id, **doc.to_dict()})
        
    raw_results.sort(key=lambda x: str(x.get("createdAt", "")), reverse=True)
    
    results = []
    for data in raw_results:
        has_pdf = bool(data.get("pdfPath"))
        safe_data = {k: v for k, v in data.items() if k not in ["pdfPath", "id"]}
        results.append(PlanPublic(
            id=data["id"],
            pdfPath=None,
            hasPdf=has_pdf,
            pdfDownloadEndpoint=f"/content/plans/{data['id']}/download" if has_pdf else None,
            **safe_data,
        ))
        
    return results

def get_published_plan(plan_id: str) -> Optional[PlanPublic]:
    db = get_db()
    snap = db.collection("plans").document(plan_id).get()
    if not snap.exists:
        return None
        
    data = snap.to_dict()
    if not data.get("published"):
        return None
        
    has_pdf = bool(data.get("pdfPath"))
    safe_data = {k: v for k, v in data.items() if k != "pdfPath"}
    return PlanPublic(
        id=snap.id,
        pdfPath=None,
        hasPdf=has_pdf,
        pdfDownloadEndpoint=f"/content/plans/{snap.id}/download" if has_pdf else None,
        **safe_data,
    )

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

def set_plan_published(plan_id: str, published: bool) -> None:
    db = get_db()
    ref = db.collection("plans").document(plan_id)
    if not ref.get().exists:
        raise KeyError("Plan not found")
    ref.update({"published": published, "updatedAt": datetime.now(timezone.utc)})

