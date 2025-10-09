"""
Activity log model for tracking user actions and system events
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system events
    action_type = Column(String(100), nullable=False)  # login, upload_resume, job_match, etc.
    description = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)  # Additional structured data
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    def __repr__(self):
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, action_type='{self.action_type}')>"
