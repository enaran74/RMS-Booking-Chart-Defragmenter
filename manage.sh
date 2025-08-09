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
INSTALL_DIR="/opt/bookingchart-defragmenter"
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
        echo "Usage: $0 {start|stop|restart|status|logs|health|update|run}"
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
        
    *)
        show_usage
        exit 1
        ;;
esac
