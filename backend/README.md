# JobAlign AI Backend

A comprehensive FastAPI backend for JobAlign AI, featuring AI-powered resume optimization, job matching, interview preparation, and LinkedIn integration.

## Features

- **User Authentication**: JWT-based auth with LinkedIn OAuth2 integration
- **Resume Processing**: Upload and parse PDF/DOCX resumes using Groq AI
- **Job Analysis**: Upload and analyze job descriptions
- **Match Scoring**: AI-powered resume-job compatibility scoring
- **Resume Optimization**: Get AI suggestions to improve resume-job matches
- **Interview Prep**: Generate personalized interview questions and tips
- **Job Recommendations**: LinkedIn integration for job discovery
- **Subscription Management**: Stripe integration for premium features

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI**: Groq API (Llama models)
- **Authentication**: JWT + LinkedIn OAuth2
- **Payments**: Stripe
- **File Processing**: PyPDF2, python-docx
- **Documentation**: Auto-generated OpenAPI/Swagger

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Groq API key
- LinkedIn Developer App
- Stripe account

### Installation

1. **Clone and setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment setup**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Database setup**:
   ```bash
   # Create PostgreSQL database
   createdb jobalign
   
   # Run the application (creates tables automatically)
   uvicorn app.main:app --reload
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/linkedin` - LinkedIn OAuth login
- `GET /api/auth/me` - Get current user info

### Resume Management
- `POST /api/resume/upload` - Upload resume file
- `POST /api/resume/upload-text` - Upload resume text
- `GET /api/resume/list` - List user's resumes
- `GET /api/resume/{id}` - Get specific resume
- `DELETE /api/resume/{id}` - Delete resume

### Job Management
- `POST /api/job/upload` - Upload job description file
- `POST /api/job/upload-text` - Upload job text
- `GET /api/job/list` - List user's jobs
- `GET /api/job/{id}` - Get specific job
- `DELETE /api/job/{id}` - Delete job

### Matching & Optimization
- `POST /api/match/calculate` - Calculate match score
- `POST /api/match/batch-calculate` - Batch match calculation
- `GET /api/match/history` - Get match history
- `POST /api/optimize/optimize` - Optimize resume for job
- `GET /api/optimize/suggestions/{resume_id}/{job_id}` - Get optimization suggestions

### Interview Preparation
- `POST /api/interview/generate` - Generate interview questions
- `POST /api/interview/follow-up` - Generate follow-up questions
- `POST /api/interview/answer-suggestions` - Generate answer suggestions
- `GET /api/interview/categories/{job_id}` - Get question categories

### Job Recommendations
- `POST /api/recommendations/search` - Search and recommend jobs
- `GET /api/recommendations/recommended` - Get recommended jobs
- `PUT /api/recommendations/application-status` - Update application status
- `GET /api/recommendations/application-stats` - Get application statistics

### LinkedIn Integration
- `GET /api/linkedin/status` - Check LinkedIn connection
- `POST /api/linkedin/refresh-profile` - Refresh LinkedIn profile
- `DELETE /api/linkedin/disconnect` - Disconnect LinkedIn
- `GET /api/linkedin/skills` - Get LinkedIn skills
- `GET /api/linkedin/experience` - Get LinkedIn experience
- `POST /api/linkedin/sync-resume` - Sync LinkedIn to resume

### Stripe Webhooks
- `POST /api/stripe/webhook` - Handle Stripe events

## Database Schema

### Core Tables
- `users` - User accounts and profiles
- `resumes` - Uploaded resumes and parsed data
- `job_descriptions` - Job postings and requirements
- `match_history` - Resume-job match results
- `recommended_jobs` - LinkedIn job recommendations
- `subscriptions` - Stripe subscription data
- `activity_logs` - User activity tracking

## Environment Variables

See `env.example` for all required environment variables:

### Required
- `POSTGRES_*` - Database connection
- `GROQ_API_KEY` - Groq AI API key
- `JWT_SECRET_KEY` - JWT signing key
- `STRIPE_SECRET_KEY` - Stripe API key

### Optional
- `LINKEDIN_*` - LinkedIn OAuth (for job recommendations)
- `DEBUG` - Enable debug mode

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
flake8 app/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## Deployment

### Docker (Recommended)
```bash
docker build -t jobalign-backend .
docker run -p 8000:8000 --env-file .env jobalign-backend
```

### Production Setup
1. Set up PostgreSQL database
2. Configure environment variables
3. Run with Gunicorn:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Integration with Frontend

This backend is designed to work seamlessly with the Lovable.ai frontend. Key integration points:

1. **Authentication**: JWT tokens for session management
2. **File Uploads**: Multipart form data for resume/job files
3. **Real-time Updates**: WebSocket support for live updates
4. **Error Handling**: Consistent error response format

## Security Considerations

- JWT tokens with expiration
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy
- File upload restrictions

## Monitoring & Logging

- Structured logging with timestamps
- Activity tracking for audit trails
- Health check endpoints
- Error tracking and reporting

## Support

For issues and questions:
1. Check the API documentation
2. Review the logs for error details
3. Verify environment configuration
4. Test with the provided examples

## License

Private - JobAlign AI Platform
