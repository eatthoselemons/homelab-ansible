"""
DEPRECATED: This file has been split into more focused test modules.

Please use the following specialized test files instead:
- test_switches.py: MikroTik switch configuration tests
- test_network_topology.py: Overall network topology and VLAN tests
- test_network_performance.py: Performance, MTU, and bonding tests
- test_network_security.py: Security and isolation tests
- test_network_services.py: DHCP, DNS, NTP, and other services
- test_vyos.py: VyOS router-specific tests (already exists)

This file is kept for backward compatibility but should not be used for new tests.
"""

import pytest


class TestNetworkingDeprecated:
    """Deprecated test class - use specialized test files instead."""
    
    def test_deprecated(self, host):
        """This test file is deprecated."""
        pytest.skip("This test file is deprecated. Use the specialized network test files instead.")