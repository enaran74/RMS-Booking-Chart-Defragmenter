#!/bin/bash
# Run Defragmentation Analysis Script
# This script executes the actual defragmentation analysis process

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Try Docker .env file first, fallback to traditional location
if [ -f "/opt/defrag-app/.env" ]; then
    CONFIG_FILE="/opt/defrag-app/.env"
elif [ -f "/etc/bookingchart-defragmenter/config.env" ]; then
    CONFIG_FILE="/etc/bookingchart-defragmenter/config.env"
else
    CONFIG_FILE="/opt/defrag-app/.env"  # Default for Docker setup
fi
# Use user-accessible log location for Docker setup
if [ "$CONFIG_FILE" = "/opt/defrag-app/.env" ]; then
    LOG_FILE="/opt/defrag-app/logs/manual_analysis.log"
else
    LOG_FILE="/var/log/bookingchart-defragmenter/analysis.log"
fi
OUTPUT_DIR="$SCRIPT_DIR/output"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

echo -e "${BLUE}🚀 Starting Defragmentation Analysis${NC}"
echo "=========================================="
echo ""

# Validate directory permissions and access
print_info "Validating directory permissions..."

# Create log directory if it doesn't exist and test write access
if ! mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null; then
    print_error "Cannot create log directory: $(dirname "$LOG_FILE")"
    print_error "Please ensure the current user has write access to this location"
    exit 1
fi

# Test write access to log file
if ! touch "$LOG_FILE" 2>/dev/null; then
    print_error "Cannot write to log file: $LOG_FILE"
    print_error "Please ensure the current user has write access to this file"
    exit 1
fi

# Create output directory if it doesn't exist and test write access
if ! mkdir -p "$OUTPUT_DIR" 2>/dev/null; then
    print_error "Cannot create output directory: $OUTPUT_DIR"
    print_error "Please ensure the current user has write access to this location"
    exit 1
fi

# Test write access to output directory
if ! touch "$OUTPUT_DIR/.test_write" 2>/dev/null; then
    print_error "Cannot write to output directory: $OUTPUT_DIR"
    print_error "Please ensure the current user has write access to this directory"
    exit 1
else
    rm -f "$OUTPUT_DIR/.test_write" 2>/dev/null
fi

print_status "Directory permissions validated successfully"

# Log start of analysis
log_message "Starting defragmentation analysis"

# 1. Check if configuration exists
print_info "1. Checking configuration..."
if [ -f "$CONFIG_FILE" ]; then
    print_status "Configuration file found"
    # Load configuration variables safely, ignoring comments and empty lines
    while IFS= read -r line; do
        # Skip comments and empty lines
        [[ $line =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        
        # Export variables that look like assignments
        if [[ $line =~ ^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*= ]]; then
            export "$line"
        fi
    done < "$CONFIG_FILE"
else
    print_error "Configuration file not found at $CONFIG_FILE"
    log_message "ERROR: Configuration file not found"
    exit 1
fi

# 2. Verify required environment variables
print_info "2. Verifying environment variables..."
REQUIRED_VARS=("AGENT_ID" "AGENT_PASSWORD" "CLIENT_ID" "CLIENT_PASSWORD")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    print_error "Missing required environment variables: ${MISSING_VARS[*]}"
    log_message "ERROR: Missing environment variables: ${MISSING_VARS[*]}"
    exit 1
fi

print_status "All required environment variables are set"

# 3. Activate virtual environment and run analysis
print_info "3. Starting analysis..."
log_message "Starting analysis with Python"

# Change to script directory
cd "$SCRIPT_DIR"

# Run the analysis with proper environment
print_info "Executing defragmentation analysis..."
print_info "This may take a while depending on the number of parks..."

# Build command arguments to match cron_runner.py exactly
CMD_ARGS=""

# Add target properties if configured (not ALL)
if [ -n "$TARGET_PROPERTIES" ] && [ "$TARGET_PROPERTIES" != "ALL" ]; then
    CMD_ARGS="$CMD_ARGS -p $TARGET_PROPERTIES"
fi

# Add email flag if enabled
if [ "$ENABLE_EMAILS" = "true" ]; then
    CMD_ARGS="$CMD_ARGS -e"
fi

# Add training database flag if enabled
if [ "$USE_TRAINING_DB" = "true" ]; then
    CMD_ARGS="$CMD_ARGS -t"
fi

# Prepare environment variables (matching cron_runner.py exactly)
ENV_VARS="AGENT_ID=$AGENT_ID AGENT_PASSWORD=$AGENT_PASSWORD CLIENT_ID=$CLIENT_ID CLIENT_PASSWORD=$CLIENT_PASSWORD"
ENV_VARS="$ENV_VARS PYTHONPATH=/app:/app/app/original LOG_LEVEL=${LOG_LEVEL:-INFO}"

# Add email configuration if emails are enabled (with same defaults as cron_runner.py)
if [ "$ENABLE_EMAILS" = "true" ]; then
    ENV_VARS="$ENV_VARS SMTP_SERVER=${SMTP_SERVER:-smtp.gmail.com} SMTP_PORT=${SMTP_PORT:-587}"
    ENV_VARS="$ENV_VARS SENDER_EMAIL=$SENDER_EMAIL APP_PASSWORD=$APP_PASSWORD"
    ENV_VARS="$ENV_VARS SENDER_DISPLAY_NAME=${SENDER_DISPLAY_NAME:-DHP Systems}"
    ENV_VARS="$ENV_VARS TEST_RECIPIENT=$TEST_RECIPIENT CONSOLIDATED_EMAIL_RECIPIENT=$CONSOLIDATED_EMAIL_RECIPIENT"
    ENV_VARS="$ENV_VARS SEND_CONSOLIDATED_EMAIL=${SEND_CONSOLIDATED_EMAIL:-false}"
fi

# Determine execution method (Docker vs traditional)
if [ "$CONFIG_FILE" = "/opt/defrag-app/.env" ]; then
    # Docker setup - execute inside container
    DOCKER_CONTAINER="defrag-app"
    SCRIPT_PATH="/app/app/original/start.py"
    WORK_DIR="/app/app/original"
    
    print_info "Target properties: ${TARGET_PROPERTIES:-ALL}"
    print_info "Email notifications: ${ENABLE_EMAILS:-false}"
    print_info "Training database: ${USE_TRAINING_DB:-false}"
    print_info "Execution method: Docker container ($DOCKER_CONTAINER)"
    print_info "Command: python3 $SCRIPT_PATH $CMD_ARGS"
    
    # Build Docker exec command with properly quoted environment variables
    DOCKER_CMD="docker exec"
    DOCKER_CMD="$DOCKER_CMD -e \"AGENT_ID=$AGENT_ID\""
    DOCKER_CMD="$DOCKER_CMD -e \"AGENT_PASSWORD=$AGENT_PASSWORD\""
    DOCKER_CMD="$DOCKER_CMD -e \"CLIENT_ID=$CLIENT_ID\""
    DOCKER_CMD="$DOCKER_CMD -e \"CLIENT_PASSWORD=$CLIENT_PASSWORD\""
    DOCKER_CMD="$DOCKER_CMD -e \"PYTHONPATH=/app:/app/app/original\""
    DOCKER_CMD="$DOCKER_CMD -e \"LOG_LEVEL=${LOG_LEVEL:-INFO}\""
    
    # Add email environment variables if enabled
    if [ "$ENABLE_EMAILS" = "true" ]; then
        DOCKER_CMD="$DOCKER_CMD -e \"SMTP_SERVER=${SMTP_SERVER:-smtp.gmail.com}\""
        DOCKER_CMD="$DOCKER_CMD -e \"SMTP_PORT=${SMTP_PORT:-587}\""
        DOCKER_CMD="$DOCKER_CMD -e \"SENDER_EMAIL=$SENDER_EMAIL\""
        DOCKER_CMD="$DOCKER_CMD -e \"APP_PASSWORD=$APP_PASSWORD\""
        DOCKER_CMD="$DOCKER_CMD -e \"SENDER_DISPLAY_NAME=${SENDER_DISPLAY_NAME:-DHP Systems}\""
        DOCKER_CMD="$DOCKER_CMD -e \"TEST_RECIPIENT=$TEST_RECIPIENT\""
        DOCKER_CMD="$DOCKER_CMD -e \"CONSOLIDATED_EMAIL_RECIPIENT=$CONSOLIDATED_EMAIL_RECIPIENT\""
        DOCKER_CMD="$DOCKER_CMD -e \"SEND_CONSOLIDATED_EMAIL=${SEND_CONSOLIDATED_EMAIL:-false}\""
    fi
    
    DOCKER_CMD="$DOCKER_CMD $DOCKER_CONTAINER bash -c \"cd $WORK_DIR && python3 $SCRIPT_PATH $CMD_ARGS\""
    
    print_info "Full Docker command: $DOCKER_CMD"
    
    # Execute inside Docker container
    if eval "$DOCKER_CMD" 2>&1 | tee -a "$LOG_FILE"; then
        analysis_success=true
    else
        analysis_success=false
    fi
else
    # Traditional setup
    if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
        PYTHON_EXEC="$SCRIPT_DIR/venv/bin/python"
    else
        PYTHON_EXEC="python3"
    fi
    SCRIPT_PATH="$SCRIPT_DIR/start.py"
    WORK_DIR="$SCRIPT_DIR"
    
    print_info "Target properties: ${TARGET_PROPERTIES:-ALL}"
    print_info "Email notifications: ${ENABLE_EMAILS:-false}"
    print_info "Training database: ${USE_TRAINING_DB:-false}"
    print_info "Working directory: $WORK_DIR"
    print_info "Command: $PYTHON_EXEC $SCRIPT_PATH $CMD_ARGS"
    
    # Change to working directory and run the analysis
    cd "$WORK_DIR"
    if env $ENV_VARS "$PYTHON_EXEC" "$SCRIPT_PATH" $CMD_ARGS 2>&1 | tee -a "$LOG_FILE"; then
        analysis_success=true
    else
        analysis_success=false
    fi
fi

# Check result
if [ "$analysis_success" = "true" ]; then
    print_status "Analysis completed successfully!"
    log_message "Analysis completed successfully"
    
    # Check if output files were created
    if [ -d "$OUTPUT_DIR" ] && [ "$(ls -A "$OUTPUT_DIR" 2>/dev/null)" ]; then
        print_status "Output files generated in $OUTPUT_DIR"
        log_message "Output files generated successfully"
        
        # List output files
        echo ""
        print_info "Generated output files:"
        ls -la "$OUTPUT_DIR"
    else
        print_warning "No output files found in $OUTPUT_DIR"
        log_message "WARNING: No output files generated"
    fi
else
    print_error "Analysis failed!"
    log_message "ERROR: Analysis failed"
    exit 1
fi

echo ""
print_status "Defragmentation analysis completed!"
print_info "Check logs at: $LOG_FILE"
print_info "Output files at: $OUTPUT_DIR"
