from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas import CourseDB

class CourseService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_all_courses(self) -> List[dict]:
        return await self.db.courses.find({}, {"_id": 0}).to_list(1000)

    async def get_course_by_id(self, course_id: str) -> Optional[dict]:
        return await self.db.courses.find_one({"id": course_id}, {"_id": 0})

    async def delete_course(self, course_id: str) -> bool:
        # Check if course exists
        course = await self.db.courses.find_one({"id": course_id})
        if not course:
            return False
        
        # Get all video IDs for this course first
        videos = await self.db.videos.find({"course_id": course_id}, {"id": 1}).to_list(1000)
        video_ids = [v["id"] for v in videos]
        
        # Delete quizzes by video_id (quiz IDs are "quiz-{video_id}")
        if video_ids:
            quiz_ids = [f"quiz-{vid}" for vid in video_ids]
            await self.db.quizzes.delete_many({"id": {"$in": quiz_ids}})
        
        # Delete videos and course
        await self.db.videos.delete_many({"course_id": course_id})
        await self.db.courses.delete_one({"id": course_id})
        return True
