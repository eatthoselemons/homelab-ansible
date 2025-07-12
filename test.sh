#!/bin/bash
# Test runner script for Ansible Molecule tests
# Handles environment setup, virtual environment, and directory navigation

set -e

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set molecule paths
VENV_PATH="/home/user/ansible-venv"
MOLECULE_BIN="${VENV_PATH}/bin/molecule"
TEST_DIR="collections/ansible_collections/homelab/nexus/extensions"

# Add venv bin to PATH so ansible commands are available
export PATH="${VENV_PATH}/bin:$PATH"

# Set ANSIBLE environment variables if needed
export ANSIBLE_HOST_KEY_CHECKING=False

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    print_error "Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Check if molecule is installed
if [ ! -f "$MOLECULE_BIN" ]; then
    print_error "Molecule not found at $MOLECULE_BIN"
    exit 1
fi

# Parse command line arguments
COMMAND=${1:-list}
SCENARIO=${2:-}

# Change to test directory
cd "$TEST_DIR" || {
    print_error "Failed to change to test directory: $TEST_DIR"
    exit 1
}

print_info "Current directory: $(pwd)"

# Execute molecule command
case "$COMMAND" in
    list)
        print_info "Listing all molecule scenarios..."
        $MOLECULE_BIN list
        ;;
    test)
        if [ -z "$SCENARIO" ]; then
            print_error "Please specify a scenario name for testing"
            print_info "Usage: $0 test <scenario-name>"
            print_info "Run '$0 list' to see available scenarios"
            exit 1
        fi
        print_info "Running full test for scenario: $SCENARIO"
        $MOLECULE_BIN test -s "$SCENARIO"
        ;;
    syntax)
        if [ -z "$SCENARIO" ]; then
            print_error "Please specify a scenario name for syntax check"
            print_info "Usage: $0 syntax <scenario-name>"
            exit 1
        fi
        print_info "Running syntax check for scenario: $SCENARIO"
        $MOLECULE_BIN syntax -s "$SCENARIO"
        ;;
    converge)
        if [ -z "$SCENARIO" ]; then
            print_error "Please specify a scenario name for converge"
            print_info "Usage: $0 converge <scenario-name>"
            exit 1
        fi
        print_info "Running converge for scenario: $SCENARIO"
        $MOLECULE_BIN converge -s "$SCENARIO"
        ;;
    verify)
        if [ -z "$SCENARIO" ]; then
            print_error "Please specify a scenario name for verify"
            print_info "Usage: $0 verify <scenario-name>"
            exit 1
        fi
        print_info "Running verify for scenario: $SCENARIO"
        $MOLECULE_BIN verify -s "$SCENARIO"
        ;;
    destroy)
        if [ -z "$SCENARIO" ]; then
            print_error "Please specify a scenario name for destroy"
            print_info "Usage: $0 destroy <scenario-name>"
            exit 1
        fi
        print_info "Destroying test environment for scenario: $SCENARIO"
        $MOLECULE_BIN destroy -s "$SCENARIO"
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        echo "Usage: $0 [command] [scenario]"
        echo ""
        echo "Commands:"
        echo "  list              List all available scenarios"
        echo "  test <scenario>   Run full test suite for a scenario"
        echo "  syntax <scenario> Run syntax check only"
        echo "  converge <scenario> Create and configure test instances"
        echo "  verify <scenario> Run verification tests"
        echo "  destroy <scenario> Destroy test instances"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 test vyos"
        echo "  $0 converge docker"
        exit 1
        ;;
esac