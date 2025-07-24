# VyOS Image Builder Role

This role builds VyOS ISO images using the official Docker-based build process.

## Description

The `vyos_image_builder` role automates the process of building custom VyOS router images using the official VyOS build Docker container. It supports both production builds and test mode for CI/CD pipelines.

## Requirements

- Docker installed on the build host
- Sufficient disk space (~20GB) and RAM (4GB minimum)
- Internet connectivity to pull Docker images and VyOS source
- Git installed

## Role Variables

```yaml
# Build configuration
vyos_version: "current"                # VyOS version (1.4) or branch name (sagitta)
vyos_architecture: amd64               # Architecture (amd64 or arm64)
vyos_build_by: 'homelab-ansible'       # Build attribution
vyos_build_type: release               # Build type (release/development)

# Paths
vyos_build_dir: /tmp/vyos-build        # Temporary build directory
vyos_images_dir: "{{ playbook_dir }}/../images/vyos"  # Where to store built ISOs
vyos_build_cleanup: true               # Clean up build directory after completion

# Docker
vyos_docker_image: "vyos/vyos-build:{{ vyos_version }}"  # Docker image to use
```

## Dependencies

None

## Example Playbook

### Basic Usage

```yaml
- hosts: localhost
  become: yes
  roles:
    - homelab.nexus.vyos_image_builder
```

### Custom Build Configuration

```yaml
- hosts: localhost
  become: yes
  vars:
    vyos_version: "current"           # Build VyOS 1.4 LTS
    vyos_build_by: "MyOrganization"
    vyos_images_dir: "/opt/vyos-images"
  roles:
    - homelab.nexus.vyos_image_builder
```

### CI/CD Build

```yaml
- hosts: localhost
  become: yes
  vars:
    vyos_images_dir: "/tmp/test-images"
  roles:
    - homelab.nexus.vyos_image_builder
```

## Usage

### Using the Wrapper Playbook

From the project root directory:

```bash
# Build VyOS 1.4 (default)
ansible-playbook build-vyos-image.yaml

# Build specific version
ansible-playbook build-vyos-image.yaml -e vyos_version=current

# Custom builder identification
ansible-playbook build-vyos-image.yaml -e vyos_build_by="John Doe"

# Keep build directory for debugging
ansible-playbook build-vyos-image.yaml -e vyos_build_cleanup=false

# Custom output directory
ansible-playbook build-vyos-image.yaml -e vyos_images_dir=/custom/path
```

### Testing

The role includes comprehensive tests:

#### Build Test
```bash
export ANSIBLE_BECOME_PASSWORD='your_sudo_password'
./collections/ansible_collections/homelab/nexus/roles/vyos_image_builder/test-real-build.sh
```
- Builds a real VyOS ISO (~600MB) in a test directory
- Takes ~30-45 minutes
- Verifies ISO format, size, and idempotency
- Cleans up after testing

#### End-to-End Test Suite
For comprehensive testing of the entire VyOS workflow:
```bash
export ANSIBLE_BECOME_PASSWORD='your_sudo_password'
./test-vyos-end-to-end.sh
```
- Runs all VyOS-related tests in sequence
- Builds real VyOS image (if not exists)
- Tests all VyOS setup components
- Runs full integration tests
- Takes ~45-60 minutes for complete run

## Notes

- Building a VyOS image takes approximately 20-30 minutes
- The build process requires a stable internet connection
- Built images are placed in the `images/vyos/` directory by default
- The `images/` directory is gitignored to prevent large ISO files from being committed
- VyOS version mapping:
  - `current`: Latest development version (recommended for open source builds)
  - `sagitta` or `1.4`: VyOS 1.4 LTS (requires proprietary repository access)
  - `equuleus` or `1.3`: VyOS 1.3 LTS (requires proprietary repository access)

## Output

The role creates:
- `vyos-{version}.iso`: The built VyOS image
- `vyos-latest.iso`: Symlink to the most recent build

## License

Apache 2

## Author Information

Created for the homelab-ansible project