# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a homelab infrastructure automation project using Ansible to manage network equipment, VyOS, virtual routers, and server provisioning. The architecture includes VM orchestration, container management, and GitOps deployment.

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
export INFISICAL_CLIENT_SECRET=<secret>
ansible-playbook -u user router/default.yaml

# Setup VyOS router system
ansible-playbook vyos/setup-base-system.yaml
```

### Inventory and Configuration
- `server-inventory.yaml`: Defines host groups (upspi, fast-host, router)
- `ansible.cfg`: Sets default inventory and Python interpreter
- `versions/router.json`: Version pinning for specific packages

## Secret Management

All sensitive data (API keys, passwords) is managed through Infisical:
- Cloud bootstrap for initial setup
- Self-hosted instance post-deployment
- Router playbooks require `INFISICAL_CLIENT_SECRET` environment variable
- API keys retrieved dynamically from Infisical vault during playbook execution

## Development Workflow

1. Edit playbooks in respective directories (`router/`, `vyos/`)
2. Update inventory hosts in `server-inventory.yaml` as needed
3. Pin package versions in `versions/router.json` for reproducible builds
4. Test playbooks against development environment before production

## Key Integration Points

- **VyOS**: VM provisioning through LibVirt with custom XML templates
- **LibVirt**: VM lifecycle management, networking bridges, storage volumes
- **Infisical**: Dynamic secret retrieval for API authentication
- **systemd-networkd**: Network configuration through ansible_systemd role

## File Structure Context

- `bootstrap-*.sh`: System and Ansible environment setup scripts
- `vyos/`: VyOS router VM provisioning and configuration
- `docs/`: Project documentation and AI prompts
- `versions/`: Package version constraints for reproducible deployments