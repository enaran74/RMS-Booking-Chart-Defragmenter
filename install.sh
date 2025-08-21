#!/bin/bash
# ==============================================================================
# RMS Booking Chart Defragmenter - Installation Script
# ==============================================================================
# One-command installation script that downloads and deploys the complete system
# Supports Linux, macOS, and Windows (WSL)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git"
REPO_BRANCH="main"
INSTALL_DIR="$HOME/rms-defragmenter"
TEMP_DIR="/tmp/rms-defrag-install-$$"
CONTAINER_NAME="defrag-app"
COMPOSE_PROJECT="rms-defragmenter"

# Function to print colored output
print_header() {
    echo ""
    echo -e "${CYAN}================================================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================================================================================${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${PURPLE}📋 $1${NC}"
}

# Print welcome message
print_header "RMS BOOKING CHART DEFRAGMENTER - INSTALLATION"
echo -e "${BLUE}🚀 Welcome to the RMS Booking Chart Defragmenter installer!${NC}"
echo ""
echo "This script will install the complete system including:"
echo "  ✨ Original CLI defragmentation analyzer with cron scheduling"
echo "  ✨ Modern web interface for move management"
echo "  ✨ PostgreSQL database for data persistence"
echo "  ✨ Docker-based deployment for easy management"
echo ""

# Check operating system
print_step "Detecting operating system..."
OS="unknown"
ARCH=$(uname -m)

case "$(uname -s)" in
    Linux*)     OS="linux" ;;
    Darwin*)    OS="macos" ;;
    CYGWIN*|MINGW*|MSYS*) OS="windows" ;;
    *)          OS="unknown" ;;
esac

print_info "Detected OS: ${OS} (${ARCH})"

if [ "$OS" = "unknown" ]; then
    print_error "Unsupported operating system"
    exit 1
fi

# Check if running as root (not recommended)
if [ "$OS" = "linux" ] && [ "$EUID" -eq 0 ]; then
    print_warning "Running as root is not recommended"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_step "Checking prerequisites..."

# Check for git
if ! command_exists git; then
    print_error "Git is not installed"
    case "$OS" in
        linux)
            print_info "Install with: sudo apt update && sudo apt install git (Debian/Ubuntu)"
            print_info "Or: sudo yum install git (CentOS/RHEL)"
            ;;
        macos)
            print_info "Install with: brew install git"
            print_info "Or: Install Xcode Command Line Tools"
            ;;
        windows)
            print_info "Install Git for Windows from: https://git-scm.com/download/win"
            ;;
    esac
    exit 1
fi
print_status "Git is available"

# Check for Docker
if ! command_exists docker; then
    print_error "Docker is not installed"
    case "$OS" in
        linux)
            print_info "Install with: curl -fsSL https://get.docker.com | sh"
            ;;
        macos)
            print_info "Install Docker Desktop from: https://www.docker.com/products/docker-desktop"
            ;;
        windows)
            print_info "Install Docker Desktop from: https://www.docker.com/products/docker-desktop"
            ;;
    esac
    exit 1
fi
print_status "Docker is available"

# Check for Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose is not installed"
    print_info "Install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi
print_status "Docker Compose is available"

# Determine Docker Compose command
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Check Docker daemon
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon is not running"
    case "$OS" in
        linux)
            print_info "Start with: sudo systemctl start docker"
            ;;
        macos|windows)
            print_info "Start Docker Desktop application"
            ;;
    esac
    exit 1
fi
print_status "Docker daemon is running"

# Create temporary directory
print_step "Creating temporary directory..."
mkdir -p "$TEMP_DIR"
print_status "Temporary directory created: $TEMP_DIR"

# Cleanup function
cleanup() {
    print_info "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Clone repository
print_step "Downloading latest code from GitHub..."
cd "$TEMP_DIR"
git clone --branch "$REPO_BRANCH" "$REPO_URL" rms-defragmenter
print_status "Repository cloned successfully"

# Create installation directory
print_step "Setting up installation directory..."
if [ -d "$INSTALL_DIR" ]; then
    print_warning "Installation directory already exists: $INSTALL_DIR"
    read -p "Remove existing installation? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Stop existing containers
        cd "$INSTALL_DIR" 2>/dev/null && {
            print_info "Stopping existing containers..."
            $DOCKER_COMPOSE -p "$COMPOSE_PROJECT" down --remove-orphans || true
        }
        rm -rf "$INSTALL_DIR"
        print_status "Existing installation removed"
    else
        print_error "Installation aborted"
        exit 1
    fi
fi

mkdir -p "$INSTALL_DIR"
print_status "Installation directory created: $INSTALL_DIR"

# Copy files to installation directory
print_step "Installing application files..."
cp -r "$TEMP_DIR/rms-defragmenter/"* "$INSTALL_DIR/"
print_status "Application files installed"

# Set up configuration
cd "$INSTALL_DIR"
print_step "Setting up configuration..."

# Use configuration files
if [ -f "env.example" ]; then
    cp env.example .env
    print_status "Environment configuration template created"
else
    print_error "Configuration template not found"
    exit 1
fi

# Create data directories
print_step "Creating data directories..."
mkdir -p logs output backups config
print_status "Data directories created"

# Set proper permissions
if [ "$OS" = "linux" ]; then
    # Ensure current user owns the installation
    chown -R "$USER:$USER" "$INSTALL_DIR" 2>/dev/null || {
        print_warning "Could not set ownership - you may need to run: sudo chown -R $USER:$USER $INSTALL_DIR"
    }
fi

# Create convenience scripts
print_step "Creating management scripts..."

# Create start script
cat > start.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting RMS Defragmenter..."
docker compose -p rms-defragmenter up -d
echo "✅ System started!"
echo "🌐 Web Interface: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"
echo "📖 API Docs: http://localhost:8000/docs"
EOF

# Create stop script
cat > stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping RMS Defragmenter..."
docker compose -p rms-defragmenter down
echo "✅ System stopped!"
EOF

# Create logs script
cat > logs.sh << 'EOF'
#!/bin/bash
echo "📋 Showing logs (Ctrl+C to exit)..."
docker compose -p rms-defragmenter logs -f
EOF

# Create update script
cat > update.sh << 'EOF'
#!/bin/bash
set -e
echo "🔄 Updating RMS Defragmenter..."

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose -p rms-defragmenter down
docker compose -p rms-defragmenter build --no-cache
docker compose -p rms-defragmenter up -d

echo "✅ Update completed!"
echo "🌐 Web Interface: http://localhost:8000"
EOF

# Create status script
cat > status.sh << 'EOF'
#!/bin/bash
echo "📊 RMS Defragmenter Status:"
echo ""
docker compose -p rms-defragmenter ps
echo ""
echo "🌐 Web Interface: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"
echo "📖 API Docs: http://localhost:8000/docs"
EOF

# Make scripts executable
chmod +x *.sh
print_status "Management scripts created"

# Configuration guide
print_header "CONFIGURATION REQUIRED"
echo -e "${YELLOW}📝 Before starting the system, you need to configure your RMS credentials:${NC}"
echo ""
echo "1. Edit the configuration file:"
echo -e "   ${CYAN}nano .env${NC}"
echo ""
echo "2. Update the following required variables:"
echo -e "   ${YELLOW}AGENT_ID=${NC}your_agent_id"
echo -e "   ${YELLOW}AGENT_PASSWORD=${NC}your_agent_password"
echo -e "   ${YELLOW}CLIENT_ID=${NC}your_client_id"
echo -e "   ${YELLOW}CLIENT_PASSWORD=${NC}your_client_password"
echo ""
echo "3. Optional: Configure email notifications, database passwords, etc."
echo ""

# Installation complete
print_header "INSTALLATION COMPLETE"
print_status "RMS Booking Chart Defragmenter installed successfully!"
echo ""
echo -e "${BLUE}📁 Installation directory:${NC} $INSTALL_DIR"
echo -e "${BLUE}🔧 Configuration file:${NC} $INSTALL_DIR/.env"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "1. Configure your RMS credentials: ${CYAN}cd $INSTALL_DIR && nano .env${NC}"
echo "2. Start the system: ${CYAN}./start.sh${NC}"
echo "3. Open web interface: ${CYAN}http://localhost:8000${NC}"
echo ""
echo -e "${CYAN}Management commands:${NC}"
echo "  ${GREEN}./start.sh${NC}   - Start the system"
echo "  ${GREEN}./stop.sh${NC}    - Stop the system"
echo "  ${GREEN}./status.sh${NC}  - Check system status"
echo "  ${GREEN}./logs.sh${NC}    - View system logs"
echo "  ${GREEN}./update.sh${NC}  - Update to latest version"
echo ""
echo -e "${BLUE}🎉 Enjoy your unified RMS Defragmentation system!${NC}"
echo ""
print_info "Default login credentials: username=admin, password=admin123"
print_warning "Change default passwords in production!"
echo ""
