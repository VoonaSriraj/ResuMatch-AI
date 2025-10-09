from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.job import RecommendedJob
import requests, os

router = APIRouter()

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
LINKEDIN_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI")

@router.get("/login")
def linkedin_login():
    url = (
        "https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code&client_id={LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={LINKEDIN_REDIRECT_URI}"
        "&scope=r_liteprofile%20r_emailaddress%20r_jobs_search"
    )
    return {"auth_url": url}

@router.get("/callback")
def linkedin_callback(code: str, db: Session = Depends(get_db), request: Request = None):
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="LinkedIn token exchange failed")
    access_token = response.json().get("access_token")
    # Store token for the user (assume user is authenticated and user_id is available)
    user_id = request.query_params.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.linkedin_access_token = access_token
        db.commit()
    return {"access_token": access_token}

@router.post("/fetch_jobs")
def fetch_linkedin_jobs(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.linkedin_access_token:
        raise HTTPException(status_code=401, detail="LinkedIn not connected")
    headers = {"Authorization": f"Bearer {user.linkedin_access_token}"}
    jobs_url = "https://api.linkedin.com/v2/jobSearch"  # Example endpoint, adjust as needed
    response = requests.get(jobs_url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch jobs from LinkedIn")
    jobs = response.json().get("elements", [])
    # For each job, analyze with Groq and store in RecommendedJob
    for job in jobs:
        # Extract job info
        title = job.get("title", "")
        company = job.get("companyName", "")
        location = job.get("location", "")
        description = job.get("description", "")
        linkedin_job_id = job.get("id", "")
        apply_link = job.get("applyUrl", "")
        # Call Groq AI for analysis (pseudo-code)
        groq_result = analyze_with_groq(description)  # Implement this function
        recommended = RecommendedJob(
            user_id=user.id,
            linkedin_job_id=linkedin_job_id,
            title=title,
            company=company,
            location=location,
            description=description,
            match_score=groq_result["match_score"],
            apply_link=apply_link,
            source="linkedin",
            notes=groq_result["short_reason"]
        )
        db.add(recommended)
    db.commit()
    return {"message": "Jobs fetched and analyzed"}