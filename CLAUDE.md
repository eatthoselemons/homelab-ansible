# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Guidelines

### Ansible Best Practices

**DO:**
- Use YAML anchors and aliases to reduce duplication
- Implement proper error handling with `failed_when` and `ignore_errors`
- Use Ansible Vault for sensitive data, Infisical for runtime secrets
- Follow collection namespace conventions: `homelab.nexus.role_name`
- Test all roles with molecule before deployment
- Use meaningful task names that describe the action
- Implement idempotency - tasks should be safe to run multiple times
- Use `check_mode` compatible tasks where possible
- Document role variables in `meta/main.yml`

**DON'T:**
- Hardcode sensitive values in playbooks or roles
- Use `shell` module when `command` or specialized modules exist
- Mix site-specific configuration in collection roles
- Skip error handling for external dependencies
- Use `become: yes` without considering security implications

### Code Structure

- **Roles**: Single-purpose, reusable components in collection
- **Variables**: Use `defaults/main.yml` for overridable defaults, `vars/main.yml` for constants
- **Templates**: Jinja2 templates in `templates/` directory
- **Handlers**: Service restarts and notifications in `handlers/main.yml`
- **Testing**: Molecule scenarios for each role with proper isolation

### Error Handling

```yaml
# Example of proper error handling
- name: Configure service
  template:
    src: service.conf.j2
    dest: /etc/service/service.conf
  notify: restart service
  failed_when: false
  register: config_result

- name: Fail on configuration error
  fail:
    msg: "Service configuration failed: {{ config_result.stderr }}"
  when: config_result.rc != 0 and 'already exists' not in config_result.stderr
```

## Project Overview

This is a homelab infrastructure automation project using Ansible to manage network equipment, VyOS virtual routers, and server provisioning. The project is structured as two main sections:

1. **Reusable Collection** (`collections/`): The `homelab.nexus` Ansible collection containing reusable roles and playbooks
2. **Site Implementation** (`site/`): Site-specific inventory, playbooks, and configurations that use the collection

The architecture includes VM orchestration, container management, and GitOps deployment with the Nexus node as the central management hub.

## Core Architecture

- **Nexus Node**: LibVirt host running VyOS router VM and services
- **Physical Servers**: EPYC server (primary), mid server, thin clients 
- **Network**: VyOS-based software routing with VLAN segmentation (10=DMZ, 20=untrusted WiFi, 30=trusted WiFi, 40=IoT, 50=secure, 60=management, 70=logging)
- **Security**: Infisical for secrets management, TPM integration for encryption keys
- **Storage**: TrueNAS with ZFS RAIDZ2, Harvester CSI for containers

## Essential Commands

### Setup Environment
```bash
# Install system dependencies (run as sudo)
sudo ./bootstrap-system.sh $HOME

# Activate Python virtual environment
source ~/ansible-venv/bin/activate

# Install Ansible collections and roles
./bootstrap-ansible.sh
```

### Running Playbooks
```bash
# Activate virtual environment first
source ~/ansible-venv/bin/activate

# Navigate to site directory
cd site/

# Install collection dependencies
ansible-galaxy install -r requirements.yml

# Set required environment variables
export ANSIBLE_USER=<your-ssh-user>
export INFISICAL_CLIENT_SECRET=<secret>

# Setup Nexus node (primary workload)
ansible-playbook playbooks/setup-nexus.yaml

# Alternative site playbook for role-based execution
ansible-playbook playbooks/site.yml --tags="system,security"
```

### Testing with Molecule
```bash
# Activate virtual environment first
source ~/ansible-venv/bin/activate

# Navigate to collection test directory
cd collections/ansible_collections/homelab/nexus/extensions/

# Run tests - all scenarios are fully functional
molecule list
molecule test -s security_hardening
molecule test -s vyos_setup
molecule test -s services_vm_setup

# Alternative: syntax check only (faster for development)
molecule syntax -s security_hardening

# For faster iteration during development, use converge:
molecule converge -s vyos_setup

# Note: Virtual environment activation persists throughout the session
# No need to reactivate unless you open a new terminal

# Available test scenarios: default, security_hardening, vyos_setup, services_vm_setup, harvester_test
# All scenarios use centralized configuration from molecule/.env.yml and /.config/molecule/config.yml
```

## Repository Structure

### Collection Structure (`collections/ansible_collections/homelab/nexus/`)
- `roles/`: Reusable roles (system_setup, security_hardening, vyos_setup, services_vm_setup, argocd_setup)
- `vars/`: Default variables including service port mappings
- `extensions/molecule/`: Testing scenarios for all roles
- `galaxy.yml`: Collection metadata and dependencies

### Site Structure (`site/`)
- `inventory.yml`: Site-specific inventory with nexus host configuration
- `ansible.cfg`: Site-specific Ansible configuration pointing to collection
- `playbooks/`: Site-specific playbooks using homelab.nexus collection
- `requirements.yml`: Collection dependencies
- `group_vars/` & `host_vars/`: Variable overrides for site-specific configurations

## Secret Management

All sensitive data managed through Infisical with dynamic retrieval:
- SSH keys retrieved from Infisical vault
- System passwords from secret store
- API credentials for service integrations
- Environment variables: `INFISICAL_CLIENT_SECRET` required

## Nexus Node Components

### VyOS Router VM
- 4GB RAM, 2 vCPUs, 20GB disk
- WAN interface on `enp1s0f0`, LAN on `enp1s0f1`
- Security: Fail2ban, audit logging, firewall rules
- SSH on port 2222, web interface on 443

### Services VM
- 4GB RAM, 2 vCPUs, 40GB disk
- Internal services: ArgoCD (8080), iPXE (8083), Control-D DNS (8084), DHCP (67)
- Handles network boot and GitOps deployment
- SSH on port 2223

### Security Hardening
- UFW firewall with restrictive policies
- Auditd for system monitoring
- Automated security updates via unattended-upgrades
- SSH hardening and fail2ban protection
- System-wide security policies

## Development Workflow

1. **Collection Development**: Edit roles in `collections/ansible_collections/homelab/nexus/roles/`
2. **Testing**: Test roles using molecule from `collections/ansible_collections/homelab/nexus/extensions/`
3. **Site Configuration**: Update `site/inventory.yml` and variable overrides for specific deployments
4. **Deployment**: Run playbooks from `site/` directory using collection syntax
5. **Collection Distribution**: Package and distribute collection using `ansible-galaxy collection build`

## VyOS Network Configuration

The VyOS setup role supports conditional network modes and uses native VyOS modules for configuration:

### Production (Default)
```yaml
# Uses bridge mode with OpenVSwitch for real hardware integration
# No vyos_network_mode variable needed - defaults to 'bridge'
vyos_vm:
  name: vyos-router
  memory: 4096
  vcpus: 2
  disk_path: /var/lib/libvirt/images/vyos-router.qcow2
  disk_size: 20G
vyos_configure_router: true  # Enable full VyOS configuration
```

### Testing/Development  
```yaml
# Uses NAT mode for container compatibility in molecule tests
vyos_network_mode: nat
vyos_configure_router: false  # Skip VyOS configuration in tests
vyos_vm:
  name: vyos-router
  memory: 1024
  vcpus: 2
  disk_path: /var/lib/libvirt/images/vyos-router.qcow2
  disk_size: 10G
```

This allows the same role to work in both production environments (with real network bridges) and containerized testing environments (with isolated NAT networks).

### VyOS Configuration Best Practices

**Native Module Usage:**
- Use `vyos.vyos.vyos_config` module for all VyOS configuration
- Avoid bash scripts - use structured Ansible configuration blocks
- Use proper connection variables for network device access
- Implement idempotent configuration with `save: true`

**Connection Management:**
```yaml
vars:
  ansible_network_os: vyos
  ansible_host: "{{ vyos_vm_ip }}"
  ansible_port: "{{ vyos_ssh_port }}"
  ansible_user: vyos
  ansible_connection: ansible.netcommon.network_cli
```

**Task Organization:**
- `vyos_ssh_setup.yaml` - SSH key management and initial access
- `vyos_config.yaml` - Network interfaces, services, and basic configuration
- `vyos_firewall.yaml` - Firewall rules and security policies
- Logical separation improves maintainability and testing

**Error Handling:**
- Use `ignore_errors: true` for SSH connectivity tests
- Implement proper `when` conditions for configuration tasks
- Use `rescue` blocks for graceful failure handling

## Key Integration Points

- **LibVirt**: VM lifecycle through custom XML templates
- **Network Bridges**: OVS for VM networking isolation
- **Infisical Vault**: Dynamic secret retrieval during playbook execution  
- **Security Auditing**: Comprehensive logging and monitoring
- **GitOps**: ArgoCD for infrastructure deployment automation

## File Structure Context

- `collections/`: Ansible collections for reusable infrastructure components
- `site/`: Site-specific implementation using the homelab.nexus collection
- `bootstrap-*.sh`: Environment setup scripts
- `versions/`: Package version pinning
- `docs/`: Architecture documentation and prompts

## Troubleshooting

### Common Issues

**Environment Setup:**
- **Error:** `ansible-playbook: command not found`
  - **Solution:** Activate Python virtual environment: `source ~/ansible-venv/bin/activate`

**Molecule Testing:**
- **Error:** `Permission denied` accessing `/dev/kvm`
  - **Solution:** Add user to kvm group: `sudo usermod -a -G kvm $USER`

**VyOS VM Issues:**
- **Error:** VM fails to start with network errors
  - **Solution:** Check network mode configuration, use `nat` for testing

**Secret Management:**
- **Error:** Infisical secrets not found
  - **Solution:** Verify `INFISICAL_CLIENT_SECRET` environment variable is set

### Debugging Tips

```bash
# Check current directory if file/directory not found
pwd

# Verbose Ansible output
ansible-playbook -vvv playbooks/setup-nexus.yaml

# Test molecule scenario without cleanup
molecule converge -s scenario_name

# Check molecule containers
docker ps -a

# Inspect role variables
ansible-inventory --list
```