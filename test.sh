#!/bin/bash
# Test runner script for Ansible Molecule tests
# Handles environment setup, virtual environment, and directory navigation

set -e

# Load environment variables if .env exists
if [ -f .env ]; then
    # Export all non-comment lines from .env file
    set -a  # automatically export all variables
    source .env
    set +a  # turn off automatic export
fi

# Set molecule paths
VENV_PATH="/home/user/ansible-venv"
MOLECULE_BIN="${VENV_PATH}/bin/molecule"
TEST_DIR="collections/ansible_collections/homelab/nexus/extensions"
MOLECULE_DIR="$TEST_DIR/molecule"

# Add venv bin to PATH so ansible commands are available
export PATH="${VENV_PATH}/bin:$PATH"

# Set ANSIBLE environment variables if needed
export ANSIBLE_HOST_KEY_CHECKING=False

# Set VyOS image path for tests that need it
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export VYOS_IMAGE_PATH="${PROJECT_ROOT}/images/vyos"

# Function to check for valid real VyOS image (not mock)
check_vyos_image() {
    local image_path="${VYOS_IMAGE_PATH}/vyos-current.iso"
    local verify_script="${PROJECT_ROOT}/scripts/testing/verify-vyos-image.sh"
    
    if [ -f "$verify_script" ] && [ -f "$image_path" ]; then
        # Run verification script and check if it reports a real image
        local verify_output
        verify_output=$("$verify_script" "$image_path" 2>/dev/null)
        
        # Check if the output indicates a real VyOS image (not mock)
        if echo "$verify_output" | grep -q "Type: Real VyOS image"; then
            return 0  # Real VyOS image found
        fi
    fi
    return 1  # No valid real image found
}

# Determine test mode (will be set later after parsing args)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
PATTERN_MODE=false
DEBUG_MODE=false
FORCE_MOCK=false
FORCE_REAL=false

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

print_test() {
    echo -e "${CYAN}  →${NC} $1"
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
        if [ -d "$dir" ] && [ -f "$dir/molecule.yaml" ]; then
            test_name=$(basename "$dir")
            if [[ "$test_name" =~ $pattern ]]; then
                ((total_tests++))
                echo "----------------------------------------"
                print_info "Running test: $test_name"
                if run_single_test "$test_name"; then
                    passed_tests+=("$test_name")
                    print_info "✓ Test passed: $test_name"
                else
                    failed_tests+=("$test_name")
                    print_error "✗ Test failed: $test_name"
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
        print_info "Passed tests (${#passed_tests[@]}):"
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

# Function to run a single test
run_single_test() {
    local scenario="$1"
    local command="${2:-test}"
    
    local molecule_args=""
    if [ "$DEBUG_MODE" = true ]; then
        molecule_args="--debug"
    fi
    
    case "$command" in
        test)
            $MOLECULE_BIN test $molecule_args -s "$scenario"
            ;;
        syntax)
            $MOLECULE_BIN syntax $molecule_args -s "$scenario"
            ;;
        converge)
            $MOLECULE_BIN converge $molecule_args -s "$scenario"
            ;;
        verify)
            $MOLECULE_BIN verify $molecule_args -s "$scenario"
            ;;
        destroy)
            $MOLECULE_BIN destroy $molecule_args -s "$scenario"
            ;;
        *)
            print_error "Unknown test command: $command"
            return 1
            ;;
    esac
}

# Parse command line arguments
COMMAND=""
SCENARIO=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --pattern|-p)
            PATTERN_MODE=true
            shift
            ;;
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --mock)
            FORCE_MOCK=true
            shift
            ;;
        --real)
            FORCE_REAL=true
            shift
            ;;
        --help|-h)
            print_info "Usage: $0 [options] [command] [scenario]"
            echo ""
            echo "Commands:"
            echo "  list              List all available scenarios"
            echo "  test <scenario>   Run full test suite for a scenario"
            echo "  syntax <scenario> Run syntax check only"
            echo "  converge <scenario> Create and configure test instances"
            echo "  verify <scenario> Run verification tests"
            echo "  destroy <scenario> Destroy test instances"
            echo ""
            echo "Options:"
            echo "  --pattern, -p     Run tests matching pattern (use with scenario as pattern)"
            echo "  --debug           Enable molecule debug output"
            echo "  --mock            Force mock test mode (regardless of image availability)"
            echo "  --real            Force real test mode (requires valid VyOS image)"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 list"
            echo "  $0 test nexus.vyos.setup"
            echo "  $0 --pattern vyos                # Run all vyos tests"
            echo "  $0 --debug test nexus.vyos.vlans"
            echo "  $0 --mock test nexus.vyos.setup  # Force mock mode"
            echo "  $0 --real test nexus.vyos.setup  # Force real mode"
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            if [ -z "$COMMAND" ]; then
                COMMAND="$1"
            elif [ -z "$SCENARIO" ]; then
                SCENARIO="$1"
            else
                print_error "Too many arguments"
                exit 1
            fi
            shift
            ;;
    esac
done

# Set defaults
COMMAND=${COMMAND:-list}

# Determine test mode based on options and image availability
if [ "$FORCE_MOCK" = true ] && [ "$FORCE_REAL" = true ]; then
    print_error "Cannot use both --mock and --real options"
    exit 1
elif [ "$FORCE_MOCK" = true ]; then
    export VYOS_TEST_MODE="true"
    print_info "Forced mock test mode"
elif [ "$FORCE_REAL" = true ]; then
    if check_vyos_image; then
        export VYOS_TEST_MODE="false"
        print_info "Forced real test mode - using VyOS image"
    else
        print_error "No valid VyOS image found for real test mode"
        print_info "Run: ./scripts/build-vyos.sh to build an image"
        exit 1
    fi
else
    # Auto-detect test mode based on image availability
    if check_vyos_image; then
        export VYOS_TEST_MODE="false"
        print_info "Real VyOS image detected - running full tests"
    else
        export VYOS_TEST_MODE="true"
        print_info "No real VyOS image found - using mock tests"
    fi
fi

# Change to test directory
cd "$TEST_DIR" || {
    print_error "Failed to change to test directory: $TEST_DIR"
    exit 1
}

print_info "Current directory: $(pwd)"

# Handle pattern mode
if [ "$PATTERN_MODE" = true ]; then
    if [ -z "$COMMAND" ]; then
        print_error "Pattern required when using --pattern"
        print_info "Usage: $0 --pattern <pattern>"
        exit 1
    fi
    run_pattern_tests "$COMMAND"
    exit $?
fi

# Execute molecule command
case "$COMMAND" in
    list)
        print_info "Listing all molecule scenarios..."
        if [ -d "$MOLECULE_DIR" ]; then
            echo ""
            local test_count=0
            for dir in "$MOLECULE_DIR"/*; do
                if [ -d "$dir" ] && [ -f "$dir/molecule.yaml" ]; then
                    test_name=$(basename "$dir")
                    print_test "$test_name"
                    ((test_count++))
                fi
            done
            echo ""
            print_info "Total tests found: $test_count"
        else
            $MOLECULE_BIN list
        fi
        ;;
    test|syntax|converge|verify|destroy)
        if [ -z "$SCENARIO" ]; then
            print_error "Please specify a scenario name for $COMMAND"
            print_info "Usage: $0 $COMMAND <scenario-name>"
            print_info "Run '$0 list' to see available scenarios"
            exit 1
        fi
        print_info "Running $COMMAND for scenario: $SCENARIO"
        run_single_test "$SCENARIO" "$COMMAND"
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        echo "Usage: $0 [options] [command] [scenario]"
        echo ""
        echo "Commands:"
        echo "  list              List all available scenarios"
        echo "  test <scenario>   Run full test suite for a scenario"
        echo "  syntax <scenario> Run syntax check only"
        echo "  converge <scenario> Create and configure test instances"
        echo "  verify <scenario> Run verification tests"
        echo "  destroy <scenario> Destroy test instances"
        echo ""
        echo "Options:"
        echo "  --pattern, -p     Run tests matching pattern"
        echo "  --debug           Enable molecule debug output"
        echo "  --help, -h        Show detailed help"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 test nexus.vyos.setup"
        echo "  $0 --pattern vyos"
        echo "  $0 --debug test nexus.vyos.vlans"
        exit 1
        ;;
esac