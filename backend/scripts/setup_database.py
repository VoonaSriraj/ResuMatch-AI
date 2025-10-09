#!/usr/bin/env python3
"""
Database setup script for JobAlign AI Backend
Creates database tables and initial data
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to the path so we can import our app
sys.path.append(str(Path(__file__).parent.parent))

from app.database import engine, Base
from app.models import user, resume, job, match_history, subscription, activity_log
from app.config import settings
from sqlalchemy import create_engine
from app.utils.logger import get_logger

logger = get_logger(__name__)

def create_tables():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
        # Test the connection
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful!")
            
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise

def check_database_connection():
    """Check if database connection is working"""
    try:
        logger.info(f"Testing connection to: {settings.database_url}")
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"Connected to PostgreSQL: {version}")
            return True
            
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def main():
    """Main setup function"""
    logger.info("Starting JobAlign AI Backend database setup...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Cannot connect to database. Please check your configuration.")
        sys.exit(1)
    
    # Create tables
    create_tables()
    
    logger.info("Database setup completed successfully!")
    logger.info("You can now start the application with: uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()
