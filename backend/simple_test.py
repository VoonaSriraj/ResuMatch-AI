#!/usr/bin/env python3
"""
Simple database test without config dependencies
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
    
    # Create SQLite engine
    engine = create_engine("sqlite:///./jobalign.db", echo=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 as test"))
        print("✅ SQLite connection successful!")
        print(f"   Test result: {result.fetchone()}")
    
    # Import all models to register them
    from app.models import user, resume, job, match_history, subscription, activity_log
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    # List created tables
    print("📋 Created tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"   - {table_name}")
    
    print("\n🎉 Database setup completed!")
    print("📁 Database file: jobalign.db")
    print("🚀 You can now start the application!")
    
except Exception as e:
    print(f"❌ Database setup failed: {e}")
    import traceback
    traceback.print_exc()
