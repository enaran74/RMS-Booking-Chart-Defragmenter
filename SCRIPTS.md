# Scripts Reference Guide

This document provides detailed information about all the management and utility scripts in the RMS Booking Chart Defragmenter project.

## Customer Management Scripts

### Installation Scripts

#### `install-customer.sh` - Smart Customer Installation

The main installation script for customer deployments using pre-built Docker images.

**Features:**
- ✅ **Environment Detection** - Automatically detects Tailscale, VPN, and networking issues
- ✅ **Smart Deployment** - Chooses appropriate docker-compose configuration
- ✅ **Pre-Built Images** - Downloads production-ready images from Docker Hub
- ✅ **Management Scripts** - Creates convenient management scripts
- ✅ **Fast Setup** - 5-10 minute deployment vs 30-60 minutes

**Usage:**
```bash
# One-command installation
curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install-customer.sh | bash
```

**What It Does:**
1. **Checks Prerequisites** - Docker and Docker Compose
2. **Detects Environment Issues** - Tailscale, VPN, networking conflicts
3. **Downloads Configuration** - Appropriate docker-compose file
4. **Pulls Images** - Pre-built production images
5. **Creates Management Scripts** - start.sh, stop.sh, status.sh, logs.sh, update.sh
6. **Sets Up Environment** - .env configuration template

### Management Scripts

These scripts are automatically created in `~/rms-defragmenter/` after installation:

#### `start.sh` - Start System
```bash
#!/bin/bash
echo "🚀 Starting RMS Defragmenter..."
docker compose up -d
echo "✅ System started!"
echo "🌐 Web Interface: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"
```

#### `stop.sh` - Stop System
```bash
#!/bin/bash
echo "🛑 Stopping RMS Defragmenter..."
docker compose down
echo "✅ System stopped!"
```

#### `status.sh` - Check Status
```bash
#!/bin/bash
echo "📊 RMS Defragmenter Status:"
echo ""
docker compose ps
echo ""
echo "📋 Container Health:"
docker compose exec defrag-app ./health_check.sh 2>/dev/null || echo "❌ Health check failed"
```

#### `logs.sh` - View Logs
```bash
#!/bin/bash
echo "📋 Showing logs (Ctrl+C to exit)..."
docker compose logs -f
```

#### `update.sh` - Update System
```bash
#!/bin/bash
echo "🔄 Updating RMS Defragmenter..."
docker compose pull
docker compose up -d
echo "✅ Update completed!"
```

### Usage Examples

```bash
# Navigate to installation directory
cd ~/rms-defragmenter

# Start the system
./start.sh

# Check system status
./status.sh

# View live logs
./logs.sh

# Update to latest version
./update.sh

# Stop the system
./stop.sh
```

## Developer Build Scripts

### Production Build Pipeline

#### `build-pipeline.sh` - Multi-Architecture Build

Builds and pushes production-ready Docker images for multiple architectures.

**Features:**
- ✅ **Multi-Architecture** - Builds for AMD64, ARM64
- ✅ **Docker Hub Push** - Pushes to dhpsystems/rms-defragmenter
- ✅ **Version Tagging** - Creates versioned and latest tags
- ✅ **BuildKit Support** - Uses Docker BuildKit for efficiency

**Usage:**
```bash
# Build and push production images
./build-pipeline.sh
```

**Prerequisites:**
- Docker Desktop with BuildKit
- Docker Hub account and login
- Multi-architecture builder setup

#### `Dockerfile.production` - Production Image

Optimized multi-stage Dockerfile for production deployments.

**Features:**
- ✅ **Multi-Stage Build** - Separate build and runtime stages
- ✅ **Minimal Size** - Only runtime dependencies in final image
- ✅ **Security** - Non-root user, minimal attack surface
- ✅ **Multi-Architecture** - Supports AMD64, ARM64, ARMv7

## Docker Compose Configurations

### `docker-compose.customer.yml` - Standard Deployment

Default customer deployment using bridge networking.

**Use Cases:**
- Most customer environments
- Standard networking setup
- No VPN or Tailscale conflicts

### `docker-compose.hostnet.yml` - Host Network Deployment

Alternative deployment using host networking for problematic environments.

**Use Cases:**
- Tailscale installations
- VPN conflicts
- Complex networking environments
- Docker networking issues

### Configuration Comparison

| Feature | Standard (customer.yml) | Host Network (hostnet.yml) |
|---------|------------------------|----------------------------|
| **Networking** | Bridge | Host |
| **Port Mapping** | 8000:8000 | Direct |
| **Isolation** | High | Medium |
| **Compatibility** | Most environments | Networking conflicts |
| **Security** | Better isolation | Less isolation |
| **Troubleshooting** | Easier | More complex |

## Utility Scripts

### Docker Container Scripts

These scripts run inside the Docker container:

#### `health_check.sh` - Container Health Check
- Checks web application responsiveness
- Validates database connectivity
- Verifies file system access
- Used by Docker health checks

#### `entrypoint.sh` - Container Startup
- Initializes the container environment
- Starts web application
- Sets up logging
- Configures cron jobs (if enabled)

## Configuration Management

### Environment Files

#### `.env` - Production Configuration
Main configuration file for customer deployments:

```bash
# RMS API Credentials (Required)
AGENT_ID=your_agent_id
AGENT_PASSWORD=your_agent_password
CLIENT_ID=your_client_id
CLIENT_PASSWORD=your_client_password

# Application Configuration
USE_TRAINING_DB=false
WEB_APP_PORT=8000

# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=defrag_db
DB_USER=defrag_user
DB_PASSWORD=DefragDB2024!

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
```

#### `env.example` - Configuration Template
Template for creating production `.env` files with all available options.

## Deployment Strategies

### Customer Deployment Workflow

1. **Installation**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install-customer.sh | bash
   ```

2. **Configuration**
   ```bash
   cd ~/rms-defragmenter
   nano .env  # Configure RMS credentials
   ```

3. **Start System**
   ```bash
   ./start.sh
   ```

4. **Verify Deployment**
   ```bash
   ./status.sh
   curl http://localhost:8000/health
   ```

### Developer Deployment Workflow

1. **Build Images**
   ```bash
   ./build-pipeline.sh
   ```

2. **Test Locally**
   ```bash
   docker run --rm -p 8000:8000 dhpsystems/rms-defragmenter:latest
   ```

3. **Customer Testing**
   ```bash
   # Test customer installation
   ./install-customer.sh
   ```

## Troubleshooting Scripts

### Common Diagnostic Commands

#### Check Docker Status
```bash
# Check if Docker is running
docker info

# Check container status
docker compose ps

# Check container health
docker compose exec defrag-app ./health_check.sh
```

#### Network Diagnostics
```bash
# Test external connectivity
docker compose exec defrag-app ping google.com

# Test internal connectivity
docker compose exec defrag-app ping postgres

# Check DNS resolution
docker compose exec defrag-app nslookup github.com
```

#### Application Diagnostics
```bash
# Check web application
curl http://localhost:8000/health

# Check API endpoints
curl http://localhost:8000/docs

# Check logs
docker compose logs defrag-app

# Access container shell
docker compose exec defrag-app bash
```

### Recovery Procedures

#### Complete System Reset
```bash
# Stop all containers
./stop.sh

# Remove all data (WARNING: Deletes everything!)
docker compose down -v
docker volume prune -f

# Restart fresh
./start.sh
```

#### Update Recovery
```bash
# If update fails, restart with old images
docker compose down
docker compose up -d

# Check system status
./status.sh
```

## File Locations

### Customer Installation Structure
```
~/rms-defragmenter/
├── docker-compose.yml     # Active docker-compose configuration
├── .env                   # Production configuration
├── start.sh              # Start system
├── stop.sh               # Stop system
├── status.sh             # Check status
├── logs.sh               # View logs
└── update.sh             # Update system
```

### Docker Volume Mounts
```
postgres_data:/var/lib/postgresql/data    # Database files
defrag_logs:/app/logs                     # Application logs
defrag_output:/app/output                 # Excel reports
```

## Integration Examples

### Automation Scripts

#### Automated Backup
```bash
#!/bin/bash
# backup.sh - Backup important data
cd ~/rms-defragmenter

# Backup database
docker compose exec postgres pg_dump -U defrag_user defrag_db > backup_$(date +%Y%m%d).sql

# Backup output files
docker cp defrag-app:/app/output ./backup_output_$(date +%Y%m%d)

echo "Backup completed"
```

#### Health Monitoring
```bash
#!/bin/bash
# monitor.sh - Check system health
cd ~/rms-defragmenter

if curl -sf http://localhost:8000/health > /dev/null; then
    echo "✅ System healthy"
else
    echo "❌ System unhealthy - attempting restart"
    ./stop.sh
    sleep 10
    ./start.sh
fi
```

#### Automated Updates
```bash
#!/bin/bash
# auto-update.sh - Check for and apply updates
cd ~/rms-defragmenter

echo "🔄 Checking for updates..."
docker compose pull

if docker images --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | grep dhpsystems/rms-defragmenter:latest | grep "$(date +%Y-%m-%d)"; then
    echo "📦 New image available - updating..."
    ./update.sh
    echo "✅ Update completed"
else
    echo "✅ Already up to date"
fi
```

## Best Practices

### Script Management
1. **Make scripts executable**: `chmod +x *.sh`
2. **Use absolute paths** when running from cron
3. **Add error handling** for production scripts
4. **Log script execution** for troubleshooting

### Docker Best Practices
1. **Use specific image tags** for production
2. **Monitor resource usage** with `docker stats`
3. **Regular cleanup** with `docker system prune`
4. **Backup volumes** before major updates

### Security Considerations
1. **Protect .env files** - never commit to git
2. **Use non-root containers** (already implemented)
3. **Regular security updates** via `./update.sh`
4. **Monitor logs** for suspicious activity

This comprehensive script reference ensures smooth operation and maintenance of the RMS Booking Chart Defragmenter system across all deployment scenarios.