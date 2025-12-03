# JobAlign AI - Complete System Architecture Analysis

## 🏗️ System Architecture Overview

JobAlign AI is a comprehensive career assistance platform built with modern web technologies, featuring AI-powered resume optimization, job matching, and interview preparation capabilities.

### **Tech Stack Summary**
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Python 3.12 + SQLAlchemy + Alembic
- **Database**: PostgreSQL (production) / SQLite (development)
- **AI/ML**: Groq API (Llama 3.1 70B model)
- **External APIs**: LinkedIn API, Adzuna Job API, RapidAPI
- **Authentication**: JWT + OAuth2 (Google, GitHub, LinkedIn)
- **Payments**: Stripe integration
- **Deployment**: Docker + Render

---

## 📊 Visual System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                FRONTEND LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  React App (Vite + TypeScript)                                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   Dashboard     │ │   Job Match     │ │ Resume Optimizer│ │ Interview Prep  │ │
│  │   Component     │ │   Component     │ │   Component     │ │   Component     │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │Recommended Jobs │ │    Settings     │ │   OAuth Callback│ │   Layout        │ │
│  │   Component     │ │   Component     │ │   Component     │ │   Component     │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                                                 │
│  UI Components: shadcn/ui + Tailwind CSS + Lucide Icons                        │
│  State Management: React Query + Local State                                    │
│  Routing: React Router v6                                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ HTTP/REST API Calls
                                        │ (JWT Authentication)
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                BACKEND LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  FastAPI Application (Python 3.12)                                             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   Auth API      │ │  Resume API     │ │   Job API       │ │  Match API      │ │
│  │   (/api/auth)   │ │  (/api/resume)  │ │  (/api/job)     │ │  (/api/match)  │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │Optimize API     │ │Interview API    │ │Recommendations │ │  Dashboard API │ │
│  │(/api/optimize)  │ │(/api/interview)│ │   API          │ │   API          │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │ LinkedIn API    │ │  Stripe API     │ │   Jobs API      │ │   Utils        │ │
│  │(/api/linkedin)  │ │(/api/stripe)    │ │(/api/jobs)     │ │   Module       │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                                                 │
│  Middleware: CORS, Authentication, Logging, Error Handling                     │
│  Services: Groq AI, LinkedIn, Resume Parser, Match Engine                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ SQLAlchemy ORM
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PostgreSQL Database (Production) / SQLite (Development)                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │     Users       │ │    Resumes      │ │ Job Descriptions│ │ Match History   │ │
│  │   Table         │ │    Table        │ │    Table        │ │    Table        │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │Recommended Jobs │ │ Subscriptions   │ │ Activity Logs   │ │ User Profiles   │ │
│  │   Table         │ │   Table         │ │   Table         │ │   Table         │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                                                 │
│  Relationships: Foreign Keys, Cascade Deletes, Indexes                        │
│  Migrations: Alembic for schema versioning                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ External API Calls
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL SERVICES LAYER                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   Groq AI       │ │  LinkedIn API   │ │   Adzuna API    │ │   Stripe API    │ │
│  │ (Llama 3.1 70B) │ │ (Job Search)    │ │ (Job Data)      │ │ (Payments)      │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   RapidAPI      │ │   Google OAuth  │ │  GitHub OAuth   │ │   File Storage  │ │
│  │ (Job Aggregator)│ │ (Authentication)│ │(Authentication) │ │   (Local/Cloud)│ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema Design

### **Core Tables & Relationships**

```sql
-- Users Table (Central entity)
users (
    id: INTEGER PRIMARY KEY
    name: VARCHAR(255) NOT NULL
    email: VARCHAR(255) UNIQUE NOT NULL
    hashed_password: VARCHAR(255) NULLABLE (OAuth users)
    linkedin_id: VARCHAR(255) UNIQUE NULLABLE
    linkedin_access_token: TEXT NULLABLE
    subscription_plan: VARCHAR(50) DEFAULT 'free'
    is_active: BOOLEAN DEFAULT TRUE
    is_verified: BOOLEAN DEFAULT FALSE
    profile_picture: VARCHAR(500) NULLABLE
    created_at: TIMESTAMP WITH TIME ZONE
    updated_at: TIMESTAMP WITH TIME ZONE
)

-- Resumes Table
resumes (
    id: INTEGER PRIMARY KEY
    user_id: INTEGER FOREIGN KEY → users.id
    filename: VARCHAR(255) NOT NULL
    file_path: VARCHAR(500) NULLABLE
    file_type: VARCHAR(50) NOT NULL
    file_size: INTEGER NULLABLE
    extracted_text: TEXT NULLABLE
    parsed_skills: TEXT NULLABLE (JSON)
    parsed_experience: TEXT NULLABLE (JSON)
    parsed_education: TEXT NULLABLE (JSON)
    parsed_certifications: TEXT NULLABLE (JSON)
    parsed_achievements: TEXT NULLABLE (JSON)
    raw_ai_response: TEXT NULLABLE
    processing_status: VARCHAR(50) DEFAULT 'pending'
    upload_date: TIMESTAMP WITH TIME ZONE
)

-- Job Descriptions Table
job_descriptions (
    id: INTEGER PRIMARY KEY
    user_id: INTEGER FOREIGN KEY → users.id
    title: VARCHAR(255) NOT NULL
    company: VARCHAR(255) NULLABLE
    location: VARCHAR(255) NULLABLE
    job_text: TEXT NOT NULL
    source_link: VARCHAR(500) NULLABLE
    source_type: VARCHAR(50) DEFAULT 'upload'
    file_path: VARCHAR(500) NULLABLE
    file_type: VARCHAR(50) NULLABLE
    extracted_skills: TEXT NULLABLE (JSON)
    experience_requirements: TEXT NULLABLE (JSON)
    education_requirements: TEXT NULLABLE (JSON)
    required_certifications: TEXT NULLABLE (JSON)
    salary_range: VARCHAR(100) NULLABLE
    job_type: VARCHAR(50) NULLABLE
    seniority_level: VARCHAR(50) NULLABLE
    remote_friendly: VARCHAR(20) NULLABLE
    raw_ai_response: TEXT NULLABLE
    processing_status: VARCHAR(50) DEFAULT 'pending'
    created_at: TIMESTAMP WITH TIME ZONE
)

-- Match History Table
match_history (
    id: INTEGER PRIMARY KEY
    user_id: INTEGER FOREIGN KEY → users.id
    resume_id: INTEGER FOREIGN KEY → resumes.id
    job_id: INTEGER FOREIGN KEY → job_descriptions.id
    match_score: FLOAT NOT NULL (0-100)
    missing_keywords: TEXT NULLABLE (JSON)
    matching_keywords: TEXT NULLABLE (JSON)
    missing_skills: TEXT NULLABLE (JSON)
    matching_skills: TEXT NULLABLE (JSON)
    optimized_resume_text: TEXT NULLABLE
    optimization_suggestions: TEXT NULLABLE (JSON)
    improvement_areas: TEXT NULLABLE (JSON)
    experience_match_score: FLOAT NULLABLE
    skills_match_score: FLOAT NULLABLE
    education_match_score: FLOAT NULLABLE
    keywords_match_score: FLOAT NULLABLE
    detailed_analysis: TEXT NULLABLE
    raw_ai_response: TEXT NULLABLE
    processing_status: VARCHAR(50) DEFAULT 'completed'
    created_at: TIMESTAMP WITH TIME ZONE
)

-- Recommended Jobs Table
recommended_jobs (
    id: INTEGER PRIMARY KEY
    user_id: INTEGER FOREIGN KEY → users.id
    linkedin_job_id: VARCHAR(255) NULLABLE
    external_job_id: VARCHAR(255) NULLABLE
    title: VARCHAR(255) NOT NULL
    company: VARCHAR(255) NOT NULL
    location: VARCHAR(255) NULLABLE
    description: TEXT NULLABLE
    match_score: FLOAT NULLABLE
    apply_link: VARCHAR(500) NULLABLE
    source: VARCHAR(50) DEFAULT 'linkedin'
    salary_info: VARCHAR(255) NULLABLE
    job_type: VARCHAR(50) NULLABLE
    seniority_level: VARCHAR(50) NULLABLE
    remote_friendly: VARCHAR(20) NULLABLE
    posted_date: TIMESTAMP WITH TIME ZONE NULLABLE
    application_deadline: TIMESTAMP WITH TIME ZONE NULLABLE
    is_applied: VARCHAR(20) DEFAULT 'no'
    notes: TEXT NULLABLE
    fetched_at: TIMESTAMP WITH TIME ZONE
)

-- Subscriptions Table
subscriptions (
    id: INTEGER PRIMARY KEY
    user_id: INTEGER FOREIGN KEY → users.id
    plan_type: VARCHAR(50) NOT NULL
    stripe_customer_id: VARCHAR(255) NULLABLE
    stripe_subscription_id: VARCHAR(255) NULLABLE
    stripe_price_id: VARCHAR(255) NULLABLE
    status: VARCHAR(50) NOT NULL
    current_period_start: TIMESTAMP WITH TIME ZONE NULLABLE
    current_period_end: TIMESTAMP WITH TIME ZONE NULLABLE
    cancel_at_period_end: BOOLEAN DEFAULT FALSE
    canceled_at: TIMESTAMP WITH TIME ZONE NULLABLE
    trial_start: TIMESTAMP WITH TIME ZONE NULLABLE
    trial_end: TIMESTAMP WITH TIME ZONE NULLABLE
    created_at: TIMESTAMP WITH TIME ZONE
    updated_at: TIMESTAMP WITH TIME ZONE
)

-- Activity Logs Table
activity_logs (
    id: INTEGER PRIMARY KEY
    user_id: INTEGER FOREIGN KEY → users.id
    action_type: VARCHAR(100) NOT NULL
    description: TEXT NOT NULL
    meta_data: TEXT NULLABLE (JSON)
    created_at: TIMESTAMP WITH TIME ZONE
)
```

---

## 🔄 API Flow & Component Interactions

### **1. Authentication Flow**
```
Frontend → Backend → External OAuth → Database
    │         │           │              │
    │         │           │              │
    ▼         ▼           ▼              ▼
Login Page → Auth API → Google/GitHub → User Table
    │         │           │              │
    │         │           │              │
    ▼         ▼           ▼              ▼
JWT Token ← Response ← Profile Data ← User Created
```

### **2. Resume Upload & Processing Flow**
```
Frontend → Backend → AI Service → Database
    │         │         │           │
    │         │         │           │
    ▼         ▼         ▼           ▼
Upload → Resume API → Groq AI → Resume Table
    │         │         │           │
    │         │         │           │
    ▼         ▼         ▼           ▼
File → Parser → Llama 3.1 → Parsed Data
    │         │         │           │
    │         │         │           │
    ▼         ▼         ▼           ▼
PDF/DOCX → Extract → AI Analysis → Skills/Experience
```

### **3. Job Matching Flow**
```
Frontend → Backend → AI Service → Database
    │         │         │           │
    │         │         │           │
    ▼         ▼         ▼           ▼
Upload → Job API → Groq AI → Job Table
    │         │         │           │
    │         │         │           │
    ▼         ▼         ▼           ▼
Job Desc → Parser → Analysis → Requirements
    │         │         │           │
    │         │         │           │
    ▼         ▼         ▼           ▼
Match → Match API → Scoring → Match History
    │         │         │           │
    │         │         │           │
    ▼         ▼         ▼           ▼
Score ← Response ← AI Compare ← Results
```

### **4. Job Recommendations Flow**
```
Frontend → Backend → External APIs → Database
    │         │           │            │
    │         │           │            │
    ▼         ▼           ▼            ▼
Request → LinkedIn API → Job Search → Recommended Jobs
    │         │           │            │
    │         │           │            │
    ▼         ▼           ▼            ▼
User → Adzuna API → Job Data → Match Scoring
    │         │           │            │
    │         │           │            │
    ▼         ▼           ▼            ▼
Profile → RapidAPI → Aggregation → AI Filtering
```

---

## 🧩 Module Interconnections

### **Backend Services Architecture**

```python
# Core Service Dependencies
app/
├── api/                    # REST API endpoints
│   ├── auth.py            # Authentication & OAuth
│   ├── upload_resume.py   # Resume processing
│   ├── upload_job.py      # Job description processing
│   ├── match_score.py     # Matching algorithms
│   ├── optimize_resume.py # Resume optimization
│   ├── generate_interview_questions.py # AI interview prep
│   ├── recommended_jobs.py # Job recommendations
│   ├── linkedin_connect.py # LinkedIn integration
│   ├── stripe_webhook.py  # Payment processing
│   └── dashboard.py       # Analytics & stats
├── services/              # Business logic services
│   ├── groq_service.py    # AI processing (Llama 3.1)
│   ├── linkedin_service.py # LinkedIn API integration
│   ├── resume_parser.py   # Document parsing
│   ├── match_engine.py    # Matching algorithms
│   ├── job_service.py     # Job data management
│   ├── stripe_service.py  # Payment processing
│   └── interview_engine.py # Interview question generation
├── models/                 # Database models
│   ├── user.py           # User management
│   ├── resume.py         # Resume data
│   ├── job.py            # Job descriptions
│   ├── match_history.py  # Matching results
│   ├── subscription.py   # Payment plans
│   └── activity_log.py   # User activity tracking
└── utils/                 # Utility functions
    ├── auth.py           # JWT & password handling
    ├── helpers.py        # Common utilities
    └── logger.py         # Logging configuration
```

### **Frontend Component Hierarchy**

```typescript
// React Component Structure
src/
├── App.tsx                 # Main application wrapper
├── components/
│   ├── Layout.tsx         # Main layout wrapper
│   ├── AppSidebar.tsx     # Navigation sidebar
│   ├── RequireAuth.tsx    # Authentication guard
│   ├── LinkedInConnection.tsx # LinkedIn integration
│   └── ui/                # Reusable UI components
│       ├── button.tsx     # Button component
│       ├── card.tsx       # Card component
│       ├── input.tsx      # Input component
│       └── ...            # Other UI components
├── pages/                  # Page components
│   ├── Dashboard.tsx      # Main dashboard
│   ├── JobMatch.tsx       # Job matching interface
│   ├── ResumeOptimizer.tsx # Resume optimization
│   ├── InterviewPrep.tsx  # Interview preparation
│   ├── RecommendedJobs.tsx # Job recommendations
│   ├── Settings.tsx       # User settings
│   ├── Login.tsx          # Authentication
│   └── OAuthCallback.tsx  # OAuth handling
├── hooks/                  # Custom React hooks
│   ├── use-mobile.tsx     # Mobile detection
│   └── use-toast.ts       # Toast notifications
└── lib/
    └── utils.ts           # Utility functions & API client
```

---

## 🔌 External API Integrations

### **1. Groq AI (Llama 3.1 70B)**
- **Purpose**: All AI processing tasks
- **Endpoints**: `/v1/chat/completions`
- **Usage**: Resume parsing, job analysis, match scoring, optimization suggestions
- **Rate Limits**: Based on Groq API tier
- **Fallback**: Mock responses for development

### **2. LinkedIn API**
- **Purpose**: Job search, profile data, OAuth authentication
- **Endpoints**: 
  - `/v2/people/~` (Profile data)
  - `/v2/jobSearch` (Job search)
  - `/oauth/v2/accessToken` (Authentication)
- **Scopes**: `r_liteprofile`, `r_emailaddress`
- **Fallback**: Mock job data for development

### **3. Adzuna API**
- **Purpose**: Job data aggregation
- **Endpoints**: `/api/ads/search`
- **Usage**: Additional job postings beyond LinkedIn
- **Rate Limits**: 1000 requests/day (free tier)

### **4. Stripe API**
- **Purpose**: Payment processing, subscription management
- **Endpoints**: 
  - `/v1/customers` (Customer management)
  - `/v1/subscriptions` (Subscription handling)
  - `/v1/webhooks` (Event handling)
- **Webhooks**: Subscription status updates

### **5. OAuth Providers**
- **Google**: `/oauth2/v2/auth`, `/oauth2/v3/userinfo`
- **GitHub**: `/login/oauth/authorize`, `/user`
- **LinkedIn**: `/oauth/v2/authorization`, `/people/~`

---

## 🚀 Key Features & Data Flow

### **1. Resume Optimizer**
```
User Upload → File Processing → AI Analysis → Optimization Suggestions
     │              │              │                    │
     ▼              ▼              ▼                    ▼
PDF/DOCX → Text Extraction → Groq AI → Skills/Experience Parsing
     │              │              │                    │
     ▼              ▼              ▼                    ▼
Database → Parsed Data → Match Scoring → Improvement Tips
```

### **2. Job Match Analyzer**
```
Resume + Job → AI Comparison → Match Score → Detailed Analysis
     │              │              │              │
     ▼              ▼              ▼              ▼
Upload Files → Groq Processing → Scoring Algorithm → Suggestions
     │              │              │              │
     ▼              ▼              ▼              ▼
Database → Match History → Missing Keywords → Optimization Tips
```

### **3. Interview Preparation**
```
Job Description → AI Analysis → Question Generation → Practice Materials
     │              │              │                    │
     ▼              ▼              ▼                    ▼
Job Text → Groq Processing → Question Categories → Interview Tips
     │              │              │                    │
     ▼              ▼              ▼                    ▼
Database → Stored Questions → Technical/Behavioral → Preparation Guide
```

### **4. Job Recommendations**
```
User Profile → External APIs → Job Aggregation → AI Filtering → Recommendations
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
Skills/Experience → LinkedIn/Adzuna → Job Data → Groq Matching → Personalized Feed
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
Database → API Integration → Data Processing → Match Scoring → User Dashboard
```

---

## 🔒 Security & Authentication

### **Authentication Flow**
1. **OAuth Integration**: Google, GitHub, LinkedIn
2. **JWT Tokens**: 24-hour expiration
3. **Password Hashing**: bcrypt with salt
4. **API Security**: Bearer token authentication
5. **CORS Configuration**: Environment-specific origins

### **Data Protection**
- **File Uploads**: Size limits (10MB), type validation
- **SQL Injection**: SQLAlchemy ORM protection
- **XSS Prevention**: Input sanitization
- **Rate Limiting**: API endpoint protection

---

## 📈 Performance & Scalability

### **Database Optimization**
- **Indexes**: On frequently queried columns
- **Connection Pooling**: SQLAlchemy pool management
- **Query Optimization**: Efficient joins and filters

### **Caching Strategy**
- **Frontend**: React Query for API caching
- **Backend**: In-memory caching for AI responses
- **Database**: Query result caching

### **AI Processing**
- **Async Processing**: Non-blocking AI calls
- **Batch Operations**: Multiple job matching
- **Error Handling**: Graceful fallbacks

---

## 🛠️ Development & Deployment

### **Development Setup**
- **Backend**: `uvicorn app.main:app --reload`
- **Frontend**: `npm run dev`
- **Database**: SQLite for local development
- **Environment**: `.env` configuration

### **Production Deployment**
- **Containerization**: Docker + Docker Compose
- **Database**: PostgreSQL on Render
- **Frontend**: Vite build + static hosting
- **Backend**: Gunicorn + Uvicorn workers

### **Monitoring & Logging**
- **Structured Logging**: Python `structlog`
- **Error Tracking**: Exception handling
- **Activity Logging**: User action tracking
- **Health Checks**: API endpoint monitoring

---

