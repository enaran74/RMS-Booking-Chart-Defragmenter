#!/bin/bash
# SSH Setup Script for GitHub Access
# Run this on your Raspberry Pi to configure SSH keys for GitHub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_USER="defrag"
SSH_DIR="/home/$SERVICE_USER/.ssh"
SSH_KEY="$SSH_DIR/id_rsa"

# Function to print colored output
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

echo -e "${BLUE}🔑 SSH Key Setup for GitHub Access${NC}"
echo "=================================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if service user exists
if ! id "$SERVICE_USER" &>/dev/null; then
    print_error "Service user '$SERVICE_USER' not found. Please install the application first."
    exit 1
fi

print_info "Setting up SSH keys for GitHub access..."

# Create SSH directory if it doesn't exist
if [ ! -d "$SSH_DIR" ]; then
    print_info "Creating SSH directory..."
    mkdir -p "$SSH_DIR"
    chown "$SERVICE_USER:$SERVICE_USER" "$SSH_DIR"
    chmod 700 "$SSH_DIR"
fi

# Check if SSH key already exists
if [ -f "$SSH_KEY" ]; then
    print_warning "SSH key already exists at $SSH_KEY"
    read -p "Do you want to generate a new key? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Backing up existing key..."
        mv "$SSH_KEY" "${SSH_KEY}.backup.$(date +%Y%m%d_%H%M%S)"
        mv "${SSH_KEY}.pub" "${SSH_KEY}.pub.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    else
        print_info "Using existing SSH key"
    fi
fi

# Generate SSH key if it doesn't exist
if [ ! -f "$SSH_KEY" ]; then
    print_info "Generating new SSH key..."
    print_info "Please provide your email address for the SSH key:"
    read -p "Email: " EMAIL
    
    if [ -z "$EMAIL" ]; then
        print_error "Email address is required"
        exit 1
    fi
    
    # Generate SSH key as the service user
    sudo -u "$SERVICE_USER" ssh-keygen -t rsa -b 4096 -C "$EMAIL" -f "$SSH_KEY" -N ""
    print_status "SSH key generated successfully"
else
    print_status "Using existing SSH key"
fi

# Set proper permissions
chown "$SERVICE_USER:$SERVICE_USER" "$SSH_KEY"*
chmod 600 "$SSH_KEY"
chmod 644 "${SSH_KEY}.pub"

# Start SSH agent and add key
print_info "Configuring SSH agent..."
sudo -u "$SERVICE_USER" bash -c "eval \$(ssh-agent -s) && ssh-add $SSH_KEY"

# Test GitHub connection
print_info "Testing GitHub SSH connection..."
if sudo -u "$SERVICE_USER" ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    print_status "SSH authentication successful!"
else
    print_warning "SSH authentication failed. You need to add the public key to GitHub."
    echo ""
    print_info "📋 Next Steps:"
    echo "1. Copy the public key below:"
    echo ""
    cat "${SSH_KEY}.pub"
    echo ""
    print_info "2. Go to GitHub: https://github.com/settings/keys"
    print_info "3. Click 'New SSH key'"
    print_info "4. Paste the key above and save"
    print_info "5. Test again: sudo -u $SERVICE_USER ssh -T git@github.com"
    echo ""
    print_info "Or run this script again after adding the key to GitHub"
    exit 1
fi

print_status "SSH setup completed successfully!"
echo ""
print_info "You can now run updates with:"
echo "sudo /opt/bookingchart-defragmenter/manage.sh update"
