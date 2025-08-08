#!/bin/bash
# Service Wrapper for BookingChartDefragmenter
# This script ensures the service environment is ready without running analysis

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="/etc/bookingchart-defragmenter/config.env"
LOG_FILE="/var/log/bookingchart-defragmenter/service.log"

# Function to print colored output
print_status() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_error() {
    echo -e "\033[0;31m❌ $1\033[0m"
}

print_info() {
    echo -e "\033[0;34mℹ️  $1\033[0m"
}

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Log startup
echo "$(date): Service wrapper starting" >> "$LOG_FILE"

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    print_info "Loading configuration from: $CONFIG_FILE"
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
    done < "$CONFIG_FILE"
    print_status "Configuration loaded successfully"
else
    print_error "Configuration file not found: $CONFIG_FILE"
    echo "$(date): ERROR - Configuration file not found" >> "$LOG_FILE"
    exit 1
fi

# Verify Python environment
print_info "Verifying Python environment..."
if [ -d "$SCRIPT_DIR/venv" ]; then
    print_status "Virtual environment exists"
    export PATH="$SCRIPT_DIR/venv/bin:$PATH"
else
    print_error "Virtual environment not found"
    echo "$(date): ERROR - Virtual environment not found" >> "$LOG_FILE"
    exit 1
fi

# Test Python import
print_info "Testing Python imports..."
if python3 -c "import pandas, numpy, requests, openpyxl; print('✅ All dependencies available')" 2>/dev/null; then
    print_status "Python dependencies verified"
else
    print_error "Python dependencies missing"
    echo "$(date): ERROR - Python dependencies missing" >> "$LOG_FILE"
    exit 1
fi

# Test RMS API connectivity (optional - just verify credentials are set)
print_info "Verifying RMS API credentials..."
if [ -n "$AGENT_ID" ] && [ -n "$AGENT_PASSWORD" ] && [ -n "$CLIENT_ID" ] && [ -n "$CLIENT_PASSWORD" ]; then
    print_status "RMS API credentials configured"
else
    print_error "RMS API credentials missing"
    echo "$(date): ERROR - RMS API credentials missing" >> "$LOG_FILE"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/output"

# Log successful startup
echo "$(date): Service wrapper started successfully" >> "$LOG_FILE"
print_status "Service environment ready"

# Keep the service running (this is what systemd expects)
print_info "Service environment is ready. Analysis will run via cron or manual execution."
print_info "To run analysis manually: sudo /opt/bookingchart-defragmenter/run_defragmentation.sh"
print_info "To check cron schedule: sudo crontab -u defrag -l"

# Sleep indefinitely to keep service "active"
# This allows systemd to manage the service without running analysis
while true; do
    sleep 3600  # Sleep for 1 hour
    # Log that we're still alive
    echo "$(date): Service wrapper heartbeat" >> "$LOG_FILE"
done
