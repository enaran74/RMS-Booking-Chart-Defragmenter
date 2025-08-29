"""
Configuration settings for the RMS Booking Chart Defragmenter Web Application
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
import secrets
import hashlib

def _generate_secure_key(prefix: str = "", length: int = 64) -> str:
    """Generate a cryptographically secure key with optional prefix"""
    # Generate random bytes and encode as URL-safe base64
    random_bytes = secrets.token_bytes(length)
    # Create a secure hash to ensure fixed length and valid characters
    secure_hash = hashlib.sha256(random_bytes).hexdigest()
    return f"{prefix}{secure_hash}" if prefix else secure_hash

def _get_fallback_db_password() -> str:
    """Generate a secure fallback database password"""
    # Use a combination of hostname, timestamp, and random data for uniqueness
    hostname = os.environ.get('HOSTNAME', 'defrag-app')
    random_component = secrets.token_hex(16)
    combined = f"DefragDB-{hostname}-{random_component}"
    # Hash to create a fixed-length, secure password
    return hashlib.sha256(combined.encode()).hexdigest()[:24] + "!"

class Settings(BaseSettings):
    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "defrag_db"
    DB_USER: str = "defrag_user"
    DB_PASSWORD: str = _get_fallback_db_password()  # Secure fallback, overridden by environment variable
    
    # Web Application Configuration
    WEB_APP_PORT: int = 8000
    WEB_APP_HOST: str = "0.0.0.0"  # nosec B104: Required in Docker to bind inside container
    
    # Security - Generate cryptographically secure defaults
    SECRET_KEY: str = _generate_secure_key("dhp-secret-")  # Secure fallback, overridden by environment variable
    JWT_SECRET_KEY: str = _generate_secure_key("dhp-jwt-")  # Secure fallback, overridden by environment variable  
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Reduced for better security
    
    # RMS API Configuration - MUST be set via environment variables
    # These placeholder values clearly indicate setup is required
    AGENT_ID: str = "SETUP_REQUIRED_VIA_ENVIRONMENT_VARIABLE"
    AGENT_PASSWORD: str = "SETUP_REQUIRED_VIA_ENVIRONMENT_VARIABLE"
    CLIENT_ID: str = "SETUP_REQUIRED_VIA_ENVIRONMENT_VARIABLE"
    CLIENT_PASSWORD: str = "SETUP_REQUIRED_VIA_ENVIRONMENT_VARIABLE"
    USE_TRAINING_DB: bool = True
    
    # Application Settings
    DEBUG: bool = False  # Force disabled in production for security
    LOG_LEVEL: str = "INFO"
    
    def __post_init__(self):
        """Post-initialization security checks"""
        # Force disable debug mode in production (when not explicitly in development)
        if os.environ.get('ENVIRONMENT', 'production').lower() == 'production':
            object.__setattr__(self, 'DEBUG', False)
        
        # Validate critical security settings
        if self.SECRET_KEY == "your-secret-key-here":
            raise ValueError("SECRET_KEY must be changed from default value")
        if self.JWT_SECRET_KEY == "your-jwt-secret-key-here":
            raise ValueError("JWT_SECRET_KEY must be changed from default value")
    
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
    # Analysis settings for the CLI application
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
