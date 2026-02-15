
import sys
import os
import asyncio

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import db

async def fix_thumbnails(dry_run=False):
    print(f"🔍 Starting thumbnail fix script (dry_run={dry_run})...")
    
    # Find courses that have 'landscape' in their thumbnail URL or are missing a thumbnail
    query = {
        "$or": [
            {"thumbnail": {"$regex": "landscape", "$options": "i"}},
            {"thumbnail": {"$eq": ""}},
            {"thumbnail": {"$exists": False}}
        ]
    }
    
    courses = await db.courses.find(query).to_list(length=1000)
    print(f"Found {len(courses)} courses to process.")
    
    updated_count = 0
    for course in courses:
        course_id = course.get('id')
        current_thumbnail = course.get('thumbnail', 'MISSING')
        print(f"\nProcessing course: {course.get('title')} ({course_id})")
        print(f"Current thumbnail: {current_thumbnail}")
        
        # Find the first video for this course
        first_video = await db.videos.find_one(
            {"course_id": course_id},
            sort=[("order", 1)]
        )
        
        if first_video and first_video.get('thumbnail'):
            new_thumbnail = first_video['thumbnail']
            print(f"Found video thumbnail: {new_thumbnail}")
            
            if not dry_run:
                result = await db.courses.update_one(
                    {"id": course_id},
                    {"$set": {"thumbnail": new_thumbnail}}
                )
                if result.modified_count > 0:
                    print("✅ Successfully updated.")
                    updated_count += 1
                else:
                    print("⚠️ Already updated or no change needed.")
            else:
                print("⏭️ Dry run: skipping update.")
        else:
            print("❌ No video thumbnail found for this course.")
            
    print(f"\n🏁 Finished. Updated {updated_count} courses.")

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(fix_thumbnails(dry_run))
