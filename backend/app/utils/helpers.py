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

    return list(skills)

def calculate_match_percentage(matching_items: List[str], total_items: List[str]) -> float:
    """Calculate match percentage between two lists"""
    if not total_items:
        return 0.0
    
    matching_count = len(set(matching_items) & set(total_items))
    return (matching_count / len(total_items)) * 100

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
        1. overall_match_score (0-100)
        2. skills_match_score (0-100)
        3. experience_match_score (0-100)
        4. missing_keywords: List of important keywords missing from resume
        5. matching_keywords: List of keywords that match
        6. suggestions: List of improvement suggestions
        
        Return only valid JSON.
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
        Generate interview questions based on this job description. Create questions for different categories.
        
        Job Description:
        {job_text}
        
        Provide JSON with categories:
        1. technical_questions: Technical/skill-based questions
        2. behavioral_questions: Behavioral/situational questions
        3. company_culture_questions: Company and culture questions
        4. leadership_questions: Leadership and management questions (if applicable)
        5. tips: Interview preparation tips
        
        Return only valid JSON.
        """
    }
    
    if prompt_type not in prompts:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    return prompts[prompt_type].format(**kwargs)
