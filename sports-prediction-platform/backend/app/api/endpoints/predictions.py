"""Prediction endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import PredictionResponse, PredictionCreate, APIResponse
from app.agents.master_orchestrator import get_master_orchestrator

router = APIRouter()


@router.get("/", response_model=List[PredictionResponse])
async def list_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all predictions with optional filtering."""
    # Implementation would query database
    return []


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(prediction_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific prediction by ID."""
    raise HTTPException(status_code=404, detail="Prediction not found")


@router.post("/generate", response_model=APIResponse)
async def generate_prediction(
    match_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Generate a new prediction for a match using the multi-agent system."""
    orchestrator = get_master_orchestrator()
    
    input_data = {
        "match_id": match_id,
    }
    
    result = await orchestrator.run_with_retry(input_data)
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    return APIResponse(
        success=True,
        data=result.data,
        message="Prediction generated successfully",
    )


@router.get("/value-bets", response_model=List[PredictionResponse])
async def get_value_bets(
    min_value_pct: float = Query(5.0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get all detected value betting opportunities."""
    return []
