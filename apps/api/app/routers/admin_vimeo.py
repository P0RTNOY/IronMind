"""
Admin router for Vimeo integrations.

Provides endpoints to verify video privacy settings against our required domain list.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.deps import require_admin
from app.models import UserContext
from app.repos import lessons as lessons_repo
from app.services import vimeo_verify

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/lessons/{lesson_id}/verify", response_model=vimeo_verify.VerificationResult)
async def verify_lesson_video(
    lesson_id: str,
    admin: UserContext = Depends(require_admin),
):
    """
    Verifies that the video attached to a lesson has the correct embed privacy settings.
    Requires admin privileges.
    Saves the result to the lesson document.
    """
    if not settings.VIMEO_VERIFY_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="vimeo_verify_disabled",
        )

    # 1. Load lesson
    lesson = lessons_repo.get_lesson_admin(lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    video_id = lesson.get("vimeoVideoId")
    if not video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lesson has no Vimeo video ID")

    # 2. Verify settings via Vimeo API
    logger.info(f"Admin {admin.uid} verifying video privacy for lesson {lesson_id}")
    result = await vimeo_verify.verify_video_domains(video_id)

    # 3. Store result in DB
    verify_data = {
        "vimeoVerifyOk": result.ok,
        "vimeoVerifyCheckedAt": result.checked_at,
        "vimeoVerifyMissingDomains": result.missing_domains,
        "vimeoVerifyAllowedDomains": result.allowed_domains,
        "vimeoVerifyEmbedMode": result.embed_mode,
    }
    
    try:
        lessons_repo.update_lesson_verification(lesson_id, verify_data)
    except KeyError:
        # Lesson was deleted between read and update
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found during update")

    return result
