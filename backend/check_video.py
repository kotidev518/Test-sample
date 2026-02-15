import asyncio
from app.database import db

async def check_video():
    # Find the Vue JS 2 Tutorial video
    video = await db.videos.find_one(
        {'title': {'$regex': 'Vue JS 2 Tutorial.*Introduction', '$options': 'i'}},
        {'_id': 0, 'id': 1, 'title': 1, 'transcript': 1, 'processing_status': 1}
    )
    
    if not video:
        print(" Video not found")
        return
    
    video_id = video.get('id')
    print(f" Video ID: {video_id}")
    print(f" Title: {video.get('title')}")
    print(f" Processing Status: {video.get('processing_status')}")
    
    transcript = video.get('transcript', '')
    print(f" Has transcript: {bool(transcript)}")
    print(f" Transcript length: {len(transcript)} chars")
    
    # Check if quiz exists
    quiz = await db.quizzes.find_one(
        {'video_id': video_id},
        {'_id': 0, 'id': 1, 'questions': 1}
    )
    
    if quiz:
        num_questions = len(quiz.get('questions', []))
        print(f" Quiz exists: {num_questions} questions")
    else:
        print(f" No quiz found for this video")

asyncio.run(check_video())
