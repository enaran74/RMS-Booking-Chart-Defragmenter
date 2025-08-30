#!/bin/bash
# BookingChartDefragmenter Service Management Script
# Simplified service control for production environments

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="bookingchart-defragmenter.service"
# Support both Docker and traditional installations
if [ -d "/opt/defrag-app" ]; then
    INSTALL_DIR="/opt/defrag-app"
else
    INSTALL_DIR="/opt/bookingchart-defragmenter"
fi
LOG_DIR="/var/log/bookingchart-defragmenter"

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

# Function to show usage
    show_usage() {
        echo -e "${BLUE}🔧 BookingChartDefragmenter Service Manager${NC}"
        echo "=================================================="
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|health|update|run|dev-restart|fast-deploy}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the service (environment setup)"
        echo "  stop     - Stop the service"  
        echo "  restart  - Restart the service"
        echo "  status   - Show service status"
        echo "  logs     - Show recent logs (follow mode)"
        echo "  health   - Run health check"
        echo "  update   - Update from GitHub (requires internet)"
        echo "  run      - Run analysis manually (runs once and exits)"
        echo "  dev-restart - Restart docker-compose stack (fast reload of templates/code)"
        echo "  fast-deploy - Sync templates/code to VPS and restart app container"
        echo ""
        echo "Examples:"
        echo "  sudo $0 restart"
        echo "  sudo $0 logs"
        echo "  sudo $0 update main    # Update from main branch"
        echo "  $0 run                 # Run analysis manually (no sudo needed)"
        echo ""
    }

# Function to check if running as root for commands that need it
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This command must be run as root (use sudo)"
        exit 1
    fi
}

# Function to check if service exists
check_service() {
    if ! systemctl list-units --full -all | grep -Fq "$SERVICE_NAME"; then
        print_error "Service $SERVICE_NAME not found. Please install the application first."
        exit 1
    fi
}

case "$1" in
    start)
        check_root
        check_service
        print_info "Starting $SERVICE_NAME..."
        systemctl start $SERVICE_NAME
        sleep 2
        if systemctl is-active --quiet $SERVICE_NAME; then
            print_status "Service started successfully"
        else
            print_error "Failed to start service"
            exit 1
        fi
        ;;
        
    stop)
        check_root
        check_service
        print_info "Stopping $SERVICE_NAME..."
        systemctl stop $SERVICE_NAME
        print_status "Service stopped"
        ;;
        
    restart)
        check_root
        check_service
        print_info "Restarting $SERVICE_NAME..."
        systemctl restart $SERVICE_NAME
        sleep 2
        if systemctl is-active --quiet $SERVICE_NAME; then
            print_status "Service restarted successfully"
        else
            print_error "Failed to restart service"
            exit 1
        fi
        ;;
        
    status)
        check_service
        echo -e "${BLUE}📊 Service Status:${NC}"
        systemctl status $SERVICE_NAME --no-pager -l
        ;;
        
    logs)
        check_service
        echo -e "${BLUE}📝 Service Logs (Press Ctrl+C to exit):${NC}"
        journalctl -u $SERVICE_NAME -f --no-pager
        ;;
        
    health)
        if [ -f "$INSTALL_DIR/health_check.sh" ]; then
            print_info "Running health check..."
            bash $INSTALL_DIR/health_check.sh
        else
            print_warning "Health check script not found at $INSTALL_DIR/health_check.sh"
            # Basic health check
            if systemctl is-active --quiet $SERVICE_NAME; then
                print_status "Service is running"
            else
                print_error "Service is not running"
                exit 1
            fi
        fi
        ;;
        
    update)
        check_root
        if [ -f "$INSTALL_DIR/update.sh" ]; then
            print_info "Running update script..."
            BRANCH=${2:-main}
            bash $INSTALL_DIR/update.sh $BRANCH
        else
            print_error "Update script not found at $INSTALL_DIR/update.sh"
            print_info "Please ensure the update script is available or run the update manually"
            exit 1
        fi
        ;;
        
    run)
        if [ -f "$INSTALL_DIR/run_defragmentation.sh" ]; then
            print_info "Running analysis manually..."
            print_info "This will execute the full defragmentation analysis"
            print_info "Press Ctrl+C to cancel if needed"
            print_info "Note: Running as user $(whoami)"
            bash $INSTALL_DIR/run_defragmentation.sh
        else
            print_error "Analysis script not found at $INSTALL_DIR/run_defragmentation.sh"
            exit 1
        fi
        ;;
        
    dev-restart)
        print_info "Restarting docker-compose stack..."
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose -f docker-compose.yml down || true
            docker-compose -f docker-compose.yml up -d
            print_status "Stack restarted"
            docker-compose -f docker-compose.yml ps
        else
            print_error "docker-compose not found"
            exit 1
        fi
        ;;

    fast-deploy)
        # Fast deploy - Full filesystem sync to VPS; requires sshpass and rsync
        VPS_IP=${VPS_IP:-100.78.0.44}
        VPS_USER=${VPS_USER:-root}
        VPS_PASSWORD=${VPS_PASSWORD:-BLConfigur8&1}
        REMOTE_DIR=/opt/defrag-app
        
        print_info "Syncing entire project to ${VPS_USER}@${VPS_IP}..."
        
        # Check dependencies
        if ! command -v sshpass >/dev/null 2>&1; then
            print_error "sshpass is required for fast-deploy"
            exit 1
        fi
        if ! command -v rsync >/dev/null 2>&1; then
            print_error "rsync is required for fast-deploy"
            exit 1
        fi
        
        # Generate version info file for containerized deployment
        GIT_VERSION=$(git describe --tags --dirty --always 2>/dev/null || echo "v1.0.0-unknown")
        if [[ ! "$GIT_VERSION" =~ ^v ]]; then
            GIT_VERSION="v1.0.0-$GIT_VERSION"
        fi
        echo "$GIT_VERSION" > web_app/VERSION_INFO
        print_info "Generated version: $GIT_VERSION"
        
        # Full project sync using rsync with smart exclusions
        print_info "Performing full filesystem sync..."
        rsync -avz --delete \
            --rsh="sshpass -p '$VPS_PASSWORD' ssh -o StrictHostKeyChecking=no" \
            --exclude='.git/' \
            --exclude='__pycache__/' \
            --exclude='*.pyc' \
            --exclude='.pytest_cache/' \
            --exclude='node_modules/' \
            --exclude='.env' \
            --exclude='logs/' \
            --exclude='output/' \
            --exclude='.DS_Store' \
            --exclude='*.log' \
            --exclude='.vscode/' \
            --exclude='.idea/' \
            ./ "${VPS_USER}@${VPS_IP}:${REMOTE_DIR}/" || {
                print_warning "rsync failed, falling back to manual sync..."
                
                # Fallback: Create tar and transfer
                print_info "Creating project archive..."
                tar czf /tmp/fast-deploy-$$.tar.gz \
                    --exclude='.git' \
                    --exclude='__pycache__' \
                    --exclude='*.pyc' \
                    --exclude='.pytest_cache' \
                    --exclude='node_modules' \
                    --exclude='.env' \
                    --exclude='logs' \
                    --exclude='output' \
                    --exclude='.DS_Store' \
                    --exclude='*.log' \
                    --exclude='.vscode' \
                    --exclude='.idea' \
                    ./
                
                print_info "Transferring archive..."
                sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no \
                    /tmp/fast-deploy-$$.tar.gz "${VPS_USER}@${VPS_IP}:/tmp/"
                
                print_info "Extracting on VPS..."
                sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} \
                    "cd ${REMOTE_DIR} && tar xzf /tmp/fast-deploy-$$.tar.gz && rm /tmp/fast-deploy-$$.tar.gz"
                
                # Cleanup local temp file
                rm -f /tmp/fast-deploy-$$.tar.gz
            }
        
        print_info "Restarting app container on VPS..."
        sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} \
            'cd /opt/defrag-app && docker-compose restart defrag-app'
        
        print_status "Fast deploy complete - full project synchronized"
        ;;

    *)
        show_usage
        exit 1
        ;;
esac
