"""
LinkedIn integration service for job recommendations and profile data
"""

import requests
from typing import Dict, Any, List, Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class LinkedInService:
    def __init__(self):
        self.base_url = "https://api.linkedin.com/v2"
        self.client_id = settings.linkedin_client_id
        self.client_secret = settings.linkedin_client_secret
    
    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """Get user's LinkedIn profile information"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Get basic profile
            profile_response = requests.get(
                f"{self.base_url}/people/~",
                headers=headers
            )
            
            if profile_response.status_code != 200:
                raise Exception(f"Failed to get profile: {profile_response.text}")
            
            profile_data = profile_response.json()
            
            # Get email
            email_response = requests.get(
                f"{self.base_url}/emailAddress?q=members&projection=(elements*(handle~))",
                headers=headers
            )
            
            email = None
            if email_response.status_code == 200:
                email_data = email_response.json()
                if email_data.get("elements"):
                    email = email_data["elements"][0]["handle~"]["emailAddress"]
            
            return {
                "id": profile_data.get("id"),
                "first_name": profile_data.get("localizedFirstName", ""),
                "last_name": profile_data.get("localizedLastName", ""),
                "email": email,
                "profile_picture": profile_data.get("profilePicture", {}).get("displayImage", ""),
                "headline": profile_data.get("headline", ""),
                "summary": profile_data.get("summary", "")
            }
            
        except Exception as e:
            logger.error(f"Failed to get LinkedIn profile: {str(e)}")
            raise
    
    async def search_jobs(
        self, 
        access_token: str, 
        keywords: List[str] = None,
        location: str = None,
        experience_level: str = None,
        job_type: str = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Search for jobs on LinkedIn"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Build search parameters
            params = {
                "keywords": " ".join(keywords) if keywords else "",
                "locationName": location or "",
                "count": limit,
                "start": 0
            }
            
            # LinkedIn Job Search API endpoint (Note: This might require additional permissions)
            search_url = f"{self.base_url}/jobSearch"
            
            response = requests.get(search_url, headers=headers, params=params)
            
            if response.status_code != 200:
                logger.warning(f"LinkedIn job search failed: {response.text}")
                # Return mock data for development
                return self._get_mock_job_data(keywords, location, limit)
            
            search_data = response.json()
            jobs = []
            
            for job in search_data.get("elements", []):
                job_info = self._parse_job_data(job)
                if job_info:
                    jobs.append(job_info)
            
            return jobs
            
        except Exception as e:
            logger.error(f"LinkedIn job search failed: {str(e)}")
            # Return mock data for development
            return self._get_mock_job_data(keywords, location, limit)
    
    async def get_job_details(self, access_token: str, job_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific job"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(
                f"{self.base_url}/jobs/{job_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get job details: {response.text}")
            
            job_data = response.json()
            return self._parse_job_data(job_data, detailed=True)
            
        except Exception as e:
            logger.error(f"Failed to get job details: {str(e)}")
            raise
    
    def _parse_job_data(self, job_data: Dict[str, Any], detailed: bool = False) -> Optional[Dict[str, Any]]:
        """Parse job data from LinkedIn API response"""
        try:
            # Extract basic job information
            job_info = {
                "linkedin_job_id": job_data.get("id"),
                "title": job_data.get("title", "Job Title Not Available"),
                "company": job_data.get("companyDetails", {}).get("name", "Company Not Specified"),
                "location": job_data.get("formattedLocation", "Location Not Specified"),
                "description": job_data.get("description", {}).get("text", ""),
                "apply_url": job_data.get("applyMethod", {}).get("easyApplyUrl") or 
                           job_data.get("applyMethod", {}).get("externalUrl"),
                "posted_date": job_data.get("listedAt"),
                "job_type": job_data.get("workplaceTypes", []),
                "seniority_level": job_data.get("experienceLevel"),
                "employment_type": job_data.get("employmentType")
            }
            
            if detailed:
                # Add more detailed information
                job_info.update({
                    "skills": job_data.get("skills", []),
                    "salary_range": job_data.get("salaryInfo", {}),
                    "benefits": job_data.get("benefits", []),
                    "requirements": job_data.get("jobRequirements", {}),
                    "responsibilities": job_data.get("jobResponsibilities", {})
                })
            
            return job_info
            
        except Exception as e:
            logger.error(f"Failed to parse job data: {str(e)}")
            return None
    
    def _get_mock_job_data(self, keywords: List[str] = None, location: str = None, limit: int = 25) -> List[Dict[str, Any]]:
        """Generate mock job data for development/testing"""
        # More realistic job titles and descriptions
        job_templates = [
            {
                "title": "Software Engineer",
                "description": "We are looking for a skilled Software Engineer to join our development team. You will be responsible for designing, developing, and maintaining software applications using modern programming languages and frameworks. Experience with Python, JavaScript, React, and database technologies is required.",
                "company": "TechCorp Solutions",
                "skills": ["Python", "JavaScript", "React", "SQL", "Git"]
            },
            {
                "title": "Data Scientist",
                "description": "Join our data science team to analyze complex datasets and build machine learning models. You will work with Python, R, SQL, and various ML frameworks. Strong background in statistics, machine learning algorithms, and data visualization required.",
                "company": "DataFlow Inc",
                "skills": ["Python", "R", "SQL", "Machine Learning", "Statistics"]
            },
            {
                "title": "Full Stack Developer",
                "description": "We need a Full Stack Developer to build end-to-end web applications. You will work with frontend technologies like React/Vue.js and backend technologies like Node.js/Python. Experience with cloud platforms and DevOps practices is a plus.",
                "company": "WebTech Solutions",
                "skills": ["React", "Node.js", "Python", "AWS", "Docker"]
            },
            {
                "title": "DevOps Engineer",
                "description": "Looking for a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines. You will work with AWS/Azure, Docker, Kubernetes, and automation tools. Strong scripting skills in Python/Bash required.",
                "company": "CloudScale Technologies",
                "skills": ["AWS", "Docker", "Kubernetes", "Python", "Jenkins"]
            },
            {
                "title": "Product Manager",
                "description": "We are seeking a Product Manager to drive product strategy and work with cross-functional teams. You will define product requirements, work with engineering teams, and analyze user data. Technical background and experience with agile methodologies required.",
                "company": "ProductVision Corp",
                "skills": ["Product Management", "Agile", "Analytics", "User Research", "Strategy"]
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
                "apply_url": f"https://www.linkedin.com/jobs/view/{3000000000 + i}",  # Real LinkedIn job ID format
                "posted_date": None,  # Will be set to current time in database
                "job_type": ["remote", "hybrid", "on-site"][i % 3],
                "seniority_level": ["entry", "mid", "senior"][i % 3],
                "employment_type": "full-time",
                "salary_range": f"${80000 + i*5000}-${120000 + i*5000}",
                "skills": template["skills"]
            })
        
        return mock_jobs
    
    async def get_user_skills(self, access_token: str) -> List[str]:
        """Get user's skills from LinkedIn profile"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(
                f"{self.base_url}/people/~:(skills)",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to get skills: {response.text}")
                return []
            
            skills_data = response.json()
            skills = []
            
            for skill in skills_data.get("skills", {}).get("elements", []):
                skill_name = skill.get("name")
                if skill_name:
                    skills.append(skill_name)
            
            return skills
            
        except Exception as e:
            logger.error(f"Failed to get user skills: {str(e)}")
            return []
    
    async def get_user_experience(self, access_token: str) -> List[Dict[str, Any]]:
        """Get user's work experience from LinkedIn profile"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = requests.get(
                f"{self.base_url}/people/~:(positions)",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to get experience: {response.text}")
                return []
            
            experience_data = response.json()
            experiences = []
            
            for position in experience_data.get("positions", {}).get("elements", []):
                exp = {
                    "title": position.get("title", ""),
                    "company": position.get("companyName", ""),
                    "location": position.get("locationName", ""),
                    "description": position.get("description", ""),
                    "start_date": position.get("startDate", {}),
                    "end_date": position.get("endDate", {}),
                    "is_current": position.get("isCurrent", False)
                }
                experiences.append(exp)
            
            return experiences
            
        except Exception as e:
            logger.error(f"Failed to get user experience: {str(e)}")
            return []

# Global instance
linkedin_service = LinkedInService()
