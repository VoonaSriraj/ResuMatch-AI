# Backend API Documentation

## Authentication Endpoints
- POST /api/auth/login
- POST /api/auth/register
- POST /api/auth/logout
- POST /api/auth/refresh

## Resume Endpoints
- POST /api/resume/upload
- GET /api/resume/{id}
- PUT /api/resume/{id}
- DELETE /api/resume/{id}

## Job Endpoints
- POST /api/jobs/upload
- GET /api/jobs
- GET /api/jobs/{id}
- POST /api/jobs/match

## Matching Endpoints
- POST /api/match/calculate
- GET /api/match/history
- GET /api/recommendations
