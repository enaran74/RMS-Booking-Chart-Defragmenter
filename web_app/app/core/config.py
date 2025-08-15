"""
Configuration settings for the RMS Booking Chart Defragmenter Web Application
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "defrag_db"
    DB_USER: str = "defrag_user"
    DB_PASSWORD: str = "DefragDB2024!"
    
    # Web Application Configuration
    WEB_APP_PORT: int = 8000
    WEB_APP_HOST: str = "0.0.0.0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # RMS API Configuration
    AGENT_ID: Optional[str] = None
    AGENT_PASSWORD: Optional[str] = None
    CLIENT_ID: Optional[str] = None
    CLIENT_PASSWORD: Optional[str] = None
    
    # Application Settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Database URL
DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
