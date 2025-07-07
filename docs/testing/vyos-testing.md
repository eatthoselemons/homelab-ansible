# VyOS Testing Guide

This guide covers testing procedures for VyOS image building and setup.

## Quick Commands

### Verify Existing Image
```bash
./scripts/testing/verify-vyos-image.sh [path/to/image.iso]
```

### Run Mock Tests (CI/CD)
```bash
cd collections/ansible_collections/homelab/nexus/extensions/
molecule test -s nexus.vyos.image_builder_mock
```

### Build and Test Real Image
```bash
export ANSIBLE_BECOME_PASSWORD='your_sudo_password'
./collections/ansible_collections/homelab/nexus/roles/vyos_image_builder/test-real-build.sh
```

### Full End-to-End Test
```bash
export ANSIBLE_BECOME_PASSWORD='your_sudo_password'
./scripts/testing/test-vyos-end-to-end.sh

# With options
./scripts/testing/test-vyos-end-to-end.sh --skip-build  # Use existing image
./scripts/testing/test-vyos-end-to-end.sh --help        # Show all options
```

## Test Scripts Overview

All test scripts are located in the `scripts/testing/` directory.

### `scripts/testing/verify-vyos-image.sh`
- Quick verification of any VyOS ISO file
- Checks size, format, and bootability
- No build required, instant results

### `collections/.../roles/vyos_image_builder/test-real-build.sh`
- Tests the vyos_image_builder role with real image building
- Uses temporary directory for isolation
- Verifies image properties and idempotency
- Cleans up after testing

### `scripts/testing/test-vyos-end-to-end.sh`
- Comprehensive test suite for entire VyOS workflow
- Runs all molecule tests
- Builds VyOS image (if needed)
- Tests all VyOS setup components
- Provides detailed progress and results

## Testing Strategy

1. **Development**: Use mock tests for rapid iteration
2. **Pre-commit**: Run verify-vyos-image.sh on existing images
3. **CI/CD**: Use mock molecule tests
4. **Release**: Run full end-to-end test suite

## Requirements

- Docker installed and running
- Ansible and molecule installed
- ANSIBLE_BECOME_PASSWORD environment variable set
- ~20GB free disk space for real builds
- Internet connectivity for downloading VyOS sources

## Troubleshooting

### Docker-in-Docker Issues
The real image building tests must run on the host, not inside molecule containers, due to Docker-in-Docker limitations.

### Sudo Password
Always export ANSIBLE_BECOME_PASSWORD before running tests that require sudo:
```bash
export ANSIBLE_BECOME_PASSWORD='your_password'
```

### Disk Space
Real VyOS builds require significant disk space:
- Build directory: ~15GB
- Final ISO: ~600MB
- Docker images: ~5GB

### Build Time
- Mock tests: 2-3 minutes
- Real image build: 20-30 minutes
- Full test suite: 45-60 minutes