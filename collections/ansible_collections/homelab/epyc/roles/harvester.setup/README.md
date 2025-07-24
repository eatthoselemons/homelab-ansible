# Harvester Setup Role

Deploy and configure a 3-node Harvester HCI cluster with PCIe passthrough support across EPYC server, mid server, and HP thin client.

## Description

This role automates the deployment of a production-ready Harvester HCI (Hyper-Converged Infrastructure) cluster with:
- 3-node HA configuration (all management nodes)
- PCIe passthrough for GPU and storage HBA
- Storage network configuration on VLAN 65
- Terraform provider access configured
- Ready for VM and container deployments

## Prerequisites

Before running this role, ensure:
1. VyOS VLAN 65 is configured (10.60.65.0/24)
2. NTP server is running on Nexus VM
3. Run `harvester-infrastructure-prerequisites.md` first
4. IOMMU is enabled in BIOS/UEFI for passthrough nodes
5. Minimum 32GB RAM per node
6. Nodes are accessible via SSH

## Requirements

### Collections
- `infisical.vault` >= 0.6.0
- `kubernetes.core` >= 2.4.0
- `ansible.posix` >= 1.5.0
- `community.general` >= 6.0.0

### Environment Variables
```bash
export INFISICAL_CLIENT_ID="your-client-id"
export INFISICAL_CLIENT_SECRET="your-client-secret"
export INFISICAL_PROJECT_ID="your-project-id"
```

### Infisical Secrets
The following secrets must be configured in Infisical:
- `harvesterClusterToken`: Cluster join token
- `harvesterAdminPassword`: Admin user password
- `harvesterAnsibleSSHKey`: SSH public key for Ansible access

## Role Variables

### Required Variables
```yaml
# Node configuration (usually from inventory)
harvester_nodes:
  - name: "epyc-harvester"
    ip: "10.60.1.11"
    is_first: true
    interfaces:
      - name: "eth0"
        hwaddr: "aa:bb:cc:dd:ee:01"
    pcie_devices: ["10de:1fb9", "10de:10fa"]  # GPU device IDs
  - name: "mid-harvester"
    ip: "10.60.1.12"
    interfaces:
      - name: "eth0"
        hwaddr: "aa:bb:cc:dd:ee:02"
  - name: "thin-harvester"
    ip: "10.60.1.13"
    interfaces:
      - name: "eth0"
        hwaddr: "aa:bb:cc:dd:ee:03"
```

### Optional Variables
```yaml
# Cluster configuration
harvester_cluster_vip: "10.60.1.10"
harvester_cluster_name: "harvester-cluster"

# Storage network
harvester_storage_network:
  enabled: true
  vlan: 65
  cidr: "10.60.65.0/24"
  ip_range_start: "10.60.65.10"
  ip_range_end: "10.60.65.250"

# Feature flags
harvester_configure_networks: true
harvester_enable_pcie_passthrough: true
harvester_configure_storage_network: true
harvester_setup_terraform: true

# Test mode (skips actual deployment)
harvester_test_mode: false
```

## Dependencies

None

## Example Playbook

```yaml
---
- name: Deploy Harvester cluster
  hosts: localhost
  gather_facts: yes
  
  vars:
    harvester_nodes:
      - name: "epyc-harvester"
        ip: "10.60.1.11"
        is_first: true
        interfaces:
          - name: "enp1s0"
            hwaddr: "{{ hostvars['epyc-harvester']['mac_address'] }}"
        pcie_devices: ["10de:1fb9", "10de:10fa"]
      - name: "mid-harvester"
        ip: "10.60.1.12"
        interfaces:
          - name: "enp1s0"
            hwaddr: "{{ hostvars['mid-harvester']['mac_address'] }}"
      - name: "thin-harvester"
        ip: "10.60.1.13"
        interfaces:
          - name: "enp1s0"
            hwaddr: "{{ hostvars['thin-harvester']['mac_address'] }}"
  
  tasks:
    - name: Deploy Harvester cluster
      include_role:
        name: homelab.epyc.harvester_setup
```

## Deployment Process

The role executes the following steps:

1. **Validate Prerequisites**: Checks VLAN, NTP, hardware requirements
2. **Configure Networks**: Sets up network configurations on nodes
3. **Prepare Nodes**: Configures IOMMU, GRUB, and kernel modules
4. **Initialize Cluster**: Deploys first node and creates cluster
5. **Join Nodes**: Adds remaining nodes to cluster
6. **Configure Storage**: Sets up storage network for Longhorn
7. **Enable PCIe Passthrough**: Configures GPU/HBA passthrough
8. **Setup Terraform**: Configures Terraform provider access

## Testing

Run molecule tests:
```bash
cd /home/user/IdeaProjects/homelab-ansible
./test.sh test epyc.harvester_setup
```

## Verification

After deployment, verify:

1. **Cluster Status**:
   ```bash
   kubectl --kubeconfig=/tmp/harvester-kubeconfig get nodes
   ```

2. **PCIe Devices**:
   ```bash
   kubectl --kubeconfig=/tmp/harvester-kubeconfig get pcidevices
   ```

3. **Storage Network**:
   ```bash
   kubectl --kubeconfig=/tmp/harvester-kubeconfig get clusternetworks
   ```

4. **Terraform Access**:
   ```bash
   cd /tmp/harvester-terraform-test
   terraform plan
   ```

## Troubleshooting

### Common Issues

1. **IOMMU Not Enabled**
   - Enable Intel VT-d or AMD-Vi in BIOS/UEFI
   - Verify with: `dmesg | grep -i iommu`

2. **Node Join Failures**
   - Check network connectivity between nodes
   - Verify cluster token is correct
   - Check firewall rules allow port 6443

3. **PCIe Passthrough Issues**
   - Ensure all devices in IOMMU group are passed
   - Check device IDs with: `lspci -nn`
   - Verify VFIO modules are loaded

4. **Storage Network Problems**
   - Verify VLAN 65 is configured on switches
   - Check MTU settings match across nodes
   - Ensure IP range has enough addresses

### Logs

- Harvester logs: `kubectl --kubeconfig=/tmp/harvester-kubeconfig logs -n harvester-system`
- Node logs: `journalctl -u harvester -f` on each node

## License

GPL-3.0

## Author

homelab