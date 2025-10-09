"""
Resume optimization endpoints for improving resume-job matches
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.models.job import JobDescription
from app.models.activity_log import ActivityLog
from app.utils.auth import get_current_active_user
from app.services.match_engine import match_engine_service
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Pydantic models
class ResumeOptimizationRequest(BaseModel):
    resume_id: int
    job_id: int

class ResumeOptimizationResponse(BaseModel):
    optimized_resume_text: str
    changes_made: list
    keywords_added: list
    improvements: list
    original_score: float
    optimized_score: float
    improvement_score: float
    processing_status: str

@router.post("/optimize", response_model=ResumeOptimizationResponse)
async def optimize_resume_for_job(
    request: ResumeOptimizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Optimize a resume for a specific job description"""
    try:
        # Get resume and job
        resume = db.query(Resume).filter(
            Resume.id == request.resume_id,
            Resume.user_id == current_user.id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        job = db.query(JobDescription).filter(
            JobDescription.id == request.job_id,
            JobDescription.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        
        # Check if both are processed
        if resume.processing_status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume is not fully processed yet"
            )
        
        if job.processing_status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is not fully processed yet"
            )
        
        if not resume.extracted_text or not job.job_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume or job description text is missing"
            )
        
        # Optimize resume
        optimization_result = await match_engine_service.optimize_resume_for_job(
            resume.extracted_text,
            job.job_text
        )
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="resume_optimization",
            description=f"Resume optimized for {job.title} - Score improved by {optimization_result.get('improvement_score', 0):.1f}%",
            meta_data={
                "resume_id": resume.id,
                "job_id": job.id,
                "original_score": optimization_result.get("original_score", 0),
                "optimized_score": optimization_result.get("optimized_score", 0),
                "improvement_score": optimization_result.get("improvement_score", 0)
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Resume optimized for user {current_user.id} - Score improved by {optimization_result.get('improvement_score', 0):.1f}%")
        
        return ResumeOptimizationResponse(
            optimized_resume_text=optimization_result.get("optimized_resume_text", resume.extracted_text),
            changes_made=optimization_result.get("changes_made", []),
            keywords_added=optimization_result.get("keywords_added", []),
            improvements=optimization_result.get("improvements", []),
            original_score=optimization_result.get("original_score", 0),
            optimized_score=optimization_result.get("optimized_score", 0),
            improvement_score=optimization_result.get("improvement_score", 0),
            processing_status=optimization_result.get("processing_status", "completed")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume optimization failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume optimization failed"
        )

@router.post("/optimize-text")
async def optimize_resume_text_direct(
    resume_text: str,
    job_text: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Optimize resume text directly without database records"""
    try:
        if not resume_text.strip() or not job_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both resume text and job text are required"
            )
        
        # Optimize resume
        optimization_result = await match_engine_service.optimize_resume_for_job(
            resume_text,
            job_text
        )
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="resume_text_optimization",
            description=f"Resume text optimized - Score improved by {optimization_result.get('improvement_score', 0):.1f}%",
            meta_data={
                "original_score": optimization_result.get("original_score", 0),
                "optimized_score": optimization_result.get("optimized_score", 0),
                "improvement_score": optimization_result.get("improvement_score", 0)
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Resume text optimized for user {current_user.id} - Score improved by {optimization_result.get('improvement_score', 0):.1f}%")
        
        return {
            "message": "Resume text optimized successfully",
            "result": optimization_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume text optimization failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume text optimization failed"
        )

@router.get("/suggestions/{resume_id}/{job_id}")
async def get_optimization_suggestions(
    resume_id: int,
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get optimization suggestions for a resume-job pair"""
    try:
        # Get resume and job
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == current_user.id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        job = db.query(JobDescription).filter(
            JobDescription.id == job_id,
            JobDescription.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        
        # Calculate current match score
        match_result = await match_engine_service.calculate_comprehensive_match_score(
            resume_text=resume.extracted_text or "",
            job_text=job.job_text or "",
            resume_skills=resume.parsed_skills or [],
            resume_experience=resume.parsed_experience or [],
            job_skills=job.extracted_skills or [],
            job_requirements=job.experience_requirements or []
        )
        
        # Generate suggestions based on match analysis
        suggestions = {
            "current_match_score": match_result.get("overall_match_score", 0),
            "missing_keywords": match_result.get("missing_keywords", []),
            "matching_keywords": match_result.get("matching_keywords", []),
            "improvement_suggestions": match_result.get("suggestions", []),
            "skills_analysis": {
                "missing_skills": list(set(job.extracted_skills or []) - set(resume.parsed_skills or [])),
                "matching_skills": list(set(job.extracted_skills or []) & set(resume.parsed_skills or [])),
                "extra_skills": list(set(resume.parsed_skills or []) - set(job.extracted_skills or []))
            },
            "experience_analysis": {
                "missing_requirements": list(set(job.experience_requirements or []) - set(resume.parsed_experience or [])),
                "matching_requirements": list(set(job.experience_requirements or []) & set(resume.parsed_experience or []))
            },
            "optimization_tips": [
                "Add missing keywords naturally throughout your resume",
                "Quantify your achievements with specific numbers and metrics",
                "Use action verbs to describe your accomplishments",
                "Align your skills section with job requirements",
                "Highlight relevant experience prominently",
                "Include industry-specific terminology",
                "Show progression and growth in your career"
            ]
        }
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="optimization_suggestions_request",
            description=f"Optimization suggestions requested for {job.title}",
            meta_data={
                "resume_id": resume.id,
                "job_id": job.id,
                "current_match_score": match_result.get("overall_match_score", 0)
            }
        )
        db.add(activity)
        db.commit()
        
        return {
            "message": "Optimization suggestions generated successfully",
            "suggestions": suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get optimization suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate optimization suggestions"
        )
