"""
Helper utilities for JobAlign AI Backend
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import re
from pathlib import Path

def create_upload_directory(upload_dir: str) -> str:
    """Create upload directory if it doesn't exist"""
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    return upload_dir

def generate_unique_filename(original_filename: str, user_id: int) -> str:
    """Generate a unique filename for uploaded files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = Path(original_filename).suffix
    random_string = secrets.token_hex(8)
    
    return f"user_{user_id}_{timestamp}_{random_string}{file_extension}"

def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate if file type is allowed"""
    file_extension = Path(filename).suffix.lower()
    return file_extension in allowed_types

def validate_file_size(file_size: int, max_size: int) -> bool:
    """Validate if file size is within limits"""
    return file_size <= max_size

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal"""
    # Remove any path components
    filename = Path(filename).name
    # Remove special characters except dots and hyphens
    filename = re.sub(r'[^a-zA-Z0-9.\-_]', '_', filename)
    return filename

def extract_skills_from_text(text: str) -> List[str]:
    """Extract potential skills from text using simple regex patterns"""
    # Common skill patterns (expanded)
    skill_patterns = [
        r'\b(?:Python|Java|C\+\+|C#|Go|Ruby|PHP|TypeScript|JavaScript)\b',
        r'\b(?:React|Angular|Vue|Next\.js|Nuxt|Svelte|Redux|Tailwind|HTML|CSS|SASS)\b',
        r'\b(?:Node\.?js|Express|NestJS|Django|Flask|Spring|Spring Boot|Laravel|Rails)\b',
        r'\b(?:SQL|NoSQL|PostgreSQL|MySQL|SQLite|MongoDB|Redis|Elasticsearch|Kafka|RabbitMQ)\b',
        r'\b(?:AWS|Azure|GCP|CloudFormation|Terraform|Ansible|Docker|Kubernetes|Helm)\b',
        r'\b(?:REST|GraphQL|gRPC|WebSockets|API[s]?)\b',
        r'\b(?:CI/CD|Jenkins|GitHub Actions|GitLab CI|CircleCI|Travis)\b',
        r'\b(?:Machine Learning|Deep Learning|AI|Data Science|NLP|Computer Vision|Analytics|Statistics|TensorFlow|PyTorch|sklearn|NumPy|pandas)\b',
        r'\b(?:Project Management|Agile|Scrum|Kanban|Leadership|Communication|Stakeholder Management)\b',
        r'\b(?:Salesforce|SAP|Oracle|Tableau|Power BI|Looker|Snowflake|Databricks)\b',
        r'\b(?:Microservices|Event[- ]Driven|Domain[- ]Driven Design|DDD|TDD|BDD)\b',
    ]
    
    skills = set()
    for pattern in skill_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        skills.update(matches)
    # Normalize capitalization
    normalized = set()
    for s in skills:
        ss = s.strip()
        if not ss:
            continue
        # Keep common branding exact, otherwise title-case
        if ss.isupper() and len(ss) <= 5:
            normalized.add(ss)
        else:
            normalized.add(ss if any(ch.islower() for ch in ss) else ss.title())

    # Fallback: capture capitalized tech words separated by commas/slashes
    fallback_matches = re.findall(r'\b([A-Z][A-Za-z0-9+#\.\-]{2,})\b', text)
    for m in fallback_matches:
        if m.lower() not in {x.lower() for x in normalized} and len(normalized) < 100:
            normalized.add(m)

    return list(normalized)

def calculate_match_percentage(matching_items: List[str], total_items: List[str]) -> float:
    """Calculate match percentage between two lists"""
    if not total_items:
        return 0.0
    
    matching_count = len(set(matching_items) & set(total_items))
    return (matching_count / len(total_items)) * 100

def extract_years_of_experience(text: str) -> Optional[int]:
    """Extract an approximate years-of-experience number from text.
    Looks for patterns like '3 years', '5+ years', '7 yrs', '2-4 years'.
    Returns the maximum found to represent total/required years.
    """
    if not text:
        return None
    patterns = [
        r"(\d+)\s*\+?\s*(?:years|year|yrs|yr)",
        r"(\d+)\s*[-–]\s*(\d+)\s*(?:years|year|yrs|yr)",
    ]
    years: List[int] = []
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            try:
                if len(m.groups()) >= 2 and m.group(2):
                    years.append(max(int(m.group(1)), int(m.group(2))))
                else:
                    years.append(int(m.group(1)))
            except Exception:
                continue
    if not years:
        return None
    return max(y for y in years if y is not None)

def extract_role_tokens(text: str) -> List[str]:
    """Extract simple role/title tokens from text."""
    if not text:
        return []
    role_words = [
        "engineer", "developer", "manager", "lead", "architect", "analyst",
        "scientist", "consultant", "specialist", "admin", "administrator",
        "product", "program", "project", "designer", "devops", "sre",
        "frontend", "backend", "fullstack", "data", "ml", "ai", "qa", "test"
    ]
    tokens = set()
    lower = text.lower()
    for w in role_words:
        if w in lower:
            tokens.add(w)
    return list(tokens)

def extract_domain_keywords(text: str) -> List[str]:
    """Extract coarse domain keywords to estimate domain relevance."""
    if not text:
        return []
    domains = [
        "fintech", "healthcare", "ecommerce", "e-commerce", "retail", "logistics",
        "cloud", "saas", "banking", "insurance", "telecom", "education",
        "gaming", "media", "adtech", "security", "iot", "automotive"
    ]
    tokens = set()
    lower = text.lower()
    for d in domains:
        if d in lower:
            tokens.add(d)
    return list(tokens)

def format_currency(amount: int, currency: str = "USD") -> str:
    """Format currency amount for display"""
    return f"${amount / 100:.2f} {currency}"

def generate_job_hash(title: str, company: str, location: str) -> str:
    """Generate a hash for job deduplication"""
    content = f"{title.lower().strip()}|{company.lower().strip()}|{location.lower().strip()}"
    return hashlib.md5(content.encode()).hexdigest()

def parse_salary_range(salary_text: str) -> Dict[str, Any]:
    """Parse salary information from text"""
    if not salary_text:
        return {}
    
    # Extract numeric values
    numbers = re.findall(r'[\d,]+', salary_text.replace(',', ''))
    
    if len(numbers) >= 2:
        try:
            min_salary = int(numbers[0])
            max_salary = int(numbers[1])
            return {
                "min": min_salary,
                "max": max_salary,
                "currency": "USD",
                "period": "year"
            }
        except ValueError:
            pass
    
    return {"raw_text": salary_text}

def clean_text_for_ai(text: str) -> str:
    """Clean and prepare text for AI processing"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might confuse AI
    text = re.sub(r'[^\w\s.,!?()-]', '', text)
    
    # Limit length to prevent token overflow
    max_length = 8000  # Conservative limit for Groq API
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()

def format_ai_prompt(prompt_type: str, **kwargs) -> str:
    """Format prompts for different AI tasks"""
    
    prompts = {
        "resume_parsing": """
        Please analyze the following resume text and extract the following information in JSON format:
        
        1. Skills: List all technical and soft skills mentioned
        2. Experience: List all work experiences with company, position, duration
        3. Education: List all educational qualifications
        4. Certifications: List all certifications and licenses
        5. Achievements: List notable achievements and accomplishments
        
        Resume Text:
        {resume_text}
        
        Return only valid JSON with keys: skills, experience, education, certifications, achievements
        """,
        
        "job_parsing": """
        Please analyze the following job description and extract the following information in JSON format:
        
        1. Required Skills: List all technical and soft skills required
        2. Experience Requirements: List experience requirements and years needed
        3. Education Requirements: List educational requirements
        4. Certifications: List required certifications
        5. Job Details: Extract salary range, job type, seniority level, remote options
        
        Job Description:
        {job_text}
        
        Return only valid JSON with keys: required_skills, experience_requirements, education_requirements, certifications, job_details
        """,
        
        "match_scoring": """
        Please analyze the match between this resume and job description. Calculate a match score (0-100) and provide detailed analysis.
        
        Resume Text:
        {resume_text}
        
        Job Description:
        {job_text}
        
        Provide JSON with:
        1. overall_match_score (0-100): Overall compatibility score
        2. skills_match_score (0-100): How well resume skills match job requirements
        3. experience_match_score (0-100): How well resume experience matches job requirements
        4. keywords_match_score (0-100): Percentage of important keywords from JD found in resume
        5. missing_keywords: List of important keywords missing from resume (max 25)
        6. matching_keywords: List of keywords that match between resume and JD (max 25)
        7. suggestions: List of specific, actionable improvement suggestions (3-5 items)
        8. ats_findings: List of ATS (Applicant Tracking System) friendliness findings and recommendations (3-5 items)
        9. readability: List of readability and structure recommendations (3-5 items)
        10. strengths: List of resume strengths and highlights specific to this job (2-4 items)
        
        Be specific and actionable. Base scores on actual comparison between resume and job description.
        Return only valid JSON.
        """,
        "interview_tech_questions_only": """
        Read the following job description and output ONLY JSON with one key: technical_questions.
        The value must be a list of 10-15 concise technical questions tailored to the JD (tools, systems, domain).

        Job Description:
        {job_text}

        Output format example:
        {"technical_questions": ["Question 1", "Question 2", "..."]}
        """,
        
        "resume_optimization": """
        Based on the job description, optimize this resume to improve the match score. Provide:
        
        Original Resume:
        {resume_text}
        
        Target Job Description:
        {job_text}
        
        Provide JSON with:
        1. optimized_resume_text: The improved resume text
        2. changes_made: List of specific changes made
        3. keywords_added: List of keywords added
        4. improvements: List of improvements made
        
        Return only valid JSON.
        """,
        
        "interview_questions": """
        You are a senior interviewer. Read the job description and generate practical interview questions.
        
        Job Description:
        {job_text}
        
        Output STRICTLY valid JSON with these keys ONLY:
        - technical_questions: 10-15 concise, role-specific questions (focus on tools, systems, problem-solving). REQUIRED.
        - behavioral_questions: 3-5 questions (use STAR-friendly prompts). REQUIRED.
        - company_culture_questions: 3-4 questions tailored to the org/team context. REQUIRED.
        - leadership_questions: 2-4 questions IF the role implies senior/lead/manager; otherwise return an empty list.
        - tips: 3-5 short preparation tips.
        
        Rules:
        - Base questions on the actual job text (skills, stack, domain). Do NOT return empty lists unless truly no context exists.
        - Questions must be strings only; avoid numbering or extra formatting.
        - Keep each question under 22 words.
        
        Return only valid JSON.
        """
        ,
        "interview_qa_from_jd": """
        You are a senior interviewer. Read the job description and produce targeted interview preparation.

        Job Description:
        {job_text}

        Requirements:
        1) Extract these lists from the JD:
           - core_skills (technical competencies)
           - languages (programming/query)
           - tools_frameworks
           - key_responsibilities
        2) Generate 10–15 technical interview questions grounded in the JD.
        3) For each question, provide a short, high-quality sample answer that demonstrates hands-on understanding using correct technical terms and realistic project context.
        4) If the JD is specialized (Data Science/AI/Cloud/etc.), ensure questions reflect that domain.

        Output STRICTLY valid JSON with keys:
        - extracted: {"core_skills":[], "languages":[], "tools_frameworks":[], "key_responsibilities":[]}
        - qa: [{"question":"...","sample_answer":"..."}]   // 10–15 entries

        Rules:
        - All strings should be concise and practical (answers 2–6 sentences).
        - No markdown, numbering, or extra commentary outside JSON.
        """,
        "resume_ats_evaluation": """
        You are an expert ATS evaluator. Analyze the following single resume and score it STRICTLY by this rubric.

        Scoring Breakdown (0-100 each):
        - Structure & Formatting (25%): Clear section headings (Summary, Skills, Experience, Education, Projects). No tables, columns, or graphics.
        - Keyword Coverage (25%): Uses action-oriented, professional, and technical terms (e.g., implemented, optimized, analysis, leadership, teamwork, Python, SQL).
        - Skill Presentation (20%): Skills are clearly listed and reflected in the experience section.
        - Readability (15%): Sentences are concise, grammatically correct, and use consistent bullets.
        - Achievements & Metrics (15%): Presence of quantifiable results, impact statements, or metrics.

        Overall ATS Score formula:
        overall = 0.25*structure + 0.25*keyword + 0.20*skills + 0.15*readability + 0.15*impact

        Output Requirements:
        - Return ONLY valid JSON with the following keys exactly:
          structure_score, keyword_score, skills_score, readability_score, impact_score, overall_ats_score, strengths, weaknesses
        - All scores must be numbers between 0 and 100 (no strings). Do not default to 50; base scores on evidence in the resume text.
        - strengths: 2-3 concise, resume-specific positives (no generic fluff)
        - weaknesses: 3-5 specific, actionable improvements tailored to the resume

        Resume Text:
        {resume_text}

        Return only valid JSON.
        """
    }
    
    if prompt_type not in prompts:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    return prompts[prompt_type].format(**kwargs)
