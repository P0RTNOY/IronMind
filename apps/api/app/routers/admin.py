from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from app.models import (
    UserContext, 
    CourseUpsertRequest, CourseAdmin, 
    LessonUpsertRequest, LessonAdmin,
    PlanUpsertRequest, PlanAdmin,
    MetricsOverview
)
from app.deps import require_admin
from app.repos import courses, lessons, plans, admin_audit
from app.repos.firestore import get_db

router = APIRouter()

# --- Courses ---

@router.get("/courses", response_model=List[CourseAdmin])
async def list_courses(admin: UserContext = Depends(require_admin)):
    """List all courses (including unpublished)."""
    # Repo returns dicts, Pydantic validates
    return courses.list_courses_admin()


@router.post("/courses", response_model=CourseAdmin, status_code=201)
async def create_course(
    request: CourseUpsertRequest, 
    admin: UserContext = Depends(require_admin)
):
    course_id = courses.create_course(request.dict())
    
    admin_audit.write_audit(
        action="create_course",
        entity_type="course",
        entity_id=course_id,
        admin_uid=admin.uid,
        payload=request.dict()
    )
    
    course = courses.get_course_admin(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course created but not found")
    return course

@router.put("/courses/{course_id}", response_model=CourseAdmin)
async def update_course(
    course_id: str, 
    request: CourseUpsertRequest, 
    admin: UserContext = Depends(require_admin)
):
    try:
        courses.update_course(course_id, request.dict())
    except KeyError:
        raise HTTPException(status_code=404, detail="Course not found")
    
    admin_audit.write_audit(
        action="update_course",
        entity_type="course",
        entity_id=course_id,
        admin_uid=admin.uid,
        payload=request.dict()
    )
    
    course = courses.get_course_admin(course_id)
    if not course:
         raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.delete("/courses/{course_id}", status_code=204)
async def delete_course(course_id: str, admin: UserContext = Depends(require_admin)):
    try:
        courses.delete_course(course_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Course not found")
    admin_audit.write_audit("delete_course", "course", course_id, admin.uid)

@router.post("/courses/{course_id}/publish", response_model=CourseAdmin)
async def publish_course(course_id: str, admin: UserContext = Depends(require_admin)):
    try:
        courses.set_course_published(course_id, True)
    except KeyError:
        raise HTTPException(status_code=404, detail="Course not found")
    
    admin_audit.write_audit("publish_course", "course", course_id, admin.uid)
    
    course = courses.get_course_admin(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.post("/courses/{course_id}/unpublish", response_model=CourseAdmin)
async def unpublish_course(course_id: str, admin: UserContext = Depends(require_admin)):
    try:
        courses.set_course_published(course_id, False)
    except KeyError:
        raise HTTPException(status_code=404, detail="Course not found")
    
    admin_audit.write_audit("unpublish_course", "course", course_id, admin.uid)
    
    course = courses.get_course_admin(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

# --- Lessons ---

@router.get("/courses/{course_id}/lessons", response_model=List[LessonAdmin])
async def list_lessons(course_id: str, admin: UserContext = Depends(require_admin)):
    return lessons.list_lessons_by_course_admin(course_id)

@router.post("/lessons", response_model=LessonAdmin, status_code=201)
async def create_lesson(request: LessonUpsertRequest, admin: UserContext = Depends(require_admin)):
    lesson_id = lessons.create_lesson(request.dict())
    admin_audit.write_audit("create_lesson", "lesson", lesson_id, admin.uid, request.dict())
    
    lesson = lessons.get_lesson_admin(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson created but not found")
    return lesson

@router.put("/lessons/{lesson_id}", response_model=LessonAdmin)
async def update_lesson(lesson_id: str, request: LessonUpsertRequest, admin: UserContext = Depends(require_admin)):
    try:
        lessons.update_lesson(lesson_id, request.dict())
    except KeyError:
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    admin_audit.write_audit("update_lesson", "lesson", lesson_id, admin.uid, request.dict())
    
    lesson = lessons.get_lesson_admin(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

@router.delete("/lessons/{lesson_id}", status_code=204)
async def delete_lesson(lesson_id: str, admin: UserContext = Depends(require_admin)):
    try:
        lessons.delete_lesson(lesson_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Lesson not found")
    admin_audit.write_audit("delete_lesson", "lesson", lesson_id, admin.uid)

# --- Plans ---

@router.get("/courses/{course_id}/plans", response_model=List[PlanAdmin])
async def list_plans(course_id: str, admin: UserContext = Depends(require_admin)):
    return plans.list_plans_by_course_admin(course_id)

@router.post("/plans", response_model=PlanAdmin, status_code=201)
async def create_plan(request: PlanUpsertRequest, admin: UserContext = Depends(require_admin)):
    plan_id = plans.create_plan(request.dict())
    admin_audit.write_audit("create_plan", "plan", plan_id, admin.uid, request.dict())
    
    plan = plans.get_plan_admin(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan created but not found")
    return plan

@router.put("/plans/{plan_id}", response_model=PlanAdmin)
async def update_plan(plan_id: str, request: PlanUpsertRequest, admin: UserContext = Depends(require_admin)):
    try:
        plans.update_plan(plan_id, request.dict())
    except KeyError:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    admin_audit.write_audit("update_plan", "plan", plan_id, admin.uid, request.dict())
    
    plan = plans.get_plan_admin(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.delete("/plans/{plan_id}", status_code=204)
async def delete_plan(plan_id: str, admin: UserContext = Depends(require_admin)):
    try:
        plans.delete_plan(plan_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Plan not found")
    admin_audit.write_audit("delete_plan", "plan", plan_id, admin.uid)

# --- Users / Revoke ---

@router.get("/users")
async def list_users(limit: int = 50, admin: UserContext = Depends(require_admin)):
    db = get_db()
    
    # Collect UIDs from entitlements + subscriptions + purchases
    uids = set()
    
    for doc in db.collection("entitlements").limit(500).stream():
        uid = doc.to_dict().get("uid")
        if uid:
            uids.add(uid)
            
    for doc in db.collection("subscriptions").limit(500).stream():
        uid = doc.to_dict().get("uid") or doc.id
        if uid:
            uids.add(uid)
            
    for doc in db.collection("purchases").limit(500).stream():
        uid = doc.to_dict().get("uid")
        if uid:
            uids.add(uid)
            
    # Return stable, limited list
    out = sorted(list(uids))[:limit]
    return {"users": [{"uid": uid} for uid in out], "count": len(out)}

@router.post("/users/{uid}/revoke")
async def revoke_access(uid: str, admin: UserContext = Depends(require_admin)):
    """
    Revoke all entitlements for a user.
    """
    db = get_db()
    # Fix: use simple where syntax compliant with pinned library
    ents = db.collection("entitlements").where("uid", "==", uid).stream()
    
    count = 0
    batch = db.batch()
    for doc in ents:
        # Use server timestamp or python datetime, consistent with repos
        from datetime import datetime, timezone
        batch.update(doc.reference, {"status": "inactive", "updatedAt": datetime.now(timezone.utc)})
        count += 1
        
    if count > 0:
        batch.commit()
    
    admin_audit.write_audit("revoke_access", "user", uid, admin.uid, {"revoked_count": count})
    return {"status": "revoked", "count": count}

# --- Metrics ---

@router.get("/metrics/overview", response_model=MetricsOverview)
async def get_metrics(admin: UserContext = Depends(require_admin)):
    db = get_db()
    
    # Helper to count using limit stream (safer for v1/compatibility)
    def count_docs(query, limit=1000):
        # Stream IDs only to be lighter? 
        # Actually .stream() fetches docs. .select(['id']) might help if possible but 
        # python-firestore often fetches full.
        # For V1 MVP, simple stream limit is fine.
        # TODO: Replace with aggregation count in prod (query.count()) when available/required
        return len(list(query.limit(limit).stream()))

    courses_ref = db.collection("courses")
    lessons_ref = db.collection("lessons")
    plans_ref = db.collection("plans")
    purchases_ref = db.collection("purchases")
    subs_ref = db.collection("subscriptions")
    ents_ref = db.collection("entitlements")

    return MetricsOverview(
        courses_total=count_docs(courses_ref),
        courses_published=count_docs(courses_ref.where("published", "==", True)),
        lessons_total=count_docs(lessons_ref),
        lessons_published=count_docs(lessons_ref.where("published", "==", True)),
        plans_total=count_docs(plans_ref),
        plans_published=count_docs(plans_ref.where("published", "==", True)),
        purchases_total=count_docs(purchases_ref),
        subscriptions_total=count_docs(subs_ref),
        entitlements_total=count_docs(ents_ref)
    )
