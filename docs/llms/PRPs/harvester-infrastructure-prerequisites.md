name: "Harvester Infrastructure Prerequisites PRP"
description: |

## Purpose
Configure essential infrastructure prerequisites for Harvester deployment including storage VLAN on VyOS and NTP server on Nexus VM. This PRP focuses on network and time synchronization setup required before Harvester cluster initialization.

## Core Principles
1. **Focused scope**: Only VyOS VLAN and NTP server configuration
2. **Validation Loops**: Executable molecule tests for each component
3. **Pattern following**: Use existing vyos_setup patterns
4. **Independence**: Can be run and tested separately from Harvester
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Prepare infrastructure for Harvester deployment:
- Add storage VLAN 65 to VyOS with stateful firewall rules
- Deploy containerized NTP server on Nexus VM using 11notes/chrony
- Ensure both components are tested and verified before Harvester deployment

## Why
- **Storage VLAN**: Required for Longhorn replication traffic isolation
- **NTP Server**: Critical for Harvester etcd cluster stability
- **Separation**: Allows testing infrastructure before complex Harvester deployment

## What
- Extend VyOS configuration with storage VLAN 65 (10.60.65.0/24)
- Deploy secure, minimal NTP server container on Nexus
- Create comprehensive molecule tests for both components

### Success Criteria
- [ ] VyOS VLAN 65 configured and accessible
- [ ] Firewall rules using stateful tracking
- [ ] NTP server running and accessible from management network
- [ ] All molecule tests passing
- [ ] Documentation updated

## All Needed Context

### Documentation & References
```yaml
- file: /home/user/IdeaProjects/homelab-ansible/collections/ansible_collections/homelab/nexus/roles/vyos_setup/defaults/main.yaml
  why: VLAN configuration pattern to follow
  critical: |
    VLANs defined in vyos_vlan_networks list
    Each VLAN has firewall_rules array
    Use same structure for consistency
    
- url: https://github.com/11notes/docker-chrony
  why: NTP server container documentation
  critical: |
    Scratch-based distroless image (1.22MB)
    Runs as non-root user (UID 1000)
    Config volume: /chrony/etc
    Read-only filesystem
    
- file: /home/user/IdeaProjects/homelab-ansible/docs/llms/design/architecture.md
  sections: ["Network Design"]
  why: Network architecture and VLAN strategy
  critical: |
    Management VLAN 60: 10.60.0.0/16
    Storage within management subnet: 10.60.65.0/24
```

### Current Codebase Structure
```bash
collections/ansible_collections/homelab/nexus/roles/
├── vyos_setup/
│   ├── defaults/main.yaml    # Contains vyos_vlan_networks list
│   ├── tasks/main.yaml
│   └── templates/
└── [to be created] ntp_server/
```

### Desired Codebase Structure
```bash
collections/ansible_collections/homelab/nexus/roles/
├── vyos_setup/
│   └── defaults/main.yaml    # Add storage VLAN to vyos_vlan_networks
└── ntp_server/
    ├── README.md
    ├── defaults/
    │   └── main.yaml         # NTP configuration variables
    ├── tasks/
    │   └── main.yaml         # Container deployment tasks
    ├── templates/
    │   ├── docker-compose.yml.j2
    │   └── chrony.conf.j2
    └── handlers/
        └── main.yaml         # Container restart handler

collections/ansible_collections/homelab/nexus/extensions/molecule/
└── ntp-server/
    ├── molecule.yml
    ├── prepare.yml
    ├── converge.yml
    └── verify.yml
```

## Implementation Blueprint

### Task 1: Add Storage VLAN to VyOS Configuration
MODIFY collections/ansible_collections/homelab/nexus/roles/vyos_setup/defaults/main.yaml:
Add to vyos_vlan_networks list:
```yaml
  - name: "storage"
    vlan_id: 65
    description: "Storage Network - Harvester Longhorn replication"
    subnet: "10.60.65.0/24"
    gateway: "10.60.65.1"
    domain: "storage.{{ vyos_domain }}"
    bridge_name: "br-storage"
    dhcp_enabled: false
    dns_servers:
      - "10.60.65.1"
    firewall_rules:
      - rule: 5
        action: "accept"
        state: 
          established: true
          related: true
        description: "Allow established and related connections"
      - rule: 10
        action: "accept"
        source: "10.60.65.0/24"
        destination: "10.60.65.0/24"
        state:
          new: true
        description: "Allow new storage replication between nodes"
      - rule: 20
        action: "accept"
        source: "10.60.0.0/16"
        destination: "10.60.65.0/24"
        state:
          new: true
        description: "Allow management to initiate connections to storage"
      - rule: 30
        action: "drop"
        source: "10.60.65.0/24"
        destination: "0.0.0.0/0"
        description: "Block storage from initiating Internet connections"
      - rule: 40
        action: "drop"
        source: "10.60.65.0/24"
        destination: "10.0.0.0/8"
        description: "Block storage from initiating connections to other VLANs"
```

### Task 2: Create NTP Server Role Structure
CREATE collections/ansible_collections/homelab/nexus/roles/ntp_server/:
- Follow vyos_setup pattern for directory structure
- Create all directories and base files

### Task 3: Implement NTP Server defaults/main.yaml
```yaml
---
# NTP Server Configuration
ntp_timezone: "UTC"
ntp_container_name: "ntp-server"
ntp_container_image: "11notes/chrony:4.7"
ntp_config_path: "/opt/chrony"

# NTP pools to use
ntp_pools:
  - "ch.pool.ntp.org iburst maxsources 5"
  - "ntp.ubuntu.com iburst maxsources 5"

# Networks allowed to query NTP
ntp_allowed_networks:
  - "10.60.0.0/16"  # Management network
  - "10.50.0.0/16"  # Secure network
```

### Task 4: Implement NTP Server tasks/main.yaml
```yaml
---
- name: Create NTP configuration directory
  file:
    path: "{{ ntp_config_path }}/etc"
    state: directory
    mode: '0755'

- name: Template chrony configuration
  template:
    src: chrony.conf.j2
    dest: "{{ ntp_config_path }}/etc/chrony.conf"
    mode: '0644'
  notify: restart ntp container

- name: Deploy chrony container via docker-compose
  template:
    src: docker-compose.yml.j2
    dest: "{{ ntp_config_path }}/docker-compose.yml"
    mode: '0644'
  notify: restart ntp container

- name: Start NTP server container
  docker_compose:
    project_src: "{{ ntp_config_path }}"
    state: present
```

### Task 5: Create NTP Templates
chrony.conf.j2:
```
# Managed by Ansible - do not edit
{% for pool in ntp_pools %}
pool {{ pool }}
{% endfor %}

maxupdateskew 10.0
makestep 1 -1
driftfile /run/chrony/drift

# Allow NTP clients
{% for network in ntp_allowed_networks %}
allow {{ network }}
{% endfor %}

# Logging
clientloglimit 268435456
```

docker-compose.yml.j2:
```yaml
---
version: '3.8'
services:
  {{ ntp_container_name }}:
    image: "{{ ntp_container_image }}"
    container_name: "{{ ntp_container_name }}"
    read_only: true
    restart: unless-stopped
    environment:
      TZ: "{{ ntp_timezone }}"
    volumes:
      - "{{ ntp_config_path }}/etc:/chrony/etc:ro"
    ports:
      - "123:123/udp"
    tmpfs:
      - /run/chrony:size=10M,mode=1750,uid=1000,gid=1000
```

### Task 6: Create NTP Server Handlers
handlers/main.yaml:
```yaml
---
- name: restart ntp container
  docker_compose:
    project_src: "{{ ntp_config_path }}"
    restarted: yes
```

### Task 7: Create Molecule Tests for NTP Server
CREATE molecule/ntp-server/molecule.yml:
```yaml
---
dependency:
  name: galaxy
driver:
  name: docker
platforms:
  - name: nexus-ntp-test
    image: geerlingguy/docker-ubuntu2404-ansible:latest
    pre_build_image: true
    privileged: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:rw
    command: /lib/systemd/systemd
provisioner:
  name: ansible
  playbooks:
    converge: ${MOLECULE_PLAYBOOK:-converge.yml}
verifier:
  name: ansible
```

### Task 8: Create NTP Test Files
prepare.yml:
```yaml
---
- name: Prepare
  hosts: all
  tasks:
    - name: Install Docker
      apt:
        name:
          - docker.io
          - python3-docker
        state: present
        update_cache: yes
      become: yes

    - name: Ensure docker service is running
      service:
        name: docker
        state: started
        enabled: yes
      become: yes
```

converge.yml:
```yaml
---
- name: Converge
  hosts: all
  become: yes
  roles:
    - role: homelab.nexus.ntp_server
```

verify.yml:
```yaml
---
- name: Verify
  hosts: all
  tasks:
    - name: Check chrony.conf exists
      stat:
        path: /opt/chrony/etc/chrony.conf
      register: chrony_conf

    - name: Assert chrony.conf exists
      assert:
        that:
          - chrony_conf.stat.exists
        fail_msg: "chrony.conf was not created"

    - name: Verify chrony.conf contains allow rules
      lineinfile:
        path: /opt/chrony/etc/chrony.conf
        line: "{{ item }}"
        state: present
      check_mode: yes
      register: conf_check
      failed_when: conf_check.changed
      loop:
        - "allow 10.60.0.0/16"
        - "allow 10.50.0.0/16"

    - name: Verify docker-compose.yml exists
      stat:
        path: /opt/chrony/docker-compose.yml
      register: compose_file

    - name: Assert docker-compose.yml exists
      assert:
        that:
          - compose_file.stat.exists
        fail_msg: "docker-compose.yml was not created"

    - name: Check container image in docker-compose
      lineinfile:
        path: /opt/chrony/docker-compose.yml
        regexp: '.*image:.*11notes/chrony:4.7.*'
        state: present
      check_mode: yes
      register: image_check
      failed_when: image_check.changed
```

## Validation Loop

### Level 1: Syntax & Style
```bash
cd collections/ansible_collections/homelab/nexus
ansible-lint roles/ntp_server/
yamllint roles/ntp_server/
```

### Level 2: Molecule Tests
```bash
cd /home/user/IdeaProjects/homelab-ansible
./test.sh test nexus-ntp-server
```

### Level 3: Manual Verification
```bash
# After deployment to test environment
# Check VLAN 65 exists on VyOS
ssh vyos@router "show interfaces ethernet eth0 vif 65"

# Test NTP server
ntpdate -q nexus.management.domain
```

## Final Validation Checklist
- [ ] Storage VLAN added to vyos_vlan_networks
- [ ] NTP server role created with all files
- [ ] Molecule tests pass for NTP server
- [ ] chrony.conf properly templated
- [ ] docker-compose.yml uses 11notes/chrony:4.7
- [ ] Container runs with read-only filesystem
- [ ] Firewall rules use stateful tracking
- [ ] Documentation updated

## Anti-Patterns to Avoid
- ❌ Don't create VyOS commands manually - use vyos_vlan_networks
- ❌ Don't run NTP as root - use 11notes container
- ❌ Don't allow NTP from all networks - restrict to internal
- ❌ Don't skip molecule tests
- ❌ Don't hardcode values - use variables

## Confidence Score: 9/10

High confidence because:
- Clear patterns from vyos_setup to follow
- Simple scope with two focused components
- Well-documented container image
- Straightforward testing approach