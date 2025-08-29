# RMS Booking Chart Defragmenter

![Version](https://img.shields.io/badge/version-v2.3.0%2016%20g5551140%20dirty-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/docker-20.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)

A comprehensive system for optimizing accommodation bookings across multiple properties through automated defragmentation analysis, interactive booking charts, and direct RMS move execution via an intuitive web interface with enterprise-grade security.

**Developed by:** Mr Tim Curtis, Operations Systems Manager
**Organization:** Discovery Holiday Parks
**Version:** Git-based automatic versioning
**CI/CD:** ✅ Automated testing, security scanning, and Docker builds

---

## 🆕 What's New in v2.5.0

### 🚀 **Major New Features**

- **⚡ RMS Move Execution**: Web interface now applies defragmentation moves directly to RMS
- **🎯 Interactive Move Management**: Select, preview, and apply moves with real-time feedback
- **📊 Enhanced Booking Charts**: Visual booking chart display with move suggestions and directional arrows
- **🔄 Live Progress Tracking**: WebSocket-powered real-time progress updates during move execution
- **📧 Unified Email System**: Consistent email functionality between web interface and scheduled analysis

### 🔧 **System Improvements**

- **⚙️ Unified CLI Integration**: `manage.sh run` now supports all features including email notifications
- **🐳 Enhanced Docker Deployment**: Improved container management and environment synchronization
- **🔐 Advanced Security**: Comprehensive security middleware with CSP, rate limiting, and audit logging
- **📱 Responsive Design**: Better mobile and desktop experience with improved state management
- **🗄️ Database Persistence**: Move history and user preferences stored in PostgreSQL

### 🛠️ **Developer Experience**

- **🔄 Fast Deploy Pipeline**: Rapid development with bind-mounted code for instant updates
- **🧪 Comprehensive Testing**: Automated CI/CD with security scanning and Docker builds
- **📖 Enhanced Documentation**: Updated deployment guides and troubleshooting sections
- **🌐 Production Ready**: Optimized for enterprise deployment with proper logging and monitoring

### 📌 **v2.5.0 Stability Checkpoint**

This version represents a **stable, production-ready release** with all core functionality complete:
- ✅ **Fully functional RMS move execution** via web interface
- ✅ **Complete CLI integration** with email notifications and manual execution
- ✅ **Enterprise-grade security** and deployment pipeline
- ✅ **Comprehensive documentation** and user guides

**Next**: Holiday analysis integration planned for v2.6.0 to add school holiday optimization to the web interface.

---

## 🚀 Quick Start (One-Command Installation)

### Prerequisites (Host VPS)

- Ubuntu 22.04/24.04 or Debian 12
- curl, git
- Docker Engine 24+ and Docker Compose V2
- Open port: 8000 (web UI)
- Tailscale/VPN environments supported (host networking is used)

### Installation

```bash
# Download and run the automated installer (will prompt for admin credentials)
curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install.sh | bash
```

### Configuration & Launch (VPS)

```bash
# Navigate to installation directory
cd ~/rms-defragmenter

# Start the system
./start.sh

# Access the web interface to complete configuration
open http://your-vps-ip:8000
```

The system will automatically guide you through configuration via the **Setup Wizard** on first access.

### Access the System

- **🌐 Web Interface**: [http://localhost:8000](http://localhost:8000)
- **📊 Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **📖 API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **👤 Secure Login**: Admin credentials configured during installation
- **🔐 Session Security**: 30-minute automatic logout with countdown timer

---

## 📋 Table of Contents

1. System Overview
2. Architecture
3. Installation
4. Configuration
5. Usage
6. Features
7. Management
8. API Reference
9. Troubleshooting
10. Development

---

## 🎯 System Overview

The RMS Booking Chart Defragmenter provides a complete solution combining:

### 🤖 **Automated CLI Analyzer**

- **Scheduled Analysis**: Runs automatically via cron (default: daily 2:00 AM)
- **Multi-Property Support**: Analyze specific properties or entire portfolios
- **Holiday-Aware Optimization**: 2-month forward holiday analysis for peak periods
- **Excel Reports**: Comprehensive visual reports with move suggestions
- **Email Notifications**: Automated stakeholder notifications

### 🖥️ **Modern Web Interface**

- **⚡ Direct RMS Integration**: Apply defragmentation moves directly to RMS system
- **🎯 Interactive Move Management**: Select, preview, and execute moves with real-time feedback
- **📊 Visual Booking Charts**: Enhanced booking chart display with directional move arrows
- **🔄 Live Progress Tracking**: WebSocket-powered real-time updates during move execution
- **🔐 Enterprise Security**: JWT authentication, session management, and comprehensive audit logging
- **🗄️ Database Persistence**: PostgreSQL for move history and user preferences
- **📱 Responsive Design**: Optimized for both desktop and mobile interfaces
- **🌐 RESTful API**: Full programmatic access with comprehensive documentation

### 🔄 **Production Benefits**

- **Pre-Built Images**: Fast 5-10 minute deployments
- **Smart Environment Detection**: Automatically handles networking conflicts
- **Multi-Architecture Support**: Works on AMD64, ARM64, and ARM platforms
- **Zero Build Time**: No compilation required for customers
- **Professional Grade**: Tested, reliable deployment pipeline

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Container                             │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   Web App       │    │   CLI Analyzer  │    │ PostgreSQL  │ │
│  │   (FastAPI)     │◄──►│   (Cron Job)    │◄──►│ Database    │ │
│  │   Port: 8000    │    │   Schedule: 2AM │    │ Port: 5433  │ │
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

- **Pre-Built Images**: Production-ready Docker images from Docker Hub
- **Smart Installation**: Automatic environment detection and deployment
- **Unified Configuration**: Single `.env` file for all settings
- **Centralized Logging**: All logs in `/app/logs/`
- **Shared Output**: Excel reports accessible to both interfaces

---

## 🚀 **Installation Methods**

Choose your preferred deployment method based on your environment and needs:

### 🐳 **Option 1: Docker Deployment (Recommended)**

#### **Quick Docker Installation**

```bash
# One-command installation with environment detection
curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install.sh | bash
```

#### **Manual Docker Setup**

```bash
# Clone repository
git clone https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
cd RMS-Booking-Chart-Defragmenter

# Start system (auto-detects host networking needs)
docker compose up -d

# Complete setup via web interface
# Navigate to http://localhost:8000 and use the Setup Wizard
```

#### **Docker Benefits**
- ✅ **Fast deployment**: 5-10 minutes with pre-built images
- ✅ **Secure setup**: Prompts for admin credentials during installation
- ✅ **No build failures**: Production-ready containers
- ✅ **Automatic networking**: Detects VPN/Tailscale conflicts
- ✅ **Easy updates**: Simple `docker compose pull`

### 🖥️ **Option 2: Native Installation**

For environments where Docker isn't preferred or available:

```bash
# Coming soon - native installer is being developed
# For now, use manual native setup below
```

#### **Manual Native Setup**

```bash
# Prerequisites: Python 3.11+, PostgreSQL 15+, Git
sudo apt update && sudo apt install -y python3.11 python3-pip postgresql git

# Clone and setup
git clone https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
cd RMS-Booking-Chart-Defragmenter

# Install Python dependencies
pip3 install -r requirements.txt

# Setup database
sudo -u postgres createuser defrag_user
sudo -u postgres createdb defrag_db -O defrag_user
sudo -u postgres psql -c "ALTER USER defrag_user PASSWORD 'DefragDB2024!';"

# Start web application
cd web_app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Complete setup via web interface
# Navigate to http://localhost:8000 and use the Setup Wizard
```

#### **Native Installation Benefits**
- ✅ **Direct system integration**: No container overhead
- ✅ **Full system access**: Direct file system and process control
- ✅ **Custom configurations**: Fine-grained system tuning
- ✅ **Development friendly**: Easy debugging and modification

### 🔧 **Option 3: Development Setup**

For developers and contributors:

```bash
# Clone repository
git clone https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
cd RMS-Booking-Chart-Defragmenter

# Install development dependencies
pip install -r requirements.txt
pip install -r web_app/requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest

# Start development server
cd web_app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

See [DEVELOPER_README.md](DEVELOPER_README.md) for complete development guide.

---

## ⚙️ Configuration

### **🎯 Recommended: Web-Based Setup (Easy)**

The modern approach uses the intuitive **Setup Wizard** and **Setup Page**:

**First-Time Setup (Setup Wizard):**
1. Start the system: `./start.sh`
2. Access web interface: `http://your-server:8000`
3. Complete the **Setup Wizard** with:
   - RMS API credentials (Agent ID, passwords, Client ID)
   - Target properties (CALI, SADE, ALL, etc.)
   - System mode (Training vs Live)
   - Email notifications (optional)
4. The system automatically creates and manages the `.env` file

**Ongoing Configuration (Setup Page):**
- Access **Setup** from the main navigation
- Modify any configuration setting via web interface
- All settings are automatically synchronized to `.env`
- No manual file editing required
- Real-time validation and testing

**🎯 Benefits:**
- ✅ **User-friendly**: Guided step-by-step setup
- ✅ **Validation**: Real-time credential testing
- ✅ **Error-free**: No typos in manual editing
- ✅ **Synchronized**: Automatically updates all locations
- ✅ **Secure**: Proper formatting and escaping

### **⚙️ Alternative: Manual Configuration**

For advanced users who prefer manual configuration:

```bash
# Edit .env file directly (shared by web and CLI)
nano .env

# Required RMS API credentials:
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

# Web Interface
WEB_APP_PORT=8000
```

### **Database**

```bash
# PostgreSQL Configuration (hostnet mode)
DB_HOST=localhost
DB_PORT=5433
DB_NAME=defrag_db
DB_USER=defrag_user
DB_PASSWORD=DefragDB2024!
```

### **Email Notifications**

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

- Navigate to [http://localhost:8000](http://localhost:8000)
- Login with the admin credentials you configured during installation
- **🔐 Session expires after 30 minutes with visual countdown**

#### **2. Manage Properties**

- View property list and access controls
- Configure user permissions per property
- Monitor property-specific analysis status

#### **3. Review Move Suggestions**

- View automated move suggestions by property
- Filter by category, importance, and date range
- Accept/reject individual moves with 3-way toggle
- Track implementation status

#### **4. Interactive Booking Charts**

- Click "Show Chart" to display visual booking layout
- View all reservations with color-coded status (Confirmed, Arrived, Departed, etc.)
- See move suggestions highlighted with directional arrows (⬆️⬇️)
- Horizontal scroll to view full accommodation layout
- Fixed bookings marked with 🎯 icon
- Out of Order/Maintenance periods clearly labeled

#### **5. Monitor System Health**

- Check system status and performance
- View analysis logs and cron job history
- Monitor database connectivity and health

### **Automated Analysis**

The CLI analyzer runs automatically based on your schedule, but you can also trigger manual runs:

#### **Manual Analysis**

The CLI analyzer automatically reads configuration from your `.env` file:

```bash
# Run analysis for all properties (uses TARGET_PROPERTIES from .env)
docker exec defrag-app python start.py

# Run analysis for specific properties (override .env setting)
docker exec defrag-app python start.py -p CALI,SADE

# Run analysis with training database (override .env setting)
docker exec defrag-app python start.py -p ALL -t

# Run analysis with email notifications (override .env setting)  
docker exec defrag-app python start.py -p CALI -e

# View available CLI options
docker exec defrag-app python start.py --help
```

**Note**: CLI mode automatically uses credentials and settings from your `.env` file. You can override specific settings using command-line arguments.

#### **Cron Schedule Configuration**

The automated analysis runs via cron schedule (default: daily at 2:00 AM). To customize:

```bash
# Check current cron schedule
docker exec defrag-app crontab -l

# Edit cron schedule (as root)
docker exec defrag-app crontab -e

# Example schedules:
# Daily at 3:00 AM:    0 3 * * *
# Every 6 hours:       0 */6 * * *  
# Twice daily:         0 6,18 * * *
# Weekly (Sundays):    0 2 * * 0
```

The CLI uses environment variables from your `.env` file:

- `TARGET_PROPERTIES`: Which properties to analyze (default: ALL)
- `ENABLE_EMAILS`: Send email notifications (default: false)
- `USE_TRAINING_DB`: Use training database (default: false)

---

## 🎮 System Operation

### **🌐 Web Interface Usage**

Access the web interface at `http://your-server:8000`:

1. **📊 View Booking Charts**: Interactive charts showing current reservations and fragmentation
2. **🎯 Load Move Suggestions**: Generate defragmentation recommendations for selected properties
3. **⚡ Execute Moves**: Select and apply moves directly to the RMS system with real-time progress
4. **📈 Track Progress**: Monitor move execution via WebSocket updates
5. **📋 Review History**: View previous moves and analysis results
6. **⚙️ Manage Settings**: Configure RMS credentials, email settings, and analysis parameters

### **🖥️ Manual CLI Execution**

Run defragmentation analysis manually using the unified command:

```bash
# Run analysis with current .env settings (emails, training mode, target properties)
./manage.sh run
```

**Features of Manual Execution:**

- ✅ **Same Configuration**: Uses identical settings as scheduled cron job
- ✅ **Email Support**: Sends notifications if `ENABLE_EMAILS=true`
- ✅ **Training Mode**: Respects `USE_TRAINING_DB` setting for safe testing
- ✅ **Property Filtering**: Honors `TARGET_PROPERTIES` configuration
- ✅ **Real-time Output**: Shows progress and results in terminal
- ✅ **Docker Integration**: Executes inside container with proper environment

### **📅 Scheduled Analysis**

The system automatically runs analysis via cron:

```bash
# Default schedule: Daily at 2:00 AM
# View current cron configuration
docker exec defrag-app crontab -l

# Check cron service status
docker exec defrag-app service cron status
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

- **🔐 Secure Authentication**: Role-based access control with automatic session management
- **⏰ Session Security**: 30-minute timeout with visual countdown timer (warning at 5min, danger at 1min)
- **📊 Interactive Booking Charts**: Visual booking chart display with horizontal scrolling
- **🎯 Move Visualization**: Directional arrows showing move suggestions (⬆️⬇️)
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices
- **⚡ Real-Time Updates**: WebSocket-powered live progress tracking
- **🎨 Professional UI**: Discovery Holiday Parks branded interface
- **🖥️ Enhanced UX**: Improved state management and interface consistency

### **Production Deployment**

- **🚀 Fast Installation**: 5-10 minute deployment with pre-built images
- **🔍 Smart Detection**: Automatic environment and networking detection
- **🌐 Multi-Platform**: AMD64, ARM64, and ARM architecture support
- **🛡️ Reliable**: No build failures, consistent deployments
- **🔄 Easy Updates**: Simple image pulling and container restart

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
docker compose up -d                                # Start (standard)
docker compose -f docker-compose.hostnet.yml up -d  # Start (host network)
docker compose down                                  # Stop
docker compose ps                                    # Status
docker compose logs -f                               # Logs

# Container access
docker exec -it defrag-app bash          # Shell access
docker exec defrag-app ./health_check.sh # Health check
```

### **Monitoring & Maintenance**

#### **Health Checks**

```bash
# Automated health check
curl http://localhost:8000/health

# System status
./status.sh
```

#### **Log Files**

- **Web App**: Docker logs via `./logs.sh`
- **Analysis**: `/app/logs/defrag_analyzer.log`
- **System**: `docker compose logs`

#### **Data Management**

```bash
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

**Complete API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

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

#### **2. Network Issues (Tailscale/VPN)**

The smart installer automatically detects and handles this, but if you installed manually:

```bash
# Use host networking
cp docker-compose.hostnet.yml docker-compose.yml
docker compose up -d
```

#### **3. Database Connection Failed**

```bash
# Check PostgreSQL container
docker compose ps postgres

# Test database connectivity
docker exec defrag-app pg_isready -h postgres -p 5432 -U defrag_user -d defrag_db

# View database logs
docker compose logs postgres
```

#### **4. RMS API Authentication Failed**

```bash
# Verify credentials in .env file
cat .env | grep -E "(AGENT_|CLIENT_)"

# Check credentials don't have extra spaces
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
```

---

## 💻 Development

For developers who want to build and customize the system, see:

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production build pipeline
- **[DEVELOPER_README.md](DEVELOPER_README.md)** - Technical architecture
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines

### **Local Development**

```bash
# Clone repository
git clone https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
cd RMS-Booking-Chart-Defragmenter

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env.dev
export $(cat .env.dev | xargs)

# Run web application
cd web_app
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run CLI analyzer (uses .env for credentials)
docker exec defrag-app python start.py -p ALL
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Support

### **Documentation**

- **Installation Guide**: This README
- **Production Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Developer Guide**: [DEVELOPER_README.md](DEVELOPER_README.md)

### **Getting Help**

1. **Check Logs**: Use `./logs.sh` or `docker compose logs`
2. **Health Check**: Run `curl http://localhost:8000/health`
3. **GitHub Issues**: Report bugs and request features
4. **System Status**: Use `./status.sh` for overview

### **Contributing**

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 🎉 Conclusion

The RMS Booking Chart Defragmenter provides a comprehensive solution for accommodation optimization with:

- **🚀 Fast Installation**: One-command setup with pre-built images
- **🔄 Automated Operations**: Scheduled analysis and reporting
- **🖥️ Modern Interface**: Intuitive web-based management
- **🏢 Enterprise Features**: Multi-property, role-based access
- **📊 Comprehensive Reporting**: Visual analytics and insights
- **🛡️ Production Ready**: Reliable, tested deployment pipeline

Transform your property management with intelligent defragmentation and maximize your revenue potential!

---

**🌟 Ready to optimize your booking charts? Get started in minutes!**

```bash
curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install-customer.sh | bash
```
