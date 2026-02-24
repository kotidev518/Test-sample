import asyncio
from arq.connections import RedisSettings
from .database import db, init_firebase, ensure_indexes
from .services.gemini_service import gemini_service
from .services.processing_queue_service import processing_worker
from .config import settings
from datetime import datetime, timezone

async def process_video_task(ctx, video_id: str):
    """
    ARQ Background Task to fetch transcript and generate embeddings.
    Routes through the semaphore on processing_worker so only one
    transcript is fetched at a time, avoiding YouTube rate-limits.
    Then enqueues the quiz generation task.
    """
    print(f"📹 Processing video for embeddings: {video_id}")
    try:
        # Check if there is an existing job in processing_queue to keep status in sync
        job = await db.processing_queue.find_one({"video_id": video_id})
        if not job:
            # Create a dummy job dict if not found
            job = {"video_id": video_id, "_id": None}
        
        # Use semaphore-gated method to ensure only 1 transcript is fetched at a time
        await processing_worker._process_with_semaphore(job)
        print(f"✅ Video processing (embeddings) finished for {video_id}")
    except Exception as e:
        print(f"❌ Error in process_video_task for {video_id}: {e}")
        raise e

async def generate_quiz_task(ctx, video_id: str):
    """
    ARQ Background Task to generate a quiz for a video.
    """
    print(f"📦 Processing quiz for video: {video_id}")
    
    try:
        # 1. Fetch video from database
        video = await db.videos.find_one({"id": video_id})
        if not video:
            print(f"❌ Video {video_id} not found in database")
            return
            
        transcript = video.get("transcript", "")
        if not transcript:
            print(f"⚠️ Video {video_id} has no transcript. Cannot generate quiz.")
            return

        # 2. Generate quiz via Gemini AI
        print(f"  🧠 Calling Gemini AI for quiz generation...")
        questions = await gemini_service.generate_quiz(
            video_title=video["title"],
            video_transcript=transcript,
            topics=video.get("topics", []),
            difficulty=video.get("difficulty", "Medium"),
            num_questions=4
        )

        if not questions or len(questions) < 4:
            raise Exception(f"AI failed to generate enough valid questions for {video_id}")

        # 3. Save to quizzes collection
        quiz_doc = {
            "id": f"quiz-{video_id}",
            "video_id": video_id,
            "questions": questions,
            "generated_at": datetime.now(timezone.utc)
        }
        
        await db.quizzes.update_one(
            {"video_id": video_id},
            {"$set": quiz_doc},
            upsert=True
        )
        
        print(f"✅ Quiz generated and saved for {video_id} ({len(questions)} questions)")

    except Exception as e:
        print(f"❌ Error generating quiz for {video_id}: {e}")
        raise e

async def startup(ctx):
    """Worker startup logic"""
    init_firebase()
    await ensure_indexes()
    print("🚀 ARQ Worker started. Ready for jobs (Embeddings + Quizzes).")

async def shutdown(ctx):
    """Worker shutdown logic"""
    print("⏹️ ARQ Worker shutting down.")

class WorkerSettings:
    """ARQ Worker configuration"""
    functions = [process_video_task, generate_quiz_task]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
    concurrency = 3
    max_retries = 3
    retry_delay_seconds = 10
