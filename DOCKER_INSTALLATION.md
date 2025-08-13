# Docker Installation Guide for RMS-Booking-Chart-Defragmenter

This guide covers deploying the RMS-Booking-Chart-Defragmenter as a Docker container across different operating systems and architectures.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Support](#architecture-support)
- [Linux Installation](#linux-installation)
- [macOS Installation](#macos-installation)
- [Windows Installation](#windows-installation)
- [Docker Deployment](#docker-deployment)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Scheduling and Automation](#scheduling-and-automation)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)
- [Platform-Specific Notes](#platform-specific-notes)

---

## Prerequisites

### System Requirements
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 10GB free space
- **Network**: Internet access for Docker image downloads and RMS API calls
- **Architecture**: x86_64 (AMD64), ARM64, or ARMv7

### Required Software
- Docker Engine 20.10+ or Docker Desktop 4.0+
- Git (for cloning the repository)
- Text editor (for configuration)

---

## Architecture Support

### Supported Architectures
| Architecture | Docker Image | Platform Support |
|--------------|--------------|------------------|
| **x86_64 (AMD64)** | `python:3.11-slim` | Linux, macOS, Windows |
| **ARM64 (AArch64)** | `python:3.11-slim` | Linux (Raspberry Pi 4), macOS (Apple Silicon) |
| **ARMv7** | `python:3.11-slim` | Linux (Raspberry Pi 3, older ARM devices) |

### Architecture Detection
```bash
# Check your system architecture
uname -m

# Expected outputs:
# x86_64    -> AMD64 architecture
# aarch64   -> ARM64 architecture  
# armv7l    -> ARMv7 architecture
```

---

## Linux Installation

### Ubuntu/Debian (x86_64, ARM64, ARMv7)

#### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Install Docker
```bash
# Download and run Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (avoid sudo for docker commands)
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Log out and back in, or restart
sudo reboot
```

#### 3. Verify Installation
```bash
docker --version
docker run hello-world
```

### CentOS/RHEL/Fedora (x86_64, ARM64)

#### 1. Install Docker
```bash
# CentOS/RHEL 8+
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
```

#### 2. Verify Installation
```bash
docker --version
docker run hello-world
```

### Raspberry Pi (ARM64, ARMv7)

#### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Install Docker
```bash
# Install Docker using the official script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add pi user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Reboot to apply group changes
sudo reboot
```

#### 3. Verify Installation
```bash
docker --version
docker run hello-world
```

---

## macOS Installation

### Intel Macs (x86_64)

#### 1. Install Docker Desktop
- Download [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- Install the `.dmg` file
- Launch Docker Desktop from Applications

#### 2. Verify Installation
```bash
docker --version
docker run hello-world
```

### Apple Silicon Macs (ARM64)

#### 1. Install Docker Desktop
- Download [Docker Desktop for Mac (Apple Silicon)](https://docs.docker.com/desktop/install/mac-install/)
- Install the `.dmg` file
- Launch Docker Desktop from Applications

#### 2. Verify Installation
```bash
docker --version
docker run hello-world
```

### Alternative: Install via Homebrew
```bash
# Install Docker via Homebrew
brew install --cask docker

# Launch Docker Desktop
open /Applications/Docker.app
```

---

## Windows Installation

### Windows 10/11 Pro/Enterprise

#### 1. Enable Features
- Enable **Hyper-V** and **Windows Subsystem for Linux (WSL)**
- Enable **Virtual Machine Platform**

#### 2. Install Docker Desktop
- Download [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- Run the installer as Administrator
- Choose **WSL 2** backend when prompted
- Restart when requested

#### 3. Verify Installation
```cmd
docker --version
docker run hello-world
```

### Windows 10/11 Home

#### 1. Install WSL 2
```cmd
# Enable WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Enable Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart computer
shutdown /r /t 0
```

#### 2. Install Docker Desktop
- Download [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- Run the installer as Administrator
- **Must use WSL 2 backend** (required for Home edition)
- Restart when requested

#### 3. Verify Installation
```cmd
docker --version
docker run hello-world
```

### Windows Server 2019/2022

#### 1. Install Docker
```powershell
# Install Docker via PowerShell
Install-Module -Name DockerMsftProvider -Repository PSGallery -Force
Install-Package -Name docker -ProviderName DockerMsftProvider -Force

# Start Docker service
Start-Service docker
Set-Service -Name docker -StartupType Automatic
```

#### 2. Verify Installation
```powershell
docker --version
docker run hello-world
```

---

## Docker Deployment

### 1. Clone Repository
```bash
# Linux/macOS
git clone https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
cd RMS-Booking-Chart-Defragmenter

# Windows Command Prompt
git clone https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
cd RMS-Booking-Chart-Defragmenter

# Windows PowerShell
git clone https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
cd RMS-Booking-Chart-Defragmenter
```

### 2. Create Configuration File
```bash
# Linux/macOS
cp env.example .env

# Windows Command Prompt
copy env.example .env

# Windows PowerShell
Copy-Item env.example .env
```

### 3. Edit Configuration
```bash
# Linux/macOS
nano .env
# or
code .env

# Windows
notepad .env
# or use any text editor
```

**Required Configuration:**
```bash
# RMS API Credentials (REQUIRED)
AGENT_ID=your_actual_agent_id
AGENT_PASSWORD=your_actual_agent_password
CLIENT_ID=your_actual_client_id
CLIENT_PASSWORD=your_actual_client_password

# Analysis Configuration
TARGET_PROPERTIES=ALL
ENABLE_EMAILS=true
SEND_CONSOLIDATED_EMAIL=true
USE_TRAINING_DB=false

# Email Configuration (if enabled)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=***REMOVED***
SENDER_DISPLAY_NAME=DHP Systems
APP_PASSWORD=your_gmail_app_password
TEST_RECIPIENT=***REMOVED***

# Logging Configuration
LOG_LEVEL=INFO
```

### 4. Build and Run
```bash
# Build the Docker image
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT_ID` | ✅ | - | RMS API Agent ID |
| `AGENT_PASSWORD` | ✅ | - | RMS API Agent Password |
| `CLIENT_ID` | ✅ | - | RMS API Client ID |
| `CLIENT_PASSWORD` | ✅ | - | RMS API Client Password |
| `TARGET_PROPERTIES` | ❌ | `ALL` | Properties to analyze (comma-separated) |
| `ENABLE_EMAILS` | ❌ | `false` | Enable email notifications |
| `SEND_CONSOLIDATED_EMAIL` | ❌ | `false` | Send consolidated report to operations team |
| `USE_TRAINING_DB` | ❌ | `false` | Use training database |
| `SMTP_SERVER` | ❌ | `smtp.gmail.com` | SMTP server for emails |
| `SMTP_PORT` | ❌ | `587` | SMTP port |
| `SENDER_EMAIL` | ❌ | `***REMOVED***` | Email sender address |
| `SENDER_DISPLAY_NAME` | ❌ | `DHP Systems` | Email sender display name |
| `APP_PASSWORD` | ❌ | - | Gmail app password |
| `TEST_RECIPIENT` | ❌ | `***REMOVED***` | Test email recipient |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Volume Mounts

The Docker setup automatically mounts:
- `./logs` → `/var/log/bookingchart-defragmenter` (application logs)
- `./output` → `/app/output` (Excel reports and analysis files)
- `./config` → `/app/config` (configuration files, read-only)

---

## Running the Application

### Manual Execution
```bash
# Run with default configuration
docker-compose exec bookingchart-defragmenter python3 start.py

# Run with specific properties
docker-compose exec bookingchart-defragmenter python3 start.py -p SADE,QROC

# Run with custom arguments
docker-compose exec bookingchart-defragmenter python3 start.py --help

# Run with email enabled
docker-compose exec bookingchart-defragmenter python3 start.py -e
```

### Check Application Status
```bash
# View running containers
docker-compose ps

# Check container health
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"

# View application logs
docker-compose logs -f bookingchart-defragmenter

# View recent logs
docker-compose logs --tail=100 bookingchart-defragmenter
```

---

## Scheduling and Automation

### Option 1: Container Cron (Recommended)
The Docker container includes a cron service that runs daily at 2:00 AM.

```bash
# Check cron status
docker-compose exec bookingchart-defragmenter crontab -l

# View cron logs
docker-compose exec bookingchart-defragmenter tail -f /var/log/cron.log
```

### Option 2: Host System Scheduler

#### Linux (cron)
```bash
# Add to crontab
crontab -e

# Daily at 2:00 AM
0 2 * * * cd /path/to/RMS-Booking-Chart-Defragmenter && docker-compose exec -T bookingchart-defragmenter python3 start.py --agent-id $AGENT_ID --agent-password $AGENT_PASSWORD --client-id $CLIENT_ID --client-password $AGENT_PASSWORD -p ALL
```

#### macOS (launchd)
```bash
# Create plist file
sudo nano /Library/LaunchDaemons/com.defragmenter.analysis.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.defragmenter.analysis</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/docker-compose</string>
        <string>-f</string>
        <string>/path/to/RMS-Booking-Chart-Defragmenter/docker-compose.yml</string>
        <string>exec</string>
        <string>-T</string>
        <string>bookingchart-defragmenter</string>
        <string>python3</string>
        <string>start.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

#### Windows (Task Scheduler)
1. Open **Task Scheduler**
2. Create **Basic Task**
3. Set trigger to **Daily at 2:00 AM**
4. Set action to **Start a program**
5. Program: `docker-compose`
6. Arguments: `-f C:\path\to\RMS-Booking-Chart-Defragmenter\docker-compose.yml exec -T bookingchart-defragmenter python3 start.py --agent-id %AGENT_ID% --agent-password %AGENT_PASSWORD% --client-id %CLIENT_ID% --client-password %AGENT_PASSWORD% -p ALL`

---

## Monitoring and Maintenance

### Health Checks
```bash
# Check container health
docker-compose ps

# Manual health check
docker-compose exec bookingchart-defragmenter python3 -c "import os; exit(0 if os.path.exists('/var/log/bookingchart-defragmenter/defrag_analyzer.log') else 1)"
```

### Log Management
```bash
# View application logs
docker-compose logs -f bookingchart-defragmenter

# View system logs
docker-compose exec bookingchart-defragmenter tail -f /var/log/syslog

# Check log file sizes
docker-compose exec bookingchart-defragmenter du -sh /var/log/bookingchart-defragmenter/*
```

### Resource Monitoring
```bash
# Check container resource usage
docker stats bookingchart-defragmenter

# Check disk usage
docker-compose exec bookingchart-defragmenter df -h

# Check memory usage
docker-compose exec bookingchart-defragmenter free -h
```

### Updates and Maintenance
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d

# Clean up old images
docker system prune -f

# Update Docker images
docker-compose pull
```

---

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs bookingchart-defragmenter

# Check container status
docker-compose ps -a

# Restart container
docker-compose restart bookingchart-defragmenter
```

#### Permission Issues
```bash
# Check file permissions
ls -la logs/ output/

# Fix permissions (Linux/macOS)
chmod -R 755 logs/ output/
chown -R $USER:$USER logs/ output/

# Windows: Run as Administrator or check folder permissions
```

#### Network Issues
```bash
# Check network connectivity
docker-compose exec bookingchart-defragmenter ping google.com

# Check DNS resolution
docker-compose exec bookingchart-defragmenter nslookup smtp.gmail.com

# Restart Docker service
sudo systemctl restart docker  # Linux
# Restart Docker Desktop on macOS/Windows
```

#### Memory Issues
```bash
# Check available memory
docker-compose exec bookingchart-defragmenter free -h

# Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G  # Increase from 2G
```

### Debug Commands
```bash
# Access container shell
docker-compose exec bookingchart-defragmenter bash

# Check environment variables
docker-compose exec bookingchart-defragmenter env

# Check file system
docker-compose exec bookingchart-defragmenter ls -la /app/

# Check Python environment
docker-compose exec bookingchart-defragmenter python3 --version
docker-compose exec bookingchart-defragmenter pip list
```

---

## Platform-Specific Notes

### Linux
- **Service Management**: Use `systemctl` for Docker service
- **Permissions**: Ensure user is in `docker` group
- **Firewall**: Configure `ufw` or `iptables` if needed
- **Log Rotation**: Use `logrotate` for log management

### macOS
- **Docker Desktop**: Must be running for containers to work
- **Resource Limits**: Adjust memory/CPU in Docker Desktop preferences
- **File Sharing**: Ensure project directory is accessible to Docker
- **Performance**: Use native ARM64 images on Apple Silicon

### Windows
- **WSL 2**: Required for Docker Desktop on Windows 10/11 Home
- **Antivirus**: May interfere with Docker - add exclusions
- **File Paths**: Use forward slashes or escaped backslashes in docker-compose.yml
- **Administrator**: Some operations require Administrator privileges

### ARM Architectures (Raspberry Pi, Apple Silicon)
- **Image Compatibility**: All images are multi-arch compatible
- **Performance**: May be slower than x86_64 equivalents
- **Memory**: Ensure sufficient RAM (2GB+ recommended)
- **Storage**: Use fast storage (SSD recommended for logs/output)

---

## Security Considerations

### Container Security
- **Non-root User**: Container runs as `defrag` user, not root
- **Read-only Mounts**: Configuration mounted as read-only
- **Resource Limits**: Memory and CPU limits prevent resource exhaustion
- **Network Isolation**: Container uses isolated network

### Data Security
- **Environment Variables**: Sensitive data stored in `.env` file
- **Volume Mounts**: Data persists on host system
- **Log Rotation**: Automatic log rotation prevents disk filling
- **Backup**: Ensure `output/` and `logs/` directories are backed up

---

## Support and Resources

### Documentation
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Project README](../README.md)
- [Developer Guide](../DEVELOPER_README.md)

### Community Support
- [GitHub Issues](https://github.com/enaran74/RMS-Booking-Chart-Defragmenter/issues)
- [Docker Community Forums](https://forums.docker.com/)

### Getting Help
1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs bookingchart-defragmenter`
3. Check system resources and Docker status
4. Create a GitHub issue with logs and error details

---

## Quick Start Checklist

- [ ] Install Docker on your platform
- [ ] Clone the repository
- [ ] Copy and configure `.env` file
- [ ] Build and start containers: `docker-compose up --build -d`
- [ ] Verify container is running: `docker-compose ps`
- [ ] Test manual execution
- [ ] Configure scheduling (optional)
- [ ] Set up monitoring and alerts (optional)

---

*This guide covers Docker deployment across all supported platforms. For platform-specific issues, refer to the troubleshooting section or create a GitHub issue.*
