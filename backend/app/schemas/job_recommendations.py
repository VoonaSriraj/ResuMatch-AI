from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class JobRecommendationRequest(BaseModel):
    keywords: Optional[List[str]] = []
    location: Optional[str] = None
    limit: int = 10

class JobRecommendationResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    description: str
    linkedin_url: Optional[str]
    match_score: float
    posted_at: datetime
    job_type: Optional[str]
    seniority_level: Optional[str]
    salary_range: Optional[str]
    remote_friendly: Optional[str]
    skills_required: List[str]

class JobSearchResponse(BaseModel):
    jobs: List[JobRecommendationResponse]
    total: int
    page: int
    limit: int
