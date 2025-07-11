#!/bin/bash
#
# run-molecule-test.sh - Run specific molecule tests for homelab-ansible
#
# DESCRIPTION:
#   This script provides a convenient way to run specific molecule tests
#   or test patterns from the homelab.nexus collection. It can list all
#   available tests, run specific tests, or run tests matching a pattern.
#
# USAGE:
#   ./run-molecule-test.sh [options] [test-name|pattern]
#
# OPTIONS:
#   --list, -l         List all available molecule tests
#   --pattern, -p      Run all tests matching the pattern
#   --syntax-only      Only run syntax check (no converge)
#   --converge-only    Only run converge (no verify)
#   --debug            Enable molecule debug output
#   --help, -h         Show this help message
#
# EXAMPLES:
#   # List all available tests
#   ./run-molecule-test.sh --list
#
#   # Run a specific test
#   ./run-molecule-test.sh nexus.vyos.setup
#
#   # Run all VyOS-related tests
#   ./run-molecule-test.sh --pattern vyos
#
#   # Run syntax check only
#   ./run-molecule-test.sh --syntax-only nexus.vyos.vlans
#
#   # Run with debug output
#   ./run-molecule-test.sh --debug nexus.vyos.security_hardening
#
# EXIT CODES:
#   0 - All tests passed
#   1 - One or more tests failed
#   2 - Invalid arguments or prerequisites missing
#

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MOLECULE_DIR="$PROJECT_ROOT/collections/ansible_collections/homelab/nexus/extensions/molecule"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
LIST_TESTS=false
PATTERN_MODE=false
SYNTAX_ONLY=false
CONVERGE_ONLY=false
DEBUG_MODE=false
TEST_PATTERN=""
SPECIFIC_TEST=""

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

print_test() {
    echo -e "${CYAN}  →${NC} $1"
}

# Function to show help
show_help() {
    # Extract header comments between lines 2-38
    sed -n '2,38p' "$0" | grep '^#' | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# Function to list available tests
list_tests() {
    echo ""
    echo "Available Molecule Tests"
    echo "========================"
    echo ""
    
    if [ ! -d "$MOLECULE_DIR" ]; then
        print_error "Molecule directory not found: $MOLECULE_DIR"
        exit 2
    fi
    
    # Find all directories with molecule.yml
    local test_count=0
    for dir in "$MOLECULE_DIR"/*; do
        if [ -d "$dir" ] && [ -f "$dir/molecule.yml" ]; then
            test_name=$(basename "$dir")
            print_test "$test_name"
            ((test_count++))
        fi
    done
    
    echo ""
    print_info "Total tests found: $test_count"
    echo ""
    print_info "Run a specific test with: $0 <test-name>"
    print_info "Run tests matching pattern with: $0 --pattern <pattern>"
    echo ""
}

# Function to run a specific test
run_test() {
    local test_name="$1"
    local test_dir="$MOLECULE_DIR/$test_name"
    
    if [ ! -d "$test_dir" ]; then
        print_error "Test not found: $test_name"
        print_info "Use --list to see available tests"
        return 1
    fi
    
    if [ ! -f "$test_dir/molecule.yml" ]; then
        print_error "No molecule.yml found in $test_dir"
        return 1
    fi
    
    print_status "Running test: $test_name"
    
    cd "$PROJECT_ROOT/collections/ansible_collections/homelab/nexus/extensions"
    
    local molecule_cmd="molecule"
    local molecule_args=""
    
    if [ "$DEBUG_MODE" = true ]; then
        molecule_args="--debug"
    fi
    
    if [ "$SYNTAX_ONLY" = true ]; then
        print_info "Running syntax check only..."
        if $molecule_cmd syntax $molecule_args -s "$test_name"; then
            print_status "✓ Syntax check passed: $test_name"
            return 0
        else
            print_error "✗ Syntax check failed: $test_name"
            return 1
        fi
    elif [ "$CONVERGE_ONLY" = true ]; then
        print_info "Running converge only..."
        if $molecule_cmd converge $molecule_args -s "$test_name"; then
            print_status "✓ Converge passed: $test_name"
            return 0
        else
            print_error "✗ Converge failed: $test_name"
            return 1
        fi
    else
        # Run full test
        if $molecule_cmd test $molecule_args -s "$test_name"; then
            print_status "✓ Test passed: $test_name"
            return 0
        else
            print_error "✗ Test failed: $test_name"
            return 1
        fi
    fi
}

# Function to run tests matching a pattern
run_pattern_tests() {
    local pattern="$1"
    local failed_tests=()
    local passed_tests=()
    local total_tests=0
    
    print_info "Running tests matching pattern: $pattern"
    echo ""
    
    # Find all tests matching the pattern
    for dir in "$MOLECULE_DIR"/*; do
        if [ -d "$dir" ] && [ -f "$dir/molecule.yml" ]; then
            test_name=$(basename "$dir")
            if [[ "$test_name" =~ $pattern ]]; then
                ((total_tests++))
                echo "----------------------------------------"
                if run_test "$test_name"; then
                    passed_tests+=("$test_name")
                else
                    failed_tests+=("$test_name")
                fi
                echo ""
            fi
        fi
    done
    
    # Summary
    echo "========================================"
    print_info "Test Summary"
    echo "========================================"
    echo ""
    
    if [ ${#passed_tests[@]} -gt 0 ]; then
        print_status "Passed tests (${#passed_tests[@]}):"
        for test in "${passed_tests[@]}"; do
            echo "  ✓ $test"
        done
    fi
    
    if [ ${#failed_tests[@]} -gt 0 ]; then
        echo ""
        print_error "Failed tests (${#failed_tests[@]}):"
        for test in "${failed_tests[@]}"; do
            echo "  ✗ $test"
        done
    fi
    
    echo ""
    print_info "Total: $total_tests | Passed: ${#passed_tests[@]} | Failed: ${#failed_tests[@]}"
    echo ""
    
    if [ ${#failed_tests[@]} -gt 0 ]; then
        return 1
    fi
    
    return 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --list|-l)
            LIST_TESTS=true
            shift
            ;;
        --pattern|-p)
            PATTERN_MODE=true
            shift
            ;;
        --syntax-only)
            SYNTAX_ONLY=true
            shift
            ;;
        --converge-only)
            CONVERGE_ONLY=true
            shift
            ;;
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --help|-h)
            show_help
            ;;
        -*)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 2
            ;;
        *)
            # This is either a test name or pattern
            if [ "$PATTERN_MODE" = true ]; then
                TEST_PATTERN="$1"
            else
                SPECIFIC_TEST="$1"
            fi
            shift
            ;;
    esac
done

# Check prerequisites
if ! command -v molecule &> /dev/null; then
    print_error "molecule is not installed or not in PATH"
    print_info "Install with: pip install molecule[docker]"
    exit 2
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 2
fi

# Main logic
if [ "$LIST_TESTS" = true ]; then
    list_tests
elif [ "$PATTERN_MODE" = true ]; then
    if [ -z "$TEST_PATTERN" ]; then
        print_error "Pattern required when using --pattern"
        echo "Usage: $0 --pattern <pattern>"
        exit 2
    fi
    run_pattern_tests "$TEST_PATTERN"
elif [ -n "$SPECIFIC_TEST" ]; then
    run_test "$SPECIFIC_TEST"
else
    # No arguments provided, show help
    print_error "No test specified"
    echo ""
    echo "Usage: $0 [options] [test-name|pattern]"
    echo "Use --help for detailed usage information"
    echo "Use --list to see available tests"
    exit 2
fi