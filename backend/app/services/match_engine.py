"""
Match engine service for calculating resume-job compatibility scores
"""

from typing import Dict, Any, List, Tuple
import asyncio
from app.services.groq_service import groq_service
from app.utils.logger import get_logger
from app.utils.helpers import calculate_match_percentage
from app.config import settings

logger = get_logger(__name__)

class MatchEngineService:
    def __init__(self):
        pass
    
    async def calculate_comprehensive_match_score(
        self, 
        resume_text: str, 
        job_text: str,
        resume_skills: List[str] = None,
        resume_experience: List[str] = None,
        job_skills: List[str] = None,
        job_requirements: List[str] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive match score using AI and rule-based analysis"""
        try:
            # Get AI-powered match analysis
            ai_analysis = await groq_service.calculate_match_score(resume_text, job_text)
            
            # Calculate rule-based scores if data is available
            rule_based_scores = {}
            if resume_skills and job_skills:
                rule_based_scores['skills_match_score'] = calculate_match_percentage(
                    resume_skills, job_skills
                )
            # Experience score heuristic if we have requirements
            if resume_experience and job_requirements:
                rule_based_scores['experience_match_score'] = calculate_match_percentage(
                    resume_experience, job_requirements
                )
            
            # Combine AI and rule-based scores
            final_scores = self._combine_scores(ai_analysis, rule_based_scores)
            
            # Generate detailed breakdown
            breakdown = self._generate_match_breakdown(
                ai_analysis, rule_based_scores, resume_skills, job_skills
            )

            # Fallbacks when AI returns sparse data
            missing_keywords: List[str] = ai_analysis.get("missing_keywords") or []
            matching_keywords: List[str] = ai_analysis.get("matching_keywords") or []
            suggestions: List[str] = ai_analysis.get("suggestions") or []

            if (not missing_keywords) and job_skills and resume_skills:
                # Use rule-based diff as missing keywords
                missing_keywords = list(sorted(set(job_skills) - set(resume_skills)))[:25]
                matching_keywords = list(sorted(set(job_skills) & set(resume_skills)))[:25]

            if not suggestions:
                suggestions = []
                if missing_keywords:
                    suggestions.append(
                        f"Incorporate missing keywords: {', '.join(missing_keywords[:10])}."
                    )
                if resume_text and len(resume_text) < 400:
                    suggestions.append("Add more detail: quantify achievements with metrics and impact.")
                if resume_skills and job_skills and len(set(resume_skills) & set(job_skills)) < max(1, len(job_skills)//4):
                    suggestions.append("Align skills section with job requirements; prioritize role-specific tools.")
                if job_requirements and resume_experience:
                    suggestions.append("Map your experience bullets to the job's key requirements explicitly.")
                if not suggestions:
                    suggestions = ["Resume aligns reasonably; fine-tune phrasing and highlight measurable outcomes."]

            # Estimate keywords match if not provided
            keywords_match_score = final_scores.get("keywords_match_score", 0)
            if not keywords_match_score and job_skills is not None:
                if job_skills:
                    keywords_match_score = calculate_match_percentage(
                        list(set(resume_skills or [])), list(set(job_skills or []))
                    )
                else:
                    keywords_match_score = 0
                final_scores["keywords_match_score"] = keywords_match_score
            
            return {
                "overall_match_score": final_scores.get("overall_match_score", 0),
                "skills_match_score": final_scores.get("skills_match_score", 0),
                "experience_match_score": final_scores.get("experience_match_score", 0),
                "keywords_match_score": final_scores.get("keywords_match_score", 0),
                "missing_keywords": missing_keywords,
                "matching_keywords": matching_keywords,
                "suggestions": suggestions,
                "breakdown": breakdown,
                "ai_confidence": self._calculate_ai_confidence(ai_analysis),
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Match score calculation failed: {str(e)}")
            return {
                "overall_match_score": 0,
                "skills_match_score": 0,
                "experience_match_score": 0,
                "keywords_match_score": 0,
                "missing_keywords": [],
                "matching_keywords": [],
                "suggestions": [f"Match calculation failed: {str(e)}"],
                "breakdown": {},
                "ai_confidence": 0,
                "processing_status": "failed",
                "error": str(e)
            }
    
    async def optimize_resume_for_job(
        self, 
        resume_text: str, 
        job_text: str
    ) -> Dict[str, Any]:
        """Optimize resume for a specific job using AI"""
        try:
            optimization_result = await groq_service.optimize_resume(resume_text, job_text)
            
            # Calculate improvement potential
            original_match = await groq_service.calculate_match_score(resume_text, job_text)
            optimized_match = await groq_service.calculate_match_score(
                optimization_result.get("optimized_resume_text", resume_text), 
                job_text
            )
            
            improvement_score = max(0, 
                optimized_match.get("overall_match_score", 0) - 
                original_match.get("overall_match_score", 0)
            )
            
            return {
                "optimized_resume_text": optimization_result.get("optimized_resume_text", resume_text),
                "changes_made": optimization_result.get("changes_made", []),
                "keywords_added": optimization_result.get("keywords_added", []),
                "improvements": optimization_result.get("improvements", []),
                "original_score": original_match.get("overall_match_score", 0),
                "optimized_score": optimized_match.get("overall_match_score", 0),
                "improvement_score": improvement_score,
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Resume optimization failed: {str(e)}")
            return {
                "optimized_resume_text": resume_text,
                "changes_made": [],
                "keywords_added": [],
                "improvements": [],
                "original_score": 0,
                "optimized_score": 0,
                "improvement_score": 0,
                "processing_status": "failed",
                "error": str(e)
            }
    
    def _combine_scores(self, ai_analysis: Dict[str, Any], rule_based_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Combine AI and rule-based scores with weighted averages"""
        combined = {}
        
        # AI scores (weight: 0.7)
        ai_weight = 0.7
        rule_weight = 0.3
        
        for score_key in ["overall_match_score", "skills_match_score", "experience_match_score"]:
            ai_score = ai_analysis.get(score_key, 0)
            rule_score = rule_based_scores.get(score_key, ai_score)  # Fallback to AI score
            
            if score_key in rule_based_scores:
                combined[score_key] = (ai_score * ai_weight) + (rule_score * rule_weight)
            else:
                combined[score_key] = ai_score
        
        return combined
    
    def _generate_match_breakdown(
        self, 
        ai_analysis: Dict[str, Any], 
        rule_based_scores: Dict[str, Any],
        resume_skills: List[str] = None,
        job_skills: List[str] = None
    ) -> Dict[str, Any]:
        """Generate detailed breakdown of match analysis"""
        breakdown = {
            "ai_scores": {
                "overall": ai_analysis.get("overall_match_score", 0),
                "skills": ai_analysis.get("skills_match_score", 0),
                "experience": ai_analysis.get("experience_match_score", 0)
            },
            "rule_based_scores": rule_based_scores,
            "analysis_methods": ["ai_analysis", "rule_based_analysis"]
        }
        
        # Add skill comparison if available
        if resume_skills and job_skills:
            matching_skills = list(set(resume_skills) & set(job_skills))
            missing_skills = list(set(job_skills) - set(resume_skills))
            extra_skills = list(set(resume_skills) - set(job_skills))
            
            breakdown["skill_analysis"] = {
                "matching_skills": matching_skills,
                "missing_skills": missing_skills,
                "extra_skills": extra_skills,
                "skill_match_percentage": calculate_match_percentage(resume_skills, job_skills)
            }
        
        return breakdown
    
    def _calculate_ai_confidence(self, ai_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for AI analysis"""
        # Simple confidence calculation based on response completeness
        required_fields = ["overall_match_score", "missing_keywords", "matching_keywords", "suggestions"]
        present_fields = sum(1 for field in required_fields if field in ai_analysis and ai_analysis[field])
        
        confidence = (present_fields / len(required_fields)) * 100
        
        # Boost confidence if scores are reasonable
        overall_score = ai_analysis.get("overall_match_score", 0)
        if 0 <= overall_score <= 100:
            confidence += 10
        
        return min(100, confidence)
    
    async def batch_calculate_matches(
        self, 
        resume_text: str, 
        job_descriptions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate match scores for multiple job descriptions"""
        results = []
        
        for job in job_descriptions:
            try:
                match_result = await self.calculate_comprehensive_match_score(
                    resume_text, 
                    job.get("job_text", ""),
                    job.get("required_skills", []),
                    job.get("experience_requirements", [])
                )
                
                results.append({
                    "job_id": job.get("id"),
                    "job_title": job.get("title"),
                    "company": job.get("company"),
                    "match_score": match_result.get("overall_match_score", 0),
                    "details": match_result
                })
                
            except Exception as e:
                logger.error(f"Batch match calculation failed for job {job.get('id')}: {str(e)}")
                results.append({
                    "job_id": job.get("id"),
                    "job_title": job.get("title"),
                    "company": job.get("company"),
                    "match_score": 0,
                    "error": str(e)
                })
        
        # Sort by match score descending
        results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return results

# Global instance
match_engine_service = MatchEngineService()
