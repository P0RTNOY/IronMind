from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.models import (
    UserContext, 
    CourseUpsertRequest, CourseAdmin, 
    LessonUpsertRequest, LessonAdmin,
    PlanUpsertRequest, PlanAdmin,
    MetricsOverview,
    AdminUsersListResponse, AdminUserDetailResponse, AdminUserRow, Entitlement
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


# --- Users / Revoke ---

@router.get("/users", response_model=AdminUsersListResponse)
async def list_users(limit: int = 50, cursor: Optional[str] = None, admin: UserContext = Depends(require_admin)):
    from app.repos import users
    from app.services import access_service
    
    if limit > 200:
        raise HTTPException(status_code=422, detail="Limit cannot exceed 200")
        
    user_dicts, next_cursor = users.list_users(limit, cursor)
    
    # Enrich with access status
    # Note: efficient enough for 50 users? 
    # For each user, we need to check membership and entitlements.
    # access_service.get_access_summary does 2 reads (membership, list_entitlements).
    # 50 * 2 = 100 reads. Firestore allows this, but it's heavier than just listing users.
    # User asked for "rich user objects". 
    # For MVP, N+1 is acceptable for admin panel with low traffic.
    
    rows = []
    for u in user_dicts:
        uid = u['uid']
        summary = access_service.get_access_summary(uid)
        rows.append(AdminUserRow(
            uid=uid,
            email=u.get('email'),
            name=u.get('name'),
            lastSeenAt=u.get('lastSeenAt'),
            membershipActive=summary['membershipActive'],
            membershipExpiresAt=summary['membershipExpiresAt'],
            entitledCourseIds=summary['entitledCourseIds']
        ))
        
    return {"users": rows, "nextCursor": next_cursor}

@router.get("/users/{uid}", response_model=AdminUserDetailResponse)
async def get_user_detail(uid: str, admin: UserContext = Depends(require_admin)):
    from app.repos import users, entitlements
    from app.services import access_service
    
    user_data = users.get_user(uid)
    if not user_data:
         raise HTTPException(status_code=404, detail="User not found")
         
    summary = access_service.get_access_summary(uid)
    
    profile = AdminUserRow(
        uid=uid,
        email=user_data.get('email'),
        name=user_data.get('name'),
        lastSeenAt=user_data.get('lastSeenAt'),
        membershipActive=summary['membershipActive'],
        membershipExpiresAt=summary['membershipExpiresAt'],
        entitledCourseIds=summary['entitledCourseIds']
    )
    
    ents = entitlements.list_entitlements(uid)
    # Filter? No, show all history
    
    # Purchases repo? Not implemented yet, return empty
    purchases = []
    
    return {
        "profile": profile,
        "entitlements": ents,
        "purchases": purchases
    }

class GrantCourseRequest(BaseModel):
    courseId: str
    
@router.post("/users/{uid}/entitlements", response_model=Entitlement)
async def grant_course_access(uid: str, request: GrantCourseRequest, admin: UserContext = Depends(require_admin)):
    from app.repos import entitlements, courses
    
    # Verify course exists
    if not courses.get_course_admin(request.courseId):
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Grant
    ent = entitlements.grant_course(uid, request.courseId, source="manual")
    
    admin_audit.write_audit("grant_course", "user", uid, admin.uid, {"courseId": request.courseId})
    
    return ent

@router.delete("/entitlements/{ent_id}", status_code=204)
async def revoke_entitlement(ent_id: str, admin: UserContext = Depends(require_admin)):
    from app.repos import entitlements
    
    try:
        entitlements.set_status(ent_id, "inactive")
    except KeyError:
        raise HTTPException(status_code=404, detail="Entitlement not found")
        
    admin_audit.write_audit("revoke_entitlement", "entitlement", ent_id, admin.uid)
    
# --- Metrics ---


# --- Metrics ---

class AnalyticsPoint(BaseModel):
    date: str
    signups: int
    active: int

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
    users_ref = db.collection("users")

    return MetricsOverview(
        users_total=count_docs(users_ref),
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

@router.get("/analytics/growth", response_model=List[AnalyticsPoint])
async def get_growth_data(days: int = 30, admin: UserContext = Depends(require_admin)):
    from app.repos import analytics
    return analytics.get_growth_data(days)
