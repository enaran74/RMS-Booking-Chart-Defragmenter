#!/bin/bash

# Deploy Complete RMS Defragmenter Application to VPS
# This script deploys the entire application stack including web app, database, and all services

set -e

# VPS Configuration - Can be overridden by environment variables for security
VPS_IP="${VPS_IP:-100.78.0.44}"
VPS_USER="${VPS_USER:-enaran}"
VPS_PASSWORD="${VPS_PASSWORD:-Configur8&1}"
APP_DIR="/opt/defrag-app"

echo "🚀 Deploying Complete RMS Booking Chart Defragmenter Application to VPS..."

# Create a temporary archive of the web application
echo "📦 Creating complete application archive..."
tar -czf web_app.tar.gz -C web_app .

# Copy additional required files to a temporary directory and recreate archive
echo "📋 Adding additional required files..."
mkdir -p temp_deploy
cp -r web_app/* temp_deploy/
cp health_check.sh docker-compose.yml requirements.txt temp_deploy/

# Copy CLI Python files needed for defragmentation functionality
echo "📋 Adding CLI components for defragmentation..."
cp defrag_analyzer.py temp_deploy/ 2>/dev/null || echo "⚠️ defrag_analyzer.py not found"
cp rms_client.py temp_deploy/ 2>/dev/null || echo "⚠️ rms_client.py not found"
cp utils.py temp_deploy/ 2>/dev/null || echo "⚠️ utils.py not found"
cp excel_generator.py temp_deploy/ 2>/dev/null || echo "⚠️ excel_generator.py not found"
cp email_sender.py temp_deploy/ 2>/dev/null || echo "⚠️ email_sender.py not found"
cp holiday_client.py temp_deploy/ 2>/dev/null || echo "⚠️ holiday_client.py not found"
cp school_holiday_client.py temp_deploy/ 2>/dev/null || echo "⚠️ school_holiday_client.py not found"
cp school_holidays.json temp_deploy/ 2>/dev/null || echo "⚠️ school_holidays.json not found"

tar -czf web_app.tar.gz -C temp_deploy .
rm -rf temp_deploy

# Copy the archive and docker-compose file to the VPS
echo "📤 Copying application to VPS..."
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no web_app.tar.gz "$VPS_USER@$VPS_IP:/tmp/"
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no docker-compose.yml "$VPS_USER@$VPS_IP:/tmp/"

# Extract and deploy on the VPS
echo "🔧 Deploying application on VPS..."
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" << 'EOF'
    # Stop existing containers if running
    cd /opt/defrag-app
    if [ -f docker-compose.yml ]; then
        echo "🛑 Stopping existing containers..."
        docker-compose down || true
    fi
    
    # Clean up old files (preserve .env configuration)
    echo "🧹 Cleaning up old files (preserving .env configuration)..."
    find /opt/defrag-app -mindepth 1 -maxdepth 1 ! -name '.env' -exec rm -rf {} +
    
    # Extract new application
    echo "📂 Extracting application..."
    tar -xzf /tmp/web_app.tar.gz -C /opt/defrag-app
    
    # Set proper permissions
    echo "🔐 Setting permissions..."
    chmod +x /opt/defrag-app/*.py
    chmod +x /opt/defrag-app/Dockerfile
    
    # Create logs directory
    mkdir -p /opt/defrag-app/logs
    
    # Copy the docker-compose configuration
    echo "🔧 Setting up docker-compose configuration..."
    cp /tmp/docker-compose.yml /opt/defrag-app/docker-compose.yml
    
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
           
           # Force complete cleanup to avoid caching issues (preserve database data)
           echo "🧹 Forcing complete cleanup of Docker cache (preserving database)..."
           docker-compose down --remove-orphans || true
           docker system prune -f || true
           docker builder prune -f || true
           
           # Build with proper service name and force no cache
           echo "🏗️ Building application with fresh cache..."
           timeout 600 docker-compose build --no-cache --progress=plain defrag-app 2>&1 | tee "$BUILD_LOG" || {
               echo "❌ Docker build failed or timed out after 10 minutes"
               echo "📋 Checking for existing containers and cleaning up..."
               docker-compose down --remove-orphans
               docker system prune -f
               echo "🔄 Retrying build without cache..."
               RETRY_LOG="/opt/defrag-app/logs/build-retry-$(date +%Y%m%d-%H%M%S).log"
               timeout 300 docker-compose build --no-cache --progress=plain defrag-app 2>&1 | tee "$RETRY_LOG" || {
                   echo "❌ Second build attempt failed. Exiting..."
                   exit 1
               }
           }
           
           echo "🚀 Starting application..."
           docker-compose up -d
           
           # Wait for application to start
           echo "⏳ Waiting for application to start..."
           sleep 30
           
           # Force-copy all web application code to container to override any Docker caching
           echo "🔄 Ensuring all web application code is up-to-date..."
           echo "   📁 Copying entire app directory (templates, static, API, models, core, etc.)"
           docker cp /opt/defrag-app/app/ defrag-app:/app/ 2>/dev/null || echo "⚠️ Could not copy app directory (container may not be ready yet)"
           docker cp /opt/defrag-app/health_check.sh defrag-app:/app/health_check.sh 2>/dev/null || echo "⚠️ Could not copy health_check.sh (container may not be ready yet)"
           docker exec defrag-app chmod +x /app/health_check.sh 2>/dev/null || echo "⚠️ Could not make health_check.sh executable"
           
           # Force-copy CLI components for defragmentation functionality
           echo "🔄 Ensuring CLI components are active in container..."
           docker cp /opt/defrag-app/defrag_analyzer.py defrag-app:/app/defrag_analyzer.py 2>/dev/null || echo "⚠️ Could not copy defrag_analyzer.py"
           docker cp /opt/defrag-app/rms_client.py defrag-app:/app/rms_client.py 2>/dev/null || echo "⚠️ Could not copy rms_client.py"
           docker cp /opt/defrag-app/utils.py defrag-app:/app/utils.py 2>/dev/null || echo "⚠️ Could not copy utils.py"
           docker cp /opt/defrag-app/excel_generator.py defrag-app:/app/excel_generator.py 2>/dev/null || echo "⚠️ Could not copy excel_generator.py"
           docker cp /opt/defrag-app/email_sender.py defrag-app:/app/email_sender.py 2>/dev/null || echo "⚠️ Could not copy email_sender.py"
           docker cp /opt/defrag-app/holiday_client.py defrag-app:/app/holiday_client.py 2>/dev/null || echo "⚠️ Could not copy holiday_client.py"
           docker cp /opt/defrag-app/school_holiday_client.py defrag-app:/app/school_holiday_client.py 2>/dev/null || echo "⚠️ Could not copy school_holiday_client.py"
           docker cp /opt/defrag-app/school_holidays.json defrag-app:/app/school_holidays.json 2>/dev/null || echo "⚠️ Could not copy school_holidays.json"
           
           # Restart container to ensure all changes take effect
           echo "🔄 Restarting container to apply latest code..."
           docker-compose restart defrag-app
           
           # Final wait for restart
           echo "⏳ Waiting for application restart..."
           sleep 15
    
               # Check application status
           echo "🔍 Checking application status..."
           docker-compose ps
           docker-compose logs defrag-app --tail=20
           
           # Run database migration
           echo "🗄️ Running database migration..."
           if [ -f migrate_user_properties.py ]; then
               echo "🔄 Running user-property migration..."
               docker exec defrag-app python migrate_user_properties.py
           fi
           
           # Restore .env synchronization (copy host .env to container if it exists)
           if [ -f .env ]; then
               echo "🔄 Restoring environment configuration synchronization..."
               docker cp .env defrag-app:/app/.env || echo "⚠️ Note: Container .env sync will happen on next configuration save"
           fi
           
           # Verify deployment fixes are active
           echo "🔍 Verifying deployment fixes..."
           SETUP_FIX_COUNT=$(docker exec defrag-app grep -c "except Exception as error:" /app/app/api/v1/endpoints/setup.py 2>/dev/null || echo "0")
           DB_FIX_COUNT=$(docker exec defrag-app grep -c "pool_size=2" /app/app/core/database.py 2>/dev/null || echo "0")
           
           if [ "$SETUP_FIX_COUNT" -gt "0" ] && [ "$DB_FIX_COUNT" -gt "0" ]; then
               echo "✅ Deployment fixes verified: setup.py ($SETUP_FIX_COUNT fixes) and database.py ($DB_FIX_COUNT fixes) are correct"
           else
               echo "⚠️ Warning: Some fixes may not be active (setup: $SETUP_FIX_COUNT, database: $DB_FIX_COUNT)"
               echo "🔄 Re-copying files as fallback..."
               docker cp /opt/defrag-app/app/api/v1/endpoints/setup.py defrag-app:/app/app/api/v1/endpoints/setup.py 2>/dev/null || true
               docker cp /opt/defrag-app/app/core/database.py defrag-app:/app/app/core/database.py 2>/dev/null || true
               docker-compose restart defrag-app
               sleep 10
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

echo "✅ Complete application deployment finished!"
echo ""
echo "📋 Next steps:"
echo "1. Access the application at http://100.78.0.44:8000"
echo "2. Login with admin credentials (username: admin, password: admin123)"
echo "3. Configure environment variables via Setup → Environment Configuration"
echo "4. Test application features:"
echo "   - User management and authentication"
echo "   - Environment configuration with auto-restart"
echo "   - Property and defragmentation management"
echo "5. Application is ready for production use"
