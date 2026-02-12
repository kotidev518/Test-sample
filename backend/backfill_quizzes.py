import asyncio
from datetime import datetime, timezone
from pymongo import UpdateOne
from app.database import db

async def check_missing_quizzes():
    print("🔍 Checking for videos with transcripts but MISSING quizzes...")
    
    # Get all videos with transcripts
    videos = await db.videos.find(
        {"transcript": {"$exists": True, "$ne": ""}},
        {"id": 1, "title": 1, "processing_status": 1}
    ).to_list(1000)
    
    missing_count = 0
    ids_to_requeue = []
    
    print(f"found {len(videos)} videos with transcripts.")
    
    for v in videos:
        # Check if quiz exists
        quiz = await db.quizzes.find_one({"video_id": v["id"]})
        
        if not quiz or not quiz.get("questions") or len(quiz["questions"]) < 4:
            print(f"❌ Missing quiz: {v['id']} - {v['title']}")
            missing_count += 1
            ids_to_requeue.append(v["id"])
        else:
            # print(f"✅ Has quiz: {v['id']}")
            pass
            
    print(f"\nSummary: {missing_count} videos are missing quizzes.")
    
    if missing_count > 0:
        print(f"\n⚡ Auto-requeuing {missing_count} videos for processing...")
        
        # Reset video status
        if ids_to_requeue:
            await db.videos.update_many(
                {"id": {"$in": ids_to_requeue}},
                {"$set": {"processing_status": "pending"}}
            )
            
            # Upsert into processing queue
            ops = []
            from pymongo import UpdateOne
            for vid in ids_to_requeue:
                ops.append(UpdateOne(
                    {"video_id": vid},
                    {
                        "$set": {
                            "status": "pending",
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
                from datetime import datetime
                # Need to import datetime/timezone
                # Or just rely on what's available
                # Let's fix imports
                pass 
                await db.processing_queue.bulk_write(ops)

            print(f"✅ Requeued {len(ids_to_requeue)} videos. The background worker will generate quizzes for them.")
    else:
        print("✅ All videos already have quizzes!")

if __name__ == "__main__":
    asyncio.run(check_missing_quizzes())
