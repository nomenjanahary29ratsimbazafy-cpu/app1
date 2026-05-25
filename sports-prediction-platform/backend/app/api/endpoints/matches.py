"""Match endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import MatchResponse

router = APIRouter()


@router.get("/", response_model=List[MatchResponse])
async def list_matches(db: AsyncSession = Depends(get_db)):
    """List upcoming and recent matches."""
    return []


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: str, db: AsyncSession = Depends(get_db)):
    """Get match details by ID."""
    pass
