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
