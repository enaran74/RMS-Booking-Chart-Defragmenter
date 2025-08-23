#!/bin/bash
# ==============================================================================
# RMS Defragmenter - Production Build Pipeline
# ==============================================================================
# This script builds and pushes production-ready Docker images

set -e

# Configuration
DOCKER_REPO="dhpsystems/rms-defragmenter"
VERSION="2.1.0"  # Database stability fixes: pool_pre_ping=False, optimized connection settings
LATEST_TAG="latest"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 RMS Defragmenter Production Build Pipeline${NC}"
echo "=================================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found. Please install Docker Desktop first.${NC}"
    echo "Download from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# Check if buildx is available for multi-platform builds
if ! docker buildx version &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Buildx not available. Setting up...${NC}"
    docker buildx create --name multiarch --use
else
    echo -e "${GREEN}✅ Docker Buildx available${NC}"
fi

echo -e "${BLUE}📦 Building production image...${NC}"

# Build for multiple architectures
echo "Building for linux/amd64 and linux/arm64..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${DOCKER_REPO}:${VERSION} \
    -t ${DOCKER_REPO}:${LATEST_TAG} \
    --push \
    .

echo -e "${GREEN}✅ Production images built and pushed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Images available:${NC}"
echo "  - ${DOCKER_REPO}:${VERSION}"
echo "  - ${DOCKER_REPO}:${LATEST_TAG}"
echo ""
echo -e "${BLUE}🚀 Ready for customer deployment!${NC}"
echo "Customers can now use: docker-compose.customer.yml"
