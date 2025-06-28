# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a homelab infrastructure automation project using Ansible to manage network equipment, VyOS virtual routers, and server provisioning. The architecture includes VM orchestration, container management, and GitOps deployment with the Nexus node as the central management hub.

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
# Set required environment variables
export ANSIBLE_USER=<your-ssh-user>
export INFISICAL_CLIENT_SECRET=<secret>

# Setup Nexus node (primary workload)
ansible-playbook nexus/setup-nexus.yaml

# Alternative site playbook for role-based execution
ansible-playbook nexus/site.yml --tags="system,security"

# Legacy VyOS setup
ansible-playbook vyos/setup-base-system.yaml
```

### Testing with Molecule
```bash
# Test individual roles
cd nexus/
molecule test -s security_hardening
molecule test -s vyos_setup
molecule test -s services_vm_setup
```

## Inventory Structure

- `ansible.cfg`: Updated configuration with role paths and Galaxy settings
- `server-inventory.yaml`: Legacy inventory for simple host definitions
- `inventory.yml`: Modern YAML inventory with detailed nexus configuration
- `nexus/vars/ports.yaml`: Service port mappings for VM configurations

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

1. Edit roles in `nexus/roles/` directory structure
2. Update inventory in `inventory.yml` for nexus configurations
3. Test with Molecule before deployment
4. Use tags for selective role execution
5. Version constraints in `versions/` directory

## Key Integration Points

- **LibVirt**: VM lifecycle through custom XML templates
- **Network Bridges**: OVS for VM networking isolation
- **Infisical Vault**: Dynamic secret retrieval during playbook execution  
- **Security Auditing**: Comprehensive logging and monitoring
- **GitOps**: ArgoCD for infrastructure deployment automation

## File Structure Context

- `nexus/`: Main deployment directory with roles, playbooks, and tests
- `nexus/roles/`: Modular components (system_setup, security_hardening, vyos_setup, services_vm_setup)
- `nexus/molecule/`: Testing scenarios for roles
- `bootstrap-*.sh`: Environment setup scripts
- `versions/`: Package version pinning
- `docs/`: Architecture documentation and prompts