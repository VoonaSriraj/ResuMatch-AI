"""
Recommended jobs endpoints with LinkedIn integration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.job import RecommendedJob
from app.models.resume import Resume
from app.models.activity_log import ActivityLog
from app.utils.auth import get_current_active_user
from app.services.linkedin_service import linkedin_service
from app.services.match_engine import match_engine_service
from app.services.job_service import JobService
from app.services.adzuna_service import AdzunaJobService
from app.utils.logger import get_logger
from app.config import settings

router = APIRouter()
logger = get_logger(__name__)

# Pydantic models
class JobSearchRequest(BaseModel):
    keywords: Optional[List[str]] = None
    location: Optional[str] = None
    experience_level: Optional[str] = None
    job_type: Optional[str] = None
    limit: Optional[int] = 25

class RecommendedJobResponse(BaseModel):
    id: int
    linkedin_job_id: Optional[str]
    external_job_id: Optional[str]
    title: str
    company: str
    location: Optional[str]
    description: Optional[str]
    match_score: Optional[float]
    apply_link: Optional[str]
    source: str
    salary_info: Optional[str]
    job_type: Optional[str]
    seniority_level: Optional[str]
    remote_friendly: Optional[str]
    posted_date: Optional[str]
    application_deadline: Optional[str]
    is_applied: str
    notes: Optional[str]
    fetched_at: str

class RecommendedJobsResponse(BaseModel):
    jobs: List[RecommendedJobResponse]
    total_count: int
    search_criteria: dict

class JobApplicationUpdate(BaseModel):
    job_id: int
    application_status: str  # applied, rejected, interview, offer
    notes: Optional[str] = None

@router.post("/search", response_model=RecommendedJobsResponse)
async def search_and_recommend_jobs(
    request: JobSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search for jobs and get recommendations based on user's resume"""
    try:
        if not current_user.linkedin_access_token and not settings.debug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn access token required. Please connect your LinkedIn account."
            )
        
        # Get user's latest resume for matching
        latest_resume = db.query(Resume).filter(
            Resume.user_id == current_user.id,
            Resume.processing_status == "completed"
        ).order_by(Resume.upload_date.desc()).first()
        
        if not latest_resume:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No processed resume found. Please upload and process your resume first."
            )
        
        # Search jobs - try LinkedIn first, then fallback to RapidAPI
        jobs_data = []
        
        try:
            if current_user.linkedin_access_token or settings.debug:
                # Try LinkedIn service first
                jobs_data = await linkedin_service.search_jobs(
                    access_token=current_user.linkedin_access_token or "dev-token",
                    keywords=request.keywords,
                    location=request.location,
                    experience_level=request.experience_level,
                    job_type=request.job_type,
                    limit=request.limit or 25
                )
                logger.info(f"LinkedIn service returned {len(jobs_data)} jobs")
            else:
                logger.info("No LinkedIn access token, using RapidAPI fallback")
                
        except Exception as e:
            logger.warning(f"LinkedIn service failed: {str(e)}, falling back to RapidAPI")
        
        # If LinkedIn failed or returned no results, use Adzuna API
        if not jobs_data:
            try:
                # Use Adzuna API for real-time jobs
                adzuna_service = AdzunaJobService()
                adzuna_jobs = await adzuna_service.search_jobs(
                    keywords=request.keywords,
                    location=request.location,
                    limit=request.limit or 25
                )
                
                # Convert Adzuna format to LinkedIn format for compatibility
                jobs_data = []
                for job in adzuna_jobs:
                    jobs_data.append({
                        "linkedin_job_id": job.get("job_id", ""),
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "description": job.get("description", ""),
                        "apply_url": job.get("apply_url", ""),
                        "skills": job.get("skills_required", []),
                        "salary_range": job.get("salary_range"),
                        "employment_type": job.get("job_type"),
                        "seniority_level": job.get("seniority_level"),
                        "job_type": job.get("job_type")
                    })
                
                logger.info(f"Adzuna API returned {len(jobs_data)} real-time jobs")
                
            except Exception as e:
                logger.error(f"Adzuna API failed: {str(e)}, trying JobService fallback")
                # Final fallback to JobService
                try:
                    job_service = JobService()
                    rapidapi_jobs = await job_service.fetch_jobs_from_rapidapi(
                        keywords=request.keywords,
                        location=request.location,
                        limit=request.limit or 25
                    )
                    
                    # Convert RapidAPI format to LinkedIn format for compatibility
                    jobs_data = []
                    for job in rapidapi_jobs:
                        jobs_data.append({
                            "linkedin_job_id": job.get("linkedin_job_id", ""),
                            "title": job.get("title", ""),
                            "company": job.get("company", ""),
                            "location": job.get("location", ""),
                            "description": job.get("description", ""),
                            "apply_url": job.get("apply_url", ""),
                            "skills": job.get("skills", []),
                            "salary_range": job.get("salary_range"),
                            "employment_type": job.get("employment_type"),
                            "seniority_level": job.get("seniority_level"),
                            "job_type": job.get("job_type")
                        })
                    logger.info(f"JobService fallback returned {len(jobs_data)} jobs")
                except Exception as e:
                    logger.error(f"JobService fallback also failed: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to fetch jobs from all sources"
                    )
        
        # Calculate match scores for each job
        jobs_with_scores = []
        for job_data in jobs_data:
            try:
                # Parse resume skills and experience from JSON strings
                import json
                def parse_json_field(value):
                    if value is None:
                        return []
                    if isinstance(value, str):
                        try:
                            # Try to parse as JSON first
                            parsed = json.loads(value)
                            if isinstance(parsed, list):
                                return parsed
                            else:
                                return [parsed]
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON, split by spaces and clean up
                            if isinstance(value, str) and value.strip():
                                # Split by spaces and filter out empty strings
                                skills = [skill.strip() for skill in value.split() if skill.strip()]
                                return skills
                            return []
                    elif isinstance(value, list):
                        return value
                    return []
                
                # Calculate match score using the resume
                match_result = await match_engine_service.calculate_comprehensive_match_score(
                    resume_text=latest_resume.extracted_text or "",
                    job_text=job_data.get("description", ""),
                    resume_skills=parse_json_field(latest_resume.parsed_skills),
                    resume_experience=parse_json_field(latest_resume.parsed_experience),
                    job_skills=job_data.get("skills", []),  # Use skills from job data
                    job_requirements=[]  # Would need to parse from description
                )
                
                job_data["match_score"] = match_result.get("overall_match_score", 0)
                jobs_with_scores.append(job_data)
                
            except Exception as e:
                logger.error(f"Failed to calculate match score for job {job_data.get('linkedin_job_id')}: {str(e)}")
                job_data["match_score"] = 0
                jobs_with_scores.append(job_data)
        
        # Sort by match score
        jobs_with_scores.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        # Save recommended jobs to database
        saved_jobs = []
        for job_data in jobs_with_scores:
            # Check if job already exists
            existing_job = db.query(RecommendedJob).filter(
                RecommendedJob.user_id == current_user.id,
                RecommendedJob.linkedin_job_id == job_data.get("linkedin_job_id")
            ).first()
            
            if not existing_job:
                recommended_job = RecommendedJob(
                    user_id=current_user.id,
                    linkedin_job_id=job_data.get("linkedin_job_id"),
                    title=job_data.get("title", ""),
                    company=job_data.get("company", ""),
                    location=job_data.get("location"),
                    description=job_data.get("description"),
                    match_score=job_data.get("match_score", 0),
                    apply_link=job_data.get("apply_url"),
                    source="linkedin",
                    salary_info=job_data.get("salary_range"),
                    job_type=job_data.get("employment_type"),
                    seniority_level=job_data.get("seniority_level"),
                    remote_friendly=job_data.get("job_type"),
                    posted_date=None,  # Will be set to current time automatically
                    application_deadline=None
                )
                
                db.add(recommended_job)
                db.commit()
                db.refresh(recommended_job)
                saved_jobs.append(recommended_job)
            else:
                # Update existing job with new match score
                existing_job.match_score = job_data.get("match_score", 0)
                existing_job.description = job_data.get("description")
                existing_job.apply_link = job_data.get("apply_url")
                db.commit()
                saved_jobs.append(existing_job)
        
        # Convert to response format
        job_responses = [
            RecommendedJobResponse(
                id=job.id,
                linkedin_job_id=job.linkedin_job_id,
                external_job_id=job.external_job_id,
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                match_score=job.match_score,
                apply_link=job.apply_link,
                source=job.source,
                salary_info=job.salary_info,
                job_type=job.job_type,
                seniority_level=job.seniority_level,
                remote_friendly=job.remote_friendly,
                posted_date=job.posted_date.isoformat() if job.posted_date else None,
                application_deadline=job.application_deadline.isoformat() if job.application_deadline else None,
                is_applied=job.is_applied,
                notes=job.notes,
                fetched_at=job.fetched_at.isoformat()
            )
            for job in saved_jobs
        ]
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="job_search",
            description=f"Job search performed with {len(job_responses)} results",
            meta_data={
                "keywords": request.keywords,
                "location": request.location,
                "results_count": len(job_responses),
                "resume_id": latest_resume.id
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Job search completed for user {current_user.id} with {len(job_responses)} results")
        
        return RecommendedJobsResponse(
            jobs=job_responses,
            total_count=len(job_responses),
            search_criteria={
                "keywords": request.keywords,
                "location": request.location,
                "experience_level": request.experience_level,
                "job_type": request.job_type,
                "limit": request.limit
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job search failed"
        )

@router.get("/recommended", response_model=RecommendedJobsResponse)
async def get_recommended_jobs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    min_match_score: Optional[float] = None
):
    """Get previously recommended jobs for the user"""
    try:
        query = db.query(RecommendedJob).filter(
            RecommendedJob.user_id == current_user.id
        )
        
        if min_match_score is not None:
            query = query.filter(RecommendedJob.match_score >= min_match_score)
        
        jobs = query.order_by(RecommendedJob.match_score.desc()).offset(offset).limit(limit).all()
        total_count = query.count()
        
        job_responses = [
            RecommendedJobResponse(
                id=job.id,
                linkedin_job_id=job.linkedin_job_id,
                external_job_id=job.external_job_id,
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                match_score=job.match_score,
                apply_link=job.apply_link,
                source=job.source,
                salary_info=job.salary_info,
                job_type=job.job_type,
                seniority_level=job.seniority_level,
                remote_friendly=job.remote_friendly,
                posted_date=job.posted_date.isoformat() if job.posted_date else None,
                application_deadline=job.application_deadline.isoformat() if job.application_deadline else None,
                is_applied=job.is_applied,
                notes=job.notes,
                fetched_at=job.fetched_at.isoformat()
            )
            for job in jobs
        ]
        
        return RecommendedJobsResponse(
            jobs=job_responses,
            total_count=total_count,
            search_criteria={
                "min_match_score": min_match_score,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get recommended jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recommended jobs"
        )

@router.put("/application-status")
async def update_application_status(
    request: JobApplicationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update application status for a recommended job"""
    try:
        job = db.query(RecommendedJob).filter(
            RecommendedJob.id == request.job_id,
            RecommendedJob.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommended job not found"
            )
        
        # Update application status
        job.is_applied = request.application_status
        if request.notes:
            job.notes = request.notes
        
        db.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="job_application_status_update",
            description=f"Application status updated to '{request.application_status}' for {job.title} at {job.company}",
            meta_data={
                "job_id": job.id,
                "status": request.application_status,
                "job_title": job.title,
                "company": job.company
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Application status updated for user {current_user.id}: {job.title} -> {request.application_status}")
        
        return {"message": "Application status updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update application status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application status"
        )

@router.get("/application-stats")
async def get_application_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get application statistics for the user"""
    try:
        total_jobs = db.query(RecommendedJob).filter(
            RecommendedJob.user_id == current_user.id
        ).count()
        
        applied_jobs = db.query(RecommendedJob).filter(
            RecommendedJob.user_id == current_user.id,
            RecommendedJob.is_applied == "applied"
        ).count()
        
        interview_jobs = db.query(RecommendedJob).filter(
            RecommendedJob.user_id == current_user.id,
            RecommendedJob.is_applied == "interview"
        ).count()
        
        rejected_jobs = db.query(RecommendedJob).filter(
            RecommendedJob.user_id == current_user.id,
            RecommendedJob.is_applied == "rejected"
        ).count()
        
        # Get average match score
        avg_match_score = db.query(RecommendedJob.match_score).filter(
            RecommendedJob.user_id == current_user.id,
            RecommendedJob.match_score.isnot(None)
        ).all()
        
        avg_score = sum(score[0] for score in avg_match_score) / len(avg_match_score) if avg_match_score else 0
        
        return {
            "total_jobs_recommended": total_jobs,
            "jobs_applied": applied_jobs,
            "jobs_interview": interview_jobs,
            "jobs_rejected": rejected_jobs,
            "application_rate": (applied_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            "interview_rate": (interview_jobs / applied_jobs * 100) if applied_jobs > 0 else 0,
            "average_match_score": round(avg_score, 2)
        }
        
    except Exception as e:
        logger.error(f"Failed to get application statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application statistics"
        )
