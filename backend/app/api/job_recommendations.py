"""
Job Recommendations API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import requests
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.job_recommendations import Job, UserProfile
from app.models.resume import Resume
from app.utils.auth import get_current_active_user
from app.services.groq_service import GroqService
from app.services.job_service import JobService
from app.services.adzuna_service import AdzunaJobService
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Pydantic models for API responses
from pydantic import BaseModel

class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    description: Optional[str]
    linkedin_url: Optional[str]
    match_score: float
    posted_at: Optional[datetime]
    job_type: Optional[str]
    seniority_level: Optional[str]
    salary_range: Optional[str]
    remote_friendly: Optional[str]
    skills_required: Optional[List[str]]
    source: str

class JobRecommendationsResponse(BaseModel):
    jobs: List[JobResponse]
    total_count: int
    user_profile_updated: bool

class JobRecommendationsRequest(BaseModel):
    keywords: Optional[List[str]] = None
    location: Optional[str] = None
    limit: int = 10
    force_refresh: bool = False

def parse_json_field(value):
    """Parse JSON string field to list"""
    if value is None:
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            else:
                return [parsed]
        except (json.JSONDecodeError, TypeError):
            if isinstance(value, str) and value.strip():
                skills = [skill.strip() for skill in value.split() if skill.strip()]
                return skills
            return []
    elif isinstance(value, list):
        return value
    return []

def create_job_response(job: Job) -> JobResponse:
    """Create JobResponse from Job model"""
    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        linkedin_url=job.linkedin_url,
        match_score=job.match_score,
        posted_at=job.posted_at,
        job_type=job.job_type,
        seniority_level=job.seniority_level,
        salary_range=job.salary_range,
        remote_friendly=job.remote_friendly,
        skills_required=parse_json_field(job.skills_required),
        source=job.source
    )

async def fetch_jobs_from_linkedin(keywords: List[str] = None, location: str = None, limit: int = 25) -> List[dict]:
    """Fetch jobs from Adzuna API for India"""
    try:
        # Use Adzuna API for real-time jobs
        adzuna_service = AdzunaJobService()
        jobs_data = await adzuna_service.search_jobs(
            keywords=keywords,
            location=location,
            limit=limit
        )
        
        # Convert Adzuna format to job recommendations format
        formatted_jobs = []
        for job in jobs_data:
            formatted_jobs.append({
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "description": job.get("description", ""),
                "linkedin_url": job.get("apply_url", ""),
                "job_type": job.get("job_type", "full-time"),
                "seniority_level": job.get("seniority_level", "mid"),
                "salary_range": job.get("salary_range"),
                "remote_friendly": job.get("remote_friendly", "on-site"),
                "skills_required": job.get("skills_required", [])
            })
        
        logger.info(f"Fetched {len(formatted_jobs)} real-time jobs from Adzuna API")
        return formatted_jobs
        
    except Exception as e:
        logger.error(f"Failed to fetch jobs from Adzuna API: {str(e)}")
        # Fallback to enhanced mock data if Adzuna fails
        try:
            job_service = JobService()
            fallback_jobs = await job_service.fetch_jobs_from_rapidapi(keywords, location, limit)
            logger.info(f"Using fallback jobs: {len(fallback_jobs)}")
            return fallback_jobs
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {str(fallback_error)}")
            return []

async def update_user_profile(user: User, db: Session) -> bool:
    """Update user profile from latest resume"""
    try:
        # Get latest resume
        latest_resume = db.query(Resume).filter(
            Resume.user_id == user.id,
            Resume.processing_status == "completed"
        ).order_by(Resume.upload_date.desc()).first()
        
        # Get or create user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
        
        if latest_resume:
            # Update profile with resume data
            profile.resume_text = latest_resume.extracted_text
            profile.skills = latest_resume.parsed_skills
            profile.experience_years = 3  # Default, could be extracted from resume
            logger.info(f"Updated user profile with resume data for user {user.id}")
        else:
            # No resume available, use basic profile
            profile.resume_text = ""
            profile.skills = "[]"
            profile.experience_years = 2  # Default for LinkedIn-only users
            logger.info(f"Using basic profile for user {user.id} (no resume uploaded)")
        
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"Failed to update user profile: {str(e)}")
        return False

async def calculate_job_match_scores(jobs: List[dict], user_profile: UserProfile, groq_service: GroqService) -> List[dict]:
    """Calculate match scores for jobs using Groq AI"""
    try:
        resume_text = user_profile.resume_text or ""
        user_skills = parse_json_field(user_profile.skills)
        
        scored_jobs = []
        for job in jobs:
            try:
                # Calculate match score using Groq AI
                match_result = await groq_service.calculate_match_score(
                    resume_text=resume_text,
                    job_text=job.get("description", "")
                )
                
                job["match_score"] = match_result.get("overall_match_score", 0.0)
                scored_jobs.append(job)
                
            except Exception as e:
                logger.error(f"Failed to calculate match score for job {job.get('title')}: {str(e)}")
                job["match_score"] = 0.0
                scored_jobs.append(job)
        
        return scored_jobs
        
    except Exception as e:
        logger.error(f"Failed to calculate job match scores: {str(e)}")
        return jobs

@router.post("/api/jobs/recommendations", response_model=JobRecommendationsResponse)
async def get_job_recommendations(
    request: JobRecommendationsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get personalized job recommendations based on user profile"""
    try:
        # Update user profile from latest resume
        profile_updated = await update_user_profile(current_user, db)
        
        # Get user profile
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not user_profile:
            # Create a basic profile if none exists (for LinkedIn-only users)
            user_profile = UserProfile(user_id=current_user.id)
            db.add(user_profile)
            db.commit()
            logger.info(f"Created basic profile for user {current_user.id}")
        
        # Check if we need to refresh jobs or use cached ones
        recent_jobs = db.query(Job).filter(
            Job.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        if not recent_jobs or request.force_refresh:
            # Fetch new jobs
            logger.info(f"Fetching new jobs for user {current_user.id}")
            jobs_data = await fetch_jobs_from_linkedin(
                keywords=request.keywords,
                location=request.location,
                limit=50  # Fetch more to have better selection
            )
            
            # Clear old jobs
            db.query(Job).delete()
            
            # Calculate match scores
            groq_service = GroqService()
            scored_jobs = await calculate_job_match_scores(jobs_data, user_profile, groq_service)
            
            # Store jobs in database
            for job_data in scored_jobs:
                job = Job(
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    description=job_data["description"],
                    linkedin_url=job_data["linkedin_url"],
                    match_score=job_data["match_score"],
                    job_type=job_data["job_type"],
                    seniority_level=job_data["seniority_level"],
                    salary_range=job_data["salary_range"],
                    remote_friendly=job_data["remote_friendly"],
                    skills_required=json.dumps(job_data["skills_required"]),
                    source="linkedin"
                )
                db.add(job)
            
            db.commit()
            
            # Get the stored jobs
            recent_jobs = db.query(Job).all()
        
        # Sort by match score and return top recommendations
        sorted_jobs = sorted(recent_jobs, key=lambda x: x.match_score, reverse=True)
        top_jobs = sorted_jobs[:request.limit]
        
        # Convert to response format
        job_responses = [create_job_response(job) for job in top_jobs]
        
        logger.info(f"Returned {len(job_responses)} job recommendations for user {current_user.id}")
        
        return JobRecommendationsResponse(
            jobs=job_responses,
            total_count=len(recent_jobs),
            user_profile_updated=profile_updated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job recommendations")

@router.get("/api/jobs/recommendations", response_model=JobRecommendationsResponse)
async def get_cached_recommendations(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get cached job recommendations"""
    try:
        # Get cached jobs
        jobs = db.query(Job).order_by(Job.match_score.desc()).limit(limit).all()
        
        if not jobs:
            raise HTTPException(status_code=404, detail="No job recommendations found. Please request new recommendations.")
        
        job_responses = [create_job_response(job) for job in jobs]
        
        return JobRecommendationsResponse(
            jobs=job_responses,
            total_count=len(jobs),
            user_profile_updated=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cached recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cached recommendations")
