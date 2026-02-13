from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_user, get_recommendation_service
from ..schemas import NextVideoRecommendation
from ..services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/next-video", response_model=NextVideoRecommendation)
async def get_next_video_recommendation(
    user = Depends(get_current_user),
    recommendation_service: RecommendationService = Depends(get_recommendation_service)
):
    """AI-based recommendation using SBERT embeddings and mastery scores"""
    recommendation = await recommendation_service.get_next_video_recommendation(user)
    if not recommendation:
        raise HTTPException(status_code=404, detail="No videos available")
    return recommendation
