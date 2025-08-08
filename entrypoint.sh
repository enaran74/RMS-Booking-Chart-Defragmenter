#!/bin/bash
set -e

# Function to print colored output
print_status() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_error() {
    echo -e "\033[0;31m❌ $1\033[0m"
}

# Check if required environment variables are set
if [ -z "$AGENT_ID" ] || [ -z "$AGENT_PASSWORD" ] || [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_PASSWORD" ]; then
    print_error "Missing required RMS API credentials"
    print_error "Please set: AGENT_ID, AGENT_PASSWORD, CLIENT_ID, CLIENT_PASSWORD"
    exit 1
fi

# Set default values for optional variables
export TARGET_PROPERTIES=${TARGET_PROPERTIES:-"ALL"}
export ENABLE_EMAILS=${ENABLE_EMAILS:-"false"}
export USE_TRAINING_DB=${USE_TRAINING_DB:-"false"}

print_status "Starting BookingChartDefragmenter"
print_status "Target Properties: $TARGET_PROPERTIES"
print_status "Enable Emails: $ENABLE_EMAILS"
print_status "Use Training DB: $USE_TRAINING_DB"

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

# Run the application
exec python3 start.py $ARGS

