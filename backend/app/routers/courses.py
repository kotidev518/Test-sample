from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import (
    get_current_user, 
    get_course_service, 
    get_video_service, 
    get_quiz_service,
    get_mastery_service
)
from ..schemas import (
    Course, Video, VideoProgressUpdate, QuizSubmission, QuizResult, 
    ChatRequest, ChatResponse
)
from ..services.course_service import CourseService
from ..services.video_service import VideoService
from ..services.quiz_service import QuizService
from ..services.mastery_service import MasteryService

router = APIRouter(tags=["courses"])

# ==================== Course Routes ====================

@router.get("/courses", response_model=List[Course])
async def get_courses(
    user = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
):
    return await course_service.get_all_courses()

@router.get("/courses/{course_id}", response_model=Course)
async def get_course(
    course_id: str, 
    user = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
):
    course = await course_service.get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

# ==================== Video Routes ====================

@router.get("/videos", response_model=List[Video])
async def get_videos(
    course_id: Optional[str] = None, 
    user = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service)
):
    return await video_service.get_videos(course_id)

@router.get("/videos/{video_id}", response_model=Video)
async def get_video(
    video_id: str, 
    user = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service)
):
    video = await video_service.get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.post("/videos/{video_id}/progress")
async def update_video_progress(
    video_id: str, 
    progress_data: VideoProgressUpdate, 
    user = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
    mastery_service: MasteryService = Depends(get_mastery_service)
):
    await video_service.update_progress(user['id'], video_id, progress_data)
    
    if progress_data.completed:
        video = await video_service.get_video_by_id(video_id)
        if video:
            await mastery_service.update_mastery_scores_for_video(user['id'], video, score=80.0)
    
    return {"success": True}

@router.get("/videos/{video_id}/progress")
async def get_video_progress(
    video_id: str, 
    user = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service)
):
    return await video_service.get_progress(user['id'], video_id)

@router.post("/videos/{video_id}/chat", response_model=ChatResponse)
async def ask_video_question(
    video_id: str, 
    chat_request: ChatRequest, 
    user = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service)
):
    return await video_service.ask_question(
        user['id'], user.get('name', 'User'), video_id, chat_request.message
    )

# ==================== Quiz Routes ====================

@router.get("/quizzes/{video_id}")
async def get_quiz(
    video_id: str, 
    user = Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    return await quiz_service.get_quiz_by_video_id(video_id)

@router.post("/quizzes/submit", response_model=QuizResult)
async def submit_quiz(
    submission: QuizSubmission, 
    user = Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
    video_service: VideoService = Depends(get_video_service),
    mastery_service: MasteryService = Depends(get_mastery_service)
):
    result = await quiz_service.submit_quiz(user['id'], submission)
    if not result:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    video = await video_service.get_video_by_id(result.video_id)
    if video:
        await mastery_service.update_mastery_scores_for_video(user['id'], video, result.score)
    
    return result

