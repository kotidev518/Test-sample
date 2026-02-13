import re
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import List, Optional

# Password must contain: lowercase, uppercase, number, special char (@#$), min 8 chars
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$])[A-Za-z\d@#$]{8,}$')
PASSWORD_ERROR_MESSAGE = (
    'Password must contain at least 8 characters, one lowercase letter, '
    'one uppercase letter, one number, and one special character (@, #, $)'
)

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    initial_level: Optional[str] = "Easy"  # Easy, Medium, Hard
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not PASSWORD_REGEX.match(v):
            raise ValueError(PASSWORD_ERROR_MESSAGE)
        return v

class UserProfileCreate(BaseModel):
    name: str
    initial_level: Optional[str] = "Easy"  # Easy, Medium, Hard

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not PASSWORD_REGEX.match(v):
            raise ValueError(PASSWORD_ERROR_MESSAGE)
        return v

class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    initial_level: str
    role: str = "student"  # "student" or "admin"
    created_at: str

class UserDB(UserProfile):
    firebase_uid: str

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

class CourseDB(Course):
    channel: Optional[str] = None
    imported_at: str
    imported_by: str

class Video(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    course_id: str
    title: str
    description: str
    url: Optional[str] = None
    youtube_id: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: int  # seconds
    difficulty: str
    topics: List[str]
    transcript: Optional[str] = ""
    order: int

class VideoDB(Video):
    processing_status: str = "pending"  # pending, processing, completed, failed

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

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str

class ProcessingJobDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    video_id: str
    status: str = "pending"  # pending, processing, completed, failed
    priority: int = 0
    retry_count: int = 0
    error_message: str = ""
    created_at: str
    updated_at: str
