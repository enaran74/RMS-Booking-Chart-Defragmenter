#!/bin/bash
# BookingChartDefragmenter Update Script
# This script safely updates the application from GitHub on production servers

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/bookingchart-defragmenter"
SERVICE_NAME="bookingchart-defragmenter.service"
SERVICE_USER="defrag"
LOG_DIR="/var/log/bookingchart-defragmenter"
BACKUP_DIR="/opt/bookingchart-defragmenter-backup"
TEMP_DIR="/tmp/bookingchart-defragmenter-update"
GIT_REPO_URL="git@github.com:enaran74/RMS-Booking-Chart-Defragmenter.git"
BRANCH=${1:-main}  # Default to main branch, but allow override

echo -e "${BLUE}🔄 BookingChartDefragmenter Update Script${NC}"
echo "=================================================="
echo -e "${BLUE}Target Branch: ${BRANCH}${NC}"
echo -e "${BLUE}Install Directory: ${INSTALL_DIR}${NC}"
echo ""

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

# Function to rollback on failure
rollback() {
    print_error "Update failed! Rolling back to previous version..."
    
    if [ -d "$BACKUP_DIR" ]; then
        print_info "Stopping service..."
        systemctl stop $SERVICE_NAME || true
        
        print_info "Restoring backup..."
        rm -rf $INSTALL_DIR
        mv $BACKUP_DIR $INSTALL_DIR
        
        print_info "Starting service..."
        systemctl start $SERVICE_NAME
        
        print_status "Rollback completed successfully!"
    else
        print_error "No backup found! Manual intervention required."
    fi
    
    # Cleanup
    rm -rf $TEMP_DIR
    exit 1
}

# Trap to ensure rollback on script failure
trap rollback ERR

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if service exists
if ! systemctl list-units --full -all | grep -Fq "$SERVICE_NAME"; then
    print_error "Service $SERVICE_NAME not found. Please install the application first."
    exit 1
fi

# Check if install directory exists
if [ ! -d "$INSTALL_DIR" ]; then
    print_error "Installation directory $INSTALL_DIR not found."
    exit 1
fi

# Check SSH key configuration for GitHub
print_info "Checking SSH configuration for GitHub..."
if ! ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    print_warning "SSH key not configured for GitHub. Attempting to configure..."
    
    # Check if SSH key exists
    if [ -f "/home/$SERVICE_USER/.ssh/id_rsa" ]; then
        print_info "SSH key found. Adding to SSH agent..."
        eval "$(ssh-agent -s)"
        ssh-add /home/$SERVICE_USER/.ssh/id_rsa
        
        # Test SSH connection again
        if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
            print_status "SSH authentication configured successfully"
        else
            print_error "SSH authentication failed. Please configure SSH keys manually:"
            print_info "1. Generate SSH key: ssh-keygen -t rsa -b 4096 -C 'your_email@example.com'"
            print_info "2. Add to GitHub: https://github.com/settings/keys"
            print_info "3. Test: ssh -T git@github.com"
            exit 1
        fi
    else
        print_error "SSH key not found. Please configure SSH keys manually:"
        print_info "1. Generate SSH key: ssh-keygen -t rsa -b 4096 -C 'your_email@example.com'"
        print_info "2. Add to GitHub: https://github.com/settings/keys"
        print_info "3. Test: ssh -T git@github.com"
        exit 1
    fi
else
    print_status "SSH authentication configured"
fi

# Step 1: Check current status
print_info "Checking current service status..."
SERVICE_STATUS=$(systemctl is-active $SERVICE_NAME || echo "inactive")
print_info "Current service status: $SERVICE_STATUS"

# Step 2: Create backup of current installation
print_info "Creating backup of current installation..."
rm -rf $BACKUP_DIR  # Remove old backup
cp -r $INSTALL_DIR $BACKUP_DIR
print_status "Backup created at $BACKUP_DIR"

# Step 3: Download latest version
print_info "Downloading latest version from GitHub..."
rm -rf $TEMP_DIR
git clone --branch $BRANCH --depth 1 $GIT_REPO_URL $TEMP_DIR
print_status "Latest version downloaded"

# Step 4: Check for updates (compare git hashes if possible)
if [ -d "$INSTALL_DIR/.git" ]; then
    cd $INSTALL_DIR
    CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    cd $TEMP_DIR
    NEW_COMMIT=$(git rev-parse HEAD)
    
    if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
        print_warning "No updates available. Current version is already up to date."
        echo -e "${BLUE}Current commit: $CURRENT_COMMIT${NC}"
        rm -rf $TEMP_DIR
        rm -rf $BACKUP_DIR
        exit 0
    else
        print_info "Update available!"
        echo -e "${BLUE}Current commit: $CURRENT_COMMIT${NC}"
        echo -e "${BLUE}New commit: $NEW_COMMIT${NC}"
    fi
fi

# Step 5: Stop the service
print_info "Stopping $SERVICE_NAME..."
systemctl stop $SERVICE_NAME
print_status "Service stopped"

# Step 6: Preserve configuration and logs
print_info "Preserving configuration files..."
if [ -f "$INSTALL_DIR/config.env" ]; then
    cp "$INSTALL_DIR/config.env" "$TEMP_DIR/"
fi

# Preserve any custom configurations
if [ -d "$INSTALL_DIR/config" ]; then
    cp -r "$INSTALL_DIR/config" "$TEMP_DIR/"
fi

# Step 7: Update application files
print_info "Updating application files..."
# Remove old files (but preserve venv and other important directories)
find $INSTALL_DIR -maxdepth 1 -type f -name "*.py" -delete
find $INSTALL_DIR -maxdepth 1 -type f -name "*.sh" -delete
find $INSTALL_DIR -maxdepth 1 -type f -name "*.yml" -delete
find $INSTALL_DIR -maxdepth 1 -type f -name "*.yaml" -delete
find $INSTALL_DIR -maxdepth 1 -type f -name "*.txt" -delete
find $INSTALL_DIR -maxdepth 1 -type f -name "*.md" -delete
find $INSTALL_DIR -maxdepth 1 -type f -name "Dockerfile*" -delete
rm -rf $INSTALL_DIR/.github

# Copy new files
cp -r $TEMP_DIR/* $INSTALL_DIR/
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
chmod +x $INSTALL_DIR/*.sh 2>/dev/null || true

# Ensure specific scripts are executable
chmod +x $INSTALL_DIR/health_check.sh 2>/dev/null || true
chmod +x $INSTALL_DIR/manage.sh 2>/dev/null || true
chmod +x $INSTALL_DIR/update.sh 2>/dev/null || true
chmod +x $INSTALL_DIR/setup_ssh.sh 2>/dev/null || true

print_status "Application files updated"

# Step 8: Update Python dependencies
print_info "Updating Python dependencies..."
cd $INSTALL_DIR
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
print_status "Dependencies updated"

# Step 9: Run health check
print_info "Running health check..."
if [ -f "$INSTALL_DIR/health_check.sh" ]; then
    bash $INSTALL_DIR/health_check.sh || {
        print_warning "Health check failed, but continuing with update..."
    }
else
    print_warning "Health check script not found, skipping..."
fi

# Step 9.5: Verify service configuration
print_info "Verifying service configuration..."
if [ -f "/etc/systemd/system/$SERVICE_NAME" ]; then
    print_status "Service file exists"
    # Reload systemd to pick up any changes
    systemctl daemon-reload
else
    print_error "Service file not found at /etc/systemd/system/$SERVICE_NAME"
    print_info "This might indicate the service wasn't properly installed."
    rollback
fi

# Step 10: Start the service
print_info "Starting $SERVICE_NAME..."
systemctl start $SERVICE_NAME
sleep 5  # Give service time to start

# Step 11: Verify service is running
SERVICE_STATUS=$(systemctl is-active $SERVICE_NAME)
if [ "$SERVICE_STATUS" = "active" ]; then
    print_status "Service started successfully"
else
    print_error "Service failed to start. Status: $SERVICE_STATUS"
    print_info "Checking service logs for errors..."
    echo ""
    echo -e "${BLUE}📝 Recent Service Logs:${NC}"
    journalctl -u $SERVICE_NAME --no-pager -n 20
    echo ""
    print_error "Service failed to start. Check logs above for details."
    rollback
fi

# Step 12: Final verification
print_info "Performing final verification..."
sleep 10  # Wait a bit more for service to stabilize

SERVICE_STATUS=$(systemctl is-active $SERVICE_NAME)
if [ "$SERVICE_STATUS" = "active" ]; then
    print_status "Update completed successfully!"
    
    # Show service status
    echo ""
    echo -e "${BLUE}📊 Service Status:${NC}"
    systemctl status $SERVICE_NAME --no-pager -l
    
    # Show recent logs
    echo ""
    echo -e "${BLUE}📝 Recent Logs:${NC}"
    journalctl -u $SERVICE_NAME --no-pager -n 20
    
    # Cleanup
    rm -rf $TEMP_DIR
    rm -rf $BACKUP_DIR
    
    echo ""
    print_status "✨ Update completed successfully! ✨"
    echo -e "${BLUE}🔍 Monitor logs with: sudo journalctl -u $SERVICE_NAME -f${NC}"
else
    print_error "Service is not running properly after update"
    rollback
fi

# Disable trap since we completed successfully
trap - ERR
