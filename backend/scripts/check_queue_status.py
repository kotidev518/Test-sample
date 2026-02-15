import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import db

async def check_queue():
    print("--- Processing Queue Status ---")
    
    # 1. Overall stats
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    cursor = db.processing_queue.aggregate(pipeline)
    async for doc in cursor:
        print(f"Status {doc['_id']}: {doc['count']}")
    
    # 2. Detailed failures
    print("\n--- Recent Failures ---")
    failures = db.processing_queue.find({"status": "failed"}).limit(5)
    async for job in failures:
        print(f"Video {job['video_id']}:")
        msg = job.get('error_message', 'No error message')
        print(f"  Error: {msg}")
        print(f"  Attempts: {job.get('retry_count', job.get('attempts', 0))}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_queue())
