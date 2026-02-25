"""
Admin activity endpoint — returns recent activity events.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.deps import require_admin
from app.models import UserContext
from app.repos import activity_events

router = APIRouter()


@router.get("/activity")
async def list_activity(limit: int = 50, admin: UserContext = Depends(require_admin)):
    """Return recent activity events. Max limit: 200."""
    if limit > 200:
        raise HTTPException(status_code=422, detail="Limit too high (max 200)")
    events = activity_events.list_recent(limit)
    return events
