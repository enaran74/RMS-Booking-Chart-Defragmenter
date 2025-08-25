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
    DB_PASSWORD: str = "DefragDB2024!"  # nosec B105 - Will be overridden by environment variable
    
    # Web Application Configuration
    WEB_APP_PORT: int = 8000
    WEB_APP_HOST: str = "0.0.0.0"  # nosec B104: Required in Docker to bind inside container
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # nosec B105 - Will be overridden by environment variable
    JWT_SECRET_KEY: str = "your-jwt-secret-key-here"  # nosec B105 - Will be overridden by environment variable
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # RMS API Configuration
    AGENT_ID: str = "***REMOVED***"
    AGENT_PASSWORD: str = "***REMOVED***"
    CLIENT_ID: str = "***REMOVED***"
    CLIENT_PASSWORD: str = "***REMOVED***"
    USE_TRAINING_DB: bool = True
    
    # Application Settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Property Refresh Configuration
    PROPERTY_REFRESH_INTERVAL_HOURS: int = 1
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # =============================================================================
    # CLI APPLICATION CONFIGURATION (Additional variables for unified config)
    # =============================================================================
    # Analysis settings for the original CLI application
    TARGET_PROPERTIES: str = "ALL"
    
    # Email Configuration
    ENABLE_EMAILS: bool = False
    SEND_CONSOLIDATED_EMAIL: bool = False
    CONSOLIDATED_EMAIL_RECIPIENT: str = "operations@discoveryparks.com.au"
    
    # SMTP Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SENDER_EMAIL: str = "your_email@yourdomain.com"
    SENDER_DISPLAY_NAME: str = "DHP Defragmentation System"
    APP_PASSWORD: str = "your_gmail_app_password_here"
    TEST_RECIPIENT: str = "your_test_email@yourdomain.com"
    
    # Scheduling Configuration
    CRON_SCHEDULE: str = "0 2 * * *"
    ENABLE_CRON: bool = True
    
    # Output Configuration
    OUTPUT_DIR: str = "/app/output"
    LOG_DIR: str = "/app/logs"
    
    # Container Configuration
    TZ: str = "Australia/Sydney"
    CONTAINER_USER: str = "appuser"
    CONTAINER_GROUP: str = "appuser"
    
    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: str = "30s"
    HEALTH_CHECK_TIMEOUT: str = "10s"
    HEALTH_CHECK_RETRIES: str = "3"
    
    # Backup Configuration
    BACKUP_RETENTION_DAYS: str = "30"
    BACKUP_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Database URL
DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# Add a helper to hot-reload settings from the mounted .env file
# This is useful after updating the .env via the Setup screen

def reload_settings() -> Settings:
    global settings
    settings = Settings()  # pydantic-settings will re-read env_file
    return settings
