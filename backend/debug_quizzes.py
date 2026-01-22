"""
Check specific YouTube video quiz
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb+srv://TL:Aditya1234@lms.avyadxo.mongodb.net/?appName=LMS"
DB_NAME = "learning_platform"

async def check_youtube_quiz():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Check for the specific video ID from the screenshot
    target_id = "YZkyL-f-YXY"
    
    print(f"🔍 Checking for video: {target_id}")
    video = await db.videos.find_one({"id": target_id})
    
    if video:
        print(f"✅ Video found: {video.get('title')}")
        
        # Check for quiz
        quiz = await db.quizzes.find_one({"video_id": target_id})
        if quiz:
            print(f"✅ Quiz FOUND for video {target_id}!")
            print(f"   Quiz ID: {quiz.get('id')}")
            print(f"   Questions: {len(quiz.get('questions', []))}")
            print(f"   Question 1: {quiz['questions'][0].get('question')}")
        else:
            print(f"❌ Quiz NOT found for video {target_id}")
    else:
        print(f"❌ Video {target_id} NOT found in database")
        print("Listing valid video IDs:")
        async for v in db.videos.find({}, {"id": 1, "title": 1}).limit(10):
            print(f"  - {v['id']} ({v['title'][:20]}...)")
            
    client.close()

if __name__ == "__main__":
    asyncio.run(check_youtube_quiz())
