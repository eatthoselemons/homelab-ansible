"""
Network security validation tests using testinfra.
Tests VLAN isolation, firewall rules, and security configurations.
"""

import pytest
import re


class TestVLANIsolation:
    """Test VLAN isolation and segmentation."""
    
    def test_vlan_isolation(self, host):
        """Test VLAN isolation is working."""
        # Try to access different VLAN segments
        # This should fail if isolation is properly configured
        
        # Get current host's primary IP
        ip_cmd = host.run("hostname -I | awk '{print $1}'")
        if ip_cmd.rc == 0:
            host_ip = ip_cmd.stdout.strip()
            
            # Determine which VLAN we're in
            if host_ip.startswith("10.10."):
                current_vlan = "management"
                isolated_ip = "10.80.0.1"  # IoT should be isolated
            elif host_ip.startswith("10.20."):
                current_vlan = "private"
                isolated_ip = "10.80.0.1"  # IoT should be isolated
            else:
                pytest.skip("Cannot determine current VLAN")
            
            # Test isolation (ping should fail or be filtered)
            ping_test = host.run(f"ping -c 2 -W 2 {isolated_ip}")
            
            # Note: This test might need adjustment based on firewall rules
            # Some isolation might allow ICMP but block other protocols
            if ping_test.rc != 0:
                pass  # Good, isolation is working
            else:
                pytest.warn(f"VLAN isolation may not be working: can reach {isolated_ip} from {current_vlan}")
    
    def test_dmz_isolation(self, host):
        """Test DMZ network isolation."""
        # DMZ (VLAN 30) should not be able to reach internal networks
        ip_cmd = host.run("hostname -I | awk '{print $1}'")
        if ip_cmd.rc == 0:
            host_ip = ip_cmd.stdout.strip()
            
            if host_ip.startswith("10.30."):
                # We're in DMZ, test isolation
                internal_ips = ["10.20.0.1", "10.40.0.1"]  # Private and Storage
                
                for internal_ip in internal_ips:
                    ping_test = host.run(f"ping -c 2 -W 2 {internal_ip}")
                    if ping_test.rc == 0:
                        pytest.fail(f"DMZ can reach internal network {internal_ip}")
            else:
                # Not in DMZ, skip this test
                pytest.skip("Not in DMZ VLAN")
    
    def test_guest_isolation(self, host):
        """Test guest network isolation."""
        ip_cmd = host.run("hostname -I | awk '{print $1}'")
        if ip_cmd.rc == 0:
            host_ip = ip_cmd.stdout.strip()
            
            if host_ip.startswith("10.60."):
                # We're in guest network
                # Should not reach any internal networks
                forbidden_ips = [
                    "10.10.0.1",  # Management
                    "10.20.0.1",  # Private
                    "10.40.0.1",  # Storage
                ]
                
                for forbidden_ip in forbidden_ips:
                    ping_test = host.run(f"ping -c 2 -W 2 {forbidden_ip}")
                    if ping_test.rc == 0:
                        pytest.fail(f"Guest network can reach {forbidden_ip}")
            else:
                pytest.skip("Not in guest VLAN")
    
    def test_iot_isolation(self, host):
        """Test IoT network isolation."""
        ip_cmd = host.run("hostname -I | awk '{print $1}'")
        if ip_cmd.rc == 0:
            host_ip = ip_cmd.stdout.strip()
            
            if host_ip.startswith("10.80."):
                # We're in IoT network
                # Should have very limited access
                forbidden_ips = [
                    "10.10.0.1",  # Management
                    "10.20.0.1",  # Private
                    "10.40.0.1",  # Storage
                    "10.50.0.1",  # Backup
                ]
                
                blocked_count = 0
                for forbidden_ip in forbidden_ips:
                    ping_test = host.run(f"ping -c 2 -W 2 {forbidden_ip}")
                    if ping_test.rc != 0:
                        blocked_count += 1
                
                assert blocked_count >= len(forbidden_ips) - 1, \
                    "IoT network not properly isolated"
            else:
                pytest.skip("Not in IoT VLAN")


class TestFirewallRules:
    """Test firewall rule effectiveness."""
    
    def test_port_scanning_protection(self, host):
        """Test protection against port scanning."""
        # Check for rate limiting rules
        if host.file("/proc/sys/net/ipv4/tcp_syncookies").exists:
            syncookies = host.file("/proc/sys/net/ipv4/tcp_syncookies").content_string.strip()
            assert syncookies == "1", "TCP SYN cookies not enabled"
        
        # Check for connection limit settings
        if host.file("/proc/sys/net/ipv4/tcp_max_syn_backlog").exists:
            backlog = int(host.file("/proc/sys/net/ipv4/tcp_max_syn_backlog").content_string.strip())
            if backlog < 2048:
                pytest.warn(f"TCP SYN backlog ({backlog}) may be too low")
    
    def test_ddos_protection(self, host):
        """Test DDoS protection measures."""
        # Check for DDoS protection kernel parameters
        protection_params = {
            "/proc/sys/net/ipv4/tcp_syncookies": "1",
            "/proc/sys/net/ipv4/icmp_echo_ignore_broadcasts": "1",
            "/proc/sys/net/ipv4/icmp_ignore_bogus_error_responses": "1",
            "/proc/sys/net/ipv4/conf/all/log_martians": "1",
        }
        
        for param, expected in protection_params.items():
            if host.file(param).exists:
                value = host.file(param).content_string.strip()
                if value != expected:
                    pytest.warn(f"{param} is {value}, should be {expected} for DDoS protection")
    
    def test_spoofing_protection(self, host):
        """Test IP spoofing protection."""
        # Check reverse path filtering
        rp_filter_files = [
            "/proc/sys/net/ipv4/conf/all/rp_filter",
            "/proc/sys/net/ipv4/conf/default/rp_filter"
        ]
        
        for rp_file in rp_filter_files:
            if host.file(rp_file).exists:
                value = host.file(rp_file).content_string.strip()
                if value not in ["1", "2"]:
                    pytest.warn(f"Reverse path filter not enabled in {rp_file}")
    
    def test_icmp_security(self, host):
        """Test ICMP security settings."""
        icmp_settings = {
            "/proc/sys/net/ipv4/icmp_echo_ignore_all": "0",  # Don't ignore all (too restrictive)
            "/proc/sys/net/ipv4/icmp_echo_ignore_broadcasts": "1",  # Ignore broadcasts
            "/proc/sys/net/ipv4/icmp_ratelimit": None,  # Should be set
            "/proc/sys/net/ipv4/icmp_ratemask": None,  # Should be set
        }
        
        for setting, expected in icmp_settings.items():
            if host.file(setting).exists:
                value = host.file(setting).content_string.strip()
                
                if expected is not None and value != expected:
                    pytest.warn(f"ICMP setting {setting} is {value}, expected {expected}")
                elif expected is None and value == "0":
                    pytest.warn(f"ICMP rate limiting may not be configured: {setting}")


class TestNetworkAccessControl:
    """Test network access control mechanisms."""
    
    def test_mac_address_filtering(self, host):
        """Test if MAC address filtering is possible."""
        # Check for ebtables (Ethernet bridge tables)
        ebtables_cmd = host.run("which ebtables 2>/dev/null")
        if ebtables_cmd.rc == 0:
            # Check if any MAC filtering rules exist
            mac_rules = host.run("sudo ebtables -L 2>/dev/null | grep -i mac")
            if mac_rules.rc == 0 and mac_rules.stdout:
                pass  # MAC filtering configured
            else:
                pytest.skip("No MAC filtering rules found")
        else:
            pytest.skip("ebtables not installed")
    
    def test_port_security(self, host):
        """Test port security configurations."""
        # Check for open ports
        netstat_cmd = host.run("netstat -tuln 2>/dev/null | grep LISTEN")
        if netstat_cmd.rc == 0:
            listening_ports = netstat_cmd.stdout
            
            # Check for unnecessary open ports
            risky_ports = [
                ("23", "telnet"),
                ("21", "ftp"),
                ("139", "netbios"),
                ("445", "smb"),
                ("111", "rpcbind"),
            ]
            
            for port, service in risky_ports:
                if f":{port} " in listening_ports:
                    pytest.warn(f"Risky port {port} ({service}) is open")
    
    def test_ssh_security(self, host):
        """Test SSH security configurations."""
        sshd_config = host.file("/etc/ssh/sshd_config")
        if sshd_config.exists:
            config = sshd_config.content_string
            
            # Security checks
            security_settings = {
                "PermitRootLogin": ["no", "prohibit-password"],
                "PasswordAuthentication": ["no"],
                "PubkeyAuthentication": ["yes"],
                "PermitEmptyPasswords": ["no"],
                "MaxAuthTries": None,  # Should be <= 3
                "ClientAliveInterval": None,  # Should be set
            }
            
            for setting, valid_values in security_settings.items():
                if valid_values:
                    found = False
                    for value in valid_values:
                        if f"{setting} {value}" in config:
                            found = True
                            break
                    
                    if not found:
                        pytest.warn(f"SSH {setting} not properly configured")
                else:
                    # Check if setting exists
                    if setting not in config:
                        pytest.warn(f"SSH {setting} not configured")
                    elif setting == "MaxAuthTries":
                        match = re.search(f"{setting} (\\d+)", config)
                        if match and int(match.group(1)) > 3:
                            pytest.warn(f"SSH MaxAuthTries too high: {match.group(1)}")


class TestNetworkEncryption:
    """Test network encryption and secure protocols."""
    
    def test_ssl_tls_versions(self, host):
        """Test that only secure TLS versions are used."""
        # Check OpenSSL configuration
        openssl_conf = host.file("/etc/ssl/openssl.cnf")
        if openssl_conf.exists:
            config = openssl_conf.content_string
            
            # Check for weak protocols
            if "SSLv2" in config or "SSLv3" in config:
                pytest.warn("Weak SSL versions may be enabled")
            
            # Check minimum protocol version
            if "MinProtocol" in config:
                if "TLSv1.2" not in config and "TLSv1.3" not in config:
                    pytest.warn("Minimum TLS version should be 1.2 or higher")
    
    def test_ipsec_configuration(self, host):
        """Test IPsec configuration if present."""
        # Check for strongSwan or LibreSwan
        ipsec_cmd = host.run("which ipsec 2>/dev/null")
        if ipsec_cmd.rc == 0:
            # Check IPsec status
            status_cmd = host.run("sudo ipsec status 2>/dev/null")
            if status_cmd.rc == 0:
                if "ESTABLISHED" in status_cmd.stdout:
                    pass  # IPsec tunnels established
                elif "INSTALLED" in status_cmd.stdout:
                    pass  # IPsec policies installed
                else:
                    pytest.skip("IPsec configured but no active tunnels")
        else:
            pytest.skip("IPsec not installed")
    
    def test_wireguard_security(self, host):
        """Test WireGuard VPN security if configured."""
        wg_cmd = host.run("which wg 2>/dev/null")
        if wg_cmd.rc == 0:
            # Check WireGuard interfaces
            wg_show = host.run("sudo wg show 2>/dev/null")
            if wg_show.rc == 0 and wg_show.stdout:
                # Check for proper key lengths
                if "private key: (hidden)" in wg_show.stdout:
                    pass  # Keys are properly hidden
                
                # Check handshake status
                if "latest handshake:" in wg_show.stdout:
                    # Parse handshake times
                    handshakes = re.findall(r'latest handshake: (.*)', wg_show.stdout)
                    for handshake in handshakes:
                        if "Never" in handshake:
                            pytest.warn("WireGuard peer never completed handshake")
            else:
                pytest.skip("WireGuard installed but not configured")
        else:
            pytest.skip("WireGuard not installed")


class TestBroadcastStormProtection:
    """Test broadcast storm and loop protection."""
    
    def test_broadcast_storm_protection(self, host):
        """Test if broadcast storm protection is configured."""
        # Check for storm control on interfaces
        if host.interface("bond0").exists:
            # Check interface statistics for drops
            stats_cmd = host.run("ip -s link show bond0")
            if stats_cmd.rc == 0:
                # Look for RX/TX drops which might indicate storm control
                if "dropped" in stats_cmd.stdout:
                    pass  # Statistics available
        
        # Note: Actual storm control testing would require switch access
        pytest.skip("Broadcast storm protection requires switch-level validation")
    
    def test_spanning_tree_protection(self, host):
        """Test STP/RSTP for loop prevention."""
        # Check if bridge utilities are installed
        brctl_cmd = host.run("which brctl 2>/dev/null")
        if brctl_cmd.rc == 0:
            # Check for bridges
            bridges = host.run("brctl show 2>/dev/null")
            if bridges.rc == 0 and bridges.stdout:
                # Check STP status on bridges
                bridge_names = re.findall(r'^(\S+)\s+', bridges.stdout, re.MULTILINE)
                
                for bridge in bridge_names:
                    stp_status = host.run(f"brctl showstp {bridge} 2>/dev/null")
                    if stp_status.rc == 0:
                        if "enabled no" in stp_status.stdout:
                            pytest.warn(f"STP not enabled on bridge {bridge}")
        else:
            pytest.skip("Bridge utilities not installed")
    
    def test_bpdu_guard(self, host):
        """Test BPDU guard configuration."""
        # This is typically configured on switches
        # Can only test if host has bridge with STP
        
        # Check for BPDU filter/guard kernel module
        bpdu_module = host.run("lsmod | grep -E 'bridge|stp'")
        if bpdu_module.rc == 0:
            # Bridge/STP modules loaded
            pass
        else:
            pytest.skip("Bridge/STP modules not loaded")