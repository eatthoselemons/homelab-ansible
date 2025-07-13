# VyOS Testing Guide

This guide explains how to run VyOS tests in the homelab-ansible project.

## Overview

The VyOS testing infrastructure supports multiple test levels:
- **Unit Tests**: Mock-based tests that don't require real infrastructure
- **Integration Tests**: Tests that verify configuration and basic functionality
- **Full Tests**: Complete end-to-end tests requiring KVM/libvirt and real VyOS images

## Prerequisites

### Required for All Tests
- Ansible virtual environment at `/home/user/ansible-venv`
- Docker installed and running
- Basic Python packages (installed automatically in test containers)

### Required for Full Tests
- KVM/QEMU support (`/dev/kvm` available)
- libvirt installed and running
- Real VyOS ISO image (not mock)
- Sudo or root access for VM operations

## Quick Start

### 1. Build a VyOS Image (if needed)
```bash
# Check if image exists
./scripts/build-vyos.sh --check

# Build default image (sagitta release)
./scripts/build-vyos.sh

# Build specific version
./scripts/build-vyos.sh --version current --type development --arch amd64
```

### Verify Existing Image
```bash
./scripts/testing/verify-vyos-image.sh [path/to/image.iso]
```

### 2. Run Tests

#### Simple Test Execution
```bash
# Run a single test
./test.sh test nexus.vyos.setup

# Run syntax check only
./test.sh syntax nexus.vyos.vlans

# List available tests
./test.sh list

# Run tests matching a pattern
./test.sh --pattern vyos

# Run with debug output
./test.sh --debug test nexus.vyos.setup
```

#### Smart Test Runner
```bash
# Auto-detect environment and run appropriate tests
./scripts/testing/run-all-vyos-tests.sh

# Run only unit tests (safe in containers)
./scripts/testing/run-all-vyos-tests.sh --mode unit

# Force full test execution
./scripts/testing/run-all-vyos-tests.sh --force-full

# Dry run to see what would execute
./scripts/testing/run-all-vyos-tests.sh --dry-run
```

## Test Scenarios

### Unit Tests
- `nexus.vyos.image_builder_mock` - Tests image building with mock ISO

### Integration Tests
- `nexus.vyos.setup` - Tests VyOS VM setup and configuration
- `nexus.vyos.vlans` - Tests VLAN configuration
- `nexus.vyos.security_hardening` - Tests security configurations

### Full Tests
- `nexus.vyos.image_builder` - Builds real VyOS ISO (20-30 minutes)
- `nexus.vyos.full_integration` - Complete end-to-end testing

## Environment Variables

Create a `.env` file in the project root for secrets:
```bash
cp .env.example .env
# Edit .env with your values
```

Key variables:
- `INFISICAL_TOKEN` - For secret management
- `VYOS_USER` / `VYOS_PASSWORD` - Test credentials
- `VYOS_IMAGE_PATH` - Override image location

## Test Modes

### Container Testing
When running in Docker containers:
- Only unit tests run by default
- Mock implementations are used for VM/network operations
- No KVM access required

### Bare Metal Testing
When running on physical/virtual machines:
- All tests can run
- Real VMs are created with libvirt
- Actual network bridges are configured

### Test Mode Detection
The test runner automatically detects:
- Container vs bare metal environment
- KVM availability
- Privilege level
- VyOS image type (real vs mock)

## Troubleshooting

### Common Issues

#### "VyOS image not found"
- Run `./scripts/build-vyos.sh` to build an image
- Or copy an existing image to `images/vyos/vyos-current.iso`

#### "Failed to connect to libvirt"
- Ensure libvirtd is running: `sudo systemctl start libvirtd`
- Check permissions: `sudo usermod -aG libvirt $USER`

#### Tests skip everything
- Check if `vyos_test_mode` is set to false
- Use the enhanced test runner for proper mode detection
- Review mock implementations in `tasks/test_mocks/`

### Debug Options

```bash
# Run with molecule debug
./test.sh --debug test nexus.vyos.setup

# Check environment detection
./scripts/testing/run-all-vyos-tests.sh --dry-run

# Verify image
./scripts/testing/verify-vyos-image.sh /path/to/image.iso
```

## Advanced Usage

### Running Specific Test Patterns
```bash
# Run all VyOS tests matching pattern
./test.sh --pattern vyos

# Run syntax check with debug output
./test.sh --debug syntax nexus.vyos.setup

# Run specific test patterns
./test.sh --pattern setup     # All setup-related tests
./test.sh --pattern security  # All security-related tests
```

### Custom Test Scenarios
1. Create new molecule scenario in `extensions/molecule/`
2. Use existing scenarios as templates
3. Set `vyos_test_mode: true` for container-safe testing
4. Use mock tasks for operations that require privileges

## Test Best Practices

1. **Always run full tests** when verifying functionality
2. **Use mocks appropriately** for container environments
3. **Check test output** for skipped tasks - they may indicate issues
4. **Keep tests idempotent** - they should pass when run multiple times
5. **Document requirements** for tests that need special setup

## Contributing

When adding new VyOS tests:
1. Determine appropriate test level (unit/integration/full)
2. Add to the correct test arrays in `run-all-vyos-tests.sh`
3. Ensure mock implementations exist for test mode
4. Update this documentation with any new requirements