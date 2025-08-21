# RMS Booking Chart Defragmenter

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/docker-20.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)

A comprehensive system for optimizing accommodation bookings across multiple properties through automated defragmentation analysis and an intuitive web interface for move management.

**Developed by:** Mr Tim Curtis, Operations Systems Manager  
**Organization:** Discovery Holiday Parks  
**Version:** 2.0

---

## 🚀 Quick Start (One-Command Installation)

### Prerequisites
- **Docker** and **Docker Compose** installed
- **Git** installed
- **Internet connection** for downloading components

### Installation
```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install.sh | bash
```

### Configuration & Launch
```bash
# Navigate to installation directory
cd ~/rms-defragmenter

# Configure your RMS credentials
nano .env

# Start the unified system
./start.sh
```

### Access the System
- **🌐 Web Interface**: http://localhost:8000
- **📊 Health Check**: http://localhost:8000/health  
- **📖 API Documentation**: http://localhost:8000/docs
- **👤 Default Login**: username=`admin`, password=`admin123`

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Unified Architecture](#unified-architecture)
3. [Installation Options](#installation-options)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Features](#features)
7. [Management](#management)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)
10. [Development](#development)

---

## 🎯 System Overview

The RMS Booking Chart Defragmenter Unified System combines two powerful components:

### 🤖 **Automated CLI Analyzer**
- **Scheduled Analysis**: Runs automatically via cron (default: daily 2:00 AM)
- **Multi-Property Support**: Analyze specific properties or entire portfolios
- **Holiday-Aware Optimization**: 2-month forward holiday analysis for peak periods
- **Excel Reports**: Comprehensive visual reports with move suggestions
- **Email Notifications**: Automated stakeholder notifications

### 🖥️ **Modern Web Interface**
- **Real-Time Management**: Interactive move suggestion management
- **User Authentication**: Role-based access control
- **Database Persistence**: PostgreSQL for data integrity
- **WebSocket Updates**: Live progress tracking
- **RESTful API**: Full programmatic access

### 🔄 **Integrated Benefits**
- **Single Deployment**: One Docker container for everything
- **Shared Configuration**: Unified environment management
- **Consistent Data**: Both components use same RMS credentials
- **Unified Monitoring**: Single health check and logging system

---

## 🏗️ Unified Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Container                             │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   Web App       │    │   CLI Analyzer  │    │ PostgreSQL  │ │
│  │   (FastAPI)     │◄──►│   (Cron Job)    │◄──►│ Database    │ │
│  │   Port: 8000    │    │   Schedule: 2AM │    │ Port: 5432  │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│           │                       │                      │     │
│           ▼                       ▼                      ▼     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Shared Components                              │ │
│  │  • RMS API Client  • Excel Generator  • Email Sender      │ │
│  │  • Holiday Client  • Logging System   • Config Manager    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Component Integration**
- **Shared RMS Credentials**: Both CLI and web use same API access
- **Common Configuration**: Single `.env` file for all settings
- **Unified Logging**: Centralized logs in `/app/logs/`
- **Shared Output**: Excel reports accessible to both interfaces

---

## 🛠️ Installation Options

### Option 1: One-Command Installation (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install.sh | bash
```

### Option 2: Manual Installation
```bash
# Clone repository
git clone https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
cd RMS-Booking-Chart-Defragmenter

# Setup unified configuration
cp env.unified.example .env
cp docker-compose.unified.yml docker-compose.yml
cp Dockerfile.unified Dockerfile

# Configure credentials
nano .env

# Start system
docker compose up -d
```

### Option 3: Development Setup
```bash
# Clone for development
git clone https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
cd RMS-Booking-Chart-Defragmenter

# Install dependencies
pip install -r requirements.unified.txt

# Setup development environment
cp env.unified.example .env.dev
export $(cat .env.dev | xargs)

# Run components separately for development
# Terminal 1: Web app
cd web_app && python main.py

# Terminal 2: CLI analyzer
python start.py --agent-id $AGENT_ID --agent-password "$AGENT_PASSWORD" --client-id $CLIENT_ID --client-password "$CLIENT_PASSWORD" -p ALL
```

---

## ⚙️ Configuration

### **Required Configuration**
Edit `.env` file with your RMS credentials:

```bash
# RMS API Credentials (REQUIRED)
AGENT_ID=your_agent_id_here
AGENT_PASSWORD=your_agent_password_here
CLIENT_ID=your_client_id_here
CLIENT_PASSWORD=your_client_password_here
```

### **Optional Configuration**

#### **Analysis Settings**
```bash
# Property Selection
TARGET_PROPERTIES=ALL                    # or SADE,QROC,TCRA
USE_TRAINING_DB=false                    # Use training database

# Scheduling
CRON_SCHEDULE=0 2 * * *                  # Daily at 2:00 AM
ENABLE_CRON=true                         # Enable automated runs
```

#### **Web Interface**
```bash
# Web Server
WEB_APP_PORT=8000
WEB_APP_HOST=0.0.0.0

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

#### **Database**
```bash
# PostgreSQL Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=defrag_db
DB_USER=defrag_user
DB_PASSWORD=DefragDB2024!
```

#### **Email Notifications**
```bash
# Email Settings
ENABLE_EMAILS=false                      # Enable email notifications
SEND_CONSOLIDATED_EMAIL=false            # Send consolidated reports
CONSOLIDATED_EMAIL_RECIPIENT=operations@discoveryparks.com.au

# SMTP Configuration (if emails enabled)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@domain.com
APP_PASSWORD=your_app_password_here
```

---

## 📈 Usage

### **Web Interface Usage**

#### **1. Access the System**
- Navigate to http://localhost:8000
- Login with: `admin` / `admin123`
- Change default passwords in production!

#### **2. Manage Properties**
- View property list and access controls
- Configure user permissions per property
- Monitor property-specific analysis status

#### **3. Review Move Suggestions**
- View automated move suggestions by property
- Filter by category, importance, and date range
- Accept/reject individual moves
- Track implementation status

#### **4. Monitor System Health**
- Check system status and performance
- View analysis logs and cron job history
- Monitor database connectivity and health

### **CLI Usage (Automated)**

The CLI analyzer runs automatically based on your cron schedule, but you can also trigger manual runs:

#### **Manual Analysis**
```bash
# Run analysis for all properties
docker exec defrag-app python3 /app/app/original/start.py \
  --agent-id $AGENT_ID --agent-password "$AGENT_PASSWORD" \
  --client-id $CLIENT_ID --client-password "$CLIENT_PASSWORD" \
  -p ALL

# Run analysis for specific properties
docker exec defrag-app python3 /app/app/original/start.py \
  --agent-id $AGENT_ID --agent-password "$AGENT_PASSWORD" \
  --client-id $CLIENT_ID --client-password "$CLIENT_PASSWORD" \
  -p SADE,QROC,TCRA

# Run with email notifications
docker exec defrag-app python3 /app/app/original/start.py \
  --agent-id $AGENT_ID --agent-password "$AGENT_PASSWORD" \
  --client-id $CLIENT_ID --client-password "$CLIENT_PASSWORD" \
  -p ALL -e
```

---

## ✨ Features

### **Intelligent Defragmentation**
- **🧠 Smart Algorithm**: Identifies optimal reservation moves to reduce fragmentation
- **🎯 Category-Based Optimization**: Respects accommodation type preferences
- **🎄 Holiday-Aware Analysis**: 2-month forward holiday optimization
- **📊 Strategic Importance Scoring**: Prioritizes high-impact moves
- **🔄 Sequential Move Ordering**: Optimizes implementation sequence

### **Comprehensive Reporting**
- **📈 Visual Excel Reports**: Color-coded booking charts with move suggestions
- **📅 Daily Heatmaps**: Overview of opportunities across all properties
- **📋 Detailed Move Tables**: Complete implementation guidance
- **🎄 Holiday-Enhanced Reports**: Separate analysis for peak periods
- **📊 Consolidated Summaries**: Cross-property opportunity analysis

### **Modern Web Interface**
- **🔐 Secure Authentication**: Role-based access control
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **⚡ Real-Time Updates**: WebSocket-powered live progress tracking
- **🎨 Professional UI**: Discovery Holiday Parks branded interface
- **📊 Interactive Charts**: Visual move suggestion management

### **Automated Operations**
- **⏰ Cron Scheduling**: Configurable automated analysis runs
- **📧 Email Notifications**: Automated stakeholder communications
- **🔍 Health Monitoring**: Comprehensive system health checks
- **💾 Data Persistence**: PostgreSQL database for move tracking
- **🔄 Automatic Updates**: Git-based update mechanism

### **Enterprise Features**
- **🏢 Multi-Property Support**: Analyze entire property portfolios
- **👥 User Management**: Role-based property access control
- **📈 Performance Monitoring**: API usage and system metrics
- **🔒 Security**: SQL injection protection, input validation
- **📋 Audit Trails**: Complete move suggestion and action history

---

## 🎛️ Management

### **System Management Commands**
```bash
# In your installation directory (~/rms-defragmenter)

./start.sh      # Start the system
./stop.sh       # Stop the system
./status.sh     # Check system status
./logs.sh       # View live logs
./update.sh     # Update to latest version
```

### **Docker Commands**
```bash
# Direct Docker Compose management
docker compose -p rms-defragmenter up -d     # Start
docker compose -p rms-defragmenter down      # Stop
docker compose -p rms-defragmenter ps        # Status
docker compose -p rms-defragmenter logs -f   # Logs

# Container access
docker exec -it defrag-app bash          # Shell access
docker exec defrag-app ./health_check.sh # Health check
```

### **Monitoring & Maintenance**

#### **Log Files**
- **Web App**: `/app/logs/web_app.log`
- **Cron Jobs**: `/app/logs/cron_runner.log`
- **Analysis**: `/app/logs/defrag_analyzer.log`
- **System**: `docker compose logs`

#### **Health Checks**
```bash
# Automated health check
curl http://localhost:8000/health

# Comprehensive health check
docker exec defrag-unified ./health_check.sh

# System status
./status.sh
```

#### **Data Management**
```bash
# Backup data volumes
docker run --rm -v rms-defragmenter_defrag_output:/data -v $(pwd):/backup alpine tar czf /backup/output_backup.tar.gz -C /data .

# View output files
docker exec defrag-app ls -la /app/output/

# Access database
docker exec -it defrag-postgres psql -U defrag_user -d defrag_db
```

---

## 🔗 API Reference

### **Authentication**
```bash
# Login to get access token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Authorization: Basic $(echo -n 'admin:admin123' | base64)"
```

### **Properties**
```bash
# Get all properties
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/properties/"

# Get property details
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/properties/SADE"
```

### **Move Suggestions**
```bash
# Get move suggestions for a property
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/defrag-moves/SADE/suggestions"

# Accept/reject a move
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "accept"}' \
  "http://localhost:8000/api/v1/defrag-moves/123/action"
```

### **System Status**
```bash
# Health check
curl "http://localhost:8000/health"

# System info
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/setup/database/tables"
```

**Complete API Documentation**: http://localhost:8000/docs

---

## 🐛 Troubleshooting

### **Common Issues**

#### **1. Container Won't Start**
```bash
# Check Docker daemon
docker info

# Check for port conflicts
netstat -tulpn | grep 8000

# View startup logs
docker compose logs defrag-app
```

#### **2. Database Connection Failed**
```bash
# Check PostgreSQL container
docker compose ps postgres

# Test database connectivity
docker exec defrag-app pg_isready -h postgres -p 5432 -U defrag_user -d defrag_db

# View database logs
docker compose logs postgres
```

#### **3. RMS API Authentication Failed**
```bash
# Verify credentials in .env file
cat .env | grep -E "(AGENT_|CLIENT_)"

# Test API connectivity manually
docker exec defrag-app python3 -c "
import os, requests
response = requests.post('https://api.rms.com/auth', 
  json={'agent_id': os.getenv('AGENT_ID'), 'password': os.getenv('AGENT_PASSWORD')})
print(f'Status: {response.status_code}')
"
```

#### **4. Web Interface Not Loading**
```bash
# Check web app health
curl http://localhost:8000/health

# Verify port forwarding
docker port defrag-app

# Check for JavaScript errors in browser console
```

#### **5. Cron Jobs Not Running**
```bash
# Check cron daemon
docker exec defrag-app pgrep cron

# View cron logs
docker exec defrag-app tail -f /app/logs/cron_runner.log

# List configured cron jobs
docker exec defrag-app crontab -l
```

### **System Recovery**

#### **Reset to Default State**
```bash
# Stop system
./stop.sh

# Remove data volumes (WARNING: This deletes all data!)
docker volume rm rms-defragmenter_postgres_data
docker volume rm rms-defragmenter_defrag_output
docker volume rm rms-defragmenter_defrag_logs

# Restart system
./start.sh
```

#### **Update to Latest Version**
```bash
# Automated update
./update.sh

# Manual update
git pull origin main
docker compose build --no-cache
docker compose up -d
```

### **Performance Optimization**

#### **Resource Monitoring**
```bash
# Container resource usage
docker stats defrag-app defrag-postgres

# System resource usage
docker exec defrag-app htop
```

#### **Database Optimization**
```bash
# Database size and performance
docker exec defrag-postgres psql -U defrag_user -d defrag_db -c "
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats WHERE schemaname = 'public';"
```

---

## 💻 Development

### **Development Environment Setup**
```bash
# Clone repository
git clone https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
cd RMS-Booking-Chart-Defragmenter

# Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.unified.txt

# Setup environment
cp env.unified.example .env.dev
export $(cat .env.dev | xargs)
```

### **Running Components Separately**
```bash
# Start PostgreSQL for development
docker run -d --name dev-postgres \
  -e POSTGRES_DB=defrag_db \
  -e POSTGRES_USER=defrag_user \
  -e POSTGRES_PASSWORD=DefragDB2024! \
  -p 5432:5432 postgres:15-alpine

# Run web application
cd web_app
export DB_HOST=localhost
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run CLI analyzer
python start.py --agent-id $AGENT_ID --agent-password "$AGENT_PASSWORD" \
  --client-id $CLIENT_ID --client-password "$CLIENT_PASSWORD" -p ALL
```

### **Testing**
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Integration tests
pytest tests/integration/
```

### **Building Custom Images**
```bash
# Build unified image
docker build -f Dockerfile.unified -t rms-defragmenter:custom .

# Build for specific architecture
docker buildx build --platform linux/amd64,linux/arm64 \
  -f Dockerfile.unified -t rms-defragmenter:multi-arch .
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Support

### **Documentation**
- **Installation Guide**: This README
- **API Documentation**: http://localhost:8000/docs
- **Developer Guide**: `docs/DEVELOPMENT.md`

### **Getting Help**
1. **Check Logs**: Use `./logs.sh` or `docker compose logs`
2. **Health Check**: Run `docker exec defrag-unified ./health_check.sh`
3. **GitHub Issues**: Report bugs and request features
4. **System Status**: Use `./status.sh` for overview

### **Contributing**
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 🎉 Conclusion

The RMS Booking Chart Defragmenter provides a comprehensive solution for accommodation optimization with:

- **🚀 Easy Installation**: One-command setup
- **🔄 Automated Operations**: Scheduled analysis and reporting
- **🖥️ Modern Interface**: Intuitive web-based management
- **🏢 Enterprise Features**: Multi-property, role-based access
- **📊 Comprehensive Reporting**: Visual analytics and insights
- **🔧 Easy Management**: Simple start/stop/update commands

Transform your property management with intelligent defragmentation and maximize your revenue potential!

---

**🌟 Ready to optimize your booking charts? Run the installer and get started in minutes!**

```bash
curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install.sh | bash
```
