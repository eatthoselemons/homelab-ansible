# VyOS Implementation TODO

## Overview
This document outlines the remaining tasks needed to complete the VyOS router configuration for the homelab infrastructure as specified in architecture.md.

## High Priority Tasks

### 1. VPN Configuration (WireGuard)
- [ ] Implement WireGuard VPN server on VLAN 50 (Secure network)
- [ ] Configure VPN subnet (e.g., 10.100.0.0/24)
- [ ] Set up peer authentication and key management
- [ ] Configure firewall rules to allow VPN traffic
- [ ] Enable VPN clients to access appropriate VLANs based on authentication

### 2. Port Forwarding for DMZ Services
- [ ] Configure DNAT rules for external traffic to DMZ Traefik instance
- [ ] Forward ports 80/443 to Traefik reverse proxy in DMZ (10.10.x.x)
- [ ] Implement source NAT for DMZ services accessing internet
- [ ] Configure hairpin NAT for internal access to external services

### 3. Inter-VLAN Routing and Firewall Rules
- [ ] **Authentik SSO Cross-VLAN Access**
  - Research best approach: single instance with controlled access vs dual instances
  - If single instance: Configure specific firewall rules for DMZ services to access Authentik in Secure VLAN
  - If dual instances: Document database synchronization approach via Harvester volumes
- [ ] **Service-to-Service Communication**
  - Allow specific DMZ services to access internal APIs (with strict source/destination rules)
  - Configure rules for Secure VLAN services to access TrueNAS shares
- [ ] **Logging Network Rules (VLAN 70)**
  - Allow all VLANs to send metrics/logs to VLAN 70
  - Block VLAN 70 from initiating connections to other VLANs
  - Block VLAN 70 from internet access

### 4. Management VLAN Jumphost Configuration
- [ ] Research and document jumphost best practices
- [ ] Create `jumphost-best-practices.md` in `docs/llms/best-practices/`
- [ ] Configure jumphost VM at 10.60.0.10
- [ ] Implement SSH proxy/bastion host configuration
- [ ] Configure firewall rules:
  - Only allow SSH to management VLAN from jumphost
  - Allow jumphost access from Secure VLAN only
  - Configure audit logging for jumphost access

## Medium Priority Tasks

### 5. Control-D DNS Integration
- [ ] Replace generic DNS forwarding with Control-D configuration
- [ ] Configure Control-D endpoints for each VLAN
- [ ] Implement DNS policies per VLAN (blocking, filtering)
- [ ] Set up DNS-over-HTTPS (DoH) or DNS-over-TLS (DoT)

### 6. Wake-on-LAN Configuration
- [ ] Configure WoL packet forwarding from Management VLAN
- [ ] Create firewall rules to allow magic packets
- [ ] Set up scheduled automation for Fast Server power management
- [ ] Document WoL MAC addresses and procedures

## Low Priority Tasks

### 7. Zone-Based Firewall Consideration
**Note**: After review, zone-based firewall may not be necessary given the distinct nature of each VLAN. Current per-VLAN firewall approach is sufficient. However, zones could be useful for:
- Grouping similar VLANs (e.g., "untrusted" zone for IoT + Guest WiFi)
- Simplifying rule management if VLANs share common policies
- Future scalability if more VLANs are added

Decision: Stick with per-VLAN rules for now, document zone approach for future consideration.

## Implementation Notes

### Traefik Reverse Proxy Strategy
- **DMZ Traefik Instance**: Handles all external-facing services, SSL termination for public domains
- **Secure Traefik Instance**: Handles internal services, SSL termination for private domains
- Both instances will manage their own certificates via Let's Encrypt/cert-manager
- No cross-VLAN certificate sharing needed

### Security Considerations
- Default deny policy is correct - all VLANs block by default
- Each allow rule should be specific (source IP/port, destination IP/port)
- Log all inter-VLAN traffic for security monitoring
- Regular firewall rule audits

### Testing Requirements
- [ ] Create molecule tests for each major configuration
- [ ] Test inter-VLAN routing with specific service scenarios
- [ ] Verify security isolation between VLANs
- [ ] Test failover and recovery scenarios

## Next Steps
1. Start with VPN configuration as it enables secure remote management
2. Implement jumphost for secure internal access
3. Configure port forwarding for essential external services
4. Refine inter-VLAN routing based on actual service requirements