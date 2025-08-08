# Scripts Reference Guide

This document provides detailed information about all the management and utility scripts in the BookingChartDefragmenter project.

## Installation Scripts

### `install.sh` - Automated Installation Script

The main installation script for setting up the application on Linux servers.

#### Features:
- ✅ **System Dependencies** - Installs Python, pip, git, cron, systemd
- ✅ **Service User Creation** - Creates `defrag` user and group
- ✅ **Python Environment** - Sets up virtual environment with dependencies
- ✅ **Systemd Service** - Configures and enables systemd service
- ✅ **Cron Job Setup** - Configures daily execution at 2:00 AM
- ✅ **Log Configuration** - Sets up logrotate and log directories
- ✅ **File Permissions** - Sets proper ownership and permissions
- ✅ **Configuration Template** - Creates config.env template
- ✅ **Health Check Script** - Installs health monitoring
- ✅ **Uninstall Script** - Creates uninstall.sh for cleanup

#### Usage:
```bash
# Make executable and run
sudo chmod +x install.sh
sudo ./install.sh
```

#### What It Installs:
```
/opt/bookingchart-defragmenter/          # Application directory
/etc/bookingchart-defragmenter/config.env # Configuration file
/etc/systemd/system/bookingchart-defragmenter.service # Systemd service
/var/log/bookingchart-defragmenter/      # Log directory
/etc/logrotate.d/bookingchart-defragmenter # Log rotation
```

#### Post-Installation Steps:
1. **Configure credentials**:
   ```bash
   sudo nano /etc/bookingchart-defragmenter/config.env
   ```

2. **Start the service**:
   ```bash
   sudo systemctl start bookingchart-defragmenter.service
   sudo systemctl enable bookingchart-defragmenter.service
   ```

3. **Verify installation**:
   ```bash
   sudo /opt/bookingchart-defragmenter/health_check.sh
   ```

### `uninstall.sh` - Cleanup Script

Removes the application and all associated files.

#### Usage:
```bash
sudo /opt/bookingchart-defragmenter/uninstall.sh
```

#### What It Removes:
- ✅ Stops and disables systemd service
- ✅ Removes service file and logrotate config
- ✅ Removes cron jobs
- ✅ Deletes application directory
- ✅ Removes log and config directories
- ✅ Removes service user and group
- ✅ Reloads systemd daemon

## Management Scripts

### `manage.sh` - Main Management Script

The primary script for managing the service and executing analysis.

#### Usage:
```bash
sudo /opt/bookingchart-defragmenter/manage.sh [command]
```

#### Commands:

| Command | Description |
|---------|-------------|
| `start` | Start the service (environment setup only) |
| `stop` | Stop the service |
| `restart` | Restart the service |
| `status` | Check service status |
| `logs` | View live logs |
| `run` | Run analysis manually (runs once and exits) |
| `health` | Run health check |
| `update` | Update from GitHub |

#### Examples:
```bash
# Start the service
sudo /opt/bookingchart-defragmenter/manage.sh start

# Run analysis manually
sudo /opt/bookingchart-defragmenter/manage.sh run

# Check service status
sudo /opt/bookingchart-defragmenter/manage.sh status

# Update from GitHub
sudo /opt/bookingchart-defragmenter/manage.sh update
```

### `update.sh` - Automated Update Script

Handles the complete update process with backup and rollback capabilities.

#### Features:
- ✅ **Automatic Backup** - Creates backup before update
- ✅ **Git Pull** - Downloads latest code from GitHub (public repository)
- ✅ **Dependency Update** - Updates Python packages
- ✅ **Service Restart** - Restarts service with new version
- ✅ **Auto-Rollback** - Reverts if update fails
- ✅ **Health Verification** - Ensures service starts properly
- ✅ **No Authentication Required** - Works with public repository

#### Usage:
```bash
sudo /opt/bookingchart-defragmenter/update.sh [branch]
```

#### Examples:
```bash
# Update from main branch
sudo /opt/bookingchart-defragmenter/update.sh

# Update from specific branch
sudo /opt/bookingchart-defragmenter/update.sh develop
```

## Utility Scripts

### `health_check.sh` - Health Monitoring

Comprehensive health check for the service and environment.

#### Checks Performed:
1. **Service Status** - Is the service running?
2. **Service Enablement** - Is the service enabled?
3. **Installation Directory** - Does the installation directory exist?
4. **Python Environment** - Is the virtual environment working?
5. **Script Files** - Are all required scripts present?
6. **Configuration** - Is the config file accessible?
7. **Log Directory** - Are logs being written?
8. **Python Dependencies** - Can all modules be imported?

#### Usage:
```bash
sudo /opt/bookingchart-defragmenter/health_check.sh
```

#### Output:
```
🔍 Health Check for BookingChartDefragmenter
==================================================

ℹ️  1. Checking service status...
✅ Service is running
ℹ️  2. Checking if service is enabled...
✅ Service is enabled
...
✅ Health check completed successfully!
```

### `debug_service.sh` - Service Diagnostics

Advanced diagnostics for troubleshooting service issues.

#### Diagnostics Performed:
1. **Service File** - Checks systemd service configuration
2. **Service Status** - Detailed service status information
3. **Service Enablement** - Checks if service is enabled
4. **Installation Directory** - Verifies file structure
5. **Wrapper Script** - Checks service wrapper script
6. **Configuration** - Validates configuration file
7. **User Permissions** - Checks service user setup
8. **Logs** - Shows recent service logs
9. **Manual Execution** - Tests script execution
10. **Python Environment** - Validates Python setup

#### Usage:
```bash
sudo /opt/bookingchart-defragmenter/debug_service.sh
```

### `setup_ssh.sh` - SSH Authentication Setup (Legacy)

**Note:** This script is no longer required for public repository deployments.

Guides you through setting up SSH authentication for GitHub access (only needed for private repositories).

#### Features:
- 🔑 **SSH Key Generation** - Creates new SSH keys if needed
- 🔗 **GitHub Integration** - Instructions for adding keys to GitHub
- 🧪 **Connection Testing** - Tests SSH connection to GitHub
- 📋 **Step-by-Step Guide** - Interactive setup process

#### Usage:
```bash
sudo /opt/bookingchart-defragmenter/setup_ssh.sh
```

### `setup_cron.sh` - Cron Job Setup

Sets up automated daily execution via cron.

#### Features:
- ⏰ **Daily Schedule** - Runs at 2:00 AM daily
- 📝 **Logging** - Logs output to `/var/log/bookingchart-defragmenter/cron.log`
- 🔄 **Clean Setup** - Removes old cron jobs before adding new ones
- ✅ **Verification** - Confirms cron job was added successfully

#### Usage:
```bash
sudo /opt/bookingchart-defragmenter/setup_cron.sh
```

#### Cron Job Format:
```bash
0 2 * * * /opt/bookingchart-defragmenter/run_defragmentation.sh >> /var/log/bookingchart-defragmenter/cron.log 2>&1
```

## Service Scripts

### `service_wrapper.sh` - Service Environment Wrapper

The main service script that sets up the environment and stays running.

#### Features:
- 🔧 **Environment Setup** - Loads configuration and verifies dependencies
- 🛡️ **Credential Verification** - Checks RMS API credentials
- 📊 **Python Import Test** - Validates all Python modules
- 🔄 **Continuous Running** - Stays active for systemd management
- 📝 **Logging** - Comprehensive logging of service activities

#### Behavior:
- ✅ **Fast Startup** (~30 seconds)
- ✅ **Environment Ready** - Sets up everything needed for analysis
- ❌ **No Analysis** - Does NOT run the actual defragmentation
- 🔄 **Stays Active** - Runs continuously for systemd management

### `run_defragmentation.sh` - Analysis Execution Script

Executes the actual defragmentation analysis.

#### Features:
- 🔐 **Secure Configuration Loading** - Handles app passwords with spaces
- 🌍 **Environment Variable Passing** - Passes credentials to Python process
- 📊 **Comprehensive Logging** - Logs all analysis activities
- 📁 **Output Management** - Creates and manages output files
- ⚡ **Error Handling** - Proper error reporting and exit codes

#### Usage:
```bash
sudo /opt/bookingchart-defragmenter/run_defragmentation.sh
```

#### Execution Flow:
1. **Configuration Loading** - Safely loads config file
2. **Environment Verification** - Checks all required variables
3. **Analysis Execution** - Runs Python analysis as `defrag` user
4. **Output Verification** - Checks for generated files
5. **Logging** - Records all activities

## File Locations

### Script Locations:
```
/opt/bookingchart-defragmenter/
├── manage.sh              # Main management script
├── update.sh              # Update script
├── health_check.sh        # Health monitoring
├── debug_service.sh       # Service diagnostics
├── setup_ssh.sh          # SSH authentication setup (legacy)
├── setup_cron.sh         # Cron job setup
├── service_wrapper.sh    # Service environment wrapper
└── run_defragmentation.sh # Analysis execution
```

### Configuration Files:
```
/etc/bookingchart-defragmenter/
└── config.env            # Main configuration file

/var/log/bookingchart-defragmenter/
├── defrag_analyzer.log   # Application logs
├── analysis.log          # Analysis execution logs
└── cron.log             # Cron job logs
```

### Output Files:
```
/opt/bookingchart-defragmenter/output/
├── QROC-Defragmentation-Analysis.xlsx
├── SADE-Defragmentation-Analysis.xlsx
└── Full_Defragmentation_Analysis.xlsx
```

## Troubleshooting

### Common Issues:

1. **Permission Denied**:
   ```bash
   sudo chown -R defrag:defrag /opt/bookingchart-defragmenter/
   sudo chmod +x /opt/bookingchart-defragmenter/*.sh
   ```

2. **Service Won't Start**:
   ```bash
   sudo /opt/bookingchart-defragmenter/debug_service.sh
   sudo journalctl -u bookingchart-defragmenter.service -f
   ```

3. **Cron Job Not Running**:
   ```bash
   sudo crontab -u defrag -l
   sudo /opt/bookingchart-defragmenter/setup_cron.sh
   ```

4. **Network Connectivity Issues**:
   ```bash
   ping github.com
   curl -I https://github.com
   ```

### Getting Help:

1. **Run Health Check**:
   ```bash
   sudo /opt/bookingchart-defragmenter/health_check.sh
   ```

2. **Run Diagnostics**:
   ```bash
   sudo /opt/bookingchart-defragmenter/debug_service.sh
   ```

3. **Check Logs**:
   ```bash
   sudo /opt/bookingchart-defragmenter/manage.sh logs
   ```

4. **View Service Status**:
   ```bash
   sudo /opt/bookingchart-defragmenter/manage.sh status
   ```
