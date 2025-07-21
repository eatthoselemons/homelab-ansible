# Jumphost (Bastion Host) Security Best Practices

## Overview
A jumphost (also known as a bastion host or SSH gateway) is a hardened server that acts as a single entry point into a secure network. This document outlines security best practices for implementing and maintaining a jumphost in the homelab environment.

## Architecture Principles

### 1. Single Point of Entry
- The jumphost should be the **only** way to access the management VLAN (10.60.0.0/16)
- All SSH connections to production servers must go through the jumphost
- Direct SSH access to internal servers from external networks should be blocked

### 2. Network Isolation
- Place the jumphost at the boundary between secure and management networks
- Jumphost IP: 10.60.0.10 (as defined in architecture)
- Accessible only from the Secure VLAN (10.50.0.0/16)
- Can only forward connections to Management VLAN (10.60.0.0/16)

## SSH Configuration Hardening

### 1. Authentication
```bash
# /etc/ssh/sshd_config on jumphost

# Disable password authentication
PasswordAuthentication no
ChallengeResponseAuthentication no

# Only allow public key authentication
PubkeyAuthentication yes
AuthenticationMethods publickey

# Consider adding 2FA (Google Authenticator)
# AuthenticationMethods publickey,keyboard-interactive
```

### 2. Restrict SSH Functionality
```bash
# Disable unnecessary features
AllowAgentForwarding no
AllowStreamLocalForwarding no
X11Forwarding no
PermitTunnel no

# Only allow TCP forwarding for SSH jumps
AllowTcpForwarding yes

# Disable direct shell access (optional for strict jumphosts)
# ForceCommand /bin/echo 'This bastion does not support interactive commands.'
```

### 3. Access Control
```bash
# Limit users who can use the jumphost
AllowGroups jumphost-users

# Set specific listen address
ListenAddress 10.60.0.10

# Use non-standard SSH port
Port 2222

# Limit connection attempts
MaxAuthTries 3
MaxSessions 10
```

### 4. Cryptographic Hardening
```bash
# Strong key exchange algorithms
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512

# Strong ciphers
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr

# Strong MACs
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128-etm@openssh.com

# Host key algorithms
HostKeyAlgorithms ssh-ed25519
```

## Client Configuration

### 1. SSH Config for Users
```bash
# ~/.ssh/config

# Jumphost configuration
Host jumphost
    HostName 10.60.0.10
    User jumpadmin
    Port 2222
    IdentityFile ~/.ssh/id_jumphost
    ForwardAgent no
    
# Example production server
Host prod-server
    HostName 10.60.0.100
    User admin
    ProxyJump jumphost
    IdentityFile ~/.ssh/id_production
```

### 2. Using ProxyJump (Recommended)
```bash
# Direct command
ssh -J jumpadmin@10.60.0.10:2222 admin@10.60.0.100

# With config file
ssh prod-server
```

## Ansible Integration

### 1. Inventory Configuration
```yaml
# inventory.yaml
all:
  children:
    management:
      hosts:
        prod-server:
          ansible_host: 10.60.0.100
          ansible_ssh_common_args: '-o ProxyJump=jumpadmin@10.60.0.10:2222'
```

### 2. Ansible.cfg Settings
```ini
[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o ProxyJump=jumpadmin@10.60.0.10:2222
```

### 3. Dynamic Jump Host Configuration
```yaml
# group_vars/management.yaml
ansible_ssh_common_args: >-
  -o ProxyCommand="ssh -W %h:%p -q jumpadmin@{{ jumphost_ip }} -p {{ jumphost_port }}"
```

## Security Monitoring

### 1. Logging Configuration
```bash
# Enhanced logging in sshd_config
LogLevel VERBOSE
SyslogFacility AUTH

# Log all commands (if shell access is allowed)
# Add to /etc/profile or /etc/bash.bashrc
export PROMPT_COMMAND='RETRN_VAL=$?;logger -p local6.debug "$(whoami) [$$]: $(history 1 | sed "s/^[ ]*[0-9]\+[ ]*//" )"'
```

### 2. Fail2ban Configuration
```ini
# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
```

### 3. Audit Trail
- Enable auditd for comprehensive system auditing
- Monitor all SSH connections and forwarded sessions
- Regular review of access logs

## Implementation Checklist

### Initial Setup
- [ ] Install minimal OS - **Alpine Linux** (recommended for jumphost)
  - Extremely minimal footprint (~130MB)
  - Security-focused with PaX and grsecurity features
  - No unnecessary services or packages by default
  - Alternative options: Ubuntu Server 24.04 LTS (minimal), Debian 12 netinst
- [ ] Configure static IP (10.60.0.10)
- [ ] Update and harden OS
  ```bash
  # Alpine Linux setup
  apk update && apk upgrade
  apk add openssh fail2ban audit sudo
  ```
- [ ] Configure SSH server (OpenSSH already minimal in Alpine)
- [ ] Create dedicated jumphost user accounts
- [ ] Configure SSH keys for authorized users

### Security Hardening
- [ ] Apply SSH configuration hardening
- [ ] Configure firewall rules (Alpine uses iptables/nftables)
  ```bash
  # Alpine firewall setup
  apk add iptables iptables-openrc
  rc-update add iptables
  
  # Basic rules (save to /etc/iptables/rules-save)
  *filter
  :INPUT DROP [0:0]
  :FORWARD DROP [0:0]
  :OUTPUT ACCEPT [0:0]
  -A INPUT -i lo -j ACCEPT
  -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
  -A INPUT -p tcp -s 10.50.0.0/16 --dport 2222 -j ACCEPT
  -A INPUT -p icmp -j ACCEPT
  COMMIT
  ```
- [ ] Install and configure fail2ban
- [ ] Set up logging and monitoring (Alpine uses syslog-ng)
- [ ] Remove unnecessary packages (Alpine is already minimal)
- [ ] Disable unnecessary services

### Network Configuration
- [ ] Configure VyOS firewall rules to restrict access
- [ ] Ensure jumphost can only be accessed from Secure VLAN
- [ ] Verify jumphost can only access Management VLAN
- [ ] Test connection flow: Secure → Jumphost → Management

### Ansible Role Structure
```yaml
# roles/jumphost/tasks/main.yaml
- name: Configure jumphost
  include_tasks: "{{ item }}"
  loop:
    - install.yaml
    - ssh_hardening.yaml
    - firewall.yaml
    - monitoring.yaml
    - users.yaml
```

## Maintenance

### Regular Tasks
1. **Weekly**: Review SSH logs for anomalies
2. **Monthly**: Update SSH keys and remove unused accounts
3. **Quarterly**: Security patches and updates
4. **Annually**: Full security audit and penetration testing

### Emergency Procedures
1. **Compromise Detection**: Immediate isolation and forensic analysis
2. **Key Rotation**: Procedure for emergency key replacement
3. **Backup Access**: Alternative access method (console/IPMI) for emergencies

## Alternative Solutions

### Modern Alternatives to Consider
1. **Teleport**: Modern SSH/Kubernetes/Database access proxy with better auditing
2. **Boundary**: HashiCorp's identity-based access management
3. **Tailscale**: Zero-trust network that could eliminate need for jumphost
4. **Cloudflare Zero Trust**: Cloud-based access management

### When to Use Alternatives
- If you need more sophisticated access policies
- For multi-cloud environments
- When regulatory compliance requires advanced auditing
- For teams larger than 10 people

## References
- [NIST SP 800-46 Rev. 2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-46r2.pdf) - Guide to Enterprise Telework
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/) - Security configuration guidelines
- [Mozilla SSH Guidelines](https://infosec.mozilla.org/guidelines/openssh) - Modern SSH configuration