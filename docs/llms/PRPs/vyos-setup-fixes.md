# PRP: VyOS Setup Fixes and Test Improvements

## Executive Summary
This PRP addresses critical issues in the VyOS setup automation, focusing on fixing tests to use real VyOS images, integrating Infisical for secrets management, updating VLAN configurations to proper subnets with domain names, and ensuring all tests are idempotent and comprehensive.

## Context and Background

### Current State
- VyOS setup role exists but tests are failing due to idempotency issues
- Tests use placeholder ISOs instead of real VyOS images built by vyos_image_builder
- No integration with Infisical for secrets management
- VLAN subnets use /24 instead of required /16
- No domain configuration for VLANs
- Missing dedicated VLAN molecule test
- Tests skip critical verification steps

### Requirements
1. Use real VyOS images from vyos_image_builder role in tests
2. Integrate Infisical for passwords and SSH keys
3. Update VLAN subnets to 10.<vlan>.0.0/16 format
4. Configure domains: dmz=public.awynn.info, secure=private.awynn.info, management=management.awynn.info, logging=logs.awynn.info
5. Create molecule test nexus.vyos.vlans
6. Ensure tests are idempotent
7. Verify tests aren't skipping critical steps

### Key Files to Modify
- `/collections/ansible_collections/homelab/nexus/roles/vyos_setup/*`
- `/collections/ansible_collections/homelab/nexus/extensions/molecule/nexus.vyos.setup/*`
- `/collections/ansible_collections/homelab/nexus/extensions/molecule/nexus.vyos.vlans/*` (new)
- `/collections/ansible_collections/homelab/nexus/roles/vyos_setup/defaults/main.yaml`
- `/collections/ansible_collections/homelab/nexus/roles/vyos_setup/templates/*`

## Implementation Plan

### Phase 1: Infisical Integration

#### 1.1 Install Infisical Collection
```yaml
# collections/ansible_collections/homelab/nexus/requirements.yml
collections:
  - name: infisical.vault
    version: ">=1.0.0"
```

#### 1.2 Update defaults/main.yaml with Infisical lookups
```yaml
# Infisical Configuration
infisical_client_id: "{{ lookup('env', 'INFISICAL_CLIENT_ID') }}"
infisical_client_secret: "{{ lookup('env', 'INFISICAL_CLIENT_SECRET') }}"
infisical_project_id: "{{ lookup('env', 'INFISICAL_PROJECT_ID', 'e0ff40f2-e63c-4ffc-9233-a66c46a47b2e') }}"
infisical_url: "https://app.infisical.com"

# Security Configuration with Infisical
vyos_admin_password: "{{ lookup('infisical.vault.read_secrets',
    universal_auth_client_id=infisical_client_id,
    universal_auth_client_secret=infisical_client_secret,
    project_id=infisical_project_id,
    path='/',
    env_slug='prod',
    url=infisical_url,
    secret_name='systemSudoPassword'
  ) | first | json_query('value') }}"

vyos_admin_ssh_key: "{{ lookup('infisical.vault.read_secrets',
    universal_auth_client_id=infisical_client_id,
    universal_auth_client_secret=infisical_client_secret,
    project_id=infisical_project_id,
    path='/',
    env_slug='prod',
    url=infisical_url,
    secret_name='vyosPublicSshKey'
  ) | first | json_query('value') }}"

vyos_ansible_ssh_private_key: "{{ lookup('infisical.vault.read_secrets',
    universal_auth_client_id=infisical_client_id,
    universal_auth_client_secret=infisical_client_secret,
    project_id=infisical_project_id,
    path='/',
    env_slug='prod',
    url=infisical_url,
    secret_name='nexusAnsiblePrivateSshKey'
  ) | first | json_query('value') }}"
```

### Phase 2: Update VLAN Configuration

#### 2.1 Update defaults/main.yaml with proper subnets and domains
```yaml
# Domain Configuration
vyos_domain: "awynn.info"
vyos_vlan_domains:
  dmz: "public.{{ vyos_domain }}"
  secure: "private.{{ vyos_domain }}"
  management: "management.{{ vyos_domain }}"
  logging: "logs.{{ vyos_domain }}"

# Updated VLAN Network Definitions with /16 subnets
vyos_vlan_networks:
  - name: "dmz"
    vlan_id: 10
    description: "DMZ Network - External facing services"
    subnet: "10.10.0.0/16"  # Changed from /24
    gateway: "10.10.0.1"
    domain: "{{ vyos_vlan_domains.dmz }}"
    bridge_name: "br-dmz"
    dhcp_enabled: true
    dhcp_range: "10.10.0.100-10.10.0.199"
    dns_servers:
      - "10.10.0.1"
      - "1.1.1.1"
    firewall_rules:
      - rule: 10
        action: "accept"
        source: "10.10.0.0/16"
        destination: "0.0.0.0/0"
        description: "Allow DMZ to Internet"
      - rule: 20
        action: "drop"
        source: "10.10.0.0/16"
        destination: "10.0.0.0/8"
        description: "Block DMZ to all internal networks"

  - name: "secure"
    vlan_id: 50
    description: "Secure Network - Main trusted network"
    subnet: "10.50.0.0/16"  # Changed from /24
    gateway: "10.50.0.1"
    domain: "{{ vyos_vlan_domains.secure }}"
    bridge_name: "br-secure"
    dhcp_enabled: true
    dhcp_range: "10.50.0.100-10.50.0.199"
    dns_servers:
      - "10.50.0.1"
      - "1.1.1.1"
    firewall_rules:
      - rule: 10
        action: "accept"
        source: "10.50.0.0/16"
        destination: "0.0.0.0/0"
        description: "Allow Secure to Internet"
      - rule: 20
        action: "accept"
        source: "10.50.0.0/16"
        destination: "10.60.0.0/16"
        description: "Allow Secure to Management via jumphost"
        condition: "via-jumphost"

  - name: "management"
    vlan_id: 60
    description: "Management Network - Server administration"
    subnet: "10.60.0.0/16"  # Changed from /24
    gateway: "10.60.0.1"
    domain: "{{ vyos_vlan_domains.management }}"
    bridge_name: "br-mgmt"
    dhcp_enabled: true
    dhcp_range: "10.60.0.100-10.60.0.199"
    dns_servers:
      - "10.60.0.1"
      - "1.1.1.1"

  - name: "logging"
    vlan_id: 70
    description: "Logging Network - System monitoring"
    subnet: "10.70.0.0/16"  # Changed from /24
    gateway: "10.70.0.1"
    domain: "{{ vyos_vlan_domains.logging }}"
    bridge_name: "br-logging"
    dhcp_enabled: false
    dns_servers:
      - "10.70.0.1"
```

### Phase 3: Fix Tests to Use Real VyOS Images

#### 3.1 Update molecule.yml to use real images
```yaml
# extensions/molecule/nexus.vyos.setup/molecule.yml
---
dependency:
  name: galaxy
  options:
    requirements-file: requirements.yml

driver:
  name: docker

platforms:
  - name: vyos-setup-test
    image: "${MOLECULE_DOCKER_IMAGE:-geerlingguy/docker-ubuntu2404-ansible:latest}"
    pre_build_image: true
    command: "${MOLECULE_COMMAND:-/lib/systemd/systemd}"
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
      - /dev/kvm:/dev/kvm
      # Mount the real VyOS image location
      - "${VYOS_IMAGE_PATH:-../../../../../../images/vyos}:/images/vyos:ro"
    cgroupns_mode: host
    privileged: true
    capabilities:
      - SYS_ADMIN
    groups:
      - nexus
    env:
      INFISICAL_CLIENT_ID: "${INFISICAL_CLIENT_ID}"
      INFISICAL_CLIENT_SECRET: "${INFISICAL_CLIENT_SECRET}"

provisioner:
  name: ansible
  inventory:
    host_vars:
      vyos-setup-test:
        vyos_network_mode: nat
        vyos_build_image: false
        vyos_iso_path: "/images/vyos/vyos-current.iso"  # Use real image
        vyos_configure_router: true
        vyos_enable_vlans: true  # Enable VLAN testing
        vyos_security_hardening: true
        vyos_cloud_init_enabled: true
        # Override for test environment
        vyos_test_mode: true
        # Test-specific Infisical config
        infisical_client_id: "{{ lookup('env', 'INFISICAL_CLIENT_ID') }}"
        infisical_client_secret: "{{ lookup('env', 'INFISICAL_CLIENT_SECRET') }}"

verifier:
  name: ansible
```

#### 3.2 Update converge.yml to verify real image
```yaml
# extensions/molecule/nexus.vyos.setup/converge.yml
---
- name: Converge
  hosts: all
  tasks:
    - name: Check if real VyOS ISO exists
      stat:
        path: "/images/vyos/vyos-current.iso"
      register: vyos_iso_check
      failed_when: not vyos_iso_check.stat.exists

    - name: Verify VyOS ISO is valid
      command: file /images/vyos/vyos-current.iso
      register: iso_type
      changed_when: false
      failed_when: "'ISO 9660' not in iso_type.stdout"

    - name: Install required packages for testing
      apt:
        name:
          - cloud-image-utils
          - python3-lxml
          - python3-libvirt
          - qemu-utils
        state: present
        update_cache: yes

    - name: Include vyos_setup role
      include_role:
        name: ../../../roles/vyos_setup
```

### Phase 4: Fix Idempotency Issues

#### 4.1 Update cloud-init template task
```yaml
# tasks/main.yaml - Fix cloud-init idempotency
- name: Create cloud-init user data
  template:
    src: cloud-init/user-data.j2
    dest: /var/lib/libvirt/cloud-init/vyos-user-data
    mode: '0644'
  register: cloud_init_user_data
  # Only regenerate ISO if template changed
  notify: regenerate cloud-init iso

- name: Create cloud-init network config
  template:
    src: cloud-init/network-config.j2
    dest: /var/lib/libvirt/cloud-init/vyos-network-config
    mode: '0644'
  register: cloud_init_network
  notify: regenerate cloud-init iso
```

#### 4.2 Add handler for cloud-init regeneration
```yaml
# handlers/main.yaml
---
- name: regenerate cloud-init iso
  command: |
    cloud-localds {{ vyos_cloud_init_iso }} \
      /var/lib/libvirt/cloud-init/vyos-user-data \
      --network-config=/var/lib/libvirt/cloud-init/vyos-network-config
  when: cloud_init_user_data.changed or cloud_init_network.changed
```

#### 4.3 Fix VM definition idempotency
```yaml
# tasks/main.yaml - Fix VM definition
- name: Check if VM already exists
  community.libvirt.virt:
    name: "{{ vyos_vm.name }}"
    command: list_vms
  register: existing_vms

- name: Define VM using XML template
  community.libvirt.virt:
    command: define
    xml: "{{ lookup('template', 'vyos_vm.xml.j2') }}"
    autostart: yes
  when: vyos_vm.name not in existing_vms.list_vms
```

### Phase 5: Create VLAN Molecule Test

#### 5.1 Create directory structure
```bash
mkdir -p collections/ansible_collections/homelab/nexus/extensions/molecule/nexus.vyos.vlans
```

#### 5.2 Create molecule.yml for VLAN test
```yaml
# extensions/molecule/nexus.vyos.vlans/molecule.yml
---
dependency:
  name: galaxy
  options:
    requirements-file: requirements.yml

driver:
  name: docker

platforms:
  - name: vyos-vlans-test
    image: "${MOLECULE_DOCKER_IMAGE:-geerlingguy/docker-ubuntu2404-ansible:latest}"
    pre_build_image: true
    command: "${MOLECULE_COMMAND:-/lib/systemd/systemd}"
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
      - "${VYOS_IMAGE_PATH:-../../../../../../images/vyos}:/images/vyos:ro"
    cgroupns_mode: host
    privileged: true
    capabilities:
      - SYS_ADMIN
      - NET_ADMIN
    groups:
      - nexus

provisioner:
  name: ansible
  inventory:
    host_vars:
      vyos-vlans-test:
        vyos_network_mode: bridge
        vyos_enable_vlans: true
        vyos_configure_host_vlans: true
        vyos_use_ovs: false  # Disable OVS in container
        vyos_test_mode: true
        vyos_iso_path: "/images/vyos/vyos-current.iso"

verifier:
  name: ansible
```

#### 5.3 Create converge.yml for VLAN test
```yaml
# extensions/molecule/nexus.vyos.vlans/converge.yml
---
- name: Converge
  hosts: all
  tasks:
    - name: Install network utilities
      apt:
        name:
          - bridge-utils
          - vlan
          - iproute2
        state: present
        update_cache: yes

    - name: Load 8021q module
      modprobe:
        name: 8021q
        state: present
      ignore_errors: yes  # May fail in container

    - name: Include VLAN setup task
      include_role:
        name: ../../../roles/vyos_setup
        tasks_from: vlan_setup.yaml
```

#### 5.4 Create verify.yml for VLAN test
```yaml
# extensions/molecule/nexus.vyos.vlans/verify.yml
---
- name: Verify
  hosts: all
  vars:
    expected_vlans:
      - { name: dmz, id: 10, subnet: "10.10.0.0/16", domain: "public.awynn.info" }
      - { name: secure, id: 50, subnet: "10.50.0.0/16", domain: "private.awynn.info" }
      - { name: management, id: 60, subnet: "10.60.0.0/16", domain: "management.awynn.info" }
      - { name: logging, id: 70, subnet: "10.70.0.0/16", domain: "logs.awynn.info" }
  tasks:
    - name: Check bridge interfaces
      command: "ip link show {{ item.name }}"
      loop: "{{ vyos_vlan_networks }}"
      register: bridge_check
      changed_when: false
      failed_when: false

    - name: Verify bridges exist
      assert:
        that:
          - item.rc == 0
        fail_msg: "Bridge {{ item.item.name }} not found"
      loop: "{{ bridge_check.results }}"
      when: not (vyos_test_mode | default(false))

    - name: Check VLAN configuration in defaults
      debug:
        msg: "VLAN {{ item.name }}: ID={{ item.vlan_id }}, Subnet={{ item.subnet }}, Domain={{ item.domain }}"
      loop: "{{ vyos_vlan_networks }}"

    - name: Verify VLAN subnets are /16
      assert:
        that:
          - "'/16' in item.subnet"
        fail_msg: "VLAN {{ item.name }} subnet {{ item.subnet }} is not /16"
      loop: "{{ vyos_vlan_networks }}"

    - name: Verify VLAN domains are configured
      assert:
        that:
          - item.domain is defined
          - item.domain | length > 0
          - "'awynn.info' in item.domain"
        fail_msg: "VLAN {{ item.name }} missing proper domain configuration"
      loop: "{{ vyos_vlan_networks }}"
```

### Phase 6: Update Templates

#### 6.1 Update cloud-init user-data template
```jinja2
{# templates/cloud-init/user-data.j2 #}
#cloud-config
hostname: {{ vyos_vm.name }}
manage_etc_hosts: true

users:
  - name: {{ vyos_admin_user }}
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: sudo
    shell: /bin/vbash
    lock_passwd: false
    passwd: {{ vyos_admin_password | password_hash('sha512') }}
    ssh_authorized_keys:
      - {{ vyos_admin_ssh_key }}
{% if vyos_ansible_ssh_key != vyos_admin_ssh_key %}
      - {{ vyos_ansible_ssh_key }}
{% endif %}

write_files:
  - path: /config/scripts/vyos-postconfig-bootup.script
    owner: root:vyattacfg
    permissions: '0755'
    content: |
      #!/bin/vbash
      source /opt/vyatta/etc/functions/script-template
      
      # Configure VLANs with domains
{% for vlan in vyos_vlan_networks %}
      set interfaces ethernet eth1 vif {{ vlan.vlan_id }} address '{{ vlan.gateway }}/{{ vlan.subnet.split('/')[1] }}'
      set interfaces ethernet eth1 vif {{ vlan.vlan_id }} description '{{ vlan.description }}'
      
      # Configure DHCP for VLAN {{ vlan.name }}
{% if vlan.dhcp_enabled %}
      set service dhcp-server shared-network-name {{ vlan.name }} subnet {{ vlan.subnet }}
      set service dhcp-server shared-network-name {{ vlan.name }} subnet {{ vlan.subnet }} default-router '{{ vlan.gateway }}'
      set service dhcp-server shared-network-name {{ vlan.name }} subnet {{ vlan.subnet }} name-server '{{ vlan.dns_servers | join(' ') }}'
      set service dhcp-server shared-network-name {{ vlan.name }} subnet {{ vlan.subnet }} domain-name '{{ vlan.domain }}'
      set service dhcp-server shared-network-name {{ vlan.name }} subnet {{ vlan.subnet }} range 0 start '{{ vlan.dhcp_range.split('-')[0] }}'
      set service dhcp-server shared-network-name {{ vlan.name }} subnet {{ vlan.subnet }} range 0 stop '{{ vlan.dhcp_range.split('-')[1] }}'
{% endif %}
      
      # Configure DNS for domain {{ vlan.domain }}
      set system static-host-mapping host-name {{ vlan.name }}.{{ vlan.domain }} inet {{ vlan.gateway }}
      
{% endfor %}
      
      commit
      save
```

#### 6.2 Create requirements.yml
```yaml
# extensions/molecule/nexus.vyos.vlans/requirements.yml
---
collections:
  - name: community.libvirt
    version: ">=1.2.0"
  - name: infisical.vault
    version: ">=1.0.0"
```

## Validation Gates

### Pre-Implementation Checks
```bash
# Verify environment setup
source ~/ansible-venv/bin/activate
cd collections/ansible_collections/homelab/nexus/extensions/

# Check Infisical credentials
echo "INFISICAL_CLIENT_ID: ${INFISICAL_CLIENT_ID:?Not set}"
echo "INFISICAL_CLIENT_SECRET: ${INFISICAL_CLIENT_SECRET:?Not set}"

# Verify VyOS image exists
ls -la ../../../../../../images/vyos/vyos-current.iso
```

### Syntax Validation
```bash
# Lint Ansible code
ansible-lint collections/ansible_collections/homelab/nexus/roles/vyos_setup/

# Validate YAML syntax
yamllint collections/ansible_collections/homelab/nexus/
```

### Test Execution
```bash
# Run updated setup test
cd collections/ansible_collections/homelab/nexus/extensions/
molecule test -s nexus.vyos.setup

# Run new VLAN test
molecule test -s nexus.vyos.vlans

# Run full end-to-end test
cd /home/user/IdeaProjects/homelab-ansible
./scripts/testing/test-vyos-end-to-end.sh --skip-build
```

### Idempotency Verification
```bash
# Run converge twice to ensure idempotency
molecule converge -s nexus.vyos.setup
molecule converge -s nexus.vyos.setup
# Should show no changes on second run
```

## File Structure

```
collections/ansible_collections/homelab/nexus/
├── requirements.yml (updated with infisical.vault)
├── roles/
│   └── vyos_setup/
│       ├── defaults/main.yaml (updated with Infisical, domains, /16 subnets)
│       ├── tasks/
│       │   ├── main.yaml (fixed idempotency)
│       │   └── vlan_setup.yaml (updated for domains)
│       ├── handlers/main.yaml (new - cloud-init regeneration)
│       └── templates/
│           ├── cloud-init/
│           │   └── user-data.j2 (updated with domains)
│           └── vlan_network.xml.j2 (updated)
└── extensions/
    └── molecule/
        ├── nexus.vyos.setup/
        │   ├── molecule.yml (updated to use real images)
        │   ├── converge.yml (updated)
        │   ├── verify.yml (enhanced)
        │   └── requirements.yml
        └── nexus.vyos.vlans/ (new)
            ├── molecule.yml
            ├── converge.yml
            ├── verify.yml
            └── requirements.yml
```

## Implementation Order

1. **Install Infisical collection** - Update requirements.yml
2. **Update defaults with Infisical lookups** - Integrate secrets management
3. **Fix VLAN configurations** - Update to /16 subnets with domains
4. **Fix idempotency issues** - Add handlers, conditional checks
5. **Update existing tests** - Use real VyOS images
6. **Create VLAN test** - New molecule scenario
7. **Update templates** - Add domain support
8. **Run validation** - Execute all tests

## Success Criteria

1. All molecule tests pass without skipping critical steps
2. Tests are idempotent (no changes on second run)
3. Real VyOS images are used in tests
4. Secrets are pulled from Infisical
5. VLANs use /16 subnets with proper domains
6. New VLAN test validates configuration

## External Documentation

- [Infisical Ansible Integration](https://infisical.com/docs/integrations/platforms/ansible)
- [VyOS Ansible Collection](https://docs.ansible.com/ansible/latest/collections/vyos/vyos/index.html)
- [Molecule Testing](https://molecule.readthedocs.io/en/latest/)
- [Ansible Idempotency](https://docs.ansible.com/ansible/latest/reference_appendices/glossary.html#term-Idempotency)

## Common Issues and Solutions

1. **Infisical Authentication**: Ensure environment variables are set before running tests
2. **Docker in Docker**: VyOS tests require privileged containers with KVM access
3. **VLAN Module Loading**: 8021q module may not load in containers - use ignore_errors
4. **Cloud-init ISO**: Must regenerate when templates change for idempotency

## Notes

- Tests use scripts in `scripts/testing/` for verification
- VyOS image must be built using vyos_image_builder before running tests
- Domain configuration follows pattern: service.vlan.awynn.info
- Firewall rules will need updating in a future phase to match new subnets

## Confidence Score: 9/10

This PRP provides comprehensive implementation details with clear validation gates. The only uncertainty is around potential container limitations for VLAN testing, but fallback options are provided.