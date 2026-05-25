"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_status():
    """Check API health."""
    return {"status": "healthy", "service": "sports-prediction-api"}


@router.get("/ready")
async def readiness_check():
    """Check if service is ready to accept requests."""
    return {"ready": True}
