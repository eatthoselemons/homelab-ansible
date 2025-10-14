#!/bin/bash
# Integration testing framework for homelab infrastructure
# This implements sectioned testing with real VMs as per docs/llms/design/testing-strategy.md

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/test-integration-config.yaml"
TESTS_DIR="${SCRIPT_DIR}/tests"
VAGRANT_DIR="${TESTS_DIR}/vagrant"
VALIDATION_DIR="${TESTS_DIR}/validation"
INVENTORY_DIR="${TESTS_DIR}/inventory"
LOGS_DIR="${TESTS_DIR}/logs"

# Default values
VM_BACKEND="libvirt"
CLEANUP=true
PARALLEL=false
SECTIONS=()
RUN_ALL=false
RUN_QUICK=false

# Timing
START_TIME=$(date +%s)

# Logging
mkdir -p "$LOGS_DIR"
LOG_FILE="${LOGS_DIR}/test-integration-$(date +%Y%m%d-%H%M%S).log"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Integration testing for homelab infrastructure using real VMs.

OPTIONS:
    --section <name>     Run specific test section (can be specified multiple times)
    --all               Run all test sections
    --quick             Run only quick tests (< 10 minutes)
    --backend <type>    VM backend to use (libvirt, virtualbox, vagrant) [default: libvirt]
    --no-cleanup        Keep VMs after tests for debugging
    --parallel          Run tests in parallel (experimental)
    --list              List available test sections
    --help              Show this help message

EXAMPLES:
    $0 --section networking
    $0 --section networking --section storage
    $0 --all
    $0 --quick
    $0 --section harvester_cluster --no-cleanup

For more information, see docs/llms/design/testing-strategy.md
EOF
}

list_sections() {
    log_info "Available test sections:"
    if [[ -f "$CONFIG_FILE" ]]; then
        # Parse sections from YAML config
        python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
    if 'sections' in config:
        for name, section in config['sections'].items():
            print(f\"  {name:20} - {section.get('description', 'No description')} ({section.get('estimated_time', 'Unknown time')})\")"
    else
        log_warning "Config file not found. Creating default configuration..."
        create_default_config
        list_sections
    fi
}

create_default_config() {
    log_info "Creating default test configuration..."
    cat > "$CONFIG_FILE" << 'EOF'
# Integration test configuration
# See docs/llms/design/testing-strategy.md for details

test_defaults:
  vm_backend: libvirt
  base_image: ubuntu-24.04-cloud
  cleanup: true
  parallel_execution: false

sections:
  networking:
    description: "Network bonds, VLANs, bridges"
    playbook: site.yml
    tags: [networking]
    inventory: test-inventory/networking
    validate_script: validation/validate-networking.sh
    required_vms: 1
    estimated_time: "5 minutes"
    requires_nested_virt: false
    
  storage:
    description: "LVM, filesystem, mounts"
    playbook: site.yml
    tags: [storage]
    inventory: test-inventory/storage
    validate_script: validation/validate-storage.sh
    required_vms: 1
    estimated_time: "5 minutes"
    requires_nested_virt: false
    
  vyos_config:
    description: "VyOS router configuration"
    playbook: site.yml
    tags: [vyos]
    inventory: test-inventory/vyos
    validate_script: validation/validate-vyos.sh
    required_vms: 1
    estimated_time: "10 minutes"
    requires_nested_virt: true
    
  harvester_single:
    description: "Single node Harvester setup"
    playbook: site.yml
    tags: [harvester]
    inventory: test-inventory/single-node
    validate_script: validation/validate-harvester-single.sh
    required_vms: 1
    estimated_time: "15 minutes"
    requires_nested_virt: true
    
  harvester_cluster:
    description: "3-node Harvester cluster"
    playbook: site.yml
    tags: [harvester]
    inventory: test-inventory/cluster
    validate_script: validation/validate-harvester-cluster.sh
    required_vms: 3
    estimated_time: "30 minutes"
    requires_nested_virt: true
EOF
    log_success "Created $CONFIG_FILE"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    # Check for required commands
    for cmd in vagrant ansible python3 virsh; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        fi
    done
    
    # Check for Python YAML module
    if ! python3 -c "import yaml" &> /dev/null; then
        missing_deps+=("python3-yaml")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install missing dependencies and try again."
        exit 1
    fi
    
    # Check KVM if using libvirt
    if [[ "$VM_BACKEND" == "libvirt" ]]; then
        if [[ ! -e /dev/kvm ]]; then
            log_warning "KVM not available. Performance will be degraded."
        fi
    fi
    
    log_success "All dependencies satisfied"
}

setup_test_environment() {
    log_info "Setting up test environment..."
    
    # Create necessary directories
    mkdir -p "$VAGRANT_DIR"
    mkdir -p "$VALIDATION_DIR" 
    mkdir -p "$INVENTORY_DIR"
    mkdir -p "$LOGS_DIR"
    
    # Create Vagrant configuration if not exists
    if [[ ! -f "$VAGRANT_DIR/Vagrantfile" ]]; then
        create_vagrantfile
    fi
    
    log_success "Test environment ready"
}

create_vagrantfile() {
    log_info "Creating Vagrantfile..."
    cat > "$VAGRANT_DIR/Vagrantfile" << 'EOF'
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # Base box
  config.vm.box = "generic/ubuntu2404"
  
  # VM configuration
  config.vm.provider :libvirt do |libvirt|
    libvirt.memory = 4096
    libvirt.cpus = 2
    libvirt.nested = true
    libvirt.cpu_mode = "host-passthrough"
  end
  
  config.vm.provider :virtualbox do |vb|
    vb.memory = 4096
    vb.cpus = 2
    vb.customize ["modifyvm", :id, "--nested-hw-virt", "on"]
  end
  
  # Test VM definitions will be added dynamically
end
EOF
    log_success "Created Vagrantfile"
}

provision_vms() {
    local section=$1
    log_info "Provisioning VMs for section: $section"
    
    # Get VM requirements from config
    local vm_count=$(python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
    print(config['sections'].get('$section', {}).get('required_vms', 1))")
    
    log_info "Provisioning $vm_count VM(s)..."
    
    cd "$VAGRANT_DIR"
    
    # Generate dynamic Vagrantfile for this section
    generate_section_vagrantfile "$section" "$vm_count"
    
    # Start VMs
    vagrant up --provider="$VM_BACKEND" 2>&1 | tee -a "$LOG_FILE"
    
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        log_error "Failed to provision VMs"
        return 1
    fi
    
    log_success "VMs provisioned successfully"
    cd "$SCRIPT_DIR"
}

generate_section_vagrantfile() {
    local section=$1
    local vm_count=$2
    
    cat > "$VAGRANT_DIR/Vagrantfile" << EOF
# -*- mode: ruby -*-
# vi: set ft=ruby :
# Generated for test section: $section

Vagrant.configure("2") do |config|
  config.vm.box = "generic/ubuntu2404"
  
  (1..$vm_count).each do |i|
    config.vm.define "test-${section}-#{i}" do |node|
      node.vm.hostname = "test-${section}-#{i}"
      node.vm.network "private_network", type: "dhcp"
      
      node.vm.provider :libvirt do |libvirt|
        libvirt.memory = 4096
        libvirt.cpus = 2
        libvirt.nested = true
        libvirt.cpu_mode = "host-passthrough"
      end
      
      node.vm.provider :virtualbox do |vb|
        vb.memory = 4096
        vb.cpus = 2
        vb.customize ["modifyvm", :id, "--nested-hw-virt", "on"]
      end
      
      # Basic provisioning
      node.vm.provision "shell", inline: <<-SHELL
        apt-get update
        apt-get install -y python3 python3-pip
      SHELL
    end
  end
end
EOF
}

run_ansible_playbook() {
    local section=$1
    log_info "Running Ansible playbook for section: $section"
    
    # Get playbook and tags from config
    local playbook=$(python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
    print(config['sections'].get('$section', {}).get('playbook', 'site.yml'))")
    
    local tags=$(python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
    tags = config['sections'].get('$section', {}).get('tags', [])
    print(','.join(tags))")
    
    # Generate inventory
    generate_test_inventory "$section"
    
    # Run playbook
    ansible-playbook \
        -i "${INVENTORY_DIR}/${section}.ini" \
        --tags "$tags" \
        "$playbook" 2>&1 | tee -a "$LOG_FILE"
    
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        log_error "Ansible playbook failed"
        return 1
    fi
    
    log_success "Ansible playbook completed"
}

generate_test_inventory() {
    local section=$1
    
    # Get VM SSH config from Vagrant
    cd "$VAGRANT_DIR"
    vagrant ssh-config > "${INVENTORY_DIR}/${section}-ssh.conf"
    
    # Generate Ansible inventory
    cat > "${INVENTORY_DIR}/${section}.ini" << EOF
[test_nodes]
EOF
    
    # Add each VM to inventory
    vagrant status --machine-readable | grep ",state," | grep running | cut -d',' -f2 | while read vm; do
        local port=$(vagrant ssh-config $vm | grep Port | awk '{print $2}')
        local key=$(vagrant ssh-config $vm | grep IdentityFile | awk '{print $2}')
        echo "$vm ansible_host=127.0.0.1 ansible_port=$port ansible_user=vagrant ansible_ssh_private_key_file=$key" >> "${INVENTORY_DIR}/${section}.ini"
    done
    
    cd "$SCRIPT_DIR"
}

run_validation() {
    local section=$1
    log_info "Running validation for section: $section"
    
    # Check if Python test dependencies are installed
    if ! python3 -c "import pytest; import testinfra" &> /dev/null; then
        log_warning "Python test dependencies not installed"
        log_info "Installing test dependencies..."
        pip3 install -r "${TESTS_DIR}/requirements.txt" --user
    fi
    
    # Run Python-based validation using pytest and testinfra
    local test_runner="${TESTS_DIR}/run-integration-tests.py"
    
    if [[ ! -f "$test_runner" ]]; then
        log_error "Test runner not found: $test_runner"
        return 1
    fi
    
    # Run validation with pytest
    python3 "$test_runner" \
        --section "$section" \
        --inventory "${INVENTORY_DIR}/${section}.ini" \
        --timeout 120 \
        2>&1 | tee -a "$LOG_FILE"
    
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        log_error "Validation failed"
        return 1
    fi
    
    log_success "Validation passed"
}

create_placeholder_validation() {
    local section=$1
    local script_path=$2
    
    mkdir -p "$(dirname "$script_path")"
    
    cat > "$script_path" << 'EOF'
#!/bin/bash
# Placeholder validation script
# TODO: Implement actual validation

set -e

INVENTORY=$1

echo "=== VALIDATION STARTING ==="
echo "Section: SECTION_NAME"
echo "Inventory: $INVENTORY"

# Add actual validation here
echo "⚠️  Using placeholder validation - implement actual checks!"

echo "✅ VALIDATION COMPLETE (placeholder)"
EOF
    
    sed -i "s/SECTION_NAME/$section/g" "$script_path"
    chmod +x "$script_path"
}

cleanup_vms() {
    local section=$1
    
    if [[ "$CLEANUP" == "false" ]]; then
        log_info "Skipping cleanup (--no-cleanup specified)"
        return 0
    fi
    
    log_info "Cleaning up VMs..."
    
    cd "$VAGRANT_DIR"
    vagrant destroy -f 2>&1 | tee -a "$LOG_FILE"
    cd "$SCRIPT_DIR"
    
    log_success "VMs cleaned up"
}

run_section_test() {
    local section=$1
    
    echo
    echo "=========================================="
    log_info "RUNNING TEST SECTION: $section"
    echo "=========================================="
    
    local section_start=$(date +%s)
    
    # Run test phases
    provision_vms "$section" || return 1
    run_ansible_playbook "$section" || return 1
    run_validation "$section" || return 1
    cleanup_vms "$section"
    
    local section_end=$(date +%s)
    local section_duration=$((section_end - section_start))
    
    log_success "Section $section completed in ${section_duration} seconds"
    
    return 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --section)
            SECTIONS+=("$2")
            shift 2
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --quick)
            RUN_QUICK=true
            shift
            ;;
        --backend)
            VM_BACKEND="$2"
            shift 2
            ;;
        --no-cleanup)
            CLEANUP=false
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --list)
            list_sections
            exit 0
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    log_info "Starting integration tests"
    log_info "Configuration: backend=$VM_BACKEND, cleanup=$CLEANUP, parallel=$PARALLEL"
    
    # Check dependencies
    check_dependencies
    
    # Setup environment
    setup_test_environment
    
    # Create config if not exists
    if [[ ! -f "$CONFIG_FILE" ]]; then
        create_default_config
    fi
    
    # Determine which sections to run
    if [[ "$RUN_ALL" == "true" ]]; then
        # Get all sections from config
        SECTIONS=($(python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
    print(' '.join(config.get('sections', {}).keys()))"))
    elif [[ "$RUN_QUICK" == "true" ]]; then
        # Get only quick sections (< 10 minutes)
        SECTIONS=($(python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
    quick = []
    for name, section in config.get('sections', {}).items():
        time = section.get('estimated_time', '0 minutes')
        if 'minute' in time:
            minutes = int(time.split()[0])
            if minutes < 10:
                quick.append(name)
    print(' '.join(quick))"))
    fi
    
    if [[ ${#SECTIONS[@]} -eq 0 ]]; then
        log_error "No test sections specified"
        log_info "Use --section, --all, or --quick to specify tests"
        show_usage
        exit 1
    fi
    
    log_info "Will run sections: ${SECTIONS[*]}"
    
    # Run tests
    local failed_sections=()
    
    for section in "${SECTIONS[@]}"; do
        if run_section_test "$section"; then
            log_success "✅ Section passed: $section"
        else
            log_error "❌ Section failed: $section"
            failed_sections+=("$section")
        fi
    done
    
    # Summary
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo
    echo "=========================================="
    log_info "TEST SUMMARY"
    echo "=========================================="
    log_info "Total duration: ${DURATION} seconds"
    log_info "Sections run: ${#SECTIONS[@]}"
    
    if [[ ${#failed_sections[@]} -eq 0 ]]; then
        log_success "✅ ALL TESTS PASSED"
        exit 0
    else
        log_error "❌ FAILED SECTIONS: ${failed_sections[*]}"
        log_info "Check logs at: $LOG_FILE"
        exit 1
    fi
}

# Run main function
main