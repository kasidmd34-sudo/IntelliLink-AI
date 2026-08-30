from fastapi import APIRouter
from app.config.settings import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "model": settings.GEMINI_MODEL,
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }