from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas import MasteryScore

class AnalyticsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_mastery_scores(self, user_id: str) -> List[dict]:
        return await self.db.mastery_scores.find({"user_id": user_id}, {"_id": 0}).to_list(1000)

    async def get_overall_progress(self, user_id: str) -> Dict:
        # Get all progress
        progress_list = await self.db.user_progress.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        
        total_videos = await self.db.videos.count_documents({})
        completed_videos = sum(1 for p in progress_list if p.get('completed', False))
        
        # Get quiz results
        quiz_results = await self.db.quiz_results.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        avg_quiz_score = sum(r['score'] for r in quiz_results) / len(quiz_results) if quiz_results else 0
        
        return {
            "total_videos": total_videos,
            "completed_videos": completed_videos,
            "completion_percentage": (completed_videos / total_videos * 100) if total_videos > 0 else 0,
            "average_quiz_score": avg_quiz_score,
            "total_quizzes": len(quiz_results)
        }
