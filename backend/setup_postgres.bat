@echo off
REM PostgreSQL Setup Script for JobAlign (Windows)

echo 🚀 JobAlign PostgreSQL Setup
echo =============================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ docker-compose not found. Please install docker-compose.
    pause
    exit /b 1
)

echo ✅ docker-compose is available

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.postgres.example .env
    echo ✅ .env file created. Please update the values in .env file.
) else (
    echo ✅ .env file already exists
)

REM Start PostgreSQL container
echo 🐘 Starting PostgreSQL container...
docker-compose up -d db

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
timeout /t 10 /nobreak >nul

REM Check if PostgreSQL is ready
:wait_for_postgres
docker-compose exec db pg_isready -U jobalign -d jobalign >nul 2>&1
if %errorlevel% neq 0 (
    echo ⏳ Waiting for PostgreSQL...
    timeout /t 2 /nobreak >nul
    goto wait_for_postgres
)

echo ✅ PostgreSQL is ready!

REM Run migration if SQLite database exists
if exist jobalign.db (
    echo 📊 SQLite database found. Do you want to migrate data to PostgreSQL? (y/N)
    set /p response=
    if /i "%response%"=="y" (
        echo 🔄 Running migration...
        python migrate_to_postgres.py
    ) else (
        echo ⏭️ Skipping migration
    )
) else (
    echo 📊 No SQLite database found. Creating fresh PostgreSQL database...
    python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine); print('✅ Tables created successfully!')"
)

echo.
echo 🎉 PostgreSQL setup completed!
echo.
echo Next steps:
echo 1. Update your .env file with your API keys
echo 2. Start the backend: docker-compose up backend
echo 3. Or run locally: python -m uvicorn app.main:app --reload
echo.
echo Database connection details:
echo Host: localhost
echo Port: 5432
echo Database: jobalign
echo Username: jobalign
echo Password: jobalign_password
pause
