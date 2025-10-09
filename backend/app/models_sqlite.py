"""
SQLite-compatible models (without ARRAY types)
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

# User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    linkedin_id = Column(String(255), unique=True, nullable=True)
    linkedin_access_token = Column(Text, nullable=True)
    subscription_plan = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    profile_picture = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Resume model
class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    parsed_skills = Column(Text, nullable=True)  # JSON string instead of ARRAY
    parsed_experience = Column(Text, nullable=True)  # JSON string instead of ARRAY
    parsed_education = Column(Text, nullable=True)  # JSON string instead of ARRAY
    parsed_certifications = Column(Text, nullable=True)  # JSON string instead of ARRAY
    parsed_achievements = Column(Text, nullable=True)  # JSON string instead of ARRAY
    raw_ai_response = Column(Text, nullable=True)
    processing_status = Column(String(50), default="pending")
    upload_date = Column(DateTime(timezone=True), server_default=func.now())

# Job Description model
class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    job_text = Column(Text, nullable=False)
    source_link = Column(String(500), nullable=True)
    source_type = Column(String(50), default="upload")
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)
    
    # Parsed data from AI (JSON strings instead of ARRAYS)
    extracted_skills = Column(Text, nullable=True)
    experience_requirements = Column(Text, nullable=True)
    education_requirements = Column(Text, nullable=True)
    required_certifications = Column(Text, nullable=True)
    salary_range = Column(String(100), nullable=True)
    job_type = Column(String(50), nullable=True)
    seniority_level = Column(String(50), nullable=True)
    remote_friendly = Column(String(20), nullable=True)
    raw_ai_response = Column(Text, nullable=True)
    processing_status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Recommended Job model
class RecommendedJob(Base):
    __tablename__ = "recommended_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    linkedin_job_id = Column(String(255), nullable=True)
    external_job_id = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    match_score = Column(Float, nullable=True)
    apply_link = Column(String(500), nullable=True)
    source = Column(String(50), default="linkedin")
    salary_info = Column(String(255), nullable=True)
    job_type = Column(String(50), nullable=True)
    seniority_level = Column(String(50), nullable=True)
    remote_friendly = Column(String(20), nullable=True)
    posted_date = Column(DateTime(timezone=True), nullable=True)
    application_deadline = Column(DateTime(timezone=True), nullable=True)
    is_applied = Column(String(20), default="no")
    notes = Column(Text, nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

# Match History model
class MatchHistory(Base):
    __tablename__ = "match_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    
    # Matching results
    match_score = Column(Float, nullable=False)
    missing_keywords = Column(Text, nullable=True)  # JSON string
    matching_keywords = Column(Text, nullable=True)  # JSON string
    missing_skills = Column(Text, nullable=True)  # JSON string
    matching_skills = Column(Text, nullable=True)  # JSON string
    
    # AI-generated optimized resume
    optimized_resume_text = Column(Text, nullable=True)
    optimization_suggestions = Column(Text, nullable=True)  # JSON string
    improvement_areas = Column(Text, nullable=True)  # JSON string
    
    # Detailed analysis
    experience_match_score = Column(Float, nullable=True)
    skills_match_score = Column(Float, nullable=True)
    education_match_score = Column(Float, nullable=True)
    keywords_match_score = Column(Float, nullable=True)
    
    # AI analysis details
    detailed_analysis = Column(Text, nullable=True)
    raw_ai_response = Column(Text, nullable=True)
    
    # Status and metadata
    processing_status = Column(String(50), default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Subscription model
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_type = Column(String(50), nullable=False)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_price_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Activity Log model
class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    meta_data = Column(Text, nullable=True)  # JSON string instead of JSON
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
