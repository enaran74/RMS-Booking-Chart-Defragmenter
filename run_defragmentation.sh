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
CONFIG_FILE="/etc/bookingchart-defragmenter/config.env"
LOG_FILE="/var/log/bookingchart-defragmenter/analysis.log"
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

# Run the analysis and capture output
if env AGENT_ID="$AGENT_ID" AGENT_PASSWORD="$AGENT_PASSWORD" CLIENT_ID="$CLIENT_ID" CLIENT_PASSWORD="$CLIENT_PASSWORD" "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/start.py" 2>&1 | tee -a "$LOG_FILE"; then
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
