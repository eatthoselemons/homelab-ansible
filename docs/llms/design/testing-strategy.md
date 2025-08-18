# Testing Strategy for Homelab Infrastructure

## Core Philosophy

**Infrastructure code is about side effects**. Testing it without those side effects is meaningless ceremony. We explicitly reject the notion of "unit testing" infrastructure code with heavy mocking.

### Key Principles

1. **No mock infrastructure** - If you're mocking networks, storage, or services, stop
2. **Test at the right level** - Use appropriate tools for each testing layer
3. **Real validation only** - Tests must verify actual functionality, not mocked behavior
4. **Progressive validation** - Fast failures for quick feedback
5. **One test path** - No shortcuts or "smoke tests" that can be abused

## Testing Pyramid

```
Production Deployment (manual validation)
           ↑
    Staging Hardware (full integration)
           ↑  
    VM Integration Tests (automated, sectioned)
           ↑
    Syntax & Structure Validation (molecule minimal)
```

## Testing Approaches

### 1. Minimal Molecule Tests

**Purpose**: Basic validation only - NOT functional testing

What Molecule IS good for:
- YAML syntax checking
- Variable structure validation  
- Template rendering verification
- Role dependency checking

What Molecule is NOT for:
- Network configuration (requires real interfaces)
- Storage setup (requires real block devices)
- Service interactions (requires real services)
- Cluster formation (requires real nodes)
- Anything requiring actual infrastructure

**Implementation**:
```yaml
# Keep molecule tests dead simple
- name: Syntax check only
  hosts: all
  tasks:
    - name: Validate required variables
      assert:
        that:
          - required_var is defined
          - required_var.property is defined
    
    - name: Test template rendering
      template:
        src: config.j2
        dest: /tmp/test-render.conf
      check_mode: yes
```

### 2. Sectioned Integration Tests

**Purpose**: Test real functionality in focused scenarios using VMs

#### Test Configuration

```yaml
# test-integration-config.yaml
test_defaults:
  vm_backend: libvirt  # or virtualbox, vagrant
  base_image: ubuntu-24.04-cloud
  cleanup: true
  parallel_execution: false

sections:
  networking:
    description: "Network bonds, VLANs, bridges"
    playbook: site.yml
    tags: [networking]
    inventory: test-inventory/networking
    validate_script: tests/validate-networking.sh
    required_vms: 1
    estimated_time: "5 minutes"
    requires_nested_virt: false
    
  storage:
    description: "LVM, filesystem, mounts"
    playbook: site.yml
    tags: [storage]
    inventory: test-inventory/storage
    validate_script: tests/validate-storage.sh
    required_vms: 1
    estimated_time: "5 minutes"
    requires_nested_virt: false
    
  vyos_config:
    description: "VyOS router configuration"
    playbook: site.yml
    tags: [vyos]
    inventory: test-inventory/vyos
    validate_script: tests/validate-vyos.sh
    required_vms: 1
    estimated_time: "10 minutes"
    requires_nested_virt: true
    
  harvester_single:
    description: "Single node Harvester setup"
    playbook: site.yml
    tags: [harvester]
    inventory: test-inventory/single-node
    validate_script: tests/validate-harvester-single.sh
    required_vms: 1
    estimated_time: "15 minutes"
    requires_nested_virt: true
    
  harvester_cluster:
    description: "3-node Harvester cluster"
    playbook: site.yml
    tags: [harvester]
    inventory: test-inventory/cluster
    validate_script: tests/validate-harvester-cluster.sh
    required_vms: 3
    estimated_time: "30 minutes"
    requires_nested_virt: true
    
  ups_shutdown:
    description: "UPS monitoring and shutdown sequences"
    playbook: site.yml
    tags: [ups]
    inventory: test-inventory/ups
    validate_script: tests/validate-ups.sh
    required_vms: 1
    estimated_time: "5 minutes"
    requires_nested_virt: false
    
  truenas_integration:
    description: "TrueNAS API and storage configuration"
    playbook: site.yml
    tags: [truenas]
    inventory: test-inventory/truenas
    validate_script: tests/validate-truenas.sh
    required_vms: 1
    estimated_time: "10 minutes"
    requires_nested_virt: false
```

#### Test Execution Script

```bash
#!/bin/bash
# test-integration.sh

# Run specific section
./test-integration.sh --section networking

# Run multiple sections
./test-integration.sh --section networking --section storage

# Run all quick tests (< 10 min)
./test-integration.sh --quick

# Run all tests
./test-integration.sh --all

# Run with custom VM backend
./test-integration.sh --section harvester_cluster --backend vagrant

# Keep VMs for debugging
./test-integration.sh --section networking --no-cleanup
```

### 3. Validation Scripts

Each test section has a validation script that performs REAL checks:

```bash
#!/bin/bash
# tests/validate-networking.sh
set -e

echo "=== NETWORK VALIDATION STARTING ==="

# Real network interface checks
echo "Checking bond configuration..."
ssh testvm "ip link show bond0" || exit 1
ssh testvm "cat /proc/net/bonding/bond0" || exit 1

# Real VLAN verification
echo "Checking VLAN interfaces..."
for vlan in 100 200 300; do
    ssh testvm "ip link show bond0.$vlan" || exit 1
done

# Real connectivity test
echo "Testing network connectivity..."
ssh testvm "ping -c 3 10.0.100.1" || exit 1
ssh testvm "ping -c 3 10.0.200.1" || exit 1

# Real service checks
echo "Checking bridge configuration..."
ssh testvm "brctl show br-mgmt" || exit 1
ssh testvm "bridge vlan show" || exit 1

echo "✅ NETWORK VALIDATION COMPLETE"
```

## CI/CD Pipeline Implementation

### GitLab CI Configuration

```yaml
# .gitlab-ci.yml
stages:
  - syntax
  - quick-integration  # < 10 min tests
  - full-integration   # expensive tests
  - cleanup

variables:
  VM_BACKEND: "libvirt"
  CACHE_DIR: "/cache/vms"

# Quick syntax validation
syntax:validation:
  stage: syntax
  script:
    - ansible-playbook site.yml --syntax-check
    - yamllint collections/
  tags:
    - docker
  except:
    - schedules

# Quick integration tests (run on every commit)
test:networking:
  stage: quick-integration
  script:
    - ./test-integration.sh --section networking --backend $VM_BACKEND
  tags:
    - kvm-enabled
  artifacts:
    when: on_failure
    paths:
      - tests/logs/
    expire_in: 1 week

test:storage:
  stage: quick-integration
  script:
    - ./test-integration.sh --section storage --backend $VM_BACKEND
  tags:
    - kvm-enabled

test:vyos:
  stage: quick-integration
  script:
    - ./test-integration.sh --section vyos_config --backend $VM_BACKEND
  tags:
    - kvm-enabled
    - nested-virt

# Expensive tests (manual or scheduled)
test:harvester:single:
  stage: full-integration
  script:
    - ./test-integration.sh --section harvester_single --backend $VM_BACKEND
  tags:
    - kvm-enabled
    - high-memory
    - nested-virt
  when: manual

test:harvester:cluster:
  stage: full-integration
  script:
    - ./test-integration.sh --section harvester_cluster --backend $VM_BACKEND
  tags:
    - kvm-enabled
    - high-memory
    - nested-virt
    - extended-timeout
  only:
    - main
    - merge_requests
  when: manual

# Nightly full test suite
nightly:full:
  stage: full-integration
  script:
    - ./test-integration.sh --all --backend $VM_BACKEND
  tags:
    - kvm-enabled
    - high-memory
    - nested-virt
    - extended-timeout
  only:
    - schedules
```

### Runner Requirements

```yaml
# PREFERRED: Harvester-based runners (once Harvester is deployed)
gitlab-runner-harvester:
  executor: shell
  # Runner runs as VM inside Harvester
  # Uses Harvester API to provision test VMs dynamically
  environment:
    - HARVESTER_URL=https://harvester.management.awynn.in
    - HARVESTER_NAMESPACE=gitlab-ci
  tags:
    - harvester
    - dynamic-vms
  pre_build_script: |
    # Verify Harvester API access
    kubectl get vms -n gitlab-ci || exit 1

# FALLBACK: Local KVM for initial bootstrap
gitlab-runner-local-kvm:
  executor: shell
  environment:
    - KVM_ENABLED=true
    - LIBVIRT_DEFAULT_URI=qemu:///system
  tags:
    - kvm-enabled
    - nested-virt
    - high-memory  # 32GB+
  pre_build_script: |
    # Ensure KVM is available
    test -e /dev/kvm || exit 1

# SIMPLE: Docker executor (only for syntax/lint tests)
gitlab-runner-syntax:
  executor: docker
  docker:
    image: ansible:latest
  tags:
    - docker
    - syntax-only
```

## VM Management Strategies

### Testing Infrastructure Options

| Approach | Pros | Cons | Use Case |
|----------|------|------|----------|
| **Vagrant + libvirt** | Mature, well-documented | Initial setup complexity | Developer machines |
| **Harvester VMs** | Dogfooding, no cloud costs, API-driven | Requires Harvester deployed | PREFERRED for CI/CD |
| **Shell executor + KVM** | Direct, no nesting issues | Requires dedicated hardware | Initial bootstrap only |
| **Docker + nested KVM** | Container isolation | Complex, performance hit | NOT RECOMMENDED |
| **Pre-provisioned VMs** | Very fast | State management | Repeated testing |
| **Cloud VMs** | Scalable | Cost, latency | Burst testing |

**Better Alternative for CI/CD**:
```
# Direct approach - no Docker layer:
GitLab Runner (Host with KVM)
  └── Test VM (Direct KVM)
```

Use shell executor with direct KVM access instead of Docker executor.

### Recommended: Progressive Approach

1. **Local Development**: Vagrant + libvirt
   - Easy to debug
   - Full VM capabilities  
   - Good caching
   - Direct hardware access

2. **CI/CD Pipeline (Preferred)**: Harvester-based Testing
   - GitLab runs as VM in Harvester
   - GitLab runners are VMs in Harvester
   - Test VMs provisioned dynamically via Harvester API
   - No cloud costs - using your own infrastructure
   - Clean separation of concerns
   - Example flow:
     ```
     GitLab (Harvester VM) 
       → Runner (Harvester VM)
         → Provisions test VM via API
         → Runs tests
         → Destroys test VM
     ```

3. **CI/CD Pipeline (Bootstrap)**: Shell executor + local KVM
   - Used only until Harvester is deployed
   - Direct VM management
   - Transitions to Harvester-based once available

4. **Full Integration**: Harvester VM pools
   - Persistent test environments in namespaces
   - Snapshot/restore via Harvester
   - Real hardware characteristics
   - API-driven provisioning

## Anti-patterns to Avoid

### ❌ DO NOT Create

```yaml
# Bad: Mock mode flags
harvester_test_mode: true
skip_real_deployment: true
use_mock_api: true

# Bad: Different test behaviors
when: not molecule_test_mode

# Bad: Fake services
mock_harvester_api: true
```

### ❌ DO NOT Test

- Ansible module functionality (trust that `apt` works)
- Mock infrastructure behavior
- Syntax-only validation as "tests"
- Configuration without deployment

### ✅ DO Test

- Real network configuration
- Actual service deployment
- API integrations
- Cluster formation
- Storage operations
- Service interactions

## Implementation Priorities

### Phase 1: Foundation (Do First - Local Testing)
- [ ] Create `test-integration.sh` script
- [ ] Setup basic VM provisioning with Vagrant + libvirt locally
- [ ] Implement networking section test
- [ ] Implement storage section test
- [ ] Create validation script framework
- [ ] Document local testing setup for developers

### Phase 2: Advanced Component Testing (Do Second - Prove It Works)
- [ ] Harvester single-node tests locally
- [ ] Harvester cluster tests (3-node)
- [ ] VyOS configuration tests
- [ ] TrueNAS integration tests
- [ ] UPS shutdown sequence tests
- [ ] Full end-to-end deployment test locally

### Phase 3: Optimization (Do Third - Make It Better)
- [ ] Parallel test execution
- [ ] Smart test selection based on changed components
- [ ] VM image caching strategy
- [ ] Test result caching
- [ ] Failure analysis and reporting
- [ ] Performance benchmarks

### Phase 4: CI/CD Integration (Do Last - When Infrastructure Exists)
- [ ] Setup GitLab instance
- [ ] Configure runners with shell executor + KVM
- [ ] Implement pipeline configuration
- [ ] Add artifact collection
- [ ] Setup distributed VM image caching
- [ ] Create test result dashboard
- [ ] Integrate with merge request workflow

**Note**: Phases 1-3 can be done immediately without any infrastructure. Phase 4 requires GitLab to be deployed and operational.

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Quick test runtime | < 10 min | - |
| Full test runtime | < 60 min | - |
| Test reliability | > 95% | - |
| False positive rate | < 2% | - |
| Developer feedback time | < 15 min | - |
| Resource usage | < 32GB RAM | - |

## Instructions for AI Assistants

### When Creating Tests

1. **Start with integration tests**, not unit tests
2. **Use real infrastructure** in tests (VMs, networks, storage)
3. **Write validation scripts** that check actual functionality
4. **Never create mock mode flags** or test-only behaviors
5. **Always run full tests** - no shortcuts or smoke tests

### When Running Tests

```bash
# For quick feedback (networking, storage, etc)
./test-integration.sh --section networking

# For full validation (before PR)
./test-integration.sh --all

# Never create or use:
# ❌ ./test-quick.sh
# ❌ ./test-smoke.sh
# ❌ --skip-validation
# ❌ --mock-mode
```

### Expected Test Output

```
=== INTEGRATION TEST: networking ===
[1/4] Provisioning test VM... ✓
[2/4] Applying configuration... ✓
[3/4] Running validation... ✓
[4/4] Cleanup... ✓

✅ SECTION PASSED: networking (4m 32s)

Real checks performed:
- Bond interface active
- VLANs configured
- Connectivity verified
- Services running
```

## Summary

This testing strategy:
- **Rejects unit testing of infrastructure** - embraces integration testing
- **Uses real infrastructure** - VMs, networks, actual services
- **Provides sectioned testing** - focused, fast feedback
- **Scales from local to CI/CD** - same tests everywhere
- **Prevents shortcut abuse** - one path, real validation
- **Optimizes for confidence** - what passes will work in production

The goal: **Deploy once, work first time** through comprehensive integration testing with real infrastructure components.