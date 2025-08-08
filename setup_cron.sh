#!/bin/bash
# Setup Cron Job for BookingChartDefragmenter

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_USER="defrag"
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

echo -e "${BLUE}⏰ Setting up Cron Job for BookingChartDefragmenter${NC}"
echo "=================================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if service user exists
if ! getent passwd $SERVICE_USER > /dev/null 2>&1; then
    print_error "Service user '$SERVICE_USER' does not exist"
    exit 1
fi

# Check if installation directory exists
if [ ! -d "$INSTALL_DIR" ]; then
    print_error "Installation directory '$INSTALL_DIR' does not exist"
    exit 1
fi

# Check if run_defragmentation.sh exists
if [ ! -f "$INSTALL_DIR/run_defragmentation.sh" ]; then
    print_error "run_defragmentation.sh not found in '$INSTALL_DIR'"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"
chown -R $SERVICE_USER:$SERVICE_USER "$LOG_DIR"

# Remove any existing cron jobs for this script
print_info "Removing any existing cron jobs..."
crontab -u $SERVICE_USER -l 2>/dev/null | grep -v "run_defragmentation.sh" | crontab -u $SERVICE_USER - || true

# Add new cron job
print_info "Adding cron job for daily execution at 2:00 AM..."
CRON_JOB="0 2 * * * $INSTALL_DIR/run_defragmentation.sh >> $LOG_DIR/cron.log 2>&1"

# Add the cron job
(crontab -u $SERVICE_USER -l 2>/dev/null; echo "$CRON_JOB") | crontab -u $SERVICE_USER -

# Verify the cron job was added
print_info "Verifying cron job..."
if crontab -u $SERVICE_USER -l 2>/dev/null | grep -q "run_defragmentation.sh"; then
    print_status "Cron job added successfully!"
    echo ""
    print_info "Current cron jobs for user '$SERVICE_USER':"
    crontab -u $SERVICE_USER -l
else
    print_error "Failed to add cron job"
    exit 1
fi

echo ""
print_status "Cron job setup completed!"
print_info "The defragmentation analysis will run automatically at 2:00 AM daily"
print_info "Logs will be written to: $LOG_DIR/cron.log"
print_info "To test manually: sudo /opt/bookingchart-defragmenter/manage.sh run"
