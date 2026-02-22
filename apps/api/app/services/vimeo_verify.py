import logging
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel

from app.config import settings
from app.services import vimeo_client

logger = logging.getLogger(__name__)


class VerificationResult(BaseModel):
    ok: bool
    embed_mode: Optional[str] = None
    allowed_domains: List[str] = []
    missing_domains: List[str] = []
    checked_at: datetime
    warnings: List[str] = []


def _normalize_domain(domain: str) -> str:
    """Strip protocol, path, and port; make lowercase."""
    d = domain.lower().strip()
    if "://" in d:
        d = d.split("://")[-1]
    d = d.split("/")[0]
    d = d.split(":")[0]
    return d


async def verify_video_domains(video_id: str) -> VerificationResult:
    """
    Verifies a Vimeo video's privacy settings against required config.
    """
    now = datetime.now(timezone.utc)
    
    if not settings.VIMEO_VERIFY_ENABLED:
        raise NotImplementedError("Vimeo privacy verification is disabled")

    warnings = []
    embed_mode = None
    allowed_domains = []
    
    # 1. Fetch video metadata
    video_data = await vimeo_client.get_video(video_id)
    embed_mode = video_data.get("privacy", {}).get("embed")
    if not embed_mode:
        warnings.append("Could not read embed privacy mode")
    elif embed_mode not in ("whitelist", "domains"):
        warnings.append(f"Unexpected embed mode: {embed_mode}")

    # 2. Fetch allowed domains
    allowed_domains = await vimeo_client.get_embed_domains(video_id)

    # 3. Compare required vs actual
    required_domains = [_normalize_domain(d) for d in settings.VIMEO_REQUIRED_EMBED_ORIGINS]
    actual_normalized = [_normalize_domain(d) for d in allowed_domains]
    
    missing_domains = [d for d in required_domains if d not in actual_normalized]
    
    # 4. Determine overall status
    is_ok = len(missing_domains) == 0 and embed_mode in ("whitelist", "domains")
    
    return VerificationResult(
        ok=is_ok,
        embed_mode=embed_mode,
        allowed_domains=actual_normalized,  # using normalized for clarity
        missing_domains=missing_domains,
        checked_at=now,
        warnings=warnings,
    )
