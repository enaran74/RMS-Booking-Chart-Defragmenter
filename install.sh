#!/bin/bash
# BookingChartDefragmenter Installation Script for Debian 12 Linux
# This script installs and configures the BookingChartDefragmenter on a Debian 12 server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/bookingchart-defragmenter"
SERVICE_USER="defrag"
SERVICE_GROUP="defrag"
LOG_DIR="/var/log/bookingchart-defragmenter"
CONFIG_DIR="/etc/bookingchart-defragmenter"

echo -e "${BLUE}🚀 BookingChartDefragmenter Installation for Debian 12 Linux${NC}"
echo "=================================================="

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    curl \
    wget \
    unzip \
    cron \
    systemd \
    logrotate

# Create service user and group
print_status "Creating service user and group..."
if ! getent group $SERVICE_GROUP > /dev/null 2>&1; then
    groupadd $SERVICE_GROUP
fi

if ! getent passwd $SERVICE_USER > /dev/null 2>&1; then
    useradd -r -g $SERVICE_GROUP -s /bin/bash -d $INSTALL_DIR $SERVICE_USER
fi

# Create installation directory
print_status "Creating installation directory..."
mkdir -p $INSTALL_DIR
mkdir -p $LOG_DIR
mkdir -p $CONFIG_DIR

# Copy application files
print_status "Copying application files..."
cp -r $SCRIPT_DIR/* $INSTALL_DIR/
chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR
chmod -R 755 $INSTALL_DIR

# Create Python virtual environment
print_status "Creating Python virtual environment..."
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create log directory with proper permissions
print_status "Setting up logging..."
mkdir -p $LOG_DIR
chown -R $SERVICE_USER:$SERVICE_GROUP $LOG_DIR
chmod -R 755 $LOG_DIR

# Create logrotate configuration
cat > /etc/logrotate.d/bookingchart-defragmenter << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_GROUP
    postrotate
        systemctl reload bookingchart-defragmenter.service > /dev/null 2>&1 || true
    endscript
}
EOF

# Create systemd service file
print_status "Creating systemd service..."
cat > /etc/systemd/system/bookingchart-defragmenter.service << EOF
[Unit]
Description=BookingChartDefragmenter Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
EnvironmentFile=/etc/bookingchart-defragmenter/config.env
ExecStart=$INSTALL_DIR/service_wrapper.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create configuration file template
print_status "Creating configuration template..."
cat > $CONFIG_DIR/config.env << EOF
# BookingChartDefragmenter Configuration
# Copy this file to config.env and update with your credentials

# RMS API Credentials
AGENT_ID=your_agent_id_here
AGENT_PASSWORD=your_agent_password_here
CLIENT_ID=your_client_id_here
CLIENT_PASSWORD=your_client_password_here

# Analysis Configuration
TARGET_PROPERTIES=ALL
ENABLE_EMAILS=false
USE_TRAINING_DB=false

# Email Configuration (if enabled)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=***REMOVED***
APP_PASSWORD=your_app_password_here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=$LOG_DIR/defrag_analyzer.log

# Output Configuration
OUTPUT_DIR=$INSTALL_DIR/output
EOF

chown $SERVICE_USER:$SERVICE_GROUP $CONFIG_DIR/config.env
chmod 600 $CONFIG_DIR/config.env

# Create output directory
mkdir -p $INSTALL_DIR/output
chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR/output
chmod -R 755 $INSTALL_DIR/output

# Create wrapper script
print_status "Creating wrapper script..."
cat > $INSTALL_DIR/run_defragmentation.sh << 'EOF'
#!/bin/bash
# Wrapper script for BookingChartDefragmenter

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="/etc/bookingchart-defragmenter/config.env"

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    echo "Loading configuration from: $CONFIG_FILE"
    # Read and export variables manually to handle spaces in values
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z $key ]] && continue
        
        # Remove leading/trailing whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        # Export the variable
        export "$key=$value"
        echo "Loaded: $key"
    done < "$CONFIG_FILE"
else
    echo "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Build command arguments
ARGS="--agent-id $AGENT_ID --agent-password $AGENT_PASSWORD --client-id $CLIENT_ID --client-password $CLIENT_PASSWORD"

if [ "$TARGET_PROPERTIES" != "ALL" ]; then
    ARGS="$ARGS -p $TARGET_PROPERTIES"
else
    ARGS="$ARGS -p ALL"
fi

if [ "$ENABLE_EMAILS" = "true" ]; then
    ARGS="$ARGS -e"
fi

if [ "$USE_TRAINING_DB" = "true" ]; then
    ARGS="$ARGS -t"
fi

echo "Running with arguments: $ARGS"

# Run the defragmentation analysis
cd "$SCRIPT_DIR"
python3 start.py $ARGS
EOF

chmod +x $INSTALL_DIR/run_defragmentation.sh

# Create cron job for automated runs
print_status "Setting up cron job..."
CRON_JOB="0 2 * * * $INSTALL_DIR/run_defragmentation.sh >> $LOG_DIR/cron.log 2>&1"
(crontab -u $SERVICE_USER -l 2>/dev/null; echo "$CRON_JOB") | crontab -u $SERVICE_USER -

# Reload systemd and enable service
print_status "Configuring systemd service..."
systemctl daemon-reload
systemctl enable bookingchart-defragmenter.service

# Set up firewall (if ufw is available)
if command -v ufw >/dev/null 2>&1; then
    print_status "Configuring firewall..."
    ufw allow out 587/tcp  # SMTP
    ufw allow out 443/tcp  # HTTPS for RMS API
    ufw allow out 80/tcp   # HTTP for RMS API
fi

# Create health check script
print_status "Creating health check script..."
cat > $INSTALL_DIR/health_check.sh << 'EOF'
#!/bin/bash
# Health check script for BookingChartDefragmenter

LOG_FILE="/var/log/bookingchart-defragmenter/defrag_analyzer.log"
SERVICE_NAME="bookingchart-defragmenter"

# Check if service is running
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service $SERVICE_NAME is running"
else
    echo "❌ Service $SERVICE_NAME is not running"
    exit 1
fi

# Check if log file exists and is recent
if [ -f "$LOG_FILE" ]; then
    # Check if log file was modified in the last 24 hours
    if [ $(find "$LOG_FILE" -mtime -1 | wc -l) -gt 0 ]; then
        echo "✅ Log file is recent"
    else
        echo "⚠️  Log file is older than 24 hours"
    fi
else
    echo "❌ Log file not found"
    exit 1
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    echo "✅ Disk usage is acceptable: ${DISK_USAGE}%"
else
    echo "⚠️  Disk usage is high: ${DISK_USAGE}%"
fi

echo "✅ Health check completed successfully"
EOF

chmod +x $INSTALL_DIR/health_check.sh

# Create uninstall script
print_status "Creating uninstall script..."
cat > $INSTALL_DIR/uninstall.sh << 'EOF'
#!/bin/bash
# Uninstall script for BookingChartDefragmenter

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Stopping and disabling service..."
systemctl stop bookingchart-defragmenter.service || true
systemctl disable bookingchart-defragmenter.service || true

print_status "Removing systemd service file..."
rm -f /etc/systemd/system/bookingchart-defragmenter.service

print_status "Removing logrotate configuration..."
rm -f /etc/logrotate.d/bookingchart-defragmenter

print_status "Removing cron job..."
crontab -u defrag -l 2>/dev/null | grep -v "run_defragmentation.sh" | crontab -u defrag - || true

print_status "Removing installation files..."
rm -rf /opt/bookingchart-defragmenter

print_status "Removing log directory..."
rm -rf /var/log/bookingchart-defragmenter

print_status "Removing configuration directory..."
rm -rf /etc/bookingchart-defragmenter

print_status "Removing service user and group..."
userdel defrag 2>/dev/null || true
groupdel defrag 2>/dev/null || true

print_status "Reloading systemd..."
systemctl daemon-reload

print_status "Uninstallation completed successfully!"
EOF

chmod +x $INSTALL_DIR/uninstall.sh

# Final setup
print_status "Finalizing installation..."

# Set proper permissions
chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR
chmod -R 755 $INSTALL_DIR
chmod 600 $INSTALL_DIR/uninstall.sh

# Create README for Linux
cat > $INSTALL_DIR/README_LINUX.md << EOF
# BookingChartDefragmenter for Debian 12 Linux

## Installation Complete

The BookingChartDefragmenter has been successfully installed on your Debian 12 Linux server.

## Configuration

1. Edit the configuration file:
   \`\`\`bash
   sudo nano /etc/bookingchart-defragmenter/config.env
   \`\`\`

2. Update the RMS API credentials and other settings as needed.

3. Restart the service:
   \`\`\`bash
   sudo systemctl restart bookingchart-defragmenter.service
   \`\`\`

## Usage

### Manual Run
\`\`\`bash
sudo /opt/bookingchart-defragmenter/run_defragmentation.sh
\`\`\`

### Service Management
\`\`\`bash
# Start the service
sudo systemctl start bookingchart-defragmenter.service

# Stop the service
sudo systemctl stop bookingchart-defragmenter.service

# Check status
sudo systemctl status bookingchart-defragmenter.service

# View logs
sudo journalctl -u bookingchart-defragmenter.service -f
\`\`\`

### Health Check
\`\`\`bash
sudo /opt/bookingchart-defragmenter/health_check.sh
\`\`\`

## Automated Execution

The system is configured to run automatically at 2:00 AM daily via cron.

## Logs

- Application logs: \`/var/log/bookingchart-defragmenter/\`
- System logs: \`journalctl -u bookingchart-defragmenter.service\`

## Uninstallation

To uninstall the application:
\`\`\`bash
sudo /opt/bookingchart-defragmenter/uninstall.sh
\`\`\`

## Support

For issues or questions, check the logs and ensure the configuration is correct.
EOF

print_status "Installation completed successfully!"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Edit the configuration file: sudo nano /etc/bookingchart-defragmenter/config.env"
echo "2. Update your RMS API credentials"
echo "3. Start the service: sudo systemctl start bookingchart-defragmenter.service"
echo "4. Check the status: sudo systemctl status bookingchart-defragmenter.service"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "See /opt/bookingchart-defragmenter/README_LINUX.md for detailed usage instructions"
echo ""
echo -e "${BLUE}🔧 Health Check:${NC}"
echo "Run: sudo /opt/bookingchart-defragmenter/health_check.sh"
