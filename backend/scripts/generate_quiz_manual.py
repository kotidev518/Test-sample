import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from app.database import db
from app.services.gemini_service import gemini_service

async def generate_quiz():
    # Correct video ID from screenshot URL
    video_id = "5LVNJ_zAJoA"
    
    # Get video data
    video = await db.videos.find_one({'id': video_id}, {'_id': 0})
    if not video:
        print(f"❌ Video {video_id} not found")
        print("Searching for Vue JS 2 Tutorial videos...")
        videos = await db.videos.find(
            {'title': {'$regex': 'Vue JS 2', '$options': 'i'}},
            {'_id': 0, 'id': 1, 'title': 1}
        ).to_list(length=10)
        for v in videos:
            print(f"  - {v['id']}: {v['title']}")
        return
    
    print(f"📹 Generating quiz for: {video.get('title')}")
    print(f"📝 Transcript length: {len(video.get('transcript', ''))} chars")
    
    # Check if quiz already exists
    existing_quiz = await db.quizzes.find_one({'video_id': video_id})
    if existing_quiz and existing_quiz.get('questions'):
        print(f"ℹ️  Quiz already exists with {len(existing_quiz['questions'])} questions")
        return
    
    # Generate quiz
    print("🧠 Calling Gemini API to generate quiz...")
    questions = await gemini_service.generate_quiz(
        video_title=video["title"],
        video_transcript=video.get("transcript", ""),
        topics=video.get("topics", []),
        difficulty=video.get("difficulty", "Medium"),
        num_questions=4
    )
    
    if questions and len(questions) >= 4:
        # Save to database
        quiz_doc = {
            "id": f"quiz-{video_id}",
            "video_id": video_id,
            "questions": questions
        }
        
        await db.quizzes.update_one(
            {"video_id": video_id},
            {"$set": quiz_doc},
            upsert=True
        )
        
        print(f"✅ Quiz generated and saved ({len(questions)} questions)")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. {q['question'][:60]}...")
    else:
        print(f"❌ Quiz generation failed - only {len(questions) if questions else 0} questions")
        print(f"   Transcript preview: {video.get('transcript', '')[:200]}")

asyncio.run(generate_quiz())
