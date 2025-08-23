#!/bin/bash
# Health Check Script for RMS Defragmenter Web Application
# Simple health check to verify the web application is responding

# Test the health endpoint
curl -f http://localhost:8000/health > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed"
    exit 1
fi