# Backend Setup Guide

## Prerequisites
- Python 3.9+
- PostgreSQL or SQLite
- pip package manager

## Installation Steps

1. Navigate to backend:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations (if using PostgreSQL):
```bash
python migrate_to_postgres.py
```

6. Start development server:
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000
