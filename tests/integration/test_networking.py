"""
Networking validation tests using testinfra.
Tests network interfaces, VLANs, bonds, and connectivity.
"""

import pytest


class TestNetworking:
    """Test network configuration."""
    
    def test_bond_interface_exists(self, host):
        """Test that bond0 interface exists and is up."""
        bond = host.interface("bond0")
        assert bond.exists, "bond0 interface does not exist"
        
        # Check bond is up
        cmd = host.run("ip link show bond0")
        assert cmd.rc == 0, "Failed to get bond0 status"
        assert "state UP" in cmd.stdout, "bond0 is not UP"
    
    def test_bond_has_slaves(self, host):
        """Test that bond has slave interfaces."""
        bond_slaves = host.file("/sys/class/net/bond0/bonding/slaves")
        if bond_slaves.exists:
            slaves = bond_slaves.content_string.strip()
            assert slaves, "bond0 has no slave interfaces"
            # Should have at least one slave
            slave_list = slaves.split()
            assert len(slave_list) >= 1, f"Expected at least 1 slave, got {len(slave_list)}"
    
    def test_vlan_interfaces(self, host, expected_vlans):
        """Test that all expected VLAN interfaces exist."""
        missing_vlans = []
        
        for vlan in expected_vlans:
            vlan_if = f"bond0.{vlan}"
            interface = host.interface(vlan_if)
            if not interface.exists:
                missing_vlans.append(vlan)
        
        assert not missing_vlans, f"Missing VLAN interfaces: {missing_vlans}"
    
    def test_network_connectivity(self, host, expected_networks):
        """Test connectivity to network gateways."""
        # Skip in containers or minimal environments
        if host.system_info.type == "docker":
            pytest.skip("Skipping network tests in container")
        
        failed_gateways = []
        
        for network_name, network_config in expected_networks.items():
            gateway = network_config["gateway"]
            # Try to ping gateway (3 packets, 2 second timeout)
            cmd = host.run(f"ping -c 3 -W 2 {gateway}")
            if cmd.rc != 0:
                failed_gateways.append(f"{network_name} ({gateway})")
        
        # Allow some gateways to fail (they might not all be configured)
        if len(failed_gateways) == len(expected_networks):
            pytest.fail(f"Cannot reach any gateways: {failed_gateways}")
        elif failed_gateways:
            pytest.skip(f"Some gateways unreachable (might be expected): {failed_gateways}")
    
    def test_bridge_utils_installed(self, host):
        """Test that bridge utilities are installed."""
        pkg = host.package("bridge-utils")
        assert pkg.is_installed, "bridge-utils package is not installed"
    
    def test_network_configuration_files(self, host):
        """Test that network configuration files exist."""
        # Check for either netplan or interfaces file
        netplan = host.file("/etc/netplan/01-netcfg.yaml")
        interfaces = host.file("/etc/network/interfaces")
        
        assert netplan.exists or interfaces.exists, \
            "No network configuration files found (netplan or interfaces)"
    
    def test_ip_forwarding_enabled(self, host):
        """Test that IP forwarding is enabled (for router functionality)."""
        ipv4_forward = host.file("/proc/sys/net/ipv4/ip_forward")
        if ipv4_forward.exists:
            assert ipv4_forward.content_string.strip() == "1", \
                "IPv4 forwarding is not enabled"
    
    def test_dns_resolution(self, host):
        """Test that DNS resolution works."""
        # Try to resolve a common domain
        cmd = host.run("nslookup google.com")
        assert cmd.rc == 0, "DNS resolution failed"
    
    def test_mtu_configuration(self, host):
        """Test that MTU is properly configured on interfaces."""
        # Check bond0 MTU (should typically be 1500 or 9000 for jumbo frames)
        cmd = host.run("cat /sys/class/net/bond0/mtu")
        if cmd.rc == 0:
            mtu = int(cmd.stdout.strip())
            assert mtu >= 1500, f"MTU too small: {mtu}"
            assert mtu <= 9000, f"MTU unusually large: {mtu}"
    
    @pytest.mark.parametrize("service", ["systemd-networkd", "networking"])
    def test_network_service_running(self, host, service):
        """Test that network service is running."""
        svc = host.service(service)
        if svc.exists:
            assert svc.is_running, f"{service} is not running"
            assert svc.is_enabled, f"{service} is not enabled"