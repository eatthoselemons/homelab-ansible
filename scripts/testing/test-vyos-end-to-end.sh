#!/bin/bash
#
# test-vyos-end-to-end.sh - Comprehensive VyOS testing suite
#
# DESCRIPTION:
#   This script runs a complete end-to-end test of the VyOS infrastructure,
#   including image building, verification, and all setup components.
#
# USAGE:
#   export ANSIBLE_BECOME_PASSWORD='your_sudo_password'
#   ./test-vyos-end-to-end.sh [options]
#
# OPTIONS:
#   --skip-build       Skip VyOS image building (use existing image)
#   --skip-setup       Skip VyOS setup tests
#   --force-rebuild    Force rebuild even if image exists
#   --help            Show this help message
#
# EXAMPLES:
#   # Run full test suite
#   export ANSIBLE_BECOME_PASSWORD='mysudopass'
#   ./test-vyos-end-to-end.sh
#
#   # Skip image building if you already have one
#   ./test-vyos-end-to-end.sh --skip-build
#
#   # Only test image building and verification
#   ./test-vyos-end-to-end.sh --skip-setup
#
# REQUIREMENTS:
#   - Docker installed and running
#   - Ansible and molecule installed
#   - ANSIBLE_BECOME_PASSWORD environment variable set
#   - ~20GB free disk space
#   - Internet connectivity
#
# DURATION:
#   - Full run: ~45-60 minutes
#   - With --skip-build: ~15-20 minutes
#

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
SKIP_BUILD=false
SKIP_SETUP=false
FORCE_REBUILD=false

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING:${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $1"
}

print_info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] INFO:${NC} $1"
}

# Function to show help
show_help() {
    # Extract header comments between lines 2-42
    sed -n '2,42p' "$0" | grep '^#' | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-setup)
            SKIP_SETUP=true
            shift
            ;;
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Header
echo ""
echo "================================================"
echo "     VyOS End-to-End Test Suite"
echo "================================================"
echo ""

# Show configuration
print_info "Test Configuration:"
echo "  Skip Build: $SKIP_BUILD"
echo "  Skip Setup Tests: $SKIP_SETUP"
echo "  Force Rebuild: $FORCE_REBUILD"
echo ""

# Check prerequisites
print_status "Checking prerequisites..."

if [ -z "$ANSIBLE_BECOME_PASSWORD" ]; then
    print_error "ANSIBLE_BECOME_PASSWORD environment variable not set"
    echo ""
    echo "Please set it before running this script:"
    echo "  export ANSIBLE_BECOME_PASSWORD='your_sudo_password'"
    echo ""
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v ansible-playbook &> /dev/null; then
    print_error "ansible-playbook is not installed or not in PATH"
    exit 1
fi

if ! command -v molecule &> /dev/null; then
    print_warning "molecule is not installed, skipping molecule tests"
    SKIP_SETUP=true
fi

print_status "✓ Prerequisites checked"
echo ""

# Track timing
START_TIME=$(date +%s)

# Step 1: Run molecule tests for vyos_image_builder
print_status "Step 1: Running VyOS image builder tests..."
cd collections/ansible_collections/homelab/nexus/extensions/
if molecule test -s nexus.vyos.image_builder; then
    print_status "✓ Image builder tests passed"
else
    print_error "Image builder tests failed"
    exit 1
fi
cd "$PROJECT_ROOT"
echo ""

# Step 2: Build real VyOS image
if [ "$SKIP_BUILD" = false ]; then
    print_status "Step 2: Building real VyOS image..."
    
    # Check if image already exists
    if [ -f "images/vyos/vyos-current.iso" ] && [ "$FORCE_REBUILD" = false ]; then
        print_warning "VyOS image already exists at images/vyos/vyos-current.iso"
        read -p "Do you want to rebuild it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Using existing image"
        else
            rm -f images/vyos/vyos-current.iso images/vyos/vyos-latest.iso
            print_warning "Building VyOS image (this takes 20-30 minutes)..."
            ansible-playbook build-vyos-image.yaml \
                -e ansible_become_password="${ANSIBLE_BECOME_PASSWORD}" \
                -e vyos_version=current
            print_status "✓ VyOS image built successfully"
        fi
    else
        if [ "$FORCE_REBUILD" = true ] && [ -f "images/vyos/vyos-current.iso" ]; then
            print_info "Force rebuild requested, removing existing image"
            rm -f images/vyos/vyos-current.iso images/vyos/vyos-latest.iso
        fi
        print_warning "Building VyOS image (this takes 20-30 minutes)..."
        ansible-playbook build-vyos-image.yaml \
            -e ansible_become_password="${ANSIBLE_BECOME_PASSWORD}" \
            -e vyos_version=current
        print_status "✓ VyOS image built successfully"
    fi
else
    print_info "Step 2: Skipping image build (--skip-build)"
fi
echo ""

# Step 3: Verify the built image
print_status "Step 3: Verifying VyOS image..."
if [ -f "images/vyos/vyos-current.iso" ]; then
    "$SCRIPT_DIR/verify-vyos-image.sh" "images/vyos/vyos-current.iso"
    print_status "✓ Image verification passed"
else
    print_error "No VyOS image found to verify"
    print_info "Run without --skip-build to create one"
    exit 1
fi
echo ""

# Step 4: Run VyOS setup tests
if [ "$SKIP_SETUP" = false ]; then
    print_status "Step 4: Running VyOS setup molecule tests..."
    cd collections/ansible_collections/homelab/nexus/extensions/

    # Test individual VyOS setup components
    # Note: Additional scenarios like vlans, firewall, nat may be added in the future
    SCENARIOS=(
        "nexus.vyos.setup"
        "nexus.vyos.security_hardening"
    )
    
    for scenario in "${SCENARIOS[@]}"; do
        print_info "Testing $scenario..."
        if molecule test -s "$scenario"; then
            print_status "✓ $scenario passed"
        else
            print_error "$scenario failed"
            exit 1
        fi
    done

    # Step 5: Run full integration test
    print_status "Step 5: Running VyOS full integration test..."
    if molecule test -s nexus.vyos.full_integration; then
        print_status "✓ Full integration test passed"
    else
        print_error "Full integration test failed"
        exit 1
    fi

    cd "$PROJECT_ROOT"
else
    print_info "Step 4-5: Skipping VyOS setup tests (--skip-setup)"
fi

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))

# Summary
echo ""
echo "================================================"
print_status "✅ ALL TESTS PASSED SUCCESSFULLY!"
echo "================================================"
echo ""
print_info "Test Summary:"
    echo "  ✓ VyOS image builder tests: PASSED"
fi
if [ "$SKIP_BUILD" = false ]; then
    echo "  ✓ VyOS image build: COMPLETED"
fi
echo "  ✓ VyOS image verification: PASSED"
if [ "$SKIP_SETUP" = false ]; then
    echo "  ✓ VyOS setup component tests: PASSED"
    echo "  ✓ VyOS full integration test: PASSED"
fi
echo ""
print_info "Duration: ${DURATION_MIN}m ${DURATION_SEC}s"
echo ""
if [ -f "images/vyos/vyos-current.iso" ]; then
    ISO_SIZE=$(stat -c%s "images/vyos/vyos-current.iso" 2>/dev/null || stat -f%z "images/vyos/vyos-current.iso" 2>/dev/null)
    ISO_SIZE_MB=$((ISO_SIZE / 1024 / 1024))
    print_info "VyOS image: images/vyos/vyos-current.iso (${ISO_SIZE_MB} MB)"
fi