# VyOS Images Directory

This directory stores VyOS ISO images built using the `vyos_image_builder` role.

## File Structure

- `vyos-current.iso` - Built VyOS image for current version
- `vyos-latest.iso` - Symlink to the most recent build
- Other version-specific ISOs as built

## Building Images

To build a VyOS image, run the vyos_image_builder role:

```yaml
- hosts: build_host
  roles:
    - homelab.nexus.vyos_image_builder
```

## Notes

- All .iso, .qcow2, and other image files are ignored by git
- Images should be built locally due to size constraints
- Default build requires ~20GB disk space and 4GB RAM
- Build process can take 30-60 minutes depending on system resources