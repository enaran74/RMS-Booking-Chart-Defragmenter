#!/bin/bash

# Deploy Web Application to VPS
# This script copies the web application to the VPS and starts it

set -e

# VPS Configuration - Can be overridden by environment variables for security
VPS_IP="${VPS_IP:-100.78.0.44}"
VPS_USER="${VPS_USER:-enaran}"
VPS_PASSWORD="${VPS_PASSWORD:-Configur8&1}"
APP_DIR="/opt/defrag-app"

echo "🚀 Deploying RMS Booking Chart Defragmenter Web Application to VPS..."

# Create a temporary archive of the web application
echo "📦 Creating application archive..."
tar -czf web_app.tar.gz -C web_app .

# Copy the archive to the VPS
echo "📤 Copying application to VPS..."
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no web_app.tar.gz "$VPS_USER@$VPS_IP:/tmp/"

# Extract and deploy on the VPS
echo "🔧 Deploying application on VPS..."
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" << 'EOF'
    # Stop existing containers if running
    cd /opt/defrag-app
    if [ -f docker-compose.yml ]; then
        echo "🛑 Stopping existing containers..."
        docker-compose down || true
    fi
    
    # Clean up old files
    echo "🧹 Cleaning up old files..."
    rm -rf /opt/defrag-app/*
    
    # Extract new application
    echo "📂 Extracting application..."
    tar -xzf /tmp/web_app.tar.gz -C /opt/defrag-app
    
    # Set proper permissions
    echo "🔐 Setting permissions..."
    chmod +x /opt/defrag-app/*.py
    chmod +x /opt/defrag-app/Dockerfile
    chmod +x /opt/defrag-app/docker-compose.yml
    
    # Create logs directory
    mkdir -p /opt/defrag-app/logs
    
               # Build and start the application
           echo "🏗️ Building and starting application..."
           cd /opt/defrag-app
           
           # Check network connectivity before building
           echo "🌐 Checking network connectivity..."
           ping -c 3 deb.debian.org || echo "⚠️ Warning: Cannot reach deb.debian.org"
           ping -c 3 8.8.8.8 || echo "⚠️ Warning: Cannot reach Google DNS"
           
           # Check Docker daemon
           echo "🐳 Checking Docker status..."
           docker --version
           docker system info | grep "Server Version" || echo "⚠️ Warning: Docker daemon may not be running properly"
           
           # Build with timeout and verbose output
           echo "📦 Building Docker image (this may take several minutes)..."
           echo "🔍 Build progress will be shown in real-time..."
           echo "⏰ Build timeout: 10 minutes"
           echo "📋 Starting build at: $(date)"
           
           # Create build log file
           BUILD_LOG="/opt/defrag-app/logs/build-$(date +%Y%m%d-%H%M%S).log"
           mkdir -p /opt/defrag-app/logs
           
           # Use host network for build to avoid Docker networking issues
           export DOCKER_BUILDKIT=1
           timeout 600 docker-compose build --no-cache --progress=plain --build-arg BUILDKIT_INLINE_CACHE=1 web-app 2>&1 | tee "$BUILD_LOG" || {
               echo "❌ Docker build failed or timed out after 10 minutes"
               echo "📋 Checking for existing containers and cleaning up..."
               docker-compose down --remove-orphans
               docker system prune -f
               echo "🔄 Retrying build without cache..."
               RETRY_LOG="/opt/defrag-app/logs/build-retry-$(date +%Y%m%d-%H%M%S).log"
               timeout 300 docker-compose build --no-cache --progress=plain --build-arg BUILDKIT_INLINE_CACHE=1 web-app 2>&1 | tee "$RETRY_LOG" || {
                   echo "❌ Second build attempt failed. Exiting..."
                   exit 1
               }
           }
           
           echo "🚀 Starting application..."
           docker-compose up -d
           
           # Wait for application to start
           echo "⏳ Waiting for application to start..."
           sleep 20
    
               # Check application status
           echo "🔍 Checking application status..."
           docker-compose ps
           docker-compose logs web-app --tail=20
           
           # Run database migration
           echo "🗄️ Running database migration..."
           if [ -f migrate_user_properties.py ]; then
               echo "🔄 Running user-property migration..."
               docker exec defrag-web-app python migrate_user_properties.py
           fi
    
    # Clean up temporary files
    rm -f /tmp/web_app.tar.gz
    
    echo "✅ Deployment completed!"
    echo ""
    echo "🌐 Web application is now running on:"
    echo "   http://100.78.0.44:8000"
    echo ""
    echo "📚 API documentation available at:"
    echo "   http://100.78.0.44:8000/docs"
    echo ""
    echo "🔍 Health check:"
    echo "   http://100.78.0.44:8000/health"
    echo ""
    echo "📋 New features available:"
    echo "   - User profile editing with email addresses"
    echo "   - Strong password validation and changes"
    echo "   - Admin user management (create, update, delete users)"
    echo "   - Admin users cannot be deleted"
    echo "   - Password strength requirements enforced"
EOF

# Clean up local archive
echo "🧹 Cleaning up local files..."
rm -f web_app.tar.gz

echo "✅ Deployment script completed!"
echo ""
echo "📋 Next steps:"
echo "1. Access the web application at http://100.78.0.44:8000"
echo "2. Login with admin user (username: admin, password: admin)"
echo "3. Test the new user management features:"
echo "   - Edit profile and add email address"
echo "   - Change password with strong validation"
echo "   - Create new users (admin only)"
echo "   - Manage existing users (admin only)"
echo "4. Integrate with your existing defragmentation service"
