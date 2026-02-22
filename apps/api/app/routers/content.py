"""
Content router — entitlement-gated content delivery.

Provides signed download URLs for protected assets (PDF plans)
and gated playback info for lesson videos.
"""

import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import settings
from app.deps import get_current_user
from app.models import UserContext
from app.repos import plans as plans_repo
from app.repos import lessons as lessons_repo
from app.services import access_service
from app.services.storage import generate_signed_download_url

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed prefixes for PDF paths (reject traversal / URLs)
_ALLOWED_PREFIXES = ("plans/", "pdfs/", "uploads/")  # TODO: tighten once conventions are stable


def _validate_pdf_path(path: str) -> bool:
    """
    Validate that a pdfPath is a safe, relative GCS blob name.
    Rejects traversal attacks, absolute paths, and URLs.
    """
    if not path or not path.strip():
        return False
    if ".." in path:
        return False
    if path.startswith(("gs://", "http://", "https://", "/")):
        return False
    if not path.startswith(_ALLOWED_PREFIXES):
        return False
    return True


@router.get("/plans/{plan_id}/download")
async def download_plan_pdf(
    plan_id: str,
    user: UserContext = Depends(get_current_user),
):
    """
    Return a short-lived signed download URL for a plan's PDF.
    Requires authentication + course entitlement.
    """
    uid = user.uid
    log_ctx = {"uid": uid, "plan_id": plan_id}

    # 1. Load plan
    plan = plans_repo.get_plan_admin(plan_id)
    if not plan:
        logger.info("Plan not found", extra=log_ctx)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    course_id = plan.get("courseId")
    log_ctx["courseId"] = course_id

    if not course_id:
        logger.info("Plan has no courseId", extra=log_ctx)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan has no associated course")

    # 2. Access check
    allowed = access_service.can_access_course(uid, course_id)
    if not allowed:
        logger.info("Access denied for plan download", extra=log_ctx)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # 3. Verify pdfPath exists
    pdf_path = plan.get("pdfPath")
    if not pdf_path:
        logger.info("Plan has no PDF attached", extra=log_ctx)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No PDF available for this plan")

    # 4. Validate pdfPath is safe
    if not _validate_pdf_path(pdf_path):
        logger.warning("Invalid pdfPath rejected", extra={**log_ctx, "pdfPath": pdf_path})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PDF path")

    # 5. Generate signed URL
    ttl = settings.SIGNED_URL_TTL_SECONDS
    url = generate_signed_download_url(pdf_path, ttl_seconds=ttl)

    logger.info("Plan PDF download URL generated", extra=log_ctx)

    return {"url": url, "expiresIn": ttl}


# ── Lesson video playback ───────────────────────────────────────────

@router.get("/lessons/{lesson_id}/playback")
async def get_lesson_playback(
    lesson_id: str,
    request: Request,
    user: UserContext = Depends(get_current_user),
):
    """
    Return playback info (embed URL) for a lesson video.
    Requires authentication + course entitlement.
    """
    uid = user.uid
    log_ctx = {"uid": uid, "lesson_id": lesson_id}

    # Advisory logging for unknown origins
    raw_origin = request.headers.get("origin") or request.headers.get("referer")
    if raw_origin:
        parsed = urlparse(raw_origin)
        # Reconstruct normalized origin (scheme://netloc)
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else raw_origin
        
        if origin not in settings.ALLOWED_EMBED_ORIGINS:
            if settings.ENV == "prod":
                logger.warning("Vimeo playback payload requested from unverified origin",
                               extra={**log_ctx, "origin": origin, "raw_origin": raw_origin})

    # 1. Load lesson
    lesson = lessons_repo.get_lesson_admin(lesson_id)
    if not lesson:
        logger.info("Lesson not found", extra=log_ctx)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    course_id = lesson.get("courseId")
    log_ctx["courseId"] = course_id

    if not course_id:
        logger.info("Lesson has no courseId", extra=log_ctx)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson has no associated course")

    # 2. Access check
    allowed = access_service.can_access_course(uid, course_id)
    if not allowed:
        logger.info("Access denied for lesson playback", extra=log_ctx)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # 3. Verify video exists (do NOT log video ID)
    video_id = lesson.get("vimeoVideoId")
    if not video_id:
        logger.info("Lesson has no video", extra=log_ctx)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No video available for this lesson")

    # 4. Build embed URL
    embed_url = f"{settings.VIMEO_EMBED_BASE_URL}/{video_id}"

    logger.info("Lesson playback URL generated", extra=log_ctx)

    return {"provider": settings.VIDEO_PROVIDER, "embedUrl": embed_url, "expiresIn": None}
