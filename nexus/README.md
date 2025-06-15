# Nexus Node Configuration

This directory contains the Ansible configuration for setting up and maintaining the Nexus node, which serves as the central management node for the homelab infrastructure.

## Overview

The Nexus node is responsible for:
- Hosting the VyOS router VM (WAN-facing)
- Hosting the Services VM (internal services)
- Managing network boot services
- DNS resolution
- GitOps deployment orchestration

## Directory Structure

```
nexus/
├── roles/                    # Ansible roles for different components
│   ├── security_hardening/   # System security (fail2ban, audit, SSH)
│   │   ├── tasks/           # Tasks to execute
│   │   ├── handlers/        # Service handlers
│   │   └── templates/       # Configuration templates
│   ├── vyos_setup/          # VyOS router VM setup
│   │   ├── tasks/
│   │   └── templates/
│   ├── services_vm_setup/   # Services VM setup
│   │   ├── tasks/
│   │   └── templates/
│   └── system_setup/        # Base system configuration
│       ├── tasks/
│       ├── handlers/
│       └── templates/
├── vars/                    # Variable definitions
│   └── ports.yaml          # Port configurations
├── tasks/                  # Additional tasks
├── templates/             # Additional templates
├── handlers/             # Additional handlers
└── setup-nexus.yaml      # Main playbook
```

## Prerequisites

1. Ansible installed on the control node
2. SSH access to the Nexus node
3. Infisical secrets configured for:
   - System sudo password
   - Any service-specific secrets

## Network Configuration

The Nexus node uses two network interfaces:
- WAN: `enp1s0f0`
- LAN: `enp1s0f1`

## Security Features

The security hardening role implements:
- UFW firewall configuration
- Fail2ban for SSH protection
- Audit logging (host system only)
- Automatic security updates
- SSH hardening
- Log rotation

## VM Configuration

### VyOS VM (WAN-facing)
- 4GB RAM
- 2 vCPUs
- 20GB disk space
- Network interfaces bridged to physical interfaces
- Security features:
  - Fail2ban for SSH and web interface
  - Audit logging for configuration changes
  - Firewall rules for WAN interface

### Services VM (Internal)
- 4GB RAM
- 2 vCPUs
- 40GB disk space
- Connected to LAN network
- Services:
  - ArgoCD (GitOps deployment)
    - Manages initial infrastructure deployment
    - Will be replaced by Harvester ArgoCD
  - iPXE (Network boot)
    - Serves boot images for all nodes
    - MAC-based image selection
  - Control-D (DNS)
    - Internal DNS resolution
    - Custom domain management
  - DHCP Server
    - Network configuration for all nodes
    - MAC-based IP assignment

## Usage

1. Update the inventory with the correct IP address
2. Set required environment variables:
   ```bash
   export ANSIBLE_USER=<your-ssh-user>
   export INFISICAL_CLIENT_SECRET=<your-secret>
   ```
3. Run the playbook:
   ```bash
   ansible-playbook -i ../server-inventory.yaml setup-nexus.yaml
   ```

## Maintenance

- All configuration is managed through Ansible
- System updates are automated through unattended-upgrades
- Security logs are monitored through auditd
- VM configurations are version controlled

## Future Improvements

- [ ] Implement backup automation
- [ ] Add monitoring integration
- [ ] Set up ArgoCD for VyOS image management
- [ ] Add automated testing 