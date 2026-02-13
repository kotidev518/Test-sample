"""
Admin router for playlist import and admin-only operations
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_admin_user, get_course_service, get_playlist_service
from app.database import db
from app.services.playlist_service import PlaylistService
from app.services.youtube_service import youtube_service
from app.services.transcript_service import transcript_service
from app.services.processing_queue_service import processing_worker
from app.services.video_service import VideoService
from app.services.course_service import CourseService
from app.queue import enqueue_quiz_job
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])

class PlaylistImportRequest(BaseModel):
    playlist_url: str
    difficulty: str = "Medium"

class ImportSummary(BaseModel):
    success: bool
    course_id: str
    course_title: str
    videos_imported: int
    quizzes_generated: int
    message: str

@router.post("/import-playlist", response_model=ImportSummary)
async def import_youtube_playlist(
    request: PlaylistImportRequest,
    admin = Depends(get_admin_user),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """Import a YouTube playlist as a course (metadata only)."""
    success, message, data = await playlist_service.import_playlist(
        request.playlist_url, request.difficulty, admin['id']
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return ImportSummary(
        success=True,
        course_id=data['course_id'],
        course_title=data['course_title'],
        videos_imported=data['videos_imported'],
        quizzes_generated=0,
        message=f"Imported {data['videos_imported']} videos. Processing in background."
    )

@router.get("/courses")
async def get_admin_courses(
    admin = Depends(get_admin_user),
    course_service: CourseService = Depends(get_course_service)
):
    """Get all courses (admin only)"""
    return await course_service.get_all_courses()

@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: str, 
    admin = Depends(get_admin_user),
    course_service: CourseService = Depends(get_course_service)
):
    """Delete a course and all its videos (admin only)"""
    success = await course_service.delete_course(course_id)
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return {"success": True, "message": "Course and associated data deleted successfully"}

@router.get("/processing-status/{course_id}")
async def get_course_processing_status(
    course_id: str,
    admin = Depends(get_admin_user)
):
    """Get processing progress for a course (admin only)."""
    status = await processing_worker.get_course_processing_status(course_id)
    return status

@router.post("/regenerate-quizzes")
async def regenerate_quizzes(
    course_id: str = None,
    admin = Depends(get_admin_user),
    course_service: CourseService = Depends(get_course_service)
):
    """Regenerate quizzes for all videos in a course."""
    # This logic still relies on queue.py and transcript_service.py which could be refactored later
    # For now, we keep it simple but use the service to get videos
    videos = await course_service.db.videos.find(
        {"course_id": course_id} if course_id else {}, 
        {"id": 1}
    ).to_list(1000)
    
    if not videos:
        raise HTTPException(status_code=404, detail="No videos found")
    
    video_ids = [v["id"] for v in videos]
    
    # Delete old quizzes
    quiz_ids = [f"quiz-{vid}" for vid in video_ids]
    await course_service.db.quizzes.delete_many({"id": {"$in": quiz_ids}})
    
    # Enqueue new quiz generation jobs
    for vid in video_ids:
        await enqueue_quiz_job(vid)
    
    return {
        "success": True, 
        "message": f"Enqueued {len(video_ids)} quiz generation jobs.",
        "video_count": len(video_ids)
    }
