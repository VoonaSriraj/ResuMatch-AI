import requests
import json
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.enhanced_job_service import EnhancedJobService
from app.services.adzuna_service import AdzunaJobService
from app.utils.logger import get_logger

logger = get_logger(__name__)

class JobService:
    def __init__(self):
        self.rapidapi_key = getattr(settings, 'rapidapi_key', None)
        self.rapidapi_linkedin_host = getattr(settings, 'rapidapi_linkedin_host', "linkedin-job-search-api.p.rapidapi.com")
        # Use the provided API key if no environment variable is set
        if not self.rapidapi_key:
            self.rapidapi_key = "7aa7aa52d9msha1eb98867149d10p12f163jsn05c83f56e494"
    
    async def fetch_jobs_from_rapidapi(self, keywords: List[str] = None, location: str = None, limit: int = 25) -> List[Dict[str, Any]]:
        """Fetch jobs from multiple sources including Adzuna API and fallbacks"""
        try:
            # Primary: Try Adzuna API for real-time jobs
            adzuna_service = AdzunaJobService()
            adzuna_jobs = await adzuna_service.search_jobs(keywords, location, limit)
            
            if adzuna_jobs:
                logger.info(f"Adzuna API returned {len(adzuna_jobs)} real-time jobs")
                return adzuna_jobs
            
            # Fallback: Use enhanced job service
            logger.info("Adzuna API failed, trying enhanced job service...")
            enhanced_service = EnhancedJobService()
            jobs = await enhanced_service.fetch_real_time_jobs(keywords, location, limit)
            
            if jobs:
                logger.info(f"Enhanced job service returned {len(jobs)} jobs")
                return jobs
            else:
                logger.warning("No jobs found, falling back to basic mock data")
                return self._get_mock_job_data(keywords, location, limit)
                    
        except Exception as e:
            logger.error(f"Error fetching real-time jobs: {str(e)}")
            return self._get_mock_job_data(keywords, location, limit)
    
    async def _try_rapidapi(self, keywords: List[str] = None, location: str = None, limit: int = 25) -> List[Dict[str, Any]]:
        """Try to fetch jobs from RapidAPI"""
        if not self.rapidapi_key:
            return []
        
        try:
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "linkedin-job-search-api.p.rapidapi.com"
            }
            
            # Build query parameters
            params = {
                "offset": 0,
                "description_type": "text"
            }
            
            # Add keyword filtering if provided
            if keywords:
                params["keywords"] = ",".join(keywords)
            
            # Add location filtering if provided
            if location:
                params["location"] = location
            
            logger.info(f"Trying RapidAPI with params: {params}")
            
            response = requests.get(
                "https://linkedin-job-search-api.p.rapidapi.com/active-jb-1h",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('jobs', [])
                
                if jobs:
                    formatted_jobs = self._format_rapidapi_jobs(jobs[:limit])
                    logger.info(f"RapidAPI successfully returned {len(formatted_jobs)} jobs")
                    return formatted_jobs
            
            logger.warning(f"RapidAPI failed with status {response.status_code}: {response.text}")
            return []
                
        except Exception as e:
            logger.warning(f"RapidAPI error: {str(e)}")
            return []
    
    def _format_rapidapi_jobs(self, jobs: List[Dict]) -> List[Dict[str, Any]]:
        """Format RapidAPI job data to our standard format"""
        formatted_jobs = []
        for job in jobs:
            # Extract and clean job data
            title = job.get("title", "").strip()
            company = job.get("company", "").strip()
            location = job.get("location", "").strip()
            description = job.get("description", "").strip()
            
            # Extract LinkedIn URL
            linkedin_url = job.get("apply_url", "") or job.get("linkedin_url", "")
            
            # Extract job ID
            job_id = job.get("job_id", "") or job.get("id", "")
            
            # Determine job type and seniority level from title/description
            job_type = self._extract_job_type(title, description)
            seniority_level = self._extract_seniority_level(title, description)
            
            # Extract skills from description if not provided
            skills = job.get("skills", [])
            if not skills and description:
                skills = self._extract_skills_from_description(description)
            
            formatted_jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "linkedin_url": linkedin_url,
                "apply_url": linkedin_url,  # For compatibility
                "linkedin_job_id": job_id,
                "posted_date": job.get("posted_date"),
                "job_type": job_type,
                "seniority_level": seniority_level,
                "employment_type": job.get("employment_type", "full-time"),
                "salary_range": job.get("salary_range"),
                "remote_friendly": self._extract_remote_status(title, description),
                "skills": skills
            })
        return formatted_jobs
    
    def _extract_job_type(self, title: str, description: str) -> str:
        """Extract job type from title and description"""
        text = f"{title} {description}".lower()
        if any(word in text for word in ["intern", "internship"]):
            return "internship"
        elif any(word in text for word in ["contract", "contractor", "freelance"]):
            return "contract"
        elif any(word in text for word in ["part-time", "part time"]):
            return "part-time"
        else:
            return "full-time"
    
    def _extract_seniority_level(self, title: str, description: str) -> str:
        """Extract seniority level from title and description"""
        text = f"{title} {description}".lower()
        if any(word in text for word in ["senior", "lead", "principal", "staff", "architect"]):
            return "senior"
        elif any(word in text for word in ["junior", "entry", "graduate", "trainee"]):
            return "entry"
        else:
            return "mid"
    
    def _extract_remote_status(self, title: str, description: str) -> str:
        """Extract remote work status from title and description"""
        text = f"{title} {description}".lower()
        if any(word in text for word in ["remote", "work from home", "wfh"]):
            return "remote"
        elif any(word in text for word in ["hybrid", "flexible"]):
            return "hybrid"
        else:
            return "on-site"
    
    def _extract_skills_from_description(self, description: str) -> List[str]:
        """Extract common technical skills from job description"""
        common_skills = [
            "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "Swift", "Kotlin",
            "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask", "FastAPI",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "Git",
            "Machine Learning", "AI", "TensorFlow", "PyTorch", "scikit-learn",
            "Data Science", "Analytics", "Tableau", "Power BI",
            "DevOps", "CI/CD", "Terraform", "Ansible", "Linux", "Bash"
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in common_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)
        
        return found_skills[:10]  # Limit to top 10 skills
    
    def _get_mock_job_data(self, keywords: List[str] = None, location: str = None, limit: int = 25) -> List[Dict[str, Any]]:
        """Generate realistic mock job data"""
        job_templates = [
            {
                "title": "Senior Software Engineer",
                "description": "We are looking for a Senior Software Engineer to join our development team. You will be responsible for designing, developing, and maintaining software applications using modern programming languages and frameworks. Experience with Python, JavaScript, React, Node.js, and database technologies is required. You should have 5+ years of experience in software development.",
                "company": "TechCorp Solutions",
                "skills": ["Python", "JavaScript", "React", "Node.js", "SQL", "Git", "AWS"]
            },
            {
                "title": "Data Scientist",
                "description": "Join our data science team to analyze complex datasets and build machine learning models. You will work with Python, R, SQL, and various ML frameworks. Strong background in statistics, machine learning algorithms, and data visualization required. Experience with TensorFlow, PyTorch, or scikit-learn preferred.",
                "company": "DataFlow Inc",
                "skills": ["Python", "R", "SQL", "Machine Learning", "Statistics", "TensorFlow", "Pandas"]
            },
            {
                "title": "Full Stack Developer",
                "description": "We need a Full Stack Developer to build end-to-end web applications. You will work with frontend technologies like React/Vue.js and backend technologies like Node.js/Python. Experience with cloud platforms and DevOps practices is a plus. Knowledge of Docker, Kubernetes, and CI/CD pipelines preferred.",
                "company": "WebTech Solutions",
                "skills": ["React", "Node.js", "Python", "AWS", "Docker", "Kubernetes", "JavaScript"]
            },
            {
                "title": "DevOps Engineer",
                "description": "Looking for a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines. You will work with AWS/Azure, Docker, Kubernetes, and automation tools. Strong scripting skills in Python/Bash required. Experience with Terraform, Ansible, or similar infrastructure-as-code tools preferred.",
                "company": "CloudScale Technologies",
                "skills": ["AWS", "Docker", "Kubernetes", "Python", "Jenkins", "Terraform", "Bash"]
            },
            {
                "title": "Product Manager",
                "description": "We are seeking a Product Manager to drive product strategy and work with cross-functional teams. You will define product requirements, work with engineering teams, and analyze user data. Technical background and experience with agile methodologies required. Experience with analytics tools and user research preferred.",
                "company": "ProductVision Corp",
                "skills": ["Product Management", "Agile", "Analytics", "User Research", "Strategy", "Jira", "Figma"]
            },
            {
                "title": "Machine Learning Engineer",
                "description": "Join our ML team to build and deploy machine learning models at scale. You will work with Python, TensorFlow, PyTorch, and cloud ML platforms. Experience with MLOps, model deployment, and production systems required. Knowledge of distributed computing and big data technologies preferred.",
                "company": "AI Innovations",
                "skills": ["Python", "TensorFlow", "PyTorch", "MLOps", "AWS", "Docker", "Kubernetes"]
            },
            {
                "title": "Frontend Developer",
                "description": "We are looking for a Frontend Developer to create beautiful and responsive user interfaces. You will work with React, TypeScript, CSS, and modern frontend tools. Experience with state management libraries like Redux or Zustand preferred. Knowledge of testing frameworks and performance optimization required.",
                "company": "UI Design Studio",
                "skills": ["React", "TypeScript", "CSS", "Redux", "Jest", "Webpack", "Figma"]
            },
            {
                "title": "Backend Developer",
                "description": "Looking for a Backend Developer to build scalable APIs and microservices. You will work with Python, FastAPI, PostgreSQL, and cloud services. Experience with database design, API development, and system architecture required. Knowledge of message queues and caching systems preferred.",
                "company": "API Solutions",
                "skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Celery", "Docker", "AWS"]
            }
        ]
        
        mock_jobs = []
        for i in range(min(limit, 25)):
            template = job_templates[i % len(job_templates)]
            mock_jobs.append({
                "linkedin_job_id": f"mock_job_{i}",
                "title": template["title"],
                "company": template["company"],
                "location": location or f"San Francisco, CA" if i % 3 == 0 else f"New York, NY" if i % 3 == 1 else f"Remote",
                "description": template["description"],
                "apply_url": f"https://www.linkedin.com/jobs/view/{3000000000 + i}",
                "posted_date": None,
                "job_type": ["remote", "hybrid", "on-site"][i % 3],
                "seniority_level": ["entry", "mid", "senior"][i % 3],
                "employment_type": "full-time",
                "salary_range": f"${80000 + i*5000}-${120000 + i*5000}",
                "skills": template["skills"]
            })
        
        return mock_jobs
