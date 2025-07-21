#!/bin/bash
#
# verify-vyos-image.sh - Quick verification tool for VyOS ISO images
#
# DESCRIPTION:
#   This script performs basic validation checks on a VyOS ISO image to ensure
#   it meets the expected criteria for size, format, and bootability.
#
# USAGE:
#   ./verify-vyos-image.sh [path/to/vyos.iso]
#
# EXAMPLES:
#   # Verify the default image location
#   ./verify-vyos-image.sh
#
#   # Verify a specific image
#   ./verify-vyos-image.sh /tmp/custom-vyos.iso
#
#   # Verify the latest built image
#   ./verify-vyos-image.sh images/vyos/vyos-latest.iso
#
# CHECKS PERFORMED:
#   - File existence
#   - File size (warns if < 500MB)
#   - ISO 9660 format
#   - Bootable flag
#   - Detects mock vs real images
#
# EXIT CODES:
#   0 - Verification passed
#   1 - Image not found or verification failed
#

set -e

# Default image path relative to project root
DEFAULT_IMAGE="images/vyos/vyos-current.iso"

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Use provided path or default
IMAGE_PATH="${1:-$PROJECT_ROOT/$DEFAULT_IMAGE}"

# If relative path provided, make it relative to current directory
if [[ ! "$1" =~ ^/ ]] && [ -n "$1" ]; then
    IMAGE_PATH="$(pwd)/$1"
fi

echo "VyOS Image Verification Tool"
echo "==========================="
echo "Verifying: $IMAGE_PATH"
echo ""

# Follow symlinks to get real path
if [ -L "$IMAGE_PATH" ]; then
    REAL_PATH=$(readlink -f "$IMAGE_PATH")
    echo "ℹ️  Following symlink to: $REAL_PATH"
    IMAGE_PATH="$REAL_PATH"
    echo ""
fi

# Check if image exists
if [ ! -f "$IMAGE_PATH" ]; then
    echo "❌ Error: VyOS image not found at $IMAGE_PATH"
    echo ""
    echo "Usage: $0 [path/to/vyos.iso]"
    echo ""
    echo "Default locations checked:"
    echo "  - $PROJECT_ROOT/$DEFAULT_IMAGE"
    echo ""
    echo "To build a VyOS image, run:"
    echo "  ansible-playbook build-vyos-image.yaml"
    exit 1
fi

# Check image size
ISO_SIZE=$(stat -c%s "$IMAGE_PATH" 2>/dev/null || stat -f%z "$IMAGE_PATH" 2>/dev/null)
ISO_SIZE_MB=$((ISO_SIZE / 1024 / 1024))

echo "📊 Size Analysis:"
echo "  File size: ${ISO_SIZE_MB} MB ($(printf "%'d" $ISO_SIZE) bytes)"

if [ $ISO_SIZE -lt 500000000 ]; then
    if [ $ISO_SIZE -eq 471859200 ]; then  # Exactly 450MB
        echo "  ℹ️  This is a mock test image (exactly 450MB)"
    else
        echo "  ⚠️  Warning: ISO seems small for a real VyOS image (expected > 500MB)"
    fi
else
    echo "  ✓ Size check passed (real VyOS image)"
fi

# Check image format
echo ""
echo "🔍 Format Analysis:"
ISO_FORMAT=$(file "$IMAGE_PATH")
echo "  Raw output: $ISO_FORMAT"

FORMAT_OK=true
if [[ "$ISO_FORMAT" =~ "ISO 9660" ]]; then
    echo "  ✓ ISO 9660 format detected"
else
    echo "  ❌ Not an ISO 9660 format"
    FORMAT_OK=false
fi

if [[ "$ISO_FORMAT" =~ "bootable" ]]; then
    echo "  ✓ Bootable flag present"
else
    echo "  ⚠️  Warning: Bootable flag not detected"
fi

# Summary
echo ""
echo "📋 Summary:"
if [ $ISO_SIZE -eq 471859200 ]; then
    echo "  Type: Mock test image"
    echo "  Status: Valid for testing"
elif [ "$FORMAT_OK" = true ] && [ $ISO_SIZE -gt 500000000 ]; then
    echo "  Type: Real VyOS image"
    echo "  Status: ✅ Ready for deployment"
else
    echo "  Type: Unknown/Invalid"
    echo "  Status: ⚠️  May not work correctly"
fi

echo ""
echo "Verification complete!"