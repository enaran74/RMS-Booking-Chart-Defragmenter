# Deployment Guide - Raspberry Pi & Production Servers

This guide explains how to deploy updates from your development environment (Mac) to your production Raspberry Pi.

## Development → Production Workflow

```
📱 Mac (Development) → 🌐 GitHub → 🥧 Raspberry Pi (Production)
```

## Quick Update Process

### On Raspberry Pi (Production Server):

1. **Simple Update** (recommended):
   ```bash
   sudo /opt/bookingchart-defragmenter/manage.sh update
   ```

2. **Update from specific branch**:
   ```bash
   sudo /opt/bookingchart-defragmenter/manage.sh update develop
   ```

## Service Management

### Basic Commands:
```bash
# Start the service
sudo /opt/bookingchart-defragmenter/manage.sh start

# Stop the service
sudo /opt/bookingchart-defragmenter/manage.sh stop

# Restart the service
sudo /opt/bookingchart-defragmenter/manage.sh restart

# Check status
sudo /opt/bookingchart-defragmenter/manage.sh status

# View logs (live)
sudo /opt/bookingchart-defragmenter/manage.sh logs

# Health check
sudo /opt/bookingchart-defragmenter/manage.sh health
```

## Update Process Details

The update script (`update.sh`) performs these steps automatically:

1. 🔍 **Backup Current Version** - Creates backup before any changes
2. 📥 **Download Latest Code** - Pulls from GitHub repository  
3. 🛑 **Stop Service** - Safely stops the running service
4. 📋 **Preserve Config** - Keeps your credentials and settings
5. 🔄 **Update Files** - Replaces application code
6. 📦 **Update Dependencies** - Installs any new Python packages
7. ✅ **Health Check** - Verifies the update worked
8. 🚀 **Start Service** - Restarts with new version
9. 🔄 **Auto-Rollback** - Reverts to backup if anything fails

## Safety Features

- ✅ **Automatic Backup** - Previous version saved before update
- ✅ **Configuration Preservation** - Your credentials stay safe
- ✅ **Auto-Rollback** - Reverts if update fails
- ✅ **Health Verification** - Ensures service starts properly
- ✅ **Zero-Downtime Goal** - Minimizes service interruption

## Development Workflow

### On Your Mac:
1. Make code changes
2. Test locally
3. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

### On Raspberry Pi:
1. Update with one command:
   ```bash
   sudo /opt/bookingchart-defragmenter/manage.sh update
   ```

## Branch Strategy

- **`main`** - Production-ready code (default for updates)
- **`develop`** - Development/testing code
- **Feature branches** - For experimental features

### Update from different branches:
```bash
# Production updates (stable)
sudo /opt/bookingchart-defragmenter/manage.sh update main

# Test new features
sudo /opt/bookingchart-defragmenter/manage.sh update develop
```

## Troubleshooting

### If Update Fails:
The script automatically rolls back, but you can check:

```bash
# Check service status
sudo /opt/bookingchart-defragmenter/manage.sh status

# View recent logs
sudo /opt/bookingchart-defragmenter/manage.sh logs

# Manual rollback (if needed)
sudo systemctl stop bookingchart-defragmenter.service
sudo mv /opt/bookingchart-defragmenter-backup /opt/bookingchart-defragmenter
sudo systemctl start bookingchart-defragmenter.service
```

### Common Issues:

1. **Permission Errors**: Ensure you run update commands with `sudo`
2. **Network Issues**: Check internet connection for GitHub access
3. **Service Won't Start**: Check logs and configuration files
4. **Dependencies Failed**: May need to install system packages

### View Logs:
```bash
# Live logs
sudo /opt/bookingchart-defragmenter/manage.sh logs

# Historical logs
sudo journalctl -u bookingchart-defragmenter.service -n 100

# Application logs
sudo tail -f /var/log/bookingchart-defragmenter/defrag_analyzer.log
```

## File Locations

- **Application**: `/opt/bookingchart-defragmenter/`
- **Configuration**: `/etc/bookingchart-defragmenter/config.env`
- **Logs**: `/var/log/bookingchart-defragmenter/`
- **Service**: `/etc/systemd/system/bookingchart-defragmenter.service`
- **Backups**: `/opt/bookingchart-defragmenter-backup/` (temporary)

## Security Notes

- 🔒 **Credentials Never Change** - Update preserves all API credentials
- 🔒 **Service User** - Runs as non-root `defrag` user
- 🔒 **File Permissions** - Maintained during updates
- 🔒 **Configuration Files** - Protected and preserved

## Advanced Usage

### Manual Git Update (if needed):
```bash
cd /opt/bookingchart-defragmenter
sudo git pull origin main
sudo systemctl restart bookingchart-defragmenter.service
```

### Check Current Version:
```bash
cd /opt/bookingchart-defragmenter
git log --oneline -1
```

### Configuration Changes:
```bash
sudo nano /etc/bookingchart-defragmenter/config.env
sudo /opt/bookingchart-defragmenter/manage.sh restart
```

This deployment system gives you:
- 🚀 **One-command updates**
- 🛡️ **Safe rollback capability** 
- 📊 **Easy monitoring**
- 🔧 **Simple maintenance**
