"""
Adzuna Job Search API Service
Production-ready service for fetching real-time jobs from Adzuna API for India
"""

import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AdzunaJobService:
    """
    Adzuna Job Search API Service
    
    This service provides real-time job search functionality using the Adzuna API
    specifically configured for India. It handles API requests, error management,
    and data formatting for production use.
    """
    
    def __init__(self):
        """Initialize the Adzuna service with API credentials"""
        self.app_id = settings.adzuna_app_id
        self.app_key = settings.adzuna_app_key
        self.country = settings.adzuna_country
        self.base_url = f"https://api.adzuna.com/v1/api/jobs/{self.country}/search/1"
        
        # Validate credentials
        if not self.app_id or not self.app_key:
            logger.warning("Adzuna API credentials not properly configured")
    
    async def search_jobs(
        self, 
        keywords: Optional[List[str]] = None, 
        location: Optional[str] = None, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs using Adzuna API
        
        Args:
            keywords: List of search keywords (e.g., ['Python', 'Software Engineer'])
            location: Location filter (e.g., 'Mumbai', 'Bangalore', 'Delhi')
            limit: Maximum number of jobs to return (default: 10)
            
        Returns:
            List of formatted job dictionaries
            
        Raises:
            Exception: If API request fails or returns invalid data
        """
        try:
            # Prepare search parameters
            search_params = self._prepare_search_params(keywords, location, limit)
            
            logger.info(f"Searching Adzuna API with params: {search_params}")
            
            # Make API request
            response = requests.get(
                self.base_url,
                params=search_params,
                timeout=30  # 30 second timeout for production
            )
            
            # Handle response
            if response.status_code == 200:
                return self._process_successful_response(response.json(), limit)
            elif response.status_code == 401:
                logger.error("Adzuna API authentication failed - check credentials")
                raise Exception("Invalid API credentials")
            elif response.status_code == 403:
                logger.error("Adzuna API access forbidden - check subscription")
                raise Exception("API access forbidden")
            elif response.status_code == 429:
                logger.error("Adzuna API rate limit exceeded")
                raise Exception("API rate limit exceeded")
            else:
                logger.error(f"Adzuna API request failed with status {response.status_code}: {response.text}")
                raise Exception(f"API request failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error("Adzuna API request timed out")
            raise Exception("API request timed out")
        except requests.exceptions.ConnectionError:
            logger.error("Adzuna API connection error")
            raise Exception("Network connection error")
        except requests.exceptions.RequestException as e:
            logger.error(f"Adzuna API request error: {str(e)}")
            raise Exception(f"API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Adzuna job search: {str(e)}")
            raise Exception(f"Job search failed: {str(e)}")
    
    def _prepare_search_params(
        self, 
        keywords: Optional[List[str]], 
        location: Optional[str], 
        limit: int
    ) -> Dict[str, Any]:
        """
        Prepare search parameters for Adzuna API
        
        Args:
            keywords: List of search keywords
            location: Location filter
            limit: Maximum number of results
            
        Returns:
            Dictionary of API parameters
        """
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": min(limit, 50),  # Adzuna max is 50 per page
            "what": " ".join(keywords) if keywords else "software engineer",
            "where": location or "India",
            "sort_by": "relevance",  # Sort by relevance for better results
            "content-type": "application/json"
        }
        
        return params
    
    def _process_successful_response(self, response_data: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        Process successful API response and format job data
        
        Args:
            response_data: Raw API response data
            limit: Maximum number of jobs to return
            
        Returns:
            List of formatted job dictionaries
        """
        try:
            jobs = response_data.get('results', [])
            logger.info(f"Adzuna API returned {len(jobs)} jobs")
            
            if not jobs:
                logger.warning("No jobs found in Adzuna API response")
                return []
            
            # Format jobs for our application
            formatted_jobs = []
            for job in jobs[:limit]:
                formatted_job = self._format_job_data(job)
                if formatted_job:
                    formatted_jobs.append(formatted_job)
            
            logger.info(f"Successfully formatted {len(formatted_jobs)} jobs")
            return formatted_jobs
            
        except Exception as e:
            logger.error(f"Error processing Adzuna API response: {str(e)}")
            raise Exception(f"Failed to process API response: {str(e)}")
    
    def _format_job_data(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Format individual job data from Adzuna API response
        
        Args:
            job: Raw job data from API
            
        Returns:
            Formatted job dictionary or None if invalid
        """
        try:
            # Extract basic job information
            title = job.get('title', '').strip()
            company = job.get('company', {}).get('display_name', '').strip()
            location = job.get('location', {}).get('display_name', '').strip()
            description = job.get('description', '').strip()
            redirect_url = job.get('redirect_url', '')
            
            # Skip jobs with missing essential data
            if not title or not company:
                logger.warning(f"Skipping job with missing title or company: {job.get('id', 'unknown')}")
                return None
            
            # Extract salary information
            salary_min = job.get('salary_min')
            salary_max = job.get('salary_max')
            salary_range = self._format_salary_range(salary_min, salary_max)
            
            # Extract additional job details
            job_type = job.get('contract_type', 'full-time')
            posted_date = job.get('created')
            
            # Format the job data
            formatted_job = {
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "salary_range": salary_range,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "apply_url": redirect_url,
                "job_type": job_type,
                "posted_date": posted_date,
                "source": "adzuna",
                "job_id": job.get('id', ''),
                "seniority_level": self._extract_seniority_level(title),
                "remote_friendly": self._extract_remote_status(title, description),
                "skills_required": self._extract_skills_from_description(description)
            }
            
            return formatted_job
            
        except Exception as e:
            logger.error(f"Error formatting job data: {str(e)}")
            return None
    
    def _format_salary_range(self, salary_min: Optional[float], salary_max: Optional[float]) -> Optional[str]:
        """
        Format salary range for display
        
        Args:
            salary_min: Minimum salary
            salary_max: Maximum salary
            
        Returns:
            Formatted salary range string or None
        """
        if salary_min is None and salary_max is None:
            return None
        
        if salary_min is None:
            return f"Up to ₹{salary_max:,.0f}"
        elif salary_max is None:
            return f"₹{salary_min:,.0f}+"
        else:
            return f"₹{salary_min:,.0f} - ₹{salary_max:,.0f}"
    
    def _extract_seniority_level(self, title: str) -> str:
        """
        Extract seniority level from job title
        
        Args:
            title: Job title
            
        Returns:
            Seniority level (entry, mid, senior)
        """
        title_lower = title.lower()
        
        if any(word in title_lower for word in ["senior", "lead", "principal", "staff", "architect", "manager"]):
            return "senior"
        elif any(word in title_lower for word in ["junior", "entry", "graduate", "trainee", "associate"]):
            return "entry"
        else:
            return "mid"
    
    def _extract_remote_status(self, title: str, description: str) -> str:
        """
        Extract remote work status from title and description
        
        Args:
            title: Job title
            description: Job description
            
        Returns:
            Remote status (remote, hybrid, on-site)
        """
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ["remote", "work from home", "wfh", "virtual"]):
            return "remote"
        elif any(word in text for word in ["hybrid", "flexible", "part remote"]):
            return "hybrid"
        else:
            return "on-site"
    
    def _extract_skills_from_description(self, description: str) -> List[str]:
        """
        Extract technical skills from job description
        
        Args:
            description: Job description text
            
        Returns:
            List of extracted skills
        """
        # Common technical skills for Indian job market
        common_skills = [
            "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "Swift", "Kotlin",
            "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask", "FastAPI",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "Git",
            "Machine Learning", "AI", "TensorFlow", "PyTorch", "scikit-learn",
            "Data Science", "Analytics", "Tableau", "Power BI",
            "DevOps", "CI/CD", "Terraform", "Ansible", "Linux", "Bash",
            "Spring Boot", "Hibernate", "Maven", "Gradle", "JUnit",
            "Android", "iOS", "React Native", "Flutter", "Xamarin"
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in common_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)
        
        return found_skills[:10]  # Limit to top 10 skills
    
    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed job information by ID
        
        Args:
            job_id: Adzuna job ID
            
        Returns:
            Detailed job information or None if not found
        """
        try:
            url = f"https://api.adzuna.com/v1/api/jobs/{self.country}/search/1"
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "id": job_id
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('results', [])
                if jobs:
                    return self._format_job_data(jobs[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching job by ID {job_id}: {str(e)}")
            return None
