import asyncio
from app.database import db

async def trigger_processing():
    video_id = "ieCsEdq94TA"
    
    print(f" Resetting status for {video_id}...")
    
    # 1. Reset video status
    await db.videos.update_one(
        {"id": video_id},
        {"$set": {"processing_status": "pending"}}
    )
    
    # 2. Add to processing queue
    # We can just let the worker pick it up if we use the admin endpoint
    # Or insert directly into queue collection
    
    # Check if already in queue
    in_queue = await db.processing_queue.find_one({"video_id": video_id})
    if not in_queue:
        print(" Adding to processing queue...")
        await db.processing_queue.insert_one({
            "video_id": video_id,
            "status": "pending",
            "attempts": 0,
            "created_at": "2024-01-01T00:00:00Z", # Dummy date
            "priority": 1
        })
    else:
        print("↻ Resetting queue item...")
        await db.processing_queue.update_one(
            {"video_id": video_id},
            {"$set": {"status": "pending", "attempts": 0}}
        )
        
    print(f" Triggered processing for {video_id}. Watch server logs!")

asyncio.run(trigger_processing())
