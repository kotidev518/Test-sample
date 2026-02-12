from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import asyncio

from .database import load_sbert_model, init_firebase, ensure_indexes
from .routers import auth, courses, analytics, recommendations, admin, vectors
from .processing_queue_service import processing_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_firebase()
    load_sbert_model()
    await ensure_indexes()
    
    # Start background processing worker
    worker_task = asyncio.create_task(processing_worker.start_worker())
    print("Background worker started")
    
    yield
    
    # Shutdown
    print("Shutting down background worker...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

# CORS Configuration
origins = ["*"]  # Allow all origins for development

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
