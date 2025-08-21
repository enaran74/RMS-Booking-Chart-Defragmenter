#!/bin/bash

# Incremental deployment script for quick updates without full Docker rebuild
# Usage: ./deploy_incremental.sh [--full] [--files-only]

set -e

VPS_HOST="100.78.0.44"
VPS_USER="enaran"
VPS_PASSWORD="Configur8&1"
VPS_APP_DIR="/opt/defrag-app"
CONTAINER_NAME="defrag-web-app"

FULL_DEPLOY=false
FILES_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL_DEPLOY=true
            shift
            ;;
        --files-only)
            FILES_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--full] [--files-only]"
            exit 1
            ;;
    esac
done

echo "🚀 Incremental Deployment Script"
echo "================================="
echo "Full deploy: $FULL_DEPLOY"
echo "Files only: $FILES_ONLY"
echo ""

if [ "$FULL_DEPLOY" = true ]; then
    echo "🔄 Running full deployment..."
    ./deploy_web_app.sh
    exit $?
fi

echo "📦 Creating incremental update package..."

# Create a package with updated files
tar -czf incremental_update.tar.gz \
    --exclude='*/__pycache__*' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    defrag_analyzer.py \
    utils.py \
    web_app/

echo "📤 Uploading incremental update to VPS..."
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no incremental_update.tar.gz ${VPS_USER}@${VPS_HOST}:${VPS_APP_DIR}/

echo "🔧 Applying incremental update on VPS..."
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} "
    cd $VPS_APP_DIR
    
    echo '📂 Extracting incremental update...'
    tar -xzf incremental_update.tar.gz
    
    echo '🐳 Checking container status...'
    if docker ps | grep -q $CONTAINER_NAME; then
        echo '✅ Container is running, applying hot update...'
        
        # Copy files directly to running container
        echo '📋 Copying defrag_analyzer.py to container...'
        docker cp defrag_analyzer.py $CONTAINER_NAME:/app/
        
        echo '📋 Copying utils.py to container...'
        docker cp utils.py $CONTAINER_NAME:/app/
        
        echo '📋 Copying web app files to container...'
        docker cp web_app/main.py $CONTAINER_NAME:/app/
        docker cp web_app/app/. $CONTAINER_NAME:/app/app/
        docker cp web_app/requirements.txt $CONTAINER_NAME:/app/
        
        if [ '$FILES_ONLY' != true ]; then
            echo '📦 Installing/updating Python dependencies...'
            docker exec $CONTAINER_NAME pip install -r /app/requirements.txt
            
            echo '🔄 Restarting container to load changes...'
            docker-compose restart web-app
        else
            echo '📁 Files updated, no container restart needed'
        fi
    else
        echo '❌ Container not running, starting containers...'
        docker-compose up -d
    fi
    
    echo '🧹 Cleaning up...'
    rm -f incremental_update.tar.gz
    
    echo '✅ Incremental deployment complete!'
    echo '📊 Container status:'
    docker-compose ps
"

echo "🧹 Cleaning up local files..."
rm -f incremental_update.tar.gz

echo ""
echo "✅ Incremental deployment completed!"
echo ""
echo "🌐 Web application status:"
echo "   URL: http://${VPS_HOST}:8000"
echo "   Health: http://${VPS_HOST}:8000/health"
echo ""
echo "💡 Tips:"
echo "   - Use --files-only for code changes that don't require restart"
echo "   - Use --full for major changes or dependency updates"
echo "   - Check logs: ssh ${VPS_USER}@${VPS_HOST} 'cd ${VPS_APP_DIR} && docker-compose logs web-app --tail=20'"
