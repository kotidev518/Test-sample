from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException

from ..database import db
from ..schemas import Course, Video, VideoProgressUpdate, Quiz, QuizSubmission, QuizResult
from ..dependencies import get_current_user
from ..utils import get_video_url
from ..services import update_mastery_scores_for_video

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

@router.get("/quizzes/{video_id}", response_model=Quiz)
async def get_quiz(video_id: str, user = Depends(get_current_user)):
    quiz = await db.quizzes.find_one({"video_id": video_id}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

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
from pathlib import Path

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
    
    # Generate and sample quizzes (1 per video)
    quizzes_data = []
    
    for video in videos_data:
        quizzes_data.append({
            "id": f"quiz-{video['id']}",
            "video_id": video['id'],
            "questions": [
                {
                    "question": f"What is the main topic of {video['title']}?",
                    "options": [
                        f"{video['topics'][0]}" if video['topics'] else "General",
                        "Cooking",
                        "History",
                        "Music"
                    ],
                    "correct_answer": 0
                },
                {
                    "question": "Which of the following is true regarding the content?",
                    "options": [
                        "It is unrelated to the course",
                        "It covers advanced topics only",
                        f"It discusses {video['description']}",
                        "None of the above"
                    ],
                    "correct_answer": 2
                },
                {
                    "question": "What is the difficulty level of this video?",
                    "options": [
                        "Impossible",
                        video['difficulty'],
                        "Very Easy",
                        "Expert"
                    ],
                    "correct_answer": 1
                },
                {
                    "question": "Which concept was mentioned?" ,
                    "options": [
                        "Quantum Physics",
                        "Blockchain",
                        video['topics'][0] if video['topics'] else "General",
                        "Augmented Reality"
                    ],
                    "correct_answer": 2
                }
            ]
        })
        
    if quizzes_data:
        await db.quizzes.insert_many(quizzes_data)
    
    return {"message": "Data initialized successfully", "counts": {
        "courses": len(courses_data),
        "videos": len(videos_data),
        "quizzes": len(quizzes_data)
    }}

