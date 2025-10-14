"""
Pytest configuration for integration tests.
Provides fixtures and configuration for testinfra.
"""

import pytest
import os
import yaml
from pathlib import Path


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--inventory",
        action="store",
        help="Path to Ansible inventory file"
    )
    parser.addoption(
        "--section",
        action="store",
        help="Test section to run"
    )
    parser.addoption(
        "--config",
        action="store",
        default="test_config.yaml",
        help="Path to test configuration file"
    )


@pytest.fixture(scope="session")
def inventory_file(request):
    """Get inventory file path from command line."""
    inventory = request.config.getoption("--inventory")
    if not inventory:
        # Try to find inventory in standard locations
        possible_paths = [
            "tests/inventory/test.ini",
            "inventory/test.ini",
            "test-inventory.ini"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                inventory = path
                break
    
    if not inventory or not os.path.exists(inventory):
        pytest.skip("No inventory file specified or found")
    
    return inventory


@pytest.fixture(scope="session")
def test_section(request):
    """Get test section from command line."""
    return request.config.getoption("--section")


@pytest.fixture(scope="session")
def test_config(request):
    """Load test configuration from centralized config file."""
    config_path = request.config.getoption("--config")
    if not config_path:
        config_path = "test_config.yaml"
    
    # Try to find config file
    possible_paths = [
        Path(config_path),
        Path(__file__).parent / config_path,
        Path("tests/integration") / config_path,
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f)
    
    # Return empty config if nothing found
    pytest.warn(f"No test configuration file found at {config_path}")
    return {}


@pytest.fixture
def expected_vlans(test_config):
    """VLANs that should be configured."""
    if test_config and 'networks' in test_config:
        return [net['vlan'] for net in test_config['networks'].values()]
    # Fallback to hardcoded values
    return [10, 20, 30, 40, 50, 60, 70, 80, 90]


@pytest.fixture
def expected_networks(test_config):
    """Network configuration expectations."""
    if test_config and 'networks' in test_config:
        return test_config['networks']
    # Fallback to hardcoded values
    return {
        "management": {
            "vlan": 10,
            "subnet": "10.10.0.0/16",
            "gateway": "10.10.0.1"
        },
        "private": {
            "vlan": 20,
            "subnet": "10.20.0.0/16",
            "gateway": "10.20.0.1"
        },
        "public": {
            "vlan": 30,
            "subnet": "10.30.0.0/16",
            "gateway": "10.30.0.1"
        },
        "storage": {
            "vlan": 40,
            "subnet": "10.40.0.0/16",
            "gateway": "10.40.0.1"
        },
        "backup": {
            "vlan": 50,
            "subnet": "10.50.0.0/16",
            "gateway": "10.50.0.1"
        },
        "logs": {
            "vlan": 90,
            "subnet": "10.90.0.0/16",
            "gateway": "10.90.0.1"
        }
    }


@pytest.fixture
def network_params(test_config):
    """Network test parameters."""
    if test_config and 'test_parameters' in test_config:
        return test_config['test_parameters'].get('network', {})
    return {
        'ping_timeout': 2,
        'ping_count': 2,
        'curl_timeout': 5,
        'max_latency_local': 5.0,
        'max_latency_internet': 100.0
    }


@pytest.fixture
def security_params(test_config):
    """Security test parameters."""
    if test_config and 'test_parameters' in test_config:
        return test_config['test_parameters'].get('security', {})
    return {
        'max_ssh_auth_tries': 3,
        'required_tls_version': '1.2',
        'forbidden_ports': [
            {'port': 23, 'service': 'telnet'},
            {'port': 21, 'service': 'ftp'},
            {'port': 139, 'service': 'netbios'},
            {'port': 445, 'service': 'smb'},
            {'port': 111, 'service': 'rpcbind'}
        ]
    }


@pytest.fixture
def device_ips(test_config):
    """Infrastructure device IPs."""
    if test_config and 'devices' in test_config:
        return test_config['devices']
    return {
        'vyos_router': {'primary_ip': '10.10.0.1'},
        'switches': {
            'main': {'ip': '10.10.0.2'},
            'basement': {'ip': '10.10.0.3'},
            'rack': {'ip': '10.10.0.4'}
        }
    }


# Configure testinfra to use ansible inventory
def pytest_collection_modifyitems(config, items):
    """Modify test collection to use ansible inventory."""
    inventory = config.getoption("--inventory")
    if inventory:
        # Set testinfra to use ansible inventory
        os.environ['TESTINFRA_HOST'] = f"ansible://all?ansible_inventory={inventory}"