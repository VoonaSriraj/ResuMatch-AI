"""
Match engine service for calculating resume-job compatibility scores
"""

from typing import Dict, Any, List, Tuple
import asyncio
from app.services.groq_service import groq_service
from app.utils.logger import get_logger
from app.utils.helpers import (
    calculate_match_percentage,
    extract_years_of_experience,
    extract_role_tokens,
    extract_domain_keywords,
)
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

            # If experience score not available from structured data, compute from text
            if 'experience_match_score' not in rule_based_scores or not rule_based_scores.get('experience_match_score'):
                resume_years = extract_years_of_experience(resume_text)
                job_years = extract_years_of_experience(job_text)
                years_score = 0.0
                if job_years and job_years > 0:
                    if resume_years is not None:
                        years_score = min(100.0, max(0.0, (resume_years / job_years) * 100.0))
                # Role similarity
                resume_roles = set(extract_role_tokens(resume_text))
                job_roles = set(extract_role_tokens(job_text))
                role_score = 0.0
                if job_roles:
                    role_score = (len(resume_roles & job_roles) / len(job_roles)) * 100.0
                # Domain similarity
                resume_domains = set(extract_domain_keywords(resume_text))
                job_domains = set(extract_domain_keywords(job_text))
                domain_score = 0.0
                if job_domains:
                    domain_score = (len(resume_domains & job_domains) / len(job_domains)) * 100.0
                rule_based_scores['experience_match_score'] = (0.5 * years_score) + (0.25 * role_score) + (0.25 * domain_score)

            # Combine AI and rule-based scores (favor AI when available)
            final_scores = self._combine_scores(ai_analysis, rule_based_scores)
            
            # Generate detailed breakdown
            breakdown = self._generate_match_breakdown(
                ai_analysis, rule_based_scores, resume_skills, job_skills
            )

            # Fallbacks when AI returns sparse data
            missing_keywords: List[str] = ai_analysis.get("missing_keywords") or []
            matching_keywords: List[str] = ai_analysis.get("matching_keywords") or []
            suggestions: List[str] = ai_analysis.get("suggestions") or []
            ats_findings: List[str] = ai_analysis.get("ats_findings") or []
            readability: List[str] = ai_analysis.get("readability") or []
            strengths: List[str] = ai_analysis.get("strengths") or []

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
                # Recommend learning/highlighting based on gaps
                if missing_keywords:
                    suggestions.append(f"Learn or highlight: {', '.join(missing_keywords[:8])}.")
                if not suggestions:
                    suggestions = ["Resume aligns reasonably; fine-tune phrasing and highlight measurable outcomes."]

            # Fallback ATS findings if not provided
            if not ats_findings:
                ats_findings = [
                    'Use standard section headings (Summary, Skills, Experience, Education, Projects).',
                    'Avoid images, text boxes, and unusual fonts; keep to simple PDF or DOCX.',
                    'Ensure keywords appear in plain text (not inside graphics).',
                ]

            # Fallback readability notes if not provided
            if not readability:
                readability = [
                    'Prefer bullet points with action verbs (Implemented, Led, Optimized).',
                    'Use concise sentences (12–20 words) and consistent tense.',
                    'Quantify impact (e.g., Increased throughput by 25%).',
                ]

            # Fallback strengths if not provided
            if not strengths:
                overall_score = final_scores.get("overall_match_score", 0)
                if overall_score >= 70:
                    strengths = ['Strong alignment with required skills.', 'Good coverage of experience relevant to the role.']
                else:
                    strengths = ['Clear baseline skills present.', 'Room to emphasize accomplishments and metrics.']

            # Estimate keywords match if not provided
            keywords_match_score = final_scores.get("keywords_match_score", ai_analysis.get("keywords_match_score", 0))
            if not keywords_match_score and job_skills is not None:
                if job_skills:
                    keywords_match_score = calculate_match_percentage(
                        list(set(resume_skills or [])), list(set(job_skills or []))
                    )
                else:
                    keywords_match_score = 0
                final_scores["keywords_match_score"] = keywords_match_score

            # Ensure overall score uses the requested weights
            final_scores["overall_match_score"] = (
                0.4 * float(final_scores.get("skills_match_score", 0))
                + 0.3 * float(final_scores.get("experience_match_score", 0))
                + 0.3 * float(final_scores.get("keywords_match_score", 0))
            )
            
            return {
                "overall_match_score": final_scores.get("overall_match_score", 0),
                "skills_match_score": final_scores.get("skills_match_score", 0),
                "experience_match_score": final_scores.get("experience_match_score", 0),
                "keywords_match_score": final_scores.get("keywords_match_score", 0),
                "missing_keywords": missing_keywords,
                "matching_keywords": matching_keywords,
                "suggestions": suggestions,
                "ats_findings": ats_findings,
                "readability": readability,
                "strengths": strengths,
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
                "ats_findings": [],
                "readability": [],
                "strengths": [],
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
        
        for score_key in ["overall_match_score", "skills_match_score", "experience_match_score", "keywords_match_score"]:
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

    async def evaluate_resume_ats(self, resume_text: str) -> Dict[str, Any]:
        """Evaluate resume via Groq AI first, then fallback to rule-based heuristics.
        This function is async so we can await the Groq client without blocking.
        """
        try:
            # Try AI first when Groq is enabled (GROQ_API_KEY present)
            ai = None
            if not getattr(groq_service, "mock", True):
                try:
                    ai = await groq_service.evaluate_resume_ats(resume_text)
                except Exception:
                    ai = None
            if isinstance(ai, dict) and not ai.get("error") and ai.get("overall_ats_score") is not None:
                # Add minimal recommendations if missing
                if not ai.get("weaknesses"):
                    ai["weaknesses"] = ["Quantify impact with metrics.", "Use action verbs in bullets."]
                if not ai.get("strengths"):
                    ai["strengths"] = ["Clean structure.", "Clear baseline skills."]
                ai["source"] = "ai"
                return ai

            text = resume_text or ""
            lower = text.lower()

            # 1) Structure & Formatting (25%)
            required_sections = ["summary", "skills", "experience", "education", "projects"]
            sections_present = sum(1 for sec in required_sections if sec in lower)
            structure_score = (sections_present / len(required_sections)) * 100.0
            # Simple penalties for tables/columns/graphics-like hints
            bad_layout_markers = ["|", "table", "column", "columns", "image", "graphic"]
            penalties = sum(1 for m in bad_layout_markers if m in lower)
            if penalties:
                structure_score = max(0.0, structure_score - min(30.0, 5.0 * penalties))

            # 2) Keyword & Content Relevance (25%)
            action_verbs = [
                "developed", "implemented", "optimized", "led", "improved", "designed",
                "built", "launched", "migrated", "reduced", "increased", "delivered",
                "automated", "refactored", "architected", "analyzed", "collaborated"
            ]
            verb_hits = sum(1 for v in action_verbs if v in lower)
            keyword_score = min(100.0, (verb_hits / 10.0) * 100.0)

            # 3) Skill Presentation & Alignment (20%)
            from app.utils.helpers import extract_skills_from_text
            skills = extract_skills_from_text(text)
            unique_skills = len({s.lower() for s in skills})
            body_hits = 0
            for s in set(skills):
                body_hits += lower.count(s.lower())
            skills_score = min(100.0, (min(unique_skills, 20) / 20.0) * 60.0 + (min(body_hits, 20) / 20.0) * 40.0)

            # 4) Readability & Clarity (15%)
            num_chars = len(text)
            num_digits = sum(1 for c in text if c.isdigit())
            bullets = text.count("\n-") + text.count("\n*") + text.count("\n•")
            sentences = [s for s in text.split('.') if s]
            avg_sentence_len = max(1.0, sum(len(s) for s in sentences) / max(1, len(sentences)))
            readability_score = 60.0
            if bullets >= 5:
                readability_score += 15.0
            if avg_sentence_len <= 140:
                readability_score += 15.0
            if num_chars and (num_digits / num_chars) > 0.01:
                readability_score += 10.0
            readability_score = max(0.0, min(100.0, readability_score))

            # 5) Impact & Achievements (15%)
            impact_hits = 0
            impact_markers = ["%", "percent", "x", "$", "reduced", "increased", "decreased"]
            for m in impact_markers:
                if m in lower:
                    impact_hits += 1
            impact_hits += min(10, num_digits // 5)
            impact_score = min(100.0, (impact_hits / 10.0) * 100.0)

            # Overall score per formula
            overall = (
                0.25 * structure_score
                + 0.25 * keyword_score
                + 0.20 * skills_score
                + 0.15 * readability_score
                + 0.15 * impact_score
            )

            # Recommendations
            recommendations: List[str] = []
            if sections_present < len(required_sections):
                missing_secs = [s.title() for s in required_sections if s not in lower]
                recommendations.append(f"Add standard sections: {', '.join(missing_secs)}.")
            if verb_hits < 8:
                recommendations.append("Use action verbs (Developed, Implemented, Optimized) in bullets.")
            if unique_skills < 8:
                recommendations.append("Expand Skills section with relevant tools and technologies.")
            if bullets < 5:
                recommendations.append("Use concise bullet points; avoid long paragraphs.")
            if num_digits < 10:
                recommendations.append("Quantify impact with metrics (%, latency, throughput, revenue, users).")

            result = {
                "structure_score": round(structure_score, 1),
                "keyword_score": round(keyword_score, 1),
                "skills_score": round(skills_score, 1),
                "readability_score": round(readability_score, 1),
                "impact_score": round(impact_score, 1),
                "overall_ats_score": round(overall, 1),
                "recommendations": recommendations,
                "strengths": [s for s in [
                    "Strong skills coverage" if unique_skills >= 10 else None,
                    "Readable bullet structure" if bullets >= 5 else None,
                ] if s],
                "weaknesses": recommendations,
                "source": "heuristic",
            }
            return result
        except Exception as e:
            logger.error(f"ATS evaluation failed: {str(e)}")
            return {
                "structure_score": 0,
                "keyword_score": 0,
                "skills_score": 0,
                "readability_score": 0,
                "impact_score": 0,
                "overall_ats_score": 0,
                "recommendations": [f"Evaluation failed: {str(e)}"],
                "strengths": [],
                "weaknesses": [f"Evaluation failed: {str(e)}"],
            }

# Global instance
match_engine_service = MatchEngineService()
