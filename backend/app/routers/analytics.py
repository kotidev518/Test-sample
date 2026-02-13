from typing import List
from fastapi import APIRouter, Depends

from ..dependencies import get_current_user, get_analytics_service
from ..schemas import MasteryScore
from ..services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/mastery", response_model=List[MasteryScore])
async def get_mastery_scores(
    user = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    return await analytics_service.get_mastery_scores(user['id'])

@router.get("/progress")
async def get_overall_progress(
    user = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    return await analytics_service.get_overall_progress(user['id'])
