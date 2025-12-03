# Architecture Overview

## Project Structure

```
JobAlign-AI/
├── frontend/          # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/     # Page components
│   │   ├── components/# Reusable components
│   │   └── lib/       # Utilities
│   └── package.json
│
└── backend/           # Python FastAPI
    ├── app/
    │   ├── api/       # API endpoints
    │   ├── models/    # Database models
    │   ├── services/  # Business logic
    │   ├── schemas/   # Request/response schemas
    │   └── utils/     # Utilities
    └── requirements.txt
```

## Key Features

1. **Resume Analysis**: AI-powered resume parsing and optimization
2. **Job Matching**: Intelligent job-resume matching algorithm
3. **Interview Prep**: AI-generated interview questions
4. **LinkedIn Integration**: Direct LinkedIn profile connection
5. **Job Aggregation**: Multiple job sources (RapidAPI, Adzuna)
6. **User Profiles**: User accounts and job preferences
