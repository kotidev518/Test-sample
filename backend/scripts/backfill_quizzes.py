import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from datetime import datetime, timezone
from pymongo import UpdateOne
from app.database import db
from app.queue import enqueue_quiz_job, close_redis_pool

async def check_missing_quizzes():
    print("🔍 Checking for videos with transcripts but MISSING quizzes...")
    
    # Get all videos with transcripts
    videos = await db.videos.find(
        {"transcript": {"$exists": True, "$ne": ""}},
        {"id": 1, "title": 1, "processing_status": 1}
    ).to_list(1000)
    
    missing_count = 0
    ids_to_requeue = []
    
    print(f"Found {len(videos)} videos with transcripts.")
    
    for v in videos:
        # Check if quiz exists
        quiz = await db.quizzes.find_one({"video_id": v["id"]})
        
        # If no quiz, or questions list is empty/small, it needs generation
        if not quiz or not quiz.get("questions") or len(quiz["questions"]) < 4:
            print(f"❌ Missing quiz: {v['id']} - {v['title']}")
            missing_count += 1
            ids_to_requeue.append(v["id"])
            
    print(f"\nSummary: {missing_count} videos are missing quizzes.")
    
    if missing_count > 0:
        print(f"\n⚡ Re-queuing {missing_count} videos for ARQ processing...")
        
        # 1. Update video status in MongoDB
        if ids_to_requeue:
            await db.videos.update_many(
                {"id": {"$in": ids_to_requeue}},
                {"$set": {"processing_status": "processing"}} # Set to processing so UI knows it's happening
            )
            
            # 2. Update/Sync processing_queue logic (optional but good for consistency)
            ops = []
            for vid in ids_to_requeue:
                ops.append(UpdateOne(
                    {"video_id": vid},
                    {
                        "$set": {
                            "status": "processing",
                            "attempts": 0,
                            "priority": 1,
                            "updated_at": datetime.now(timezone.utc)
                        },
                        "$setOnInsert": {
                            "created_at": datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                ))
            
            if ops:
                await db.processing_queue.bulk_write(ops)

            # 3. CRITICAL: Enqueue in ARQ (Redis) so the worker actually starts working
            for vid in ids_to_requeue:
                await enqueue_quiz_job(vid)

            print(f"\n✅ Successfully enqueued {len(ids_to_requeue)} videos. The ARQ worker will process them shortly.")
    else:
        print("✅ All videos already have quizzes!")

async def main():
    try:
        await check_missing_quizzes()
    finally:
        # Gracefully close Redis connection pool
        await close_redis_pool()

if __name__ == "__main__":
    asyncio.run(main())
