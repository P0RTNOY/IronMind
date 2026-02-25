from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_current_user
from app.models import UserContext, AccessMeResponse, AccessCheckResponse
from app.services import access_service
from app.repos import activity_events
from app.repos import courses

router = APIRouter()

@router.get("/me", response_model=AccessMeResponse)
async def get_access_me(user: UserContext = Depends(get_current_user)):
    """
    Get current user's access status and entitlements.
    """
    summary = access_service.get_access_summary(user.uid)
    return {
        "uid": user.uid,
        "email": user.email,
        "isAdmin": user.is_admin,
        **summary
    }

@router.get("/courses/{course_id}", response_model=AccessCheckResponse)
async def check_course_access(course_id: str, user: UserContext = Depends(get_current_user)):
    """
    Check if user can access a specific course.
    Returns 200 { "allowed": true } if allowed.
    Returns 403 if not allowed.
    Returns 404 if course does not exist.
    """
    # Verify course existence (even if unpublished, we check existence first)
    # Using get_course_admin to check existence without exposing data
    course = courses.get_course_admin(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    allowed = access_service.can_access_course(user.uid, course_id)
    if not allowed:
        # Return 403 as requested
        raise HTTPException(status_code=403, detail="Access denied")
        
    return {"allowed": True}
