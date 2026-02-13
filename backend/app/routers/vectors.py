from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_current_user, get_admin_user, get_vector_service
from app.services.embedding_service import embedding_service
from app.services.processing_queue_service import processing_worker
from app.services.vector_service import VectorService

router = APIRouter(prefix="/videos", tags=["vectors"])

# ==================== Request/Response Models ====================

class ProcessVideosRequest(BaseModel):
    video_ids: List[str]
    priority: int = 0

class ProcessVideosResponse(BaseModel):
    success: bool
    queued_count: int
    skipped_count: int
    message: str

class VideoStatusResponse(BaseModel):
    video_id: str
    status: Optional[str]
    has_embedding: bool
    has_transcript: bool
    updated_at: Optional[str]

class SimilarVideo(BaseModel):
    video_id: str
    title: str
    similarity_score: float
    course_id: str
    thumbnail: Optional[str] = None

class SimilarVideosResponse(BaseModel):
    video_id: str
    similar_videos: List[SimilarVideo]

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    course_id: Optional[str] = None

class SearchResult(BaseModel):
    video_id: str
    title: str
    similarity_score: float
    course_id: str
    transcript_preview: str
    thumbnail: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]

class QueueStatusResponse(BaseModel):
    pending: int
    processing: int
    completed: int
    failed: int

# ==================== Endpoints ====================

@router.post("/process", response_model=ProcessVideosResponse)
async def process_videos(
    request: ProcessVideosRequest,
    admin = Depends(get_admin_user)
):
    if not request.video_ids:
        raise HTTPException(status_code=400, detail="No video IDs provided")
    
    results = await processing_worker.add_batch_to_queue(
        request.video_ids,
        priority=request.priority
    )
    
    return ProcessVideosResponse(
        success=True,
        queued_count=results["queued"],
        skipped_count=results["skipped"],
        message=f"Queued {results['queued']} videos for processing"
    )

@router.get("/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(
    video_id: str,
    user = Depends(get_current_user),
    vector_service: VectorService = Depends(get_vector_service)
):
    video = await vector_service.get_video_status(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return VideoStatusResponse(
        video_id=video_id,
        status=video.get("processing_status"),
        has_embedding=video.get("embedding") is not None,
        has_transcript=bool(video.get("transcript", "").strip()),
        updated_at=video.get("embedding_generated_at", "").isoformat() if video.get("embedding_generated_at") else None
    )

@router.get("/{video_id}/similar", response_model=SimilarVideosResponse)
async def get_similar_videos(
    video_id: str,
    limit: int = 5,
    course_id: Optional[str] = None,
    user = Depends(get_current_user),
    vector_service: VectorService = Depends(get_vector_service)
):
    similar = await vector_service.find_similar_videos(video_id, limit, course_id)
    if similar is None:
        raise HTTPException(status_code=404, detail="Video not found")
        
    return SimilarVideosResponse(
        video_id=video_id,
        similar_videos=[SimilarVideo(**v) for v in similar]
    )

@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    user = Depends(get_current_user),
    vector_service: VectorService = Depends(get_vector_service)
):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    results = await vector_service.semantic_search(request.query, request.limit, request.course_id)
    return SearchResponse(
        query=request.query,
        results=[SearchResult(**r) for r in results]
    )

# ==================== Admin/Monitoring Endpoints ====================

@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(admin = Depends(get_admin_user)):
    status = await processing_worker.get_queue_status()
    return QueueStatusResponse(**status)

@router.post("/queue/retry-failed")
async def retry_failed_jobs(admin = Depends(get_admin_user)):
    count = await processing_worker.retry_failed_jobs()
    return {"success": True, "message": f"Reset {count} failed jobs to pending"}

@router.post("/queue/clear-completed")
async def clear_completed_jobs(
    older_than_days: int = 7,
    admin = Depends(get_admin_user)
):
    count = await processing_worker.clear_completed_jobs(older_than_days)
    return {"success": True, "message": f"Removed {count} completed jobs older than {older_than_days} days"}
