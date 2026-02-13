import os
import firebase_admin
from firebase_admin import credentials
from motor.motor_asyncio import AsyncIOMotorClient
from .core.config import settings
from .db.session import db_manager

# Backward compatibility for existing code
db = db_manager.get_db()

def init_firebase():
    """Initialize Firebase Admin with proper error handling and configuration."""
    try:
        if not firebase_admin._apps:
            cred_path = settings.get_firebase_credentials_path()
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                })
                print("Firebase Admin initialized successfully")
            else:
                print(f"Warning: Firebase credentials not found at {cred_path}")
    except Exception as e:
        print(f"Error initializing Firebase Admin: {e}")

async def ensure_indexes():
    """Create database indexes using the centralized session manager."""
    print("Ensuring database indexes...")
    database = db_manager.get_db()
    try:
        await database.courses.create_index("id", unique=True)
        await database.videos.create_index("id", unique=True)
        await database.videos.create_index("processing_status")
        await database.videos.create_index([("course_id", 1), ("processing_status", 1)])
        await database.processing_queue.create_index([("status", 1), ("priority", -1)])
        await database.processing_queue.create_index("video_id", unique=True)
        print("Database indexes ensured successfully")
    except Exception as e:
        print(f"Error creating indexes: {e}")
