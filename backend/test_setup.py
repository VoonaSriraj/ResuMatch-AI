#!/usr/bin/env python3
"""
Simple test script to verify database setup
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

# Try SQLite first (no installation required)
try:
    print("🔧 Testing SQLite database setup...")
    
    from sqlalchemy import create_engine, text
    from app.models import user, resume, job, match_history, subscription, activity_log
    
    # Create SQLite engine
    engine = create_engine("sqlite:///./jobalign.db", echo=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ SQLite connection successful!")
    
    # Create tables
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    print("\n🎉 Database setup completed!")
    print("📁 Database file: jobalign.db")
    print("🚀 You can now start the application with: uvicorn app.main:app --reload")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure you're in the backend directory and have activated the virtual environment")
except Exception as e:
    print(f"❌ Database setup failed: {e}")
    print("Please check your configuration")
