# VyOS Setup Role

This role sets up a VyOS router VM with comprehensive network configuration, security hardening, and VLAN support for the homelab environment.

## Features

- **Automated VyOS VM Deployment**: Uses stafwag.delegated_vm_install for proper VM provisioning
- **Cloud-Init Configuration**: Initial setup via cloud-init for zero-touch deployment
- **Security Hardening**: Firewall rules, SSH hardening, fail2ban integration
- **VLAN Support**: Complete 7-VLAN network segmentation
- **Idempotent Configuration**: Safe to run multiple times

## Requirements

- LibVirt/KVM hypervisor
- VyOS ISO image (built using vyos_image_builder role or downloaded)
- Ansible collections:
  - community.libvirt
  - vyos.vyos
  - stafwag.delegated_vm_install

## Role Variables

```yaml
# VM Configuration
vyos_vm:
  name: vyos-router
  memory: 4096              # MB of RAM
  vcpus: 2                  # Number of CPUs
  disk_size: 20G            # Disk size
  disk_path: /var/lib/libvirt/images/vyos-router.qcow2

# Build Configuration
vyos_build_image: false     # Build ISO using vyos_image_builder
vyos_iso_path: "{{ playbook_dir }}/../images/vyos/vyos-current.iso"
vyos_cloud_init_iso: /var/lib/libvirt/images/vyos-cloud-init.iso

# Network Configuration
vyos_vm_ip: "192.168.122.50"
vyos_ssh_port: 2222
vyos_web_port: 443
vyos_network_mode: bridge   # bridge or nat
vyos_enable_vlans: true
vyos_configure_router: true
vyos_security_hardening: true

# Security Configuration
vyos_admin_user: admin
vyos_admin_password: "{{ vault_vyos_admin_password }}"
vyos_admin_ssh_key: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"

# VLAN Configuration (see defaults/main.yaml for full VLAN definitions)
vyos_vlan_networks:
  - name: "dmz"
    vlan_id: 10
    subnet: "10.10.0.0/24"
    # ... additional settings
```

## Dependencies

- homelab.nexus.vyos_image_builder (optional, if vyos_build_image is true)

## Example Playbook

```yaml
- hosts: nexus_nodes
  become: yes
  roles:
    - role: homelab.nexus.vyos_setup
      vars:
        vyos_admin_password: "{{ vault_vyos_admin_password }}"
        vyos_network_mode: bridge
        vyos_enable_vlans: true
        vyos_security_hardening: true
```

## Security Features

1. **Firewall Configuration**
   - Default deny policies on input/forward chains
   - Stateful connection tracking
   - Rate limiting on SSH access
   - Zone-based firewall for VLAN isolation

2. **SSH Hardening**
   - Non-standard port (2222)
   - Key-based authentication only
   - Strong cipher selection
   - Rate limiting via firewall

3. **User Management**
   - Default 'vyos' user removed
   - Custom admin user with SSH key
   - Password authentication disabled

4. **Fail2ban Integration**
   - Automatic blocking of brute force attempts
   - Configurable ban times and thresholds

## Network Architecture

```
Internet → Modem → Nexus:Port1(WAN) → VyOS VM → Nexus:Port2(LAN) → Switch → Servers
                                          ↓
                                    VLAN Networks:
                                    - DMZ (10)
                                    - Untrusted WiFi (20)
                                    - Trusted WiFi (30)
                                    - IoT (40)
                                    - Secure (50)
                                    - Management (60)
                                    - Logging (70)
```

## Troubleshooting

### VM Won't Start
- Check KVM/libvirt is installed and running: `systemctl status libvirtd`
- Verify VyOS ISO exists at configured path
- Check disk space: `df -h /var/lib/libvirt`
- Review libvirt logs: `journalctl -u libvirtd`

### Cloud-Init Not Working
- Verify cloud-init ISO was created: `ls -la /var/lib/libvirt/images/vyos-cloud-init.iso`
- Check cloud-init templates render correctly
- VyOS uses custom cloud-init implementation - keep configs simple

### Network Connectivity Issues
- Verify networks are active: `virsh net-list`
- Check VM interfaces: `virsh domiflist vyos-router`
- Review firewall rules aren't blocking traffic
- Ensure physical interfaces are configured correctly

### SSH Access Denied
- Confirm SSH key is correct in cloud-init
- Wait for full boot (60+ seconds)
- Try default port first: `ssh -p 2222 admin@192.168.122.50`
- Check firewall allows SSH from your network

### Build Failures
- Docker needs ~20GB disk space for builds
- Ensure internet connectivity for package downloads
- Build process can take 30-60 minutes
- Check Docker service is running

## Testing

Run molecule tests:
```bash
cd collections/ansible_collections/homelab/nexus/extensions
molecule test -s nexus.vyos.setup
molecule test -s nexus.vyos.security_hardening
molecule test -s nexus.vyos.full_integration
```

## License

MIT

## Author Information

Created for the homelab-ansible project