# test_interview.py
import asyncio
from app.services.interview_engine import interview_engine_service

async def test_interview_answers():
    result = await interview_engine_service.generate_questions_with_answers(
        job_text="Looking for a Python developer with experience in FastAPI and ML",
        job_title="Senior Python Developer",
        company="Tech Corp",
        seniority_level="Senior"
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(test_interview_answers())