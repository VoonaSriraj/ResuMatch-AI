"""
Groq AI service for all AI processing tasks
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from groq import Groq
from app.config import settings
from app.utils.logger import get_logger
from app.utils.helpers import clean_text_for_ai, format_ai_prompt

logger = get_logger(__name__)

class GroqService:
    def __init__(self):
        # In development, operate in mock mode when no API key is provided
        self.mock = not bool(settings.groq_api_key)
        self.client = None
        self.model = settings.groq_model
        if not self.mock:
            self.client = Groq(api_key=settings.groq_api_key)
    
    async def generate_response(self, prompt: str, max_tokens: int = 4000) -> str:
        """Generate response from Groq AI"""
        try:
            if self.mock:
                # Return prompt back – higher-level methods will not use this in mock mode
                return "{}"
            # Clean the prompt
            clean_prompt = clean_text_for_ai(prompt)
            
            # Make async call to Groq
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[
                    {
                        "role": "user",
                        "content": clean_prompt
                    }
                ],
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.1  # Low temperature for more consistent results
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise Exception(f"AI processing failed: {str(e)}")
    
    async def parse_json_response(self, prompt: str, max_tokens: int = 4000) -> Dict[str, Any]:
        """Generate and parse JSON response from Groq AI.
        Robust against markdown code fences and extra text around JSON.
        """
        try:
            response_text = await self.generate_response(prompt, max_tokens)

            # 1) Handle fenced code blocks first: ```json ... ``` or ``` ... ```
            if "```" in response_text:
                try:
                    fence_start = response_text.find("```")
                    fence_end = response_text.rfind("```")
                    if fence_end > fence_start + 3:
                        fenced = response_text[fence_start + 3:fence_end]
                        # Remove an optional language tag like 'json' on the first line
                        first_newline = fenced.find("\n")
                        if first_newline != -1:
                            maybe_lang = fenced[:first_newline].strip().lower()
                            content = fenced[first_newline + 1:] if maybe_lang in {"json", "javascript", "ts", "python"} else fenced
                        else:
                            content = fenced
                        return json.loads(content)
                except Exception:
                    pass  # fall through to other strategies

            # 2) Try to extract the largest JSON object substring
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)

            # 3) Last resort: try to parse the entire response
            return json.loads(response_text)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}, Response: {response_text}")
            return {
                "error": "Failed to parse AI response",
                "raw_response": response_text
            }
        except Exception as e:
            logger.error(f"Error in parse_json_response: {str(e)}")
            raise
    
    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text and extract structured data"""
        prompt = format_ai_prompt("resume_parsing", resume_text=resume_text)
        
        try:
            if self.mock:
                # Simple heuristics in mock mode
                from app.utils.helpers import extract_skills_from_text
                return {
                    "skills": extract_skills_from_text(resume_text),
                    "experience": [],
                    "education": [],
                    "certifications": [],
                    "achievements": []
                }
            result = await self.parse_json_response(prompt)
            
            # Validate and clean the response
            parsed_data = {
                "skills": result.get("skills", []),
                "experience": result.get("experience", []),
                "education": result.get("education", []),
                "certifications": result.get("certifications", []),
                "achievements": result.get("achievements", [])
            }
            
            # Ensure all values are lists
            for key, value in parsed_data.items():
                if not isinstance(value, list):
                    parsed_data[key] = [value] if value else []
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Resume parsing failed: {str(e)}")
            return {
                "skills": [],
                "experience": [],
                "education": [],
                "certifications": [],
                "achievements": [],
                "error": str(e)
            }
    
    async def parse_job_description(self, job_text: str) -> Dict[str, Any]:
        """Parse job description and extract requirements"""
        prompt = format_ai_prompt("job_parsing", job_text=job_text)
        
        try:
            if self.mock:
                from app.utils.helpers import extract_skills_from_text
                skills = extract_skills_from_text(job_text)
                return {
                    "required_skills": skills,
                    "experience_requirements": [],
                    "education_requirements": [],
                    "certifications": [],
                    "job_details": {}
                }
            result = await self.parse_json_response(prompt)
            
            # Validate and clean the response
            parsed_data = {
                "required_skills": result.get("required_skills", []),
                "experience_requirements": result.get("experience_requirements", []),
                "education_requirements": result.get("education_requirements", []),
                "certifications": result.get("certifications", []),
                "job_details": result.get("job_details", {})
            }
            
            # Ensure skills and requirements are lists
            for key in ["required_skills", "experience_requirements", "education_requirements", "certifications"]:
                if not isinstance(parsed_data[key], list):
                    parsed_data[key] = [parsed_data[key]] if parsed_data[key] else []
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Job parsing failed: {str(e)}")
            return {
                "required_skills": [],
                "experience_requirements": [],
                "education_requirements": [],
                "certifications": [],
                "job_details": {},
                "error": str(e)
            }
    
    async def calculate_match_score(self, resume_text: str, job_text: str) -> Dict[str, Any]:
        """Calculate match score between resume and job description"""
        prompt = format_ai_prompt("match_scoring", resume_text=resume_text, job_text=job_text)
        
        try:
            if self.mock:
                from app.utils.helpers import extract_skills_from_text, calculate_match_percentage
                resume_sk = extract_skills_from_text(resume_text)
                job_sk = extract_skills_from_text(job_text)
                skills_score = calculate_match_percentage(resume_sk, job_sk)
                overall = round(0.7 * skills_score + 0.3 * 60, 2)  # heuristic
                missing = list(sorted(set(job_sk) - set(resume_sk)))[:25]
                matching = list(sorted(set(job_sk) & set(resume_sk)))[:25]
                suggestions = []
                if missing:
                    suggestions.append(f"Add missing keywords: {', '.join(missing[:10])}.")
                suggestions.append("Quantify achievements and align bullets to the JD.")
                return {
                    "overall_match_score": overall,
                    "skills_match_score": skills_score,
                    "experience_match_score": 60.0,
                    "missing_keywords": missing,
                    "matching_keywords": matching,
                    "suggestions": suggestions
                }
            result = await self.parse_json_response(prompt)
            
            # Validate scores are within 0-100 range
            scores = {}
            for score_key in ["overall_match_score", "skills_match_score", "experience_match_score"]:
                score = result.get(score_key, 0)
                if isinstance(score, (int, float)):
                    scores[score_key] = max(0, min(100, score))
                else:
                    scores[score_key] = 0
            
            return {
                **scores,
                "missing_keywords": result.get("missing_keywords", []),
                "matching_keywords": result.get("matching_keywords", []),
                "suggestions": result.get("suggestions", [])
            }
            
        except Exception as e:
            logger.error(f"Match scoring failed: {str(e)}")
            return {
                "overall_match_score": 0,
                "skills_match_score": 0,
                "experience_match_score": 0,
                "missing_keywords": [],
                "matching_keywords": [],
                "suggestions": [],
                "error": str(e)
            }
    
    async def optimize_resume(self, resume_text: str, job_text: str) -> Dict[str, Any]:
        """Optimize resume for a specific job description"""
        prompt = format_ai_prompt("resume_optimization", resume_text=resume_text, job_text=job_text)
        
        try:
            if self.mock:
                from app.utils.helpers import extract_skills_from_text
                job_keywords = extract_skills_from_text(job_text)
                added = [kw for kw in job_keywords if kw.lower() not in resume_text.lower()][:10]
                optimized = resume_text + ("\n\nKeywords: " + ", ".join(added) if added else "")
                return {
                    "optimized_resume_text": optimized,
                    "changes_made": [f"Added keywords: {', '.join(added)}"] if added else [],
                    "keywords_added": added,
                    "improvements": ["Aligned skills to JD", "Added measurable outcomes where missing"],
                }
            result = await self.parse_json_response(prompt, max_tokens=6000)
            
            return {
                "optimized_resume_text": result.get("optimized_resume_text", resume_text),
                "changes_made": result.get("changes_made", []),
                "keywords_added": result.get("keywords_added", []),
                "improvements": result.get("improvements", [])
            }
            
        except Exception as e:
            logger.error(f"Resume optimization failed: {str(e)}")
            return {
                "optimized_resume_text": resume_text,
                "changes_made": [],
                "keywords_added": [],
                "improvements": [],
                "error": str(e)
            }
    
    async def generate_interview_questions(self, job_text: str) -> Dict[str, Any]:
        """Generate interview questions based on job description"""
        prompt = format_ai_prompt("interview_questions", job_text=job_text)
        
        try:
            result = await self.parse_json_response(prompt)
            
            # Ensure all categories have lists
            categories = [
                "technical_questions", "behavioral_questions", 
                "company_culture_questions", "leadership_questions"
            ]
            
            for category in categories:
                if not isinstance(result.get(category), list):
                    result[category] = []
            
            return {
                "technical_questions": result.get("technical_questions", []),
                "behavioral_questions": result.get("behavioral_questions", []),
                "company_culture_questions": result.get("company_culture_questions", []),
                "leadership_questions": result.get("leadership_questions", []),
                "tips": result.get("tips", [])
            }
            
        except Exception as e:
            logger.error(f"Interview questions generation failed: {str(e)}")
            return {
                "technical_questions": [],
                "behavioral_questions": [],
                "company_culture_questions": [],
                "leadership_questions": [],
                "tips": [],
                "error": str(e)
            }

# Global instance
groq_service = GroqService()
