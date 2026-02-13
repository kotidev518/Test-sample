from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth
from motor.motor_asyncio import AsyncIOMotorDatabase

from .db.session import get_db
from .services.course_service import CourseService
from .services.playlist_service import PlaylistService
from .services.mastery_service import MasteryService
from .services.video_service import VideoService
from .services.quiz_service import QuizService
from .services.analytics_service import AnalyticsService
from .services.recommendation_service import RecommendationService
from .services.auth_service import AuthService
from .services.vector_service import VectorService

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Verify Firebase ID token and return user from database"""
    try:
        decoded_token = firebase_auth.verify_id_token(credentials.credentials)
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        
        if not firebase_uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"firebase_uid": firebase_uid}, {"_id": 0})
        
        if not user and email:
            user = await db.users.find_one({"email": email}, {"_id": 0})
            if user:
                await db.users.update_one(
                    {"email": email},
                    {"$set": {"firebase_uid": firebase_uid}}
                )
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found. Please register first.")
        
        return user
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_admin_user(user = Depends(get_current_user)):
    """Verify that the current user is an admin"""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def get_course_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> CourseService:
    return CourseService(db)

async def get_playlist_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> PlaylistService:
    return PlaylistService(db)

async def get_mastery_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> MasteryService:
    return MasteryService(db)

async def get_video_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> VideoService:
    return VideoService(db)

async def get_quiz_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> QuizService:
    return QuizService(db)

async def get_analytics_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

async def get_recommendation_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> RecommendationService:
    return RecommendationService(db)

async def get_auth_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> AuthService:
    return AuthService(db)

async def get_vector_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> VectorService:
    return VectorService(db)
