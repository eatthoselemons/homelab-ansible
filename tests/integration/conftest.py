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
def test_config():
    """Load test configuration."""
    config_file = Path("test-integration-config.yaml")
    if config_file.exists():
        with open(config_file) as f:
            return yaml.safe_load(f)
    return {}


@pytest.fixture
def expected_vlans():
    """VLANs that should be configured."""
    return [10, 20, 30, 40, 50, 60, 70, 80, 90]


@pytest.fixture
def expected_networks():
    """Network configuration expectations."""
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


# Configure testinfra to use ansible inventory
def pytest_collection_modifyitems(config, items):
    """Modify test collection to use ansible inventory."""
    inventory = config.getoption("--inventory")
    if inventory:
        # Set testinfra to use ansible inventory
        os.environ['TESTINFRA_HOST'] = f"ansible://all?ansible_inventory={inventory}"