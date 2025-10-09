#!/usr/bin/env python3
"""
Test SQLite database with compatible models
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

try:
    print("🔧 Testing SQLite database setup...")
    
    from sqlalchemy import create_engine, text
    from app.database import Base
    from app.models_sqlite import User, Resume, JobDescription, RecommendedJob, MatchHistory, Subscription, ActivityLog
    
    # Create SQLite engine
    engine = create_engine("sqlite:///./jobalign.db", echo=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 as test"))
        print("✅ SQLite connection successful!")
        print(f"   Test result: {result.fetchone()}")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    # List created tables
    print("📋 Created tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"   - {table_name}")
    
    # Test inserting a user
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Check if users table is empty
    user_count = db.query(User).count()
    print(f"📊 Current users in database: {user_count}")
    
    db.close()
    
    print("\n🎉 Database setup completed!")
    print("📁 Database file: jobalign.db")
    print("🚀 You can now start the application!")
    
except Exception as e:
    print(f"❌ Database setup failed: {e}")
    import traceback
    traceback.print_exc()
