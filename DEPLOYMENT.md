# 🚀 RMS Defragmenter - Production Deployment Guide

## Overview

This guide covers the production deployment pipeline using pre-built Docker images for reliable customer deployments.

## 🏗️ Build Pipeline (Developer)

### Prerequisites

- Docker Desktop with BuildKit enabled
- Docker Hub account (dhpsystems)
- Multi-architecture build support

### Building Production Images

```bash
# Build and push production images
./build-pipeline.sh
```

This will:

- Build for `linux/amd64` and `linux/arm64`
- Push to Docker Hub as `dhpsystems/rms-defragmenter:latest`
- Create versioned tags

### Manual Build Process

```bash
# Setup multi-arch builder
docker buildx create --name multiarch --use

# Build and push
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t dhpsystems/rms-defragmenter:2.0.0 \
    -t dhpsystems/rms-defragmenter:latest \
    --push \
    .
```

## 🚀 Customer Deployment

### One-Command Installation

```bash
curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install.sh | bash
```

### What the Installer Does

1. **Environment Detection**
   - Detects Tailscale/VPN conflicts
   - Tests Docker networking
   - Chooses appropriate deployment method

2. **Smart Configuration**
   - Standard networking (default)
   - Host networking (for problematic environments)
   - Automatic fallback based on environment

3. **Downloads Pre-built Images**
   - No local compilation required
   - Fast deployment (5-10 minutes vs 30-60 minutes)
   - Consistent, tested images

## 📁 Deployment Configurations

### VPS Deployment (Host Networking + Bind Mounts)

- **File**: `docker-compose.yml` (host networking)
- **Bind Mounts** (included):
  - `./app` → `/app/app` (web app)
  - `./main.py` → `/app/main.py` (FastAPI entrypoint)
  - `./app/static/uploads` → `/app/app/static/uploads` (avatars)
  - Analyzer helpers mounted into `/app/` for CLI/web shared use:
    `defrag_analyzer.py`, `utils.py`, `holiday_client.py`, `school_holiday_client.py`, `school_holidays.json`, `rms_client.py`, `excel_generator.py`, `email_sender.py`
- **Why**: Eliminates stale templates and avoids long Docker builds over Tailscale/VPN. Updates are applied by syncing files and restarting only the app container.

## 🔧 Configuration

### Environment Variables

All configuration is done via a single unified `.env` file (shared by both the web app and the original CLI):

```bash
# RMS API Credentials (Required)
AGENT_ID=your_agent_id
AGENT_PASSWORD=your_agent_password
CLIENT_ID=your_client_id
CLIENT_PASSWORD=your_client_password

# Database Configuration (hostnet stack)
DB_HOST=localhost
DB_PORT=5433
DB_NAME=defrag_db
DB_USER=defrag_user
DB_PASSWORD=DefragDB2024!

# Application Configuration
USE_TRAINING_DB=false
WEB_APP_PORT=8000
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
```

### Customer Management Commands

```bash
# Start system
./start.sh

# Stop system
./stop.sh

# View status
./status.sh

# View logs
./logs.sh

# Update to latest version
./update.sh
```

## 🔍 Troubleshooting

### Network Issues

If installation fails with networking errors:

1. **Automatic Detection**: The installer detects most issues automatically
2. **Standard Deployment**: Use the single deployment script:

```bash
./deploy_app.sh
```

### Common Issues

#### Tailscale Conflicts

```bash
# Symptoms: Docker build hangs, apt-get timeouts
# Solution: Host networking is used automatically by the VPS compose
```

#### VPN Conflicts

```bash
# Symptoms: Cannot reach external services
# Solution: Disable VPN during installation or use host networking
```

#### Resource Constraints

```bash
# Symptoms: Out of memory errors
# Solution: Pre-built images eliminate this issue
```

## 📈 Benefits of This Approach

### For Customers

- ✅ **Fast deployment**: 5-10 minutes vs 30-60 minutes
- ✅ **Reliable**: No build-time failures
- ✅ **Works everywhere**: Automatic environment detection
- ✅ **Easy updates**: Pull new images, restart
- ✅ **No technical expertise**: One command installation

### For Support

- ✅ **Consistent environment**: Same image everywhere
- ✅ **Predictable issues**: Known, tested configurations
- ✅ **Easy debugging**: Standard image, standard logs
- ✅ **Version control**: Tagged releases, rollback capability

### For Development

- ✅ **Build once, deploy everywhere**: No customer-specific builds
- ✅ **Test what customers get**: Exact same images
- ✅ **Faster iterations**: Fast-deploy via bind mounts and restarts
- ✅ **Multi-architecture**: ARM64 support for modern hardware

## ⚡ Fast Update Process (Recommended for iteration)

### From developer workstation

```bash
./manage.sh fast-deploy
```

This command:

- Syncs `web_app/app/templates`, `web_app/app/static`, and `web_app/main.py` to `/opt/defrag-app`
- Restarts only the `defrag-app` container

Expected duration: seconds (no image rebuild).

### On VPS

```bash
cd /opt/defrag-app
docker-compose down || true
docker-compose up -d
docker-compose ps
```

### Local dev utility

```bash
./manage.sh dev-restart
```

Restarts the docker-compose stack locally/wherever the script runs.

## 🔄 Update Process

### Developer Updates

1. Update code
2. Run `./build-pipeline.sh`
3. New images automatically available

### Customer Updates

```bash
cd ~/rms-defragmenter
./update.sh
```

## 🏷️ Version Management

### Tagging Strategy

- `latest`: Current stable release
- `2.0.0`: Specific version tags
- `dev`: Development builds (if needed)

### Rolling Updates

- Zero-downtime updates via Docker Compose
- Automatic health checks
- Rollback capability if needed

## ⚠️ Critical Database Configuration Fix

**IMPORTANT FOR ALL DEPLOYMENTS**: The current Docker image contains database configuration that can cause stability issues. Apply this fix for reliable operation:

### Required Database Engine Configuration

Update `web_app/app/core/database.py` with these settings to prevent authentication and stability issues:

```python
# Create database engine with configuration to avoid transaction conflicts
engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,    # Recycle connections every hour
    pool_size=3,          # Conservative pool size to handle concurrent requests
    max_overflow=2,       # Allow overflow connections
    pool_timeout=30,      # Reasonable timeout for connections
    pool_pre_ping=False,  # Disable ping to avoid transaction conflicts
    echo=False,           # Disable query logging to reduce overhead
    # Remove isolation_level to use default PostgreSQL behavior
)
```

### Issues This Fixes

- ✅ **Authentication Problems**: Prevents "set_session cannot be used inside a transaction" errors
- ✅ **Move History**: Fixes 422 Unprocessable Entity errors in search functionality  
- ✅ **Session Stability**: Prevents redirects to login page
- ✅ **Database Connections**: Eliminates "connection already closed" errors

### Deployment Commands

```bash
# Copy fixed database configuration to running container
docker cp app/core/database.py defrag-app:/app/app/core/database.py

# Restart application to apply changes
docker-compose restart defrag-app
```

## 🛡️ Security Considerations

1. **Image Security**: Multi-stage builds, minimal attack surface
2. **Credentials**: Environment variables, never in images
3. **Network Isolation**: Proper Docker networking
4. **User Permissions**: Non-root containers
5. **Health Monitoring**: Built-in health checks

## 📈 Monitoring

### Health Checks

- Application: `http://localhost:8000/health`
- Database: Automatic PostgreSQL health checks
- Container: Docker health check integration

### Logs

- Application logs: `docker compose logs defrag-app`
- Database logs: `docker compose logs postgres`
- System logs: `./logs.sh`

This deployment pipeline solves the networking issues we encountered and provides a robust, customer-friendly deployment experience.

## 🧪 CLI Testing & Validation

### Testing CLI Execution

After deployment, validate the CLI analyzer functionality:

```bash
# Check CLI help
docker exec defrag-app python start.py --help

# Test CLI with specific property (uses .env credentials)
docker exec defrag-app python start.py -p CALI

# Test with training database
docker exec defrag-app python start.py -p CALI -t

# Verify output directory permissions
docker exec defrag-app ls -la /app/output/

# Check logs
docker exec defrag-app tail -f /app/logs/defrag_cron.log
```

### Common Issues & Solutions

#### Permission Errors
```bash
# Fix output directory permissions
docker exec defrag-app chown -R appuser:appuser /app/output
docker exec defrag-app chmod 755 /app/output
```

#### Missing Environment Variables
```bash
# Verify .env file is mounted
docker exec defrag-app cat /app/.env | head -10

# Check environment loading
docker exec defrag-app env | grep -E "(TARGET_|AGENT_|CLIENT_)"
```

#### Cron Job Verification
```bash
# Check cron schedule
docker exec defrag-app crontab -l

# View cron logs
docker exec defrag-app tail -f /app/logs/defrag_cron.log

# Manual cron test
docker exec defrag-app python start.py
```

### Fresh Deployment Checklist

For new machine deployments, ensure:

1. ✅ `.env` file configured with valid RMS credentials
2. ✅ `TARGET_PROPERTIES` set correctly (e.g., CALI, ALL)
3. ✅ Docker containers running and healthy
4. ✅ CLI execution successful: `docker exec defrag-app python start.py --help`
5. ✅ Output directory writable: `/app/output/` permissions correct
6. ✅ Cron job scheduled and logging properly
7. ✅ Web interface accessible on port 8000
8. ✅ Database connectivity confirmed

### Deployment Validation Script

```bash
#!/bin/bash
# Quick deployment validation
echo "🔍 Validating RMS Defragmenter deployment..."

# Check containers
docker ps | grep -E "(defrag-app|postgres)" && echo "✅ Containers running" || echo "❌ Containers not running"

# Check CLI help
docker exec defrag-app python start.py --help &>/dev/null && echo "✅ CLI accessible" || echo "❌ CLI not accessible"

# Check permissions
docker exec defrag-app test -w /app/output && echo "✅ Output directory writable" || echo "❌ Output directory not writable"

# Check web interface
curl -s http://localhost:8000/health &>/dev/null && echo "✅ Web interface responding" || echo "❌ Web interface not responding"

echo "🎉 Validation complete!"
```

This comprehensive approach ensures reliable CLI execution across all deployment scenarios.
