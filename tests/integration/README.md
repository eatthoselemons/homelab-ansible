# Integration Tests

This directory contains integration tests for validating the homelab infrastructure using testinfra.

## Overview

The tests validate:
- Network topology and VLAN configuration
- Router (VyOS) and switch (MikroTik) configurations
- Storage and filesystem setup
- Service availability (DNS, DHCP, NTP, etc.)
- Security policies and isolation
- Performance optimizations

## Test Structure

```
tests/integration/
├── conftest.py              # Pytest configuration and fixtures
├── pytest.ini               # Pytest settings and markers
├── test_config.yaml         # Centralized test configuration
├── test_helpers.py          # Helper functions and retry logic
├── test_vyos.py            # VyOS router tests
├── test_harvester.py       # Harvester cluster tests
├── test_switches.py        # MikroTik switch tests
├── test_storage.py         # Storage and filesystem tests
├── test_network_*.py       # Various network tests
└── README.md               # This file
```

## Prerequisites

1. Install test dependencies:
```bash
pip install pytest testinfra pytest-timeout pytest-rerunfailures
```

2. Set up inventory file with target hosts
3. Configure SSH access to test targets
4. Copy `.env.example` to `.env` for any secrets

## Running Tests

### Run all tests:
```bash
pytest tests/integration/ --inventory path/to/inventory
```

### Run specific test categories using markers:
```bash
# Critical tests only
pytest -m critical tests/integration/

# Network tests
pytest -m network tests/integration/

# Security tests
pytest -m security tests/integration/

# Skip slow tests
pytest -m "not slow" tests/integration/
```

### Run tests for specific infrastructure:
```bash
# VyOS router tests
pytest tests/integration/test_vyos.py

# Storage tests
pytest tests/integration/test_storage.py

# Network topology tests
pytest tests/integration/test_network_topology.py
```

### Using custom configuration:
```bash
pytest tests/integration/ --config my_config.yaml
```

## Test Configuration

The `test_config.yaml` file contains all test parameters including:
- Network definitions (VLANs, subnets, gateways)
- Device IPs (routers, switches, servers)
- Test parameters (timeouts, thresholds, security settings)
- DNS domains and service ports

To override configuration, create your own YAML file and use the `--config` option.

## Test Markers

Tests are categorized with pytest markers:
- `@pytest.mark.critical` - Must-pass infrastructure tests
- `@pytest.mark.network` - Network connectivity tests
- `@pytest.mark.security` - Security validation tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.storage` - Storage tests
- `@pytest.mark.services` - Service availability tests
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.flaky` - Tests that might fail intermittently

## Writing New Tests

1. Create test file following naming convention: `test_*.py`
2. Import required modules:
```python
import pytest
from test_helpers import retry, check_command_output
```

3. Use fixtures for configuration:
```python
def test_example(self, host, expected_networks, network_params):
    timeout = network_params['ping_timeout']
    # test implementation
```

4. Add appropriate markers:
```python
@pytest.mark.network
@pytest.mark.critical
def test_critical_network(self, host):
    pass
```

5. Use helper functions for common operations:
```python
from test_helpers import network_test, assert_service_running

def test_connectivity(self, host):
    assert network_test(host, "10.10.0.1", "ping")
```

## Troubleshooting

### Tests fail with "No inventory file"
Ensure you specify the inventory with `--inventory` flag or place it in standard locations.

### Network tests timeout
Adjust timeouts in `test_config.yaml` under `test_parameters.network`

### Permission errors
Ensure the test user has necessary sudo permissions on target hosts

### Flaky test failures
Use the retry decorator or pytest-rerunfailures:
```bash
pytest --reruns 3 --reruns-delay 2 tests/integration/
```

## CI/CD Integration

For CI/CD pipelines, use:
```bash
pytest tests/integration/ \
  --inventory inventory/ci.ini \
  --config test_config.ci.yaml \
  -m "critical and not destructive" \
  --junit-xml=test-results.xml \
  --timeout=300
```

## Best Practices

1. Always check command return codes before parsing output
2. Use fixtures for shared configuration
3. Mark critical tests appropriately
4. Add timeouts to network operations
5. Use descriptive assertion messages
6. Handle missing components with `pytest.skip()`
7. Warn for non-critical issues instead of failing
8. Document expected infrastructure state in tests