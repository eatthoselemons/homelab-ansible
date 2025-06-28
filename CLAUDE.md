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
# Activate virtual environment first
source ~/ansible-venv/bin/activate

# Test individual roles from collection extensions directory
cd collections/ansible_collections/homelab/nexus/extensions/
molecule test -s security_hardening
molecule test -s vyos_setup
molecule test -s services_vm_setup
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