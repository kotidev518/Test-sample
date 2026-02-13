from datetime import datetime, timezone
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas import VideoProgress, VideoProgressUpdate, ChatResponse
from app.utils import get_video_url
from app.services.gemini_service import gemini_service
from app.database import db
from app.services.embedding_service import embedding_service
from app.services.transcript_service import transcript_service

class VideoService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_videos(self, course_id: Optional[str] = None) -> List[dict]:
        query = {"course_id": course_id} if course_id else {}
        videos = await self.db.videos.find(query, {"_id": 0}).sort("order", 1).to_list(1000)
        
        for video in videos:
            if 'url' in video:
                video['url'] = get_video_url(video['url'])
        return videos

    async def get_video_by_id(self, video_id: str) -> Optional[dict]:
        video = await self.db.videos.find_one({"id": video_id}, {"_id": 0})
        if video and 'url' in video:
            video['url'] = get_video_url(video['url'])
        return video

    async def update_progress(self, user_id: str, video_id: str, progress_data: VideoProgressUpdate) -> bool:
        progress_doc = VideoProgress(
            user_id=user_id,
            video_id=video_id,
            watch_percentage=progress_data.watch_percentage,
            completed=progress_data.completed,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        await self.db.user_progress.update_one(
            {"user_id": user_id, "video_id": video_id},
            {"$set": progress_doc.model_dump()},
            upsert=True
        )
        return True

    async def get_progress(self, user_id: str, video_id: str) -> dict:
        progress = await self.db.user_progress.find_one(
            {"user_id": user_id, "video_id": video_id},
            {"_id": 0}
        )
        return progress if progress else {"watch_percentage": 0, "completed": False}

    async def ask_question(self, user_id: str, user_name: str, video_id: str, message: str) -> ChatResponse:
        video = await self.get_video_by_id(video_id)
        if not video:
            return ChatResponse(answer="Video not found.")
            
        transcript = video.get("transcript", "")
        if not transcript:
            return ChatResponse(answer="Transcript is still being processed. Please try again later.")
            
        answer = await gemini_service.ask_video_chatbot(
            user_name=user_name,
            video_title=video["title"],
            video_transcript=transcript,
            user_question=message
        )
        return ChatResponse(answer=answer)
