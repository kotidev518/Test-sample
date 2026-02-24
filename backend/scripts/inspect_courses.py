import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import db

async def inspect():
    # Find course by title
    course = await db.courses.find_one({"title": {"$regex": "Vue", "$options": "i"}})
    if not course:
        print("❌ No course with 'Vue' in title found.")
        # List all for debug
        all_courses = await db.courses.find({}, {"title": 1}).to_list(100)
        print("Available courses:")
        for ac in all_courses:
            print(f"  - {ac['title']}")
        return
        
    cid = course['id']
    print(f"Course: {course['title']} ({cid})")
    
    videos = await db.videos.find({"course_id": cid}).to_list(1000)
    print(f"Total Videos: {len(videos)}")
    
    video_ids = [v["id"] for v in videos]
    quizzes = await db.quizzes.find({"video_id": {"$in": video_ids}}).to_list(1000)
    quiz_vids = {q["video_id"] for q in quizzes}
    print(f"Videos with Quizzes: {len(quizzes)}")
    
    missing = []
    for v in videos:
        if v["id"] not in quiz_vids:
            missing.append(v)
            
    print(f"Videos missing Quizzes: {len(missing)}")
    for v in missing:
        print(f"  - {v['id']}: {v['title']} (Transcript: {'Yes' if v.get('transcript') else 'No'})")

if __name__ == "__main__":
    asyncio.run(inspect())
