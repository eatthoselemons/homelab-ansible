# VyOS Image Builder Role

This role builds VyOS images using the official Docker-based build process.

## Requirements

- Docker installed on the build host
- Sufficient disk space (~20GB) and RAM (4GB minimum)
- Internet connectivity to pull Docker images and VyOS source

## Role Variables

```yaml
vyos_build_dir: /tmp/vyos-build          # Temporary build directory
vyos_images_dir: "{{ playbook_dir }}/../images/vyos"  # Where to store built ISOs
vyos_version: current                    # VyOS version to build
vyos_architecture: amd64                 # Architecture (amd64 or arm64)
vyos_build_by: 'homelab-ansible'        # Build attribution
vyos_build_type: release                 # Build type (release/development)
vyos_docker_image: "vyos/vyos-build:{{ vyos_version }}"  # Docker image to use
vyos_build_cleanup: true                 # Clean up build directory after completion
```

## Dependencies

None

## Example Playbook

```yaml
- hosts: build_host
  roles:
    - homelab.nexus.vyos_image_builder
```

## License

MIT

## Author Information

Created for the homelab-ansible project