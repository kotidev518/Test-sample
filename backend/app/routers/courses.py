from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException

from ..database import db
from ..schemas import Course, Video, VideoProgressUpdate, Quiz, QuizSubmission, QuizResult
from ..dependencies import get_current_user
from ..utils import get_video_url
from ..services import update_mastery_scores_for_video
from ..gemini_service import gemini_service

router = APIRouter(tags=["courses"])

# ==================== Course Routes ====================

@router.get("/courses", response_model=List[Course])
async def get_courses(user = Depends(get_current_user)):
    courses = await db.courses.find({}, {"_id": 0}).to_list(1000)
    return courses

@router.get("/courses/{course_id}", response_model=Course)
async def get_course(course_id: str, user = Depends(get_current_user)):
    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

# ==================== Video Routes ====================

@router.get("/videos", response_model=List[Video])
async def get_videos(course_id: Optional[str] = None, user = Depends(get_current_user)):
    query = {"course_id": course_id} if course_id else {}
    videos = await db.videos.find(query, {"_id": 0}).sort("order", 1).to_list(1000)
    
    # Process URLs
    for video in videos:
        if 'url' in video:
            video['url'] = get_video_url(video['url'])
            
    return videos

@router.get("/videos/{video_id}", response_model=Video)
async def get_video(video_id: str, user = Depends(get_current_user)):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    if 'url' in video:
        video['url'] = get_video_url(video['url'])
        
    return video

@router.post("/videos/{video_id}/progress")
async def update_video_progress(video_id: str, progress_data: VideoProgressUpdate, user = Depends(get_current_user)):
    progress_doc = {
        "user_id": user['id'],
        "video_id": video_id,
        "watch_percentage": progress_data.watch_percentage,
        "completed": progress_data.completed,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_progress.update_one(
        {"user_id": user['id'], "video_id": video_id},
        {"$set": progress_doc},
        upsert=True
    )
    
    # Update mastery scores if completed
    if progress_data.completed:
        video = await db.videos.find_one({"id": video_id}, {"_id": 0})
        if video:
            await update_mastery_scores_for_video(user['id'], video, score=80.0)  # Base score
    
    return {"success": True}

@router.get("/videos/{video_id}/progress")
async def get_video_progress(video_id: str, user = Depends(get_current_user)):
    progress = await db.user_progress.find_one(
        {"user_id": user['id'], "video_id": video_id},
        {"_id": 0}
    )
    return progress if progress else {"watch_percentage": 0, "completed": False}

# ==================== Quiz Routes ====================

@router.get("/quizzes/{video_id}")
async def get_quiz(video_id: str, user = Depends(get_current_user)):
    """
    Get quiz for a video. Generates on-demand if not cached.
    - If quiz exists in DB with 4+ questions → return it (cached)
    - If transcript available but no quiz → generate with Gemini, save, return
    - If no transcript yet → return empty questions (frontend will retry)
    """
    # 1. Check if quiz already exists and is complete
    existing_quiz = await db.quizzes.find_one({"video_id": video_id}, {"_id": 0})
    if existing_quiz and existing_quiz.get("questions") and len(existing_quiz["questions"]) >= 4:
        return existing_quiz
    
    # 2. Return payload (empty if not ready yet)
    # The background worker pre-generates quizzes now, so we don't generate on-demand to avoid latency.
    return {
        "id": f"quiz-{video_id}",
        "video_id": video_id,
        "questions": []
    }

@router.post("/quizzes/submit", response_model=QuizResult)
async def submit_quiz(submission: QuizSubmission, user = Depends(get_current_user)):
    quiz = await db.quizzes.find_one({"id": submission.quiz_id}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Calculate score
    correct = 0
    for i, answer in enumerate(submission.answers):
        if i < len(quiz['questions']) and answer == quiz['questions'][i]['correct_answer']:
            correct += 1
    
    score = (correct / len(quiz['questions'])) * 100 if quiz['questions'] else 0
    
    # Save result
    result_id = str(uuid4())
    result_doc = {
        "id": result_id,
        "user_id": user['id'],
        "quiz_id": submission.quiz_id,
        "video_id": quiz['video_id'],
        "score": score,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.quiz_results.insert_one(result_doc)
    
    # Update mastery scores based on quiz performance
    video = await db.videos.find_one({"id": quiz['video_id']}, {"_id": 0})
    if video:
        # Use update_mastery_scores_for_video from services
        await update_mastery_scores_for_video(user['id'], video, score)
    
    return QuizResult(**result_doc)

import json
import os
import re
from pathlib import Path

from ..gemini_service import gemini_service
from ..transcript_service import transcript_service

@router.post("/init-data")
async def initialize_data(force: bool = False):
    """Initialize sample courses and videos with stable IDs from external JSON"""
    # Check if data exists
    if force:
        print("Forced re-initialization: clearing existing data...")
        await db.courses.delete_many({})
        await db.videos.delete_many({})
        await db.quizzes.delete_many({})
    else:
        existing = await db.courses.count_documents({})
        if existing > 0:
            return {"message": "Data already initialized. Use force=true to override."}
    
    # Load data from JSON file
    data_path = Path(__file__).parent.parent / "data" / "initial_data.json"
    if not data_path.exists():
        raise HTTPException(status_code=500, detail="Initial data file not found")
        
    try:
        with open(data_path, "r") as f:
            initial_data = json.load(f)
            courses_data = initial_data.get("courses", [])
            videos_data = initial_data.get("videos", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading initial data: {str(e)}")

    if courses_data:
        await db.courses.insert_many(courses_data)
    
    if videos_data:
        await db.videos.insert_many(videos_data)
    
    # Extract video IDs for transcript fetching
    video_ids = [v.get('id', '') for v in videos_data if v.get('id')]
    
    # Fetch real transcripts for all videos
    print(f"Fetching transcripts for {len(video_ids)} videos...")
    transcripts = await transcript_service.get_transcripts_batch(video_ids)
    transcript_count = sum(1 for t in transcripts.values() if t)
    print(f"Successfully fetched {transcript_count}/{len(video_ids)} transcripts")
    
    # Generate AI-powered quizzes using real transcripts (1 per video)
    quizzes_data = []
    
    for video in videos_data:
        vid = video.get('id', '')
        video_transcript = transcripts.get(vid, "")
        
        # Generate quiz from transcript using Gemini AI
        ai_questions = await gemini_service.generate_quiz(
            video_title=video['title'],
            video_transcript=video_transcript,
            topics=video.get('topics', []),
            difficulty=video.get('difficulty', 'Medium')
        )
        
        quizzes_data.append({
            "id": f"quiz-{vid}",
            "video_id": vid,
            "questions": ai_questions
        })
        
        # Update video's transcript field if we got a real one
        if video_transcript:
            await db.videos.update_one(
                {"id": vid},
                {"$set": {"transcript": video_transcript}}
            )
        
    if quizzes_data:
        await db.quizzes.insert_many(quizzes_data)
    
    return {"message": "Data initialized successfully", "counts": {
        "courses": len(courses_data),
        "videos": len(videos_data),
        "quizzes": len(quizzes_data),
        "transcripts_found": transcript_count
    }}

