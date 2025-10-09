"""
AI Interview preparation endpoints for generating questions and tips
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.job import JobDescription
from app.models.activity_log import ActivityLog
from app.utils.auth import get_current_active_user
from app.services.interview_engine import interview_engine_service
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Pydantic models
class InterviewQuestionsRequest(BaseModel):
    job_id: Optional[int] = None
    job_text: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    seniority_level: Optional[str] = None

class InterviewQuestionsResponse(BaseModel):
    technical_questions: List[str]
    behavioral_questions: List[str]
    company_culture_questions: List[str]
    leadership_questions: List[str]
    industry_questions: List[str]
    preparation_tips: List[str]
    ai_tips: List[str]
    job_context: dict
    processing_status: str

class FollowUpQuestionsRequest(BaseModel):
    question: str
    job_context: dict

class AnswerSuggestionRequest(BaseModel):
    question: str
    user_experience: str
    job_context: dict

@router.post("/generate", response_model=InterviewQuestionsResponse)
async def generate_interview_questions(
    request: InterviewQuestionsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate interview questions based on job description"""
    try:
        job_text = request.job_text
        job_title = request.job_title
        company = request.company
        seniority_level = request.seniority_level
        
        # If job_id is provided, get job details from database
        if request.job_id:
            job = db.query(JobDescription).filter(
                JobDescription.id == request.job_id,
                JobDescription.user_id == current_user.id
            ).first()
            
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job description not found"
                )
            
            if job.processing_status != "completed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Job description is not fully processed yet"
                )
            
            # Use job data if not provided in request
            if not job_text:
                job_text = job.job_text
            if not job_title:
                job_title = job.title
            if not company:
                company = job.company
            if not seniority_level:
                seniority_level = job.seniority_level
        
        if not job_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description text is required"
            )
        
        # Generate interview questions
        questions_result = await interview_engine_service.generate_interview_questions(
            job_text=job_text,
            job_title=job_title,
            company=company,
            seniority_level=seniority_level
        )
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="interview_questions_generation",
            description=f"Interview questions generated for {job_title or 'job'} at {company or 'company'}",
            meta_data={
                "job_id": request.job_id,
                "job_title": job_title,
                "company": company,
                "questions_count": len(questions_result.get("technical_questions", [])) + 
                                 len(questions_result.get("behavioral_questions", [])) +
                                 len(questions_result.get("company_culture_questions", [])) +
                                 len(questions_result.get("leadership_questions", []))
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Interview questions generated for user {current_user.id}")
        
        return InterviewQuestionsResponse(
            technical_questions=questions_result.get("technical_questions", []),
            behavioral_questions=questions_result.get("behavioral_questions", []),
            company_culture_questions=questions_result.get("company_culture_questions", []),
            leadership_questions=questions_result.get("leadership_questions", []),
            industry_questions=questions_result.get("industry_questions", []),
            preparation_tips=questions_result.get("preparation_tips", []),
            ai_tips=questions_result.get("ai_tips", []),
            job_context=questions_result.get("job_context", {}),
            processing_status=questions_result.get("processing_status", "completed")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interview questions generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate interview questions"
        )

@router.post("/follow-up")
async def generate_follow_up_questions(
    request: FollowUpQuestionsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate follow-up questions for a specific interview question"""
    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        # Generate follow-up questions
        follow_up_result = await interview_engine_service.generate_follow_up_questions(
            question=request.question,
            job_context=request.job_context
        )
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="follow_up_questions_generation",
            description=f"Follow-up questions generated for: {request.question[:50]}...",
            meta_data={
                "original_question": request.question,
                "follow_up_count": len(follow_up_result.get("follow_up_questions", []))
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Follow-up questions generated for user {current_user.id}")
        
        return {
            "message": "Follow-up questions generated successfully",
            "result": follow_up_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Follow-up questions generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate follow-up questions"
        )

@router.post("/answer-suggestions")
async def generate_answer_suggestions(
    request: AnswerSuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate answer suggestions for interview questions"""
    try:
        if not request.question.strip() or not request.user_experience.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question and user experience are required"
            )
        
        # Generate answer suggestions
        answer_result = await interview_engine_service.generate_answer_suggestions(
            question=request.question,
            user_experience=request.user_experience,
            job_context=request.job_context
        )
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action_type="answer_suggestions_generation",
            description=f"Answer suggestions generated for: {request.question[:50]}...",
            meta_data={
                "question": request.question,
                "has_structure": bool(answer_result.get("answer_structure")),
                "key_points_count": len(answer_result.get("key_points", []))
            }
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"Answer suggestions generated for user {current_user.id}")
        
        return {
            "message": "Answer suggestions generated successfully",
            "result": answer_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Answer suggestions generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer suggestions"
        )

@router.get("/categories/{job_id}")
async def get_question_categories(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get available interview question categories for a job"""
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
        
        # Generate questions to get categories
        questions_result = await interview_engine_service.generate_interview_questions(
            job_text=job.job_text or "",
            job_title=job.title,
            company=job.company,
            seniority_level=job.seniority_level
        )
        
        # Organize categories
        categories = {
            "technical": {
                "title": "Technical Questions",
                "description": "Questions about technical skills, tools, and methodologies",
                "count": len(questions_result.get("technical_questions", [])),
                "questions": questions_result.get("technical_questions", [])[:5]  # Show first 5
            },
            "behavioral": {
                "title": "Behavioral Questions",
                "description": "Questions about past experiences and situations",
                "count": len(questions_result.get("behavioral_questions", [])),
                "questions": questions_result.get("behavioral_questions", [])[:5]
            },
            "company_culture": {
                "title": "Company & Culture Questions",
                "description": "Questions about the company, culture, and fit",
                "count": len(questions_result.get("company_culture_questions", [])),
                "questions": questions_result.get("company_culture_questions", [])[:5]
            },
            "leadership": {
                "title": "Leadership Questions",
                "description": "Questions about leadership, management, and team skills",
                "count": len(questions_result.get("leadership_questions", [])),
                "questions": questions_result.get("leadership_questions", [])[:5]
            },
            "industry": {
                "title": "Industry Questions",
                "description": "Questions specific to the industry and domain",
                "count": len(questions_result.get("industry_questions", [])),
                "questions": questions_result.get("industry_questions", [])[:5]
            }
        }
        
        return {
            "message": "Question categories retrieved successfully",
            "job_title": job.title,
            "company": job.company,
            "categories": categories,
            "preparation_tips": questions_result.get("preparation_tips", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get question categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve question categories"
        )
