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
DOCKER_REPO="enaran/rms-defragmenter:2.3.0"

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
    
    # Update to use latest stable image
    sed -i 's/enaran\/rms-defragmenter:latest/enaran\/rms-defragmenter:2.3.0/g' docker-compose.yml
    
    # Download environment template
    curl -fsSL "https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/env.example" \
        -o env.example
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        cp env.example .env
        print_status "Environment configuration created"
    fi
    
    # Configure admin credentials securely
    configure_admin_credentials
    
    # Pull the latest images
    print_info "Pulling latest Docker images..."
    docker compose pull
    
    # Create management scripts
    create_management_scripts
    
    print_header "🎉 Installation Complete!"
    echo ""
    print_status "✅ Installed with v2.3.0 (latest stable release)"
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
    print_info "🔐 Admin credentials have been configured during installation"
    print_warning "Keep your admin credentials secure!"
    echo ""
    print_info "🔧 New features in v2.3.0:"
    echo "   • 🔐 Automatic session management (30-min timeout with countdown)"
    echo "   • 📊 Interactive booking charts with move visualizations"
    echo "   • 🎯 Enhanced move suggestions with directional arrows"
    echo "   • 🧹 Production-ready code with cleaned debug output"
    echo "   • 🖥️ Improved UX and interface consistency"
}

generate_secure_password() {
    # Generate a cryptographically secure password using /dev/urandom
    # Use base64 encoding for readability, then clean it up
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-20
}

generate_secure_key() {
    # Generate a cryptographically secure key for secrets
    openssl rand -hex 32
}

configure_admin_credentials() {
    print_header "🔐 Admin Account Setup"
    echo ""
    
    # Prompt for admin username
    while true; do
        read -p "Enter admin username (default: admin): " admin_user
        admin_user=${admin_user:-admin}
        
        if [[ "$admin_user" =~ ^[a-zA-Z0-9_]+$ ]]; then
            break
        else
            print_warning "Username must contain only letters, numbers, and underscores"
        fi
    done
    
    # Generate secure password or allow user input
    echo ""
    print_info "Password Options:"
    echo "1. Generate a secure random password (recommended)"
    echo "2. Enter your own password"
    read -p "Choose option (1 or 2, default: 1): " password_option
    password_option=${password_option:-1}
    
    if [ "$password_option" = "1" ]; then
        admin_pass=$(generate_secure_password)
        print_status "Generated secure password: $admin_pass"
        print_warning "IMPORTANT: Save this password in a secure location!"
        echo ""
        read -p "Press Enter to continue after saving the password..."
    else
        # Prompt for admin password
        while true; do
            echo ""
            echo "Enter admin password (minimum 12 characters, include uppercase, lowercase, digits, and special characters):"
            read -s admin_pass
            echo ""
            echo "Confirm admin password:"
            read -s admin_pass_confirm
            echo ""
            
            if [ "$admin_pass" != "$admin_pass_confirm" ]; then
                print_warning "Passwords don't match. Please try again."
                continue
            fi
            
            if [ ${#admin_pass} -lt 12 ]; then
                print_warning "Password must be at least 12 characters long. Please try again."
                continue
            fi
            
            # Basic password strength check
            if ! echo "$admin_pass" | grep -q '[A-Z]' || \
               ! echo "$admin_pass" | grep -q '[a-z]' || \
               ! echo "$admin_pass" | grep -q '[0-9]' || \
               ! echo "$admin_pass" | grep -q '[^A-Za-z0-9]'; then
                print_warning "Password must include uppercase, lowercase, digits, and special characters. Please try again."
                continue
            fi
            
            break
        done
    fi
    
    # Update .env file with admin credentials
    if [ -f .env ]; then
        # Update existing .env file
        sed -i.bak "s/^ADMIN_USERNAME=.*/ADMIN_USERNAME=$admin_user/" .env
        sed -i.bak "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$admin_pass/" .env
        rm -f .env.bak
    else
        # Create new .env file with admin credentials
        echo "ADMIN_USERNAME=$admin_user" >> .env
        echo "ADMIN_PASSWORD=$admin_pass" >> .env
    fi
    
    print_status "Admin credentials configured successfully"
    echo ""
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
