import logging
import os
import firebase_admin
from firebase_admin import credentials, storage, auth
from motor.motor_asyncio import AsyncIOMotorClient
from sentence_transformers import SentenceTransformer
from .config import settings

# Initialize MongoDB
client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]

# Initialize Firebase Admin
def init_firebase():
    try:
        print(f"Initializing Firebase... Credentials path: {settings.FIREBASE_CREDENTIALS}")
            
        if not firebase_admin._apps:
            cred_path = settings.FIREBASE_CREDENTIALS
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

# Initialize SBERT model
sbert_model = None

def load_sbert_model():
    global sbert_model
    print("Loading SBERT model...")
    sbert_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("SBERT model loaded successfully")
    
    # Initialize embedding service with the loaded model
    from .embedding_service import init_embedding_service
    init_embedding_service(sbert_model)
    print("Embedding service initialized")

async def ensure_indexes():
    """Create indexes to prevent duplicates and optimize queries"""
    print("Ensuring database indexes...")
    try:
        # Existing indexes
        await db.courses.create_index("id", unique=True)
        await db.videos.create_index("id", unique=True)
        
        # New indexes for vector search and processing queue
        await db.videos.create_index("processing_status")
        await db.videos.create_index([("course_id", 1), ("processing_status", 1)])
        await db.processing_queue.create_index([("status", 1), ("priority", -1)])
        await db.processing_queue.create_index("video_id", unique=True)
        
        print("Database indexes ensured successfully")
    except Exception as e:
        print(f"Error creating indexes: {e}")

# Initialize services on module import or explicit call? 
# Better to call explicit init function in main.py startup event, 
# but for simplicity we can init firebase here if it's safe.
# init_firebase() 
# We'll call these from main.py lifespan/startup for better control.
