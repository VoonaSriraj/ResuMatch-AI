"""
Job description upload and parsing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import os

from app.database import get_db
from app.models.user import User
from app.models.job import JobDescription
from app.models.activity_log import ActivityLog
from app.utils.auth import get_current_active_user
from app.services.job_analyzer import job_analyzer_service
from app.utils.logger import get_logger
from app.config import settings
import json

router = APIRouter()
logger = get_logger(__name__)

# Pydantic models
class JobResponse(BaseModel):
    id: int
    title: str
    company: Optional[str]
    location: Optional[str]
    source_link: Optional[str]
    source_type: str
    processing_status: str
    created_at: str
    extracted_skills: Optional[List[str]]
    experience_requirements: Optional[List[str]]
    education_requirements: Optional[List[str]]
    required_certifications: Optional[List[str]]
    salary_range: Optional[str]
    job_type: Optional[str]
    seniority_level: Optional[str]
    remote_friendly: Optional[str]

class JobUploadResponse(BaseModel):
    message: str
    job: JobResponse

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total_count: int

@router.post("/upload", response_model=JobUploadResponse)
async def upload_job_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and parse a job description file"""
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        file_extension = file.filename.lower().split('.')[-1]
        if f".{file_extension}" not in settings.allowed_file_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed types: {settings.allowed_file_types}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {settings.max_file_size / (1024*1024):.1f}MB limit"
            )
        
        try:
            # Process the file FIRST to get job_text and metadata
            processing_result = await job_analyzer_service.process_job_file(
                file_content, file.filename, current_user.id, title, company, location
            )

            # Create job description record only after we have job_text (NOT NULL)
            job = JobDescription(
                user_id=current_user.id,
                title=processing_result.get("title", title or "Job Title Not Specified"),
                company=processing_result.get("company", company),
                location=processing_result.get("location", location),
                job_text=processing_result.get("job_text"),
                source_type="upload",
                file_path=processing_result.get("file_path"),
                file_type=processing_result.get("file_type"),
                processing_status="completed"
            )

            # Extract parsed data (coerce to arrays of strings for PostgreSQL ARRAY columns)
            parsed_data = processing_result.get("parsed_data", {})

            def to_string_list(value):
                if value is None:
                    return []
                result = []
                for item in (value if isinstance(value, list) else [value]):
                    if isinstance(item, (str, int, float)):
                        result.append(str(item))
                    else:
                        # For dicts/objects, store JSON string
                        try:
                            result.append(json.dumps(item, ensure_ascii=False))
                        except Exception:
                            result.append(str(item))
                return result

            job.extracted_skills = to_string_list(parsed_data.get("required_skills"))
            job.experience_requirements = to_string_list(parsed_data.get("experience_requirements"))
            job.education_requirements = to_string_list(parsed_data.get("education_requirements"))
            job.required_certifications = to_string_list(parsed_data.get("certifications"))

            # Extract job details
            job_details = parsed_data.get("job_details", {})
            job.salary_range = job_details.get("salary_range")
            job.job_type = job_details.get("job_type")
            job.seniority_level = job_details.get("seniority_level")
            job.remote_friendly = job_details.get("remote_friendly")

            db.add(job)
            db.commit()
            db.refresh(job)
            
            # Log activity
            activity = ActivityLog(
                user_id=current_user.id,
                action_type="job_upload",
                description=f"Job description uploaded and parsed: {job.title} at {job.company}",
                meta_data={"job_id": job.id, "file_type": file_extension}
            )
            db.add(activity)
            db.commit()
            
            logger.info(f"Job description uploaded and parsed successfully: {job.title} for user {current_user.id}")
            
            return JobUploadResponse(
                message="Job description uploaded and parsed successfully",
                job=JobResponse(
                    id=job.id,
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    source_link=job.source_link,
                    source_type=job.source_type,
                    processing_status=job.processing_status,
                    created_at=job.created_at.isoformat(),
                    extracted_skills=job.extracted_skills,
                    experience_requirements=job.experience_requirements,
                    education_requirements=job.education_requirements,
                    required_certifications=job.required_certifications,
                    salary_range=job.salary_range,
                    job_type=job.job_type,
                    seniority_level=job.seniority_level,
                    remote_friendly=job.remote_friendly
                )
            )
            
        except Exception as e:
            # Roll back any partial transaction
            try:
                db.rollback()
            except Exception:
                pass
            logger.error(f"Job processing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Job upload failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job upload failed"
        )

@router.post("/upload-text", response_model=JobUploadResponse)
async def upload_job_text(
    job_text: str = Form(...),
    title: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    source_link: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and parse job description text directly"""
    try:
        if not job_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job text cannot be empty"
            )

        # Process the text first
        processing_result = await job_analyzer_service.process_job_text(
            job_text, title, company, location, source_link
        )

        # Create job description record with parsed content
        job = JobDescription(
            user_id=current_user.id,
            title=processing_result.get("title", title or "Job Title Not Specified"),
            company=processing_result.get("company", company),
            location=processing_result.get("location", location),
            source_link=processing_result.get("source_link", source_link),
            source_type="text_upload",
            job_text=processing_result.get("job_text"),
            processing_status="completed"
        )

        # Coerce parsed arrays to string lists
        def to_string_list(value):
            if value is None:
                return []
            out = []
            for item in (value if isinstance(value, list) else [value]):
                if isinstance(item, (str, int, float)):
                    out.append(str(item))
                else:
                    try:
                        out.append(json.dumps(item, ensure_ascii=False))
                    except Exception:
                        out.append(str(item))
            return out

        parsed_data = processing_result.get("parsed_data", {})
        job.extracted_skills = to_string_list(parsed_data.get("required_skills"))
        job.experience_requirements = to_string_list(parsed_data.get("experience_requirements"))
        job.education_requirements = to_string_list(parsed_data.get("education_requirements"))
        job.required_certifications = to_string_list(parsed_data.get("certifications"))

        job_details = parsed_data.get("job_details", {})
        job.salary_range = job_details.get("salary_range")
        job.job_type = job_details.get("job_type")
        job.seniority_level = job_details.get("seniority_level")
        job.remote_friendly = job_details.get("remote_friendly")

        db.add(job)
        db.commit()
        db.refresh(job)

        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="job_text_upload",
            description=f"Job description text uploaded and parsed: {job.title} at {job.company}",
            meta_data={"job_id": job.id}
        )
        db.add(activity)
        db.commit()

        logger.info(f"Job description text uploaded and parsed successfully: {job.title} for user {current_user.id}")

        return JobUploadResponse(
            message="Job description text uploaded and parsed successfully",
            job=JobResponse(
                id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                source_link=job.source_link,
                source_type=job.source_type,
                processing_status=job.processing_status,
                created_at=job.created_at.isoformat(),
                extracted_skills=job.extracted_skills,
                experience_requirements=job.experience_requirements,
                education_requirements=job.education_requirements,
                required_certifications=job.required_certifications,
                salary_range=job.salary_range,
                job_type=job.job_type,
                seniority_level=job.seniority_level,
                remote_friendly=job.remote_friendly
            )
        )

    except HTTPException:
        # Let HTTP errors pass through
        raise
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.error(f"Job text upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job text upload failed"
        )

@router.get("/list", response_model=JobListResponse)
async def list_jobs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of user's job descriptions"""
    try:
        jobs = db.query(JobDescription).filter(
            JobDescription.user_id == current_user.id
        ).order_by(JobDescription.created_at.desc()).all()
        
        job_responses = [
            JobResponse(
                id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                source_link=job.source_link,
                source_type=job.source_type,
                processing_status=job.processing_status,
                created_at=job.created_at.isoformat(),
                extracted_skills=job.extracted_skills,
                experience_requirements=job.experience_requirements,
                education_requirements=job.education_requirements,
                required_certifications=job.required_certifications,
                salary_range=job.salary_range,
                job_type=job.job_type,
                seniority_level=job.seniority_level,
                remote_friendly=job.remote_friendly
            )
            for job in jobs
        ]
        
        return JobListResponse(
            jobs=job_responses,
            total_count=len(job_responses)
        )
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job descriptions"
        )

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific job description by ID"""
    try:
        job = db.query(JobDescription).filter(
            JobDescription.id == job_id,
            JobDescription.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        
        return JobResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            source_link=job.source_link,
            source_type=job.source_type,
            processing_status=job.processing_status,
            created_at=job.created_at.isoformat(),
            extracted_skills=job.extracted_skills,
            experience_requirements=job.experience_requirements,
            education_requirements=job.education_requirements,
            required_certifications=job.required_certifications,
            salary_range=job.salary_range,
            job_type=job.job_type,
            seniority_level=job.seniority_level,
            remote_friendly=job.remote_friendly
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job description"
        )

@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a job description"""
    try:
        job = db.query(JobDescription).filter(
            JobDescription.id == job_id,
            JobDescription.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        
        # Delete file if it exists
        if job.file_path and os.path.exists(job.file_path):
            os.remove(job.file_path)
        
        # Delete from database
        db.delete(job)
        db.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="job_deletion",
            description=f"Job description deleted: {job.title} at {job.company}",
            meta_data={"job_id": job_id}
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Job description deleted: {job.title} for user {current_user.id}")
        
        return {"message": "Job description deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job description"
        )
