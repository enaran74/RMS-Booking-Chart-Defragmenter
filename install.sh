#!/bin/bash
# ==============================================================================
# RMS Booking Chart Defragmenter - Customer Installation Script
# ==============================================================================
# Smart installer that detects environment and uses appropriate deployment method

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
INSTALL_DIR="$HOME/rms-defragmenter"
DOCKER_REPO="dhpsystems/rms-defragmenter:latest"

# Helper functions
print_header() { echo -e "${BLUE}$1${NC}"; }
print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

# Environment detection functions
detect_tailscale() {
    if pgrep -f tailscale > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

detect_vpn() {
    # Check for common VPN indicators
    if ip route | grep -E "(tun|tap|vpn)" > /dev/null 2>&1; then
        return 0
    fi
    if pgrep -f "openvpn|wireguard" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

test_docker_networking() {
    print_info "Testing Docker networking..."
    if timeout 30 docker run --rm alpine:latest ping -c 1 google.com > /dev/null 2>&1; then
        print_status "Standard Docker networking works"
        return 0
    else
        print_warning "Standard Docker networking has issues"
        return 1
    fi
}

# Main installation
main() {
    print_header "🚀 RMS Booking Chart Defragmenter Installation"
    echo "=============================================="
    
    # Check prerequisites
    print_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Please install Docker first:"
        echo "  - Linux: curl -fsSL https://get.docker.com | sh"
        echo "  - macOS/Windows: Download Docker Desktop"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
        exit 1
    fi
    
    print_status "Docker is available"
    
    # Detect environment issues
    NETWORKING_ISSUES=false
    COMPOSE_FILE="docker-compose.yml"
    
    if detect_tailscale; then
        print_warning "Tailscale detected - may cause networking issues"
        NETWORKING_ISSUES=true
    fi
    
    if detect_vpn; then
        print_warning "VPN detected - may cause networking issues"
        NETWORKING_ISSUES=true
    fi
    
    # Test Docker networking
    if ! test_docker_networking; then
        NETWORKING_ISSUES=true
    fi
    
    # Choose deployment method
    if [ "$NETWORKING_ISSUES" = true ]; then
        print_warning "Network issues detected - using host networking mode"
        COMPOSE_FILE="docker-compose.hostnet.yml"
    else
        print_status "Using standard bridge networking"
    fi
    
    # Create installation directory
    print_info "Setting up installation directory..."
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Download configuration files
    print_info "Downloading configuration files..."
    
    # Download the appropriate docker-compose file
    curl -fsSL "https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/${COMPOSE_FILE}" \
        -o docker-compose.yml
    
    # Update to use latest stable image with database fixes
    sed -i 's/dhpsystems\/rms-defragmenter:latest/dhpsystems\/rms-defragmenter:2.1.0/g' docker-compose.yml
    
    # Download environment template
    curl -fsSL "https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/env.example" \
        -o env.example
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        cp env.example .env
        print_status "Environment configuration created"
    fi
    
    # Pull the latest images
    print_info "Pulling latest Docker images..."
    docker compose pull
    
    # Create management scripts
    create_management_scripts
    
    print_header "🎉 Installation Complete!"
    echo ""
    print_status "✅ Installed with v2.1.0 (includes database stability fixes)"
    echo ""
    print_info "Next steps:"
    echo "1. Configure your RMS credentials:"
    echo "   ${CYAN}cd $INSTALL_DIR && nano .env${NC}"
    echo ""
    echo "2. Start the system:"
    echo "   ${CYAN}./start.sh${NC}"
    echo ""
    echo "3. Access the web interface:"
    echo "   ${CYAN}http://localhost:8000${NC}"
    echo ""
    print_warning "Default login: username=admin, password=admin123"
    print_warning "Change these credentials in production!"
    echo ""
    print_info "🔧 This version includes important database stability fixes:"
    echo "   • Resolved authentication issues"
    echo "   • Fixed move history functionality"
    echo "   • Improved session management"
}

create_management_scripts() {
    print_info "Creating management scripts..."
    
    # Start script
    cat > start.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting RMS Defragmenter..."
docker compose up -d
echo "✅ System started!"
echo "🌐 Web Interface: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"
EOF
    
    # Stop script
    cat > stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping RMS Defragmenter..."
docker compose down
echo "✅ System stopped!"
EOF
    
    # Status script
    cat > status.sh << 'EOF'
#!/bin/bash
echo "📊 RMS Defragmenter Status:"
echo ""
docker compose ps
echo ""
echo "📋 Container Health:"
docker compose exec defrag-app ./health_check.sh 2>/dev/null || echo "❌ Health check failed"
EOF
    
    # Logs script
    cat > logs.sh << 'EOF'
#!/bin/bash
echo "📋 Showing logs (Ctrl+C to exit)..."
docker compose logs -f
EOF
    
    # Update script
    cat > update.sh << 'EOF'
#!/bin/bash
echo "🔄 Updating RMS Defragmenter..."
docker compose pull
docker compose up -d
echo "✅ Update completed!"
EOF
    
    chmod +x *.sh
    print_status "Management scripts created"
}

# Run main function
main "$@"
