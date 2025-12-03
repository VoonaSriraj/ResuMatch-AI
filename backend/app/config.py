"""
Configuration settings for JobAlign AI Backend
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    postgres_user: str = "jobalign"
    postgres_password: str = "password"
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    postgres_db: str = "jobalign"
    database_url_env: Optional[str] = None
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    
    # Groq AI
    groq_api_key: str = ""
    # Try these models in order: mixtral (most stable), llama-3.3, gemma2
    groq_model: str = "mixtral-8x7b-32768"  # Stable model, check https://console.groq.com/docs/models for latest
    
    # RapidAPI Configuration
    rapidapi_key: str = ""
    rapidapi_linkedin_host: str = "linkedin-job-search-api.p.rapidapi.com"
    
    # Adzuna API Configuration
    adzuna_app_id: str = "8450d6de"
    adzuna_app_key: str = "5ebddcf5b476183d5387ee614469371b"
    adzuna_country: str = "in"  # India
    
    # Google OAuth2
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/auth/google/callback"
    
    # GitHub OAuth2
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:3000/auth/github/callback"
    
    # LinkedIn OAuth2
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:3000/auth/linkedin/callback"
    
    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""
    
    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".pdf", ".docx", ".doc", ".txt"]
    upload_directory: str = "uploads"
    
    # App Settings
    debug: bool = False
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]
    
    @property
    def database_url(self) -> str:
        # In debug mode, always prefer SQLite to simplify local development
        if self.debug:
            return "sqlite:///./jobalign.db"
        # Otherwise respect DATABASE_URL if provided
        if self.database_url_env:
            return self.database_url_env
        # Fallback to Postgres DSN from individual vars
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        # Point explicitly to backend/.env regardless of current working directory
        env_file = str((Path(__file__).resolve().parent.parent / ".env").resolve())
        extra = "ignore"

settings = Settings()
