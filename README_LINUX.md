# BookingChartDefragmenter for Debian 12 Linux Server

## Overview

The BookingChartDefragmenter is a comprehensive RMS API-based defragmentation analysis tool designed to optimize booking charts across multiple properties. This version is specifically optimized for deployment on Debian 12 Linux servers.

## Features

- **Multi-Property Analysis**: Analyze all properties or specific property codes
- **Real-time RMS API Integration**: Live data retrieval with comprehensive caching
- **Excel Report Generation**: Visual charts and detailed move suggestions
- **Email Notifications**: Automated email delivery with Excel attachments
- **Training Database Support**: Safe testing with training database
- **Linux Server Optimized**: Systemd service, logrotate, and proper permissions
- **Docker Support**: Containerized deployment option
- **Environment Variable Configuration**: Secure credential management

## System Requirements

- **OS**: Debian 12 (Bookworm) or compatible Linux distribution
- **Python**: 3.11 or higher
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: 10GB free space for logs and output files
- **Network**: Internet access for RMS API and email (SMTP)

## Installation Options

### Option 1: Direct Installation (Recommended)

1. **Clone or download the application**:
   ```bash
   git clone <repository-url>
   cd BookingChartDefragmenter
   ```

2. **Run the installation script**:
   ```bash
   sudo chmod +x install.sh
   sudo ./install.sh
   ```

3. **Configure the application**:
   ```bash
   sudo nano /etc/bookingchart-defragmenter/config.env
   ```

4. **Start the service**:
   ```bash
   sudo systemctl start bookingchart-defragmenter.service
   sudo systemctl enable bookingchart-defragmenter.service
   ```

### Option 2: Docker Deployment

1. **Prepare environment file**:
   ```bash
   cp env.example .env
   nano .env  # Edit with your credentials
   ```

2. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Check container status**:
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

## Configuration

### Environment Variables

The application supports configuration via environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT_ID` | Yes | - | RMS Agent ID |
| `AGENT_PASSWORD` | Yes | - | RMS Agent Password |
| `CLIENT_ID` | Yes | - | RMS Client ID |
| `CLIENT_PASSWORD` | Yes | - | RMS Client Password |
| `TARGET_PROPERTIES` | No | ALL | Property codes (comma-separated) or ALL |
| `ENABLE_EMAILS` | No | false | Enable email notifications |
| `USE_TRAINING_DB` | No | false | Use training database |
| `SMTP_SERVER` | No | smtp.gmail.com | SMTP server for emails |
| `SMTP_PORT` | No | 587 | SMTP port |
| `SENDER_EMAIL` | No | ***REMOVED*** | Sender email address |
| `APP_PASSWORD` | No | - | Gmail app password |
| `LOG_LEVEL` | No | INFO | Logging level |

### Configuration File

For direct installation, edit `/etc/bookingchart-defragmenter/config.env`:

```bash
# RMS API Credentials
AGENT_ID=your_agent_id_here
AGENT_PASSWORD=your_agent_password_here
CLIENT_ID=your_client_id_here
CLIENT_PASSWORD=your_client_password_here

# Analysis Configuration
TARGET_PROPERTIES=ALL
ENABLE_EMAILS=false
USE_TRAINING_DB=false

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=***REMOVED***
APP_PASSWORD=your_app_password_here
```

## Usage

### Manual Execution

```bash
# Using wrapper script
sudo /opt/bookingchart-defragmenter/run_defragmentation.sh

# Direct execution with arguments
python3 start.py --agent-id ***REMOVED*** --agent-password "password" --client-id ***REMOVED*** --client-password "password" -p ALL

# Using environment variables
export AGENT_ID=***REMOVED***
export AGENT_PASSWORD="password"
export CLIENT_ID=***REMOVED***
export CLIENT_PASSWORD="password"
export TARGET_PROPERTIES=ALL
python3 start.py
```

### Service Management

```bash
# Start the service
sudo systemctl start bookingchart-defragmenter.service

# Stop the service
sudo systemctl stop bookingchart-defragmenter.service

# Restart the service
sudo systemctl restart bookingchart-defragmenter.service

# Check status
sudo systemctl status bookingchart-defragmenter.service

# View logs
sudo journalctl -u bookingchart-defragmenter.service -f
```

### Docker Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update and rebuild
docker-compose up -d --build
```

## Automated Execution

### Cron Job (Direct Installation)

The installation script automatically configures a daily cron job at 2:00 AM:

```bash
# View cron job
sudo crontab -u defrag -l

# Edit cron job
sudo crontab -u defrag -e
```

### Docker Cron (Containerized)

For Docker deployment, you can add a cron service:

```yaml
# Add to docker-compose.yml
services:
  cron:
    image: alpine:latest
    command: |
      sh -c "
        echo '0 2 * * * curl -X POST http://bookingchart-defragmenter:8080/trigger' > /etc/crontabs/root
        crond -f
      "
    volumes:
      - ./cron:/etc/crontabs
```

## Monitoring and Health Checks

### Health Check Script

```bash
# Run health check
sudo /opt/bookingchart-defragmenter/health_check.sh
```

### Log Monitoring

```bash
# Application logs
tail -f /var/log/bookingchart-defragmenter/defrag_analyzer.log

# System logs
journalctl -u bookingchart-defragmenter.service -f

# Docker logs
docker-compose logs -f bookingchart-defragmenter
```

### Performance Monitoring

```bash
# Check disk usage
df -h /var/log/bookingchart-defragmenter

# Check memory usage
free -h

# Check process status
ps aux | grep python3
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify RMS API credentials
   - Check network connectivity
   - Ensure credentials are properly escaped in config

2. **Permission Denied**
   - Check file permissions: `ls -la /opt/bookingchart-defragmenter/`
   - Verify service user: `id defrag`
   - Fix permissions: `sudo chown -R defrag:defrag /opt/bookingchart-defragmenter/`

3. **Service Won't Start**
   - Check service status: `sudo systemctl status bookingchart-defragmenter.service`
   - View logs: `sudo journalctl -u bookingchart-defragmenter.service`
   - Verify configuration: `sudo cat /etc/bookingchart-defragmenter/config.env`

4. **Docker Issues**
   - Check container logs: `docker-compose logs bookingchart-defragmenter`
   - Verify environment variables: `docker-compose config`
   - Rebuild container: `docker-compose up -d --build`

### Log Analysis

```bash
# Search for errors
grep -i error /var/log/bookingchart-defragmenter/defrag_analyzer.log

# Search for specific property
grep "SADE" /var/log/bookingchart-defragmenter/defrag_analyzer.log

# View recent activity
tail -100 /var/log/bookingchart-defragmenter/defrag_analyzer.log
```

## Security Considerations

1. **Credential Management**
   - Use environment variables instead of hardcoded credentials
   - Restrict access to configuration files: `chmod 600 /etc/bookingchart-defragmenter/config.env`
   - Rotate credentials regularly

2. **File Permissions**
   - Service runs as non-root user (`defrag`)
   - Log files have appropriate permissions
   - Output directories are properly secured

3. **Network Security**
   - Firewall rules for outbound connections
   - HTTPS for API communications
   - SMTP over TLS for email

## Backup and Recovery

### Backup Strategy

```bash
# Backup configuration
sudo cp /etc/bookingchart-defragmenter/config.env /backup/config.env.$(date +%Y%m%d)

# Backup logs
sudo tar -czf /backup/logs-$(date +%Y%m%d).tar.gz /var/log/bookingchart-defragmenter/

# Backup output files
sudo tar -czf /backup/output-$(date +%Y%m%d).tar.gz /opt/bookingchart-defragmenter/output/
```

### Recovery

```bash
# Restore configuration
sudo cp /backup/config.env.20231201 /etc/bookingchart-defragmenter/config.env

# Restore logs
sudo tar -xzf /backup/logs-20231201.tar.gz -C /

# Restart service
sudo systemctl restart bookingchart-defragmenter.service
```

## Uninstallation

### Direct Installation

```bash
sudo /opt/bookingchart-defragmenter/uninstall.sh
```

### Docker Installation

```bash
docker-compose down -v
docker rmi bookingchart-defragmenter_bookingchart-defragmenter
```

## Support and Maintenance

### Regular Maintenance

1. **Log Rotation**: Automatically handled by logrotate
2. **Disk Space**: Monitor `/var/log/bookingchart-defragmenter/` and `/opt/bookingchart-defragmenter/output/`
3. **Updates**: Check for application updates regularly
4. **Backups**: Implement regular backup schedule

### Getting Help

1. Check the logs for error messages
2. Verify configuration settings
3. Test with a single property first
4. Use training database for testing

## Performance Optimization

### Resource Tuning

```bash
# Increase memory limit (if needed)
sudo systemctl set-property bookingchart-defragmenter.service MemoryMax=4G

# Adjust CPU limits
sudo systemctl set-property bookingchart-defragmenter.service CPUQuota=200%
```

### Docker Resource Limits

```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 1G
      cpus: '1.0'
```

## License and Legal

This software is proprietary and confidential. Unauthorized distribution or modification is prohibited.

---

For additional support or questions, please refer to the internal documentation or contact the development team.
