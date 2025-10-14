# Network Standards and Domain Conventions

## Domain Structure

All services follow a strict subdomain hierarchy based on network segmentation:

### Primary Domains
- **public.awynn.in** - Internet-facing services
- **private.awynn.in** - Internal services (LAN only)
- **management.awynn.in** - Infrastructure management interfaces
- **logs.awynn.in** - Logging and monitoring stack

### Service URL Format
```
<service>.<network-segment>.awynn.in
```

### Examples by Network Segment

#### Management Network (`management.awynn.in`)
- `harvester.management.awynn.in` - Harvester cluster UI
- `truenas.management.awynn.in` - TrueNAS management interface
- `vyos.management.awynn.in` - VyOS router management
- `ipmi.management.awynn.in` - IPMI/BMC interfaces
- `switch.management.awynn.in` - Network switch management

#### Private Network (`private.awynn.in`)
- `gitlab.private.awynn.in` - GitLab instance
- `rancher.private.awynn.in` - Rancher UI
- `argocd.private.awynn.in` - ArgoCD interface
- `infisical.private.awynn.in` - Secrets management
- `docker-registry.private.awynn.in` - Container registry

#### Public Network (`public.awynn.in`)
- `www.public.awynn.in` - Public website
- `api.public.awynn.in` - Public API endpoints
- `mail.public.awynn.in` - Mail server

#### Logging Network (`logs.awynn.in`)
- `grafana.logs.awynn.in` - Metrics visualization
- `prometheus.logs.awynn.in` - Metrics collection
- `loki.logs.awynn.in` - Log aggregation
- `elastic.logs.awynn.in` - Elasticsearch
- `kibana.logs.awynn.in` - Log visualization
- `alertmanager.logs.awynn.in` - Alert management

## IP Address Ranges

### Network Segmentation
```yaml
networks:
  management:
    vlan: 10
    subnet: 10.10.0.0/16
    gateway: 10.10.0.1
    description: "Infrastructure management"
    
  private:
    vlan: 20
    subnet: 10.20.0.0/16
    gateway: 10.20.0.1
    description: "Internal services"
    
  public:
    vlan: 30
    subnet: 10.30.0.0/16
    gateway: 10.30.0.1
    description: "DMZ for public services"
    
  storage:
    vlan: 40
    subnet: 10.40.0.0/16
    gateway: 10.40.0.1
    description: "Storage network (NFS/iSCSI)"
    
  backup:
    vlan: 50
    subnet: 10.50.0.0/16
    gateway: 10.50.0.1
    description: "Backup network"
    
  guest_wifi:
    vlan: 60
    subnet: 10.60.0.0/16
    gateway: 10.60.0.1
    description: "Guest WiFi (isolated)"
    
  trusted_wifi:
    vlan: 70
    subnet: 10.70.0.0/16
    gateway: 10.70.0.1
    description: "Trusted WiFi"
    
  iot:
    vlan: 80
    subnet: 10.80.0.0/16
    gateway: 10.80.0.1
    description: "IoT devices (isolated)"
    
  logs:
    vlan: 90
    subnet: 10.90.0.0/16
    gateway: 10.90.0.1
    description: "Logging and monitoring stack"
```

### Reserved IP Ranges (per VLAN)
```yaml
reserved_ranges:
  routers: x.x.0.1-x.x.0.10           # Gateways and VIPs
  infrastructure: x.x.0.11-x.x.0.50   # Physical infrastructure
  services: x.x.0.51-x.x.0.100        # Service VMs
  dynamic: x.x.1.1-x.x.10.254         # DHCP pool (large range)
  kubernetes: x.x.100.0-x.x.199.255   # K8s nodes and services (25,600 IPs)
  containers: x.x.200.0-x.x.250.255   # Container networks (13,056 IPs)
```

Example for VLAN 20 (Private):
- 10.20.0.1-10.20.0.10: Routers/VIPs
- 10.20.0.11-10.20.0.50: Physical servers
- 10.20.0.51-10.20.0.100: Service VMs
- 10.20.1.1-10.20.10.254: DHCP
- 10.20.100.0-10.20.199.255: Kubernetes
- 10.20.200.0-10.20.250.255: Containers

## DNS Configuration

### Internal DNS Zones
```yaml
internal_zones:
  - management.awynn.in
  - private.awynn.in
  - logs.awynn.in
  
external_zones:
  - public.awynn.in  # Public DNS provider
```

### Split-Horizon DNS
- Internal clients resolve all `*.awynn.in` to internal IPs
- External clients only resolve `public.awynn.in` domains
- Management interfaces are never exposed externally

## Certificate Management

### Wildcard Certificates
```yaml
certificates:
  - "*.management.awynn.in"  # Internal CA
  - "*.private.awynn.in"      # Internal CA
  - "*.logs.awynn.in"         # Internal CA
  - "*.public.awynn.in"       # Let's Encrypt
```

## Naming Conventions

### Hostnames
```
<role>-<environment>-<index>
```

Examples:
- `harvester-prod-01`
- `gitlab-runner-ci-02`
- `vyos-edge-01`

### VM Names
```
<service>-<purpose>-<index>
```

Examples:
- `gitlab-app-01`
- `prometheus-metrics-01`
- `nginx-proxy-02`

## Service Discovery

### Consul Service Names
```
<service>.<datacenter>.consul
```

Examples:
- `gitlab.homelab.consul`
- `postgresql.homelab.consul`

### Kubernetes Services
```
<service>.<namespace>.svc.cluster.local
```

Examples:
- `gitlab.gitlab.svc.cluster.local`
- `prometheus.monitoring.svc.cluster.local`

## Examples in Configuration

### Ansible Inventory
```yaml
harvester_cluster:
  hosts:
    harvester-01:
      ansible_host: 10.10.0.11
      public_url: harvester.management.awynn.in
    harvester-02:
      ansible_host: 10.10.0.12
    harvester-03:
      ansible_host: 10.10.0.13
```

### Service Configuration
```yaml
gitlab:
  external_url: https://gitlab.private.awynn.in
  registry_url: https://docker-registry.private.awynn.in
  
monitoring:
  grafana_url: https://grafana.logs.awynn.in
  prometheus_url: https://prometheus.logs.awynn.in
```

## Important Notes

1. **Never use `.local` or `.homelab` domains** - Always use `awynn.in` subdomains
2. **Management interfaces are sacred** - Never expose to public internet
3. **Use network segmentation** - Don't mix service types in VLANs
4. **Document all deviations** - If you must break convention, document why

## Quick Reference

| Service Type | Domain | VLAN | Subnet | Usable IPs |
|-------------|--------|------|--------|------------|
| Infrastructure Mgmt | `*.management.awynn.in` | 10 | 10.10.0.0/16 | 65,534 |
| Internal Services | `*.private.awynn.in` | 20 | 10.20.0.0/16 | 65,534 |
| Public Services | `*.public.awynn.in` | 30 | 10.30.0.0/16 | 65,534 |
| Storage Traffic | N/A | 40 | 10.40.0.0/16 | 65,534 |
| Backup Traffic | N/A | 50 | 10.50.0.0/16 | 65,534 |
| Guest WiFi | N/A | 60 | 10.60.0.0/16 | 65,534 |
| Trusted WiFi | N/A | 70 | 10.70.0.0/16 | 65,534 |
| IoT Devices | N/A | 80 | 10.80.0.0/16 | 65,534 |
| Monitoring/Logging | `*.logs.awynn.in` | 90 | 10.90.0.0/16 | 65,534 |

## Cross-Reference

This network standard is referenced in:
- `/docs/llms/design/architecture.md`
- `/docs/llms/design/testing-strategy.md`
- All Ansible inventory files
- All service configuration templates