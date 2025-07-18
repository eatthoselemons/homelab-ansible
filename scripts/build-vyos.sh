#!/bin/bash
# Build VyOS ISO image using Ansible
# This script wraps the ansible-playbook command with proper setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VYOS_VERSION="current"
VYOS_BUILD_TYPE="release"
VYOS_ARCHITECTURE="amd64"
FORCE_BUILD=false
CHECK_ONLY=false

# Project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
IMAGES_DIR="$PROJECT_ROOT/images/vyos"
VENV_PATH="/home/user/ansible-venv"

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
VyOS Image Builder

Usage: $0 [OPTIONS]

Options:
    -v, --version VERSION      VyOS version to build (default: current)
                              Options: current, current, circinus
    -t, --type TYPE           Build type (default: release)
                              Options: release, development
    -a, --arch ARCH           Architecture (default: amd64)
                              Options: amd64, arm64
    -f, --force               Force rebuild even if image exists
    -c, --check               Check if image exists without building
    -h, --help                Show this help message

Examples:
    # Build default VyOS image (current release)
    $0

    # Build current development version
    $0 --version current --type development

    # Check if image exists
    $0 --check

    # Force rebuild
    $0 --force

Notes:
    - Building a VyOS image takes 20-30 minutes
    - Requires sudo for Docker operations
    - Images are saved to: $IMAGES_DIR

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VYOS_VERSION="$2"
            shift 2
            ;;
        -t|--type)
            VYOS_BUILD_TYPE="$2"
            shift 2
            ;;
        -a|--arch)
            VYOS_ARCHITECTURE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_BUILD=true
            shift
            ;;
        -c|--check)
            CHECK_ONLY=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    print_error "Ansible virtual environment not found at $VENV_PATH"
    print_info "Please set up the ansible environment first"
    exit 1
fi

# Activate virtual environment
export PATH="$VENV_PATH/bin:$PATH"

# Check if ansible is available
if ! command -v ansible-playbook &> /dev/null; then
    print_error "ansible-playbook not found in virtual environment"
    exit 1
fi

# Create images directory if it doesn't exist
mkdir -p "$IMAGES_DIR"

# Define image path
IMAGE_PATH="$IMAGES_DIR/vyos-${VYOS_VERSION}.iso"
LATEST_LINK="$IMAGES_DIR/vyos-latest.iso"
CURRENT_LINK="$IMAGES_DIR/vyos-current.iso"

# Check if image exists
if [ -f "$IMAGE_PATH" ]; then
    IMAGE_SIZE=$(du -h "$IMAGE_PATH" | cut -f1)
    print_info "VyOS image exists: $IMAGE_PATH (Size: $IMAGE_SIZE)"
    
    if [ "$CHECK_ONLY" = true ]; then
        print_success "Image check complete"
        exit 0
    fi
    
    if [ "$FORCE_BUILD" = false ]; then
        print_warning "Image already exists. Use --force to rebuild"
        exit 0
    else
        print_warning "Force rebuild requested. Existing image will be replaced"
    fi
else
    print_info "VyOS image not found: $IMAGE_PATH"
    
    if [ "$CHECK_ONLY" = true ]; then
        print_warning "Image does not exist"
        exit 1
    fi
fi

# Display build configuration
echo ""
print_info "Build Configuration:"
echo "  Version: $VYOS_VERSION"
echo "  Type: $VYOS_BUILD_TYPE"
echo "  Architecture: $VYOS_ARCHITECTURE"
echo "  Output: $IMAGE_PATH"
echo ""

# Confirm build
if [ "$FORCE_BUILD" = false ]; then
    read -p "This will build a VyOS ISO which takes 20-30 minutes. Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Build cancelled"
        exit 0
    fi
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    print_info "Please install Docker first: sudo apt-get install docker.io"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running or you don't have permissions"
    print_info "Try: sudo usermod -aG docker $USER && newgrp docker"
    exit 1
fi

# Run the build
print_info "Starting VyOS build process..."
echo ""

# Execute build
print_info "Starting build with the following parameters:"
echo "  Version: $VYOS_VERSION"
echo "  Type: $VYOS_BUILD_TYPE"
echo "  Architecture: $VYOS_ARCHITECTURE"
echo "  Builder: $USER"
echo ""

# Run ansible-playbook directly without building command string
if ansible-playbook build-vyos-image.yml \
    -e "vyos_version=$VYOS_VERSION" \
    -e "vyos_build_type=$VYOS_BUILD_TYPE" \
    -e "vyos_architecture=$VYOS_ARCHITECTURE" \
    -e "vyos_build_by=Built_by_$USER" \
    -K; then
    print_success "VyOS image build completed successfully!"
    
    # Create symlinks
    if [ -f "$IMAGE_PATH" ]; then
        print_info "Creating symlinks..."
        ln -sf "vyos-${VYOS_VERSION}.iso" "$LATEST_LINK"
        
        # If this is 'current' version, also create vyos-current.iso link
        if [ "$VYOS_VERSION" = "current" ]; then
            ln -sf "vyos-${VYOS_VERSION}.iso" "$CURRENT_LINK"
        fi
        
        # Show final results
        echo ""
        print_info "Build results:"
        ls -lah "$IMAGES_DIR"/vyos*.iso
    fi
else
    print_error "Build failed!"
    exit 1
fi

echo ""
print_success "Done! VyOS image is ready at: $IMAGE_PATH"