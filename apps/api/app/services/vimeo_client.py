import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class VimeoAPIError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


def _normalize_video_id(video_id: str) -> str:
    """
    Extracts the clean numeric ID from raw string inputs:
    - '123456789' -> '123456789'
    - ' /videos/123456789 ' -> '123456789'
    - 'https://vimeo.com/123456789' -> '123456789'
    - 'https://player.vimeo.com/video/123456789' -> '123456789'
    """
    if not video_id:
        return ""
        
    cleaned = str(video_id).strip()
    
    # Take the last segment after any slash
    if "/" in cleaned:
        cleaned = cleaned.rstrip("/").split("/")[-1]
        
    cleaned = cleaned.split("?")[0].split("#")[0]
        
    return cleaned


_client: Optional[httpx.AsyncClient] = None

def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is not None:
        return _client
        
    token = settings.VIMEO_ACCESS_TOKEN
    if not token:
        raise VimeoAPIError("Vimeo access token not configured", status_code=500)
    
    _client = httpx.AsyncClient(
        base_url=settings.VIMEO_API_BASE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.vimeo.*+json;version=3.4",
        },
        timeout=settings.VIMEO_VERIFY_TIMEOUT_SECONDS,
    )
    return _client


async def get_video(video_id: str) -> dict:
    """
    Fetch video details from Vimeo.
    Returns the video dict, specifically containing ['privacy']['embed'].
    """
    clean_id = _normalize_video_id(video_id)
    if not clean_id:
        raise VimeoAPIError("Invalid video ID", status_code=400)
        
    logger.debug(f"Fetching Vimeo video detais for ID: {clean_id}")
    
    try:
        client = _get_client()
        resp = await client.get(f"/videos/{clean_id}")
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        logger.error(f"Vimeo API HTTP error fetching video: {status}")
        raise VimeoAPIError(f"Vimeo API error: {status}", status_code=status)
    except Exception as e:
        logger.error(f"Vimeo API network error: {e}")
        raise VimeoAPIError("Failed to connect to Vimeo API", status_code=502)


async def get_embed_domains(video_id: str) -> list[str]:
    """
    Fetch the list of allowed embed domains for a video.
    Returns a list of strings.
    """
    clean_id = _normalize_video_id(video_id)
    if not clean_id:
        raise VimeoAPIError("Invalid video ID", status_code=400)
        
    logger.debug(f"Fetching Vimeo embed domains for ID: {clean_id}")
    
    try:
        client = _get_client()
        resp = await client.get(f"/videos/{clean_id}/privacy/domains")
        resp.raise_for_status()
        data = resp.json()
        # The structure is usually {"data": [{"domain": "example.com"}, ...]}
        domains = []
        for item in data.get("data", []):
            domain = item.get("domain")
            if domain:
                domains.append(domain)
        return domains
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        logger.error(f"Vimeo API HTTP error fetching domains: {status}")
        raise VimeoAPIError(f"Vimeo API domain error: {status}", status_code=status)
    except Exception as e:
        logger.error(f"Vimeo API network error: {e}")
        raise VimeoAPIError("Failed to connect to Vimeo API", status_code=502)
