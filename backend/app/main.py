"""
JobAlign AI - FastAPI Backend
Main application entry point with all routes and middleware
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from contextlib import asynccontextmanager

from app.api import (
    auth,
    upload_resume,
    upload_job,
    match_score,
    optimize_resume,
    generate_interview_questions,
    recommended_jobs,
    linkedin_connect,
    stripe_webhook
)
from app.models import user, resume, job, match_history, subscription, activity_log
from app.database import engine, Base
from sqlalchemy import text
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create database tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting JobAlign AI Backend...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    yield
    # Shutdown
    logger.info("Shutting down JobAlign AI Backend...")

app = FastAPI(
    title="JobAlign AI Backend",
    description="AI-powered job matching and resume optimization platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload_resume.router, prefix="/api/resume", tags=["Resume"])
app.include_router(upload_job.router, prefix="/api/job", tags=["Job"])
app.include_router(match_score.router, prefix="/api/match", tags=["Matching"])
app.include_router(optimize_resume.router, prefix="/api/optimize", tags=["Optimization"])
app.include_router(generate_interview_questions.router, prefix="/api/interview", tags=["Interview Prep"])
app.include_router(recommended_jobs.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(linkedin_connect.router, prefix="/api/linkedin", tags=["LinkedIn"])
app.include_router(stripe_webhook.router, prefix="/api/stripe", tags=["Stripe"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "JobAlign AI Backend is running!",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        from app.database import get_db
        db = next(get_db())
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
