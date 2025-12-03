# AI Integration Guide

## Groq AI Service
- Resume analysis and optimization
- Interview question generation
- Job description analysis

## Implementation Details
- Endpoint: /api/interview/generate
- Model: Groq LLaMA
- Response time: < 2 seconds

## Usage Example
```python
from app.services.groq_service import GroqService

service = GroqService()
questions = service.generate_interview_questions(job_description)
```
