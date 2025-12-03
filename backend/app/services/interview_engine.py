"""
Interview preparation service for generating AI-powered interview questions
"""

from typing import Dict, Any, List, Optional
import asyncio
from app.services.groq_service import groq_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

class InterviewEngineService:
    def __init__(self):
        pass
    
    async def generate_interview_questions(
        self, 
        job_text: str,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        seniority_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive interview questions based on job description"""
        try:
            # Generate base questions using AI
            questions_data = await groq_service.generate_interview_questions(job_text)

            # Normalize: coerce any list of dicts (with 'question'/'tip') into list of strings
            def to_string_list(items):
                if not isinstance(items, list):
                    return []
                out: List[str] = []
                for item in items:
                    if isinstance(item, str):
                        out.append(item)
                    elif isinstance(item, dict):
                        # Prefer 'question' key, fallback to 'tip' or stringify
                        if 'question' in item and isinstance(item['question'], str):
                            out.append(item['question'])
                        elif 'tip' in item and isinstance(item['tip'], str):
                            out.append(item['tip'])
                        else:
                            out.append(str(item))
                return out

            normalized = {
                "technical_questions": to_string_list(questions_data.get("technical_questions", [])),
                "behavioral_questions": to_string_list(questions_data.get("behavioral_questions", [])),
                "company_culture_questions": to_string_list(questions_data.get("company_culture_questions", [])),
                "leadership_questions": to_string_list(questions_data.get("leadership_questions", [])),
                "industry_questions": to_string_list(questions_data.get("industry_questions", [])),
                "tips": to_string_list(questions_data.get("tips", [])),
            }

            # Fallbacks when AI returns sparse results
            if not normalized["technical_questions"]:
                # Rely on Groq service's enriched fallbacks (skills-derived) already applied
                normalized["technical_questions"] = []
            if not normalized["behavioral_questions"]:
                normalized["behavioral_questions"] = [
                    "Tell me about a time you handled a difficult stakeholder.",
                    "Describe a failure. What did you learn and change?",
                    "Give an example of leading without authority."
                ]
            if not normalized["company_culture_questions"]:
                normalized["company_culture_questions"] = [
                    "What about our mission and products resonates with you?",
                    "How do you prefer to receive and give feedback?",
                    "What environment helps you do your best work?"
                ]
            
            # Enhance with additional contextual questions
            enhanced_questions = self._enhance_questions(
                normalized, job_title, company, seniority_level
            )
            
            # Add preparation tips
            preparation_tips = self._generate_preparation_tips(job_title, company, seniority_level)
            
            return {
                "technical_questions": enhanced_questions["technical_questions"],
                "behavioral_questions": enhanced_questions["behavioral_questions"],
                "company_culture_questions": enhanced_questions["company_culture_questions"],
                "leadership_questions": enhanced_questions["leadership_questions"],
                "industry_questions": enhanced_questions.get("industry_questions", []),
                "preparation_tips": preparation_tips,
                "ai_tips": normalized.get("tips", []),
                "job_context": {
                    "job_title": job_title,
                    "company": company,
                    "seniority_level": seniority_level
                },
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Interview questions generation failed: {str(e)}")
            return {
                "technical_questions": [],
                "behavioral_questions": [],
                "company_culture_questions": [],
                "leadership_questions": [],
                "industry_questions": [],
                "preparation_tips": [],
                "ai_tips": [],
                "job_context": {
                    "job_title": job_title,
                    "company": company,
                    "seniority_level": seniority_level
                },
                "processing_status": "failed",
                "error": str(e)
            }

    async def generate_qa_from_jd(
        self,
        job_text: str,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        seniority_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate 10–15 Q&A pairs based on a JD and extract skills"""
        try:
            result = await groq_service.generate_interview_qa(job_text)
            qa = result.get("qa", [])
            extracted = result.get("extracted", {})
            # Ensure minimum of 10 by adding generic but useful prompts if needed
            while len(qa) < 10:
                fillers = [
                    {"question": "Describe a recent project aligned with this JD.", "sample_answer": "I led ... focusing on ... resulting in ..."},
                    {"question": "How do you ensure code quality and reliability?", "sample_answer": "I use tests (unit/integration), code reviews, and CI checks ..."},
                    {"question": "How did you optimize performance in a critical path?", "sample_answer": "Profiled with ..., identified bottleneck in ..., improved by ...%"}
                ]
                for f in fillers:
                    if len(qa) >= 10:
                        break
                    qa.append(f)
            return {
                "qa": qa[:15],
                "extracted": extracted,
                "job_context": {"job_title": job_title, "company": company, "seniority_level": seniority_level},
                "processing_status": "completed"
            }
        except Exception as e:
            logger.error(f"Q&A generation failed: {str(e)}")
            return {"qa": [], "extracted": {"core_skills": [], "languages": [], "tools_frameworks": [], "key_responsibilities": []}, "processing_status": "failed", "error": str(e)}

    async def generate_questions_with_answers(
        self,
        job_text: str,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        seniority_level: Optional[str] = None,
        limit: int = 12,
        job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate technical interview questions along with AI-generated answers in one call."""
        try:
            logger.info(f"Starting to generate questions with answers for job_id: {job_id}")
            
            # First get the questions
            qres = await self.generate_interview_questions(
                job_text=job_text,
                job_title=job_title,
                company=company,
                seniority_level=seniority_level,
            )
            
            # Get questions from all categories
            questions: List[str] = []
            for category in ["technical_questions", "industry_questions", 
                           "leadership_questions", "company_culture_questions", 
                           "behavioral_questions"]:
                questions.extend(qres.get(category, [])[:limit])
                if len(questions) >= limit:
                    questions = questions[:limit]
                    break
            
            # If still no questions, use fallback questions
            if not questions:
                questions = [
                    "Tell me about yourself and your experience.",
                    "What interests you about this position?",
                    "What are your strengths and weaknesses?",
                    "Describe a challenging project you worked on.",
                    "How do you handle tight deadlines?"
                ][:limit]
            
            logger.info(f"Generated {len(questions)} questions, now generating answers...")

            async def build(q: str) -> Dict[str, Any]:
                try:
                    # Generate answer for the question
                    ans = await self.generate_answer_suggestions(
                        question=q,
                        user_experience="",
                        job_context={
                            "job_title": job_title,
                            "company": company,
                            "seniority_level": seniority_level,
                            "job_text": job_text[:1000]  # Send first 1000 chars for context
                        },
                        job_text=job_text,
                    )
                    
                    # Create a comprehensive answer by combining structure and key points
                    answer_structure = ans.get("answer_structure", "")
                    key_points = ans.get("key_points", [])
                    tailoring_tips = ans.get("tailoring_tips", [])
                    
                    # Create a paragraph combining structure and top 3 key points
                    answer_paragraph = answer_structure
                    if key_points:
                        answer_paragraph += " " + " ".join(key_points[:3])
                    
                    return {
                        "question": q,
                        "key_points": key_points[:5],  # Limit to top 5 key points
                        "tailoring_tips": tailoring_tips[:3],  # Limit to top 3 tips
                        "answer_text": answer_paragraph.strip(),
                        "answer_structure": answer_structure,
                        "processing_status": "completed"
                    }
                except Exception as e:
                    logger.error(f"Error generating answer for question '{q}': {str(e)}")
                    return {
                        "question": q,
                        "key_points": [],
                        "tailoring_tips": [],
                        "answer_text": "",
                        "answer_structure": "",
                        "processing_status": "failed",
                        "error": str(e)
                    }

            # Process questions in batches to avoid rate limiting
            batch_size = 3
            results: List[Dict[str, Any]] = []
            
            for i in range(0, len(questions), batch_size):
                batch = questions[i:i+batch_size]
                batch_results = await asyncio.gather(
                    *(build(q) for q in batch),
                    return_exceptions=True
                )
                
                # Process batch results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Error in batch processing: {str(result)}")
                        continue
                    results.append(result)
                
                # Add a small delay between batches
                if i + batch_size < len(questions):
                    await asyncio.sleep(1)
            
            logger.info(f"Successfully generated answers for {len(results)} questions")
            
            return {
                "items": results,
                "job_context": {
                    "job_title": job_title,
                    "company": company,
                    "seniority_level": seniority_level,
                    "job_text": job_text[:500] + "..." if job_text else ""
                },
                "processing_status": "completed"
            }
        except Exception as e:
            logger.error(f"Questions-with-answers generation failed: {str(e)}")
            return {"items": [], "processing_status": "failed", "error": str(e)}
    
    async def generate_follow_up_questions(
        self, 
        question: str, 
        job_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate follow-up questions for a specific interview question"""
        try:
            prompt = f"""
            Generate 3-5 follow-up questions for this interview question:
            
            Main Question: {question}
            
            Job Context:
            - Title: {job_context.get('job_title', 'Not specified')}
            - Company: {job_context.get('company', 'Not specified')}
            - Seniority: {job_context.get('seniority_level', 'Not specified')}
            
            Provide follow-up questions that would help the interviewer dive deeper into the candidate's experience and qualifications.
            Return as JSON with key "follow_up_questions" containing a list of questions.
            """
            
            result = await groq_service.parse_json_response(prompt)
            
            return {
                "follow_up_questions": result.get("follow_up_questions", []),
                "original_question": question,
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Follow-up questions generation failed: {str(e)}")
            return {
                "follow_up_questions": [],
                "original_question": question,
                "processing_status": "failed",
                "error": str(e)
            }
    
    async def generate_answer_suggestions(
        self, 
        question: str, 
        user_experience: str,
        job_context: Dict[str, Any],
        job_text: str = ""
    ) -> Dict[str, Any]:
        """Generate answer suggestions for interview questions based on user experience"""
        try:
            prompt = f"""
            Generate answer suggestions for this interview question.
            
            Question: {question}
            
            Job Description:
            {job_text}
            
            Candidate Background (if provided):
            {user_experience}
            
            Job Context:
            - Title: {job_context.get('job_title', 'Not specified')}
            - Company: {job_context.get('company', 'Not specified')}
            - Seniority: {job_context.get('seniority_level', 'Not specified')}
            
            Provide JSON with:
            - structure: brief outline (prefer STAR where applicable)
            - key_points: 4-6 bullet ideas grounded in the JD
            - avoid_points: 2-3 pitfalls to avoid
            - tailoring_tips: 3-5 ways to tailor the answer for this role/company
            """
            
            result = await groq_service.parse_json_response(prompt)
            
            return {
                "answer_structure": result.get("structure", ""),
                "key_points": result.get("key_points", []),
                "avoid_points": result.get("avoid_points", []),
                "tailoring_tips": result.get("tailoring_tips", []),
                "question": question,
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Answer suggestions generation failed: {str(e)}")
            return {
                "answer_structure": "",
                "key_points": [],
                "avoid_points": [],
                "tailoring_tips": [],
                "question": question,
                "processing_status": "failed",
                "error": str(e)
            }
    
    def _enhance_questions(
        self, 
        base_questions: Dict[str, Any], 
        job_title: Optional[str],
        company: Optional[str],
        seniority_level: Optional[str]
    ) -> Dict[str, Any]:
        """Enhance questions with contextual additions"""
        enhanced = {
            "technical_questions": base_questions.get("technical_questions", [])[:],
            "behavioral_questions": base_questions.get("behavioral_questions", [])[:],
            "company_culture_questions": base_questions.get("company_culture_questions", [])[:],
            "leadership_questions": base_questions.get("leadership_questions", [])[:],
            "industry_questions": base_questions.get("industry_questions", [])[:],
        }
        
        # Add industry-specific questions based on job title
        if job_title:
            industry_questions = self._get_industry_questions(job_title)
            enhanced["industry_questions"] = industry_questions
        
        # Add company-specific questions
        if company:
            company_questions = self._get_company_questions(company)
            enhanced["company_culture_questions"].extend(company_questions)
        
        # Add seniority-specific questions
        if seniority_level:
            seniority_questions = self._get_seniority_questions(seniority_level)
            if seniority_level.lower() in ["senior", "lead", "principal", "director", "manager"]:
                enhanced["leadership_questions"].extend(seniority_questions)
            else:
                enhanced["behavioral_questions"].extend(seniority_questions)
        
        return enhanced
    
    def _get_industry_questions(self, job_title: str) -> List[str]:
        """Get industry-specific questions based on job title"""
        title_lower = job_title.lower()
        
        industry_questions = {
            "software": [
                "How do you stay updated with the latest programming languages and frameworks?",
                "Describe your experience with version control and collaborative development.",
                "How do you approach debugging complex software issues?"
            ],
            "data": [
                "How do you ensure data quality and integrity in your analysis?",
                "Describe your experience with different data visualization tools.",
                "How do you handle missing or incomplete data in your datasets?"
            ],
            "marketing": [
                "How do you measure the success of a marketing campaign?",
                "Describe your experience with different marketing automation platforms.",
                "How do you stay updated with changing consumer behavior and trends?"
            ],
            "sales": [
                "How do you handle objections from potential customers?",
                "Describe your approach to building long-term customer relationships.",
                "How do you qualify leads and prioritize your sales efforts?"
            ]
        }
        
        # Match job title to industry
        for industry, questions in industry_questions.items():
            if any(keyword in title_lower for keyword in [industry, "engineer", "analyst", "specialist"]):
                return questions
        
        return []
    
    def _get_company_questions(self, company: str) -> List[str]:
        """Get company-specific questions"""
        # This could be enhanced with company research API integration
        return [
            f"What do you know about {company}'s mission and values?",
            f"How would you contribute to {company}'s company culture?",
            f"What interests you most about working at {company}?"
        ]
    
    def _get_seniority_questions(self, seniority_level: str) -> List[str]:
        """Get seniority-specific questions"""
        seniority_lower = seniority_level.lower()
        
        if seniority_lower in ["senior", "lead", "principal"]:
            return [
                "How do you mentor junior team members?",
                "Describe a time when you had to make a difficult technical decision.",
                "How do you balance technical debt with feature development?"
            ]
        elif seniority_lower in ["manager", "director", "head"]:
            return [
                "How do you handle conflicts within your team?",
                "Describe your approach to performance management.",
                "How do you balance team productivity with individual growth?"
            ]
        else:
            return [
                "How do you prioritize your learning and professional development?",
                "Describe a time when you had to learn something new quickly.",
                "How do you handle feedback and incorporate it into your work?"
            ]
    
    def _generate_preparation_tips(
        self, 
        job_title: Optional[str],
        company: Optional[str],
        seniority_level: Optional[str]
    ) -> List[str]:
        """Generate preparation tips for the interview"""
        tips = [
            "Research the company's recent news, products, and company culture",
            "Prepare specific examples using the STAR method (Situation, Task, Action, Result)",
            "Practice explaining your experience and achievements clearly",
            "Prepare thoughtful questions to ask the interviewer",
            "Dress appropriately for the company culture",
            "Arrive 10-15 minutes early",
            "Bring multiple copies of your resume",
            "Prepare to discuss your career goals and motivation for this role"
        ]
        
        if job_title:
            tips.append(f"Research the latest trends and technologies in {job_title} field")
        
        if company:
            tips.append(f"Look up {company}'s competitors and market position")
        
        if seniority_level and seniority_level.lower() in ["senior", "lead", "manager"]:
            tips.extend([
                "Prepare examples of leadership and team management",
                "Be ready to discuss your strategic thinking and decision-making process"
            ])
        
        return tips

# Global instance
interview_engine_service = InterviewEngineService()
