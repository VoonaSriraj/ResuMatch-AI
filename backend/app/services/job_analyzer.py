"""
Job analysis service for parsing job descriptions and requirements
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import asyncio
from app.services.groq_service import groq_service
from app.utils.logger import get_logger
from app.utils.helpers import generate_unique_filename, validate_file_type, validate_file_size, parse_salary_range

logger = get_logger(__name__)

class JobAnalyzerService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        self.create_upload_directory()
    
    def create_upload_directory(self):
        """Create upload directory if it doesn't exist"""
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
    
    async def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """Extract text from job description file"""
        file_type = file_type.lower()
        
        if file_type == '.pdf':
            # Use the same PDF extraction method as resume parser
            from app.services.resume_parser import resume_parser_service
            return await resume_parser_service.extract_text_from_pdf(file_path)
        elif file_type in ['.docx', '.doc']:
            from app.services.resume_parser import resume_parser_service
            return await resume_parser_service.extract_text_from_docx(file_path)
        elif file_type == '.txt':
            from app.services.resume_parser import resume_parser_service
            return await resume_parser_service.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    async def parse_job_with_ai(self, job_text: str) -> Dict[str, Any]:
        """Parse job description using Groq AI"""
        try:
            return await groq_service.parse_job_description(job_text)
        except Exception as e:
            logger.error(f"AI job parsing failed: {str(e)}")
            raise Exception(f"AI parsing failed: {str(e)}")
    
    async def process_job_file(
        self, 
        file_content: bytes, 
        filename: str, 
        user_id: int,
        title: Optional[str] = None,
        company: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process uploaded job description file"""
        try:
            # Validate file type
            file_extension = Path(filename).suffix.lower()
            if file_extension not in ['.pdf', '.docx', '.doc', '.txt']:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Validate file size
            file_size = len(file_content)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError("File size exceeds 10MB limit")
            
            # Generate unique filename
            unique_filename = generate_unique_filename(filename, user_id)
            file_path = os.path.join(self.upload_dir, unique_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Extract text
            extracted_text = await self.extract_text_from_file(file_path, file_extension)
            
            if not extracted_text.strip():
                raise ValueError("No text could be extracted from the file")
            
            # Parse with AI
            parsed_data = await self.parse_job_with_ai(extracted_text)
            
            # Extract basic job information from text if not provided
            if not title:
                title = self.extract_job_title(extracted_text)
            if not company:
                company = self.extract_company_name(extracted_text)
            if not location:
                location = self.extract_location(extracted_text)
            
            # Extract salary information
            salary_info = parse_salary_range(extracted_text)
            
            return {
                "filename": unique_filename,
                "file_path": file_path,
                "file_type": file_extension,
                "file_size": file_size,
                "job_text": extracted_text,
                "title": title,
                "company": company,
                "location": location,
                "salary_info": salary_info,
                "parsed_data": parsed_data,
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Job processing failed: {str(e)}")
            # Clean up file if it was created
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            raise
    
    async def process_job_text(
        self, 
        job_text: str,
        title: Optional[str] = None,
        company: Optional[str] = None,
        location: Optional[str] = None,
        source_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process job description text directly"""
        try:
            if not job_text.strip():
                raise ValueError("Job text cannot be empty")
            
            # Parse with AI
            parsed_data = await self.parse_job_with_ai(job_text)
            
            # Extract basic job information from text if not provided
            if not title:
                title = self.extract_job_title(job_text)
            if not company:
                company = self.extract_company_name(job_text)
            if not location:
                location = self.extract_location(job_text)
            
            # Extract salary information
            salary_info = parse_salary_range(job_text)
            
            return {
                "job_text": job_text,
                "title": title,
                "company": company,
                "location": location,
                "source_link": source_link,
                "salary_info": salary_info,
                "parsed_data": parsed_data,
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Job text processing failed: {str(e)}")
            raise
    
    def extract_job_title(self, text: str) -> str:
        """Extract job title from text"""
        # Simple heuristics to find job title
        lines = text.split('\n')[:10]  # Check first 10 lines
        
        for line in lines:
            line = line.strip()
            if line and len(line) < 100:  # Reasonable title length
                # Skip common non-title patterns
                if any(word in line.lower() for word in ['job description', 'company:', 'location:', 'salary:']):
                    continue
                return line
        
        return "Job Title Not Found"
    
    def extract_company_name(self, text: str) -> str:
        """Extract company name from text"""
        import re
        
        # Look for "Company:" or "at [Company Name]" patterns
        patterns = [
            r'company:\s*([^\n]+)',
            r'at\s+([A-Z][a-zA-Z\s&]+)',
            r'([A-Z][a-zA-Z\s&]+)\s+is\s+hiring'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) < 50:  # Reasonable company name length
                    return company
        
        return "Company Not Specified"
    
    def extract_location(self, text: str) -> str:
        """Extract location from text"""
        import re
        
        # Look for location patterns
        patterns = [
            r'location:\s*([^\n]+)',
            r'([A-Z][a-z]+,\s*[A-Z]{2})',  # City, State
            r'([A-Z][a-z]+,\s*[A-Z][a-z]+)',  # City, Country
            r'(remote|hybrid|on-site)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) < 50:  # Reasonable location length
                    return location
        
        return "Location Not Specified"

# Global instance
job_analyzer_service = JobAnalyzerService()
