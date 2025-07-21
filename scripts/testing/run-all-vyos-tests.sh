#!/bin/bash
# Enhanced VyOS test runner with environment detection and smart test execution
# This script runs all VyOS-related tests with proper environment setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_DIR="$PROJECT_ROOT/collections/ansible_collections/homelab/nexus/extensions"
VENV_PATH="/home/user/ansible-venv"

# VyOS test scenarios
VYOS_TESTS=(
    "nexus.vyos.setup"
    "nexus.vyos.vlans"
    "nexus.vyos.security_hardening"
    "nexus.vyos.image_builder"
    "nexus.vyos.full_integration"
)

# Test categories
UNIT_TESTS=()
INTEGRATION_TESTS=("nexus.vyos.setup" "nexus.vyos.vlans" "nexus.vyos.security_hardening")
FULL_TESTS=("nexus.vyos.image_builder" "nexus.vyos.full_integration")

# Default values
RUN_MODE="auto"
FORCE_FULL=false
DRY_RUN=false
SPECIFIC_TEST=""

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

print_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

detect_environment() {
    local env_type="bare-metal"
    
    # Check if running in Docker
    if [ -f /.dockerenv ]; then
        env_type="docker"
    elif grep -q docker /proc/1/cgroup 2>/dev/null; then
        env_type="docker"
    fi
    
    # Check if KVM is available
    local kvm_available=false
    if [ -e /dev/kvm ]; then
        kvm_available=true
    fi
    
    # Check if running with privileges
    local privileged=false
    if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
        privileged=true
    fi
    
    echo "$env_type|$kvm_available|$privileged"
}

show_help() {
    cat << EOF
Enhanced VyOS Test Runner

Usage: $0 [OPTIONS] [test-name]

Options:
    -m, --mode MODE       Test mode: auto, unit, integration, full (default: auto)
    -f, --force-full      Force full test execution even in containers
    -d, --dry-run         Show what would be run without executing
    -h, --help            Show this help message

Test Modes:
    auto         Automatically detect environment and run appropriate tests
    unit         Run only unit tests (safe in containers)
    integration  Run integration tests (requires some privileges)
    full         Run all tests including those requiring KVM/libvirt

Examples:
    # Auto-detect and run appropriate tests
    $0

    # Run only unit tests
    $0 --mode unit

    # Run a specific test
    $0 nexus.vyos.setup

    # Dry run to see what would execute
    $0 --dry-run

Environment Detection:
    The script automatically detects:
    - Container vs bare metal environment
    - KVM availability
    - Privilege level
    
    And adjusts test execution accordingly.

EOF
}

check_vyos_image() {
    local image_path="$PROJECT_ROOT/images/vyos/vyos-current.iso"
    
    if [ -f "$image_path" ]; then
        local size=$(stat -c%s "$image_path" 2>/dev/null || stat -f%z "$image_path" 2>/dev/null)
        local size_mb=$((size / 1024 / 1024))
        print_info "VyOS image found: $image_path (${size_mb}MB)"
        
        # Check if it's a test image (exactly 450MB)
        if [ "$size_mb" -eq 450 ]; then
            print_warning "Detected test VyOS image (450MB)"
            return 1
        fi
        return 0
    else
        print_warning "VyOS image not found at: $image_path"
        return 2
    fi
}

setup_environment() {
    # Export paths
    export PATH="$VENV_PATH/bin:$PATH"
    export VYOS_IMAGE_PATH="$PROJECT_ROOT/images/vyos"
    
    # Load .env if exists
    if [ -f "$PROJECT_ROOT/.env" ]; then
        print_info "Loading environment from .env"
        export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
    fi
    
    # Set Ansible environment
    export ANSIBLE_HOST_KEY_CHECKING=False
    export ANSIBLE_STDOUT_CALLBACK=yaml
    
    print_info "Environment configured:"
    echo "  VYOS_IMAGE_PATH: $VYOS_IMAGE_PATH"
    echo "  Virtual env: $VENV_PATH"
}

run_test() {
    local test_name="$1"
    local test_mode="$2"
    
    print_test "Running $test_name in $test_mode mode"
    
    if [ "$DRY_RUN" = true ]; then
        echo "  Would run: $PROJECT_ROOT/test.sh test $test_name"
        return 0
    fi
    
    cd "$PROJECT_ROOT"
    
    # Run the test
    if ./test.sh test "$test_name"; then
        print_success "$test_name passed"
        return 0
    else
        print_error "$test_name failed"
        return 1
    fi
}

select_tests() {
    local env_info="$1"
    local env_type=$(echo "$env_info" | cut -d'|' -f1)
    local kvm_available=$(echo "$env_info" | cut -d'|' -f2)
    local privileged=$(echo "$env_info" | cut -d'|' -f3)
    
    local selected_tests=()
    
    case "$RUN_MODE" in
        auto)
            if [ "$env_type" = "docker" ] && [ "$kvm_available" = "false" ]; then
                print_info "Container environment without KVM - running unit tests only"
                selected_tests=("${UNIT_TESTS[@]}")
            elif [ "$privileged" = "true" ] || [ "$kvm_available" = "true" ]; then
                print_info "Privileged environment - running all tests"
                selected_tests=("${VYOS_TESTS[@]}")
            else
                print_info "Unprivileged environment - running unit and basic integration tests"
                selected_tests=("${UNIT_TESTS[@]}" "${INTEGRATION_TESTS[@]}")
            fi
            ;;
        unit)
            selected_tests=("${UNIT_TESTS[@]}")
            ;;
        integration)
            selected_tests=("${INTEGRATION_TESTS[@]}")
            ;;
        full)
            selected_tests=("${VYOS_TESTS[@]}")
            ;;
    esac
    
    echo "${selected_tests[@]}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            RUN_MODE="$2"
            shift 2
            ;;
        -f|--force-full)
            FORCE_FULL=true
            RUN_MODE="full"
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            SPECIFIC_TEST="$1"
            shift
            ;;
    esac
done

# Main execution
print_info "VyOS Test Runner Starting..."
echo ""

# Detect environment
env_info=$(detect_environment)
env_type=$(echo "$env_info" | cut -d'|' -f1)
kvm_available=$(echo "$env_info" | cut -d'|' -f2)
privileged=$(echo "$env_info" | cut -d'|' -f3)

print_info "Environment Detection:"
echo "  Type: $env_type"
echo "  KVM Available: $kvm_available"
echo "  Privileged: $privileged"
echo ""

# Check VyOS image
image_status=$(check_vyos_image)
image_result=$?

# Setup environment
setup_environment

# Select tests to run
if [ -n "$SPECIFIC_TEST" ]; then
    tests_to_run=("$SPECIFIC_TEST")
    print_info "Running specific test: $SPECIFIC_TEST"
else
    tests_to_run=($(select_tests "$env_info"))
    print_info "Selected ${#tests_to_run[@]} tests based on environment"
fi

# Check if we can run the selected tests
if [ "$RUN_MODE" = "full" ] || [[ " ${FULL_TESTS[@]} " =~ " ${tests_to_run[0]} " ]]; then
    if [ "$image_result" -ne 0 ] && [ "$FORCE_FULL" = false ]; then
        print_error "Full tests require a real VyOS image"
        print_info "Run '$PROJECT_ROOT/scripts/build-vyos.sh' to build one"
        exit 1
    fi
fi

# Run tests
echo ""
print_info "Running Tests..."
echo "========================================"

passed=0
failed=0
skipped=0

for test in "${tests_to_run[@]}"; do
    echo ""
    echo "----------------------------------------"
    
    # Determine test type
    if [[ " ${UNIT_TESTS[@]} " =~ " $test " ]]; then
        test_type="unit"
    elif [[ " ${INTEGRATION_TESTS[@]} " =~ " $test " ]]; then
        test_type="integration"
    else
        test_type="full"
    fi
    
    # Check if we can run this test type
    can_run=true
    if [ "$test_type" = "full" ] && [ "$kvm_available" = "false" ] && [ "$FORCE_FULL" = false ]; then
        print_warning "Skipping $test - requires KVM"
        ((skipped++))
        continue
    fi
    
    # Run the test
    if run_test "$test" "$test_type"; then
        ((passed++))
    else
        ((failed++))
    fi
done

# Summary
echo ""
echo "========================================"
print_info "Test Summary"
echo "========================================"
echo "Total: $((passed + failed + skipped))"
echo -e "Passed: ${GREEN}$passed${NC}"
echo -e "Failed: ${RED}$failed${NC}"
echo -e "Skipped: ${YELLOW}$skipped${NC}"
echo ""

# Exit code
if [ "$failed" -gt 0 ]; then
    print_error "Some tests failed"
    exit 1
else
    print_success "All tests completed successfully!"
    exit 0
fi