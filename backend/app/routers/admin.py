"""
Admin router for playlist import and admin-only operations
"""
from datetime import datetime, timezone
from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..database import db
from ..dependencies import get_admin_user
from ..youtube_service import youtube_service
from ..gemini_service import gemini_service
from ..transcript_service import transcript_service
from ..queue import enqueue_quiz_job

router = APIRouter(prefix="/admin", tags=["admin"])


class PlaylistImportRequest(BaseModel):
    playlist_url: str
    difficulty: str = "Medium"  # Easy, Medium, Hard - default for all videos


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
    admin = Depends(get_admin_user)
):
    """
    Import a YouTube playlist as a course (INSTANT - metadata only).
    Transcripts, embeddings, and quizzes are handled separately:
    - Transcripts + embeddings: background worker (async with rate limiting)
    - Quizzes: generated on-demand when user clicks a video
    """
    # Extract playlist ID from URL
    playlist_id = youtube_service.extract_playlist_id(request.playlist_url)
    if not playlist_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube playlist URL. Please provide a valid playlist URL."
        )
    
    # Check if playlist already imported
    existing_course = await db.courses.find_one({"id": playlist_id})
    if existing_course:
        raise HTTPException(
            status_code=409,
            detail=f"This playlist has already been imported as '{existing_course['title']}'"
        )
    
    # Fetch playlist details (instant - single YouTube API call)
    playlist_details = await youtube_service.get_playlist_details(playlist_id)
    if not playlist_details:
        raise HTTPException(
            status_code=404,
            detail="Could not fetch playlist details. Check if the playlist is public."
        )
    
    # Fetch all videos from playlist (instant - YouTube API)
    playlist_videos = await youtube_service.get_playlist_videos(playlist_id)
    if not playlist_videos:
        raise HTTPException(
            status_code=404,
            detail="No videos found in this playlist. It may be empty or private."
        )
    
    # Get detailed info for all videos: duration, tags (instant - YouTube API batch)
    video_ids = [v['video_id'] for v in playlist_videos]
    video_details = await youtube_service.get_video_details(video_ids)
    
    # Create course document using YouTube metadata directly (no Gemini call)
    course_id = playlist_id
    
    # Extract topics from YouTube tags across all videos
    all_tags = set()
    for vid in video_ids:
        details = video_details.get(vid, {})
        for tag in details.get('tags', []):
            all_tags.add(tag)
    course_topics = list(all_tags)[:10] if all_tags else ['General']
    
    course_doc = {
        "id": course_id,
        "title": playlist_details['title'],
        "description": playlist_details['description'] or f"Course: {playlist_details['title']}",
        "difficulty": request.difficulty,
        "topics": course_topics,
        "thumbnail": playlist_details['thumbnail'],
        "video_count": len(playlist_videos),
        "channel": playlist_details['channel_title'],
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "imported_by": admin['id']
    }
    
    # Create video documents using YouTube metadata only (no AI calls)
    video_docs = []
    total_videos = len(playlist_videos)
    
    for video in playlist_videos:
        vid = video['video_id']
        details = video_details.get(vid, {})
        position = video['position']
        
        # Progressive difficulty based on position
        video_difficulty = _get_progressive_difficulty(position, total_videos)
        
        # Use YouTube tags directly as topics
        video_tags = details.get('tags', [])[:5]
        if not video_tags:
            video_tags = course_topics[:3]
        
        video_docs.append({
            "id": vid,
            "course_id": course_id,
            "title": video['title'],
            "description": video['description'] or f"Part of {playlist_details['title']}",
            "url": f"https://www.youtube.com/watch?v={vid}",
            "duration": details.get('duration', 0),
            "difficulty": video_difficulty,
            "topics": video_tags,
            "transcript": "",  # Will be filled by background worker
            "order": position,
            "thumbnail": video['thumbnail'],
            "processing_status": "pending"  # Track background processing
        })
    
    # Insert into database (NO quizzes - generated on-demand)
    try:
        await db.courses.insert_one(course_doc)
        
        if video_docs:
            await db.videos.insert_many(video_docs)
        
        # Queue all videos for background transcript + embedding processing
        from ..processing_queue_service import processing_worker
        video_ids_to_queue = [v["id"] for v in video_docs]
        queue_results = await processing_worker.add_batch_to_queue(video_ids_to_queue, priority=1)
        
        print(f"✅ Imported playlist instantly: {playlist_details['title']}")
        print(f"   - Videos: {len(video_docs)}")
        print(f"   - Queued for processing: {queue_results['queued']}")
        
        return ImportSummary(
            success=True,
            course_id=course_id,
            course_title=playlist_details['title'],
            videos_imported=len(video_docs),
            quizzes_generated=0,  # Quizzes generated on-demand now
            message=f"Imported {len(video_docs)} videos instantly. Transcripts & embeddings processing in background. Quizzes will be generated when users watch videos."
        )
            
    except Exception as e:
        # Rollback on error
        await db.courses.delete_one({"id": course_id})
        await db.videos.delete_many({"course_id": course_id})
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import playlist: {str(e)}"
        )


@router.get("/courses")
async def get_admin_courses(admin = Depends(get_admin_user)):
    """Get all courses with import metadata (admin only)"""
    courses = await db.courses.find({}, {"_id": 0}).to_list(1000)
    return courses


@router.delete("/courses/{course_id}")
async def delete_course(course_id: str, admin = Depends(get_admin_user)):
    """Delete a course and all its videos (admin only)"""
    # Check if course exists
    course = await db.courses.find_one({"id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get all video IDs for this course first
    videos = await db.videos.find({"course_id": course_id}, {"id": 1}).to_list(1000)
    video_ids = [v["id"] for v in videos]
    
    # Delete quizzes by video_id (quiz IDs are "quiz-{video_id}")
    if video_ids:
        quiz_ids = [f"quiz-{vid}" for vid in video_ids]
        await db.quizzes.delete_many({"id": {"$in": quiz_ids}})
    
    # Delete videos and course
    await db.videos.delete_many({"course_id": course_id})
    await db.courses.delete_one({"id": course_id})
    
    return {"success": True, "message": f"Deleted course '{course['title']}' and all associated data"}


@router.get("/processing-status/{course_id}")
async def get_course_processing_status(
    course_id: str,
    admin = Depends(get_admin_user)
):
    """
    Get transcript/embedding processing progress for a course (admin only).

    Returns total videos and counts by processing_status:
    pending, processing, completed, failed — plus failed video details.
    """
    # Verify course exists
    course = await db.courses.find_one({"id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    from ..processing_queue_service import processing_worker
    status = await processing_worker.get_course_processing_status(course_id)
    return status


@router.post("/regenerate-quizzes")
async def regenerate_quizzes(
    course_id: str = None,
    admin = Depends(get_admin_user)
):
    """
    Regenerate quizzes for all videos (or a specific course) using real transcripts.
    Deletes old quizzes and creates new ones with Gemini AI + YouTube transcripts.
    """
    # Get videos to regenerate quizzes for
    query = {"course_id": course_id} if course_id else {}
    videos = await db.videos.find(query, {"_id": 0}).to_list(1000)
    
    if not videos:
        raise HTTPException(status_code=404, detail="No videos found")
    
    video_ids = [v["id"] for v in videos]
    
    # Fetch real transcripts for all videos
    print(f"Fetching transcripts for {len(video_ids)} videos...")
    transcripts = await transcript_service.get_transcripts_batch(video_ids)
    transcript_count = sum(1 for t in transcripts.values() if t)
    print(f"Successfully fetched {transcript_count}/{len(video_ids)} transcripts")
    
    # Delete old quizzes
    quiz_ids = [f"quiz-{vid}" for vid in video_ids]
    await db.quizzes.delete_many({"id": {"$in": quiz_ids}})
    
    # Enqueue new quiz generation jobs to ARQ
    print(f"Enqueuing quiz generation for {len(video_ids)} videos...")
    for vid in video_ids:
        await enqueue_quiz_job(vid)
    
    return {
        "success": True, 
        "message": f"Enqueued {len(video_ids)} quiz generation jobs to ARQ.",
        "video_count": len(video_ids)
    }
    
    return {
        "success": True,
        "quizzes_regenerated": len(new_quizzes),
        "transcripts_found": transcript_count,
        "message": f"Regenerated {len(new_quizzes)} quizzes using real transcripts"
    }



def _get_progressive_difficulty(position: int, total_videos: int) -> str:
    """
    Assign difficulty based on video position in playlist.
    First 33% = Easy, Middle 33% = Medium, Last 33% = Hard
    """
    if total_videos <= 1:
        return "Medium"
    
    progress = position / (total_videos - 1)  # 0.0 to 1.0
    
    if progress < 0.33:
        return "Easy"
    elif progress < 0.67:
        return "Medium"
    else:
        return "Hard"


def _extract_course_topics(playlist_videos: List[dict], video_details: dict) -> List[str]:
    """Extract unique topics from all videos in playlist"""
    topics = set()
    for video in playlist_videos:
        vid = video['video_id']
        if vid in video_details:
            for tag in video_details[vid].get('tags', []):
                topics.add(tag)
    
    # Limit to 10 most common topics
    topic_list = list(topics)[:10]
    return topic_list if topic_list else ['General']


def _generate_quiz_for_video(video: dict) -> dict:
    """Generate a basic quiz for a video based on its metadata"""
    topics = video.get('topics', ['General'])
    primary_topic = topics[0] if topics else 'General'
    
    return {
        "id": f"quiz-{video['id']}",
        "video_id": video['id'],
        "questions": [
            {
                "question": f"What is the main topic covered in '{video['title']}'?",
                "options": [
                    primary_topic,
                    "Unrelated Topic",
                    "Advanced Mathematics",
                    "Historical Events"
                ],
                "correct_answer": 0
            },
            {
                "question": "Which of the following best describes this video's content?",
                "options": [
                    "Entertainment only",
                    "Technical documentation",
                    video['description'][:50] + "..." if len(video['description']) > 50 else video['description'],
                    "None of the above"
                ],
                "correct_answer": 2
            },
            {
                "question": f"What is the difficulty level of this video?",
                "options": [
                    "Beginner",
                    video['difficulty'],
                    "Expert",
                    "Professional"
                ],
                "correct_answer": 1
            },
            {
                "question": f"Which concept is mentioned in this video?",
                "options": [
                    "Quantum Mechanics",
                    "Blockchain Technology",
                    primary_topic,
                    "Virtual Reality"
                ],
                "correct_answer": 2
            },
            {
                "question": f"Which additional topic is related to '{video['title']}'?",
                "options": [
                    "Cooking",
                    topics[1] if len(topics) > 1 else "General Concepts",
                    "Music Theory",
                    "Architecture"
                ],
                "correct_answer": 1
            }
        ]
    }
