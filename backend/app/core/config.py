from pathlib import Path
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    # MongoDB
    MONGO_URL: str
    DB_NAME: str = "course_platform"
    
    # Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 72
    
    # Firebase
    FIREBASE_STORAGE_BUCKET: Optional[str] = None
    FIREBASE_CREDENTIALS: str = "serviceAccountKey.json"
    
    # External APIs
    YOUTUBE_API_KEY: str
    GEMINI_API_KEY: str
    
    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6379"
    
    # CORS
    # Can be a JSON list or a comma-separated string
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Fallback to stripping brackets and splitting
                    v = v[1:-1]
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def get_firebase_credentials_path(self) -> str:
        """Resolve firebase credentials path relative to ROOT_DIR if not absolute."""
        path = Path(self.FIREBASE_CREDENTIALS)
        if not path.is_absolute():
            return str(self.BASE_DIR / path)
        return str(path)


settings = Settings()
