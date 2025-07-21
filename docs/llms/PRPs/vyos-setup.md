# VyOS Setup Fix - Project Requirements Plan (PRP)

## Executive Summary

This PRP outlines the implementation plan to fix the VyOS setup and testing in the homelab environment. The current setup fails to properly install the VyOS operating system, lacks security hardening, and needs comprehensive molecule testing. This implementation will leverage the `stafwag/ansible-role-delegated_vm_install` role for proper VM installation and include building VyOS images using Docker.

## Context and References

### Critical Documentation URLs
- VyOS Build Documentation: https://docs.vyos.io/en/latest/contributing/build-vyos.html
- VyOS Ansible Module Documentation: https://docs.ansible.com/ansible/latest/collections/vyos/vyos/index.html
- Delegated VM Install Role: https://github.com/stafwag/ansible-role-delegated_vm_install
- VyOS Cloud-Init: https://docs.vyos.io/en/latest/installation/cloud/index.html
- Zone-based Firewall: https://docs.vyos.io/en/latest/configuration/firewall/zone.html
- VyOS Security Hardening: https://forum.vyos.io/t/vyos-configuration-tips-for-enhancing-network-security/11087

### Local Documentation References
- Molecule Testing Documentation: `/home/user/IdeaProjects/homelab-ansible/references/molecule/docs`
- Delegated VM Install Documentation: `/home/user/IdeaProjects/homelab-ansible/references/ansible-role-delegated_vm_install/README.md`
- Architecture Overview: `/home/user/IdeaProjects/homelab-ansible/docs/llms/design/architecture.md`
- Security Best Practices: `/home/user/IdeaProjects/homelab-ansible/docs/llms/examples/best-practices.md`

### Existing Codebase References
- Current VyOS Role: `/home/user/IdeaProjects/homelab-ansible/collections/ansible_collections/homelab/nexus/roles/vyos_setup/`
- Molecule Test Examples: `/home/user/IdeaProjects/homelab-ansible/collections/ansible_collections/homelab/nexus/extensions/molecule/`
- VM Setup Pattern: `/home/user/IdeaProjects/homelab-ansible/collections/ansible_collections/homelab/nexus/roles/services_vm_setup/`

## Current State Analysis

### Issues Identified
1. **No OS Installation**: VM created but ISO path commented out in `templates/vyos_vm.xml.j2`
2. **Missing Cloud-Init**: No cloud-init configuration for initial setup
3. **Incomplete Testing**: Basic molecule test exists but doesn't verify functionality
4. **Security Gaps**: Default user not removed, firewall not properly configured

### Architecture Context
From `docs/llms/design/architecture.md`:
- Nexus Node runs LibVirt hosting VyOS router VM
- Network topology: Internet → Modem → Nexus:Port1(WAN) → VyOS VM → Nexus:Port2(LAN)
- 7 VLANs configured: DMZ(10), Untrusted WiFi(20), Trusted WiFi(30), IoT(40), Secure(50), Management(60), Logging(70)

## Implementation Blueprint

### Phase 1: VyOS Image Building
As specified in the feature requirements, build VyOS image using Docker method:

```pseudocode
1. Create role: vyos_image_builder
   - Install Docker prerequisites
   - Clone VyOS build repository  
   - Run Docker container build process
   - Save ISO to ignored directory
   
2. Directory structure:
   collections/ansible_collections/homelab/nexus/
   └── images/
       └── vyos/
           ├── .gitignore (*.iso, *.qcow2)
           └── README.md
```

### Phase 2: Integrate delegated_vm_install Role
Refactor vyos_setup to properly install VM with OS:

```pseudocode
1. Install delegated_vm_install and dependencies:
   - stafwag.libvirt
   - stafwag.qemu_img
   - stafwag.cloud_localds
   - stafwag.virt_install_import
   
2. Configure delegated_vm_install:
   - Use built VyOS ISO as boot_disk.src
   - Set up dual network interfaces (WAN/LAN)
   - Configure minimal cloud-init
```

### Phase 3: Security Hardening
Based on `docs/llms/examples/best-practices.md`:

```pseudocode
1. User Management:
   - Create admin user with strong password
   - Add SSH key authentication
   - Delete default "vyos" user
   
2. Firewall Configuration:
   - Default deny on input/forward chains
   - Stateful connection tracking
   - Zone-based firewall for VLANs
   - Rate limiting on SSH
   
3. System Hardening:
   - SSH on port 2222
   - Disable password authentication
   - Configure fail2ban
   - Set up NTP without server mode
```

### Phase 4: Comprehensive Testing

```pseudocode
Test scenarios:
1. nexus.vyos.setup - VM creation and boot
2. nexus.vyos.security_hardening - Security verification  
3. nexus.vyos.full_integration - Complete VLAN setup
```

## Detailed Implementation Tasks

### Task 1: Create VyOS Image Builder Role
**Location**: `collections/ansible_collections/homelab/nexus/roles/vyos_image_builder/`

```yaml
# defaults/main.yaml
---
vyos_build_dir: /tmp/vyos-build
vyos_images_dir: "{{ playbook_dir }}/../images/vyos"
vyos_version: current
vyos_architecture: amd64

# tasks/main.yaml
---
- name: Check if VyOS image already exists
  stat:
    path: "{{ vyos_images_dir }}/vyos-{{ vyos_version }}.iso"
  register: vyos_image

- name: Build VyOS image
  when: not vyos_image.stat.exists
  block:
    - name: Install Docker and dependencies
      apt:
        name:
          - docker.io
          - git
          - curl
        state: present

    - name: Ensure Docker service is running
      systemd:
        name: docker
        state: started
        enabled: yes

    - name: Create build directory
      file:
        path: "{{ vyos_build_dir }}"
        state: directory
        mode: '0755'

    - name: Clone VyOS build repository
      git:
        repo: https://github.com/vyos/vyos-build.git
        dest: "{{ vyos_build_dir }}/vyos-build"
        version: "{{ vyos_version }}"

    - name: Pull VyOS build Docker image
      docker_image:
        name: vyos/vyos-build:{{ vyos_version }}
        source: pull

    - name: Build VyOS ISO using Docker
      docker_container:
        name: vyos-builder
        image: vyos/vyos-build:{{ vyos_version }}
        command: |
          bash -c "./build-vyos-image iso 
            --architecture {{ vyos_architecture }} 
            --build-by 'homelab-ansible' 
            --build-type release"
        volumes:
          - "{{ vyos_build_dir }}/vyos-build:/vyos"
        working_dir: /vyos
        detach: no
        cleanup: yes

    - name: Ensure images directory exists
      file:
        path: "{{ vyos_images_dir }}"
        state: directory
        mode: '0755'

    - name: Find built ISO
      find:
        paths: "{{ vyos_build_dir }}/vyos-build/build"
        patterns: "vyos-*.iso"
      register: built_iso

    - name: Copy ISO to images directory
      copy:
        src: "{{ built_iso.files[0].path }}"
        dest: "{{ vyos_images_dir }}/vyos-{{ vyos_version }}.iso"
        remote_src: yes
        mode: '0644'
```

### Task 2: Refactor vyos_setup Role
**Location**: `collections/ansible_collections/homelab/nexus/roles/vyos_setup/`

```yaml
# tasks/main.yaml - Updated structure
---
- name: Build VyOS image if needed
  include_role:
    name: homelab.nexus.vyos_image_builder
  when: vyos_build_image | default(false)

- name: Install libvirt and dependencies
  apt:
    name:
      - qemu-kvm
      - libvirt-daemon-system
      - libvirt-clients
      - bridge-utils
      - python3-libvirt
      - cloud-image-utils
    state: present
    update_cache: yes

- name: Start and enable libvirtd
  systemd:
    name: libvirtd
    state: started
    enabled: yes

- name: Create required directories
  file:
    path: "{{ item }}"
    state: directory
    owner: libvirt-qemu
    group: kvm
    mode: '0755'
  loop:
    - /var/lib/libvirt/images
    - /var/lib/libvirt/cloud-init

- name: Check for VyOS ISO
  stat:
    path: "{{ vyos_iso_path | default(vyos_images_dir + '/vyos-current.iso') }}"
  register: vyos_iso
  failed_when: not vyos_iso.stat.exists
  vars:
    vyos_images_dir: "{{ playbook_dir }}/../images/vyos"

- name: Create cloud-init user data
  template:
    src: cloud-init/user-data.j2
    dest: /var/lib/libvirt/cloud-init/vyos-user-data
    mode: '0644'

- name: Create cloud-init network config
  template:
    src: cloud-init/network-config.j2
    dest: /var/lib/libvirt/cloud-init/vyos-network-config
    mode: '0644'

- name: Generate cloud-init ISO
  command: |
    cloud-localds /var/lib/libvirt/images/vyos-cloud-init.iso \
      /var/lib/libvirt/cloud-init/vyos-user-data \
      --network-config=/var/lib/libvirt/cloud-init/vyos-network-config
  args:
    creates: /var/lib/libvirt/images/vyos-cloud-init.iso

- name: Deploy VyOS VM using delegated_vm_install
  include_role:
    name: stafwag.delegated_vm_install
  vars:
    vm_ip_address: "{{ vyos_vm_ip }}"
    vm_kvm_host: "{{ inventory_hostname }}"
    delegated_vm_install:
      post:
        pause:
          seconds: 30
        update_etc_hosts: false
        ensure_running: true
        package_update: false
        reboot_after_update: false
      vm:
        hostname: "{{ vyos_vm.name }}"
        path: "/var/lib/libvirt/images/"
        boot_disk:
          src: "{{ vyos_iso.stat.path }}"
        size: "{{ vyos_vm.disk_size }}"
        disks:
          - dest: "/var/lib/libvirt/images/vyos-cloud-init.iso"
            format: raw
            src: "/var/lib/libvirt/images/vyos-cloud-init.iso"
            type: cdrom
        memory: "{{ vyos_vm.memory }}"
        vcpus: "{{ vyos_vm.vcpus }}"
        interface: "eth0"
        gateway: "{{ ansible_default_ipv4.gateway | default('192.168.122.1') }}"
        dns_nameservers: "{{ vyos_dns_servers | join(',') }}"
        wait: 0
        poweroff: false
        reboot: false

- name: Configure libvirt networks
  include_tasks: configure_networks.yaml

- name: Wait for VyOS to be accessible
  wait_for:
    host: "{{ vyos_vm_ip }}"
    port: "{{ vyos_ssh_port }}"
    delay: 60
    timeout: 600

- name: Apply VyOS configuration
  include_tasks: vyos_config.yaml
  when: vyos_configure_router | default(true)

- name: Apply security hardening
  include_tasks: security_hardening.yaml
  when: vyos_security_hardening | default(true)

- name: Configure VLANs
  include_tasks: vlan_setup.yaml
  when: vyos_enable_vlans | default(true)
```

### Task 3: Cloud-Init Templates
**Location**: `collections/ansible_collections/homelab/nexus/roles/vyos_setup/templates/cloud-init/`

```yaml
# user-data.j2
#cloud-config
vyos_config_commands:
  # System configuration
  - set system host-name '{{ vyos_vm.name | default("vyos-router") }}'
  - set system time-zone 'UTC'
  
  # Temporary user for initial access
  - set system login user vyos authentication plaintext-password 'temp-{{ lookup('password', '/dev/null length=16') }}'
  - set system login user vyos authentication public-keys ansible type 'ssh-rsa'
  - set system login user vyos authentication public-keys ansible key '{{ vyos_ansible_ssh_key }}'
  
  # Basic interface configuration
  - set interfaces ethernet eth0 description 'WAN'
  - set interfaces ethernet eth0 address 'dhcp'
  - set interfaces ethernet eth1 description 'LAN'
  - set interfaces ethernet eth1 address '{{ vyos_vm_ip }}/24'
  
  # Enable SSH
  - set service ssh port '{{ vyos_ssh_port }}'
  - set service ssh disable-password-authentication
  
  # Save configuration
  - commit
  - save

# network-config.j2
version: 2
ethernets:
  eth0:
    dhcp4: true
  eth1:
    addresses: [{{ vyos_vm_ip }}/24]
```

### Task 4: Security Hardening
**Location**: `collections/ansible_collections/homelab/nexus/roles/vyos_setup/tasks/security_hardening.yaml`

```yaml
---
- name: Create admin user
  vyos.vyos.vyos_user:
    name: "{{ vyos_admin_user }}"
    configured_password: "{{ vyos_admin_password | password_hash('sha512') }}"
    state: present

- name: Add SSH key for admin user
  vyos.vyos.vyos_config:
    lines:
      - set system login user {{ vyos_admin_user }} authentication public-keys admin@homelab type 'ssh-rsa'
      - set system login user {{ vyos_admin_user }} authentication public-keys admin@homelab key '{{ vyos_admin_ssh_key }}'

- name: Configure firewall default policies
  vyos.vyos.vyos_config:
    lines:
      # Default policies
      - set firewall ipv4 input filter default-action 'drop'
      - set firewall ipv4 forward filter default-action 'drop'
      - set firewall ipv4 output filter default-action 'accept'
      
      # State policies
      - set firewall global-options state-policy established action 'accept'
      - set firewall global-options state-policy related action 'accept'
      - set firewall global-options state-policy invalid action 'drop'

- name: Configure firewall rules
  vyos.vyos.vyos_config:
    lines:
      # Allow SSH from management network with rate limiting
      - set firewall ipv4 input filter rule 100 action 'accept'
      - set firewall ipv4 input filter rule 100 destination port '{{ vyos_ssh_port }}'
      - set firewall ipv4 input filter rule 100 protocol 'tcp'
      - set firewall ipv4 input filter rule 100 source address '10.60.0.0/24'
      - set firewall ipv4 input filter rule 100 limit rate '3/minute'
      
      # Allow DHCP
      - set firewall ipv4 input filter rule 200 action 'accept'
      - set firewall ipv4 input filter rule 200 destination port '67-68'
      - set firewall ipv4 input filter rule 200 protocol 'udp'
      
      # Allow DNS
      - set firewall ipv4 input filter rule 300 action 'accept'
      - set firewall ipv4 input filter rule 300 destination port '53'
      - set firewall ipv4 input filter rule 300 protocol 'tcp_udp'

- name: Configure SSH hardening
  vyos.vyos.vyos_config:
    lines:
      - set service ssh ciphers 'aes256-gcm@openssh.com'
      - set service ssh ciphers 'chacha20-poly1305@openssh.com'
      - set service ssh ciphers 'aes256-ctr'
      - set service ssh mac 'hmac-sha2-256-etm@openssh.com'
      - set service ssh mac 'hmac-sha2-512-etm@openssh.com'
      - set service ssh key-exchange 'curve25519-sha256@libssh.org'
      - set service ssh key-exchange 'diffie-hellman-group-exchange-sha256'

- name: Delete default vyos user
  vyos.vyos.vyos_user:
    name: vyos
    state: absent

- name: Configure fail2ban
  vyos.vyos.vyos_config:
    src: templates/vyos_fail2ban.j2
```

### Task 5: Molecule Test Scenarios

#### Test 1: nexus.vyos.setup
**Location**: `collections/ansible_collections/homelab/nexus/extensions/molecule/nexus.vyos.setup/`

```yaml
# molecule.yaml
---
dependency:
  name: galaxy
  options:
    requirements-file: requirements.yaml

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
    cgroupns_mode: host
    privileged: true
    capabilities:
      - SYS_ADMIN
    groups:
      - nexus

provisioner:
  name: ansible
  inventory:
    host_vars:
      vyos-setup-test:
        vyos_network_mode: nat
        vyos_build_image: false
        vyos_iso_path: /tmp/test-vyos.iso
        vyos_configure_router: true
        vyos_enable_vlans: false
        vyos_security_hardening: false

verifier:
  name: ansible

# converge.yaml
---
- name: Converge
  hosts: all
  tasks:
    - name: Create test VyOS ISO placeholder
      command: truncate -s 500M /tmp/test-vyos.iso
      args:
        creates: /tmp/test-vyos.iso

    - name: Include vyos_setup role
      include_role:
        name: homelab.nexus.vyos_setup

# verify.yaml
---
- name: Verify
  hosts: all
  tasks:
    - name: Check if VM is defined
      command: virsh list --all
      register: vm_list
      changed_when: false

    - name: Verify VyOS VM exists
      assert:
        that:
          - "'vyos-router' in vm_list.stdout"
        fail_msg: "VyOS VM not found in libvirt"

    - name: Check if VM is running
      command: virsh domstate vyos-router
      register: vm_state
      changed_when: false

    - name: Verify VM is running
      assert:
        that:
          - vm_state.stdout == "running"
        fail_msg: "VyOS VM is not running"
```

#### Test 2: nexus.vyos.security_hardening
```yaml
# verify.yaml
---
- name: Verify security hardening
  hosts: all
  vars:
    ansible_user: "{{ vyos_admin_user | default('admin') }}"
    ansible_ssh_private_key_file: "{{ vyos_admin_ssh_key_file }}"
    ansible_port: "{{ vyos_ssh_port | default(2222) }}"
  tasks:
    - name: Gather VyOS configuration
      vyos.vyos.vyos_facts:
        gather_subset:
          - config
      delegate_to: "{{ vyos_vm_ip }}"

    - name: Verify firewall default policies
      assert:
        that:
          - ansible_net_config is search('firewall ipv4 input filter default-action drop')
          - ansible_net_config is search('firewall ipv4 forward filter default-action drop')
        fail_msg: "Firewall default policies not properly configured"

    - name: Check if default user exists
      vyos.vyos.vyos_command:
        commands:
          - show configuration commands | grep "system login user vyos"
      delegate_to: "{{ vyos_vm_ip }}"
      register: default_user_check
      failed_when: default_user_check.stdout != ""

    - name: Verify SSH hardening
      assert:
        that:
          - ansible_net_config is search('service ssh port 2222')
          - ansible_net_config is search('service ssh disable-password-authentication')
        fail_msg: "SSH not properly hardened"
```

## Desired Directory Structure

```
collections/ansible_collections/homelab/nexus/
├── roles/
│   ├── vyos_image_builder/
│   │   ├── defaults/main.yaml
│   │   ├── tasks/main.yaml
│   │   ├── handlers/main.yaml
│   │   └── README.md
│   └── vyos_setup/
│       ├── defaults/main.yaml
│       ├── tasks/
│       │   ├── main.yaml
│       │   ├── configure_networks.yaml
│       │   ├── vyos_config.yaml
│       │   ├── security_hardening.yaml
│       │   ├── vlan_setup.yaml
│       │   └── fail2ban.yaml
│       ├── templates/
│       │   ├── cloud-init/
│       │   │   ├── user-data.j2
│       │   │   └── network-config.j2
│       │   ├── vyos_vm_template.yaml
│       │   ├── vyos_firewall_config.j2
│       │   ├── vyos_fail2ban.j2
│       │   └── *.xml.j2 (network configs)
│       ├── handlers/main.yaml
│       └── meta/
│           └── requirements.yaml
├── extensions/molecule/
│   ├── nexus.vyos.setup/
│   ├── nexus.vyos.security_hardening/
│   └── nexus.vyos.full_integration/
└── images/
    └── vyos/
        ├── .gitignore
        └── README.md
```

## Validation Gates

```bash
# Pre-execution checks
cd /home/user/IdeaProjects/homelab-ansible/collections/ansible_collections/homelab/nexus/extensions/

# Verify current directory
echo $PWD

# Activate virtual environment
source ~/ansible-venv/bin/activate

# Syntax validation
molecule syntax -s nexus.vyos.setup
molecule syntax -s nexus.vyos.security_hardening
molecule syntax -s nexus.vyos.full_integration

# Individual test execution
molecule test -s nexus.vyos.setup
molecule test -s nexus.vyos.security_hardening
molecule test -s nexus.vyos.full_integration

# Debugging failed tests
molecule converge -s nexus.vyos.setup
molecule verify -s nexus.vyos.setup
molecule destroy -s nexus.vyos.setup
```

## Error Handling Strategy

1. **Image Build Failures**:
   ```yaml
   - name: Fallback to pre-built image
     get_url:
       url: "{{ vyos_fallback_iso_url }}"
       dest: "{{ vyos_images_dir }}/vyos-fallback.iso"
     when: vyos_build_failed | default(false)
   ```

2. **VM Installation Failures**:
   - Check libvirt permissions: `usermod -aG libvirt,kvm ansible`
   - Verify KVM support: `kvm-ok`
   - Check disk space: `df -h /var/lib/libvirt`

3. **Configuration Failures**:
   - Use `vyos_config` with `backup: yes`
   - Implement rollback on failure
   - Log all changes to `/var/log/ansible-vyos.log`

## Implementation Order

1. **Day 1**: Create vyos_image_builder role and test build process
2. **Day 2**: Update vyos_setup with delegated_vm_install integration
3. **Day 3**: Implement cloud-init templates and test VM boot
4. **Day 4**: Apply security hardening configurations
5. **Day 5**: Create comprehensive molecule tests
6. **Day 6**: Full integration testing and documentation
7. **Day 7**: Production deployment preparation

## Success Criteria Checklist

- [ ] VyOS ISO successfully built using Docker method
- [ ] VM boots with VyOS operating system installed
- [ ] Cloud-init applies initial configuration
- [ ] SSH accessible on port 2222 with key authentication
- [ ] Default vyos user removed after admin user created
- [ ] Firewall configured with default-deny policies
- [ ] All VLANs properly configured and isolated
- [ ] Fail2ban operational and blocking brute force attempts
- [ ] Molecule tests pass consistently
- [ ] Configuration is idempotent
- [ ] Documentation complete with troubleshooting guide

## Known Challenges and Mitigations

1. **VyOS Cloud-Init Limitations**:
   - VyOS uses custom cloud-init implementation
   - Solution: Keep cloud-init minimal, do complex config via SSH

2. **Docker Build Requirements**:
   - Needs ~20GB disk space and 4GB RAM
   - Solution: Pre-build images on capable system

3. **Nested Virtualization in Tests**:
   - Docker containers need KVM access
   - Solution: Use privileged containers with /dev/kvm mounted

4. **Network Interface Ordering**:
   - MAC addresses must be consistent
   - Solution: Explicitly set MAC in VM definition

5. **Test Environment Limitations**:
   - Can't test bridge mode in containers
   - Solution: Use NAT mode for tests, document bridge setup

## Quality Score: 9/10

**High Confidence Areas**:
- Comprehensive implementation plan with detailed code examples
- Clear testing strategy with executable validation gates
- Strong security implementation based on best practices
- Detailed error handling and troubleshooting guides

**Areas Requiring Attention**:
- VyOS cloud-init exact syntax may need adjustment
- Build process timing depends on system resources
- Bridge networking testing requires physical hardware

This PRP provides a complete roadmap for implementing a secure, tested VyOS setup that addresses all requirements from the feature specification.