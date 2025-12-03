#!/bin/bash
# PostgreSQL Setup Script for JobAlign

echo "🚀 JobAlign PostgreSQL Setup"
echo "============================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

echo "✅ docker-compose is available"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.postgres.example .env
    echo "✅ .env file created. Please update the values in .env file."
else
    echo "✅ .env file already exists"
fi

# Start PostgreSQL container
echo "🐘 Starting PostgreSQL container..."
docker-compose up -d db

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check if PostgreSQL is ready
until docker-compose exec db pg_isready -U jobalign -d jobalign; do
    echo "⏳ Waiting for PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run migration if SQLite database exists
if [ -f jobalign.db ]; then
    echo "📊 SQLite database found. Do you want to migrate data to PostgreSQL? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🔄 Running migration..."
        python migrate_to_postgres.py
    else
        echo "⏭️ Skipping migration"
    fi
else
    echo "📊 No SQLite database found. Creating fresh PostgreSQL database..."
    python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine); print('✅ Tables created successfully!')"
fi

echo ""
echo "🎉 PostgreSQL setup completed!"
echo ""
echo "Next steps:"
echo "1. Update your .env file with your API keys"
echo "2. Start the backend: docker-compose up backend"
echo "3. Or run locally: python -m uvicorn app.main:app --reload"
echo ""
echo "Database connection details:"
echo "Host: localhost"
echo "Port: 5432"
echo "Database: jobalign"
echo "Username: jobalign"
echo "Password: jobalign_password"
