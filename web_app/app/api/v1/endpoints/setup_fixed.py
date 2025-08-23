"""
Setup API endpoints for system configuration and management
"""

from typing import List, Dict, Any
import logging
import re
import os
import subprocess
import asyncio
from pathlib import Path
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.models.user import User
from app.core.security import get_current_user

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

class EnvironmentVariableUpdate(BaseModel):
    """Model for updating environment variables"""
    variables: Dict[str, str]

class EnvironmentVariableResponse(BaseModel):
    """Response model for environment variables"""
    variables: Dict[str, str]
    file_exists: bool
    file_path: str

def get_env_file_path() -> Path:
    """Get the path to the .env file"""
    # Try current working directory first, then project root
    possible_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent.parent.parent.parent / ".env"
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Return the first one (current directory) if none exist
    return possible_paths[0]

def parse_env_file(file_path: Path) -> Dict[str, str]:
    """Parse an existing .env file and return variables as dict"""
    variables = {}
    
    if not file_path.exists():
        return variables
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    variables[key] = value
                    
    except Exception as e:
        logger.error(f"Error parsing .env file: {e}")
    
    return variables

def validate_environment_variables(variables: Dict[str, str]) -> None:
    """Validate environment variables"""
    errors = []
    
    for key, value in variables.items():
        # Type validation
        if not isinstance(value, str):
            errors.append(f"{key}: must be a string")
            continue
        
        # Length validation
        if len(value) > 1000:
            errors.append(f"{key}: value too long (max 1000 characters)")
        
        # Format validation for specific keys
        if key.endswith('_PORT') and value:
            try:
                port = int(value)
                if not (1 <= port <= 65535):
                    errors.append(f"{key}: must be a valid port number (1-65535)")
            except ValueError:
                errors.append(f"{key}: must be a valid port number")
        
        if key.endswith('_EMAIL') and value:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                errors.append(f"{key}: must be a valid email address")
        
        # Security checks
        if any(pattern in value.lower() for pattern in ['<script', 'javascript:', 'data:', 'vbscript:']):
            errors.append(f"{key}: contains potentially unsafe content")
    
    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"Validation errors: {'; '.join(errors)}"
        )

async def restart_application_containers() -> None:
    """Restart the Docker containers to apply new environment configuration"""
    try:
        # We're running inside a container, so we need to restart from outside
        # This will restart the entire docker-compose stack
        logger.info("Initiating application restart to apply configuration changes...")
        
        # Schedule restart after a short delay to allow the API response to complete
        async def delayed_restart():
            await asyncio.sleep(3)  # Give time for the response to be sent
            try:
                # Use docker-compose down and up to ensure clean restart with new environment
                logger.info("Stopping containers...")
                process_down = await asyncio.create_subprocess_exec(
                    'docker-compose', 'down',
                    cwd='/opt/defrag-app',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process_down.communicate()
                
                await asyncio.sleep(2)  # Brief pause between down and up
                
                logger.info("Starting containers with new configuration...")
                process_up = await asyncio.create_subprocess_exec(
                    'docker-compose', 'up', '-d',
                    cwd='/opt/defrag-app',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process_up.communicate()
                
                if process_up.returncode == 0:
                    logger.info("Application containers restarted successfully with new configuration")
                else:
                    logger.error(f"Failed to start containers: {stderr.decode()}")
                    
            except Exception as e:
                logger.error(f"Error during delayed restart: {e}")
        
        # Run the restart in the background
        asyncio.create_task(delayed_restart())
        
    except Exception as e:
        logger.error(f"Error initiating application restart: {e}")
        # Don't raise the exception as this shouldn't fail the save operation

def write_env_file(file_path: Path, variables: Dict[str, str]) -> None:
    """Write environment variables to .env file with proper formatting and defaults"""
    
    # Define the comprehensive defaults for all environment variables
    defaults = {
        # Critical RMS API credentials - these should be provided by user
        'AGENT_ID': '***REMOVED***',  # Use the actual values from variables if provided
        'AGENT_PASSWORD': '***REMOVED***',
        'CLIENT_ID': '***REMOVED***', 
        'CLIENT_PASSWORD': '***REMOVED***',
        
        # Database settings - use current working defaults
        'DB_HOST': 'localhost',
        'DB_PORT': '5433',  # Use the port we're actually using
        'DB_NAME': 'defrag_db',
        'DB_USER': 'defrag_user',
        'DB_PASSWORD': 'DefragDB2024!',
        
        # Web application settings - use production-ready defaults
        'WEB_APP_PORT': '8000',
        'WEB_APP_HOST': '0.0.0.0',
        'SECRET_KEY': 'your-secret-key-here-change-this-in-production',
        'JWT_SECRET_KEY': 'your-jwt-secret-key-here-change-this-in-production',
        'PROPERTY_REFRESH_INTERVAL_HOURS': '1',
        
        # Analysis settings - default to training mode and user's target properties
        'TARGET_PROPERTIES': 'CALI',
        'USE_TRAINING_DB': 'true',  # Always default to training as requested
        
        # Email settings - use user preferences or sensible defaults
        'ENABLE_EMAILS': 'false',
        'SEND_CONSOLIDATED_EMAIL': 'false',
        'CONSOLIDATED_EMAIL_RECIPIENT': 'operations@discoveryparks.com.au',
        
        # SMTP settings - use user values or defaults
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SENDER_EMAIL': '***REMOVED***',
        'SENDER_DISPLAY_NAME': 'DHP Defragmentation System',
        'APP_PASSWORD': '***REMOVED***',
        'TEST_RECIPIENT': 'operations@discoveryparks.com.au',
        
        # Scheduling - use sensible production defaults
        'CRON_SCHEDULE': '0 2 * * *',  # 2 AM daily
        'ENABLE_CRON': 'true',
        
        # Logging - use production defaults
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        
        # Output - use production defaults
        'OUTPUT_DIR': '/app/output',
        
        # Container settings - use production defaults
        'TZ': 'Australia/Sydney',
        'CONTAINER_USER': 'appuser',
        'CONTAINER_GROUP': 'appuser',
        
        # Health check - use production defaults
        'HEALTH_CHECK_INTERVAL': '30s',
        'HEALTH_CHECK_TIMEOUT': '10s',
        'HEALTH_CHECK_RETRIES': '3',
        
        # Backup - use production defaults
        'BACKUP_RETENTION_DAYS': '30',
        'BACKUP_ENABLED': 'true'
    }
    
    # Override defaults with user-provided values (only for non-empty values)
    final_variables = defaults.copy()
    for key, value in variables.items():
        if value and value.strip():  # Only override if user provided a non-empty value
            final_variables[key] = value
    
    try:
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the .env content by writing each variable directly
        lines = [
            "# ==============================================================================",
            "# RMS Booking Chart Defragmenter - Unified Configuration",
            "# ==============================================================================",
            "# This configuration supports both the original CLI application and web interface",
            "# Copy this file to .env and update with your actual credentials",
            "# ",
            "# SECURITY NOTE: Never commit the .env file to version control!",
            "",
            "# ==============================================================================",
            "# RMS API CREDENTIALS (REQUIRED for both applications)",
            "# ==============================================================================",
            "# These credentials are used by both the original analyzer and web app",
            f"AGENT_ID={final_variables['AGENT_ID']}",
            f"AGENT_PASSWORD={final_variables['AGENT_PASSWORD']}",
            f"CLIENT_ID={final_variables['CLIENT_ID']}",
            f"CLIENT_PASSWORD={final_variables['CLIENT_PASSWORD']}",
            "",
            "# ==============================================================================",
            "# DATABASE CONFIGURATION (Web App)",
            "# ==============================================================================",
            "# PostgreSQL configuration for the web interface",
            f"DB_HOST={final_variables['DB_HOST']}",
            f"DB_PORT={final_variables['DB_PORT']}",
            f"DB_NAME={final_variables['DB_NAME']}",
            f"DB_USER={final_variables['DB_USER']}",
            f"DB_PASSWORD={final_variables['DB_PASSWORD']}",
            "",
            "# ==============================================================================",
            "# WEB APPLICATION CONFIGURATION",
            "# ==============================================================================",
            "# Web server settings",
            f"WEB_APP_PORT={final_variables['WEB_APP_PORT']}",
            f"WEB_APP_HOST={final_variables['WEB_APP_HOST']}",
            f"SECRET_KEY={final_variables['SECRET_KEY']}",
            f"JWT_SECRET_KEY={final_variables['JWT_SECRET_KEY']}",
            "",
            "# Property data refresh interval (hours)",
            f"PROPERTY_REFRESH_INTERVAL_HOURS={final_variables['PROPERTY_REFRESH_INTERVAL_HOURS']}",
            "",
            "# ==============================================================================",
            "# ORIGINAL APPLICATION CONFIGURATION",
            "# ==============================================================================",
            "# Analysis settings for the original CLI application",
            f"TARGET_PROPERTIES={final_variables['TARGET_PROPERTIES']}",
            "# TARGET_PROPERTIES=SADE,QROC,TCRA  # Example: specific properties (comma-separated)",
            "",
            "# Database mode selection",
            f"USE_TRAINING_DB={final_variables['USE_TRAINING_DB']}",
            "# USE_TRAINING_DB=true  # Set to true to use training database for testing",
            "",
            "# ==============================================================================",
            "# EMAIL CONFIGURATION (Original App)",
            "# ==============================================================================",
            "# Enable/disable email notifications with Excel attachments",
            f"ENABLE_EMAILS={final_variables['ENABLE_EMAILS']}",
            "# ENABLE_EMAILS=true  # Set to true to enable email notifications",
            "",
            "# Enable/disable consolidated report email to operations team",
            f"SEND_CONSOLIDATED_EMAIL={final_variables['SEND_CONSOLIDATED_EMAIL']}",
            "# SEND_CONSOLIDATED_EMAIL=true  # Set to true to send consolidated report",
            "",
            "# Email address for consolidated report (when SEND_CONSOLIDATED_EMAIL=true)",
            f"CONSOLIDATED_EMAIL_RECIPIENT={final_variables['CONSOLIDATED_EMAIL_RECIPIENT']}",
            "",
            "# ==============================================================================",
            "# SMTP CONFIGURATION (Required only if ENABLE_EMAILS=true)",
            "# ==============================================================================",
            "# Gmail SMTP settings for sending notification emails",
            f"SMTP_SERVER={final_variables['SMTP_SERVER']}",
            f"SMTP_PORT={final_variables['SMTP_PORT']}",
            f"SENDER_EMAIL={final_variables['SENDER_EMAIL']}",
            f"SENDER_DISPLAY_NAME={final_variables['SENDER_DISPLAY_NAME']}",
            f"APP_PASSWORD={final_variables['APP_PASSWORD']}",
            f"TEST_RECIPIENT={final_variables['TEST_RECIPIENT']}",
            "",
            "# Note: For Gmail, you need to:",
            "# 1. Enable 2-factor authentication on your Google account",
            "# 2. Generate an \"App Password\" (not your regular password)",
            "# 3. Use the App Password in the APP_PASSWORD field above",
            "",
            "# ==============================================================================",
            "# SCHEDULING CONFIGURATION",
            "# ==============================================================================",
            "# Cron schedule for automated analysis (format: minute hour day month weekday)",
            f"CRON_SCHEDULE={final_variables['CRON_SCHEDULE']}",
            "# CRON_SCHEDULE=0 */6 * * *  # Every 6 hours",
            "# CRON_SCHEDULE=0 2 * * 1-5  # Weekdays only at 2:00 AM",
            "",
            "# Enable/disable cron scheduling",
            f"ENABLE_CRON={final_variables['ENABLE_CRON']}",
            "",
            "# ==============================================================================",
            "# LOGGING CONFIGURATION",
            "# ==============================================================================",
            "# Set logging verbosity level",
            f"LOG_LEVEL={final_variables['LOG_LEVEL']}",
            "# LOG_LEVEL=DEBUG  # For more detailed logging (useful for troubleshooting)",
            "",
            "# Log directory (within container)",
            f"LOG_DIR={final_variables['LOG_DIR']}",
            "",
            "# ==============================================================================",
            "# OUTPUT CONFIGURATION",
            "# ==============================================================================",
            "# Directory where Excel reports and analysis files are saved",
            f"OUTPUT_DIR={final_variables['OUTPUT_DIR']}",
            "",
            "# ==============================================================================",
            "# CONTAINER CONFIGURATION",
            "# ==============================================================================",
            "# Container timezone",
            f"TZ={final_variables['TZ']}",
            "",
            "# Container user configuration",
            f"CONTAINER_USER={final_variables['CONTAINER_USER']}",
            f"CONTAINER_GROUP={final_variables['CONTAINER_GROUP']}",
            "",
            "# ==============================================================================",
            "# HEALTH CHECK CONFIGURATION",
            "# ==============================================================================",
            "# Health check endpoints and intervals",
            f"HEALTH_CHECK_INTERVAL={final_variables['HEALTH_CHECK_INTERVAL']}",
            f"HEALTH_CHECK_TIMEOUT={final_variables['HEALTH_CHECK_TIMEOUT']}",
            f"HEALTH_CHECK_RETRIES={final_variables['HEALTH_CHECK_RETRIES']}",
            "",
            "# ==============================================================================",
            "# BACKUP CONFIGURATION",
            "# ==============================================================================",
            "# Backup settings for data persistence",
            f"BACKUP_RETENTION_DAYS={final_variables['BACKUP_RETENTION_DAYS']}",
            f"BACKUP_ENABLED={final_variables['BACKUP_ENABLED']}",
            ""
        ]
        
        # Write the content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            
        logger.info(f"Successfully wrote .env file to {file_path} with {len(final_variables)} variables")
        
    except Exception as e:
        logger.error(f"Error writing .env file: {e}")
        raise

@router.get("/environment", response_model=EnvironmentVariableResponse)
async def get_environment_variables(
    current_user: User = Depends(get_current_user)
):
    """Get current environment variables from .env file"""
    try:
        env_path = get_env_file_path()
        variables = parse_env_file(env_path)
        
        return {
            "variables": variables,
            "file_exists": env_path.exists(),
            "file_path": str(env_path)
        }
        
    except Exception as e:
        logger.error(f"Error reading environment variables: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read environment variables: {str(e)}"
        )

@router.post("/environment")
async def update_environment_variables(
    update_request: EnvironmentVariableUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update environment variables in .env file"""
    try:
        # Validate the variables
        validate_environment_variables(update_request.variables)
        
        # Get the .env file path
        env_path = get_env_file_path()
        
        # Create backup if file exists
        if env_path.exists():
            backup_path = env_path.with_suffix('.env.backup')
            backup_path.write_text(env_path.read_text())
            logger.info(f"Created backup of .env file at {backup_path}")
        
        # Write the new .env file
        write_env_file(env_path, update_request.variables)
        
        # Return the updated configuration
        variables = parse_env_file(env_path)
        
        # Trigger application restart to apply changes
        await restart_application_containers()
        
        return {
            "message": "Environment variables updated successfully. Application is restarting to apply changes.",
            "variables": variables,
            "file_path": str(env_path),
            "restart_initiated": True
        }
        
    except Exception as e:
        logger.error(f"Error updating environment variables: {e}")
        
        # Try to restore backup if something went wrong
        try:
            env_path = get_env_file_path()
            backup_path = env_path.with_suffix('.env.backup')
            if backup_path.exists():
                env_path.write_text(backup_path.read_text())
                logger.info("Restored .env file from backup due to error")
        except Exception as restore_error:
            logger.error(f"Failed to restore backup: {restore_error}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update environment variables: {str(e)}"
        )

@router.get("/test-db")
async def test_database_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test database connection and return basic info"""
    try:
        # Test basic query
        result = db.execute(text("SELECT version()"))
        version_info = result.scalar()
        
        # Get user count
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        
        return {
            "status": "success",
            "database_version": version_info,
            "user_count": user_count,
            "message": "Database connection successful"
        }
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )

