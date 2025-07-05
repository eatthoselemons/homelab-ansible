# Security Best Practices for LLM Infrastructure Automation

## Network Security

### Core Principles
- **Network Segmentation**: Use VLANs to isolate traffic (DMZ=10, WiFi=20/30, IoT=40, Secure=50, Management=60, Logging=70)
- **Zero Trust**: Never trust network location - authenticate and authorize all connections
- **Least Privilege**: Grant minimum network access required for function
- **Defense in Depth**: Layer multiple security controls (firewalls, IDS, monitoring)

### Implementation
- Use private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Implement inter-VLAN routing controls with explicit allow rules
- Use SSH key authentication only - disable password auth
- Change default ports for services (SSH on 2222, not 22)
- Enable network logging and monitoring
- Use WPA3 for wireless networks with strong passphrases

### DNS and Naming
- Use structured domain hierarchy: `service.vlan.private.domain.tld`
- Separate public (`service.public.domain.tld`) from private services
- Implement DNS filtering to block malicious domains
- Use local DNS resolution for internal services (controlD)

### DNS Security with controlD Home
- **DNS Filtering**: Block ads, malicious websites, and potentially harmful content
- **Network-level Protection**: Use DNS filtering for network-wide security
- **Secure DNS Servers**: Use reliable external DNS servers (9.9.9.9, 1.1.1.1)
- **Interface Binding**: Bind DNS services to specific interfaces for security
- **Query Logging**: Regularly review DNS query logs for suspicious activity
- **Multiple Instances**: Consider running redundant DNS filtering instances

## Firewall Security

### UFW/iptables Best Practices
- **Default Deny**: Block all traffic by default, explicitly allow required connections
- **Stateful Inspection**: Track connection state, only allow established/related return traffic
- **Rate Limiting**: Prevent brute force attacks with connection throttling
- **Geo-blocking**: Block traffic from high-risk countries for public services

### Rule Structure
```bash
# Default policies
ufw default deny incoming
ufw default allow outgoing
ufw default deny forward

# Explicit service allows
ufw allow from 192.168.50.0/24 to any port 22
ufw limit ssh  # Rate limit SSH connections
```

### VyOS Firewall Best Practices
- **Default Deny Policy**: Set default actions to "drop" for Input and Forward chains
- **Stateful Filtering**: Allow only established/related return traffic through firewall
- **Zone-based Configuration**: Use zone-based firewall with explicit inter-zone rules
- **Interface Scoping**: Scope firewall rules to specific network interfaces
- **Commit Verification**: Use `commit-confirm` when making firewall changes
- **Flow Tables**: Use flow tables for faster packet processing on high-traffic rules
- **Silent Drop**: Use "drop" instead of "reject" to deny packets silently
- **Trusted Interface Rules**: Explicitly allow traffic from trusted interfaces only

#### VyOS Firewall Chain Configuration
```vyos
# Input Chain - Router destined traffic
set firewall ipv4 input filter default-action drop
set firewall ipv4 input filter rule 100 action accept
set firewall ipv4 input filter rule 100 state established
set firewall ipv4 input filter rule 100 state related

# Forward Chain - Transit traffic
set firewall ipv4 forward filter default-action drop
set firewall ipv4 forward filter rule 100 action accept
set firewall ipv4 forward filter rule 100 state established
set firewall ipv4 forward filter rule 100 state related

# Output Chain - Router originated traffic (trusted)
set firewall ipv4 output filter default-action accept
```

#### VyOS Initial Setup Security
- **User Management**: Create unique admin account, delete default "vyos" user
- **Strong Authentication**: Use complex passwords, avoid common usernames ('root', 'admin', 'superuser')
- **NTP Security**: Disable NTP server capabilities for home use, use geographically close NTP servers
- **SSH Hardening**: Limit SSH access to specific interfaces and IP addresses, use non-standard ports
- **Hostname**: Set unique, identifiable hostname for the router
- **Hardware Security**: Use dedicated hardware for routing, avoid VM-based routing for stability

## Linux Security Hardening

### System Hardening
- **Updates**: Enable automatic security updates (`unattended-upgrades`)
- **Users**: Disable root login, use sudo for privileged access
- **Services**: Disable unnecessary services, use systemd hardening
- **File Permissions**: Use proper ownership (644 for files, 755 for dirs, 600 for secrets)

### Access Control
- **SSH**: Key-based auth only, disable root login, use non-standard ports
- **Sudo**: Use specific commands instead of ALL, implement timeout
- **File Systems**: Mount with `noexec`, `nosuid`, `nodev` where appropriate
- **AppArmor/SELinux**: Enable mandatory access controls

### Monitoring and Auditing
- **auditd**: Monitor file access, user actions, privilege escalation
- **fail2ban**: Automatically block brute force attempts
- **System Logs**: Centralize logging, monitor for anomalies
- **File Integrity**: Use AIDE or similar for change detection

### Secrets Management
- **Never hardcode**: Use external secret stores (Infisical, Vault)
- **Environment Variables**: For runtime secrets, not committed secrets
- **File Permissions**: 600 for secret files, proper ownership
- **Rotation**: Regular rotation of passwords, keys, certificates

### Container Security (when applicable)
- **Non-root**: Run containers as non-privileged users
- **Read-only**: Mount filesystems read-only when possible
- **Capabilities**: Drop unnecessary Linux capabilities (only grant net-raw when required)
- **Network**: Use custom networks, avoid host networking unless necessary
- **Volume Permissions**: Set appropriate permissions for container volumes (avoid 777)
- **Default Credentials**: Change default credentials immediately for all services

### Network Monitoring and DHCP Security
- **Deep Packet Inspection**: Use tools like ntopng for application-level traffic monitoring
- **DHCP IP Management**: Reserve IP ranges for dynamic assignment, leave room for static IPs
- **Network Segmentation**: Use VLANs to separate wired vs wireless clients
- **NAT Security**: Implement Source NAT (SNAT) to mask internal IP addresses
- **Traffic Monitoring**: Monitor network interfaces for security insights
- **Interface Security**: Use dummy interfaces for service binding and management access

## Common Ansible Security Patterns

### Safe Secret Handling
```yaml
# Good: Dynamic secret retrieval
- name: Retrieve SSH key from vault
  uri:
    url: "{{ infisical_api_url }}/api/v3/secrets/{{ item }}"
    headers:
      Authorization: "Bearer {{ infisical_token }}"
  register: secret_result
  no_log: true

# Bad: Hardcoded secrets
ssh_private_key: "-----BEGIN PRIVATE KEY-----"
```

### Privilege Escalation
```yaml
# Use specific sudo commands
become_user: root
become_method: sudo

# Avoid shell module for security-sensitive tasks
command: systemctl restart firewall
# Not: shell: systemctl restart firewall
```

### Error Handling
```yaml
failed_when: 
  - result.rc != 0
  - "'already exists' not in result.stderr"
ignore_errors: false  # Default - fail on errors
```

## Red Flags to Avoid

- Storing secrets in version control
- Using default passwords or keys
- Running services as root unnecessarily
- Opening firewall rules to 0.0.0.0/0
- Disabling security features for "convenience"
- Using unencrypted protocols (HTTP, Telnet, FTP)
- Ignoring security updates
- Using weak authentication methods
- Excessive sudo/root privileges
- Logging sensitive data in plaintext
- Using common usernames ('root', 'admin', 'superuser', 'vyos')
- Enabling NTP server capabilities unnecessarily
- Running routers as VMs in production
- Using overly permissive container volume permissions (777)
- Not monitoring DNS queries for suspicious activity
- Failing to segment network traffic with VLANs