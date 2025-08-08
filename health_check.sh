#!/bin/bash
# Health Check Script for BookingChartDefragmenter
# Simple health check to verify the service is working properly

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="bookingchart-defragmenter.service"
INSTALL_DIR="/opt/bookingchart-defragmenter"
LOG_DIR="/var/log/bookingchart-defragmenter"

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

echo -e "${BLUE}🔍 Health Check for BookingChartDefragmenter${NC}"
echo "=================================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script should be run as root (use sudo)"
   exit 1
fi

# 1. Check if service is running
print_info "1. Checking service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    print_status "Service is running"
else
    print_error "Service is not running"
    exit 1
fi

# 2. Check if service is enabled
print_info "2. Checking if service is enabled..."
if systemctl is-enabled --quiet $SERVICE_NAME; then
    print_status "Service is enabled"
else
    print_warning "Service is not enabled"
fi

# 3. Check installation directory
print_info "3. Checking installation directory..."
if [ -d "$INSTALL_DIR" ]; then
    print_status "Installation directory exists"
else
    print_error "Installation directory not found"
    exit 1
fi

# 4. Check Python virtual environment
print_info "4. Checking Python virtual environment..."
if [ -d "$INSTALL_DIR/venv" ]; then
    print_status "Virtual environment exists"
else
    print_error "Virtual environment not found"
    exit 1
fi

# 5. Check if main scripts exist
print_info "5. Checking main scripts..."
if [ -f "$INSTALL_DIR/start.py" ]; then
    print_status "start.py exists"
else
    print_error "start.py not found"
    exit 1
fi

if [ -f "$INSTALL_DIR/service_wrapper.sh" ]; then
    print_status "service_wrapper.sh exists"
else
    print_error "service_wrapper.sh not found"
    exit 1
fi

if [ -f "$INSTALL_DIR/run_defragmentation.sh" ]; then
    print_status "run_defragmentation.sh exists"
else
    print_error "run_defragmentation.sh not found"
    exit 1
fi

# 6. Check configuration
print_info "6. Checking configuration..."
if [ -f "/etc/bookingchart-defragmenter/config.env" ]; then
    print_status "Configuration file exists"
else
    print_warning "Configuration file not found"
fi

# 7. Check log directory
print_info "7. Checking log directory..."
if [ -d "$LOG_DIR" ]; then
    print_status "Log directory exists"
else
    print_warning "Log directory not found"
fi

# 8. Check recent service logs
print_info "8. Checking recent service logs..."
RECENT_LOGS=$(journalctl -u $SERVICE_NAME --no-pager -n 5 2>/dev/null | wc -l)
if [ "$RECENT_LOGS" -gt 0 ]; then
    print_status "Service logs are available"
else
    print_warning "No recent service logs found"
fi

# 9. Test Python import (basic check)
print_info "9. Testing Python imports..."
if sudo -u defrag "$INSTALL_DIR/venv/bin/python" -c "import pandas, numpy, requests, openpyxl; print('Dependencies OK')" 2>/dev/null; then
    print_status "Python dependencies verified"
else
    print_error "Python dependencies failed"
    exit 1
fi

echo ""
print_status "Health check completed successfully!"
echo ""
print_info "Service is healthy and ready for operation"
print_info "Analysis can be run manually with: sudo /opt/bookingchart-defragmenter/manage.sh run"
print_info "View logs with: sudo journalctl -u $SERVICE_NAME -f"
