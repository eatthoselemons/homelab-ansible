#!/bin/bash
# Networking validation wrapper script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="${SCRIPT_DIR}/validator.py"
INVENTORY="$1"

if [[ -z "$INVENTORY" ]]; then
    echo "Usage: $0 <inventory-file>"
    exit 1
fi

echo "=== NETWORKING VALIDATION STARTING ==="
echo "Inventory: $INVENTORY"

# Run Python validator
python3 "$VALIDATOR" networking "$INVENTORY"

exit $?