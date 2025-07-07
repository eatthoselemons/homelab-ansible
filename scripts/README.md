# Scripts Directory

This directory contains utility scripts for the homelab-ansible project.

## Directory Structure

```
scripts/
├── testing/           # Testing and validation scripts
│   ├── verify-vyos-image.sh         # Quick VyOS ISO verification
│   └── test-vyos-end-to-end.sh      # Complete VyOS test suite
└── README.md          # This file
```

## Testing Scripts

### verify-vyos-image.sh

Quick verification tool for VyOS ISO images.

**Usage:**
```bash
# Verify default image location
./scripts/testing/verify-vyos-image.sh

# Verify specific image
./scripts/testing/verify-vyos-image.sh /path/to/vyos.iso

# Verify from any directory
cd /tmp && /path/to/project/scripts/testing/verify-vyos-image.sh my-vyos.iso
```

**Features:**
- Checks file existence and size
- Validates ISO 9660 format
- Verifies bootable flag
- Detects mock vs real images
- No dependencies beyond standard Unix tools

### test-vyos-end-to-end.sh

Comprehensive test suite for the entire VyOS infrastructure.

**Usage:**
```bash
# Full test run (requires sudo password)
export ANSIBLE_BECOME_PASSWORD='your_sudo_password'
./scripts/testing/test-vyos-end-to-end.sh

# Skip image building (use existing)
./scripts/testing/test-vyos-end-to-end.sh --skip-build

# Only test image building
./scripts/testing/test-vyos-end-to-end.sh --skip-setup --skip-mock

# Force rebuild of existing image
./scripts/testing/test-vyos-end-to-end.sh --force-rebuild

# Show help
./scripts/testing/test-vyos-end-to-end.sh --help
```

**Options:**
- `--skip-build`: Skip VyOS image building (use existing image)
- `--skip-mock`: Skip mock molecule tests
- `--skip-setup`: Skip VyOS setup tests
- `--force-rebuild`: Force rebuild even if image exists
- `--help`: Show detailed help message

**Test Stages:**
1. Mock molecule tests (~3 minutes)
2. VyOS image building (~30 minutes, skippable)
3. Image verification
4. VyOS setup component tests (~10 minutes)
5. Full integration test (~5 minutes)

## Quick Start

### First Time Setup
```bash
# Install dependencies
pip install ansible molecule

# Set sudo password
export ANSIBLE_BECOME_PASSWORD='your_password'

# Run full test suite
./scripts/testing/test-vyos-end-to-end.sh
```

### Daily Development
```bash
# Quick image verification
./scripts/testing/verify-vyos-image.sh

# Run tests with existing image
./scripts/testing/test-vyos-end-to-end.sh --skip-build
```

### CI/CD Pipeline
```bash
# Fast mock tests only
cd collections/ansible_collections/homelab/nexus/extensions/
molecule test -s nexus.vyos.image_builder_mock
```

## Requirements

- **Operating System**: Linux or macOS
- **Tools**: Docker, Ansible, Molecule (for full tests)
- **Disk Space**: ~20GB free (for image building)
- **Memory**: 4GB+ recommended
- **Network**: Internet connection for downloading VyOS sources

## Troubleshooting

### Permission Denied
```bash
chmod +x scripts/testing/*.sh
```

### ANSIBLE_BECOME_PASSWORD not set
```bash
export ANSIBLE_BECOME_PASSWORD='your_sudo_password'
```

### Docker not running
```bash
sudo systemctl start docker  # Linux
open -a Docker              # macOS
```

### Out of disk space
The VyOS build process requires significant space:
- Build directory: ~15GB
- Final ISO: ~600MB
- Docker images: ~5GB

Clean up with:
```bash
docker system prune -a
rm -rf /tmp/vyos-build*
```