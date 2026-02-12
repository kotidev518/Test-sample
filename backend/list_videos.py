import asyncio
from app.database import db

async def list_videos():
    print("📹 All Vue JS 2 Tutorial videos in database:\n")
    videos = await db.videos.find(
        {'title': {'$regex': 'Vue JS 2', '$options': 'i'}},
        {'_id': 0, 'id': 1, 'title': 1, 'transcript': 1, 'processing_status': 1}
    ).to_list(length=50)
    
    for v in videos:
        has_transcript = bool(v.get('transcript'))
        transcript_len = len(v.get('transcript', ''))
        status = v.get('processing_status', 'unknown')
        
        # Check if quiz exists
        quiz = await db.quizzes.find_one({'video_id': v['id']})
        has_quiz = bool(quiz and quiz.get('questions'))
        
        print(f"ID: {v['id']}")
        print(f"  Title: {v['title']}")
        print(f"  Status: {status}")
        print(f"  Transcript: {'✅' if has_transcript else '❌'} ({transcript_len} chars)")
        print(f"  Quiz: {'✅' if has_quiz else '❌'}")
        print()

asyncio.run(list_videos())
