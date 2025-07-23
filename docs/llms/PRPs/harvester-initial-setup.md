name: "Harvester Initial Setup PRP"
description: |

## Purpose
Implement initial setup of Harvester HCI cluster across EPYC server, mid server, and HP thin client to enable VM and container deployment with PCIe passthrough support for GPU and storage devices. This PRP provides comprehensive context for one-pass implementation success.

## Core Principles
1. **Context is Complete but Focused**: Include ALL necessary Harvester documentation, ansible patterns, and discovered caveats
2. **Validation Loops**: Provide executable molecule tests the AI can run and fix
3. **Information Dense**: Use patterns from existing vyos_setup role
4. **Progressive Success**: Start with basic cluster, validate, then add advanced features
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Deploy a production-ready Harvester HCI cluster across three nodes (EPYC server, mid server, HP thin client) with:
- HA configuration with 3 management nodes
- PCIe passthrough enabled for GPU (to GPU services) and storage HBA (to TrueNAS)
- Network segmentation following homelab architecture (Management VLAN 60, Secure VLAN 50)
- NTP time server VM added to Nexus for cluster time synchronization
- Terraform provider configured for future VM/container deployments
- Ready to deploy TrueNAS VM and Authentik containers (but not deploying them)

## Why
- **Business value**: Provides virtualization platform for all homelab services
- **Integration**: Harvester will host critical VMs like TrueNAS and containers like Authentik
- **Problems solved**: Enables hardware passthrough for performance, provides HA for services, standardizes deployment via Terraform

## What
Deploy Harvester cluster with Ansible automation that:
- Configures network interfaces with VLAN tagging
- Initializes 3-node HA cluster
- Enables PCIe passthrough for specified devices
- Configures storage network for Longhorn replication
- Sets up Terraform provider access
- Adds NTP server to Nexus services VM for time synchronization

### Success Criteria
- [ ] All 3 nodes joined to cluster and showing as Ready
- [ ] VIP accessible on management network
- [ ] PCIe devices available for passthrough
- [ ] Terraform can authenticate and list resources
- [ ] NTP server running on Nexus and Harvester nodes synchronized
- [ ] All molecule tests passing

## All Needed Context

### Documentation & References (include complete sections that are directly relevant)
```yaml
# MUST READ - Include these specific sections in your context window

- file: /home/user/IdeaProjects/homelab-ansible/docs/llms/design/architecture.md
  sections: ["Physical Infrastructure", "Network Design", "Service Architecture"]
  why: Understand overall system architecture and network VLANs
  critical: |
    Management VLAN 60 for server administration
    Secure VLAN 50 for internal services
    EPYC has 256GB RAM, Mid has 64GB RAM
    
- file: /home/user/IdeaProjects/homelab-ansible/docs/llms/best-practices/harvester-setup-best-practices.md
  why: Harvester-specific configuration requirements
  gotcha: |
    First 3 nodes automatically become management nodes
    NTP is critical for etcd stability
    Storage network IP calculation: (Nodes × 2) + (Disks × 2) + Images
    
- file: /home/user/IdeaProjects/homelab-ansible/collections/ansible_collections/homelab/nexus/roles/vyos_setup/tasks/main.yaml
  why: Follow pattern for Infisical secret retrieval and task organization
  pattern: |
    Validate Infisical env vars first
    Retrieve secrets in structured blocks
    Use include_tasks for sub-configurations
    
- url: https://docs.harvesterhci.io/v1.4/install/requirements/
  sections: ["Hardware Requirements", "Port Requirements"]
  why: Official hardware and network requirements
  discovered_caveat: |
    Management nodes need 5000+ IOPS storage
    Each node must have unique product_uuid
    
- url: https://docs.harvesterhci.io/v1.4/install/harvester-configuration/
  sections: ["Configuration File", "Networking"]
  why: Cloud-init configuration format
  critical: |
    install.mode: create (first node) or join (subsequent)
    Node IPs cannot change after installation
    
- url: https://docs.harvesterhci.io/v1.4/advanced/addons/pcidevices/
  sections: ["Enabling the Add-on", "Enabling Passthrough"]
  why: PCIe passthrough configuration
  gotcha: |
    All devices in same IOMMU group must be passed together
    VM must be scheduled on specific node (no live migration)
    
- url: https://registry.terraform.io/providers/harvester/harvester/latest/docs
  why: Terraform provider configuration
  critical: |
    Requires kubeconfig for authentication
    Version 0.6.7 as of April 2024
    
- url: https://hungvu.tech/compare-pci-and-gpu-passthrough-in-harvester-hci-with-proxmox/
  why: Real-world PCIe passthrough examples
  discovered_caveat: |
    Kernel params: intel_iommu=on vfio-pci.ids=<device_ids>
    /boot/grub/grub.cfg is ephemeral, use /oem/99-* files
```

### Context Inclusion Guidelines
- Include COMPLETE Harvester installation and configuration sections
- Include ALL vyos_setup patterns for Ansible role structure
- Include ALL network and storage configuration requirements
- Skip sections about: UI navigation, upgrade procedures, troubleshooting

### Current Codebase tree (relevant portions)
```bash
collections/ansible_collections/homelab/
├── nexus/
│   ├── roles/
│   │   └── vyos_setup/          # Example role structure to follow
│   │       ├── defaults/main.yaml
│   │       ├── tasks/main.yaml
│   │       ├── handlers/main.yaml
│   │       └── templates/
│   └── extensions/
│       └── molecule/            # Test scenarios
└── epyc/                        # New location for harvester role
    └── roles/                   # To be created
```

### Desired Codebase tree with files to be added and responsibility of file
```bash
collections/ansible_collections/homelab/epyc/
├── roles/
│   └── harvester_setup/
│       ├── README.md                           # Role documentation
│       ├── defaults/
│       │   └── main.yaml                       # Default variables (overridable)
│       ├── handlers/
│       │   └── main.yaml                       # Service restart handlers
│       ├── meta/
│       │   └── requirements.yaml               # Role dependencies
│       ├── tasks/
│       │   ├── main.yaml                       # Main task orchestration
│       │   ├── validate_prerequisites.yaml     # Hardware/network validation
│       │   ├── configure_networks.yaml         # Network interface setup
│       │   ├── prepare_nodes.yaml              # Node preparation (kernel params)
│       │   ├── init_cluster.yaml               # First node cluster creation
│       │   ├── join_nodes.yaml                 # Additional node joining
│       │   ├── configure_storage.yaml          # Storage network setup
│       │   ├── enable_pcie_passthrough.yaml    # PCIe device configuration
│       │   └── setup_terraform_access.yaml     # Kubeconfig for Terraform
│       ├── templates/
│       │   ├── harvester_config.yaml.j2        # Node configuration
│       │   ├── network_config.yaml.j2          # Network configuration
│       │   ├── grub_config.j2                  # GRUB kernel parameters
│       │   └── storage_network.yaml.j2         # Longhorn storage network
│       └── vars/
│           └── main.yaml                       # Non-overridable variables

collections/ansible_collections/homelab/nexus/roles/
└── ntp_server/                                 # New NTP server role
    ├── tasks/main.yaml                         # NTP server container setup
    ├── templates/
    │   ├── docker-compose.yml.j2               # Docker compose for chrony
    │   └── chrony.conf.j2                      # Chrony configuration
    ├── handlers/main.yaml                      # Container restart handler
    └── defaults/main.yaml                      # Default variables

collections/ansible_collections/homelab/nexus/extensions/molecule/
└── ntp-server/                                 # NTP server tests
    ├── molecule.yml                            # Test configuration
    ├── prepare.yml                             # Test preparation
    ├── converge.yml                            # Test execution
    └── verify.yml                              # Test verification

collections/ansible_collections/homelab/epyc/extensions/molecule/
└── harvester-setup/
    ├── molecule.yml                            # Test configuration
    ├── prepare.yml                             # Test preparation
    ├── converge.yml                            # Test execution
    └── verify.yml                              # Test verification
```

### Known Gotchas of our codebase & Library Quirks
```yaml
# CRITICAL: Harvester-specific gotchas
# 1. Node IPs cannot change after cluster initialization
# 2. First 3 nodes automatically become management nodes
# 3. GRUB config is ephemeral - must use cloud-init or /oem files
# 4. PCIe devices in same IOMMU group must be passed together
# 5. Time sync is critical - etcd will fail with time drift
# 6. Storage network IPs must not overlap with K8s ranges (10.52.0.0/16, 10.53.0.0/16)

# Ansible patterns from codebase:
# 1. Always validate Infisical env vars before retrieving secrets
# 2. Use structured set_fact for secret extraction
# 3. Feature flags in defaults for conditional execution
# 4. Molecule tests must set test secrets in prepare.yml
# 5. Use .yaml extension, never .yml
# 6. Always include newlines at end of files
```

## Implementation Blueprint

### Data models and structure

Create the variable structure following homelab patterns:
```yaml
# defaults/main.yaml structure
---
# Infisical Configuration (following vyos pattern)
harvester_infisical_client_id: "{{ lookup('env', 'INFISICAL_CLIENT_ID') }}"
harvester_infisical_client_secret: "{{ lookup('env', 'INFISICAL_CLIENT_SECRET') }}"
harvester_infisical_project_id: "{{ lookup('env', 'INFISICAL_PROJECT_ID') }}"
harvester_infisical_url: "https://app.infisical.com"

# Cluster Configuration
harvester_cluster_token: ""  # Retrieved from Infisical
harvester_cluster_vip: "10.60.1.10"  # Management VLAN
harvester_admin_password: ""  # Retrieved from Infisical

# Node definitions
harvester_nodes:
  - name: "epyc-harvester"
    ip: "10.60.1.11"
    role: "management"
    is_first: true
    interfaces:
      - name: "eth0"
        hwaddr: ""  # Set in inventory
    pcie_devices: ["10de:1fb9", "10de:10fa"]  # GPU IDs
  - name: "mid-harvester"
    ip: "10.60.1.12"
    role: "management"
    interfaces:
      - name: "eth0"
        hwaddr: ""  # Set in inventory
  - name: "thin-harvester"
    ip: "10.60.1.13"
    role: "witness"
    interfaces:
      - name: "eth0"
        hwaddr: ""  # Set in inventory

# Network Configuration
harvester_mgmt_interface: "harvester-mgmt"
harvester_storage_network:
  vlan: 65
  cidr: "10.65.0.0/24"
  ip_range_start: "10.65.0.10"
  ip_range_end: "10.65.0.250"

# Feature Flags
harvester_configure_networks: true
harvester_enable_pcie_passthrough: true
harvester_configure_storage_network: true
harvester_setup_terraform: true
```

### List of tasks to be completed to fulfill the PRP in the order they should be completed

```yaml
Task 1: Create role structure and base files
CREATE collections/ansible_collections/homelab/epyc/roles/harvester_setup/:
  - Create directory structure as defined above
  - Add README.md with role description
  - Create meta/requirements.yaml with infisical.vault dependency

Task 2: Implement main.yaml with Infisical validation
CREATE tasks/main.yaml:
  - MIRROR pattern from: vyos_setup/tasks/main.yaml
  - Validate Infisical environment variables
  - Retrieve cluster token and admin password from Infisical
  - Include sub-tasks based on feature flags

Task 3: Implement prerequisite validation
CREATE tasks/validate_prerequisites.yaml:
  - Check node hardware meets requirements (CPU, RAM, storage)
  - Verify network interfaces exist
  - Ensure unique product_uuid on each node
  - Validate IOMMU enabled in BIOS

Task 4: Configure network interfaces
CREATE tasks/configure_networks.yaml:
  - Template network configuration for each node
  - Configure management interface with static IP
  - Set up VLAN tagging for storage network
  - Apply network configuration via cloud-init

Task 5: Prepare nodes with kernel parameters
CREATE tasks/prepare_nodes.yaml:
  - Template GRUB configuration with IOMMU and vfio-pci parameters
  - Apply configuration to /oem/99-harvester-config.yaml
  - Handle node-specific PCIe device IDs

Task 6: Initialize Harvester cluster
CREATE tasks/init_cluster.yaml:
  - Generate harvester_config.yaml from template
  - Apply configuration to first node
  - Wait for cluster initialization
  - Retrieve kubeconfig for further operations

Task 7: Join additional nodes
CREATE tasks/join_nodes.yaml:
  - Generate join configuration for each node
  - Apply configuration with cluster token
  - Wait for nodes to join and become ready
  - Verify cluster health

Task 8: Configure storage network
CREATE tasks/configure_storage.yaml:
  - Create storage network configuration
  - Apply Longhorn settings for replication traffic
  - Verify storage network connectivity

Task 9: Enable PCIe passthrough
CREATE tasks/enable_pcie_passthrough.yaml:
  - Install pcidevices-controller addon
  - Wait for PCIDevice CRDs availability
  - Enable passthrough for specified devices
  - Verify devices available for VM attachment

Task 10: Setup Terraform access
CREATE tasks/setup_terraform_access.yaml:
  - Extract and format kubeconfig
  - Store in secure location for Terraform
  - Create example Terraform configuration
  - Test Terraform provider connectivity

Task 11: Add NTP server to Nexus
CREATE collections/ansible_collections/homelab/nexus/roles/ntp_server/:
  - Install chrony package
  - Template chrony.conf for local network
  - Configure firewall rules
  - Ensure service enabled and started

Task 12: Create comprehensive molecule tests
CREATE molecule/harvester-setup/:
  - Configure multi-node Docker test environment
  - Mock Harvester API responses
  - Test all configuration generation
  - Verify idempotency
```

### Per task pseudocode as needed added to each task

```yaml
# Task 2 - Main orchestration (tasks/main.yaml)
---
# PATTERN: Validate Infisical first (from vyos_setup)
- name: Validate Infisical environment variables
  block:
    - name: Check INFISICAL_CLIENT_ID is set
      assert:
        that:
          - harvester_infisical_client_id is defined
          - harvester_infisical_client_id | length > 0
        fail_msg: "INFISICAL_CLIENT_ID must be set"

# PATTERN: Retrieve secrets with proper extraction
- name: Retrieve Harvester secrets from Infisical
  block:
    - name: Get cluster token
      set_fact:
        harvester_cluster_token_raw: "{{ lookup('infisical.vault.read_secrets', 
          ... standard params ...,
          secret_name='harvesterClusterToken') }}"
    
    - name: Extract token value
      set_fact:
        harvester_cluster_token: "{{ harvester_cluster_token_raw.value }}"

# PATTERN: Include tasks conditionally
- name: Validate prerequisites
  include_tasks: validate_prerequisites.yaml

- name: Configure networks
  include_tasks: configure_networks.yaml
  when: harvester_configure_networks | default(true)

# Task 5 - Node preparation with kernel params
# CRITICAL: Must use /oem files as /boot/grub/grub.cfg is ephemeral
- name: Prepare harvester configuration with kernel parameters
  template:
    src: harvester_config.yaml.j2
    dest: "/tmp/harvester-{{ item.name }}-config.yaml"
  loop: "{{ harvester_nodes }}"
  delegate_to: "{{ item.ip }}"

# Task 6 - Cluster initialization
# PATTERN: First node creates, others join
- name: Initialize cluster on first node
  when: harvester_nodes[0].is_first | default(false)
  block:
    - name: Apply configuration
      copy:
        src: "/tmp/harvester-{{ harvester_nodes[0].name }}-config.yaml"
        dest: "/oem/99-harvester.yaml"
      delegate_to: "{{ harvester_nodes[0].ip }}"
    
    # GOTCHA: Wait for API availability before proceeding
    - name: Wait for Harvester API
      uri:
        url: "https://{{ harvester_cluster_vip }}:6443/healthz"
        validate_certs: no
      register: api_health
      until: api_health.status == 200
      retries: 60
      delay: 10

# Task 9 - PCIe passthrough
# CRITICAL: Check IOMMU groups before enabling
- name: Verify IOMMU groups
  shell: |
    for d in /sys/kernel/iommu_groups/*/devices/*; do
      n=${d#*/iommu_groups/*}; n=${n%%/*}
      printf 'IOMMU Group %s ' "$n"
      lspci -nns "${d##*/}"
    done
  register: iommu_groups
  delegate_to: "{{ item.ip }}"
  loop: "{{ harvester_nodes }}"

# PATTERN: Enable addon first, then configure devices
- name: Enable pcidevices-controller addon
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: harvesterhci.io/v1beta1
      kind: Addon
      metadata:
        name: pcidevices-controller
        namespace: harvester-system
      spec:
        enabled: true
```

### Integration Points
```yaml
NETWORK:
  - Management VLAN 60: All Harvester management traffic
  - Secure VLAN 50: VM workload traffic
  - Storage VLAN 65: Longhorn replication (new)
  
SERVICES:
  - Nexus VM: Add NTP server for time synchronization
  - DNS: Configure harvester.{{ domain }} entries
  
STORAGE:
  - TrueNAS: Will use PCIe passthrough for HBA
  - Longhorn: Default storage class for other workloads
  
SECRETS:
  - Infisical path: /harvester/
  - Required: clusterToken, adminPassword, sshKey
  
TERRAFORM:
  - Kubeconfig location: /etc/harvester/kubeconfig
  - Provider version: 0.6.7
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd collections/ansible_collections/homelab/epyc
ansible-lint roles/harvester_setup/
yamllint roles/harvester_setup/

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Molecule Tests
```bash
# Test role in isolation
cd /home/user/IdeaProjects/homelab-ansible
./test.sh test epyc-harvester-setup

# Expected: All tests pass, idempotency check succeeds
# If failing: Check prepare.yml has test secrets set
```

### Level 3: Integration Test
```yaml
# Test playbook for real deployment
---
- name: Test Harvester deployment
  hosts: harvester_nodes
  roles:
    - homelab.epyc.harvester_setup
  vars:
    harvester_test_mode: true  # Use test values
```

```bash
# Verify cluster health
kubectl --kubeconfig=/tmp/harvester-kubeconfig get nodes
# Expected: 3 nodes in Ready state

# Verify PCIe devices
kubectl --kubeconfig=/tmp/harvester-kubeconfig get pcidevices
# Expected: GPU devices listed as available

# Test Terraform
cd /tmp/terraform-test
terraform init
terraform plan
# Expected: Provider authenticates successfully
```

## Final validation Checklist
- [ ] All molecule tests pass: `./test.sh test epyc-harvester-setup`
- [ ] No ansible-lint errors: `ansible-lint roles/harvester_setup/`
- [ ] Cluster accessible via VIP
- [ ] All 3 nodes showing Ready status
- [ ] PCIe devices available for passthrough
- [ ] Storage network configured and active
- [ ] NTP synchronization working (check with `chronyc sources`)
- [ ] Terraform provider can list resources
- [ ] Documentation updated in README.md

---

## Anti-Patterns to Avoid
- ❌ Don't hardcode node IPs - use inventory variables
- ❌ Don't skip IOMMU group validation - will cause VM boot failures
- ❌ Don't ignore time sync - cluster will be unstable
- ❌ Don't overlap storage network with K8s ranges
- ❌ Don't modify /boot/grub/grub.cfg directly - use /oem files
- ❌ Don't enable passthrough without checking IOMMU groups
- ❌ Don't use same cluster token across environments
- ❌ Don't skip hardware validation - ensure requirements met

## Confidence Score: 9/10

High confidence due to:
- Comprehensive documentation and patterns from existing codebase
- Clear examples from vyos_setup to follow
- Detailed Harvester documentation available
- Well-defined network architecture
- Proven PCIe passthrough examples

Minor uncertainty around:
- Exact molecule test mocking for Harvester API
- Some node-specific hardware details may need adjustment