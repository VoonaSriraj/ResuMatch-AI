"""
Resume model for storing uploaded resumes and parsed data
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=False)  # pdf, docx, doc, txt
    file_size = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    parsed_skills = Column(Text, nullable=True)  # JSON string
    parsed_experience = Column(Text, nullable=True)  # JSON string
    parsed_education = Column(Text, nullable=True)  # JSON string
    parsed_certifications = Column(Text, nullable=True)  # JSON string
    parsed_achievements = Column(Text, nullable=True)  # JSON string
    raw_ai_response = Column(Text, nullable=True)  # Store full AI parsing response
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    match_history = relationship("MatchHistory", back_populates="resume", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Resume(id={self.id}, filename='{self.filename}', user_id={self.user_id})>"
