#!/bin/bash
# Debug Service Script
# Run this on your Raspberry Pi to diagnose service issues

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="bookingchart-defragmenter.service"
INSTALL_DIR="/opt/bookingchart-defragmenter"
SERVICE_USER="defrag"

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

echo -e "${BLUE}🔍 Service Debug Information${NC}"
echo "=================================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script should be run as root (use sudo)"
   exit 1
fi

# 1. Check service file
print_info "1. Checking service file..."
if [ -f "/etc/systemd/system/$SERVICE_NAME" ]; then
    print_status "Service file exists"
    echo "Service file contents:"
    cat "/etc/systemd/system/$SERVICE_NAME"
    echo ""
else
    print_error "Service file not found!"
fi

# 2. Check service status
print_info "2. Checking service status..."
systemctl status $SERVICE_NAME --no-pager -l
echo ""

# 3. Check if service is enabled
print_info "3. Checking if service is enabled..."
if systemctl is-enabled $SERVICE_NAME >/dev/null 2>&1; then
    print_status "Service is enabled"
else
    print_warning "Service is not enabled"
fi

# 4. Check installation directory
print_info "4. Checking installation directory..."
if [ -d "$INSTALL_DIR" ]; then
    print_status "Installation directory exists"
    echo "Directory contents:"
    ls -la "$INSTALL_DIR"
    echo ""
else
    print_error "Installation directory not found!"
fi

# 5. Check wrapper script
print_info "5. Checking wrapper script..."
if [ -f "$INSTALL_DIR/run_defragmentation.sh" ]; then
    print_status "Wrapper script exists"
    echo "Wrapper script permissions:"
    ls -la "$INSTALL_DIR/run_defragmentation.sh"
    echo ""
else
    print_error "Wrapper script not found!"
fi

# 6. Check configuration
print_info "6. Checking configuration..."
if [ -f "/etc/bookingchart-defragmenter/config.env" ]; then
    print_status "Configuration file exists"
    echo "Configuration file permissions:"
    ls -la "/etc/bookingchart-defragmenter/config.env"
    echo ""
else
    print_warning "Configuration file not found"
fi

# 7. Check service user
print_info "7. Checking service user..."
if id "$SERVICE_USER" &>/dev/null; then
    print_status "Service user exists"
    echo "User details:"
    id "$SERVICE_USER"
    echo ""
else
    print_error "Service user not found!"
fi

# 8. Check recent logs
print_info "8. Checking recent service logs..."
echo "Recent service logs:"
journalctl -u $SERVICE_NAME --no-pager -n 20
echo ""

# 9. Check if we can run the wrapper script manually
print_info "9. Testing wrapper script execution..."
if [ -f "$INSTALL_DIR/run_defragmentation.sh" ]; then
    print_info "Attempting to run wrapper script (this may take a moment)..."
    timeout 30s sudo -u "$SERVICE_USER" "$INSTALL_DIR/run_defragmentation.sh" || {
        print_warning "Wrapper script execution failed or timed out"
        print_info "This is normal if credentials are not configured"
    }
else
    print_error "Cannot test wrapper script - file not found"
fi

# 10. Check Python environment
print_info "10. Checking Python environment..."
if [ -d "$INSTALL_DIR/venv" ]; then
    print_status "Virtual environment exists"
    echo "Python version:"
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" --version
    echo ""
else
    print_error "Virtual environment not found!"
fi

echo -e "${BLUE}🔍 Debug Information Complete${NC}"
echo ""
print_info "If the service is failing to start, check:"
echo "1. Configuration file: /etc/bookingchart-defragmenter/config.env"
echo "2. Service logs: journalctl -u $SERVICE_NAME -f"
echo "3. Application logs: tail -f $INSTALL_DIR/defrag_analyzer.log"
echo ""
print_info "To manually start the service:"
echo "sudo systemctl start $SERVICE_NAME"
echo ""
print_info "To view live logs:"
echo "sudo journalctl -u $SERVICE_NAME -f"
