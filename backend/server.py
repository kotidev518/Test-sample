from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict
import firebase_admin
from firebase_admin import credentials, storage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 72

# Initialize SBERT model
print("Loading SBERT model...")
sbert_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print("SBERT model loaded successfully")

# Initialize Firebase Admin
try:
    cred_path = os.environ.get('FIREBASE_CREDENTIALS', 'serviceAccountKey.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET')
        })
        print("Firebase Admin initialized successfully")
    else:
        print(f"Warning: Firebase credentials not found at {cred_path}")
except Exception as e:
    print(f"Error initializing Firebase Admin: {e}")

def get_video_url(url_or_path: str) -> str:
    """
    Transforms a stored video path into a usable URL.
    - If it's already a full URL (http/https), returns it as is.
    - If it's a gs:// URI, extracts the path.
    - If it's a storage path, generates a signed URL.
    """
    if not url_or_path:
        return ""
    
    if url_or_path.startswith(('http://', 'https://')):
        return url_or_path
    
    # Handle gs:// format
    blob_path = url_or_path
    if url_or_path.startswith('gs://'):
        # Format: gs://bucket-name/path/to/file
        try:
            parts = url_or_path.replace('gs://', '').split('/', 1)
            if len(parts) == 2:
                # We ignore the bucket part if we are using the default bucket, 
                # or we could verify it matches. For now, let's just use the path.
                blob_path = parts[1]
            else:
                # Malformed gs:// uri or root of bucket
                return url_or_path
        except Exception:
            pass
            
    # Assume it's a path in Firebase Storage
    try:
        bucket = storage.bucket()
        blob = bucket.blob(blob_path)
        return blob.generate_signed_url(expiration=timedelta(hours=1))
    except Exception as e:
        print(f"Error generating signed URL for {url_or_path}: {e}")
        return url_or_path

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# ==================== Models ====================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    initial_level: Optional[str] = "Medium"  # Easy, Medium, Hard

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    initial_level: str
    created_at: str

class TokenResponse(BaseModel):
    token: str
    user: UserProfile

class Course(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    description: str
    difficulty: str
    topics: List[str]
    thumbnail: str
    video_count: int

class Video(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    course_id: str
    title: str
    description: str
    url: str
    duration: int  # seconds
    difficulty: str
    topics: List[str]
    transcript: str
    order: int

class VideoProgress(BaseModel):
    user_id: str
    video_id: str
    watch_percentage: float
    completed: bool
    timestamp: str

class VideoProgressUpdate(BaseModel):
    watch_percentage: float
    completed: bool

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int  # index of correct option

class Quiz(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    video_id: str
    questions: List[QuizQuestion]

class QuizSubmission(BaseModel):
    quiz_id: str
    answers: List[int]  # user's answers (indices)

class QuizResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    quiz_id: str
    video_id: str
    score: float  # percentage
    timestamp: str

class MasteryScore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    topic: str
    score: float  # 0-100
    updated_at: str

class NextVideoRecommendation(BaseModel):
    video: Video
    reason: str
    mastery_scores: dict

# ==================== Auth Helpers ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== Auth Routes ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    from uuid import uuid4
    user_id = str(uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "initial_level": user_data.initial_level,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create token
    token = create_token(user_id)
    
    # Return response
    user_profile = UserProfile(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        initial_level=user_data.initial_level,
        created_at=user_doc["created_at"]
    )
    
    return TokenResponse(token=token, user=user_profile)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user['id'])
    
    user_profile = UserProfile(
        id=user['id'],
        email=user['email'],
        name=user['name'],
        initial_level=user.get('initial_level', 'Medium'),
        created_at=user['created_at']
    )
    
    return TokenResponse(token=token, user=user_profile)

@api_router.get("/auth/me", response_model=UserProfile)
async def get_me(user = Depends(get_current_user)):
    return UserProfile(
        id=user['id'],
        email=user['email'],
        name=user['name'],
        initial_level=user.get('initial_level', 'Medium'),
        created_at=user['created_at']
    )

# ==================== Course Routes ====================

@api_router.get("/courses", response_model=List[Course])
async def get_courses(user = Depends(get_current_user)):
    courses = await db.courses.find({}, {"_id": 0}).to_list(1000)
    return courses

@api_router.get("/courses/{course_id}", response_model=Course)
async def get_course(course_id: str, user = Depends(get_current_user)):
    course = await db.courses.find_one({"id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

# ==================== Video Routes ====================

@api_router.get("/videos", response_model=List[Video])
async def get_videos(course_id: Optional[str] = None, user = Depends(get_current_user)):
    query = {"course_id": course_id} if course_id else {}
    videos = await db.videos.find(query, {"_id": 0}).sort("order", 1).to_list(1000)
    
    # Process URLs
    for video in videos:
        if 'url' in video:
            video['url'] = get_video_url(video['url'])
            
    return videos

@api_router.get("/videos/{video_id}", response_model=Video)
async def get_video(video_id: str, user = Depends(get_current_user)):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    if 'url' in video:
        video['url'] = get_video_url(video['url'])
        
    return video

@api_router.post("/videos/{video_id}/progress")
async def update_video_progress(video_id: str, progress_data: VideoProgressUpdate, user = Depends(get_current_user)):
    progress_doc = {
        "user_id": user['id'],
        "video_id": video_id,
        "watch_percentage": progress_data.watch_percentage,
        "completed": progress_data.completed,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_progress.update_one(
        {"user_id": user['id'], "video_id": video_id},
        {"$set": progress_doc},
        upsert=True
    )
    
    # Update mastery scores if completed
    if progress_data.completed:
        video = await db.videos.find_one({"id": video_id}, {"_id": 0})
        if video:
            await update_mastery_scores_for_video(user['id'], video, score=80.0)  # Base score
    
    return {"success": True}

@api_router.get("/videos/{video_id}/progress")
async def get_video_progress(video_id: str, user = Depends(get_current_user)):
    progress = await db.user_progress.find_one(
        {"user_id": user['id'], "video_id": video_id},
        {"_id": 0}
    )
    return progress if progress else {"watch_percentage": 0, "completed": False}

# ==================== Quiz Routes ====================

@api_router.get("/quizzes/{video_id}", response_model=Quiz)
async def get_quiz(video_id: str, user = Depends(get_current_user)):
    quiz = await db.quizzes.find_one({"video_id": video_id}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz

@api_router.post("/quizzes/submit", response_model=QuizResult)
async def submit_quiz(submission: QuizSubmission, user = Depends(get_current_user)):
    quiz = await db.quizzes.find_one({"id": submission.quiz_id}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Calculate score
    correct = 0
    for i, answer in enumerate(submission.answers):
        if i < len(quiz['questions']) and answer == quiz['questions'][i]['correct_answer']:
            correct += 1
    
    score = (correct / len(quiz['questions'])) * 100 if quiz['questions'] else 0
    
    # Save result
    from uuid import uuid4
    result_id = str(uuid4())
    result_doc = {
        "id": result_id,
        "user_id": user['id'],
        "quiz_id": submission.quiz_id,
        "video_id": quiz['video_id'],
        "score": score,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.quiz_results.insert_one(result_doc)
    
    # Update mastery scores based on quiz performance
    video = await db.videos.find_one({"id": quiz['video_id']}, {"_id": 0})
    if video:
        await update_mastery_scores_for_video(user['id'], video, score)
    
    return QuizResult(**result_doc)

# ==================== Mastery & Analytics Routes ====================

async def update_mastery_scores_for_video(user_id: str, video: dict, score: float):
    """Update mastery scores for all topics in a video"""
    for topic in video.get('topics', []):
        # Get current mastery
        current = await db.mastery_scores.find_one(
            {"user_id": user_id, "topic": topic},
            {"_id": 0}
        )
        
        if current:
            # Weighted average: 70% old, 30% new
            new_score = (current['score'] * 0.7) + (score * 0.3)
        else:
            new_score = score * 0.8  # Start at 80% of quiz score
        
        await db.mastery_scores.update_one(
            {"user_id": user_id, "topic": topic},
            {"$set": {
                "user_id": user_id,
                "topic": topic,
                "score": new_score,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )

@api_router.get("/analytics/mastery", response_model=List[MasteryScore])
async def get_mastery_scores(user = Depends(get_current_user)):
    scores = await db.mastery_scores.find({"user_id": user['id']}, {"_id": 0}).to_list(1000)
    return scores

@api_router.get("/analytics/progress")
async def get_overall_progress(user = Depends(get_current_user)):
    # Get all progress
    progress_list = await db.user_progress.find({"user_id": user['id']}, {"_id": 0}).to_list(1000)
    
    total_videos = await db.videos.count_documents({})
    completed_videos = sum(1 for p in progress_list if p.get('completed', False))
    
    # Get quiz results
    quiz_results = await db.quiz_results.find({"user_id": user['id']}, {"_id": 0}).to_list(1000)
    avg_quiz_score = sum(r['score'] for r in quiz_results) / len(quiz_results) if quiz_results else 0
    
    return {
        "total_videos": total_videos,
        "completed_videos": completed_videos,
        "completion_percentage": (completed_videos / total_videos * 100) if total_videos > 0 else 0,
        "average_quiz_score": avg_quiz_score,
        "total_quizzes": len(quiz_results)
    }

# ==================== Recommendation Engine ====================

@api_router.get("/recommendations/next-video", response_model=NextVideoRecommendation)
async def get_next_video_recommendation(user = Depends(get_current_user)):
    """AI-based recommendation using SBERT embeddings and mastery scores"""
    
    # Get user's mastery scores
    mastery_list = await db.mastery_scores.find({"user_id": user['id']}, {"_id": 0}).to_list(1000)
    mastery_dict = {m['topic']: m['score'] for m in mastery_list}
    
    # Get user's progress
    progress_list = await db.user_progress.find({"user_id": user['id']}, {"_id": 0}).to_list(1000)
    watched_videos = {p['video_id']: p for p in progress_list}
    
    # Get all videos
    all_videos = await db.videos.find({}, {"_id": 0}).sort("order", 1).to_list(1000)
    
    if not all_videos:
        raise HTTPException(status_code=404, detail="No videos available")
    
    # Get user's last watched video for semantic similarity
    last_watched_video = None
    if progress_list:
        sorted_progress = sorted(progress_list, key=lambda x: x.get('timestamp', ''), reverse=True)
        if sorted_progress:
            last_watched_video = await db.videos.find_one({"id": sorted_progress[0]['video_id']}, {"_id": 0})
    
    # Calculate scores for each unwatched video
    candidate_videos = []
    
    for video in all_videos:
        video_id = video['id']
        
        # Skip completed videos
        if video_id in watched_videos and watched_videos[video_id].get('completed', False):
            continue
        
        # Prioritize partially watched videos
        if video_id in watched_videos and not watched_videos[video_id].get('completed', False):
            candidate_videos.append({
                'video': video,
                'score': 1000,  # Highest priority
                'reason': f"Continue watching '{video['title']}' ({watched_videos[video_id]['watch_percentage']:.0f}% completed)"
            })
            continue
        
        # Calculate recommendation score
        score = 0
        reasons = []
        
        # 1. Mastery-based scoring (40% weight)
        video_topics = video.get('topics', [])
        if video_topics and mastery_dict:
            topic_scores = [mastery_dict.get(topic, 0) for topic in video_topics]
            avg_mastery = sum(topic_scores) / len(topic_scores) if topic_scores else 0
            
            # Prefer topics with 40-70% mastery (optimal learning zone)
            if 40 <= avg_mastery <= 70:
                score += 40
                reasons.append(f"Optimal challenge level for {video_topics[0]}")
            elif avg_mastery < 40:
                score += 30
                reasons.append(f"Build foundation in {video_topics[0]}")
            else:
                score += 20
        else:
            # No mastery data yet - prioritize easier content
            if video['difficulty'] == user.get('initial_level', 'Medium'):
                score += 35
                reasons.append(f"Matches your {user.get('initial_level', 'Medium')} level")
        
        # 2. Difficulty progression (20% weight)
        difficulty_map = {'Easy': 1, 'Medium': 2, 'Hard': 3}
        user_level = difficulty_map.get(user.get('initial_level', 'Medium'), 2)
        video_level = difficulty_map.get(video['difficulty'], 2)
        
        if video_level == user_level:
            score += 20
        elif video_level == user_level + 1:
            score += 15  # Slightly harder is good
            reasons.append("Next difficulty level")
        elif video_level == user_level - 1:
            score += 10
        
        # 3. Semantic similarity (30% weight)
        if last_watched_video:
            try:
                # Get embeddings
                if 'embedding' not in video:
                    # Generate embedding on-the-fly
                    video_embedding = sbert_model.encode(video.get('transcript', video['description']))
                else:
                    video_embedding = np.array(video['embedding'])
                
                if 'embedding' not in last_watched_video:
                    last_embedding = sbert_model.encode(last_watched_video.get('transcript', last_watched_video['description']))
                else:
                    last_embedding = np.array(last_watched_video['embedding'])
                
                # Cosine similarity
                similarity = np.dot(video_embedding, last_embedding) / (
                    np.linalg.norm(video_embedding) * np.linalg.norm(last_embedding)
                )
                similarity_score = float(similarity) * 30
                score += similarity_score
                
                if similarity > 0.7:
                    reasons.append(f"Related to '{last_watched_video['title']}'")
            except:
                pass
        
        # 4. Sequential ordering (10% weight)
        if video.get('order', 0) < 10:  # Early videos in sequence
            score += 10 - video.get('order', 0)
        
        # 5. Course consistency (High priority)
        if last_watched_video and video['course_id'] == last_watched_video['course_id']:
            score += 100
            reasons.append(f"Continue in '{last_watched_video.get('course_id', 'this course')}'")
        
        candidate_videos.append({
            'video': video,
            'score': score,
            'reason': reasons[0] if reasons else f"Learn {video['title']}"
        })
    
    if not candidate_videos:
        # All videos completed - recommend from start
        recommended = all_videos[0]
        reason = "Congratulations! Review from the beginning"
    else:
        # Sort by score and return top recommendation
        candidate_videos.sort(key=lambda x: x['score'], reverse=True)
        best = candidate_videos[0]
        recommended = best['video']
        reason = best['reason']
    
    recommended_video = Video(**recommended)
    if hasattr(recommended_video, 'url'):
        recommended_video.url = get_video_url(recommended_video.url)

    return NextVideoRecommendation(
        video=recommended_video,
        reason=reason,
        mastery_scores=mastery_dict
    )

# ==================== Initialize Sample Data ====================

async def clean_database():
    """Remove duplicates from courses, videos, and quizzes based on both ID and content"""
    # 1. Clean courses by ID
    pipeline = [
        {"$group": {"_id": "$id", "unique_ids": {"$push": "$_id"}}},
        {"$match": {"unique_ids": {"$size": {"$gt": 1}}}}
    ]
    duplicates = await db.courses.aggregate(pipeline).to_list(None)
    for doc in duplicates:
        await db.courses.delete_many({"_id": {"$in": doc["unique_ids"][1:]}})
    
    # 2. Clean videos by ID and content (title + course_id)
    # First by ID
    pipeline = [
        {"$group": {"_id": "$id", "unique_ids": {"$push": "$_id"}}},
        {"$match": {"unique_ids": {"$size": {"$gt": 1}}}}
    ]
    duplicates = await db.videos.aggregate(pipeline).to_list(None)
    for doc in duplicates:
        await db.videos.delete_many({"_id": {"$in": doc["unique_ids"][1:]}})
    
    # Then by title + course_id (handles same video with different UUIDs)
    pipeline = [
        {"$group": {"_id": {"t": "$title", "c": "$course_id"}, "unique_ids": {"$push": "$_id"}}},
        {"$match": {"unique_ids": {"$size": {"$gt": 1}}}}
    ]
    duplicates = await db.videos.aggregate(pipeline).to_list(None)
    for doc in duplicates:
        await db.videos.delete_many({"_id": {"$in": doc["unique_ids"][1:]}})

    # 3. Clean quizzes by ID and content (video_id)
    pipeline = [
        {"$group": {"_id": "$id", "unique_ids": {"$push": "$_id"}}},
        {"$match": {"unique_ids": {"$size": {"$gt": 1}}}}
    ]
    duplicates = await db.quizzes.aggregate(pipeline).to_list(None)
    for doc in duplicates:
        await db.quizzes.delete_many({"_id": {"$in": doc["unique_ids"][1:]}})

    # Then by video_id
    pipeline = [
        {"$group": {"_id": "$video_id", "unique_ids": {"$push": "$_id"}}},
        {"$match": {"unique_ids": {"$size": {"$gt": 1}}}}
    ]
    duplicates = await db.quizzes.aggregate(pipeline).to_list(None)
    for doc in duplicates:
        await db.quizzes.delete_many({"_id": {"$in": doc["unique_ids"][1:]}})

@api_router.post("/init-data")
async def initialize_data(force: bool = False):
    """Initialize sample courses and videos with stable IDs"""
    # Check if data exists
    if force:
        print("Forced re-initialization: clearing existing data...")
        await db.courses.delete_many({})
        await db.videos.delete_many({})
        await db.quizzes.delete_many({})
    else:
        existing = await db.courses.count_documents({})
        if existing > 0:
            return {"message": "Data already initialized. Use force=true to override."}
    
    # Sample courses with stable IDs
    courses_data = [
        {
            "id": "course-1",
            "title": "Python Programming Fundamentals",
            "description": "Master the basics of Python programming",
            "difficulty": "Easy",
            "topics": ["Python", "Programming", "Variables", "Functions"],
            "thumbnail": "https://images.unsplash.com/photo-1753998943619-b9cd910887e5?crop=entropy&cs=srgb&fm=jpg&q=85",
            "video_count": 4
        },
        {
            "id": "course-2",
            "title": "Data Science with Python",
            "description": "Learn data analysis and visualization",
            "difficulty": "Medium",
            "topics": ["Data Science", "Python", "Pandas", "Visualization"],
            "thumbnail": "https://images.unsplash.com/photo-1744782211816-c5224434614f?crop=entropy&cs=srgb&fm=jpg&q=85",
            "video_count": 4
        },
        {
            "id": "course-3",
            "title": "Machine Learning Advanced",
            "description": "Deep dive into ML algorithms",
            "difficulty": "Hard",
            "topics": ["Machine Learning", "Algorithms", "Neural Networks"],
            "thumbnail": "https://images.unsplash.com/photo-1764336312138-14a5368a6cd3?crop=entropy&cs=srgb&fm=jpg&q=85",
            "video_count": 3
        }
    ]
    
    await db.courses.insert_many(courses_data)
    
    # Sample videos with stable IDs
    videos_data = [
        # Course 1: Python Fundamentals
        {
            "id": "vid-python-1",
            "course_id": "course-1",
            "title": "Introduction to Python",
            "description": "Learn Python basics and syntax",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/01. Big O Intro.mp4",
            "duration": 600,
            "difficulty": "Easy",
            "topics": ["Python", "Programming"],
            "transcript": "Python is a high-level programming language. It is easy to learn and powerful for various applications.",
            "order": 1
        },
        {
            "id": "vid-python-2",
            "course_id": "course-1",
            "title": "Variables and Data Types",
            "description": "Understanding Python variables",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/02. Big O Worst Case.mp4",
            "duration": 480,
            "difficulty": "Easy",
            "topics": ["Python", "Variables"],
            "transcript": "Variables in Python store data values. Python has various data types including integers, strings, and lists.",
            "order": 2
        },
        {
            "id": "vid-python-3",
            "course_id": "course-1",
            "title": "Functions and Methods",
            "description": "Creating reusable code with functions",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/03. Big O O(n).mp4",
            "duration": 720,
            "difficulty": "Easy",
            "topics": ["Python", "Functions"],
            "transcript": "Functions are reusable blocks of code. They help organize your program and make it more maintainable.",
            "order": 3
        },
        {
            "id": "vid-python-4",
            "course_id": "course-1",
            "title": "Control Flow and Loops",
            "description": "Master if statements and loops",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/04. Big O Drop Constants.mp4",
            "duration": 540,
            "difficulty": "Easy",
            "topics": ["Python", "Programming"],
            "transcript": "Control flow statements like if-else and loops like for and while help control program execution.",
            "order": 4
        },
        # Course 2: Data Science
        {
            "id": "vid-ds-1",
            "course_id": "course-2",
            "title": "Introduction to Data Science",
            "description": "Overview of data science concepts",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/05. Big O O(n^2).mp4",
            "duration": 660,
            "difficulty": "Medium",
            "topics": ["Data Science"],
            "transcript": "Data science combines statistics, programming, and domain knowledge to extract insights from data.",
            "order": 1
        },
        {
            "id": "vid-ds-2",
            "course_id": "course-2",
            "title": "Pandas for Data Analysis",
            "description": "Working with dataframes in Pandas",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/06. Big O Drop Non-Dominants.mp4",
            "duration": 900,
            "difficulty": "Medium",
            "topics": ["Data Science", "Pandas", "Python"],
            "transcript": "Pandas is a powerful library for data manipulation. DataFrames allow you to work with tabular data efficiently.",
            "order": 2
        },
        {
            "id": "vid-ds-3",
            "course_id": "course-2",
            "title": "Data Visualization",
            "description": "Creating charts with matplotlib",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/07. Big O O(1).mp4",
            "duration": 780,
            "difficulty": "Medium",
            "topics": ["Data Science", "Visualization"],
            "transcript": "Data visualization helps communicate insights. Matplotlib and Seaborn are popular visualization libraries.",
            "order": 3
        },
        {
            "id": "vid-ds-4",
            "course_id": "course-2",
            "title": "Statistical Analysis",
            "description": "Statistical methods for data",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/08. Big O O(log n).mp4",
            "duration": 840,
            "difficulty": "Medium",
            "topics": ["Data Science", "Statistics"],
            "transcript": "Statistical analysis helps understand data patterns. Concepts like mean, median, and correlation are fundamental.",
            "order": 4
        },
        # Course 3: Machine Learning
        {
            "id": "vid-ml-1",
            "course_id": "course-3",
            "title": "Neural Networks Basics",
            "description": "Introduction to neural networks",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/09. Big O Different Terms for Inputs.mp4",
            "duration": 1020,
            "difficulty": "Hard",
            "topics": ["Machine Learning", "Neural Networks"],
            "transcript": "Neural networks are inspired by biological neurons. They consist of layers of interconnected nodes.",
            "order": 1
        },
        {
            "id": "vid-ml-2",
            "course_id": "course-3",
            "title": "Deep Learning Algorithms",
            "description": "Advanced deep learning techniques",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/10. Big O Lists.mp4",
            "duration": 1200,
            "difficulty": "Hard",
            "topics": ["Machine Learning", "Algorithms"],
            "transcript": "Deep learning uses multi-layer neural networks. CNNs for images and RNNs for sequences are popular architectures.",
            "order": 2
        },
        {
            "id": "vid-ml-3",
            "course_id": "course-3",
            "title": "Model Optimization",
            "description": "Optimizing ML models for production",
            "url": "gs://online-course-platform-68c2c.firebasestorage.app/DSA/11. Big O Wrap Up.mp4",
            "duration": 960,
            "difficulty": "Hard",
            "topics": ["Machine Learning", "Optimization"],
            "transcript": "Model optimization includes hyperparameter tuning, regularization, and efficient training strategies.",
            "order": 3
        }
    ]
    
    # Generate embeddings for videos
    print("Generating embeddings for videos...")
    for video in videos_data:
        embedding = sbert_model.encode(video['transcript'])
        video['embedding'] = embedding.tolist()
    
    await db.videos.insert_many(videos_data)
    
    # Create sample quizzes with stable IDs
    quizzes_data = []
    for i, video in enumerate(videos_data[:5]):  # First 5 videos
        quiz = {
            "id": f"quiz-{video['id']}",
            "video_id": video['id'],
            "questions": [
                {
                    "question": f"What is the main topic of this video?",
                    "options": [video['topics'][0], "JavaScript", "Ruby", "C++"],
                    "correct_answer": 0
                },
                {
                    "question": "What difficulty level is this content?",
                    "options": ["Easy", "Medium", "Hard", "Expert"],
                    "correct_answer": ["Easy", "Medium", "Hard"].index(video['difficulty'])
                }
            ]
        }
        quizzes_data.append(quiz)
    
    await db.quizzes.insert_many(quizzes_data)
    
    return {"message": "Sample data initialized successfully", "courses": len(courses_data), "videos": len(videos_data)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db_client():
    try:
        # Perform deduplication before enforcing unique indexes
        await clean_database()
        print("Database deduplication complete")
        
        await db.courses.create_index("id", unique=True)
        await db.videos.create_index("id", unique=True)
        await db.quizzes.create_index("id", unique=True)
        print("Verified unique indexes on courses, videos, and quizzes")
    except Exception as e:
        logger.warning(f"Could not complete startup database tasks: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
