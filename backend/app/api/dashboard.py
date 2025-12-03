"""
Dashboard statistics API endpoint
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Dict, Any

from app.database import get_db
from app.models.user import User
from app.models.resume import Resume
from app.models.job import JobDescription, RecommendedJob
from app.models.match_history import MatchHistory
from app.models.activity_log import ActivityLog
from app.models.job_recommendations import UserProfile
from app.utils.auth import get_current_active_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.get("/api/dashboard/stats")
async def get_dashboard_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get dashboard statistics for the current user"""
    try:
        # Get total matches
        total_matches = db.query(MatchHistory).filter(
            MatchHistory.user_id == current_user.id
        ).count()
        
        # Get recommended jobs count
        recommended_jobs = db.query(RecommendedJob).filter(
            RecommendedJob.user_id == current_user.id
        ).count()
        
        # Get average resume score (from match history)
        avg_match_score = db.query(func.avg(MatchHistory.match_score)).filter(
            MatchHistory.user_id == current_user.id,
            MatchHistory.match_score.isnot(None)
        ).scalar() or 0
        
        # Get active applications (jobs marked as applied)
        active_applications = db.query(RecommendedJob).filter(
            RecommendedJob.user_id == current_user.id,
            RecommendedJob.is_applied.in_(["applied", "interview"])
        ).count()
        
        # Get recent activity count (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity = db.query(ActivityLog).filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.created_at >= week_ago
        ).count()
        
        # Get resume count
        resume_count = db.query(Resume).filter(
            Resume.user_id == current_user.id
        ).count()
        
        # Get job descriptions uploaded
        job_descriptions_count = db.query(JobDescription).filter(
            JobDescription.user_id == current_user.id
        ).count()
        
        # Calculate trends (comparing last 7 days vs previous 7 days)
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        previous_week_activity = db.query(ActivityLog).filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.created_at >= two_weeks_ago,
            ActivityLog.created_at < week_ago
        ).count()
        
        activity_trend = "up" if recent_activity > previous_week_activity else "down" if recent_activity < previous_week_activity else "neutral"
        activity_change = f"{recent_activity - previous_week_activity:+d}" if previous_week_activity > 0 else f"{recent_activity} new"
        
        return {
            "total_matches": total_matches,
            "recommended_jobs": recommended_jobs,
            "average_resume_score": round(avg_match_score, 1),
            "active_applications": active_applications,
            "recent_activity": recent_activity,
            "resume_count": resume_count,
            "job_descriptions_count": job_descriptions_count,
            "activity_trend": activity_trend,
            "activity_change": activity_change,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )

@router.get("/api/dashboard/recent-matches")
async def get_recent_matches(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 5
) -> Dict[str, Any]:
    """Get recent job matches for the dashboard"""
    try:
        # Get recent matches with job and resume details
        recent_matches = db.query(MatchHistory).join(
            JobDescription, MatchHistory.job_id == JobDescription.id
        ).join(
            Resume, MatchHistory.resume_id == Resume.id
        ).filter(
            MatchHistory.user_id == current_user.id
        ).order_by(desc(MatchHistory.created_at)).limit(limit).all()
        
        matches_data = []
        for match in recent_matches:
            # Get job details
            job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
            
            # Calculate time ago
            time_diff = datetime.utcnow() - match.created_at
            if time_diff.days > 0:
                time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
            else:
                minutes = time_diff.seconds // 60
                time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            
            # Determine status based on match score
            if match.match_score >= 80:
                status = "high"
            elif match.match_score >= 60:
                status = "medium"
            else:
                status = "low"
            
            matches_data.append({
                "id": match.id,
                "job_title": job.title if job else "Unknown Job",
                "company": job.company if job else "Unknown Company",
                "match_score": match.match_score,
                "status": status,
                "date": time_ago,
                "created_at": match.created_at.isoformat()
            })
        
        return {
            "matches": matches_data,
            "total_count": len(matches_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent matches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent matches"
        )
