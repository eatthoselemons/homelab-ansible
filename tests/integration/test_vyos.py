"""
VyOS router validation tests using testinfra.
Tests router configuration, firewall, NAT, and services.
"""

import pytest


class TestVyOS:
    """Test VyOS router configuration."""
    
    def test_vyos_system(self, host):
        """Test that this is a VyOS system."""
        version_file = host.file("/etc/version")
        
        if not version_file.exists:
            pytest.skip("Not a VyOS system")
        
        assert "VyOS" in version_file.content_string, \
            f"System is not VyOS: {version_file.content_string}"
    
    def test_vyos_configuration_tools(self, host):
        """Test VyOS configuration tools are available."""
        # Check for VyOS-specific commands
        vyos_commands = [
            "vyos-cfg-cmd-wrapper",
            "vyatta-cfg-cmd-wrapper"  # Older versions
        ]
        
        found = False
        for cmd in vyos_commands:
            if host.run(f"which {cmd}").rc == 0:
                found = True
                break
        
        assert found, "VyOS configuration tools not found"
    
    def test_network_interfaces(self, host):
        """Test that WAN and LAN interfaces are configured."""
        required_interfaces = {
            "eth0": "WAN interface",
            "eth1": "LAN interface"
        }
        
        for iface, description in required_interfaces.items():
            interface = host.interface(iface)
            assert interface.exists, f"{description} ({iface}) does not exist"
            
            # Check interface is up
            cmd = host.run(f"ip link show {iface}")
            assert "state UP" in cmd.stdout or "state UNKNOWN" in cmd.stdout, \
                f"{description} ({iface}) is not UP"
    
    def test_vlan_configuration(self, host, expected_vlans):
        """Test VLAN interfaces are configured."""
        configured_vlans = []
        
        for vlan in expected_vlans:
            # VyOS uses eth1.VLAN format
            vlan_if = f"eth1.{vlan}"
            if host.interface(vlan_if).exists:
                configured_vlans.append(vlan)
        
        # Should have at least some VLANs configured
        assert len(configured_vlans) > 0, "No VLANs configured on router"
        
        # Log which VLANs are configured
        missing = set(expected_vlans) - set(configured_vlans)
        if missing:
            pytest.warn(f"Missing VLANs: {missing}")
    
    def test_firewall_configured(self, host):
        """Test that firewall rules are configured."""
        # Check iptables rules
        cmd = host.run("sudo iptables -L -n | wc -l")
        
        if cmd.rc == 0:
            rule_count = int(cmd.stdout.strip())
            # Should have more than just default policy lines (>10 lines)
            assert rule_count > 10, f"Too few firewall rules: {rule_count} lines"
    
    def test_nat_configured(self, host):
        """Test that NAT is configured for internet access."""
        cmd = host.run("sudo iptables -t nat -L -n")
        
        assert cmd.rc == 0, "Cannot check NAT rules"
        assert "MASQUERADE" in cmd.stdout or "SNAT" in cmd.stdout, \
            "No NAT masquerade rules found"
    
    def test_dhcp_server(self, host):
        """Test DHCP server is running."""
        # VyOS can use different DHCP servers
        dhcp_services = ["dhcpd", "dnsmasq", "kea-dhcp4"]
        
        found = False
        for service in dhcp_services:
            if host.service(service).is_running:
                found = True
                break
            # Also check process
            if host.run(f"pgrep {service}").rc == 0:
                found = True
                break
        
        assert found, "No DHCP server running"
    
    def test_dns_forwarding(self, host):
        """Test DNS forwarding is configured."""
        # Check for DNS forwarding services
        dns_services = ["dnsmasq", "pdns-recursor", "unbound", "bind9"]
        
        found = False
        for service in dns_services:
            if host.run(f"pgrep {service}").rc == 0:
                found = True
                break
        
        assert found, "No DNS forwarding service running"
    
    def test_routing_table(self, host):
        """Test routing table has necessary routes."""
        cmd = host.run("ip route show")
        
        assert cmd.rc == 0, "Cannot get routing table"
        routes = cmd.stdout
        
        # Should have default route
        assert "default via" in routes, "No default route configured"
        
        # Count routes - should have multiple for different VLANs
        route_count = len(routes.strip().split('\n'))
        assert route_count >= 5, f"Too few routes configured: {route_count}"
    
    def test_system_resources(self, host):
        """Test system has adequate resources."""
        # Check memory
        mem_cmd = host.run("free -m | grep Mem | awk '{print $2}'")
        if mem_cmd.rc == 0:
            total_mem = int(mem_cmd.stdout.strip())
            assert total_mem >= 512, f"Insufficient memory: {total_mem}MB (need >= 512MB)"
        
        # Check CPU count
        cpu_cmd = host.run("nproc")
        if cpu_cmd.rc == 0:
            cpu_count = int(cpu_cmd.stdout.strip())
            assert cpu_count >= 1, f"Insufficient CPUs: {cpu_count}"
    
    def test_ntp_configured(self, host):
        """Test that NTP is configured for time synchronization."""
        ntp_services = ["ntp", "chrony", "systemd-timesyncd"]
        
        found = False
        for service in ntp_services:
            svc = host.service(service)
            if svc.exists and svc.is_running:
                found = True
                break
        
        if not found:
            # Check if NTP is configured in VyOS
            ntp_conf = host.run("show configuration commands | grep ntp")
            if ntp_conf.rc == 0 and ntp_conf.stdout.strip():
                found = True
        
        assert found, "NTP not configured"
    
    def test_ssh_hardening(self, host):
        """Test SSH is properly hardened."""
        sshd_config = host.file("/etc/ssh/sshd_config")
        
        if sshd_config.exists:
            config = sshd_config.content_string
            
            # Check for basic hardening
            security_checks = [
                ("PermitRootLogin no" in config or "PermitRootLogin prohibit-password" in config,
                 "Root login should be disabled or key-only"),
                ("PasswordAuthentication no" in config or "PubkeyAuthentication yes" in config,
                 "Should prefer key authentication"),
            ]
            
            for check, message in security_checks:
                if not check:
                    pytest.warn(f"SSH Security: {message}")
    
    def test_wireguard_if_configured(self, host):
        """Test WireGuard VPN if configured."""
        wg_cmd = host.run("which wg")
        
        if wg_cmd.rc == 0:
            # WireGuard is installed, check for interfaces
            wg_show = host.run("sudo wg show")
            if wg_show.rc == 0 and wg_show.stdout.strip():
                # WireGuard is configured
                assert "interface:" in wg_show.stdout, "WireGuard installed but not configured"