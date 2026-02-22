from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "env": settings.ENV,
        "version": settings.APP_VERSION
    }

@router.get("/healthz")
async def liveness_probe():
    return {"ok": True}

@router.get("/readyz")
async def readiness_probe():
    # Extend carefully if specific subsystem connects are needed, but for MVP:
    return {"ok": True}
