import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.queue import enqueue_video_job, close_redis_pool

async def test_enqueue():
    # Use one of the existing video IDs from the database
    video_id = "5LYrN_cAJoA" # Vue.js tutorial video
    print(f"Testing unified worker by enqueuing video: {video_id}")
    
    await enqueue_video_job(video_id)
    print("Job enqueued! Please check the worker logs.")
    
    await close_redis_pool()

if __name__ == "__main__":
    asyncio.run(test_enqueue())
