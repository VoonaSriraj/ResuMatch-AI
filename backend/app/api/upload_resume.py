"""
Resume upload and parsing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import os

from app.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.models.activity_log import ActivityLog
from app.utils.auth import get_current_active_user
from app.services.resume_parser import resume_parser_service
from app.utils.logger import get_logger
from app.config import settings
import json as _json

router = APIRouter()
logger = get_logger(__name__)

# Pydantic models
class ResumeResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: Optional[int]
    processing_status: str
    upload_date: str
    parsed_skills: Optional[List[str]]
    parsed_experience: Optional[List[str]]
    parsed_education: Optional[List[str]]
    parsed_certifications: Optional[List[str]]
    parsed_achievements: Optional[List[str]]

class ResumeUploadResponse(BaseModel):
    message: str
    resume: ResumeResponse

class ResumeListResponse(BaseModel):
    resumes: List[ResumeResponse]
    total_count: int

# Helper function to parse JSON strings back to lists
def parse_json_field(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return _json.loads(value)
        except (_json.JSONDecodeError, TypeError):
            return []
    return value

# Helper function to create ResumeResponse with proper JSON parsing
def create_resume_response(resume: Resume) -> ResumeResponse:
    return ResumeResponse(
        id=resume.id,
        filename=resume.filename,
        file_type=resume.file_type,
        file_size=resume.file_size,
        processing_status=resume.processing_status,
        upload_date=resume.upload_date.isoformat(),
        parsed_skills=parse_json_field(resume.parsed_skills),
        parsed_experience=parse_json_field(resume.parsed_experience),
        parsed_education=parse_json_field(resume.parsed_education),
        parsed_certifications=parse_json_field(resume.parsed_certifications),
        parsed_achievements=parse_json_field(resume.parsed_achievements)
    )

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and parse a resume file"""
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
        
        # Create resume record
        resume = Resume(
            user_id=current_user.id,
            filename=file.filename,
            file_type=f".{file_extension}",
            file_size=len(file_content),
            processing_status="processing"
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        try:
            # Process the file
            processing_result = await resume_parser_service.process_resume_file(
                file_content, file.filename, current_user.id
            )
            
            # Update resume with parsed data
            resume.file_path = processing_result.get("file_path")
            resume.extracted_text = processing_result.get("extracted_text")
            resume.processing_status = "completed"
            
            # Extract parsed data and coerce to arrays of strings for PostgreSQL ARRAY columns
            parsed_data = processing_result.get("parsed_data", {})

            import json as _json
            def _to_string_list(value):
                if value is None:
                    return []
                out = []
                for item in (value if isinstance(value, list) else [value]):
                    if isinstance(item, (str, int, float)):
                        out.append(str(item))
                    else:
                        try:
                            out.append(_json.dumps(item, ensure_ascii=False))
                        except Exception:
                            out.append(str(item))
                return out

            # Ensure data is properly serialized for SQLite
            def ensure_json_string(value):
                if value is None:
                    return None
                if isinstance(value, str):
                    return value  # Already serialized
                elif isinstance(value, list):
                    return _json.dumps(value, ensure_ascii=False)
                else:
                    return _json.dumps([str(value)], ensure_ascii=False)
            
            resume.parsed_skills = ensure_json_string(parsed_data.get("skills"))
            resume.parsed_experience = ensure_json_string(parsed_data.get("experience"))
            resume.parsed_education = ensure_json_string(parsed_data.get("education"))
            resume.parsed_certifications = ensure_json_string(parsed_data.get("certifications"))
            resume.parsed_achievements = ensure_json_string(parsed_data.get("achievements"))
            
            db.commit()
            db.refresh(resume)
            
            # Log activity
            activity = ActivityLog(
                user_id=current_user.id,
                action_type="resume_upload",
                description=f"Resume uploaded and parsed: {file.filename}",
                meta_data={"resume_id": resume.id, "file_type": file_extension}
            )
            db.add(activity)
            db.commit()
            
            logger.info(f"Resume uploaded and parsed successfully: {file.filename} for user {current_user.id}")
            
            return ResumeUploadResponse(
                message="Resume uploaded and parsed successfully",
                resume=create_resume_response(resume)
            )
            
        except Exception as e:
            # Update resume status to failed, rolling back if needed
            try:
                db.rollback()
            except Exception:
                pass
            resume.processing_status = "failed"
            try:
                db.commit()
            except Exception:
                pass
            logger.error(f"Resume processing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process resume: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume upload failed"
        )

@router.post("/upload-text", response_model=ResumeUploadResponse)
async def upload_resume_text(
    resume_text: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and parse resume text directly"""
    try:
        if not resume_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume text cannot be empty"
            )
        
        # Create resume record
        resume = Resume(
            user_id=current_user.id,
            filename="text_resume.txt",
            file_type=".txt",
            processing_status="processing"
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        try:
            # Process the text
            processing_result = await resume_parser_service.process_resume_text(resume_text)
            
            # Update resume with parsed data
            resume.extracted_text = processing_result.get("extracted_text")
            resume.processing_status = "completed"
            
            # Extract parsed data and ensure proper serialization for SQLite
            parsed_data = processing_result.get("parsed_data", {})
            
            def ensure_json_string(value):
                if value is None:
                    return None
                if isinstance(value, str):
                    return value  # Already serialized
                elif isinstance(value, list):
                    return _json.dumps(value, ensure_ascii=False)
                else:
                    return _json.dumps([str(value)], ensure_ascii=False)
            
            resume.parsed_skills = ensure_json_string(parsed_data.get("skills"))
            resume.parsed_experience = ensure_json_string(parsed_data.get("experience"))
            resume.parsed_education = ensure_json_string(parsed_data.get("education"))
            resume.parsed_certifications = ensure_json_string(parsed_data.get("certifications"))
            resume.parsed_achievements = ensure_json_string(parsed_data.get("achievements"))
            
            db.commit()
            db.refresh(resume)
            
            # Log activity
            activity = ActivityLog(
                user_id=current_user.id,
                action_type="resume_text_upload",
                description="Resume text uploaded and parsed",
                meta_data={"resume_id": resume.id}
            )
            db.add(activity)
            db.commit()
            
            logger.info(f"Resume text uploaded and parsed successfully for user {current_user.id}")
            
            return ResumeUploadResponse(
                message="Resume text uploaded and parsed successfully",
                resume=create_resume_response(resume)
            )
            
        except Exception as e:
            # Update resume status to failed
            resume.processing_status = "failed"
            db.commit()
            
            logger.error(f"Resume text processing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process resume text: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume text upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume text upload failed"
        )

@router.get("/list", response_model=ResumeListResponse)
async def list_resumes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of user's resumes"""
    try:
        resumes = db.query(Resume).filter(
            Resume.user_id == current_user.id
        ).order_by(Resume.upload_date.desc()).all()
        
        resume_responses = [
            create_resume_response(resume)
            for resume in resumes
        ]
        
        return ResumeListResponse(
            resumes=resume_responses,
            total_count=len(resume_responses)
        )
        
    except Exception as e:
        logger.error(f"Failed to list resumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resumes"
        )

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific resume by ID"""
    try:
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == current_user.id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        return create_resume_response(resume)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume"
        )

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a resume"""
    try:
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == current_user.id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Delete file if it exists
        if resume.file_path and os.path.exists(resume.file_path):
            os.remove(resume.file_path)
        
        # Delete from database
        db.delete(resume)
        db.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="resume_deletion",
            description=f"Resume deleted: {resume.filename}",
            meta_data={"resume_id": resume_id}
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Resume deleted: {resume.filename} for user {current_user.id}")
        
        return {"message": "Resume deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume"
        )
