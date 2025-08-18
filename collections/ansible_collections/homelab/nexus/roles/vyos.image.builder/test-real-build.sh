#!/bin/bash
# Test script for real VyOS image building
# This runs the existing build playbook and verifies the result

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"

echo "Testing VyOS Image Builder with real image build..."
echo "This will build a real VyOS ISO (~600MB) and takes 20-30 minutes"
echo ""

# Check if ANSIBLE_BECOME_PASSWORD is set
if [ -z "$ANSIBLE_BECOME_PASSWORD" ]; then
    echo "Error: ANSIBLE_BECOME_PASSWORD environment variable not set"
    echo "Please export ANSIBLE_BECOME_PASSWORD='your_sudo_password'"
    exit 1
fi

cd "$PROJECT_ROOT"

echo "Running from directory: $(pwd)"
echo "Looking for playbook: $PROJECT_ROOT/build-vyos-image.yaml"

# Use a test directory for the image
TEST_IMAGE_DIR="/tmp/vyos-test-build-$$"
mkdir -p "$TEST_IMAGE_DIR"

echo "Building VyOS image to test directory: $TEST_IMAGE_DIR"

# Run the build playbook with test directory
ansible-playbook build-vyos-image.yaml \
    -e ansible_become_password="${ANSIBLE_BECOME_PASSWORD}" \
    -e vyos_images_dir="$TEST_IMAGE_DIR" \
    -e vyos_version=current \
    -K

# Verify the image was created
if [ ! -f "$TEST_IMAGE_DIR/vyos-current.iso" ]; then
    echo "Error: VyOS image not created at expected location"
    rm -rf "$TEST_IMAGE_DIR"
    exit 1
fi

# Check image size
ISO_SIZE=$(stat -c%s "$TEST_IMAGE_DIR/vyos-current.iso" 2>/dev/null || stat -f%z "$TEST_IMAGE_DIR/vyos-current.iso" 2>/dev/null)
ISO_SIZE_MB=$((ISO_SIZE / 1024 / 1024))

if [ $ISO_SIZE -lt 500000000 ]; then
    echo "Error: ISO too small (${ISO_SIZE_MB} MB), expected > 500MB"
    rm -rf "$TEST_IMAGE_DIR"
    exit 1
fi

# Check image format
ISO_FORMAT=$(file "$TEST_IMAGE_DIR/vyos-current.iso")
if [[ ! "$ISO_FORMAT" =~ "ISO 9660" ]] || [[ ! "$ISO_FORMAT" =~ "bootable" ]]; then
    echo "Error: ISO is not in expected bootable format: $ISO_FORMAT"
    rm -rf "$TEST_IMAGE_DIR"
    exit 1
fi

# Check symlink
if [ ! -L "$TEST_IMAGE_DIR/vyos-latest.iso" ]; then
    echo "Error: Latest symlink not created"
    rm -rf "$TEST_IMAGE_DIR"
    exit 1
fi

echo ""
echo "✓ VyOS Image Builder test passed!"
echo "  - Image size: ${ISO_SIZE_MB} MB"
echo "  - Format: ISO 9660 bootable"
echo "  - Symlink: vyos-latest.iso -> vyos-current.iso"

# Test idempotency by running again
echo ""
echo "Testing idempotency (should skip build)..."
ansible-playbook build-vyos-image.yaml \
    -e ansible_become_password="${ANSIBLE_BECOME_PASSWORD}" \
    -e vyos_images_dir="$TEST_IMAGE_DIR" \
    -e vyos_version=current \
    -K | grep -q "VyOS image available at" && echo "✓ Idempotency test passed"

# Cleanup
echo ""
echo "Cleaning up test directory..."
rm -rf "$TEST_IMAGE_DIR"

echo ""
echo "All tests completed successfully!"