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
from app.config import settings
import json

router = APIRouter()
logger = get_logger(__name__)

# Helper function to parse JSON strings back to lists
def parse_json_field(value):
    """Parse a DB field that may be a JSON string or a list, and coerce items to strings.
    This ensures downstream set/list operations don't fail on unhashable types like dicts.
    """
    def _to_string_list(items):
        out = []
        for item in items:
            s = "" if item is None else str(item).strip()
            if s:
                out.append(s)
        return out

    if value is None:
        return []

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return _to_string_list(parsed)
            # Single parsed value -> list of one string
            return _to_string_list([parsed])
        except (json.JSONDecodeError, TypeError):
            # Not JSON; split conservatively on commas first, then spaces
            raw = value.strip()
            if not raw:
                return []
            if "," in raw:
                parts = [p.strip() for p in raw.split(",") if p.strip()]
                return _to_string_list(parts)
            parts = [p.strip() for p in raw.split() if p.strip()]
            return _to_string_list(parts)

    if isinstance(value, list):
        return _to_string_list(value)

    # Any other type -> coerce to single string
    return _to_string_list([value])

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
    ats_findings: Optional[List[str]] = None
    readability: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
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
        
        # Validate that we have text content
        resume_text = resume.extracted_text or ""
        job_text = job.job_text or ""
        
        if not resume_text.strip():
            logger.warning(f"Resume {resume.id} has empty extracted_text")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume text is empty. Please re-upload the resume."
            )
        
        if not job_text.strip():
            logger.warning(f"Job {job.id} has empty job_text")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description text is empty. Please re-upload the job description."
            )
        
        logger.info(f"Calculating match score for resume {resume.id} and job {job.id}. Resume text length: {len(resume_text)}, Job text length: {len(job_text)}")
        
        # Calculate match score
        match_result = await match_engine_service.calculate_comprehensive_match_score(
            resume_text=resume_text,
            job_text=job_text,
            resume_skills=parse_json_field(resume.parsed_skills),
            resume_experience=parse_json_field(resume.parsed_experience),
            job_skills=parse_json_field(job.extracted_skills),
            job_requirements=parse_json_field(job.experience_requirements)
        )
        
        logger.info(f"Match calculation completed. Overall score: {match_result.get('overall_match_score', 0)}, Skills: {match_result.get('skills_match_score', 0)}, Experience: {match_result.get('experience_match_score', 0)}")
        
        # Helper function to serialize lists for SQLite
        def serialize_for_sqlite(value):
            if isinstance(value, list):
                return json.dumps(value, ensure_ascii=False)
            return value
        
        # Create match history record
        match_history = MatchHistory(
            user_id=current_user.id,
            resume_id=resume.id,
            job_id=job.id,
            match_score=match_result.get("overall_match_score", 0),
            missing_keywords=serialize_for_sqlite(match_result.get("missing_keywords", [])),
            matching_keywords=serialize_for_sqlite(match_result.get("matching_keywords", [])),
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
            ats_findings=match_result.get("ats_findings"),
            readability=match_result.get("readability"),
            strengths=match_result.get("strengths"),
            breakdown=match_result.get("breakdown", {}),
            ai_confidence=match_result.get("ai_confidence", 0),
            processing_status=match_result.get("processing_status", "completed"),
            created_at=match_history.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Match score calculation failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(f"Match score calculation failed: {str(e)}" if settings.debug else "Match score calculation failed")
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
                    "required_skills": parse_json_field(job.extracted_skills),
                    "experience_requirements": parse_json_field(job.experience_requirements)
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
                    missing_keywords=serialize_for_sqlite(result["details"].get("missing_keywords", [])),
                    matching_keywords=serialize_for_sqlite(result["details"].get("matching_keywords", [])),
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
                missing_keywords=parse_json_field(match.missing_keywords),
                matching_keywords=parse_json_field(match.matching_keywords),
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
            missing_keywords=parse_json_field(match.missing_keywords),
            matching_keywords=parse_json_field(match.matching_keywords),
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
