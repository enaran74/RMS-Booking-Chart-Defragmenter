#!/usr/bin/env python3
"""
RMS Booking Chart Defragmenter - Cron Runner
Executes the defragmentation analysis using Docker container environment
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.append('/app')
sys.path.append('/app/app/web')

# Setup logging
log_file = "/app/logs/cron_runner.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from Docker container .env file"""
    try:
        # Import the web app configuration system
        from app.core.config import settings, reload_settings
        
        # Force reload of settings from .env files
        reload_settings()
        
        logger.info("Configuration loaded from .env file successfully")
        logger.info(f"Agent ID: {settings.AGENT_ID[:4]}... (masked)")
        logger.info(f"Database: {settings.DB_NAME}")
        
        return settings
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return None

def validate_rms_credentials(settings):
    """Validate RMS credentials from configuration"""
    required_attrs = ['AGENT_ID', 'AGENT_PASSWORD', 'CLIENT_ID', 'CLIENT_PASSWORD']
    missing = []
    
    for attr in required_attrs:
        value = getattr(settings, attr, None)
        if not value or value == "SETUP_REQUIRED_VIA_ENVIRONMENT_VARIABLE":
            missing.append(attr)
    
    if missing:
        logger.error(f"Missing or placeholder RMS credentials: {', '.join(missing)}")
        logger.error("Please configure RMS credentials via the web interface Settings menu")
        return False
    
    return True

def build_command(settings):
    """Build the command to execute the defragmentation analysis using Docker container approach"""
    # Use the original CLI through start.py with proper environment
    cmd = [
        sys.executable,
        "/app/app/original/start.py"
    ]
    
    # Add target properties from configuration
    target_properties = getattr(settings, 'TARGET_PROPERTIES', 'ALL')
    if target_properties and target_properties.upper() != 'ALL':
        cmd.extend(["-p", target_properties])
    
    # Add email flag if enabled
    if getattr(settings, 'ENABLE_EMAILS', False):
        cmd.append("-e")
    
    # Add training database flag if enabled  
    if getattr(settings, 'USE_TRAINING_DB', False):
        cmd.append("-t")
    
    logger.info(f"Target properties: {target_properties}")
    logger.info(f"Email notifications: {getattr(settings, 'ENABLE_EMAILS', False)}")
    logger.info(f"Training database: {getattr(settings, 'USE_TRAINING_DB', False)}")
    
    return cmd

def run_analysis():
    """Execute the defragmentation analysis using Docker container configuration"""
    logger.info("=" * 80)
    logger.info("STARTING SCHEDULED DEFRAGMENTATION ANALYSIS")
    logger.info("=" * 80)
    logger.info(f"Execution time: {datetime.now().isoformat()}")
    
    # Load configuration from .env file
    settings = load_config()
    if not settings:
        logger.error("Configuration loading failed - aborting execution")
        return 1
    
    # Validate RMS credentials
    if not validate_rms_credentials(settings):
        logger.error("RMS credentials validation failed - aborting execution")
        return 1
    
    # Build command with configuration
    cmd = build_command(settings)
    logger.info(f"Executing command: {' '.join(cmd)}")
    
    # Set environment for the subprocess - pass RMS credentials
    env = os.environ.copy()
    env.update({
        'AGENT_ID': settings.AGENT_ID,
        'AGENT_PASSWORD': settings.AGENT_PASSWORD,
        'CLIENT_ID': settings.CLIENT_ID,
        'CLIENT_PASSWORD': settings.CLIENT_PASSWORD,
        'PYTHONPATH': '/app:/app/app/original',
        'LOG_LEVEL': getattr(settings, 'LOG_LEVEL', 'INFO')
    })
    
    try:
        # Change to the original CLI directory
        os.chdir('/app/app/original')
        
        # Execute the analysis
        start_time = datetime.now()
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Log results
        logger.info(f"Analysis completed in {duration}")
        logger.info(f"Exit code: {result.returncode}")
        
        if result.stdout:
            logger.info("STDOUT:")
            logger.info(result.stdout)
        
        if result.stderr:
            if result.returncode != 0:
                logger.error("STDERR:")
                logger.error(result.stderr)
            else:
                logger.warning("STDERR (non-fatal):")
                logger.warning(result.stderr)
        
        if result.returncode == 0:
            logger.info("✅ Defragmentation analysis completed successfully")
        else:
            logger.error(f"❌ Defragmentation analysis failed with exit code {result.returncode}")
        
        # Check for known formatting errors in output
        if "Unknown format code 'f' for object of type 'str'" in result.stderr:
            logger.warning("⚠️  Known issue: String formatting error in original CLI code")
            logger.warning("⚠️  Analysis may have partially completed despite the error")
            logger.warning("⚠️  Check output directory for generated files")
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Analysis timed out after 2 hours")
        return 124
    except FileNotFoundError as e:
        logger.error(f"❌ Command not found: {e}")
        return 127
    except Exception as e:
        logger.error(f"❌ Unexpected error during analysis: {e}")
        return 1
    finally:
        logger.info("=" * 80)
        logger.info("SCHEDULED ANALYSIS COMPLETED")
        logger.info("=" * 80)

def main():
    """Main entry point"""
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(os.getenv('OUTPUT_DIR', '/app/output'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run the analysis
        exit_code = run_analysis()
        
        # Exit with the same code as the analysis
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Fatal error in cron runner: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
