from datetime import datetime, timezone
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas import QuizSubmission, QuizResult

class QuizService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_quiz_by_video_id(self, video_id: str) -> dict:
        existing_quiz = await self.db.quizzes.find_one({"video_id": video_id}, {"_id": 0})
        if existing_quiz and existing_quiz.get("questions") and len(existing_quiz["questions"]) >= 4:
            return existing_quiz
        
        return {
            "id": f"quiz-{video_id}",
            "video_id": video_id,
            "questions": []
        }

    async def submit_quiz(self, user_id: str, submission: QuizSubmission) -> QuizResult:
        quiz = await self.db.quizzes.find_one({"id": submission.quiz_id}, {"_id": 0})
        if not quiz:
            return None
        
        correct = 0
        for i, answer in enumerate(submission.answers):
            if i < len(quiz['questions']) and answer == quiz['questions'][i]['correct_answer']:
                correct += 1
        
        score = (correct / len(quiz['questions'])) * 100 if quiz['questions'] else 0
        
        result_id = str(uuid4())
        result_doc = QuizResult(
            id=result_id,
            user_id=user_id,
            quiz_id=submission.quiz_id,
            video_id=quiz['video_id'],
            score=score,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        await self.db.quiz_results.insert_one(result_doc.model_dump())
        return result_doc
