#!/bin/bash
# ==============================================================================
# RMS Booking Chart Defragmenter - Health Check Script
# ==============================================================================
# Comprehensive health check for the unified system

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Health check variables
HEALTH_STATUS=0
WEB_PORT=${WEB_APP_PORT:-8000}

# Check web application health
check_web_app() {
    log_info "Checking web application health..."
    
    if curl -sf "http://localhost:${WEB_PORT}/health" >/dev/null 2>&1; then
        log_success "Web application is responding"
    else
        log_error "Web application is not responding"
        HEALTH_STATUS=1
    fi
}

# Check database connectivity
check_database() {
    log_info "Checking database connectivity..."
    
    if [ -n "${DB_HOST}" ]; then
        DB_HOST=${DB_HOST:-postgres}
        DB_PORT=${DB_PORT:-5432}
        DB_USER=${DB_USER:-defrag_user}
        DB_NAME=${DB_NAME:-defrag_db}
        
        if pg_isready -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} >/dev/null 2>&1; then
            log_success "Database is accessible"
        else
            log_error "Database is not accessible"
            HEALTH_STATUS=1
        fi
    else
        log_warning "Database configuration not found"
    fi
}

# Check required directories
check_directories() {
    log_info "Checking required directories..."
    
    directories=("/app/logs" "/app/output" "/app/backups")
    
    for dir in "${directories[@]}"; do
        if [ -d "$dir" ] && [ -w "$dir" ]; then
            log_success "Directory $dir is accessible"
        else
            log_error "Directory $dir is not accessible or writable"
            HEALTH_STATUS=1
        fi
    done
}

# Check Python environment
check_python_environment() {
    log_info "Checking Python environment..."
    
    required_packages=("pandas" "numpy" "fastapi" "sqlalchemy" "openpyxl" "requests")
    
    for package in "${required_packages[@]}"; do
        if python3 -c "import $package" >/dev/null 2>&1; then
            log_success "Python package $package is available"
        else
            log_error "Python package $package is missing"
            HEALTH_STATUS=1
        fi
    done
}

# Check log files
check_logs() {
    log_info "Checking log files..."
    
    log_files=("/app/logs/web_app.log" "/app/logs/cron_runner.log")
    
    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            # Check if log file was modified in the last 24 hours
            if [ $(find "$log_file" -mtime -1 | wc -l) -gt 0 ]; then
                log_success "Log file $log_file is recent"
            else
                log_warning "Log file $log_file is older than 24 hours"
            fi
        else
            log_warning "Log file $log_file does not exist yet"
        fi
    done
}

# Check disk space
check_disk_space() {
    log_info "Checking disk space..."
    
    # Check available space in key directories
    for dir in "/app/logs" "/app/output" "/app/backups"; do
        if [ -d "$dir" ]; then
            usage=$(df "$dir" | tail -1 | awk '{print $5}' | sed 's/%//')
            if [ "$usage" -lt 90 ]; then
                log_success "Disk usage for $dir: ${usage}%"
            else
                log_warning "High disk usage for $dir: ${usage}%"
            fi
        fi
    done
}

# Check cron status
check_cron() {
    log_info "Checking cron status..."
    
    if [ "${ENABLE_CRON:-true}" = "true" ]; then
        if pgrep cron >/dev/null 2>&1; then
            log_success "Cron daemon is running"
            
            # Check if cron job exists
            if crontab -l 2>/dev/null | grep -q "cron_runner.py"; then
                log_success "Defragmentation cron job is configured"
            else
                log_warning "Defragmentation cron job not found"
            fi
        else
            log_error "Cron daemon is not running"
            HEALTH_STATUS=1
        fi
    else
        log_info "Cron scheduling is disabled"
    fi
}

# Check environment variables
check_environment() {
    log_info "Checking environment configuration..."
    
    required_vars=("AGENT_ID" "AGENT_PASSWORD" "CLIENT_ID" "CLIENT_PASSWORD")
    
    for var in "${required_vars[@]}"; do
        if [ -n "${!var}" ]; then
            log_success "Environment variable $var is set"
        else
            log_error "Environment variable $var is missing"
            HEALTH_STATUS=1
        fi
    done
}

# Main health check execution
main() {
    log_info "Starting comprehensive health check..."
    echo ""
    
    check_web_app
    check_database
    check_directories
    check_python_environment
    check_logs
    check_disk_space
    check_cron
    check_environment
    
    echo ""
    if [ $HEALTH_STATUS -eq 0 ]; then
        log_success "🎉 All health checks passed!"
        echo ""
        log_info "System Information:"
        log_info "Web Interface: http://localhost:${WEB_PORT}"
        log_info "Health Endpoint: http://localhost:${WEB_PORT}/health"
        log_info "API Documentation: http://localhost:${WEB_PORT}/docs"
        
        if [ "${ENABLE_CRON:-true}" = "true" ]; then
            log_info "Cron Schedule: ${CRON_SCHEDULE:-0 2 * * *}"
        fi
        
        exit 0
    else
        log_error "❌ Health check failed!"
        log_error "Please review the errors above and fix any issues"
        exit 1
    fi
}

# Execute health check
main "$@"
