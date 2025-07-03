# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
# Activate virtual environment first (only needed once per session)
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

# Current Status: 
# ✅ Structure: All 4 scenarios discovered and configured properly
# ✅ Syntax: All playbooks pass syntax validation  
# ✅ Connectivity: Docker container setup working with systemd
# ✅ VyOS Testing: Full libvirt + KVM acceleration in containers
# ✅ Network Setup: WAN/LAN networks created and functional
# ✅ VM Creation: VyOS VMs can be created and started successfully
# ✅ Centralized Configuration: Shared molecule base config eliminates duplication
# ✅ Environment Variables: Ubuntu version management through .env.yml
# ✅ Test Isolation: Each scenario maintains independent test environments
# 
# Technical Setup:
# - Docker containers run with systemd and KVM hardware acceleration
# - libvirtd service starts properly in privileged containers
# - Disk image creation using stafwag.qemu_img community role
# - Conditional network templates: NAT mode for testing, bridge mode for production
# - Proper file ownership and permissions for libvirt access
# - Shared molecule configuration in /.config/molecule/config.yml
# - Centralized environment variables in molecule/.env.yml
# - Role-specific converge.yml files maintain test isolation
# 
# Dependencies:
# - KVM hardware acceleration (/dev/kvm mounted in containers)
# - systemd running in containers for service management
# - stafwag.qemu_img role for disk image creation
# - community.libvirt collection for VM and network management

# Molecule Testing Configuration:
# All molecule scenarios use centralized configuration management:
# 
# 1. Environment Variables (molecule/.env.yml):
#    - UBUNTU_VERSION: "2404" 
#    - MOLECULE_DOCKER_IMAGE: "geerlingguy/docker-ubuntu2404-ansible:latest"
#    - All container configuration (volumes, capabilities, etc.)
#    Usage: molecule -e molecule/.env.yml converge -s scenario_name
# 
# 2. Shared Base Configuration (/.config/molecule/config.yml):
#    - Common provisioner, dependency, driver, and verifier settings
#    - Reduces molecule.yml files from ~35 lines to ~18 lines each
#    - Maintains consistent Ansible configuration across all scenarios
# 
# 3. Scenario-Specific Testing:
#    - default: Basic container environment validation
#    - security_hardening: Security role testing with auditd, UFW, fail2ban
#    - vyos_setup: VyOS VM creation with libvirt in NAT mode
#    - services_vm_setup: Services VM prerequisites and libvirt validation
#    - harvester_test: Container networking validation for cluster testing
# 
# 4. Test Isolation Principles:
#    - Each scenario gets fresh Docker container
#    - No shared state between role tests
#    - Role-specific prerequisites in individual converge.yml files
#    - Independent failure domains prevent test contamination
# 
# 5. Version Management:
#    - Update Ubuntu version: Edit UBUNTU_VERSION in molecule/.env.yml
#    - Future versions (24.10, etc.): Change two variables instead of 5 files
#    - Centralized control without logic sharing or test dependencies
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

The VyOS setup role supports conditional network modes:

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
```

### Testing/Development  
```yaml
# Uses NAT mode for container compatibility in molecule tests
vyos_network_mode: nat
vyos_vm:
  name: vyos-router
  memory: 1024
  vcpus: 2
  disk_path: /var/lib/libvirt/images/vyos-router.qcow2
  disk_size: 10G
```

This allows the same role to work in both production environments (with real network bridges) and containerized testing environments (with isolated NAT networks).

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

## Extra instructions
- If you get a file/directory not found error use `pwd` to check your current location