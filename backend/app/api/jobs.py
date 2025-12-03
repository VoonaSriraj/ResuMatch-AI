"""
Jobs API Endpoints
Production-ready FastAPI endpoints for job search using Adzuna API
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime

from app.services.adzuna_service import AdzunaJobService
from app.utils.logger import get_logger

# Initialize router and logger
router = APIRouter()
logger = get_logger(__name__)

# Pydantic models for request/response validation
class JobSearchRequest(BaseModel):
    """Request model for job search"""
    keywords: Optional[List[str]] = Field(None, description="List of search keywords")
    location: Optional[str] = Field(None, description="Location filter (e.g., Mumbai, Bangalore)")
    limit: int = Field(10, ge=1, le=50, description="Number of jobs to return (1-50)")

class JobResponse(BaseModel):
    """Response model for individual job"""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Job description")
    salary_range: Optional[str] = Field(None, description="Formatted salary range")
    salary_min: Optional[float] = Field(None, description="Minimum salary")
    salary_max: Optional[float] = Field(None, description="Maximum salary")
    apply_url: str = Field(..., description="URL to apply for the job")
    job_type: str = Field(..., description="Type of employment")
    posted_date: Optional[str] = Field(None, description="Job posting date")
    source: str = Field(..., description="Job source (adzuna)")
    job_id: str = Field(..., description="Unique job identifier")
    seniority_level: str = Field(..., description="Seniority level (entry, mid, senior)")
    remote_friendly: str = Field(..., description="Remote work option (remote, hybrid, on-site)")
    skills_required: List[str] = Field(..., description="Required technical skills")

class JobSearchResponse(BaseModel):
    """Response model for job search results"""
    jobs: List[JobResponse] = Field(..., description="List of job results")
    total_count: int = Field(..., description="Total number of jobs found")
    search_criteria: dict = Field(..., description="Search parameters used")
    timestamp: str = Field(..., description="Response timestamp")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: str = Field(..., description="Detailed error information")
    timestamp: str = Field(..., description="Error timestamp")

# Dependency to get Adzuna service instance
def get_adzuna_service() -> AdzunaJobService:
    """Dependency to provide Adzuna service instance"""
    return AdzunaJobService()

@router.get(
    "/jobs",
    response_model=JobSearchResponse,
    responses={
        200: {"description": "Successful job search"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Search Jobs",
    description="Search for real-time jobs using Adzuna API for India"
)
async def search_jobs(
    keywords: Optional[str] = Query(
        None, 
        description="Comma-separated keywords (e.g., 'Python,Software Engineer')",
        example="Python,Software Engineer"
    ),
    location: Optional[str] = Query(
        None, 
        description="Location filter (e.g., Mumbai, Bangalore, Delhi)",
        example="Mumbai"
    ),
    limit: int = Query(
        10, 
        ge=1, 
        le=50, 
        description="Number of jobs to return (1-50)",
        example=10
    ),
    adzuna_service: AdzunaJobService = Depends(get_adzuna_service)
):
    """
    Search for jobs using Adzuna API
    
    This endpoint searches for real-time jobs in India using the Adzuna API.
    It accepts search keywords and location filters to return relevant job opportunities.
    
    **Parameters:**
    - **keywords**: Comma-separated list of search terms
    - **location**: City or region in India to search
    - **limit**: Number of jobs to return (maximum 50)
    
    **Returns:**
    - List of job opportunities with detailed information
    - Each job includes title, company, location, salary, and application URL
    
    **Example Usage:**
    ```
    GET /jobs?keywords=Python,Software Engineer&location=Mumbai&limit=10
    ```
    """
    try:
        # Parse keywords if provided
        keyword_list = None
        if keywords:
            keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        
        logger.info(f"Job search request - Keywords: {keyword_list}, Location: {location}, Limit: {limit}")
        
        # Search for jobs using Adzuna service
        jobs = await adzuna_service.search_jobs(
            keywords=keyword_list,
            location=location,
            limit=limit
        )
        
        # Prepare response
        response_data = {
            "jobs": jobs,
            "total_count": len(jobs),
            "search_criteria": {
                "keywords": keyword_list,
                "location": location,
                "limit": limit
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Successfully returned {len(jobs)} jobs")
        return JobSearchResponse(**response_data)
        
    except ValueError as e:
        logger.error(f"Validation error in job search: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid request parameters",
                "detail": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error in job search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Job search failed",
                "detail": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post(
    "/jobs/search",
    response_model=JobSearchResponse,
    responses={
        200: {"description": "Successful job search"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Search Jobs (POST)",
    description="Search for jobs using POST request with JSON body"
)
async def search_jobs_post(
    request: JobSearchRequest,
    adzuna_service: AdzunaJobService = Depends(get_adzuna_service)
):
    """
    Search for jobs using POST request
    
    This endpoint provides the same functionality as the GET endpoint but accepts
    search parameters in the request body. Useful for complex search criteria.
    
    **Request Body:**
    ```json
    {
        "keywords": ["Python", "Software Engineer"],
        "location": "Mumbai",
        "limit": 10
    }
    ```
    """
    try:
        logger.info(f"POST job search request - {request.dict()}")
        
        # Search for jobs using Adzuna service
        jobs = await adzuna_service.search_jobs(
            keywords=request.keywords,
            location=request.location,
            limit=request.limit
        )
        
        # Prepare response
        response_data = {
            "jobs": jobs,
            "total_count": len(jobs),
            "search_criteria": {
                "keywords": request.keywords,
                "location": request.location,
                "limit": request.limit
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Successfully returned {len(jobs)} jobs via POST")
        return JobSearchResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error in POST job search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Job search failed",
                "detail": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    responses={
        200: {"description": "Job details found"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get Job Details",
    description="Get detailed information about a specific job by ID"
)
async def get_job_details(
    job_id: str,
    adzuna_service: AdzunaJobService = Depends(get_adzuna_service)
):
    """
    Get detailed information about a specific job
    
    **Parameters:**
    - **job_id**: Adzuna job identifier
    
    **Returns:**
    - Detailed job information including full description and requirements
    """
    try:
        logger.info(f"Fetching job details for ID: {job_id}")
        
        job = await adzuna_service.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "detail": f"No job found with ID: {job_id}",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        logger.info(f"Successfully fetched job details for ID: {job_id}")
        return JobResponse(**job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job details for ID {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to fetch job details",
                "detail": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get(
    "/jobs/health",
    response_model=dict,
    summary="Health Check",
    description="Check if the jobs API is healthy and Adzuna service is accessible"
)
async def health_check():
    """
    Health check endpoint for the jobs API
    
    **Returns:**
    - API health status and configuration information
    """
    try:
        # Test Adzuna service connectivity
        adzuna_service = AdzunaJobService()
        
        # Make a simple test request
        test_jobs = await adzuna_service.search_jobs(
            keywords=["test"],
            location="India",
            limit=1
        )
        
        return {
            "status": "healthy",
            "service": "jobs-api",
            "adzuna_api": "accessible",
            "timestamp": datetime.now().isoformat(),
            "test_results": len(test_jobs)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "jobs-api",
            "adzuna_api": "inaccessible",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
