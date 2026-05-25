"""Bankroll and betting management endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import BankrollResponse, BetResponse

router = APIRouter()


@router.get("/", response_model=BankrollResponse)
async def get_bankroll(db: AsyncSession = Depends(get_db)):
    """Get current bankroll status."""
    pass


@router.get("/bets", response_model=List[BetResponse])
async def list_bets(db: AsyncSession = Depends(get_db)):
    """List all placed bets."""
    return []


@router.get("/performance")
async def get_performance_metrics(db: AsyncSession = Depends(get_db)):
    """Get performance metrics including ROI, yield, win rate."""
    return {
        "roi": 0.0,
        "yield": 0.0,
        "win_rate": 0.0,
        "total_bets": 0,
        "profit": 0.0,
    }
