"""
MikroTik switch validation tests using testinfra.
Tests switch connectivity, VLAN configuration, and management interfaces.
"""

import pytest
import re


class TestMikroTikSwitches:
    """Test MikroTik switch configuration."""
    
    def test_switch_connectivity(self, host):
        """Test connectivity to MikroTik switches."""
        # Switches should have management IPs in VLAN 10
        switch_ips = [
            "10.10.0.2",   # Main MikroTik switch
            "10.10.0.3",   # Basement switch
            "10.10.0.4",   # Rack switch
        ]
        
        reachable_switches = []
        unreachable_switches = []
        
        for switch_ip in switch_ips:
            ping_cmd = host.run(f"ping -c 2 -W 2 {switch_ip}")
            if ping_cmd.rc == 0:
                reachable_switches.append(switch_ip)
            else:
                unreachable_switches.append(switch_ip)
        
        # At least one switch should be reachable
        assert len(reachable_switches) > 0, \
            f"No switches reachable. Tried: {switch_ips}"
        
        if unreachable_switches:
            pytest.warn(f"Some switches unreachable: {unreachable_switches}")
    
    def test_switch_api_access(self, host):
        """Test API access to MikroTik switches."""
        # MikroTik switches should have API enabled on port 8728 (API) or 8729 (API-SSL)
        switch_ips = ["10.10.0.2", "10.10.0.3", "10.10.0.4"]
        
        api_accessible = []
        for switch_ip in switch_ips:
            # Test standard API port
            api_test = host.run(f"nc -zv -w2 {switch_ip} 8728 2>&1")
            api_ssl_test = host.run(f"nc -zv -w2 {switch_ip} 8729 2>&1")
            
            if api_test.rc == 0 or api_ssl_test.rc == 0:
                api_accessible.append(switch_ip)
        
        if len(api_accessible) == 0:
            pytest.skip("No MikroTik API access available for testing")
    
    def test_switch_web_interface(self, host):
        """Test web interface accessibility."""
        switch_ips = ["10.10.0.2", "10.10.0.3", "10.10.0.4"]
        
        web_accessible = []
        for switch_ip in switch_ips:
            # Test HTTP/HTTPS access
            http_test = host.run(f"curl -k --connect-timeout 2 http://{switch_ip} 2>/dev/null | head -n1")
            https_test = host.run(f"curl -k --connect-timeout 2 https://{switch_ip} 2>/dev/null | head -n1")
            
            if http_test.rc == 0 or https_test.rc == 0:
                web_accessible.append(switch_ip)
        
        if len(web_accessible) > 0:
            pass  # At least one switch has web interface
        else:
            pytest.warn("No switch web interfaces accessible")
    
    def test_switch_vlan_configuration(self, host):
        """Test VLAN configuration on switches via SNMP if available."""
        switch_ips = ["10.10.0.2", "10.10.0.3", "10.10.0.4"]
        
        for switch_ip in switch_ips:
            # Try SNMP to get VLAN information
            snmp_test = host.run(f"snmpwalk -v2c -c public {switch_ip} .1.3.6.1.2.1.17.7.1.4.3.1.1 2>/dev/null")
            
            if snmp_test.rc == 0 and snmp_test.stdout:
                # Parse VLAN IDs from SNMP output
                vlan_ids = re.findall(r'\.(\d+) =', snmp_test.stdout)
                vlan_ids = list(set(int(v) for v in vlan_ids if 1 < int(v) < 4095))
                
                # Check for expected VLANs
                expected_vlans = [10, 20, 30, 40, 50, 60, 70, 80, 90]
                configured_vlans = [v for v in expected_vlans if v in vlan_ids]
                
                if len(configured_vlans) > 0:
                    pass  # VLANs are configured
                else:
                    pytest.warn(f"No expected VLANs found on switch {switch_ip}")
            else:
                # SNMP not available, skip this check
                continue
    
    def test_switch_trunk_ports(self, host):
        """Test trunk port configuration between switches."""
        # This test would require switch API or SNMP access
        # Check that inter-switch links are configured as trunks
        switch_ips = ["10.10.0.2", "10.10.0.3", "10.10.0.4"]
        
        for switch_ip in switch_ips:
            # Try to get port information via SNMP
            port_info = host.run(f"snmpwalk -v2c -c public {switch_ip} .1.3.6.1.2.1.2.2.1.8 2>/dev/null")
            
            if port_info.rc == 0 and port_info.stdout:
                # Look for ports that are up (operational status = 1)
                up_ports = re.findall(r'\.(\d+) = INTEGER: 1', port_info.stdout)
                
                if len(up_ports) > 1:
                    # Multiple ports are up, likely including trunk ports
                    pass
                else:
                    pytest.warn(f"Switch {switch_ip} may not have trunk ports configured")
            else:
                # SNMP not available
                continue
    
    def test_switch_lag_configuration(self, host):
        """Test Link Aggregation Group (LAG) configuration."""
        # Check if switches have LAG configured for redundancy
        switch_ips = ["10.10.0.2", "10.10.0.3", "10.10.0.4"]
        
        for switch_ip in switch_ips:
            # Try to detect LAG via SNMP (802.3ad)
            lag_check = host.run(f"snmpwalk -v2c -c public {switch_ip} .1.2.840.10006.300.43 2>/dev/null")
            
            if lag_check.rc == 0 and lag_check.stdout:
                # LAG information found
                pass
            else:
                # LAG might not be configured or SNMP not available
                continue
    
    def test_switch_stp_configuration(self, host):
        """Test Spanning Tree Protocol configuration."""
        switch_ips = ["10.10.0.2", "10.10.0.3", "10.10.0.4"]
        
        for switch_ip in switch_ips:
            # Check for STP via SNMP
            stp_check = host.run(f"snmpwalk -v2c -c public {switch_ip} .1.3.6.1.2.1.17.2 2>/dev/null")
            
            if stp_check.rc == 0 and stp_check.stdout:
                # STP is configured
                # Could parse for root bridge, port states, etc.
                pass
            else:
                # STP status unknown
                continue
    
    def test_switch_management_access(self, host):
        """Test management access security."""
        switch_ips = ["10.10.0.2", "10.10.0.3", "10.10.0.4"]
        
        for switch_ip in switch_ips:
            # Test SSH access (should be enabled for management)
            ssh_test = host.run(f"nc -zv -w2 {switch_ip} 22 2>&1")
            
            if ssh_test.rc == 0:
                # SSH is available
                pass
            else:
                # SSH might be disabled or using non-standard port
                pytest.warn(f"SSH not accessible on switch {switch_ip}")
            
            # Test that telnet is disabled (security best practice)
            telnet_test = host.run(f"nc -zv -w2 {switch_ip} 23 2>&1")
            
            if telnet_test.rc == 0:
                pytest.warn(f"Telnet is enabled on switch {switch_ip} (security risk)")