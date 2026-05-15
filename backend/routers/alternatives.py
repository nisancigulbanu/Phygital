from __future__ import annotations

from fastapi import APIRouter, Query, Request

from backend.models.schemas import AlternativesResponse


router = APIRouter(prefix="/api/v1", tags=["alternatives"])


@router.get("/alternatives", response_model=AlternativesResponse)
async def alternatives(
    request: Request,
    current_quality_score: float = Query(default=0, ge=0, le=100),
) -> AlternativesResponse:
    """Return demo alternatives above the provided quality threshold."""
    return AlternativesResponse(
        alternatives=request.app.state.similarity_engine.find_alternatives(
            current_quality_score=current_quality_score,
        )
    )
