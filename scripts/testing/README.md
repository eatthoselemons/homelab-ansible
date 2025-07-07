# Testing Scripts

This directory contains scripts for testing VyOS infrastructure.

## Available Scripts

### verify-vyos-image.sh
Quick verification of VyOS ISO images. Run with `--help` for usage.

```bash
./verify-vyos-image.sh                    # Verify default image
./verify-vyos-image.sh /path/to/image.iso # Verify specific image
```

### test-vyos-end-to-end.sh
Complete end-to-end test suite for VyOS. Run with `--help` for all options.

```bash
# Prerequisites
export ANSIBLE_BECOME_PASSWORD='your_password'

# Common usage
./test-vyos-end-to-end.sh               # Full test run
./test-vyos-end-to-end.sh --skip-build  # Skip image building
./test-vyos-end-to-end.sh --help        # Show all options
```

## Requirements

- Docker
- Ansible & Molecule
- sudo access (via ANSIBLE_BECOME_PASSWORD)
- ~20GB disk space for full tests

See [VyOS Testing Guide](../../docs/testing/vyos-testing.md) for detailed documentation.