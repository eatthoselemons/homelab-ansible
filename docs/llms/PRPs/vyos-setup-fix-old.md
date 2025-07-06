name: "VyOS Setup Fix and Hardening PRP"
description: |

## Purpose
Fix VyOS VM setup to properly install the OS using delegated_vm_install role, implement security best practices, and create comprehensive molecule tests for production-ready deployment.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Fix the VyOS router setup on Nexus node to:
1. Properly install VyOS OS using stafwag.delegated_vm_install role
2. Apply VyOS security hardening best practices
3. Create comprehensive molecule tests that simulate production environment

## Why
- **Business value**: VyOS is the critical router/firewall for the entire homelab infrastructure
- **Integration**: Routes traffic between WAN and 7 internal VLANs (DMZ, Untrusted WiFi, Trusted WiFi, IoT, Secure, Management, Logging)
- **Problems solved**: Currently VM has no OS installed, security hardening not applied, tests insufficient

## What
- VyOS VM properly boots with installed OS
- Security hardening applied (fail2ban, firewall rules, SSH keys)
- Idempotent role that can run multiple times
- Comprehensive molecule tests simulating production

### Success Criteria
- [ ] VyOS VM successfully installs and boots with cloud-init
- [ ] All 7 VLANs configured with proper isolation
- [ ] Security hardening applied (fail2ban, firewall default drop)
- [ ] Molecule tests pass with simulated VyOS environment
- [ ] Role is idempotent - can run multiple times without issues

## All Needed Context

### Documentation & References (list all context needed to implement the feature)
```yaml
# MUST READ - Include these in your context window
- url: https://docs.vyos.io/en/latest/automation/cloud-init.html
  why: VyOS cloud-init configuration for automated setup
  
- url: https://docs.vyos.io/en/latest/configuration/firewall/index.html
  why: Firewall configuration best practices for VyOS 1.5.x
  
- url: https://github.com/vyos/vyos-vm-images
  why: Official VyOS VM image generation with cloud-init support
  
- file: references/ansible-role-delegated_vm_install/README.md
  why: How to use delegated_vm_install role for VM provisioning
  
- file: references/ansible-role-delegated_vm_install/docs/examples/single_node_debian12/inventory.yml
  why: Example of VM configuration with delegated_vm_install
  
- file: collections/ansible_collections/homelab/nexus/roles/vyos_setup/defaults/main.yaml
  why: Current VyOS configuration including VLANs and security settings
  
- file: collections/ansible_collections/homelab/nexus/roles/vyos_setup/tasks/main.yaml
  why: Current implementation to understand what needs fixing
  
- doc: references/molecule/docs
  why: Molecule testing documentation for creating comprehensive tests
  
- docfile: docs/llms/design/architecture.md
  why: System architecture showing VyOS role in infrastructure
```

### Current Codebase tree (run `tree` in the root of the project) to get an overview of the codebase
```bash
collections/ansible_collections/homelab/nexus/
├── roles/
│   └── vyos_setup/
│       ├── defaults/main.yaml     # VM and VLAN configurations
│       ├── tasks/
│       │   ├── main.yaml         # Main orchestration (needs fix)
│       │   ├── vlan_setup.yaml   # VLAN network setup
│       │   ├── vyos_config.yaml  # VyOS configuration
│       │   └── fail2ban.yaml     # Security hardening
│       └── templates/
│           ├── vyos_vm.xml.j2    # LibVirt VM definition
│           ├── *_network.xml.j2  # Network configurations
│           └── vyos_*.j2         # VyOS config templates
└── extensions/molecule/
    └── vyos_setup/               # Basic test (needs enhancement)
```

### Desired Codebase tree with files to be added and responsibility of file
```bash
collections/ansible_collections/homelab/nexus/
├── roles/
│   └── vyos_setup/
│       ├── defaults/main.yaml         # Enhanced with delegated_vm_install vars
│       ├── tasks/
│       │   ├── main.yaml             # Orchestrate delegated_vm_install
│       │   ├── prepare_vm.yaml       # NEW: Prepare VM installation
│       │   ├── vlan_setup.yaml      # Existing VLAN setup
│       │   ├── vyos_config.yaml     # Enhanced with cloud-init
│       │   └── fail2ban.yaml        # Security hardening
│       ├── templates/
│       │   ├── vyos_vm_template.yml  # NEW: delegated_vm_install template
│       │   ├── cloud-init/
│       │   │   ├── user-data.j2     # NEW: VyOS cloud-init config
│       │   │   └── network-config.j2 # NEW: Network cloud-init
│       │   └── (existing templates)
│       └── files/
│           └── vyos-1.5-cloud.qcow2  # NEW: VyOS cloud image (or URL)
└── extensions/molecule/
    ├── nexus.vyos.setup/            # Renamed: Basic VM setup test
    ├── nexus.vyos.security_hardening/ # NEW: Security test scenario
    └── nexus.vyos.full_integration/  # NEW: Complete integration test
```

### Known Gotchas of our codebase & Library Quirks
```yaml
# CRITICAL: VyOS specific requirements
# - VyOS 1.5.x requires cloud-init for automated provisioning
# - Default VyOS allows all traffic - must change to drop
# - VyOS cloud images need qcow2 format for libvirt
# - Cloud-init runs only on first boot - use vyos_config_commands

# CRITICAL: delegated_vm_install requirements
# - Requires stafwag.delegated_vm_install from Ansible Galaxy
# - VM must be defined in inventory with vm_ip_address and vm_kvm_host
# - Template path must be relative to playbook or absolute
# - Cloud-init ISO is auto-generated from templates

# CRITICAL: Molecule testing with VMs
# - Use Docker containers with KVM support for VM testing
# - Mount /dev/kvm for hardware acceleration
# - LibVirt must be installed in test container
# - Network isolation required for VLAN testing
```

## Implementation Blueprint

### Data models and structure

VyOS VM inventory configuration structure:
```yaml
# inventory.yml enhancement
vyos:
  hosts:
    vyos-router:
      ansible_host: "{{ vyos_wan_ip }}"
      vm_ip_address: "{{ vyos_wan_ip }}"
      vm_kvm_host: localhost
      delegated_vm_install:
        vm:
          template: roles/vyos_setup/templates/vyos_vm_template.yml
          path: /var/lib/libvirt/images/vyos
          boot_disk:
            src: https://github.com/vyos/vyos-rolling-nightly-builds/releases/download/1.5-rolling/vyos-1.5-rolling-amd64.qcow2
            size: 20G
          memory: 4096
          cpus: 2
          networks:
            - name: wan
              type: bridge
              bridge: "{{ vyos_wan_bridge }}"
            - name: lan
              type: bridge
              bridge: "{{ vyos_lan_bridge }}"
```

### list of tasks to be completed to fullfill the PRP in the order they should be completed

```yaml
Task 1:
MODIFY collections/ansible_collections/homelab/nexus/roles/vyos_setup/tasks/main.yaml:
  - REMOVE direct virt-install commands
  - ADD include_role for stafwag.delegated_vm_install
  - ADD pre-tasks for network setup
  - PRESERVE VLAN configuration tasks

Task 2:
CREATE collections/ansible_collections/homelab/nexus/roles/vyos_setup/templates/vyos_vm_template.yml:
  - MIRROR pattern from: references/ansible-role-delegated_vm_install/templates/vms/debian/12/debian_vm_template.yml
  - MODIFY for VyOS specific requirements
  - ADD dual network interface configuration
  - INCLUDE cloud-init user-data template reference

Task 3:
CREATE collections/ansible_collections/homelab/nexus/roles/vyos_setup/templates/cloud-init/user-data.j2:
  - ADD VyOS initial configuration commands
  - INCLUDE VLAN interface setup
  - ADD firewall default-action drop rules
  - CONFIGURE SSH with key-only authentication
  - SET hostname and system parameters

Task 4:
MODIFY collections/ansible_collections/homelab/nexus/roles/vyos_setup/defaults/main.yaml:
  - ADD delegated_vm_install variables
  - ADD VyOS image URL or path
  - PRESERVE existing VLAN configurations
  - ADD cloud-init command lists

Task 5:
CREATE collections/ansible_collections/homelab/nexus/roles/vyos_setup/tasks/prepare_vm.yaml:
  - CHECK for existing VM
  - DOWNLOAD VyOS cloud image if needed
  - PREPARE cloud-init configuration
  - SET proper file permissions

Task 6:
ENHANCE collections/ansible_collections/homelab/nexus/roles/vyos_setup/tasks/vyos_config.yaml:
  - ADD vyos.vyos collection tasks
  - CONFIGURE firewall rules per VLAN
  - APPLY security hardening
  - ENSURE idempotency

Task 7:
CREATE collections/ansible_collections/homelab/nexus/extensions/molecule/nexus.vyos.setup/molecule.yml:
  - CONFIGURE Docker platform with KVM support
  - ADD libvirt installation in prepare.yml
  - TEST basic VM creation and boot

Task 8:
CREATE collections/ansible_collections/homelab/nexus/extensions/molecule/nexus.vyos.security_hardening/molecule.yml:
  - TEST firewall default drop policy
  - VERIFY fail2ban configuration
  - CHECK SSH key-only access
  - VALIDATE VLAN isolation

Task 9:
CREATE comprehensive integration test scenario
```

### Per task pseudocode as needed added to each task
```yaml
# Task 1 - Main orchestration
# Path: collections/ansible_collections/homelab/nexus/roles/vyos_setup/tasks/main.yaml
---
- name: Include VyOS VM preparation
  include_tasks: prepare_vm.yaml

- name: Setup network infrastructure
  include_tasks: vlan_setup.yaml
  
- name: Deploy VyOS VM using delegated_vm_install
  include_role:
    name: stafwag.delegated_vm_install
  vars:
    # Variables will come from inventory and defaults
    
- name: Wait for VyOS to be reachable
  wait_for:
    host: "{{ vm_ip_address }}"
    port: 22
    delay: 30
    timeout: 300
    
- name: Configure VyOS
  include_tasks: vyos_config.yaml
  when: vyos_vm_created is changed or vyos_always_configure | bool

# Task 3 - Cloud-init user data
# Path: templates/cloud-init/user-data.j2
#cloud-config
vyos_config_commands:
  # System configuration
  - set system host-name '{{ vyos_hostname }}'
  - set system domain-name '{{ vyos_domain }}'
  
  # Interface configuration
  - set interfaces ethernet eth0 address 'dhcp'
  - set interfaces ethernet eth0 description 'WAN'
  
  # VLAN interfaces
{% for vlan in vyos_vlans %}
  - set interfaces ethernet eth1 vif {{ vlan.id }} address '{{ vlan.gateway }}'
  - set interfaces ethernet eth1 vif {{ vlan.id }} description '{{ vlan.name }}'
{% endfor %}

  # Firewall - CRITICAL: Default drop
  - set firewall global-options state-policy established action 'accept'
  - set firewall global-options state-policy related action 'accept'
  - set firewall global-options state-policy invalid action 'drop'
  
  # Default policies
  - set firewall ipv4 forward filter default-action 'drop'
  - set firewall ipv4 input filter default-action 'drop'
  
  # Management access
  - set firewall ipv4 input filter rule 10 action 'accept'
  - set firewall ipv4 input filter rule 10 destination port '22'
  - set firewall ipv4 input filter rule 10 protocol 'tcp'
  - set firewall ipv4 input filter rule 10 source address '{{ vyos_vlans | selectattr("name", "eq", "management") | map(attribute="subnet") | first }}'

users:
  - name: vyos
    ssh_authorized_keys:
{% for key in vyos_ssh_authorized_keys %}
      - {{ key }}
{% endfor %}
```

### Integration Points
```yaml
INVENTORY:
  - add to: collections/ansible_collections/homelab/nexus/inventory.yml
  - pattern: Define vyos host with delegated_vm_install vars
  
REQUIREMENTS:
  - add to: collections/ansible_collections/homelab/nexus/requirements.yml
  - content: |
      - name: stafwag.delegated_vm_install
        version: ">=2.0.0"
      - name: vyos.vyos
        version: ">=4.0.0"
  
MOLECULE:
  - update: extensions/molecule/default/molecule.yml
  - add: KVM device mounting and libvirt packages
  
SITE PLAYBOOK:
  - verify: site/playbooks/setup-nexus.yaml includes vyos_setup role
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Navigate to role directory
cd collections/ansible_collections/homelab/nexus

# Validate ansible syntax
ansible-playbook --syntax-check site/playbooks/setup-nexus.yaml

# Lint the role
ansible-lint roles/vyos_setup/

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests each new feature/file/function use existing test patterns
```bash
# Test basic VM creation
cd collections/ansible_collections/homelab/nexus/extensions
molecule test -s nexus.vyos.setup

# Test security hardening
molecule test -s nexus.vyos.security_hardening

# Expected output: All tests pass
# Common issues:
# - Missing /dev/kvm: Ensure Docker privileged mode
# - LibVirt errors: Install libvirt-daemon-system in prepare.yml
```

### Level 3: Integration Test
```bash
# Full integration test with all components
molecule test -s nexus.vyos.full_integration

# Verify specific functionality:
# - VM boots successfully
# - Cloud-init completes
# - Firewall blocks by default
# - VLANs are isolated
# - Management access works

# Manual verification commands:
virsh list --all  # Should show vyos-router running
virsh net-list    # Should show WAN, LAN, and VLAN networks

# Test connectivity
ssh vyos@<vyos_wan_ip> "show configuration"
```

## Final validation Checklist
- [ ] All molecule tests pass: `molecule test`
- [ ] No ansible-lint errors: `ansible-lint roles/vyos_setup/`
- [ ] VM successfully boots with VyOS OS
- [ ] Cloud-init applies initial configuration
- [ ] Firewall default action is drop
- [ ] All 7 VLANs are configured and isolated
- [ ] SSH access is key-only
- [ ] Fail2ban is active
- [ ] Role is idempotent (run twice without changes)
- [ ] Documentation updated in role README

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode network interfaces (eth0/eth1) - use variables
- ❌ Don't skip cloud-init - it's required for automation
- ❌ Don't leave default VyOS password - use SSH keys only
- ❌ Don't forget to test VLAN isolation
- ❌ Don't use old VyOS versions without cloud-init support
- ❌ Don't create VM without checking if it exists first

---

## Additional Context for VyOS Setup

### VyOS Cloud-Init Specifics
VyOS uses a special vyos_config_commands section in cloud-init that runs VyOS configuration commands on first boot. This is different from standard cloud-init.

### Network Architecture
- eth0: WAN interface (DHCP from upstream)
- eth1: LAN trunk with 7 VLANs
  - VLAN 10: DMZ (10.0.10.0/24)
  - VLAN 20: Untrusted WiFi (10.0.20.0/24)
  - VLAN 30: Trusted WiFi (10.0.30.0/24)
  - VLAN 40: IoT (10.0.40.0/24)
  - VLAN 50: Secure (10.0.50.0/24)
  - VLAN 60: Management (10.0.60.0/24)
  - VLAN 70: Logging (10.0.70.0/24)

### Security Requirements
1. Default firewall action: DROP (not ACCEPT)
2. Explicit allow rules for each service
3. Inter-VLAN routing controlled by firewall
4. Management VLAN only for SSH access
5. Fail2ban on all exposed services

### Testing Strategy
1. **nexus.vyos.setup**: Basic VM deployment
2. **nexus.vyos.security_hardening**: Security validation
3. **nexus.vyos.full_integration**: Complete system test

Each test should be as close to production as possible using Docker containers with KVM support.