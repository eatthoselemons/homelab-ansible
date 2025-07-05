# Homelab Infrastructure Automation Project

## Mission Statement
Create a comprehensive Ansible automation system for a sophisticated homelab environment featuring VM orchestration (Harvester), container management (Rancher), network virtualization (VyOS), and automated provisioning (iPXE/ArgoCD).

## Architecture Components

### Physical Infrastructure
- **Nexus Node**: Lenovo thin client + Intel NIC (LibVirt host for VyOS router + services VM)
- **EPYC Server**: AMD EPYC 7532, 256GB RAM, mixed storage, AMD GPU
- **Fast Server**: AMD 5950X, 128GB RAM (on-demand via WoL)
- **Mid Server**: AMD 5700G, 64GB RAM
- **Additional**: 2x HP thin clients, Raspberry Pi
- **Networking**: 24-port MikroTik switches, Eaton 5PX1500 UPS
- **Storage Architecture**: ZFS RAIDZ2 (5x6TB + 1 hot spare), separate 4TB volume, NVMe caching

### Network Topology
```
Internet -> Modem -> Nexus:Port1(WAN) -> VyOS VM
                 -> Nexus:Port2(LAN) -> MikroTik -> Basement Switch -> Rack Switch -> Servers
```

### VLAN Design
- **VLAN 1**: Unused
- **VLAN 10**: DMZ (external-facing services, no internal access)
- **VLAN 20**: Untrusted WiFi (guest access, isolated)
- **VLAN 30**: Trusted WiFi (personal devices, limited secure access)
- **VLAN 40**: IoT (isolated, no inter-network access)
- **VLAN 50**: Secure (main network, VPN endpoint)
- **VLAN 60**: Management (server administration, jump-host access only)
- **VLAN 70**: Log Aggregation (no internet access, service-to-monitoring only)

### Service Architecture

#### Core Infrastructure Services (Nexus VM)
- **Control-D**: DNS resolution
- **iPXE Server**: Network boot images for all nodes
- **DHCP**: Network configuration
- **ArgoCD**: GitOps deployment orchestration

#### Harvester Cluster Nodes
- EPYC Server (primary, resource-intensive workloads)
- Mid Server (auxiliary services)
- Thin Client (management/lightweight services)

#### Container Services (Harvester-managed)
- **External-facing** (DMZ): Traefik, Lychee, Immich, Authentik, OmniTools
- **Internal-only** (Secure): PrivateBin, HomeBox, Grocy, VictoriaMetrics
- **Cross-network**: Authentik (SSO for both DMZ and Secure)

### Technical Requirements

#### Security & Secrets Management
- **Cloud Bootstrap**: Infisical cloud service for initial secrets
- **Local Secrets**: Self-hosted Infisical instance post-bootstrap
- **TPM Integration**: Each server stores decryption key in TPM
- **Starbucks Method**: Encrypted files per server, TPM-decrypted for cloud access

#### Storage Strategy
- **TrueNAS VM**: GPU passthrough for ZFS management
- **Codex Volume**: RAIDZ2 with 2-drive redundancy + hot spare
- **Ephemeral Volume**: Single 4TB for non-critical data
- **Container Storage**: Harvester CSI + selective NFS mounts
- **Backup**: Selective Backblaze B2 integration via Restic

#### Automation & Deployment
- **Network Boot**: All nodes default to iPXE, MAC-based image selection
- **GitOps**: ArgoCD monitors Git repositories for configuration changes
- **Data Preservation**: UUID-based disk identification prevents data loss during redeployment
- **IAC**: Using a variety of services, ansible, pulumi, argocd 

## Implementation Challenges Requiring API Documentation

1. **Harvester Integration**: VM lifecycle management, node placement policies, CSI storage configuration
2. **VyOS Configuration**: VLAN routing, firewall rules, VPN setup, port forwarding
3. **ArgoCD Setup**: Multi-environment management, secret integration, selective deployment from monorepo
4. **Rancher Integration**: GPU node management, container-to-VM placement strategies
5. **TrueNAS API**: Automated share creation, backup job configuration, user management
6. **Infisical Integration**: Ansible vault integration, secret rotation, access policies

## Specific Technical Questions Needing Resolution

1. **GPU Container Strategy**: Best practices for AMD GPU sharing in Kubernetes via Harvester
2. **Cross-VLAN Service Communication**: Secure routing for services accessing TrueNAS from different VLANs
3. **Certificate Management**: Wildcard cert distribution across VLANs via cert-manager
4. **WoL Implementation**: Automated power management for Fast Server via management VLAN
5. **Repository Structure**: Optimal Git organization for selective ArgoCD deployments

## Success Criteria
- Complete infrastructure provisioning via single Ansible playbook execution
- Automated service deployment via GitOps
- Secure secret management without manual intervention
- Resilient storage with automated backup
- Network segmentation with appropriate inter-VLAN access controls
