# Harvester HCI Setup Best Practices

This document outlines best practices for setting up Harvester HCI in your homelab environment, with special consideration for running TrueNAS as a VM and using Terraform for infrastructure automation.

## Table of Contents
- [Hardware Requirements](#hardware-requirements)
- [Cluster Configuration](#cluster-configuration)
- [Network Configuration](#network-configuration)
- [Storage Best Practices](#storage-best-practices)
- [TrueNAS VM Configuration](#truenas-vm-configuration)
- [GPU Passthrough](#gpu-passthrough)
- [Terraform Automation](#terraform-automation)
- [Security Considerations](#security-considerations)

## Hardware Requirements

### Production Environment
- **CPU**: 16-core minimum (server-class processors recommended)
- **RAM**: 64 GB minimum
- **Storage**: 500 GB+ SSD/NVMe with 5,000+ random IOPS per disk
- **Network**: 10 Gbps interface recommended
- **Hardware**: YES-certified hardware for SUSE Linux Enterprise Server (SLES) 15 SP3/SP4 preferred

### Testing/Development Environment
- **CPU**: 8-core minimum
- **RAM**: 32 GB minimum
- **Storage**: 200-250 GB SSD/NVMe
- **Network**: 1 Gbps interface minimum

### Important Notes
- Laptops and nested virtualization are NOT officially supported
- Management nodes (first three nodes) must have fast storage for etcd performance
- Harvester runs on commodity x86_64 or ARM64 servers

## Cluster Configuration

### High Availability Setup
1. **Minimum 3 nodes** for production HA cluster
   - First node becomes the initial management node
   - Next two nodes automatically promoted to management nodes
   - Forms HA control plane with etcd cluster

2. **Node Requirements**
   - Consistent hardware across management nodes
   - Reliable network connectivity between nodes
   - Shared storage considerations for VM migration

### Time Synchronization
- **Critical Requirement**: Configure reliable NTP server
- Required for etcd cluster stability
- Prevents issues with:
  - Leader election
  - Log replication
  - Cluster consistency

## Network Configuration

### NIC Configuration Best Practices
1. **Multiple NICs Recommended**
   - One NIC for node/management access
   - One or more NICs for VM networking
   - Separate NICs for storage network (optional but recommended)

2. **Bonded NICs for HA**
   - Use at least 2 NICs for bonded management network
   - Each custom cluster network requires 2+ NICs for bonding
   - Improves reliability and performance

### VLAN Integration
Based on your existing VyOS configuration:
- **Management VLAN (60)**: Use for Harvester node management
- **Secure VLAN (50)**: Use for VM-to-VM communication
- **DMZ VLAN (10)**: For external-facing services
- **Logging VLAN (70)**: For monitoring without internet access

### Storage Network
For high-performance workloads:
- Create dedicated storage network
- Removes I/O contention between workload and storage traffic
- Critical for latency-sensitive operations

## Storage Best Practices

### Longhorn Integration
- Harvester includes Longhorn as default CSI driver
- Each PV can have 3+ replicas for redundancy
- Data automatically rebuilt when replicas are rescheduled

### Pre-Shutdown Procedures
1. **Always backup before cluster shutdown**
2. **Stop PVs when possible** to avoid unnecessary data movement
3. **Document VM states** before maintenance

### Performance Optimization
- Use enterprise-grade SSDs/NVMe for production
- Consider separate storage tiers for different workloads
- Monitor IOPS and latency metrics

## TrueNAS VM Configuration

### Critical Requirements for TrueNAS
1. **PCI Passthrough for Storage**
   - **REQUIRED**: Pass through physical disks directly to TrueNAS
   - ZFS does not perform well with virtualized I/O
   - Use PCI passthrough for HBA or individual drives

2. **VM Specifications**
   - **CPU**: Start with 2 vCPUs, scale based on workload
   - **RAM**: Minimum 16 GB (ZFS benefits from more RAM)
   - **Boot**: Legacy BIOS mode works well (UEFI optional)

3. **Disk Configuration**
   ```yaml
   disks:
     - bootOrder: 1
       disk:
         bus: virtio
       name: disk-2
       serial: dae05b93-c3c4-4a3e-9ec0-5403f9e70494  # Add serial for TrueNAS
   ```

### Network Configuration for TrueNAS
- Use VirtIO network drivers for best performance
- Consider dedicated network for storage traffic
- Configure on Management or Secure VLAN based on use case

## GPU Passthrough

### Setup Process
1. **Enable PCI Devices Controller**
   - Navigate to Advanced → Addons
   - Enable and deploy `pcidevices-controller`

2. **Configure GPU Passthrough**
   - Go to PCI Devices
   - Enable passthrough for GPU and all devices in same IOMMU group
   - All devices with same Domain:Bus:Device must be passed together

3. **VM Configuration**
   - Schedule VM on specific node (no live migration)
   - Assign GPU to VM after enabling passthrough
   - Configure node scheduling for GPU-enabled node

### IOMMU Considerations
- Check IOMMU groups before configuration
- Pass through entire IOMMU group together
- Harvester uses format: `nodename-address` for device naming

## Terraform Automation

### Provider Configuration
```hcl
terraform {
  required_providers {
    harvester = {
      source  = "harvester/harvester"
      version = "0.6.3"  # Use latest version
    }
  }
}

provider "harvester" {
  kubeconfig = file("~/.kube/harvester-config")
}
```

### Resource Management Structure
```
harvester-terraform/
├── providers.tf      # Provider configuration
├── variables.tf      # Variable definitions
├── images.tf        # OS image definitions
├── networks.tf      # Network configurations
├── vms.tf          # VM definitions
└── storage.tf      # Storage configurations
```

### Example VM Definition
```hcl
resource "harvester_virtualmachine" "truenas" {
  name      = "truenas"
  namespace = "default"
  
  cpu    = 4
  memory = "32Gi"
  
  network_interface {
    name         = "default"
    network_name = "management-network"
  }
  
  disk {
    name        = "rootdisk"
    size        = "100Gi"
    boot_order  = 1
  }
}
```

### Best Practices for Terraform
1. **State Management**
   - Use remote state backend
   - Enable state locking
   - Regular state backups

2. **Resource Organization**
   - Separate resources by type
   - Use modules for reusable components
   - Implement proper variable management

3. **Integration with Existing Infrastructure**
   - Reference existing VyOS VLANs
   - Coordinate with ArgoCD for GitOps
   - Maintain consistency with Ansible roles

## Security Considerations

### Access Control
1. **RBAC Configuration**
   - Implement least-privilege access
   - Separate admin and operator roles
   - Regular access audits

2. **Network Security**
   - Leverage existing VLAN segmentation
   - Implement firewall rules at VM level
   - Use private networks for sensitive workloads

### Backup and Recovery
1. **Regular Backups**
   - VM snapshots before major changes
   - Longhorn volume snapshots
   - Off-cluster backup storage

2. **Disaster Recovery**
   - Document recovery procedures
   - Test restore processes regularly
   - Maintain configuration backups

## Integration with Existing Infrastructure

### VyOS Integration
- Harvester nodes on Management VLAN (60)
- VMs distributed across appropriate VLANs
- Firewall rules updated for Harvester traffic

### iPXE Boot Integration
- Use existing iPXE server for Harvester node provisioning
- Create Harvester-specific boot configurations
- Automate node deployment via network boot

### ArgoCD Integration
- Deploy Harvester CSI configurations via GitOps
- Manage Kubernetes workloads on Harvester
- Coordinate with existing CI/CD pipelines

## Monitoring and Maintenance

### Monitoring Setup
- Deploy Prometheus/Grafana on Harvester
- Monitor node health and resource usage
- Alert on storage and performance issues

### Regular Maintenance
1. **Updates**
   - Plan maintenance windows
   - Test updates in non-production first
   - Follow official upgrade procedures

2. **Performance Tuning**
   - Regular performance assessments
   - Adjust resource allocations as needed
   - Monitor and optimize storage performance

## Troubleshooting Tips

1. **Search Context**
   - Search for "XYZ error in Kubevirt" rather than "XYZ error in Harvester"
   - Harvester is built on Kubevirt, so Kubevirt documentation often helps

2. **Support Resources**
   - Generate support bundles before making changes
   - Consult SUSE support for production issues
   - Active community on GitHub and forums

## Summary

These best practices ensure a robust Harvester HCI deployment that:
- Integrates seamlessly with your existing VyOS network infrastructure
- Supports TrueNAS VM with proper storage passthrough
- Enables GPU passthrough for specialized workloads
- Leverages Terraform for infrastructure automation
- Maintains security and performance standards

Remember to test thoroughly in your environment before production deployment, especially the interaction between Harvester, TrueNAS, and your existing network segmentation.