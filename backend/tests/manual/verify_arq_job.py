import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
from app.queue import enqueue_quiz_job

async def test_job():
    # Pick a video ID from the previous list (e.g., Intro to Vue JS)
    video_id = "ieCsEdq94TA" # Vue JS 2 Tutorial #2
    print(f"Triggering ARQ job for video: {video_id}")
    await enqueue_quiz_job(video_id)
    print("Job enqueued. Check worker logs!")

if __name__ == "__main__":
    asyncio.run(test_job())
