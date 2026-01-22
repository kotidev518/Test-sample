from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    initial_level: Optional[str] = "Medium"  # Easy, Medium, Hard

class UserProfileCreate(BaseModel):
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
    role: str = "student"  # "student" or "admin"
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
    url: Optional[str] = None
    youtube_id: Optional[str] = None
    thumbnail: Optional[str] = None
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
