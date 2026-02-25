"""
Dev-only seed router — creates demo content via admin endpoint.

Only mounted when ENV != "prod".
"""

from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.deps import require_admin
from app.models import UserContext
from app.dev.seed import seed_demo_data

router = APIRouter()


@router.post("/seed")
async def run_seed(force: int = 0, admin: UserContext = Depends(require_admin)):
    """
    Seed demo data (courses, lessons, plans) into Firestore.

    - Requires admin auth.
    - Returns 404 in production (route is not even mounted, but double-guard).
    - ?force=1 to overwrite existing docs.
    """
    if settings.ENV == "prod":
        raise HTTPException(status_code=404, detail="Not found")

    result = seed_demo_data(force=bool(force))
    return result
