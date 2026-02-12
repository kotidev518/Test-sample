import asyncio
from app.database import db

async def check_results():
    # Video ID used in test_arq_job.py
    video_id = "ieCsEdq94TA"
    print(f"🔍 Checking results for video: {video_id}")
    
    quiz = await db.quizzes.find_one({"video_id": video_id})
    if quiz:
        print("✅ Success! Quiz found in database.")
        print(f"📊 Questions: {len(quiz.get('questions', []))}")
        print(f"🕒 Generated at: {quiz.get('generated_at')}")
        
        # Also check video status
        video = await db.videos.find_one({"id": video_id})
        print(f"📹 Video processing_status: {video.get('processing_status')}")
    else:
        print("❌ Test failed: No quiz found. Re-checking in 5 seconds...")
        await asyncio.sleep(5)
        quiz = await db.quizzes.find_one({"video_id": video_id})
        if quiz:
            print("✅ Success! Quiz found after retry.")
        else:
            print("❌ Still no quiz found.")

if __name__ == "__main__":
    asyncio.run(check_results())
