"""
Database configuration and session management
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# Create database engine
def get_engine_kwargs():
    if "sqlite" in settings.database_url:
        return {
            "connect_args": {
                "check_same_thread": False,
                "timeout": 30,  # Increase timeout to 30 seconds
                "isolation_level": None,  # Let SQLAlchemy handle transactions
                "uri": True  # Enable URI mode for additional parameters
            },
            "echo": settings.debug,
            "pool_pre_ping": True  # Enable connection health checks
        }
    else:  # PostgreSQL
        return {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "pool_size": 10,
            "max_overflow": 20,
            "echo": settings.debug
        }

def setup_sqlite_engine():
    engine = create_engine(
        settings.database_url,
        **get_engine_kwargs()
    )
    
    # Enable WAL mode for SQLite to improve concurrency
    if "sqlite" in settings.database_url:
        from sqlalchemy import event
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds
                cursor.close()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to set SQLite PRAGMAs: {e}")
    
    return engine

engine = setup_sqlite_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database metadata for migrations
metadata = MetaData()
