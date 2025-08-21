#!/bin/bash
# ==============================================================================
# RMS Booking Chart Defragmenter - Prepare Unified Structure
# ==============================================================================
# This script reorganizes the project for the unified deployment model

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Project root directory
PROJECT_ROOT=$(dirname "$(dirname "$(realpath "$0")")")
cd "$PROJECT_ROOT"

log_info "🔄 Preparing unified project structure..."
log_info "Project root: $PROJECT_ROOT"

# Create unified directory structure
log_info "Creating unified directory structure..."

# Create app subdirectories
mkdir -p app/original
mkdir -p app/web
mkdir -p app/shared
mkdir -p scripts
mkdir -p docs

# Move original application files to app/original/
log_info "Moving original application files..."
cp start.py defrag_analyzer.py rms_client.py excel_generator.py \
   email_sender.py holiday_client.py school_holiday_client.py \
   utils.py school_holidays.json app/original/

# Move web application files to app/web/
log_info "Moving web application files..."
cp -r web_app/* app/web/
# Remove the old web_app directory structure references
find app/web -name "*.py" -exec sed -i 's|from app\.|from web.app.|g' {} \; 2>/dev/null || true

# Create shared configuration management
log_info "Creating shared configuration..."
cat > app/shared/config.py << 'EOF'
"""
Unified configuration management for RMS Defragmenter
"""
import os
from pathlib import Path
from typing import Optional

class UnifiedConfig:
    """Unified configuration for both CLI and web components"""
    
    def __init__(self):
        self.load_env()
    
    def load_env(self):
        """Load environment variables"""
        # RMS API Credentials
        self.agent_id = os.getenv('AGENT_ID')
        self.agent_password = os.getenv('AGENT_PASSWORD')
        self.client_id = os.getenv('CLIENT_ID')
        self.client_password = os.getenv('CLIENT_PASSWORD')
        
        # Database Configuration
        self.db_host = os.getenv('DB_HOST', 'postgres')
        self.db_port = int(os.getenv('DB_PORT', '5432'))
        self.db_name = os.getenv('DB_NAME', 'defrag_db')
        self.db_user = os.getenv('DB_USER', 'defrag_user')
        self.db_password = os.getenv('DB_PASSWORD', 'DefragDB2024!')
        
        # Web Application
        self.web_app_port = int(os.getenv('WEB_APP_PORT', '8000'))
        self.web_app_host = os.getenv('WEB_APP_HOST', '0.0.0.0')
        self.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
        self.jwt_secret_key = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-here')
        
        # Original Application
        self.target_properties = os.getenv('TARGET_PROPERTIES', 'ALL')
        self.use_training_db = os.getenv('USE_TRAINING_DB', 'false').lower() == 'true'
        self.enable_emails = os.getenv('ENABLE_EMAILS', 'false').lower() == 'true'
        self.send_consolidated_email = os.getenv('SEND_CONSOLIDATED_EMAIL', 'false').lower() == 'true'
        
        # Scheduling
        self.cron_schedule = os.getenv('CRON_SCHEDULE', '0 2 * * *')
        self.enable_cron = os.getenv('ENABLE_CRON', 'true').lower() == 'true'
        
        # Logging and Output
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_dir = Path(os.getenv('LOG_DIR', '/app/logs'))
        self.output_dir = Path(os.getenv('OUTPUT_DIR', '/app/output'))
    
    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def validate_rms_credentials(self) -> bool:
        """Validate that required RMS credentials are present"""
        required = [self.agent_id, self.agent_password, self.client_id, self.client_password]
        return all(cred is not None for cred in required)

# Global configuration instance
config = UnifiedConfig()
EOF

# Move management scripts
log_info "Organizing management scripts..."
mv debug_service.sh deploy_incremental.sh deploy_web_app.sh health_check.sh \
   manage.sh run_defragmentation.sh service_wrapper.sh setup_cron.sh \
   setup_ssh.sh update.sh scripts/ 2>/dev/null || true

# Replace configuration files with unified versions
log_info "Activating unified configuration files..."

# Backup original files
mkdir -p backup/original
cp README.md backup/original/ 2>/dev/null || true
cp docker-compose.yml backup/original/ 2>/dev/null || true
cp Dockerfile backup/original/ 2>/dev/null || true
cp env.example backup/original/ 2>/dev/null || true
cp requirements.txt backup/original/ 2>/dev/null || true

# Activate unified files
if [ -f "README.unified.md" ]; then
    cp README.unified.md README.md
    log_success "Activated unified README"
fi

if [ -f "docker-compose.unified.yml" ]; then
    cp docker-compose.unified.yml docker-compose.yml
    log_success "Activated unified Docker Compose"
fi

if [ -f "Dockerfile.unified" ]; then
    cp Dockerfile.unified Dockerfile
    log_success "Activated unified Dockerfile"
fi

if [ -f "env.unified.example" ]; then
    cp env.unified.example env.example
    log_success "Activated unified environment template"
fi

if [ -f "requirements.unified.txt" ]; then
    cp requirements.unified.txt requirements.txt
    log_success "Activated unified requirements"
fi

if [ -f "install.unified.sh" ]; then
    cp install.unified.sh install.sh
    chmod +x install.sh
    log_success "Activated unified installer"
fi

# Create documentation structure
log_info "Organizing documentation..."
mkdir -p docs

# Move technical documentation
mv DEVELOPER_README.md docs/DEVELOPMENT.md 2>/dev/null || true
mv DOCKER_INSTALLATION.md docs/DOCKER.md 2>/dev/null || true
mv SCRIPTS.md docs/SCRIPTS.md 2>/dev/null || true

# Create consolidated API documentation
cat > docs/API.md << 'EOF'
# API Reference

This document covers the REST API provided by the web interface component.

## Base URL
```
http://localhost:8000
```

## Authentication
The API uses Bearer token authentication. Obtain a token by logging in:

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Authorization: Basic $(echo -n 'admin:admin123' | base64)"
```

## Endpoints

### Health Check
- **GET** `/health` - System health status

### Authentication
- **POST** `/auth/login` - User authentication

### Properties
- **GET** `/api/v1/properties/` - List all properties
- **GET** `/api/v1/properties/{code}` - Get property details

### Move Suggestions
- **GET** `/api/v1/defrag-moves/{property}/suggestions` - Get move suggestions
- **POST** `/api/v1/defrag-moves/{move_id}/action` - Accept/reject move

### System Management
- **GET** `/api/v1/setup/database/tables` - Database information

For complete API documentation, visit: http://localhost:8000/docs
EOF

# Create deployment guide
cat > docs/DEPLOYMENT.md << 'EOF'
# Deployment Guide

## Quick Deployment
Use the one-command installer:
```bash
curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install.sh | bash
```

## Manual Deployment
1. Clone repository
2. Copy unified configuration files
3. Configure environment variables
4. Start with Docker Compose

## Production Considerations
- Change default passwords
- Configure proper backup strategy
- Set up monitoring and alerting
- Configure firewall and security

See README.md for detailed instructions.
EOF

# Clean up redundant files
log_info "Cleaning up redundant files..."

# Remove old configuration files (keep backups)
rm -f docker-compose.unified.yml Dockerfile.unified env.unified.example \
      requirements.unified.txt README.unified.md install.unified.sh \
      2>/dev/null || true

# Remove old web app directory (files moved to app/web)
rm -rf web_app 2>/dev/null || true

# Create final directory structure documentation
cat > STRUCTURE.md << 'EOF'
# Project Structure

```
RMS-Booking-Chart-Defragmenter/
├── README.md                    # Main documentation
├── docker-compose.yml           # Unified container orchestration
├── Dockerfile                   # Unified container image
├── requirements.txt             # All Python dependencies
├── env.example                  # Configuration template
├── install.sh                   # One-command installer
├── LICENSE                      # MIT license
├── .gitignore                   # Git ignore rules
│
├── app/                         # Application code
│   ├── original/                # CLI defragmentation analyzer
│   │   ├── start.py            # Main entry point
│   │   ├── defrag_analyzer.py  # Core algorithm
│   │   ├── rms_client.py       # RMS API client
│   │   ├── excel_generator.py  # Report generation
│   │   ├── email_sender.py     # Email notifications
│   │   ├── holiday_client.py   # Holiday data integration
│   │   └── utils.py            # Utilities and logging
│   │
│   ├── web/                     # Web interface
│   │   ├── main.py             # FastAPI application
│   │   ├── api/                # REST API endpoints
│   │   ├── core/               # Core web components
│   │   ├── models/             # Database models
│   │   ├── services/           # Business logic
│   │   ├── static/             # Static web assets
│   │   └── templates/          # HTML templates
│   │
│   └── shared/                  # Shared components
│       ├── config.py           # Unified configuration
│       └── utils.py            # Common utilities
│
├── scripts/                     # Management scripts
│   ├── entrypoint.sh           # Container startup
│   ├── cron_runner.py          # Scheduled analysis
│   ├── health_check.sh         # Health monitoring
│   └── prepare_unified_structure.sh
│
├── docs/                        # Documentation
│   ├── DEVELOPMENT.md          # Developer guide
│   ├── DEPLOYMENT.md           # Deployment guide
│   ├── API.md                  # API reference
│   └── DOCKER.md               # Docker guide
│
├── backup/                      # Backup of original files
│   └── original/               # Pre-migration backups
│
└── output/                      # Generated reports and logs
    ├── logs/                   # Application logs
    ├── reports/                # Excel reports
    └── backups/                # Data backups
```
EOF

# Set proper permissions
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true

# Final validation
log_info "Validating unified structure..."

# Check that key files exist
required_files=(
    "README.md"
    "docker-compose.yml"
    "Dockerfile"
    "requirements.txt"
    "env.example"
    "install.sh"
    "app/original/start.py"
    "app/web/main.py"
    "app/shared/config.py"
    "scripts/entrypoint.sh"
    "scripts/cron_runner.py"
    "scripts/health_check.sh"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    log_success "✅ All required files are present"
else
    log_error "❌ Missing files: ${missing_files[*]}"
    exit 1
fi

# Summary
log_success "🎉 Unified structure preparation complete!"
echo ""
log_info "📋 Summary of changes:"
echo "  ✅ Original CLI app moved to app/original/"
echo "  ✅ Web application moved to app/web/"
echo "  ✅ Shared configuration created in app/shared/"
echo "  ✅ Management scripts organized in scripts/"
echo "  ✅ Documentation consolidated in docs/"
echo "  ✅ Unified configuration files activated"
echo "  ✅ Redundant files cleaned up"
echo "  ✅ Backup of original files preserved"
echo ""
log_info "🚀 Ready for unified deployment!"
log_info "Next steps:"
echo "  1. Configure credentials: nano env.example -> .env"
echo "  2. Test deployment: docker compose up -d"
echo "  3. Verify functionality: ./scripts/health_check.sh"
echo ""
