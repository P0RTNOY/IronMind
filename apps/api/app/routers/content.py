"""
Content router — entitlement-gated content delivery.

Provides signed download URLs for protected assets (PDF plans).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.deps import get_current_user
from app.models import UserContext
from app.repos import plans as plans_repo
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
