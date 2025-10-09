"""
Resume parsing service for handling file uploads and text extraction
"""

import os
import PyPDF2
import docx
from typing import Dict, Any, Optional
from pathlib import Path
import asyncio
from app.services.groq_service import groq_service
from app.utils.logger import get_logger
from app.utils.helpers import generate_unique_filename, validate_file_type, validate_file_size

logger = get_logger(__name__)

class ResumeParserService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        self.create_upload_directory()
    
    def create_upload_directory(self):
        """Create upload directory if it doesn't exist"""
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
    
    async def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"PDF text extraction failed: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    async def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"DOCX text extraction failed: {str(e)}")
            raise Exception(f"Failed to extract text from DOCX: {str(e)}")
    
    async def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            logger.error(f"TXT text extraction failed: {str(e)}")
            raise Exception(f"Failed to extract text from TXT: {str(e)}")
    
    async def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """Extract text from file based on file type"""
        file_type = file_type.lower()
        
        if file_type == '.pdf':
            return await self.extract_text_from_pdf(file_path)
        elif file_type in ['.docx', '.doc']:
            return await self.extract_text_from_docx(file_path)
        elif file_type == '.txt':
            return await self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    async def parse_resume_with_ai(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text using Groq AI"""
        try:
            return await groq_service.parse_resume(resume_text)
        except Exception as e:
            logger.error(f"AI resume parsing failed: {str(e)}")
            raise Exception(f"AI parsing failed: {str(e)}")
    
    async def process_resume_file(
        self, 
        file_content: bytes, 
        filename: str, 
        user_id: int
    ) -> Dict[str, Any]:
        """Process uploaded resume file"""
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
            
            # Parse with AI (or heuristics in mock mode)
            parsed_data = await self.parse_resume_with_ai(extracted_text)

            # Coerce AI output fields to lists of strings for DB storage
            import json as _json
            def _to_string_list(value):
                if value is None:
                    return []
                out = []
                for item in (value if isinstance(value, list) else [value]):
                    if isinstance(item, (str, int, float)):
                        out.append(str(item))
                    else:
                        try:
                            out.append(_json.dumps(item, ensure_ascii=False))
                        except Exception:
                            out.append(str(item))
                return out

            parsed_data = {
                "skills": _to_string_list(parsed_data.get("skills")),
                "experience": _to_string_list(parsed_data.get("experience")),
                "education": _to_string_list(parsed_data.get("education")),
                "certifications": _to_string_list(parsed_data.get("certifications")),
                "achievements": _to_string_list(parsed_data.get("achievements")),
            }
            
            # Heuristic fallback if AI returns empty lists
            try:
                if (
                    isinstance(parsed_data, dict)
                    and not any(parsed_data.get(k) for k in [
                        "skills", "experience", "education", "certifications", "achievements"
                    ])
                ):
                    from app.utils.helpers import extract_skills_from_text
                    fallback_skills = extract_skills_from_text(extracted_text)
                    parsed_data = {
                        **parsed_data,
                        "skills": fallback_skills,
                    }
            except Exception:
                pass
            
            return {
                "filename": unique_filename,
                "file_path": file_path,
                "file_type": file_extension,
                "file_size": file_size,
                "extracted_text": extracted_text,
                "parsed_data": parsed_data,
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Resume processing failed: {str(e)}")
            # Clean up file if it was created
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            raise
    
    async def process_resume_text(self, resume_text: str) -> Dict[str, Any]:
        """Process resume text directly (no file upload)"""
        try:
            if not resume_text.strip():
                raise ValueError("Resume text cannot be empty")
            
            # Parse with AI
            parsed_data = await self.parse_resume_with_ai(resume_text)

            # Coerce AI output fields to lists of strings for DB storage
            import json as _json
            def _to_string_list(value):
                if value is None:
                    return []
                out = []
                for item in (value if isinstance(value, list) else [value]):
                    if isinstance(item, (str, int, float)):
                        out.append(str(item))
                    else:
                        try:
                            out.append(_json.dumps(item, ensure_ascii=False))
                        except Exception:
                            out.append(str(item))
                return out

            parsed_data = {
                "skills": _to_string_list(parsed_data.get("skills")),
                "experience": _to_string_list(parsed_data.get("experience")),
                "education": _to_string_list(parsed_data.get("education")),
                "certifications": _to_string_list(parsed_data.get("certifications")),
                "achievements": _to_string_list(parsed_data.get("achievements")),
            }
            
            return {
                "extracted_text": resume_text,
                "parsed_data": parsed_data,
                "processing_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Resume text processing failed: {str(e)}")
            raise

# Global instance
resume_parser_service = ResumeParserService()
