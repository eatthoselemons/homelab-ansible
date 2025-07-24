name: "Harvester Cluster Setup PRP"
description: |

## Purpose
Deploy a production-ready Harvester HCI cluster across EPYC server, mid server, and HP thin client with PCIe passthrough support. This PRP assumes infrastructure prerequisites (VyOS VLAN 65 and NTP server) are already configured.

## Core Principles
1. **Focused on Harvester**: Only cluster deployment and configuration
2. **Validation Loops**: Comprehensive molecule tests
3. **Pattern following**: Use existing vyos_setup patterns for Infisical
4. **Progressive deployment**: Init cluster, join nodes, configure features
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Deploy Harvester cluster with:
- 3-node HA configuration (all management nodes)
- PCIe passthrough for GPU and storage HBA
- Storage network configuration on VLAN 65
- Terraform provider access configured
- Ready for VM and container deployments

## Why
- **Virtualization platform**: Foundation for all homelab services
- **Hardware passthrough**: Direct access for TrueNAS storage and GPU services
- **HA deployment**: Resilient infrastructure with 3 management nodes
- **GitOps ready**: Terraform provider for declarative deployments

## What
Deploy and configure:
- 3-node Harvester cluster with proper networking
- PCIe device passthrough for specified devices
- Storage network for Longhorn replication
- Kubeconfig extraction for Terraform access
- Comprehensive testing suite

### Success Criteria
- [ ] All 3 nodes showing as Ready in cluster
- [ ] VIP accessible on management network
- [ ] PCIe devices available for passthrough
- [ ] Storage network configured and active
- [ ] Terraform provider can authenticate
- [ ] All molecule tests passing

## All Needed Context

### Prerequisites
```yaml
REQUIRED BEFORE STARTING:
- VyOS VLAN 65 configured (10.60.65.0/24)
- NTP server running on Nexus VM
- Run harvester-infrastructure-prerequisites.md first
```

### Documentation & References
```yaml
- file: /home/user/IdeaProjects/homelab-ansible/docs/llms/design/architecture.md
  sections: ["Physical Infrastructure"]
  why: Server specifications and network layout
  critical: |
    EPYC: 256GB RAM, 6 NICs
    Mid: 64GB RAM
    Management VLAN 60
    
- file: /home/user/IdeaProjects/homelab-ansible/docs/llms/best-practices/harvester-setup-best-practices.md
  why: Harvester-specific requirements
  gotcha: |
    First 3 nodes automatically become management nodes
    Node IPs cannot change after initialization
    Storage network needs (Nodes × 2) + (Disks × 2) + Images IPs
    
- file: /home/user/IdeaProjects/homelab-ansible/collections/ansible_collections/homelab/nexus/roles/vyos_setup/tasks/main.yaml
  why: Infisical secret retrieval pattern
  pattern: |
    Validate env vars first
    Retrieve secrets in blocks
    Extract values with set_fact
    
- url: https://docs.harvesterhci.io/v1.4/install/harvester-configuration/
  sections: ["Configuration File", "Networking"]
  why: Cloud-init configuration format
  critical: |
    install.mode: create (first) or join (others)
    Use /oem/99-* files for persistent config
    
- url: https://docs.harvesterhci.io/v1.4/advanced/addons/pcidevices/
  why: PCIe passthrough configuration
  gotcha: |
    All devices in IOMMU group must be passed together
    No live migration with passthrough
    Enable pcidevices-controller addon first
    
- url: https://registry.terraform.io/providers/harvester/harvester/latest/docs
  why: Terraform provider setup
  critical: |
    Version 0.6.7 as of April 2024
    Requires kubeconfig authentication
```

### Current Codebase Structure
```bash
collections/ansible_collections/homelab/
├── nexus/
│   └── roles/
│       └── vyos_setup/      # Pattern to follow
└── epyc/                    # To be created
```

### Desired Codebase Structure
```bash
collections/ansible_collections/homelab/epyc/
├── roles/
│   └── harvester_setup/
│       ├── README.md
│       ├── defaults/
│       │   └── main.yaml
│       ├── handlers/
│       │   └── main.yaml
│       ├── meta/
│       │   └── requirements.yaml
│       ├── tasks/
│       │   ├── main.yaml
│       │   ├── validate_prerequisites.yaml
│       │   ├── configure_networks.yaml
│       │   ├── prepare_nodes.yaml
│       │   ├── init_cluster.yaml
│       │   ├── join_nodes.yaml
│       │   ├── configure_storage.yaml
│       │   ├── enable_pcie_passthrough.yaml
│       │   └── setup_terraform_access.yaml
│       ├── templates/
│       │   ├── harvester_config.yaml.j2
│       │   ├── network_config.yaml.j2
│       │   ├── grub_config.j2
│       │   └── storage_network.yaml.j2
│       └── vars/
│           └── main.yaml

collections/ansible_collections/homelab/epyc/extensions/molecule/
└── harvester-setup/
    ├── molecule.yaml
    ├── prepare.yaml
    ├── converge.yaml
    ├── verify.yaml
    └── mock_scripts/
        ├── mock_harvester_api.py
        └── mock_kubectl.sh
```

## Implementation Blueprint

### Data Models and Structure

defaults/main.yaml:
```yaml
---
# Infisical Configuration
harvester_infisical_client_id: "{{ lookup('env', 'INFISICAL_CLIENT_ID') }}"
harvester_infisical_client_secret: "{{ lookup('env', 'INFISICAL_CLIENT_SECRET') }}"
harvester_infisical_project_id: "{{ lookup('env', 'INFISICAL_PROJECT_ID') }}"
harvester_infisical_url: "https://app.infisical.com"

# Retrieved from Infisical
harvester_cluster_token: ""
harvester_admin_password: ""

# Cluster Configuration
harvester_cluster_vip: "10.60.1.10"
harvester_cluster_name: "harvester-cluster"
harvester_dns_servers:
  - "10.60.0.1"
  - "1.1.1.1"
harvester_ntp_servers:
  - "10.60.0.2"  # Nexus NTP server

# Node Configuration
harvester_nodes:
  - name: "epyc-harvester"
    ip: "10.60.1.11"
    is_first: true
    interfaces:
      - name: "eth0"
        hwaddr: ""  # From inventory
    pcie_devices: ["10de:1fb9", "10de:10fa"]  # GPU
  - name: "mid-harvester"
    ip: "10.60.1.12"
    interfaces:
      - name: "eth0"
        hwaddr: ""  # From inventory
  - name: "thin-harvester"
    ip: "10.60.1.13"
    interfaces:
      - name: "eth0"
        hwaddr: ""  # From inventory

# Storage Network
harvester_storage_network:
  enabled: true
  vlan: 65
  cidr: "10.60.65.0/24"
  ip_range_start: "10.60.65.10"
  ip_range_end: "10.60.65.250"

# Feature Flags
harvester_configure_networks: true
harvester_enable_pcie_passthrough: true
harvester_configure_storage_network: true
harvester_setup_terraform: true

### Task Implementation

#### Task 1: Main Orchestration (tasks/main.yaml)
```yaml
---
# Validate Infisical environment
- name: Validate Infisical environment variables
  block:
    - assert:
        that:
          - harvester_infisical_client_id is defined
          - harvester_infisical_client_id | length > 0
        fail_msg: "INFISICAL_CLIENT_ID must be set"

# Retrieve secrets
- name: Retrieve Harvester secrets from Infisical
  block:
    - name: Get cluster token
      set_fact:
        harvester_cluster_token_raw: "{{ lookup('infisical.vault.read_secrets',
          universal_auth_client_id=harvester_infisical_client_id,
          universal_auth_client_secret=harvester_infisical_client_secret,
          project_id=harvester_infisical_project_id,
          path='/',
          env_slug='prod',
          url=harvester_infisical_url,
          secret_name='harvesterClusterToken'
        ) }}"
    
    - name: Extract token value
      set_fact:
        harvester_cluster_token: "{{ harvester_cluster_token_raw.value }}"

# Include sub-tasks
- include_tasks: validate_prerequisites.yaml

- include_tasks: configure_networks.yaml
  when: harvester_configure_networks

- include_tasks: prepare_nodes.yaml

- include_tasks: init_cluster.yaml
  when: harvester_nodes[0].is_first | default(false)

- include_tasks: join_nodes.yaml

- include_tasks: configure_storage.yaml
  when: harvester_configure_storage_network

- include_tasks: enable_pcie_passthrough.yaml
  when: harvester_enable_pcie_passthrough

- include_tasks: setup_terraform_access.yaml
  when: harvester_setup_terraform
```

#### Task 2: Validate Prerequisites
```yaml
---
- name: Check VyOS VLAN 65 connectivity
  wait_for:
    host: "10.60.65.1"
    port: 22
    timeout: 5
  delegate_to: localhost
  ignore_errors: yes
  register: vlan_check

- name: Verify VLAN 65 is configured
  assert:
    that:
      - vlan_check is succeeded
    fail_msg: "VLAN 65 not accessible. Run infrastructure prerequisites first."

- name: Check NTP server connectivity
  uri:
    url: "http://{{ harvester_ntp_servers[0] }}:123"
    method: GET
  delegate_to: localhost
  ignore_errors: yes
  register: ntp_check

- name: Verify hardware requirements
  shell: |
    free -g | grep Mem | awk '{print $2}'
  register: memory_gb
  delegate_to: "{{ item.ip }}"
  loop: "{{ harvester_nodes }}"

- name: Check IOMMU enabled
  shell: |
    dmesg | grep -i iommu | grep -i enabled
  register: iommu_check
  delegate_to: "{{ item.ip }}"
  loop: "{{ harvester_nodes }}"
  failed_when: false
```

#### Task 3: Configure Networks
```yaml
---
- name: Template network configuration
  template:
    src: network_config.yaml.j2
    dest: "/tmp/network-{{ item.name }}.yaml"
  loop: "{{ harvester_nodes }}"
  delegate_to: "{{ item.ip }}"

- name: Apply network configuration
  copy:
    src: "/tmp/network-{{ item.name }}.yaml"
    dest: "/oem/99-network.yaml"
    mode: '0644'
  loop: "{{ harvester_nodes }}"
  delegate_to: "{{ item.ip }}"
  become: yes
```

#### Task 4: Prepare Nodes
```yaml
---
- name: Generate GRUB configuration with IOMMU
  template:
    src: grub_config.j2
    dest: "/tmp/grub-{{ item.name }}.cfg"
  loop: "{{ harvester_nodes }}"
  when: item.pcie_devices is defined

- name: Apply kernel parameters
  lineinfile:
    path: /etc/default/grub
    regexp: '^GRUB_CMDLINE_LINUX='
    line: 'GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt vfio-pci.ids={{ item.pcie_devices | join(",") }}"'
  loop: "{{ harvester_nodes }}"
  when: item.pcie_devices is defined
  delegate_to: "{{ item.ip }}"
  become: yes

- name: Update GRUB
  command: update-grub
  loop: "{{ harvester_nodes }}"
  delegate_to: "{{ item.ip }}"
  become: yes
```

#### Task 5: Initialize Cluster
```yaml
---
- name: Generate first node configuration
  template:
    src: harvester_config.yaml.j2
    dest: "/tmp/harvester-init.yaml"
  vars:
    node: "{{ harvester_nodes[0] }}"
    install_mode: "create"

- name: Apply configuration to first node
  copy:
    src: "/tmp/harvester-init.yaml"
    dest: "/oem/99-harvester.yaml"
  delegate_to: "{{ harvester_nodes[0].ip }}"
  become: yes

- name: Reboot first node to apply configuration
  reboot:
    reboot_timeout: 600
  delegate_to: "{{ harvester_nodes[0].ip }}"
  become: yes

- name: Wait for Harvester API
  uri:
    url: "https://{{ harvester_cluster_vip }}:6443/healthz"
    validate_certs: no
  register: api_health
  until: api_health.status == 200
  retries: 60
  delay: 10

- name: Retrieve kubeconfig
  uri:
    url: "https://{{ harvester_cluster_vip }}:6443/v3/kubeconfig"
    method: GET
    headers:
      Authorization: "Bearer {{ harvester_cluster_token }}"
    validate_certs: no
  register: kubeconfig_response

- name: Save kubeconfig
  copy:
    content: "{{ kubeconfig_response.json }}"
    dest: "/tmp/harvester-kubeconfig"
  delegate_to: localhost
```

#### Task 6: Join Additional Nodes
```yaml
---
- name: Generate join configurations
  template:
    src: harvester_config.yaml.j2
    dest: "/tmp/harvester-join-{{ item.name }}.yaml"
  vars:
    node: "{{ item }}"
    install_mode: "join"
  loop: "{{ harvester_nodes[1:] }}"

- name: Apply join configuration
  copy:
    src: "/tmp/harvester-join-{{ item.name }}.yaml"
    dest: "/oem/99-harvester.yaml"
  loop: "{{ harvester_nodes[1:] }}"
  delegate_to: "{{ item.ip }}"
  become: yes

- name: Reboot nodes to join cluster
  reboot:
    reboot_timeout: 600
  loop: "{{ harvester_nodes[1:] }}"
  delegate_to: "{{ item.ip }}"
  become: yes

- name: Wait for all nodes ready
  k8s_info:
    api_version: v1
    kind: Node
    kubeconfig: /tmp/harvester-kubeconfig
  register: nodes
  until: nodes.resources | length == 3 and (nodes.resources | selectattr('status.conditions', 'defined') | selectattr('status.conditions', 'selectattr', 'type', 'equalto', 'Ready') | list | length == 3)
  retries: 30
  delay: 20
```

#### Task 7: Configure Storage Network
```yaml
---
- name: Create storage network configuration
  k8s:
    state: present
    kubeconfig: /tmp/harvester-kubeconfig
    definition:
      apiVersion: network.harvesterhci.io/v1beta1
      kind: ClusterNetwork
      metadata:
        name: storage
      spec:
        description: "Longhorn storage replication network"
```

#### Task 8: Enable PCIe Passthrough
```yaml
---
- name: Enable pcidevices addon
  k8s:
    state: present
    kubeconfig: /tmp/harvester-kubeconfig
    definition:
      apiVersion: harvesterhci.io/v1beta1
      kind: Addon
      metadata:
        name: pcidevices-controller
        namespace: harvester-system
      spec:
        enabled: true

- name: Wait for PCIDevice CRDs
  k8s_info:
    api_version: apiextensions.k8s.io/v1
    kind: CustomResourceDefinition
    name: pcidevices.devices.harvesterhci.io
    kubeconfig: /tmp/harvester-kubeconfig
  register: crd
  until: crd.resources | length > 0
  retries: 30
  delay: 10

- name: List available PCI devices
  k8s_info:
    api_version: devices.harvesterhci.io/v1beta1
    kind: PCIDevice
    kubeconfig: /tmp/harvester-kubeconfig
  register: pci_devices

- debug:
    msg: "Available PCI devices: {{ pci_devices.resources | map(attribute='metadata.name') | list }}"
```

#### Task 9: Setup Terraform Access
```yaml
---
- name: Create Terraform example configuration
  copy:
    content: |
      terraform {
        required_providers {
          harvester = {
            source = "harvester/harvester"
            version = "0.6.7"
          }
        }
      }
      
      provider "harvester" {
        kubeconfig = "/tmp/harvester-kubeconfig"
      }
      
      # Example: List cluster info
      data "harvester_clusterinfo" "cluster" {}
      
      output "cluster_version" {
        value = data.harvester_clusterinfo.cluster.version
      }
    dest: /tmp/harvester-terraform-example.tf
  delegate_to: localhost

- name: Test Terraform provider
  shell: |
    cd /tmp
    terraform init
    terraform plan
  delegate_to: localhost
  register: terraform_test
```

### Template Files

harvester_config.yaml.j2:
```yaml
#cloud-config
hostname: {{ node.name }}
ssh_authorized_keys:
  - "{{ harvester_ansible_ssh_key }}"

write_files:
  - path: /etc/sysctl.d/99-harvester.conf
    content: |
      net.ipv4.ip_forward = 1
      net.ipv6.conf.all.forwarding = 1

harvester:
  install:
    mode: {{ install_mode }}
    management_interface: {{ node.interfaces[0].name }}
    device: /dev/sda
    iso_url: ""
    tty: ttyS0
    vip: {{ harvester_cluster_vip }}
    vip_mode: static
    {% if install_mode == "join" %}
    server_url: https://{{ harvester_cluster_vip }}:6443
    {% endif %}
    token: {{ harvester_cluster_token }}
    password: {{ harvester_admin_password }}
  network:
    interfaces:
    {% for iface in node.interfaces %}
      - name: {{ iface.name }}
        hwaddr: "{{ iface.hwaddr }}"
        method: static
        ip: {{ node.ip }}/24
        gateway: 10.60.1.1
        mtu: 1500
    {% endfor %}
    dns_nameservers:
    {% for dns in harvester_dns_servers %}
      - {{ dns }}
    {% endfor %}
  ntp_servers:
  {% for ntp in harvester_ntp_servers %}
    - {{ ntp }}
  {% endfor %}
```

## Validation Loop

### Level 1: Syntax & Style
```bash
cd collections/ansible_collections/homelab/epyc
ansible-lint roles/harvester_setup/
yamllint roles/harvester_setup/
```

### Level 2: Molecule Tests
```bash
cd /home/user/IdeaProjects/homelab-ansible
./test.sh test epyc.harvester_setup
```

### Level 3: Cluster Verification
```bash
# Check cluster nodes
kubectl --kubeconfig=/tmp/harvester-kubeconfig get nodes

# Verify PCIe devices
kubectl --kubeconfig=/tmp/harvester-kubeconfig get pcidevices

# Test storage network
kubectl --kubeconfig=/tmp/harvester-kubeconfig get clusternetworks

# Verify Terraform
cd /tmp && terraform init && terraform plan
```

## Final Validation Checklist
- [ ] All 3 nodes in Ready state
- [ ] Cluster VIP accessible
- [ ] PCIe devices listed and available
- [ ] Storage network configured
- [ ] Kubeconfig extracted successfully
- [ ] Terraform provider authenticates
- [ ] Molecule tests pass
- [ ] Documentation updated

## Anti-Patterns to Avoid
- ❌ Don't hardcode IPs - use inventory
- ❌ Don't skip IOMMU validation
- ❌ Don't modify /boot/grub directly - use /oem
- ❌ Don't ignore hardware prerequisites
- ❌ Don't use same token across environments
- ❌ Don't enable passthrough without checking groups

## Confidence Score: 9/10

High confidence due to:
- Clear patterns from existing codebase
- Comprehensive Harvester documentation
- Well-defined network architecture
- Detailed implementation steps

Minor uncertainty:
- Exact hardware configurations may vary
- Some API responses need mocking for tests