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
    Import a YouTube playlist as a course with all its videos.
    Uses Gemini AI for accurate topics and clean transcripts.
    Requires admin authentication.
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
    
    # Fetch playlist details
    playlist_details = await youtube_service.get_playlist_details(playlist_id)
    if not playlist_details:
        raise HTTPException(
            status_code=404,
            detail="Could not fetch playlist details. Check if the playlist is public."
        )
    
    # Fetch all videos from playlist
    playlist_videos = await youtube_service.get_playlist_videos(playlist_id)
    if not playlist_videos:
        raise HTTPException(
            status_code=404,
            detail="No videos found in this playlist. It may be empty or private."
        )
    
    # Get detailed info for all videos (duration, tags)
    video_ids = [v['video_id'] for v in playlist_videos]
    video_details = await youtube_service.get_video_details(video_ids)
    
    # Generate AI-powered course topics from first few video titles
    sample_titles = " | ".join([v['title'] for v in playlist_videos[:5]])
    course_topics = await gemini_service.generate_topics(playlist_details['title'], sample_titles)
    
    # Create course document
    course_id = playlist_id  # Use playlist ID as course ID
    course_doc = {
        "id": course_id,
        "title": playlist_details['title'],
        "description": await gemini_service.generate_transcript_summary(
            playlist_details['title'], 
            playlist_details['description'] or ""
        ) or f"Course: {playlist_details['title']}",
        "difficulty": request.difficulty,
        "topics": course_topics,
        "thumbnail": playlist_details['thumbnail'],
        "video_count": len(playlist_videos),
        "channel": playlist_details['channel_title'],
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "imported_by": admin['id']
    }
    
    # Create video documents with progressive difficulty and AI-generated content
    video_docs = []
    total_videos = len(playlist_videos)
    
    for video in playlist_videos:
        vid = video['video_id']
        details = video_details.get(vid, {})
        position = video['position']
        
        # Assign progressive difficulty based on position in playlist
        video_difficulty = _get_progressive_difficulty(position, total_videos)
        
        # Generate AI-powered topics for this video
        video_topics = await gemini_service.generate_topics(video['title'], video['description'] or "")
        
        # Generate clean transcript/summary
        video_transcript = await gemini_service.generate_transcript_summary(
            video['title'], 
            video['description'] or ""
        )
        
        video_docs.append({
            "id": vid,
            "course_id": course_id,
            "title": video['title'],
            "description": video_transcript or f"Part of {playlist_details['title']}",
            "url": f"https://www.youtube.com/watch?v={vid}",
            "duration": details.get('duration', 0),
            "difficulty": video_difficulty,
            "topics": video_topics,
            "transcript": video_transcript,
            "order": position,
            "thumbnail": video['thumbnail']
        })
    
    # Generate AI-powered quizzes for each video
    quiz_docs = []
    for video_doc in video_docs:
        # Generate AI quiz using Gemini
        ai_questions = await gemini_service.generate_quiz(
            video_title=video_doc['title'],
            video_transcript=video_doc.get('transcript', ''),
            topics=video_doc.get('topics', []),
            difficulty=video_doc['difficulty']
        )
        
        quiz_docs.append({
            "id": f"quiz-{video_doc['id']}",
            "video_id": video_doc['id'],
            "questions": ai_questions
        })
    
    # Insert into database
    try:
        await db.courses.insert_one(course_doc)
        
        if video_docs:
            await db.videos.insert_many(video_docs)
        
        if quiz_docs:
            await db.quizzes.insert_many(quiz_docs)
            
    except Exception as e:
        # Rollback on error
        await db.courses.delete_one({"id": course_id})
        await db.videos.delete_many({"course_id": course_id})
        await db.quizzes.delete_many({"video_id": {"$in": [v['id'] for v in video_docs]}})
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import playlist: {str(e)}"
        )
    
    return ImportSummary(
        success=True,
        course_id=course_id,
        course_title=playlist_details['title'],
        videos_imported=len(video_docs),
        quizzes_generated=len(quiz_docs),
        message=f"Successfully imported '{playlist_details['title']}' with {len(video_docs)} videos"
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
            }
        ]
    }
