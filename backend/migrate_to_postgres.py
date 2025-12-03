#!/usr/bin/env python3
"""
Database migration script from SQLite to PostgreSQL
This script helps migrate existing data from SQLite to PostgreSQL
"""

import sqlite3
import psycopg2
import json
import os
from datetime import datetime
from app.config import settings
from app.database import engine, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

def get_sqlite_connection():
    """Get SQLite connection"""
    return sqlite3.connect('jobalign.db')

def get_postgres_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password
    )

def migrate_table_data(table_name, sqlite_conn, postgres_conn):
    """Migrate data from SQLite table to PostgreSQL"""
    print(f"Migrating {table_name}...")
    
    # Get data from SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"No data found in {table_name}")
        return
    
    # Get column names
    columns = [description[0] for description in sqlite_cursor.description]
    
    # Insert data into PostgreSQL
    postgres_cursor = postgres_conn.cursor()
    
    # Create placeholders for the INSERT statement
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    
    insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    try:
        postgres_cursor.executemany(insert_query, rows)
        postgres_conn.commit()
        print(f"Successfully migrated {len(rows)} rows to {table_name}")
    except Exception as e:
        print(f"Error migrating {table_name}: {e}")
        postgres_conn.rollback()

def create_tables():
    """Create all tables in PostgreSQL"""
    print("Creating tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

def migrate_data():
    """Migrate all data from SQLite to PostgreSQL"""
    print("Starting data migration...")
    
    # Create tables first
    create_tables()
    
    # Connect to both databases
    sqlite_conn = get_sqlite_connection()
    postgres_conn = get_postgres_connection()
    
    try:
        # List of tables to migrate (in order to respect foreign key constraints)
        tables = [
            'users',
            'user_profiles', 
            'resumes',
            'job_descriptions',
            'jobs',
            'match_history',
            'recommended_jobs',
            'subscriptions',
            'activity_logs'
        ]
        
        for table in tables:
            try:
                migrate_table_data(table, sqlite_conn, postgres_conn)
            except Exception as e:
                print(f"Skipping {table}: {e}")
                continue
                
    finally:
        sqlite_conn.close()
        postgres_conn.close()
    
    print("Data migration completed!")

def verify_migration():
    """Verify that migration was successful"""
    print("Verifying migration...")
    
    postgres_conn = get_postgres_connection()
    postgres_cursor = postgres_conn.cursor()
    
    tables = ['users', 'resumes', 'job_descriptions', 'jobs', 'match_history', 'activity_logs']
    
    for table in tables:
        try:
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = postgres_cursor.fetchone()[0]
            print(f"{table}: {count} records")
        except Exception as e:
            print(f"Error checking {table}: {e}")
    
    postgres_conn.close()

if __name__ == "__main__":
    print("JobAlign Database Migration Tool")
    print("=" * 40)
    
    # Check if PostgreSQL is available
    try:
        postgres_conn = get_postgres_connection()
        postgres_conn.close()
        print("PostgreSQL connection successful!")
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}")
        print("Make sure PostgreSQL is running and accessible.")
        exit(1)
    
    # Check if SQLite database exists
    if not os.path.exists('jobalign.db'):
        print("SQLite database not found!")
        exit(1)
    
    print("SQLite database found!")
    
    # Ask for confirmation
    response = input("Do you want to proceed with migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        exit(0)
    
    # Perform migration
    migrate_data()
    verify_migration()
    
    print("Migration completed successfully!")
    print("You can now switch to PostgreSQL by setting DEBUG=false in your environment.")
