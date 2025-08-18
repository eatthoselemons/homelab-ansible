"""
Network topology validation tests using testinfra.
Tests overall network structure, VLANs, and DNS resolution.
"""

import pytest
import re


class TestNetworkTopology:
    """Test overall network topology is correct."""
    
    def test_router_connectivity(self, host):
        """Test connectivity to VyOS router."""
        # Router should be reachable at gateway addresses
        router_ips = [
            "10.10.0.1",  # Management VLAN gateway
            "10.20.0.1",  # Private VLAN gateway
        ]
        
        reachable = []
        for router_ip in router_ips:
            ping_cmd = host.run(f"ping -c 2 -W 2 {router_ip}")
            if ping_cmd.rc == 0:
                reachable.append(router_ip)
        
        assert len(reachable) > 0, f"Cannot reach router at any gateway IP: {router_ips}"
    
    def test_critical_network_paths(self, host):
        """Test critical network paths are functional."""
        # Test paths between key network segments
        critical_paths = {
            "Router to Switches": ["10.10.0.1", "10.10.0.2"],
            "Management to Private": ["10.10.0.1", "10.20.0.1"],
            "Private to Storage": ["10.20.0.1", "10.40.0.1"],
        }
        
        for path_name, endpoints in critical_paths.items():
            reachable = 0
            for endpoint in endpoints:
                ping_cmd = host.run(f"ping -c 1 -W 1 {endpoint}")
                if ping_cmd.rc == 0:
                    reachable += 1
            
            if reachable < len(endpoints):
                pytest.warn(f"Path '{path_name}' partially unreachable")


class TestVLANConfiguration:
    """Test VLAN configuration across network."""
    
    def test_vlan_interfaces_on_host(self, host):
        """Test VLAN interfaces are properly configured on host."""
        # Check for bond interface first
        bond_exists = host.interface("bond0").exists
        
        if bond_exists:
            base_interface = "bond0"
        else:
            # Fallback to physical interface
            base_interface = None
            for iface in ["eth0", "eth1", "enp1s0", "ens3"]:
                if host.interface(iface).exists:
                    base_interface = iface
                    break
            
            if not base_interface:
                pytest.skip("No suitable network interface found")
        
        # Expected VLANs per network design
        expected_vlans = {
            10: "Management",
            20: "Private", 
            30: "Public/DMZ",
            40: "Storage",
            50: "Backup",
            60: "Guest WiFi",
            70: "Trusted WiFi",
            80: "IoT",
            90: "Logs/Monitoring"
        }
        
        configured_vlans = []
        missing_vlans = []
        
        for vlan_id, description in expected_vlans.items():
            vlan_interface = f"{base_interface}.{vlan_id}"
            
            if host.interface(vlan_interface).exists:
                configured_vlans.append(vlan_id)
                
                # Check interface is up
                state_cmd = host.run(f"ip link show {vlan_interface}")
                if state_cmd.rc == 0:
                    assert "state UP" in state_cmd.stdout or "state UNKNOWN" in state_cmd.stdout, \
                        f"VLAN {vlan_id} ({description}) interface not UP"
            else:
                missing_vlans.append(f"{vlan_id} ({description})")
        
        # Should have at least critical VLANs
        critical_vlans = [10, 20, 30]  # Management, Private, Public
        critical_configured = [v for v in critical_vlans if v in configured_vlans]
        
        assert len(critical_configured) > 0, \
            f"No critical VLANs configured. Missing: {missing_vlans}"
        
        if missing_vlans:
            pytest.warn(f"Missing VLANs: {missing_vlans}")
    
    def test_vlan_connectivity(self, host):
        """Test connectivity within VLANs."""
        # Test that we can reach gateways in different VLANs
        vlan_gateways = {
            "Management": "10.10.0.1",
            "Private": "10.20.0.1",
            "Public": "10.30.0.1",
            "Storage": "10.40.0.1",
            "Backup": "10.50.0.1",
            "Logs": "10.90.0.1"
        }
        
        reachable = {}
        unreachable = {}
        
        for vlan_name, gateway in vlan_gateways.items():
            ping_cmd = host.run(f"ping -c 2 -W 2 {gateway}")
            if ping_cmd.rc == 0:
                reachable[vlan_name] = gateway
            else:
                unreachable[vlan_name] = gateway
        
        # Should be able to reach at least some gateways
        assert len(reachable) > 0, \
            f"Cannot reach any VLAN gateways. Tried: {list(vlan_gateways.values())}"
        
        if unreachable:
            # Some VLANs might not be configured yet
            pytest.warn(f"Unreachable VLAN gateways: {unreachable}")
    
    def test_vlan_tagging(self, host):
        """Test VLAN tagging is properly configured."""
        # Check that 802.1Q module is loaded
        lsmod_cmd = host.run("lsmod | grep 8021q")
        if lsmod_cmd.rc != 0:
            # Module might be built-in
            modinfo_cmd = host.run("modinfo 8021q 2>/dev/null")
            if modinfo_cmd.rc != 0:
                pytest.warn("802.1Q VLAN module not loaded")
        
        # Check VLAN configuration files
        vlan_configs = [
            "/proc/net/vlan/config",
            "/etc/network/interfaces.d/vlans",
        ]
        
        config_found = False
        for config_path in vlan_configs:
            if host.file(config_path).exists:
                config_found = True
                break
        
        if not config_found:
            # VLANs might be configured differently
            pytest.skip("VLAN configuration method not detected")


class TestDNSResolution:
    """Test DNS resolution across network."""
    
    def test_internal_dns(self, host):
        """Test internal DNS resolution."""
        # Test resolution of internal domains
        internal_domains = [
            "harvester.management.awynn.in",
            "gitlab.private.awynn.in",
            "grafana.logs.awynn.in"
        ]
        
        resolved = []
        failed = []
        
        for domain in internal_domains:
            # Use nslookup or dig
            dns_test = host.run(f"nslookup {domain} 2>/dev/null | grep -A1 'Name:'")
            if dns_test.rc == 0 and "Address:" in dns_test.stdout:
                resolved.append(domain)
            else:
                failed.append(domain)
        
        if len(resolved) == 0:
            # Internal DNS might not be configured yet
            pytest.skip("Internal DNS not configured")
        
        if failed:
            pytest.warn(f"Failed to resolve internal domains: {failed}")
    
    def test_external_dns(self, host):
        """Test external DNS resolution."""
        # Test resolution of external domains
        external_domains = [
            "google.com",
            "cloudflare.com",
            "github.com"
        ]
        
        resolved = []
        for domain in external_domains:
            dns_test = host.run(f"nslookup {domain} 2>/dev/null | grep -A1 'Name:'")
            if dns_test.rc == 0:
                resolved.append(domain)
        
        assert len(resolved) > 0, "Cannot resolve any external domains"
    
    def test_dns_servers(self, host):
        """Test DNS server configuration."""
        # Check /etc/resolv.conf
        resolv_conf = host.file("/etc/resolv.conf")
        if resolv_conf.exists:
            content = resolv_conf.content_string
            
            # Should have nameserver entries
            assert "nameserver" in content, "No DNS servers configured"
            
            # Count nameservers
            nameservers = [line for line in content.split('\n') 
                          if line.strip().startswith('nameserver')]
            
            assert len(nameservers) > 0, "No nameserver entries found"
            
            # Check for local DNS (VyOS router)
            local_dns = ["10.10.0.1", "10.20.0.1", "127.0.0.1"]
            has_local_dns = any(dns in content for dns in local_dns)
            
            if not has_local_dns:
                pytest.warn("No local DNS server configured")
    
    def test_dns_search_domains(self, host):
        """Test DNS search domains configuration."""
        resolv_conf = host.file("/etc/resolv.conf")
        if resolv_conf.exists:
            content = resolv_conf.content_string
            
            # Check for search domains
            search_lines = [line for line in content.split('\n')
                          if line.strip().startswith('search')]
            
            if search_lines:
                # Should include our domains
                expected_domains = ["awynn.in", "management.awynn.in", "private.awynn.in"]
                search_domains = search_lines[0].split()[1:]
                
                matches = [d for d in expected_domains if any(d in sd for sd in search_domains)]
                
                if not matches:
                    pytest.warn(f"DNS search domains don't include expected domains: {search_domains}")
            else:
                pytest.warn("No DNS search domains configured")


class TestNetworkSegmentation:
    """Test network segmentation and isolation."""
    
    def test_vlan_count(self, host):
        """Test that expected number of VLANs are configured."""
        # Count VLAN interfaces
        vlan_count_cmd = host.run("ip link show | grep -c '\\..*@' || true")
        if vlan_count_cmd.rc == 0:
            vlan_count = int(vlan_count_cmd.stdout.strip())
            
            # Should have at least 3 VLANs (Management, Private, Public)
            assert vlan_count >= 3, f"Only {vlan_count} VLANs configured, expected at least 3"
            
            # Warn if not all 9 VLANs are configured
            if vlan_count < 9:
                pytest.warn(f"Only {vlan_count} of 9 expected VLANs configured")
    
    def test_network_ranges(self, host):
        """Test that network ranges follow standards."""
        # Get all IP addresses
        ip_cmd = host.run("ip addr show | grep 'inet ' | grep -v '127.0.0.1'")
        if ip_cmd.rc == 0:
            ip_addresses = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', ip_cmd.stdout)
            
            # Check that IPs follow our network standards
            expected_prefixes = {
                "10.10.": "Management",
                "10.20.": "Private",
                "10.30.": "Public",
                "10.40.": "Storage",
                "10.50.": "Backup",
                "10.60.": "Guest",
                "10.70.": "Trusted",
                "10.80.": "IoT",
                "10.90.": "Logs"
            }
            
            for ip in ip_addresses:
                # Skip link-local and other special addresses
                if ip.startswith("169.254.") or ip.startswith("192.168."):
                    continue
                
                # Check if IP matches expected pattern
                matched = False
                for prefix in expected_prefixes:
                    if ip.startswith(prefix):
                        matched = True
                        break
                
                if not matched and ip.startswith("10."):
                    pytest.warn(f"IP {ip} doesn't match expected network standards")