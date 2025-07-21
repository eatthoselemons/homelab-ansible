# Notes on stafwag.delegated_vm_install Issues and Fixes

## Issue 1: Namespace Error in add_disk.yaml

### Problem
The role uses `builtin.set_fact` instead of `ansible.builtin.set_fact` in `/home/user/.ansible/roles/stafwag.delegated_vm_install/tasks/add_disk.yaml`. This causes an error in newer Ansible versions:

```
ERROR! couldn't resolve module/action 'builtin.set_fact'. This often indicates a misspelling, missing collection, or incorrect module path.
```

### Fix Applied
Changed lines 17, 26, and 38 in `add_disk.yaml`:
- From: `builtin.set_fact`
- To: `ansible.builtin.set_fact`

Also fixed `builtin.debug` to `ansible.builtin.debug` in the same file.

### Root Cause
This appears to be a bug in the stafwag.delegated_vm_install v2.0.3 role where the ansible namespace prefix was omitted.

## Issue 2: remote_src Support for boot_disk

### Problem
When running VyOS tests in Docker containers with libvirt, the VyOS ISO is mounted inside the container at `/opt/vyos/vyos-current.iso`. However, the delegated_vm_install role tries to copy the ISO from the Ansible controller's filesystem, resulting in:

```
Could not find or access '/opt/vyos/vyos-current.iso' on the Ansible Controller.
If you are using a module and expect the file to exist on the remote, see the remote_src option
```

### Investigation
1. The role uses stafwag.qemu_img internally, which DOES support `remote_src` parameter
2. However, delegated_vm_install doesn't pass through `remote_src` from the boot_disk configuration
3. In `tasks/delegate_vms.yaml`, the role creates the _qemu_img array but only includes specific fields:
   - dest, format, src, size, owner, group, mode
   - It does NOT include remote_src even if provided

### Attempted Fix
Added `remote_src: true` to the boot_disk configuration in vyos_setup role:
```yaml
boot_disk:
  src: "{{ vyos_iso.stat.path }}"
  remote_src: true
```

But this parameter is not passed through to the qemu_img role by delegated_vm_install.

### Potential Solutions
1. **Patch delegated_vm_install**: Modify the role to pass through additional boot_disk parameters to qemu_img
2. **Use wrapper roles directly**: Instead of delegated_vm_install, use stafwag.qemu_img and stafwag.virt_install_import directly
3. **Pre-copy the image**: Copy the ISO to where the controller expects it before running delegated_vm_install

### Underlying Architecture
The delegated_vm_install role is a wrapper around:
- stafwag.qemu_img - for disk image management
- stafwag.cloud_localds - for cloud-init ISO creation
- stafwag.virt_install_import - for VM creation with libvirt

Since qemu_img supports remote_src, the fix would be to modify delegated_vm_install to pass this parameter through.

### Fix Applied for remote_src
Modified `/home/user/.ansible/roles/stafwag.delegated_vm_install/tasks/delegate_vms.yaml` to include remote_src in the _qemu_img array creation (around line 206):

```yaml
- name: Create _qemu_img array
  ansible.builtin.set_fact:
    _qemu_img:
      - dest:
          "{{ _vm.path }}/{{ _hostname }}.qcow2"
        format:
          qcow2
        src:
          "{{ _vm.boot_disk.src }}"
        size:
          "{{ _vm.boot_disk.size | default('100G') }}"
        owner:
          "{{ _security.file.owner }}"
        group:
          "{{ _security.file.group }}"
        mode:
          "{{ _security.file.mode }}"
        remote_src:
          "{{ _vm.boot_disk.remote_src | default(false) }}"  # Added this line
```

This allows the boot_disk configuration to pass the remote_src parameter through to the qemu_img role, enabling the use of images that already exist on the remote host (inside containers).

### Result
**The fix worked!** After applying this change, the delegated_vm_install role now correctly passes the `remote_src` parameter to the underlying qemu_img role. This enables the VyOS tests to run in Docker containers with the VyOS ISO mounted inside the container, rather than requiring the ISO to exist on the Ansible controller.

### Usage Example
In the vyos_setup role, we can now use:
```yaml
delegated_vm_install:
  vm:
    boot_disk:
      src: "{{ vyos_iso.stat.path }}"
      remote_src: true  # This now works!
    disks:
      - name: "vyos-cloud-init.iso"
        dest: "{{ vyos_cloud_init_iso }}"
        remote_src: true  # This also works for additional disks
```