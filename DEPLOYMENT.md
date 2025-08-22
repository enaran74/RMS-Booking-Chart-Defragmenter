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
    -f Dockerfile.production \
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

### Standard Deployment
- **File**: `docker-compose.customer.yml`
- **Network**: Bridge networking
- **Use Case**: Most customer environments

### Host Network Deployment
- **File**: `docker-compose.hostnet.yml`
- **Network**: Host networking
- **Use Case**: Tailscale, VPN, or networking conflicts

## 🔧 Configuration

### Environment Variables

All configuration is done via `.env` file:

```bash
# RMS API Credentials (Required)
AGENT_ID=your_agent_id
AGENT_PASSWORD=your_agent_password
CLIENT_ID=your_client_id
CLIENT_PASSWORD=your_client_password

# Database Configuration
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
2. **Manual Override**: Force host networking:
   ```bash
   docker compose -f docker-compose.hostnet.yml up -d
   ```

### Common Issues

#### Tailscale Conflicts
```bash
# Symptoms: Docker build hangs, apt-get timeouts
# Solution: Automatically uses host networking
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

## 📊 Benefits of This Approach

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
- ✅ **Faster iterations**: Push image, customers update
- ✅ **Multi-architecture**: ARM64 support for modern hardware

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
