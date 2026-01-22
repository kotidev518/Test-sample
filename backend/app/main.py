from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .database import load_sbert_model, init_firebase, ensure_indexes
from .routers import auth, courses, analytics, recommendations, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_firebase()
    load_sbert_model()
    await ensure_indexes()
    yield
    # Shutdown
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

@app.get("/")
async def root():
    return {"message": "Welcome to the Course Platform API"}
