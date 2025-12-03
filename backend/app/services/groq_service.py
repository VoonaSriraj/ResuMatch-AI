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
        
        if self.mock:
            logger.warning("Groq API key not found. Running in MOCK mode. Set GROQ_API_KEY environment variable to enable AI features.")
        else:
            logger.info(f"Groq API initialized with model: {self.model}")
            try:
                self.client = Groq(api_key=settings.groq_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {str(e)}")
                self.mock = True
    
    async def generate_response(self, prompt: str, max_tokens: int = 4000, model_name: str = None) -> str:
        """Generate response from Groq AI"""
        try:
            if self.mock:
                # Return prompt back – higher-level methods will not use this in mock mode
                return "{}"
            # Clean the prompt
            clean_prompt = clean_text_for_ai(prompt)
            
            # Use provided model_name or fallback to self.model
            model_to_use = model_name or self.model
            
            # Make async call to Groq
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[
                    {
                        "role": "user",
                        "content": clean_prompt
                    }
                ],
                model=model_to_use,
                max_tokens=max_tokens,
                temperature=0.1  # Low temperature for more consistent results
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise Exception(f"AI processing failed: {str(e)}")
    
    async def parse_json_response(self, prompt: str, max_tokens: int = 4000, model_name: str = None) -> Dict[str, Any]:
        """Generate and parse JSON response from Groq AI.
        Robust against markdown code fences and extra text around JSON.
        """
        try:
            response_text = await self.generate_response(prompt, max_tokens, model_name)

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
        # Log input lengths for debugging
        logger.info(f"Calculating match score. Resume text length: {len(resume_text)}, Job text length: {len(job_text)}")
        
        if not resume_text.strip() or not job_text.strip():
            logger.warning("Empty resume_text or job_text provided to calculate_match_score")
            return {
                "overall_match_score": 0,
                "skills_match_score": 0,
                "experience_match_score": 0,
                "keywords_match_score": 0,
                "missing_keywords": [],
                "matching_keywords": [],
                "suggestions": ["Resume or job description text is empty. Please ensure files were processed correctly."],
                "ats_findings": [],
                "readability": [],
                "strengths": [],
                "error": "Empty input text"
            }
        
        prompt = format_ai_prompt("match_scoring", resume_text=resume_text, job_text=job_text)
        
        try:
            if self.mock:
                logger.info("Using mock mode for match score calculation")
                from app.utils.helpers import extract_skills_from_text, calculate_match_percentage
                resume_sk = extract_skills_from_text(resume_text)
                job_sk = extract_skills_from_text(job_text)
                
                # Calculate skills match score
                skills_score = calculate_match_percentage(resume_sk, job_sk)
                
                # Calculate experience match based on text similarity
                resume_words = set(resume_text.lower().split())
                job_words = set(job_text.lower().split())
                common_words = resume_words & job_words
                experience_score = min(100, (len(common_words) / max(len(job_words), 1)) * 100)
                
                # Calculate overall score with weighted average
                overall = round(0.4 * skills_score + 0.3 * experience_score + 0.3 * 65, 2)
                
                # Ensure minimum score for any match - provide realistic scores
                if overall < 15 and (resume_sk and job_sk):
                    overall = max(25, overall)  # Minimum 25% for any skills match
                elif overall < 5:
                    overall = 15  # Minimum 15% even with no skills match
                
                missing = list(sorted(set(job_sk) - set(resume_sk)))[:25]
                matching = list(sorted(set(job_sk) & set(resume_sk)))[:25]
                
                suggestions = []
                if missing:
                    suggestions.append(f"Add missing keywords: {', '.join(missing[:10])}.")
                if overall < 50:
                    suggestions.append("Quantify achievements and align bullets to the job description.")
                if skills_score < 30:
                    suggestions.append("Highlight relevant technical skills prominently.")
                if not suggestions:
                    suggestions.append("Resume aligns well with job requirements.")
                
                # Calculate keywords match score
                keywords_score = calculate_match_percentage(matching, job_sk) if job_sk else 0
                
                # Generate ATS findings based on resume structure
                ats_findings = []
                if len(resume_text) < 400:
                    ats_findings.append("Resume is too short; add more detail to improve ATS parsing.")
                if "pdf" not in resume_text.lower()[:50] and "docx" not in resume_text.lower()[:50]:
                    ats_findings.append("Ensure resume is in ATS-friendly format (PDF or DOCX).")
                if not any(keyword in resume_text.lower() for keyword in ["experience", "education", "skills"]):
                    ats_findings.append("Use standard section headings (Summary, Skills, Experience, Education).")
                if not ats_findings:
                    ats_findings.append("Resume structure appears ATS-friendly.")
                
                # Generate readability notes
                readability = []
                if len(resume_text.split()) < 200:
                    readability.append("Add more detail and quantify achievements with metrics.")
                if not any(char.isdigit() for char in resume_text):
                    readability.append("Include quantifiable results (percentages, numbers, metrics).")
                if not readability:
                    readability.append("Resume readability is good; maintain concise, action-oriented language.")
                
                # Generate strengths
                strengths = []
                if skills_score >= 60:
                    strengths.append("Strong alignment with required technical skills.")
                if experience_score >= 60:
                    strengths.append("Good coverage of experience relevant to the role.")
                if matching:
                    strengths.append(f"Key skills present: {', '.join(matching[:5])}.")
                if not strengths:
                    strengths.append("Resume shows baseline qualifications; focus on highlighting relevant experience.")
                
                return {
                    "overall_match_score": overall,
                    "skills_match_score": skills_score,
                    "experience_match_score": experience_score,
                    "keywords_match_score": keywords_score,
                    "missing_keywords": missing,
                    "matching_keywords": matching,
                    "suggestions": suggestions,
                    "ats_findings": ats_findings,
                    "readability": readability,
                    "strengths": strengths
                }
            logger.info("Calling Groq API for match score calculation")
            
            # Try the configured model first, then fallback models if it fails
            models_to_try = [
                self.model,
                "mixtral-8x7b-32768",
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "gemma2-9b-it"
            ]
            
            result = None
            last_error = None
            
            for model_name in models_to_try:
                try:
                    logger.info(f"Trying model: {model_name}")
                    
                    result = await self.parse_json_response(prompt, max_tokens=6000, model_name=model_name)
                    
                    # Check if we got an error response
                    if "error" in result:
                        error_msg = result.get("error", {}).get("message", "") if isinstance(result.get("error"), dict) else str(result.get("error", ""))
                        if "decommissioned" in error_msg.lower() or "not supported" in error_msg.lower() or "model_decommissioned" in error_msg.lower():
                            logger.warning(f"Model {model_name} is decommissioned, trying next model...")
                            last_error = error_msg
                            result = None
                            continue
                        else:
                            # Different error, break and handle below
                            break
                    else:
                        # Success! Use this model going forward
                        logger.info(f"Successfully using model: {model_name}")
                        if model_name != self.model:
                            # Update the model setting for future calls
                            self.model = model_name
                            from app.config import settings
                            settings.groq_model = model_name
                        break
                        
                except Exception as e:
                    error_str = str(e)
                    if "decommissioned" in error_str.lower() or "not supported" in error_str.lower() or "model_decommissioned" in error_str.lower():
                        logger.warning(f"Model {model_name} failed: {error_str}, trying next model...")
                        last_error = error_str
                        result = None
                        continue
                    else:
                        # Different error, break and handle
                        last_error = error_str
                        break
            
            # If all models failed or we got an error response
            if result is None or ("error" in result if result else False):
                logger.error(f"All Groq models failed. Last error: {last_error}")
                # Fall back to rule-based calculation
                from app.utils.helpers import extract_skills_from_text, calculate_match_percentage
                resume_sk = extract_skills_from_text(resume_text)
                job_sk = extract_skills_from_text(job_text)
                
                skills_score = calculate_match_percentage(resume_sk, job_sk) if job_sk else 0
                resume_words = set(resume_text.lower().split())
                job_words = set(job_text.lower().split())
                common_words = resume_words & job_words
                experience_score = min(100, (len(common_words) / max(len(job_words), 1)) * 100) if job_words else 0
                overall = round(0.4 * skills_score + 0.3 * experience_score + 0.3 * 50, 2)
                keywords_score = calculate_match_percentage(resume_sk, job_sk) if job_sk else 0
                
                return {
                    "overall_match_score": max(overall, 15),  # Minimum 15%
                    "skills_match_score": skills_score,
                    "experience_match_score": experience_score,
                    "keywords_match_score": keywords_score,
                    "missing_keywords": list(sorted(set(job_sk) - set(resume_sk)))[:25],
                    "matching_keywords": list(sorted(set(job_sk) & set(resume_sk)))[:25],
                    "suggestions": ["AI analysis temporarily unavailable. Using rule-based matching."],
                    "ats_findings": ["Use standard section headings (Summary, Skills, Experience, Education)."],
                    "readability": ["Ensure resume is clear and well-structured."],
                    "strengths": ["Resume shows baseline qualifications."]
                }
            
            logger.info(f"Groq API response received. Overall score: {result.get('overall_match_score', 0)}")
            
            # Validate scores are within 0-100 range
            scores = {}
            for score_key in ["overall_match_score", "skills_match_score", "experience_match_score", "keywords_match_score"]:
                score = result.get(score_key, 0)
                if isinstance(score, (int, float)):
                    scores[score_key] = max(0, min(100, score))
                else:
                    scores[score_key] = 0
            
            # If all scores are 0, something went wrong - use fallback calculation
            if all(v == 0 for v in scores.values()):
                logger.warning("All scores are 0 from Groq API, using fallback calculation")
                from app.utils.helpers import extract_skills_from_text, calculate_match_percentage
                resume_sk = extract_skills_from_text(resume_text)
                job_sk = extract_skills_from_text(job_text)
                
                skills_score = calculate_match_percentage(resume_sk, job_sk) if job_sk else 0
                resume_words = set(resume_text.lower().split())
                job_words = set(job_text.lower().split())
                common_words = resume_words & job_words
                experience_score = min(100, (len(common_words) / max(len(job_words), 1)) * 100) if job_words else 0
                overall = round(0.4 * skills_score + 0.3 * experience_score + 0.3 * 50, 2)
                keywords_score = calculate_match_percentage(resume_sk, job_sk) if job_sk else 0
                
                scores = {
                    "overall_match_score": max(overall, 15),
                    "skills_match_score": skills_score,
                    "experience_match_score": experience_score,
                    "keywords_match_score": keywords_score
                }
            
            # Validate lists are actually lists
            def ensure_list(value, default=None):
                if isinstance(value, list):
                    return value
                elif isinstance(value, str):
                    return [value] if value else []
                return default if default is not None else []
            
            return {
                **scores,
                "missing_keywords": ensure_list(result.get("missing_keywords"), []),
                "matching_keywords": ensure_list(result.get("matching_keywords"), []),
                "suggestions": ensure_list(result.get("suggestions"), []),
                "ats_findings": ensure_list(result.get("ats_findings"), []),
                "readability": ensure_list(result.get("readability"), []),
                "strengths": ensure_list(result.get("strengths"), [])
            }
            
        except Exception as e:
            logger.error(f"Match scoring failed: {str(e)}", exc_info=True)
            # Fallback to rule-based calculation on error
            try:
                from app.utils.helpers import extract_skills_from_text, calculate_match_percentage
                resume_sk = extract_skills_from_text(resume_text)
                job_sk = extract_skills_from_text(job_text)
                
                skills_score = calculate_match_percentage(resume_sk, job_sk) if job_sk else 0
                resume_words = set(resume_text.lower().split())
                job_words = set(job_text.lower().split())
                common_words = resume_words & job_words
                experience_score = min(100, (len(common_words) / max(len(job_words), 1)) * 100) if job_words else 0
                overall = round(0.4 * skills_score + 0.3 * experience_score + 0.3 * 50, 2)
                keywords_score = calculate_match_percentage(resume_sk, job_sk) if job_sk else 0
                
                return {
                    "overall_match_score": max(overall, 15),
                    "skills_match_score": skills_score,
                    "experience_match_score": experience_score,
                    "keywords_match_score": keywords_score,
                    "missing_keywords": list(sorted(set(job_sk) - set(resume_sk)))[:25],
                    "matching_keywords": list(sorted(set(job_sk) & set(resume_sk)))[:25],
                    "suggestions": [f"AI analysis error: {str(e)}. Using rule-based matching."],
                    "ats_findings": ["Use standard section headings (Summary, Skills, Experience, Education)."],
                    "readability": ["Ensure resume is clear and well-structured."],
                    "strengths": ["Resume shows baseline qualifications."],
                    "error": str(e)
                }
            except Exception as fallback_error:
                logger.error(f"Fallback calculation also failed: {str(fallback_error)}")
                return {
                    "overall_match_score": 0,
                    "skills_match_score": 0,
                    "experience_match_score": 0,
                    "keywords_match_score": 0,
                    "missing_keywords": [],
                    "matching_keywords": [],
                    "suggestions": [f"Analysis failed: {str(e)}"],
                    "ats_findings": [],
                    "readability": [],
                    "strengths": [],
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
            
            # If technical questions are still empty, try a simpler focused prompt
            tech: List[str] = result.get("technical_questions", [])
            if not tech:
                try:
                    simple_prompt = format_ai_prompt("interview_tech_questions_only", job_text=job_text)
                    simple = await self.parse_json_response(simple_prompt)
                    if isinstance(simple.get("technical_questions"), list) and simple["technical_questions"]:
                        result["technical_questions"] = simple["technical_questions"][:15]
                except Exception:
                    pass

            # Final safeguard: derive varied questions from extracted skills in the JD
            if not result.get("technical_questions"):
                from app.utils.helpers import extract_skills_from_text
                skills = extract_skills_from_text(job_text)[:6]
                generated = []
                for s in skills:
                    generated.append(f"Describe your hands-on experience with {s}. What problems did you solve?")
                    generated.append(f"How would you design a reliable system using {s} in this JD context?")
                generated.extend([
                    "Walk through a recent project. Scope, decisions, results?",
                    "How do you test and deploy safely in this stack?",
                ])
                result["technical_questions"] = generated[:15]

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

    async def generate_interview_qa(self, job_text: str) -> Dict[str, Any]:
        """Generate 10–15 Q&A pairs and extracted skills from a JD"""
        prompt = format_ai_prompt("interview_qa_from_jd", job_text=job_text)
        try:
            result = await self.parse_json_response(prompt, max_tokens=4000)
            # Normalize result shape
            extracted = result.get("extracted") or {}
            qa = result.get("qa") or []
            # Coerce list of dicts with required keys
            normalized_qa = []
            if isinstance(qa, list):
                for item in qa:
                    if isinstance(item, dict):
                        q = str(item.get("question", "")).strip()
                        a = str(item.get("sample_answer", "")).strip()
                        if q and a:
                            normalized_qa.append({"question": q, "sample_answer": a})
            # Enforce 10–15 length; add sensible fallbacks if sparse
            if len(normalized_qa) < 10:
                templates = [
                    ("Explain a recent project aligned with this JD.", "I delivered a feature using the specified stack (e.g., React/Node/SQL). My role covered design, implementation, tests, and deployment. We solved X by doing Y, improving Z by N%."),
                    ("How would you design a scalable solution for a core requirement in this JD?", "I’d start with a clear API/contract, choose a reliable data model, add caching and async processing where needed, and automate testing and CI/CD."),
                    ("How do you ensure performance and reliability?", "Benchmark hotspots, profile, use indexes/caching, apply circuit breakers/retries, add observability (logs/metrics/traces) and SLOs."),
                    ("Describe your testing strategy for this stack.", "Unit tests for pure logic, integration tests around DB/queues, e2e smoke tests in CI, and contract tests for APIs."),
                    ("How do you handle security and compliance?", "Secrets management, input validation, least-privilege access, dependency scanning, and regular audits/patching."),
                    ("How do you approach database schema and migrations?", "Normalize where needed, add necessary indexes, write backward-compatible migrations, and verify with rollback plans."),
                    ("Tell me about a production incident you resolved.", "We detected errors via alerts, mitigated impact with a quick rollback/feature flag, identified root cause, and added tests/monitoring."),
                    ("How do you collaborate across teams?", "Write clear RFCs, discuss tradeoffs, async updates, track work transparently, and incorporate feedback quickly."),
                    ("What patterns do you use to keep code maintainable?", "Separation of concerns, small modules, dependency injection, clear interfaces, and linting/formatting."),
                    ("How do you choose tools from the JD?", "Map requirements to strengths of each tool, validate with small spikes/benchmarks, and consider team expertise and ops overhead."),
                ]
                i = 0
                while len(normalized_qa) < 10 and i < len(templates):
                    q, a = templates[i]
                    normalized_qa.append({"question": q, "sample_answer": a})
                    i += 1
            normalized_qa = normalized_qa[:15]
            return {
                "extracted": {
                    "core_skills": extracted.get("core_skills", []),
                    "languages": extracted.get("languages", []),
                    "tools_frameworks": extracted.get("tools_frameworks", []),
                    "key_responsibilities": extracted.get("key_responsibilities", []),
                },
                "qa": normalized_qa,
            }
        except Exception as e:
            logger.error(f"Interview Q&A generation failed: {str(e)}")
            return {"extracted": {"core_skills": [], "languages": [], "tools_frameworks": [], "key_responsibilities": []}, "qa": [], "error": str(e)}

    async def evaluate_resume_ats(self, resume_text: str) -> Dict[str, Any]:
        """AI-powered ATS evaluation for a single resume."""
        prompt = format_ai_prompt("resume_ats_evaluation", resume_text=resume_text)
        try:
            logger.info("Calling Groq API for ATS evaluation")
            result = await self.parse_json_response(prompt, max_tokens=4000)

            # Normalize numeric scores
            def clamp(v):
                if isinstance(v, (int, float)):
                    return max(0, min(100, float(v)))
                return 0.0

            structure = clamp(result.get("structure_score", result.get("structure", 0)))
            keyword = clamp(result.get("keyword_score", result.get("keyword", 0)))
            skills = clamp(result.get("skills_score", result.get("skills", 0)))
            readability = clamp(result.get("readability_score", result.get("readability", 0)))
            impact = clamp(result.get("impact_score", result.get("impact", 0)))
            overall = 0.25*structure + 0.25*keyword + 0.20*skills + 0.15*readability + 0.15*impact

            strengths = result.get("strengths") or []
            weaknesses = result.get("weaknesses") or result.get("recommendations") or []
            if not isinstance(strengths, list):
                strengths = [str(strengths)]
            if not isinstance(weaknesses, list):
                weaknesses = [str(weaknesses)]

            return {
                "structure_score": round(structure, 1),
                "keyword_score": round(keyword, 1),
                "skills_score": round(skills, 1),
                "readability_score": round(readability, 1),
                "impact_score": round(impact, 1),
                "overall_ats_score": round(overall, 1),
                "strengths": strengths[:5],
                "weaknesses": weaknesses[:8],
            }
        except Exception as e:
            logger.error(f"ATS evaluation AI failed: {str(e)}")
            return {"error": str(e)}

# Global instance
groq_service = GroqService()
