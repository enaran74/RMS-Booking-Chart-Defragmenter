#!/usr/bin/env python3
"""
RMS Booking Chart Defragmenter - Cron Runner
Executes the original defragmentation analysis on schedule
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path

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

def validate_environment():
    """Validate required environment variables"""
    required_vars = ['AGENT_ID', 'AGENT_PASSWORD', 'CLIENT_ID', 'CLIENT_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def build_command():
    """Build the command to execute the defragmentation analysis"""
    # Base command
    cmd = [
        sys.executable,
        "/app/app/original/start.py",
        "--agent-id", os.getenv('AGENT_ID'),
        "--agent-password", os.getenv('AGENT_PASSWORD'),
        "--client-id", os.getenv('CLIENT_ID'),
        "--client-password", os.getenv('CLIENT_PASSWORD')
    ]
    
    # Add target properties
    target_properties = os.getenv('TARGET_PROPERTIES', 'ALL')
    cmd.extend(["-p", target_properties])
    
    # Add email flag if enabled
    if os.getenv('ENABLE_EMAILS', 'false').lower() == 'true':
        cmd.append("-e")
    
    # Add training database flag if enabled
    if os.getenv('USE_TRAINING_DB', 'false').lower() == 'true':
        cmd.append("-t")
    
    return cmd

def run_analysis():
    """Execute the defragmentation analysis"""
    logger.info("=" * 80)
    logger.info("STARTING SCHEDULED DEFRAGMENTATION ANALYSIS")
    logger.info("=" * 80)
    logger.info(f"Execution time: {datetime.now().isoformat()}")
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed - aborting execution")
        return 1
    
    # Build command
    cmd = build_command()
    logger.info(f"Executing command: {' '.join(cmd)}")
    
    # Set environment for the subprocess
    env = os.environ.copy()
    
    # Additional environment setup
    env['PYTHONPATH'] = '/app/app/original:/app/app/shared'
    env['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
    
    try:
        # Change to the original app directory
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
