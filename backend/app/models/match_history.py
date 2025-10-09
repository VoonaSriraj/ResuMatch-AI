"""
Match history model for storing resume-job matching results
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, ARRAY, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class MatchHistory(Base):
    __tablename__ = "match_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    
    # Matching results
    match_score = Column(Float, nullable=False)  # 0-100
    missing_keywords = Column(ARRAY(String), nullable=True)
    matching_keywords = Column(ARRAY(String), nullable=True)
    missing_skills = Column(ARRAY(String), nullable=True)
    matching_skills = Column(ARRAY(String), nullable=True)
    
    # AI-generated optimized resume
    optimized_resume_text = Column(Text, nullable=True)
    optimization_suggestions = Column(ARRAY(String), nullable=True)
    improvement_areas = Column(ARRAY(String), nullable=True)
    
    # Detailed analysis
    experience_match_score = Column(Float, nullable=True)
    skills_match_score = Column(Float, nullable=True)
    education_match_score = Column(Float, nullable=True)
    keywords_match_score = Column(Float, nullable=True)
    
    # AI analysis details
    detailed_analysis = Column(Text, nullable=True)
    raw_ai_response = Column(Text, nullable=True)
    
    # Status and metadata
    processing_status = Column(String(50), default="completed")  # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="match_history")
    resume = relationship("Resume", back_populates="match_history")
    job_description = relationship("JobDescription", back_populates="match_history")
    
    def __repr__(self):
        return f"<MatchHistory(id={self.id}, user_id={self.user_id}, match_score={self.match_score})>"
