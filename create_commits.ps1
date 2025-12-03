#!/usr/bin/env pwsh

# Script to create 64 more atomic commits from current changes
# This organizes changes by module/feature for better commit history

$commitCommands = @(
    # Backend Models (6 commits)
    @("backend/app/models/user.py", "feat: enhance user model with additional fields"),
    @("backend/app/models/resume.py", "feat: improve resume model and validation"),
    @("backend/app/models/job.py", "feat: update job model with new properties"),
    @("backend/app/models/match_history.py", "feat: add match history model enhancements"),
    
    # Backend API Routes (8 commits)
    @("backend/app/api/auth.py", "feat: implement authentication endpoints"),
    @("backend/app/api/upload_resume.py", "feat: enhance resume upload functionality"),
    @("backend/app/api/upload_job.py", "feat: improve job upload endpoint"),
    @("backend/app/api/match_score.py", "feat: refactor job matching algorithm"),
    @("backend/app/api/optimize_resume.py", "feat: enhance resume optimization engine"),
    @("backend/app/api/generate_interview_questions.py", "feat: improve interview question generation"),
    @("backend/app/api/recommended_jobs.py", "feat: update job recommendations logic"),
    @("backend/app/api/linkedin_connect.py", "feat: enhance LinkedIn integration"),
    @("backend/app/api/dashboard.py", "feat: add dashboard API endpoints"),
    @("backend/app/api/job_recommendations.py", "feat: implement job recommendation service"),
    @("backend/app/api/jobs.py", "feat: add job query endpoints"),
    
    # Backend Services (10 commits)
    @("backend/app/services/resume_parser.py", "feat: improve resume parsing service"),
    @("backend/app/services/job_analyzer.py", "feat: enhance job analysis engine"),
    @("backend/app/services/match_engine.py", "feat: refactor job matching engine"),
    @("backend/app/services/interview_engine.py", "feat: upgrade interview question engine"),
    @("backend/app/services/groq_service.py", "feat: integrate Groq AI service"),
    @("backend/app/services/linkedin_service.py", "feat: enhance LinkedIn integration service"),
    @("backend/app/services/job_service.py", "feat: add job aggregation service"),
    @("backend/app/services/adzuna_service.py", "feat: integrate Adzuna job API"),
    @("backend/app/services/enhanced_job_service.py", "feat: add enhanced job search service"),
    @("backend/app/utils/auth.py", "feat: improve authentication utilities"),
    
    # Backend Utils (3 commits)
    @("backend/app/utils/helpers.py", "feat: enhance utility helper functions"),
    @("backend/app/utils/logger.py", "feat: improve logging configuration"),
    @("backend/requirements.txt", "chore: update Python dependencies"),
    @("backend/env.example", "chore: update environment variables template"),
    
    # Backend Configuration (4 commits)
    @("backend/docker-compose.yml", "chore: update Docker Compose configuration"),
    @("backend/migrate_to_postgres.py", "feat: add PostgreSQL migration script"),
    @("backend/setup_postgres.sh", "chore: add PostgreSQL setup script"),
    @("backend/setup_postgres.bat", "chore: add Windows PostgreSQL setup"),
    
    # Frontend Pages (8 commits)
    @("src/pages/Dashboard.tsx", "feat: redesign Dashboard page"),
    @("src/pages/JobMatch.tsx", "feat: improve Job Match page"),
    @("src/pages/RecommendedJobs.tsx", "feat: enhance Recommended Jobs page"),
    @("src/pages/ResumeOptimizer.tsx", "feat: update Resume Optimizer page"),
    @("src/pages/InterviewPrep.tsx", "feat: improve Interview Prep page"),
    @("src/pages/SignIn.tsx", "feat: add SignIn page with OAuth"),
    @("src/pages/SignUp.tsx", "feat: add SignUp page with OAuth"),
    @("src/pages/JobRecommendations.tsx", "feat: add Job Recommendations page"),
    
    # Frontend Components (6 commits)
    @("src/components/AppSidebar.tsx", "feat: enhance AppSidebar with new navigation"),
    @("src/components/Layout.tsx", "feat: improve main Layout component"),
    @("src/components/LinkedInConnection.tsx", "feat: add LinkedIn connection component"),
    
    # Frontend Configuration & Build (5 commits)
    @("package.json", "chore: update package dependencies and scripts"),
    @("index.html", "chore: update HTML entry point"),
    @("src/App.tsx", "feat: update main App component"),
    @("src/lib/utils.ts", "feat: enhance utility functions"),
    @("start_backend.ps1", "chore: add PowerShell backend startup script"),
    
    # Frontend Assets (3 commits)
    @("start_backend.bat", "chore: add Windows backend startup script"),
    @("favicon1.png;favicon2.png;favicon3.png;src/favicon3.png", "chore: add favicon assets"),
    @("vivid-blurred-colorful-wallpaper-background.jpg", "chore: add background assets"),
    
    # Documentation & Setup (5 commits)
    @("backend/app/schemas/", "feat: add request/response schemas"),
    @("backend/test_groq.py", "test: add Groq service test"),
    @("backend/test_interview.py", "test: add interview engine test"),
    @("backend/test_linkedin.py", "test: add LinkedIn integration test"),
    @("backend/test_rapidapi.py", "test: add RapidAPI test"),
    
    # Final Cleanup (2 commits)
    @("backend/jobalign.db", "chore: update database"),
    @("backend/env.postgres.example", "chore: add PostgreSQL environment template")
)

Write-Host "Starting to create commits..." -ForegroundColor Green
$count = 0

foreach ($item in $commitCommands) {
    $files = $item[0]
    $message = $item[1]
    
    Write-Host "[$($count + 1)/$($commitCommands.Count)] Creating commit: $message" -ForegroundColor Cyan
    
    # Add files
    git add $files.Split(";") 2>$null
    
    # Commit
    $result = git commit -m $message 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Committed" -ForegroundColor Green
    } else {
        Write-Host "✗ No changes or error" -ForegroundColor Yellow
    }
    
    $count++
}

Write-Host "`nCommit creation complete!" -ForegroundColor Green
git log --oneline --max-count=10
