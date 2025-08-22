#!/bin/bash

# ==============================================================================
# RMS Booking Chart Defragmenter - Unified Deployment Script
# ==============================================================================
# Intelligent deployment that handles ANY type of change across the project
#
# Usage: ./deploy.sh [OPTIONS]
# Options:
#   --full              Force full deployment (rebuild containers)
#   --files-only        Update files without restarting services
#   --quick             Skip dependency updates (fastest)
#   --check             Show what would be deployed without deploying
#   --help              Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# VPS Configuration
VPS_HOST="100.78.0.44"
VPS_USER="enaran"
VPS_PASSWORD="Configur8&1"
VPS_APP_DIR="/opt/defrag-app"
CONTAINER_NAME="defrag-app"

# Deployment options
FULL_DEPLOY=false
FILES_ONLY=false
QUICK_DEPLOY=false
CHECK_ONLY=false

# File categories for intelligent deployment
declare -A FILE_CATEGORIES=(
    ["DOCKER"]="Dockerfile* docker-compose*.yml .dockerignore"
    ["CORE_CLI"]="start.py defrag_analyzer.py rms_client.py excel_generator.py email_sender.py holiday_client.py school_holiday_client.py utils.py school_holidays.json"
    ["WEB_APP"]="web_app/"
    ["SCRIPTS"]="scripts/ entrypoint.sh health_check.sh"
    ["CONFIG"]="requirements.txt env.example .env"
    ["DEPLOYMENT"]="install.sh deploy*.sh manage.sh setup*.sh"
    ["DOCS"]="*.md docs/"
)

# Function to print colored output
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

# Function to show help
show_help() {
    echo "RMS Booking Chart Defragmenter - Unified Deployment Script"
    echo ""
    echo "USAGE:"
    echo "    $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "    --full              Force full deployment (rebuild containers)"
    echo "    --files-only        Update files without restarting services"
    echo "    --quick             Skip dependency updates (fastest)"
    echo "    --check             Show what would be deployed without deploying"
    echo "    --help              Show this help message"
    echo ""
    echo "DEPLOYMENT MODES:"
    echo "    Auto-detect         Analyzes changes and chooses optimal deployment"
    echo "    Hot Update          Updates running containers without restart"
    echo "    Service Restart     Restarts services after file updates"
    echo "    Full Rebuild        Rebuilds containers from scratch"
    echo ""
    echo "EXAMPLES:"
    echo "    $0                  Auto-detect changes and deploy"
    echo "    $0 --check          Show what would be deployed"
    echo "    $0 --quick          Fast file-only update"
    echo "    $0 --full           Force complete rebuild"
    echo ""
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --full)
                FULL_DEPLOY=true
                shift
                ;;
            --files-only)
                FILES_ONLY=true
                shift
                ;;
            --quick)
                QUICK_DEPLOY=true
                shift
                ;;
            --check)
                CHECK_ONLY=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Function to detect what types of files have changed
detect_changes() {
    log_step "Analyzing project changes..."
    
    # Get list of changed files (if in git repo)
    if [ -d .git ]; then
        CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null || echo "")
        if [ -z "$CHANGED_FILES" ]; then
            CHANGED_FILES=$(git diff --name-only --cached 2>/dev/null || echo "")
        fi
        if [ -z "$CHANGED_FILES" ]; then
            log_warning "No git changes detected, checking all files"
            CHANGED_FILES="*"
        fi
    else
        log_warning "Not a git repository, assuming all files changed"
        CHANGED_FILES="*"
    fi
    
    # Determine change categories
    DOCKER_CHANGES=false
    CORE_CHANGES=false
    WEB_CHANGES=false
    SCRIPT_CHANGES=false
    CONFIG_CHANGES=false
    DEPLOYMENT_CHANGES=false
    DOCS_CHANGES=false
    
    if [[ "$CHANGED_FILES" == "*" ]]; then
        DOCKER_CHANGES=true
        CORE_CHANGES=true
        WEB_CHANGES=true
        SCRIPT_CHANGES=true
        CONFIG_CHANGES=true
        DEPLOYMENT_CHANGES=true
        DOCS_CHANGES=true
    else
        for file in $CHANGED_FILES; do
            case $file in
                Dockerfile*|docker-compose*|.dockerignore)
                    DOCKER_CHANGES=true
                    ;;
                start.py|defrag_analyzer.py|rms_client.py|excel_generator.py|email_sender.py|holiday_client.py|school_holiday_client.py|utils.py|school_holidays.json)
                    CORE_CHANGES=true
                    ;;
                web_app/*)
                    WEB_CHANGES=true
                    ;;
                scripts/*|entrypoint.sh|health_check.sh)
                    SCRIPT_CHANGES=true
                    ;;
                requirements.txt|env.example|.env)
                    CONFIG_CHANGES=true
                    ;;
                install.sh|deploy*.sh|manage.sh|setup*.sh)
                    DEPLOYMENT_CHANGES=true
                    ;;
                *.md|docs/*)
                    DOCS_CHANGES=true
                    ;;
            esac
        done
    fi
    
    # Show detected changes
    log_info "Change analysis results:"
    echo "  🐳 Docker configs: $([ $DOCKER_CHANGES = true ] && echo "CHANGED" || echo "unchanged")"
    echo "  ⚙️  Core CLI app: $([ $CORE_CHANGES = true ] && echo "CHANGED" || echo "unchanged")" 
    echo "  🌐 Web application: $([ $WEB_CHANGES = true ] && echo "CHANGED" || echo "unchanged")"
    echo "  📜 Scripts: $([ $SCRIPT_CHANGES = true ] && echo "CHANGED" || echo "unchanged")"
    echo "  ⚙️  Configuration: $([ $CONFIG_CHANGES = true ] && echo "CHANGED" || echo "unchanged")"
    echo "  🚀 Deployment: $([ $DEPLOYMENT_CHANGES = true ] && echo "CHANGED" || echo "unchanged")"
    echo "  📚 Documentation: $([ $DOCS_CHANGES = true ] && echo "CHANGED" || echo "unchanged")"
}

# Function to determine deployment strategy
determine_strategy() {
    log_step "Determining deployment strategy..."
    
    if [ $FULL_DEPLOY = true ]; then
        STRATEGY="FULL_REBUILD"
        log_info "Strategy: Full rebuild (forced)"
    elif [ $FILES_ONLY = true ]; then
        STRATEGY="FILES_ONLY"
        log_info "Strategy: Files only (forced)"
    elif [ $QUICK_DEPLOY = true ]; then
        STRATEGY="QUICK_UPDATE"
        log_info "Strategy: Quick update (forced)"
    elif [ $DOCKER_CHANGES = true ] || [ $SCRIPT_CHANGES = true ]; then
        STRATEGY="FULL_REBUILD"
        log_info "Strategy: Full rebuild (Docker/script changes detected)"
    elif [ $CONFIG_CHANGES = true ] && [ $CORE_CHANGES = true ] && [ $WEB_CHANGES = true ]; then
        STRATEGY="SERVICE_RESTART"
        log_info "Strategy: Service restart (major changes detected)"
    elif [ $CONFIG_CHANGES = true ]; then
        STRATEGY="SERVICE_RESTART"
        log_info "Strategy: Service restart (config changes detected)"
    elif [ $CORE_CHANGES = true ] || [ $WEB_CHANGES = true ]; then
        STRATEGY="HOT_UPDATE"
        log_info "Strategy: Hot update (application changes only)"
    elif [ $DOCS_CHANGES = true ] || [ $DEPLOYMENT_CHANGES = true ]; then
        STRATEGY="DOCS_ONLY"
        log_info "Strategy: Documentation only (no service changes needed)"
    else
        STRATEGY="HOT_UPDATE"
        log_info "Strategy: Hot update (default)"
    fi
}

# Function to create deployment package
create_package() {
    log_step "Creating deployment package..."
    
    # Clean up any existing package
    rm -f deployment_package.tar.gz
    
    # Determine what to include based on changes
    INCLUDE_FILES=""
    
    if [ $DOCKER_CHANGES = true ] || [ $STRATEGY = "FULL_REBUILD" ]; then
        INCLUDE_FILES="$INCLUDE_FILES Dockerfile* docker-compose*.yml .dockerignore"
    fi
    
    if [ $CORE_CHANGES = true ] || [ $STRATEGY = "FULL_REBUILD" ] || [ $STRATEGY = "HOT_UPDATE" ] || [ $STRATEGY = "SERVICE_RESTART" ]; then
        INCLUDE_FILES="$INCLUDE_FILES start.py defrag_analyzer.py rms_client.py excel_generator.py email_sender.py holiday_client.py school_holiday_client.py utils.py school_holidays.json"
    fi
    
    if [ $WEB_CHANGES = true ] || [ $STRATEGY = "FULL_REBUILD" ] || [ $STRATEGY = "HOT_UPDATE" ] || [ $STRATEGY = "SERVICE_RESTART" ]; then
        INCLUDE_FILES="$INCLUDE_FILES web_app"
    fi
    
    if [ $SCRIPT_CHANGES = true ] || [ $STRATEGY = "FULL_REBUILD" ]; then
        INCLUDE_FILES="$INCLUDE_FILES scripts entrypoint.sh health_check.sh"
    fi
    
    if [ $CONFIG_CHANGES = true ] || [ $STRATEGY = "FULL_REBUILD" ] || [ $STRATEGY = "SERVICE_RESTART" ]; then
        INCLUDE_FILES="$INCLUDE_FILES requirements.txt env.example"
    fi
    
    if [ $DEPLOYMENT_CHANGES = true ] || [ $STRATEGY = "FULL_REBUILD" ]; then
        INCLUDE_FILES="$INCLUDE_FILES install.sh manage.sh"
    fi
    
    # Create the package
    if [ "$STRATEGY" != "DOCS_ONLY" ]; then
        echo "📦 Including files: $INCLUDE_FILES"
        tar -czf deployment_package.tar.gz $INCLUDE_FILES 2>/dev/null || {
            log_warning "Some files might be missing, continuing..."
            tar -czf deployment_package.tar.gz --ignore-failed-read $INCLUDE_FILES 2>/dev/null || true
        }
        log_success "Deployment package created"
    else
        log_info "Documentation-only changes, no package needed"
    fi
}

# Function to deploy to VPS
deploy_to_vps() {
    if [ "$STRATEGY" = "DOCS_ONLY" ]; then
        log_success "Documentation-only changes, no deployment needed"
        return 0
    fi
    
    if [ $CHECK_ONLY = true ]; then
        log_success "Check complete - would deploy using strategy: $STRATEGY"
        return 0
    fi
    
    log_step "Deploying to VPS using strategy: $STRATEGY"
    
    # Copy package to VPS
    log_info "Uploading deployment package..."
    sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no deployment_package.tar.gz ${VPS_USER}@${VPS_HOST}:${VPS_APP_DIR}/
    
    # Execute deployment on VPS
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} "
        cd $VPS_APP_DIR
        echo '📂 Extracting deployment package...'
        tar -xzf deployment_package.tar.gz
        
        case '$STRATEGY' in
            'FULL_REBUILD')
                echo '🔄 Full rebuild deployment...'
                docker-compose down
                docker-compose build --no-cache
                docker-compose up -d
                ;;
            'SERVICE_RESTART')
                echo '🔄 Service restart deployment...'
                if docker ps | grep -q $CONTAINER_NAME; then
                    docker exec $CONTAINER_NAME pip install -r /app/requirements.txt || true
                fi
                docker-compose restart
                ;;
            'HOT_UPDATE')
                echo '🔥 Hot update deployment...'
                if docker ps | grep -q $CONTAINER_NAME; then
                    # Copy files to running container
                    [ -f defrag_analyzer.py ] && docker cp defrag_analyzer.py $CONTAINER_NAME:/app/
                    [ -f utils.py ] && docker cp utils.py $CONTAINER_NAME:/app/
                    [ -f start.py ] && docker cp start.py $CONTAINER_NAME:/app/
                    [ -f rms_client.py ] && docker cp rms_client.py $CONTAINER_NAME:/app/
                    [ -f excel_generator.py ] && docker cp excel_generator.py $CONTAINER_NAME:/app/
                    [ -f email_sender.py ] && docker cp email_sender.py $CONTAINER_NAME:/app/
                    [ -f holiday_client.py ] && docker cp holiday_client.py $CONTAINER_NAME:/app/
                    [ -f school_holiday_client.py ] && docker cp school_holiday_client.py $CONTAINER_NAME:/app/
                    [ -f school_holidays.json ] && docker cp school_holidays.json $CONTAINER_NAME:/app/
                    [ -d web_app ] && docker cp web_app/. $CONTAINER_NAME:/app/web_app/
                    echo '✅ Hot update completed'
                else
                    echo '❌ Container not running, starting services...'
                    docker-compose up -d
                fi
                ;;
            'QUICK_UPDATE')
                echo '⚡ Quick update deployment...'
                if docker ps | grep -q $CONTAINER_NAME; then
                    [ -d web_app ] && docker cp web_app/. $CONTAINER_NAME:/app/web_app/
                    echo '✅ Quick update completed'
                else
                    docker-compose up -d
                fi
                ;;
            'FILES_ONLY')
                echo '📁 Files-only deployment...'
                # Files are already extracted, no service changes
                echo '✅ Files updated'
                ;;
        esac
        
        echo '🧹 Cleaning up...'
        rm -f deployment_package.tar.gz
        
        echo '🔍 Checking service status...'
        docker-compose ps
        
        if docker ps | grep -q $CONTAINER_NAME; then
            echo '✅ Deployment successful! Service is running.'
            echo '🌐 Web interface: http://$VPS_HOST:8000'
        else
            echo '⚠️ Warning: Service may not be running properly'
        fi
    "
}

# Function to cleanup
cleanup() {
    log_step "Cleaning up local files..."
    rm -f deployment_package.tar.gz
    log_success "Cleanup complete"
}

# Main deployment function
main() {
    echo "🚀 RMS Booking Chart Defragmenter - Unified Deployment"
    echo "======================================================"
    
    parse_arguments "$@"
    detect_changes
    determine_strategy
    create_package
    deploy_to_vps
    cleanup
    
    log_success "Deployment complete!"
    echo ""
    echo "🎯 Next steps:"
    echo "   • Check web interface: http://$VPS_HOST:8000"
    echo "   • Monitor logs: ./manage.sh logs"
    echo "   • Check status: ./manage.sh status"
}

# Run main function with all arguments
main "$@"
