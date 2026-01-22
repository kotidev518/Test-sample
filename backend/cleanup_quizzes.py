"""
Script to fully reset and clean the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb+srv://TL:Aditya1234@lms.avyadxo.mongodb.net/?appName=LMS"
DB_NAME = "learning_platform"

async def reset_database():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🧹 Cleaning all courses, videos, and quizzes...")
    
    # Delete all
    c = await db.courses.delete_many({})
    v = await db.videos.delete_many({})
    q = await db.quizzes.delete_many({})
    
    print(f"✅ Deleted: {c.deleted_count} courses, {v.deleted_count} videos, {q.deleted_count} quizzes")
    
    # Verify empty
    print(f"\n📊 Current counts:")
    print(f"  - Courses: {await db.courses.count_documents({})}")
    print(f"  - Videos: {await db.videos.count_documents({})}")
    print(f"  - Quizzes: {await db.quizzes.count_documents({})}")
    
    client.close()
    print("\n✅ Database is now clean! You can import fresh playlists.")

if __name__ == "__main__":
    asyncio.run(reset_database())
