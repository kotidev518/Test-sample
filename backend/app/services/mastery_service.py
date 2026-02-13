from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas import MasteryScore

class MasteryService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def update_mastery_scores_for_video(self, user_id: str, video: dict, score: float):
        """Update mastery scores for all topics in a video"""
        for topic in video.get('topics', []):
            # Get current mastery
            current_doc = await self.db.mastery_scores.find_one(
                {"user_id": user_id, "topic": topic},
                {"_id": 0}
            )
            
            if current_doc:
                current = MasteryScore(**current_doc)
                # Weighted average: 70% old, 30% new
                new_score = (current.score * 0.7) + (score * 0.3)
            else:
                new_score = score * 0.8  # Start at 80% of quiz score
            
            mastery_doc = MasteryScore(
                user_id=user_id,
                topic=topic,
                score=new_score,
                updated_at=datetime.now(timezone.utc).isoformat()
            )
            
            await self.db.mastery_scores.update_one(
                {"user_id": user_id, "topic": topic},
                {"$set": mastery_doc.model_dump()},
                upsert=True
            )
