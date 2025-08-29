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
from app.core import config as app_config

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
    # Optional sync diagnostics
    host_exists: bool | None = None
    container_exists: bool | None = None
    in_sync: bool | None = None

def get_env_file_path() -> Path:
    """Get the path to the .env file - use shared location for both CLI and web app"""
    # Priority order for shared configuration
    possible_paths = [
        Path("/opt/defrag-app/.env"),  # Preferred host-mounted location
        Path("/app/.env"),            # In-container fallback
        Path("/etc/bookingchart-defragmenter/config.env"),  # CLI config location  
        Path.cwd() / ".env",          # Current working directory
        Path(__file__).parent.parent.parent.parent.parent / ".env"  # Project root
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Return the primary shared location if none exist
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
                    
    except Exception as error:
        logger.error(f"Error parsing .env file: {error}")
    
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
        
        # Only validate specific email address fields
        email_fields = ['SENDER_EMAIL', 'CONSOLIDATED_EMAIL_RECIPIENT', 'TEST_RECIPIENT']
        if key in email_fields and value:
            import re as regex_module
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not regex_module.match(email_pattern, value):
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
                    
            except Exception as error:
                logger.error(f"Error during delayed restart: {error}")
        
        # Run the restart in the background
        asyncio.create_task(delayed_restart())
        
    except Exception as error:
        logger.error(f"Error initiating application restart: {error}")
        # Don't raise the exception as this shouldn't fail the save operation

def sync_env_files(primary_path: Path, content: str) -> None:
    """Synchronize .env file between host and container locations"""
    try:
        # Define all required locations
        host_path = Path("/opt/defrag-app/.env")        # For docker-compose variable substitution
        container_path = Path("/app/.env")              # Container root location
        working_dir_path = Path("/app/web/.env")        # Working directory for Pydantic Settings
        
        # Ensure all locations have the same content
        for path in [host_path, container_path, working_dir_path]:
            if path != primary_path:  # Don't write to the same file we just wrote
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Synchronized .env file to {path}")
                except Exception as error:
                    logger.warning(f"Could not sync to {path}: {error}")
                    
    except Exception as error:
        logger.warning(f"Error during .env file synchronization: {error}")

def write_env_file(file_path: Path, variables: Dict[str, str]) -> None:
    """Write environment variables to .env file with proper formatting and defaults"""
    
    # Define the comprehensive defaults for all environment variables
    defaults = {
        # Critical RMS API credentials - MUST be provided by user via Setup wizard
        'AGENT_ID': 'YOUR_AGENT_ID_HERE',
        'AGENT_PASSWORD': 'YOUR_AGENT_PASSWORD_HERE',
        'CLIENT_ID': 'YOUR_CLIENT_ID_HERE',
        'CLIENT_PASSWORD': 'YOUR_CLIENT_PASSWORD_HERE',
        
        # Database settings - use current working defaults
        'DB_HOST': 'localhost',
        'DB_PORT': '5433',  # Use the port we're actually using
        'DB_NAME': 'defrag_db',
        'DB_USER': 'defrag_user',
        'DB_PASSWORD': 'DefragDB2024!',
        
        # Web application settings - use production-ready defaults
        'WEB_APP_PORT': '8000',
        'WEB_APP_HOST': '0.0.0.0',  # nosec B104: Docker container binding
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
        
        # SMTP settings - MUST be provided by user via Setup wizard
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SENDER_EMAIL': 'YOUR_EMAIL@YOURDOMAIN.COM',
        'SENDER_DISPLAY_NAME': 'DHP Defragmentation System',
        'APP_PASSWORD': 'YOUR_GMAIL_APP_PASSWORD_HERE',
        'TEST_RECIPIENT': 'YOUR_TEST_EMAIL@YOURDOMAIN.COM',
        
        # Scheduling - use sensible production defaults
        'CRON_SCHEDULE': '0 2 * * *',  # 2 AM daily
        'ENABLE_CRON': 'true',
        
        # Logging - use production defaults
        'LOG_LEVEL': 'INFO',
        'LOG_DIR': '/app/logs',
        
        # Output - use production defaults
        'OUTPUT_DIR': '/app/output',
        
        # Container settings - use production defaults
        'TZ': 'Australia/Sydney'
    }
    
    # Override defaults with user-provided values (only for non-empty values)
    final_variables = defaults.copy()
    for key, value in variables.items():
        if value and value.strip():  # Only override if user provided a non-empty value
            final_variables[key] = value
    
    try:
        logger.info(f"WRITE_ENV: Target path={file_path}")
        logger.info(f"WRITE_ENV: Incoming USE_TRAINING_DB={variables.get('USE_TRAINING_DB')}")
        logger.info(f"WRITE_ENV: Final USE_TRAINING_DB={final_variables.get('USE_TRAINING_DB')}")
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the .env content by writing each variable directly
        lines = [
            "# ==============================================================================",
            "# RMS Booking Chart Defragmenter - Unified Configuration",
            "# ==============================================================================",
            "# This configuration supports both the CLI application and web interface",
            "# Copy this file to .env and update with your actual credentials",
            "# ",
            "# SECURITY NOTE: Never commit the .env file to version control!",
            "",
            "# ==============================================================================",
            "# RMS API CREDENTIALS (REQUIRED for both applications)",
            "# ==============================================================================",
            "# These credentials are used by both the CLI analyzer and web app",
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
            "# CLI APPLICATION CONFIGURATION",
            "# ==============================================================================",
            "# Analysis settings for the CLI application",
            f"TARGET_PROPERTIES={final_variables['TARGET_PROPERTIES']}",
            "# TARGET_PROPERTIES=SADE,QROC,TCRA  # Example: specific properties (comma-separated)",
            "",
            "# Database mode selection",
            f"USE_TRAINING_DB={final_variables['USE_TRAINING_DB']}",
            "# USE_TRAINING_DB=true  # Set to true to use training database for testing",
            "",
            "# ==============================================================================",
            "# EMAIL CONFIGURATION (CLI App)",
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

            ""
        ]
        
        # Write the content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            
        logger.info(f"Successfully wrote .env file to {file_path} with {len(final_variables)} variables")
        
        # Ensure synchronization between host and container locations
        sync_env_files(file_path, '\n'.join(lines))
        
    except Exception as error:
        logger.error(f"Error writing .env file: {error}")
        raise

@router.get("/environment", response_model=EnvironmentVariableResponse)
async def get_environment_variables(
    current_user: User = Depends(get_current_user)
):
    """Get current environment variables from .env file"""
    try:
        env_path = get_env_file_path()
        variables = parse_env_file(env_path)
        # Sync diagnostics
        host_path = Path("/opt/defrag-app/.env")
        container_path = Path("/app/.env")
        host_exists = host_path.exists()
        container_exists = container_path.exists()
        in_sync = False
        try:
            if host_exists and container_exists:
                in_sync = host_path.read_text() == container_path.read_text()
        except Exception:
            in_sync = False
        
        return {
            "variables": variables,
            "file_exists": env_path.exists(),
            "file_path": str(env_path),
            "host_exists": host_exists,
            "container_exists": container_exists,
            "in_sync": in_sync
        }
        
    except Exception as error:
        logger.error(f"Error reading environment variables: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read environment variables: {str(error)}"
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
        
        # Normalize booleans passed from UI (especially USE_TRAINING_DB)
        variables = dict(update_request.variables)
        if 'USE_TRAINING_DB' in variables:
            val = variables['USE_TRAINING_DB']
            if isinstance(val, bool):
                variables['USE_TRAINING_DB'] = 'true' if val else 'false'
            else:
                variables['USE_TRAINING_DB'] = str(val).strip().lower()
        
        # Create backup if file exists (best-effort; do not fail save on backup error)
        if env_path.exists():
            try:
                backup_path = env_path.parent / f"{env_path.name}.backup"
                backup_path.write_text(env_path.read_text())
                logger.info(f"Created backup of .env file at {backup_path}")
            except Exception as be:
                logger.warning(f"Could not create .env backup at {env_path}: {be}")
        
        # Write the new .env file
        write_env_file(env_path, variables)
        
        # Return the updated configuration
        variables = parse_env_file(env_path)
        
        # Trigger application restart to apply changes
        await restart_application_containers()
        # Attempt a hot-reload immediately so response reflects new values
        try:
            app_config.reload_settings()
        except Exception:
            pass
        
        # Return a minimal response; frontend is resilient to partial responses during restart
        return {
            "message": "Environment variables updated successfully. Application is restarting to apply changes.",
            "variables": variables,
            "file_path": str(env_path),
            "restart_initiated": True
        }
        
    except Exception as error:
        logger.error(f"Error updating environment variables: {error}")
        
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
            detail=f"Failed to update environment variables: {str(error)}"
        )

@router.post("/restart")
async def restart_application(current_user: User = Depends(get_current_user)):
    """Explicitly restart the application containers from the Setup UI"""
    try:
        await restart_application_containers()
        return {"success": True, "message": "Restart initiated"}
    except Exception as error:
        logger.error(f"Failed to initiate restart: {error}")
        raise HTTPException(status_code=500, detail="Failed to initiate restart")

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
        
    except Exception as error:
        logger.error(f"Database connection test failed: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(error)}"
        )

@router.get("/database/tables")
async def get_database_tables(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get database table information"""
    try:
        # Get table names and record counts - using known table list to avoid SQLAlchemy issues
        known_tables = ["defrag_moves", "move_batches", "properties", "user_properties", "users"]
        tables = []
        
        for table_name in known_tables:
            try:
                # Get record count for each table
                count_query = text(f"SELECT COUNT(*) FROM {table_name}")  # nosec B608: table_name is whitelisted above
                count_result = db.execute(count_query)
                record_count = count_result.scalar()
                
                # Get column information using a simpler approach
                try:
                    # Use a simple query to get column names
                    inspect_query = text(f"SELECT * FROM {table_name} LIMIT 0")  # nosec B608: table_name is whitelisted above
                    inspect_result = db.execute(inspect_query)
                    columns = list(inspect_result.keys())
                    logger.info(f"Retrieved {len(columns)} columns for table {table_name}")
                except Exception as col_error:
                    logger.warning(f"Could not get columns for {table_name}: {col_error}")
                    columns = ["id", "..."]  # Fallback
                
                # Skip sample records for now to avoid RMKeyView errors
                sample_records = []
                
                tables.append({
                    "name": table_name,
                    "record_count": record_count,
                    "columns": columns,
                    "sample_records": sample_records
                })
            except Exception as e:
                # Log the actual error that's causing tables to show 0 records
                logger.error(f"❌ ERROR processing table {table_name}: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                # If anything fails, still include the table with minimal info
                tables.append({
                    "name": table_name,
                    "record_count": 0,
                    "columns": [],
                    "sample_records": [],
                    "error": str(e)
                })
        
        response_data = {"tables": tables}
        logger.info(f"Returning database tables response: {len(tables)} tables found")
        for table in tables[:3]:  # Log first 3 tables
            logger.info(f"  Table: {table['name']} - {table['record_count']} records")
        return response_data
        
    except Exception as error:
        logger.error(f"Failed to get database tables: {error}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database tables: {str(error)}"
        )

@router.get("/database/table/{table_name}/records")
async def get_table_records(
    table_name: str,
    offset: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get records from a specific table"""
    try:
        # Validate table name to prevent SQL injection - use strict allowlist
        allowed_tables = {
            "users": "users",
            "properties": "properties", 
            "user_properties": "user_properties",
            "defrag_moves": "defrag_moves",
            "move_batches": "move_batches"
        }
        
        if table_name not in allowed_tables:
            raise HTTPException(status_code=400, detail=f"Table {table_name} not allowed")
        
        safe_table_name = allowed_tables[table_name]
        
        # Get total count
        count_query = text(f"SELECT COUNT(*) FROM {safe_table_name}")  # nosec B608: table_name validated against allowed_tables
        total_result = db.execute(count_query)
        total_count = total_result.scalar()
        
        # Get records with pagination
        # Use parameters for limit/offset values
        records_query = text(f"SELECT * FROM {safe_table_name} ORDER BY id LIMIT :limit OFFSET :offset")  # nosec B608: table_name validated
        records_result = db.execute(records_query, {"limit": limit, "offset": offset})
        
        # Convert to list of dictionaries
        columns = list(records_result.keys())  # Convert RMKeyView to list
        records = []
        for row in records_result:
            record = {}
            for i, value in enumerate(row):
                if value is not None:
                    # Convert datetime objects to strings
                    if hasattr(value, 'isoformat'):
                        record[columns[i]] = value.isoformat()
                    else:
                        record[columns[i]] = str(value)
                else:
                    record[columns[i]] = None
            records.append(record)
        
        return {
            "table_name": table_name,
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "records": records,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as error:
        logger.error(f"Failed to get records from table {table_name}: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get records from table {table_name}: {str(error)}"
        )


@router.delete("/database/table/{table_name}/delete-all")
async def delete_all_records_from_table(
    table_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete all records from a specific table (admin only)"""
    
    # Security check - only admin users can delete all records
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only admin users can delete all records from tables"
        )
    
    # Validate table name to prevent SQL injection - use strict allowlist
    allowed_tables = {
        "defrag_moves": "defrag_moves", 
        "move_batches": "move_batches", 
        "properties": "properties", 
        "user_properties": "user_properties", 
        "users": "users"
    }
    
    if table_name not in allowed_tables:
        raise HTTPException(
            status_code=400,
            detail=f"Table '{table_name}' is not allowed for deletion operations"
        )
    
    # Prevent deletion of critical system tables
    protected_tables = ["users"]  # Don't allow deleting all users
    if table_name in protected_tables:
        raise HTTPException(
            status_code=400,
            detail=f"Table '{table_name}' is protected and cannot have all records deleted"
        )
    
    try:
        logger.info(f"Admin user {current_user.username} is deleting all records from table {table_name}")
        
        # Get count before deletion using safe table name
        safe_table_name = allowed_tables[table_name]  # Use validated table name
        count_query = text(f"SELECT COUNT(*) FROM {safe_table_name}")  # nosec B608: table_name validated against allowed_tables
        count_result = db.execute(count_query)
        record_count = count_result.scalar()
        
        # Delete all records using safe table name
        delete_query = text(f"DELETE FROM {safe_table_name}")  # nosec B608: table_name validated against allowed_tables
        db.execute(delete_query)
        db.commit()
        
        logger.info(f"Successfully deleted {record_count} records from table {table_name}")
        
        return {
            "success": True,
            "table_name": table_name,
            "deleted_count": record_count,
            "message": f"Successfully deleted all {record_count} records from {table_name}"
        }
        
    except Exception as error:
        db.rollback()
        logger.error(f"Failed to delete records from table {table_name}: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete records from table {table_name}: {str(error)}"
        )


@router.post("/test-rms-connection")
async def test_rms_connection(
    test_data: EnvironmentVariableUpdate,
    current_user: User = Depends(get_current_user)
):
    """Test RMS API connection using provided credentials"""
    try:
        logger.info(f"Testing RMS API connection for user {current_user.username}")
        
        # Extract RMS credentials from the test data
        variables = test_data.variables
        agent_id = variables.get('AGENT_ID')
        agent_password = variables.get('AGENT_PASSWORD')
        client_id = variables.get('CLIENT_ID')
        client_password = variables.get('CLIENT_PASSWORD')
        use_training_db = variables.get('USE_TRAINING_DB', 'true').lower() == 'true'
        
        # Validate required credentials
        if not all([agent_id, agent_password, client_id, client_password]):
            raise HTTPException(
                status_code=400,
                detail="Missing required RMS credentials (Agent ID, Agent Password, Client ID, Client Password)"
            )
        
        # Test RMS API connection
        import requests
        from datetime import datetime, timedelta
        
        base_url = "https://restapi12.rmscloud.com"
        
        auth_payload = {
            "AgentId": agent_id,
            "AgentPassword": agent_password,
            "ClientId": client_id,
            "ClientPassword": client_password,
            "UseTrainingDatabase": use_training_db,
            "ModuleType": ["distribution"]
        }
        
        logger.info(f"Testing authentication with RMS API at {base_url}/authToken")
        
        # Test authentication
        response = requests.post(f"{base_url}/authToken", json=auth_payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            
            if token:
                # Test a simple API call to verify the token works
                headers = {
                    'authtoken': token,
                    'Content-Type': 'application/json'
                }
                
                # Try to fetch properties to verify full API access
                try:
                    properties_response = requests.get(
                        f"{base_url}/properties",
                        headers=headers,
                        params={'modelType': 'Full', 'limit': 10},
                        timeout=30
                    )
                    
                    if properties_response.status_code == 200:
                        properties = properties_response.json()
                        properties_count = len(properties) if properties else 0
                        
                        database_type = "Training Database" if use_training_db else "Live Database"
                        
                        return {
                            "success": True,
                            "message": f"RMS API connection successful! Connected to {database_type}.",
                            "details": {
                                "authentication": "✅ Successful",
                                "database_mode": database_type,
                                "properties_accessible": f"✅ {properties_count} properties found",
                                "token_expiry": data.get('expiryDate', 'Not specified'),
                                "api_endpoint": base_url
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "message": "Authentication successful but failed to access RMS data",
                            "details": {
                                "authentication": "✅ Successful",
                                "api_access": f"❌ Failed ({properties_response.status_code})",
                                "error": properties_response.text[:200] if properties_response.text else "Unknown error"
                            }
                        }
                        
                except requests.exceptions.Timeout:
                    return {
                        "success": False,
                        "message": "Authentication successful but RMS API is not responding",
                        "details": {
                            "authentication": "✅ Successful",
                            "api_access": "❌ Timeout",
                            "error": "RMS API did not respond within 30 seconds"
                        }
                    }
                except Exception as api_error:
                    return {
                        "success": False,
                        "message": "Authentication successful but failed to verify API access",
                        "details": {
                            "authentication": "✅ Successful", 
                            "api_access": "❌ Error",
                            "error": str(api_error)[:200]
                        }
                    }
            else:
                return {
                    "success": False,
                    "message": "RMS API authentication failed - no token received",
                    "details": {
                        "authentication": "❌ Failed",
                        "error": "No authentication token in response",
                        "response": str(data)[:200] if data else "Empty response"
                    }
                }
        else:
            error_message = "Unknown error"
            try:
                error_data = response.json()
                error_message = error_data.get('message', str(error_data))
            except:
                error_message = response.text[:200] if response.text else f"HTTP {response.status_code}"
            
            return {
                "success": False,
                "message": f"RMS API authentication failed (HTTP {response.status_code})",
                "details": {
                    "authentication": "❌ Failed",
                    "status_code": response.status_code,
                    "error": error_message,
                    "credentials_check": {
                        "agent_id": f"✅ Provided ({agent_id})" if agent_id else "❌ Missing",
                        "agent_password": "✅ Provided" if agent_password else "❌ Missing",
                        "client_id": f"✅ Provided ({client_id})" if client_id else "❌ Missing",
                        "client_password": "✅ Provided" if client_password else "❌ Missing"
                    }
                }
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "RMS API connection timeout - server not responding",
            "details": {
                "error": "Connection timeout after 30 seconds",
                "possible_causes": [
                    "RMS API server is down",
                    "Network connectivity issues",
                    "Firewall blocking the connection"
                ]
            }
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Cannot connect to RMS API server",
            "details": {
                "error": "Connection failed",
                "api_endpoint": "https://restapi12.rmscloud.com",
                "possible_causes": [
                    "No internet connection",
                    "RMS API server is unreachable",
                    "DNS resolution issues"
                ]
            }
        }
    except Exception as error:
        logger.error(f"Error testing RMS connection: {error}")
        return {
            "success": False,
            "message": f"RMS API test failed: {str(error)}",
            "details": {
                "error": str(error)[:300],
                "type": type(error).__name__
            }
        }
