#!/bin/bash
# VyOS validation wrapper script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="${SCRIPT_DIR}/validator.py"
INVENTORY="$1"

if [[ -z "$INVENTORY" ]]; then
    echo "Usage: $0 <inventory-file>"
    exit 1
fi

echo "=== VYOS VALIDATION STARTING ==="
echo "Inventory: $INVENTORY"

# Run Python validator for vyos
python3 "$VALIDATOR" vyos "$INVENTORY"

exit $?