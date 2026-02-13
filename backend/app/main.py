from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import asyncio

from .database import init_firebase, ensure_indexes
from .services.embedding_service import init_embedding_service
from .routers import auth, courses, analytics, recommendations, admin, vectors
from .services.processing_queue_service import processing_worker
from .core.config import settings
from .db.session import db_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db_manager.init_db()
    init_firebase()
    init_embedding_service()  # Now initializes for lazy loading
    await ensure_indexes()
    
    yield
    
    # Shutdown
    print("Shutting down background worker...")
    await processing_worker.stop_worker()
    await db_manager.close_db()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(vectors.router, prefix="/api")  # Vector search endpoints

@app.get("/")
async def root():
    return {"message": "Welcome to the Course Platform API"}
