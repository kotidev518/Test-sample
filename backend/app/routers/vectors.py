"""
Vector Search Router - API endpoints for semantic search and similarity detection
Uses SBERT embeddings for video recommendations and content discovery
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..database import db
from ..dependencies import get_current_user, get_admin_user
from ..embedding_service import embedding_service
from ..processing_queue_service import processing_worker


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
    """
    Queue one or more videos for embedding generation (Admin only).
    Videos will be processed asynchronously by the background worker.
    
    - **video_ids**: List of video IDs to process
    - **priority**: Higher priority videos are processed first (default: 0)
    """
    if not request.video_ids:
        raise HTTPException(status_code=400, detail="No video IDs provided")
    
    # Add videos to processing queue
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
    user = Depends(get_current_user)
):
    """
    Check the processing status of a video.
    
    Returns information about transcript and embedding availability.
    """
    video = await db.videos.find_one({"id": video_id})
    
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
    user = Depends(get_current_user)
):
    """
    Find videos similar to the specified video using cosine similarity.
    
    - **video_id**: Source video ID
    - **limit**: Maximum number of similar videos to return (default: 5)
    - **course_id**: Optional - Filter results by course
    """
    # Fetch source video
    source_video = await db.videos.find_one({"id": video_id})
    
    if not source_video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check if video has embedding
    source_embedding = source_video.get("embedding")
    if not source_embedding:
        raise HTTPException(
            status_code=400,
            detail="Video has no embedding. Process it first using /videos/process endpoint"
        )
    
    # Fetch all videos with embeddings (excluding source video)
    query = {
        "embedding": {"$exists": True, "$ne": None},
        "id": {"$ne": video_id}
    }
    
    if course_id:
        query["course_id"] = course_id
    
    candidate_videos = await db.videos.find(
        query,
        {"id": 1, "title": 1, "embedding": 1, "course_id": 1, "thumbnail": 1, "_id": 0}
    ).to_list(length=1000)  # Limit to prevent memory issues
    
    if not candidate_videos:
        return SimilarVideosResponse(video_id=video_id, similar_videos=[])
    
    # Prepare candidates for similarity computation
    candidates = [(v["id"], v["embedding"]) for v in candidate_videos]
    
    # Find most similar videos
    similar = await embedding_service.find_most_similar(
        source_embedding,
        candidates,
        top_k=limit
    )
    
    # Build response with video details
    similar_videos = []
    for vid, score in similar:
        video_data = next((v for v in candidate_videos if v["id"] == vid), None)
        if video_data:
            similar_videos.append(SimilarVideo(
                video_id=vid,
                title=video_data["title"],
                similarity_score=round(score, 4),
                course_id=video_data["course_id"],
                thumbnail=video_data.get("thumbnail")
            ))
    
    return SimilarVideosResponse(
        video_id=video_id,
        similar_videos=similar_videos
    )


@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    user = Depends(get_current_user)
):
    """
    Perform semantic search across all videos using natural language query.
    
    - **query**: Natural language search query (e.g., "learn python loops")
    - **limit**: Maximum number of results (default: 10)
    - **course_id**: Optional - Filter results by course
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    # Generate embedding for search query
    query_embedding = await embedding_service.generate_embedding(request.query)
    
    if not query_embedding:
        raise HTTPException(status_code=500, detail="Failed to generate query embedding")
    
    # Fetch all videos with embeddings
    query = {"embedding": {"$exists": True, "$ne": None}}
    
    if request.course_id:
        query["course_id"] = request.course_id
    
    candidate_videos = await db.videos.find(
        query,
        {"id": 1, "title": 1, "embedding": 1, "course_id": 1, "transcript": 1, "thumbnail": 1, "_id": 0}
    ).to_list(length=1000)
    
    if not candidate_videos:
        return SearchResponse(query=request.query, results=[])
    
    # Prepare candidates for similarity computation
    candidates = [(v["id"], v["embedding"]) for v in candidate_videos]
    
    # Find most similar videos
    similar = await embedding_service.find_most_similar(
        query_embedding,
        candidates,
        top_k=request.limit
    )
    
    # Build response with video details
    results = []
    for vid, score in similar:
        video_data = next((v for v in candidate_videos if v["id"] == vid), None)
        if video_data:
            # Create transcript preview (first 150 chars)
            transcript = video_data.get("transcript", "")
            preview = transcript[:150] + "..." if len(transcript) > 150 else transcript
            
            results.append(SearchResult(
                video_id=vid,
                title=video_data["title"],
                similarity_score=round(score, 4),
                course_id=video_data["course_id"],
                transcript_preview=preview,
                thumbnail=video_data.get("thumbnail")
            ))
    
    return SearchResponse(
        query=request.query,
        results=results
    )


# ==================== Admin/Monitoring Endpoints ====================

@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(admin = Depends(get_admin_user)):
    """
    Get current processing queue statistics (Admin only).
    
    Returns counts of videos in each processing state.
    """
    status = await processing_worker.get_queue_status()
    return QueueStatusResponse(**status)


@router.post("/queue/retry-failed")
async def retry_failed_jobs(admin = Depends(get_admin_user)):
    """
    Retry all failed processing jobs (Admin only).
    
    Resets failed jobs to pending status for reprocessing.
    """
    count = await processing_worker.retry_failed_jobs()
    return {
        "success": True,
        "message": f"Reset {count} failed jobs to pending"
    }


@router.post("/queue/clear-completed")
async def clear_completed_jobs(
    older_than_days: int = 7,
    admin = Depends(get_admin_user)
):
    """
    Remove completed jobs from queue (Admin only).
    
    - **older_than_days**: Remove jobs completed more than N days ago (default: 7)
    """
    count = await processing_worker.clear_completed_jobs(older_than_days)
    return {
        "success": True,
        "message": f"Removed {count} completed jobs older than {older_than_days} days"
    }
