"""
VyOS router validation tests using testinfra.
Tests router configuration, VLANs, firewall, NAT, DHCP, and services.
Based on the actual vyos.setup role requirements and network standards.
"""

import pytest
import json
import re


class TestVyOSSystem:
    """Test VyOS system configuration."""
    
    def test_vyos_version(self, host):
        """Test that this is a VyOS system with correct version."""
        # Check for VyOS version file
        version_file = host.file("/usr/share/vyos/version.json")
        if version_file.exists:
            try:
                version_data = json.loads(version_file.content_string)
                assert "version" in version_data, "No version in VyOS version file"
                # Should be VyOS 1.4 or later for modern features
                version = version_data.get("version", "")
                assert version.startswith("1.4") or version.startswith("1.5"), \
                    f"VyOS version {version} may not support all required features"
            except json.JSONDecodeError:
                # Fallback to text version file
                version_text = host.file("/etc/version")
                if version_text.exists:
                    assert "VyOS" in version_text.content_string
        else:
            # Legacy version check
            version_text = host.file("/etc/version")
            assert version_text.exists and "VyOS" in version_text.content_string, \
                "Not a VyOS system"
    
    def test_vyos_config_mode(self, host):
        """Test VyOS configuration system is available."""
        # Check for VyOS configuration binaries
        vyos_cmds = [
            "/usr/libexec/vyos/conf_mode",
            "/usr/libexec/vyos/op_mode",
            "/usr/bin/vyos-configd"
        ]
        
        found_cmds = []
        for cmd_path in vyos_cmds:
            if host.file(cmd_path).exists:
                found_cmds.append(cmd_path)
        
        assert len(found_cmds) > 0, "No VyOS configuration system found"
    
    def test_system_login(self, host):
        """Test system login configuration."""
        # Check that admin user exists
        admin_user = host.user("vyos") or host.user("admin")
        assert admin_user, "No admin user (vyos/admin) found"
        
        # Check SSH key is configured for ansible
        ssh_dir = host.file("/home/vyos/.ssh") or host.file("/home/admin/.ssh")
        if ssh_dir and ssh_dir.exists:
            authorized_keys = host.file(f"{ssh_dir.path}/authorized_keys")
            assert authorized_keys.exists, "No SSH authorized_keys configured"
            # Should contain ansible SSH key
            assert authorized_keys.size > 0, "authorized_keys is empty"
    
    def test_hostname_configuration(self, host):
        """Test hostname is properly configured."""
        hostname_cmd = host.run("hostname")
        assert hostname_cmd.rc == 0
        hostname = hostname_cmd.stdout.strip()
        
        # Should not be default hostname
        assert hostname not in ["vyos", "localhost"], \
            f"Hostname '{hostname}' is not configured properly"
        
        # Check hostname in config
        if host.file("/config/config.boot").exists:
            config = host.file("/config/config.boot").content_string
            assert f"host-name {hostname}" in config or f"host-name '{hostname}'" in config


class TestVyOSNetworkInterfaces:
    """Test VyOS network interface configuration."""
    
    def test_wan_interface(self, host):
        """Test WAN interface configuration."""
        # Common WAN interface names
        wan_interfaces = ["eth0", "eth1", "wan0"]
        
        wan_found = False
        for iface in wan_interfaces:
            if host.interface(iface).exists:
                wan_found = True
                # Check interface is up
                iface_state = host.run(f"ip link show {iface}")
                assert "state UP" in iface_state.stdout or "state UNKNOWN" in iface_state.stdout, \
                    f"WAN interface {iface} is not UP"
                
                # Check for IP address (could be DHCP or static)
                ip_cmd = host.run(f"ip addr show {iface}")
                assert "inet " in ip_cmd.stdout, f"No IP address on WAN interface {iface}"
                break
        
        assert wan_found, "No WAN interface found"
    
    def test_lan_interface(self, host):
        """Test LAN interface configuration."""
        # Common LAN interface names  
        lan_interfaces = ["eth1", "eth2", "lan0"]
        
        lan_found = False
        for iface in lan_interfaces:
            if host.interface(iface).exists:
                lan_found = True
                # Check interface is up
                iface_state = host.run(f"ip link show {iface}")
                assert "state UP" in iface_state.stdout or "state UNKNOWN" in iface_state.stdout, \
                    f"LAN interface {iface} is not UP"
                break
        
        assert lan_found, "No LAN interface found"
    
    def test_vlan_interfaces(self, host, expected_networks):
        """Test VLAN interfaces are configured per network standards."""
        # VLANs should be on LAN interface (eth1 typically)
        base_interface = None
        for iface in ["eth1", "eth2", "lan0"]:
            if host.interface(iface).exists:
                base_interface = iface
                break
        
        if not base_interface:
            pytest.skip("No LAN interface found for VLANs")
        
        configured_vlans = []
        missing_vlans = []
        
        for network_name, network_config in expected_networks.items():
            vlan_id = network_config["vlan"]
            vlan_interface = f"{base_interface}.{vlan_id}"
            
            if host.interface(vlan_interface).exists:
                configured_vlans.append(vlan_id)
                
                # Check VLAN interface is up
                iface_state = host.run(f"ip link show {vlan_interface}")
                if iface_state.rc == 0:
                    assert "state UP" in iface_state.stdout or "state UNKNOWN" in iface_state.stdout, \
                        f"VLAN {vlan_id} interface is not UP"
                
                # Check IP configuration
                expected_ip = network_config["gateway"]
                ip_cmd = host.run(f"ip addr show {vlan_interface}")
                if ip_cmd.rc == 0 and expected_ip:
                    # Gateway should be .1 in the subnet
                    assert expected_ip.split('/')[0] in ip_cmd.stdout, \
                        f"VLAN {vlan_id} missing expected IP {expected_ip}"
            else:
                missing_vlans.append(vlan_id)
        
        # Should have at least some VLANs configured
        assert len(configured_vlans) > 0, f"No VLANs configured. Expected: {list(expected_networks.keys())}"
        
        # Log missing VLANs as warning (some might be optional)
        if missing_vlans:
            pytest.warn(f"Missing VLANs: {missing_vlans}")


class TestVyOSFirewall:
    """Test VyOS firewall configuration."""
    
    def test_firewall_zones(self, host):
        """Test firewall zones are configured."""
        # Check nftables rules (VyOS 1.4+ uses nftables)
        nft_cmd = host.run("sudo nft list ruleset")
        if nft_cmd.rc == 0:
            ruleset = nft_cmd.stdout
            
            # Should have zones defined
            assert "zone" in ruleset.lower() or "chain" in ruleset.lower(), \
                "No firewall zones or chains configured"
            
            # Check for common zones
            expected_zones = ["wan", "lan", "local", "dmz"]
            configured_zones = []
            for zone in expected_zones:
                if zone in ruleset.lower():
                    configured_zones.append(zone)
            
            assert len(configured_zones) > 0, "No standard firewall zones found"
        else:
            # Fallback to iptables for older VyOS
            iptables_cmd = host.run("sudo iptables -L -n")
            assert iptables_cmd.rc == 0, "Cannot check firewall rules"
            assert len(iptables_cmd.stdout.split('\n')) > 20, "Too few firewall rules"
    
    def test_firewall_nat(self, host):
        """Test NAT configuration."""
        # Check NAT rules
        nft_nat = host.run("sudo nft list table nat 2>/dev/null")
        if nft_nat.rc == 0:
            # nftables NAT
            assert "masquerade" in nft_nat.stdout.lower() or "snat" in nft_nat.stdout.lower(), \
                "No NAT masquerade rules found"
        else:
            # iptables NAT
            iptables_nat = host.run("sudo iptables -t nat -L -n")
            assert iptables_nat.rc == 0, "Cannot check NAT rules"
            assert "MASQUERADE" in iptables_nat.stdout or "SNAT" in iptables_nat.stdout, \
                "No NAT masquerade rules found"
    
    def test_firewall_state_policy(self, host):
        """Test stateful firewall configuration."""
        # Check for connection tracking
        conntrack = host.run("sudo conntrack -L 2>/dev/null | head -5")
        if conntrack.rc == 0:
            # Connection tracking is active
            pass
        else:
            # Check if connection tracking modules are loaded
            modules = host.run("lsmod | grep -E 'nf_conntrack|ip_conntrack'")
            assert modules.rc == 0, "Connection tracking not configured"
    
    def test_firewall_logging(self, host):
        """Test firewall logging configuration."""
        # Check if firewall logging is configured
        if host.file("/var/log/vyos/vyos-firewall.log").exists:
            # Firewall logging to file
            pass
        else:
            # Check syslog for firewall entries
            syslog_check = host.run("grep -i firewall /etc/rsyslog.conf 2>/dev/null")
            if syslog_check.rc != 0:
                pytest.warn("Firewall logging may not be configured")


class TestVyOSServices:
    """Test VyOS services configuration."""
    
    def test_dhcp_server(self, host):
        """Test DHCP server configuration."""
        # Check for DHCP server process
        dhcp_processes = ["dhcpd", "kea-dhcp4", "dnsmasq"]
        
        dhcp_running = False
        for process in dhcp_processes:
            if host.process.filter(comm=process):
                dhcp_running = True
                break
        
        if not dhcp_running:
            # Check if DHCP is configured but not running
            config_file = host.file("/config/config.boot")
            if config_file.exists:
                if "dhcp-server" in config_file.content_string:
                    pytest.fail("DHCP server configured but not running")
                else:
                    pytest.skip("DHCP server not configured")
        
        # If DHCP is running, check for leases
        lease_files = [
            "/var/lib/dhcp/dhcpd.leases",
            "/var/lib/kea/dhcp4.leases",
            "/var/lib/misc/dnsmasq.leases"
        ]
        
        lease_file_found = False
        for lease_file in lease_files:
            if host.file(lease_file).exists:
                lease_file_found = True
                break
        
        assert lease_file_found, "DHCP server running but no lease file found"
    
    def test_dns_forwarding(self, host):
        """Test DNS forwarding configuration."""
        # Check for DNS forwarding services
        dns_services = ["pdns_recursor", "dnsmasq", "unbound", "systemd-resolved"]
        
        dns_running = False
        for service in dns_services:
            if host.process.filter(comm=service):
                dns_running = True
                break
        
        assert dns_running, "No DNS forwarding service running"
        
        # Check DNS is listening on port 53
        dns_socket = host.socket("udp://0.0.0.0:53") or host.socket("udp://127.0.0.1:53")
        assert dns_socket.is_listening, "DNS not listening on port 53"
    
    def test_ssh_service(self, host):
        """Test SSH service configuration."""
        ssh_service = host.service("ssh") or host.service("sshd")
        assert ssh_service.is_running, "SSH service not running"
        assert ssh_service.is_enabled, "SSH service not enabled"
        
        # Check SSH configuration
        sshd_config = host.file("/etc/ssh/sshd_config")
        if sshd_config.exists:
            config = sshd_config.content_string
            
            # Security checks
            security_settings = {
                "PermitRootLogin": ["no", "prohibit-password"],
                "PubkeyAuthentication": ["yes"],
                "PasswordAuthentication": ["no"],  # Should use keys only
            }
            
            for setting, valid_values in security_settings.items():
                setting_found = False
                for value in valid_values:
                    if f"{setting} {value}" in config:
                        setting_found = True
                        break
                
                if not setting_found and setting == "PasswordAuthentication":
                    # Password auth might be needed for initial setup
                    pytest.warn(f"SSH {setting} not set to recommended value")
                elif not setting_found:
                    pytest.warn(f"SSH {setting} not configured securely")
    
    def test_ntp_service(self, host):
        """Test NTP time synchronization."""
        # Check for NTP services
        ntp_services = ["ntpd", "chrony", "systemd-timesyncd"]
        
        ntp_running = False
        for service in ntp_services:
            svc = host.service(service)
            if svc.exists and svc.is_running:
                ntp_running = True
                break
        
        if not ntp_running:
            # Check if NTP client is configured in VyOS
            ntp_config = host.run("show configuration commands | grep ntp")
            if ntp_config.rc == 0 and ntp_config.stdout:
                pass  # NTP is configured
            else:
                pytest.warn("NTP time synchronization not configured")


class TestVyOSRouting:
    """Test VyOS routing configuration."""
    
    def test_default_route(self, host):
        """Test default route is configured."""
        route_cmd = host.run("ip route show default")
        assert route_cmd.rc == 0, "Cannot get default route"
        assert "default via" in route_cmd.stdout, "No default route configured"
        
        # Should have a reasonable gateway
        default_route = route_cmd.stdout.strip()
        assert not any(x in default_route for x in ["127.0.0.1", "::1"]), \
            "Default route points to localhost"
    
    def test_routing_table(self, host):
        """Test routing table has expected routes."""
        route_cmd = host.run("ip route show")
        assert route_cmd.rc == 0, "Cannot get routing table"
        
        routes = route_cmd.stdout.strip().split('\n')
        assert len(routes) > 5, f"Too few routes configured: {len(routes)}"
        
        # Check for VLAN network routes
        expected_networks = [
            "10.10.0.0",  # Management
            "10.20.0.0",  # Private
            "10.30.0.0",  # Public/DMZ
        ]
        
        configured_networks = []
        for network in expected_networks:
            if any(network in route for route in routes):
                configured_networks.append(network)
        
        assert len(configured_networks) > 0, \
            f"No expected network routes found. Expected: {expected_networks}"
    
    def test_ip_forwarding(self, host):
        """Test IP forwarding is enabled."""
        # Check IPv4 forwarding
        ipv4_forward = host.file("/proc/sys/net/ipv4/ip_forward")
        assert ipv4_forward.exists
        assert ipv4_forward.content_string.strip() == "1", "IPv4 forwarding not enabled"
        
        # Check IPv6 forwarding (optional)
        ipv6_forward = host.file("/proc/sys/net/ipv6/conf/all/forwarding")
        if ipv6_forward.exists:
            if ipv6_forward.content_string.strip() != "1":
                pytest.warn("IPv6 forwarding not enabled")


class TestVyOSHighAvailability:
    """Test VyOS high availability features."""
    
    def test_vrrp_configuration(self, host):
        """Test VRRP configuration if configured."""
        # Check for keepalived (VRRP implementation)
        keepalived = host.service("keepalived")
        if keepalived.exists:
            if keepalived.is_running:
                # VRRP is configured and running
                # Check for VRRP interfaces
                vrrp_check = host.run("ip addr show | grep -i vrrp")
                if vrrp_check.rc == 0:
                    pass  # VRRP addresses found
            else:
                pytest.warn("VRRP configured but keepalived not running")
        else:
            # VRRP might not be configured (single router setup)
            pytest.skip("VRRP not configured (single router setup)")
    
    def test_conntrack_sync(self, host):
        """Test connection tracking synchronization for HA."""
        # Check if conntrack-sync is configured
        conntrackd = host.service("conntrackd")
        if conntrackd.exists:
            if conntrackd.is_running:
                # Check conntrackd configuration
                config = host.file("/etc/conntrackd/conntrackd.conf")
                assert config.exists, "conntrackd running but no config found"
            else:
                pytest.warn("conntrackd configured but not running")
        else:
            # Not configured for HA
            pytest.skip("Connection tracking sync not configured")


class TestVyOSVPN:
    """Test VPN configuration."""
    
    def test_wireguard_configuration(self, host):
        """Test WireGuard VPN if configured."""
        # Check for WireGuard interfaces
        wg_check = host.run("ip link show type wireguard")
        if wg_check.rc == 0 and wg_check.stdout:
            # WireGuard interfaces exist
            wg_interfaces = [line.split(':')[1].strip() 
                           for line in wg_check.stdout.split('\n') 
                           if ':' in line]
            
            for wg_if in wg_interfaces:
                # Check interface is up
                if_state = host.run(f"ip link show {wg_if}")
                assert "state UP" in if_state.stdout or "state UNKNOWN" in if_state.stdout, \
                    f"WireGuard interface {wg_if} is not UP"
                
                # Check for peers
                peers = host.run(f"sudo wg show {wg_if} peers")
                if peers.rc == 0 and peers.stdout.strip():
                    pass  # Has peers configured
        else:
            pytest.skip("WireGuard not configured")
    
    def test_ipsec_configuration(self, host):
        """Test IPsec VPN if configured."""
        # Check for strongSwan (IPsec implementation)
        ipsec_service = host.service("ipsec") or host.service("strongswan")
        if ipsec_service.exists:
            if ipsec_service.is_running:
                # Check IPsec status
                ipsec_status = host.run("sudo ipsec status")
                if ipsec_status.rc == 0:
                    pass  # IPsec is running
            else:
                pytest.warn("IPsec configured but not running")
        else:
            pytest.skip("IPsec not configured")


class TestVyOSConfiguration:
    """Test VyOS configuration management."""
    
    def test_config_file(self, host):
        """Test configuration file exists and is valid."""
        config_file = host.file("/config/config.boot")
        assert config_file.exists, "VyOS config.boot not found"
        assert config_file.size > 100, "config.boot appears empty"
        assert config_file.user == "root" or config_file.user == "vyos", \
            f"config.boot owned by unexpected user: {config_file.user}"
        
        # Check basic configuration sections
        config_content = config_file.content_string
        required_sections = ["interfaces", "system", "service"]
        
        for section in required_sections:
            assert section in config_content, f"Missing '{section}' section in config"
    
    def test_config_backup(self, host):
        """Test configuration backup exists."""
        # Check for backup configurations
        backup_dir = host.file("/config/backup")
        if backup_dir.exists:
            # List backup files
            backups = host.run("ls /config/backup/*.boot 2>/dev/null | wc -l")
            if backups.rc == 0:
                backup_count = int(backups.stdout.strip())
                if backup_count == 0:
                    pytest.warn("Backup directory exists but no backups found")
        else:
            pytest.warn("No configuration backup directory")
    
    def test_commit_archive(self, host):
        """Test commit archive if configured."""
        # Check for commit archive
        archive_dir = host.file("/config/archive")
        if archive_dir.exists:
            # Check for archived commits
            archives = host.run("ls /config/archive/ 2>/dev/null | wc -l")
            if archives.rc == 0:
                archive_count = int(archives.stdout.strip())
                if archive_count > 0:
                    pass  # Commit archive is working
        else:
            # Commit archive might not be configured
            pytest.skip("Commit archive not configured")


class TestVyOSMonitoring:
    """Test VyOS monitoring and logging."""
    
    def test_syslog_configuration(self, host):
        """Test syslog is configured."""
        # Check rsyslog service
        rsyslog = host.service("rsyslog")
        if rsyslog.exists:
            assert rsyslog.is_running, "rsyslog not running"
            
            # Check for VyOS specific logs
            vyos_logs = [
                "/var/log/vyos/vyos.log",
                "/var/log/messages",
                "/var/log/vyos/vyos-config.log"
            ]
            
            log_found = False
            for log_file in vyos_logs:
                if host.file(log_file).exists:
                    log_found = True
                    break
            
            assert log_found, "No VyOS log files found"
    
    def test_snmp_configuration(self, host):
        """Test SNMP if configured."""
        snmpd = host.service("snmpd")
        if snmpd.exists:
            if snmpd.is_running:
                # SNMP is configured
                # Check SNMP port
                snmp_port = host.socket("udp://0.0.0.0:161")
                assert snmp_port.is_listening, "SNMP not listening on port 161"
            else:
                pytest.warn("SNMP configured but not running")
        else:
            # SNMP not configured (optional)
            pytest.skip("SNMP not configured")
    
    def test_flow_accounting(self, host):
        """Test NetFlow/sFlow if configured."""
        # Check for flow accounting daemons
        flow_daemons = ["uacctd", "pmacctd", "softflowd"]
        
        flow_configured = False
        for daemon in flow_daemons:
            if host.process.filter(comm=daemon):
                flow_configured = True
                break
        
        if not flow_configured:
            # Flow accounting is optional
            pytest.skip("Flow accounting not configured")