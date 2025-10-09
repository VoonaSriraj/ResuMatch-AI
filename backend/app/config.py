"""
Configuration settings for JobAlign AI Backend
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    postgres_user: str = os.getenv("POSTGRES_USER", "jobalign")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "password")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_db: str = os.getenv("POSTGRES_DB", "jobalign")
    database_url_env: str | None = os.getenv("DATABASE_URL")
    
    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    
    # Groq AI
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = "llama3-70b-8192"  # Default Groq model
    
    # LinkedIn OAuth2
    linkedin_client_id: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    linkedin_client_secret: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    linkedin_redirect_uri: str = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:3000/auth/linkedin/callback")
    
    # Google OAuth2
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
    
    # GitHub OAuth2
    github_client_id: str = os.getenv("GITHUB_CLIENT_ID", "")
    github_client_secret: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    github_redirect_uri: str = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:3000/auth/github/callback")
    
    # Stripe
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_publishable_key: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".pdf", ".docx", ".doc", ".txt"]
    upload_directory: str = "uploads"
    
    # App Settings
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    @property
    def database_url(self) -> str:
        if self.database_url_env:
            return self.database_url_env
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
