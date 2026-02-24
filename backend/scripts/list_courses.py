import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import db

async def list_courses():
    courses = await db.courses.find({}, {"id": 1, "title": 1}).to_list(100)
    for c in courses:
        print(f"ID: '{c['id']}' | Title: '{c['title']}'")

if __name__ == "__main__":
    asyncio.run(list_courses())
