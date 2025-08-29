#!/bin/bash
# ==============================================================================
# RMS Booking Chart Defragmenter - Unified Entrypoint
# ==============================================================================
# This script manages both the web application and cron-scheduled analysis

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Handle help requests
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "RMS Booking Chart Defragmenter - Unified System"
    echo ""
    echo "DESCRIPTION:"
    echo "    Complete defragmentation solution with web interface and automated analysis"
    echo ""
    echo "USAGE:"
    echo "    docker run [options] <image>"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "    Required RMS API Credentials:"
    echo "        AGENT_ID          - RMS Agent ID"
    echo "        AGENT_PASSWORD    - RMS Agent Password"
    echo "        CLIENT_ID         - RMS Client ID"
    echo "        CLIENT_PASSWORD   - RMS Client Password"
    echo ""
    echo "    Optional Configuration:"
    echo "        WEB_APP_PORT      - Web interface port (default: 8000)"
    echo "        WEB_APP_HOST      - Web interface host (default: 0.0.0.0)"
    echo "        DB_HOST          - Database host (default: postgres)"
    echo "        DB_PORT          - Database port (default: 5432)"
    echo "        ENABLE_CRON      - Enable scheduled analysis (default: true)"
    echo "        CRON_SCHEDULE    - Cron schedule (default: '0 2 * * *')"
    echo "        LOG_LEVEL        - Logging level (default: INFO)"
    echo "        TZ               - Timezone (default: system)"
    echo ""
    echo "SERVICES:"
    echo "    - Web Interface: http://localhost:8000"
    echo "    - API Documentation: http://localhost:8000/docs"
    echo "    - Health Check: http://localhost:8000/health"
    echo "    - Automated Analysis: Via cron schedule"
    echo ""
    echo "VOLUMES:"
    echo "    /app/logs     - Application logs"
    echo "    /app/output   - Analysis output files"
    echo "    /app/backups  - Database backups"
    echo ""
    echo "For more information, visit:"
    echo "    https://github.com/enaran74/RMS-Booking-Chart-Defragmenter"
    exit 0
fi

# Environment setup
log_info "🚀 Starting RMS Booking Chart Defragmenter Unified System"
log_info "Container started at $(date)"

# Set timezone via environment variable
if [ -n "${TZ}" ]; then
    log_info "Setting timezone to ${TZ}"
    export TZ="${TZ}"
    # Note: /etc/timezone and /etc/localtime are managed by the container environment
fi

# Create required directories
log_info "Creating required directories..."
mkdir -p /app/logs /app/output /app/backups /app/config

# Environment validation
log_info "Validating environment configuration..."

# Check if this is CLI mode (has arguments and is not web mode)
CLI_MODE=false
log_info "Arguments received: $# args: $*"
log_info "Environment: CI=$CI GITHUB_ACTIONS=$GITHUB_ACTIONS"

if [ "$#" -gt 0 ] && [ "$1" != "web" ] && [ "$1" != "--help" ] && [ "$1" != "-h" ] && [ "$1" != "test" ]; then
    CLI_MODE=true
    log_info "Initial CLI_MODE detection: true (based on arguments)"
else
    log_info "Initial CLI_MODE detection: false (web mode default)"
fi

# Special handling for CI test environment
if [ "$CI" = "true" ] || [ "$GITHUB_ACTIONS" = "true" ]; then
    log_info "CI environment detected - forcing web mode"
    CLI_MODE=false
fi

log_info "Final CLI_MODE decision: $CLI_MODE"

# Check required RMS credentials (only for CLI mode, web app gets them from user setup)
if [ "$CLI_MODE" = "true" ]; then
    # CLI mode requires credentials
    if [ -z "${AGENT_ID}" ] || [ -z "${AGENT_PASSWORD}" ] || [ -z "${CLIENT_ID}" ] || [ -z "${CLIENT_PASSWORD}" ]; then
        log_error "Missing required RMS API credentials for CLI mode"
        log_error "Required: AGENT_ID, AGENT_PASSWORD, CLIENT_ID, CLIENT_PASSWORD"
        exit 1
    fi
    log_info "CLI mode: RMS API credentials validated"
else
    # Web mode - credentials are optional (provided through setup wizard)
    if [ -z "${AGENT_ID}" ] || [ -z "${AGENT_PASSWORD}" ] || [ -z "${CLIENT_ID}" ] || [ -z "${CLIENT_PASSWORD}" ]; then
        log_warning "RMS API credentials not set - will be configured through web interface"
    else
        log_info "Web mode: RMS API credentials available"
    fi
fi

# Database connectivity check
log_info "Checking database connectivity..."
if [ -n "${DB_HOST}" ]; then
    DB_HOST=${DB_HOST:-postgres}
    DB_PORT=${DB_PORT:-5432}
    DB_USER=${DB_USER:-defrag_user}
    DB_NAME=${DB_NAME:-defrag_db}
    
    # Wait for database to be ready
    for i in {1..30}; do
        if pg_isready -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} >/dev/null 2>&1; then
            log_success "Database connection established"
            break
        fi
        log_info "Waiting for database... (attempt $i/30)"
        sleep 2
    done
    
    if ! pg_isready -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} >/dev/null 2>&1; then
        log_error "Failed to connect to database after 60 seconds"
        exit 1
    fi
else
    log_warning "No database configuration found - web app may not function properly"
fi

# Setup cron if enabled
if [ "${ENABLE_CRON:-true}" = "true" ]; then
    log_info "Setting up cron scheduling..."
    CRON_SCHEDULE=${CRON_SCHEDULE:-"0 2 * * *"}
    
    # Create cron job for defragmentation analysis
    echo "${CRON_SCHEDULE} cd /app && python3 scripts/cron_runner.py >> /app/logs/cron.log 2>&1" > /tmp/crontab
    crontab /tmp/crontab
    rm /tmp/crontab
    
    log_success "Cron job configured: ${CRON_SCHEDULE}"
    
    # Start cron daemon
    service cron start
    log_success "Cron daemon started"
else
    log_info "Cron scheduling disabled"
fi

# Setup logging
LOG_LEVEL=${LOG_LEVEL:-INFO}
log_info "Setting log level to ${LOG_LEVEL}"

# Create unified startup script
cat > /tmp/start_services.sh << 'EOF'
#!/bin/bash

# Function for logging
log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1" >&2
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1" >&2
}

# Start the web application
start_web_app() {
    log_info "Starting FastAPI web application..."
    cd /app/app/web
    
    # Wait a bit for database migrations if needed
    sleep 5
    
    # Start the web server as appuser for security
    exec su -s /bin/bash -c "uvicorn main:app \
        --host ${WEB_APP_HOST:-0.0.0.0} \
        --port ${WEB_APP_PORT:-8000} \
        --log-level ${LOG_LEVEL:-info} \
        2>&1 | tee -a /app/logs/web_app.log" appuser
}

# Trap signals for graceful shutdown
cleanup() {
    log_info "Received shutdown signal, cleaning up..."
    pkill -f uvicorn || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start web application
start_web_app &
WEB_PID=$!

# Wait for web app process
wait $WEB_PID
EOF

chmod +x /tmp/start_services.sh

# Final system check
log_info "Performing final system checks..."

# Check Python environment
python3 -c "import pandas, numpy, fastapi, sqlalchemy" 2>/dev/null || {
    log_error "Failed to import required Python packages"
    exit 1
}

# Check file permissions
if [ ! -w "/app/logs" ] || [ ! -w "/app/output" ]; then
    log_error "Insufficient permissions for output directories"
    exit 1
fi

# System ready
log_success "🎉 System initialization complete!"
log_info "Web Interface: http://localhost:${WEB_APP_PORT:-8000}"
log_info "Health Check: http://localhost:${WEB_APP_PORT:-8000}/health"
log_info "API Documentation: http://localhost:${WEB_APP_PORT:-8000}/docs"

if [ "${ENABLE_CRON:-true}" = "true" ]; then
    log_info "Cron Schedule: ${CRON_SCHEDULE:-0 2 * * *}"
fi

log_info "Log files: /app/logs/"
log_info "Output files: /app/output/"
log_info "Configuration: /app/config/"

# Determine execution mode
if [ "$CLI_MODE" = "true" ]; then
    # CLI mode - run defragmentation analysis
    log_info "🚀 Starting CLI defragmentation analysis..."
    
    # Ensure output directory permissions
    mkdir -p /app/output
    chown appuser:appuser /app/output
    chmod 755 /app/output
    
    # Switch to app user and run CLI analysis
    log_info "Executing: python start.py $*"
    exec gosu appuser python start.py "$@"
else
    # Web mode - start services
    log_info "🌐 Starting web application services..."
    exec /tmp/start_services.sh
fi
