"""
API Routes for Sports Prediction Platform.
"""

from fastapi import APIRouter

from app.api.endpoints import (
    health,
    predictions,
    matches,
    agents,
    bankroll,
)

router = APIRouter()

# Include endpoint routers
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
router.include_router(matches.router, prefix="/matches", tags=["Matches"])
router.include_router(agents.router, prefix="/agents", tags=["Agents"])
router.include_router(bankroll.router, prefix="/bankroll", tags=["Bankroll"])
