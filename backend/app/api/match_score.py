"""
Match score calculation endpoints for resume-job compatibility
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.models.job import JobDescription
from app.models.match_history import MatchHistory
from app.models.activity_log import ActivityLog
from app.utils.auth import get_current_active_user
from app.services.match_engine import match_engine_service
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Pydantic models
class MatchScoreRequest(BaseModel):
    resume_id: int
    job_id: int

class MatchScoreResponse(BaseModel):
    id: int
    resume_id: int
    job_id: int
    overall_match_score: float
    skills_match_score: float
    experience_match_score: float
    keywords_match_score: Optional[float]
    missing_keywords: List[str]
    matching_keywords: List[str]
    suggestions: List[str]
    breakdown: dict
    ai_confidence: float
    processing_status: str
    created_at: str

class MatchHistoryResponse(BaseModel):
    matches: List[MatchScoreResponse]
    total_count: int

@router.post("/calculate", response_model=MatchScoreResponse)
async def calculate_match_score(
    request: MatchScoreRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate match score between a resume and job description"""
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
        
        # Calculate match score
        match_result = await match_engine_service.calculate_comprehensive_match_score(
            resume_text=resume.extracted_text or "",
            job_text=job.job_text or "",
            resume_skills=resume.parsed_skills or [],
            resume_experience=resume.parsed_experience or [],
            job_skills=job.extracted_skills or [],
            job_requirements=job.experience_requirements or []
        )
        
        # Create match history record
        match_history = MatchHistory(
            user_id=current_user.id,
            resume_id=resume.id,
            job_id=job.id,
            match_score=match_result.get("overall_match_score", 0),
            missing_keywords=match_result.get("missing_keywords", []),
            matching_keywords=match_result.get("matching_keywords", []),
            experience_match_score=match_result.get("experience_match_score", 0),
            skills_match_score=match_result.get("skills_match_score", 0),
            keywords_match_score=match_result.get("keywords_match_score", 0),
            detailed_analysis=str(match_result.get("breakdown", {})),
            processing_status="completed"
        )
        
        db.add(match_history)
        db.commit()
        db.refresh(match_history)
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="match_score_calculation",
            description=f"Match score calculated: {match_result.get('overall_match_score', 0):.1f}% for {job.title}",
            meta_data={
                "resume_id": resume.id,
                "job_id": job.id,
                "match_score": match_result.get("overall_match_score", 0)
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Match score calculated: {match_result.get('overall_match_score', 0):.1f}% for user {current_user.id}")
        
        return MatchScoreResponse(
            id=match_history.id,
            resume_id=resume.id,
            job_id=job.id,
            overall_match_score=match_result.get("overall_match_score", 0),
            skills_match_score=match_result.get("skills_match_score", 0),
            experience_match_score=match_result.get("experience_match_score", 0),
            keywords_match_score=match_result.get("keywords_match_score"),
            missing_keywords=match_result.get("missing_keywords", []),
            matching_keywords=match_result.get("matching_keywords", []),
            suggestions=match_result.get("suggestions", []),
            breakdown=match_result.get("breakdown", {}),
            ai_confidence=match_result.get("ai_confidence", 0),
            processing_status=match_result.get("processing_status", "completed"),
            created_at=match_history.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Match score calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Match score calculation failed"
        )

@router.post("/batch-calculate")
async def batch_calculate_matches(
    resume_id: int,
    job_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate match scores for multiple jobs against one resume"""
    try:
        # Get resume
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == current_user.id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        if resume.processing_status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume is not fully processed yet"
            )
        
        # Get jobs
        jobs = db.query(JobDescription).filter(
            JobDescription.id.in_(job_ids),
            JobDescription.user_id == current_user.id
        ).all()
        
        if not jobs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No job descriptions found"
            )
        
        # Prepare job data for batch processing
        job_data = []
        for job in jobs:
            if job.processing_status == "completed":
                job_data.append({
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "job_text": job.job_text or "",
                    "required_skills": job.extracted_skills or [],
                    "experience_requirements": job.experience_requirements or []
                })
        
        # Calculate batch matches
        batch_results = await match_engine_service.batch_calculate_matches(
            resume.extracted_text or "",
            job_data
        )
        
        # Save results to database
        saved_matches = []
        for result in batch_results:
            if "error" not in result:
                match_history = MatchHistory(
                    user_id=current_user.id,
                    resume_id=resume.id,
                    job_id=result["job_id"],
                    match_score=result["match_score"],
                    missing_keywords=result["details"].get("missing_keywords", []),
                    matching_keywords=result["details"].get("matching_keywords", []),
                    experience_match_score=result["details"].get("experience_match_score", 0),
                    skills_match_score=result["details"].get("skills_match_score", 0),
                    keywords_match_score=result["details"].get("keywords_match_score", 0),
                    detailed_analysis=str(result["details"].get("breakdown", {})),
                    processing_status="completed"
                )
                db.add(match_history)
                saved_matches.append(match_history)
        
        db.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="batch_match_calculation",
            description=f"Batch match scores calculated for {len(job_data)} jobs",
            meta_data={
                "resume_id": resume.id,
                "job_count": len(job_data),
                "successful_matches": len(saved_matches)
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Batch match scores calculated for {len(job_data)} jobs for user {current_user.id}")
        
        return {
            "message": f"Batch match scores calculated for {len(job_data)} jobs",
            "results": batch_results,
            "saved_matches": len(saved_matches)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch match calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch match calculation failed"
        )

@router.get("/history", response_model=MatchHistoryResponse)
async def get_match_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get user's match history"""
    try:
        matches = db.query(MatchHistory).filter(
            MatchHistory.user_id == current_user.id
        ).order_by(MatchHistory.created_at.desc()).offset(offset).limit(limit).all()
        
        total_count = db.query(MatchHistory).filter(
            MatchHistory.user_id == current_user.id
        ).count()
        
        match_responses = []
        for match in matches:
            match_responses.append(MatchScoreResponse(
                id=match.id,
                resume_id=match.resume_id,
                job_id=match.job_id,
                overall_match_score=match.match_score,
                skills_match_score=match.skills_match_score or 0,
                experience_match_score=match.experience_match_score or 0,
                keywords_match_score=match.keywords_match_score,
                missing_keywords=match.missing_keywords or [],
                matching_keywords=match.matching_keywords or [],
                suggestions=[],  # Could be stored separately or regenerated
                breakdown={},  # Could be parsed from detailed_analysis
                ai_confidence=0,  # Could be calculated from stored data
                processing_status=match.processing_status,
                created_at=match.created_at.isoformat()
            ))
        
        return MatchHistoryResponse(
            matches=match_responses,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Failed to get match history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve match history"
        )

@router.get("/{match_id}", response_model=MatchScoreResponse)
async def get_match_details(
    match_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed match score information"""
    try:
        match = db.query(MatchHistory).filter(
            MatchHistory.id == match_id,
            MatchHistory.user_id == current_user.id
        ).first()
        
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match record not found"
            )
        
        return MatchScoreResponse(
            id=match.id,
            resume_id=match.resume_id,
            job_id=match.job_id,
            overall_match_score=match.match_score,
            skills_match_score=match.skills_match_score or 0,
            experience_match_score=match.experience_match_score or 0,
            keywords_match_score=match.keywords_match_score,
            missing_keywords=match.missing_keywords or [],
            matching_keywords=match.matching_keywords or [],
            suggestions=[],  # Could be stored separately
            breakdown={},  # Could be parsed from detailed_analysis
            ai_confidence=0,
            processing_status=match.processing_status,
            created_at=match.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get match details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve match details"
        )
