import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

class Settings:
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'learning_platform')
    JWT_SECRET: str = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRATION_HOURS: int = 72
    FIREBASE_STORAGE_BUCKET: str = os.environ.get('FIREBASE_STORAGE_BUCKET')
    YOUTUBE_API_KEY: str = os.environ.get('YOUTUBE_API_KEY', '')
    GEMINI_API_KEY: str = os.environ.get('GEMINI_API_KEY', '')

    def __init__(self):
        # Resolve absolute path for credentials
        creds = os.environ.get('FIREBASE_CREDENTIALS', 'serviceAccountKey.json')
        if not os.path.isabs(creds):
            self.FIREBASE_CREDENTIALS = str(ROOT_DIR / creds)
        else:
            self.FIREBASE_CREDENTIALS = creds

settings = Settings()
