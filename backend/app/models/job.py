"""
Job description model for storing job postings and parsed requirements
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    job_text = Column(Text, nullable=False)
    source_link = Column(String(500), nullable=True)
    source_type = Column(String(50), default="upload")  # upload, linkedin, indeed, etc.
    file_path = Column(String(500), nullable=True)  # If uploaded as file
    file_type = Column(String(50), nullable=True)  # pdf, docx, doc, txt
    
    # Parsed data from AI
    extracted_skills = Column(Text, nullable=True)  # JSON string
    experience_requirements = Column(Text, nullable=True)  # JSON string
    education_requirements = Column(Text, nullable=True)  # JSON string
    required_certifications = Column(Text, nullable=True)  # JSON string
    salary_range = Column(String(100), nullable=True)
    job_type = Column(String(50), nullable=True)  # full-time, part-time, contract, etc.
    seniority_level = Column(String(50), nullable=True)  # entry, mid, senior, executive
    remote_friendly = Column(String(20), nullable=True)  # yes, no, hybrid
    raw_ai_response = Column(Text, nullable=True)
    processing_status = Column(String(50), default="pending")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="job_descriptions")
    match_history = relationship("MatchHistory", back_populates="job_description", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<JobDescription(id={self.id}, title='{self.title}', company='{self.company}')>"

class RecommendedJob(Base):
    __tablename__ = "recommended_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    linkedin_job_id = Column(String(255), nullable=True)
    external_job_id = Column(String(255), nullable=True)  # For other job boards
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    match_score = Column(Float, nullable=True)
    apply_link = Column(String(500), nullable=True)
    source = Column(String(50), default="linkedin")  # linkedin, indeed, glassdoor, etc.
    salary_info = Column(String(255), nullable=True)
    job_type = Column(String(50), nullable=True)
    seniority_level = Column(String(50), nullable=True)
    remote_friendly = Column(String(20), nullable=True)
    posted_date = Column(DateTime(timezone=True), nullable=True)
    application_deadline = Column(DateTime(timezone=True), nullable=True)
    is_applied = Column(String(20), default="no")  # no, applied, rejected, interview
    notes = Column(Text, nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="recommended_jobs")
    
    def __repr__(self):
        return f"<RecommendedJob(id={self.id}, title='{self.title}', company='{self.company}', score={self.match_score})>"
