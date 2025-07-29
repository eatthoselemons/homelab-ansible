# Ansible Role: harvester_image_builder

Build and cache Harvester base images for fast testing and deployment.

## Description

This role creates base QCOW2 images from Harvester ISO files, which can then be used as templates for rapid deployment. Similar to the VyOS image builder pattern, it:

- Downloads Harvester ISO (if not present)
- Creates base VM images for different node types
- Caches images to speed up subsequent deployments
- Tracks ISO checksums to detect when rebuilds are needed

## Requirements

- libvirt/KVM installed and configured
- qemu-img and genisoimage tools
- Sufficient disk space for images (200GB+ per node type)
- Internet connection for ISO download

## Role Variables

```yaml
# Harvester version
harvester_version: "v1.3.2"

# Images directory
harvester_images_dir: "{{ playbook_dir }}/../images/harvester"

# Base image configurations
harvester_base_images:
  - name: "harvester-epyc-base"
    memory: 16384
    vcpus: 8
    disk_size: "200G"
  - name: "harvester-mid-base"
    memory: 8192
    vcpus: 4
    disk_size: "150G"
  - name: "harvester-thin-base"
    memory: 4096
    vcpus: 2
    disk_size: "100G"

# Force rebuild even if images exist
harvester_force_rebuild: false
```

## Dependencies

None.

## Example Playbook

```yaml
---
- name: Build Harvester base images
  hosts: localhost
  gather_facts: yes
  become: no

  tasks:
    - name: Build Harvester images
      include_role:
        name: homelab.epyc.harvester_image_builder
```

## How It Works

1. **First Run**: Downloads ISO, creates base images (~30 minutes)
2. **Subsequent Runs**: Skips if images exist and ISO hasn't changed (~10 seconds)
3. **Updates**: Automatically rebuilds if new ISO version detected

## Output

Creates the following in `images/harvester/`:
- `harvester-v1.3.2.iso` - Downloaded ISO
- `harvester-epyc-base.qcow2` - EPYC server base image
- `harvester-mid-base.qcow2` - Mid server base image  
- `harvester-thin-base.qcow2` - Thin client base image
- `checksums/` - Checksums for change detection

## Integration with harvester_setup

The harvester_setup role can use these base images to:
- Create linked clones for fast deployment
- Skip installation phase
- Test cluster formation with real VMs

## License

Apache 2

## Author Information

Created for the homelab.epyc collection.