"""
Network services validation tests using testinfra.
Tests DHCP, DNS, NTP, and other network services.
"""

import pytest
import re


class TestDHCPServices:
    """Test DHCP client and server configurations."""
    
    def test_dhcp_client(self, host):
        """Test DHCP client configuration if used."""
        # Check for DHCP client
        dhcp_clients = ["dhclient", "dhcpcd", "systemd-networkd"]
        
        dhcp_found = False
        for client in dhcp_clients:
            if host.process.filter(comm=client):
                dhcp_found = True
                break
        
        if dhcp_found:
            # Check for DHCP lease
            lease_files = [
                "/var/lib/dhcp/dhclient.leases",
                "/var/lib/dhclient/dhclient.leases",
                "/var/lib/NetworkManager/dhclient*.lease"
            ]
            
            lease_found = False
            for lease_file in lease_files:
                if host.run(f"test -f {lease_file}").rc == 0:
                    lease_found = True
                    break
            
            if not lease_found:
                pytest.warn("DHCP client running but no lease file found")
    
    def test_dhcp_client_options(self, host):
        """Test DHCP client request options."""
        # Check dhclient configuration
        dhclient_conf = host.file("/etc/dhcp/dhclient.conf")
        if dhclient_conf.exists:
            config = dhclient_conf.content_string
            
            # Should request important options
            important_options = [
                "domain-name-servers",
                "domain-name",
                "domain-search",
                "host-name",
                "routers",
                "subnet-mask",
                "ntp-servers"
            ]
            
            requested = []
            for option in important_options:
                if option in config:
                    requested.append(option)
            
            if len(requested) < 3:
                pytest.warn("DHCP client not requesting all important options")
    
    def test_dhcp_reservation(self, host):
        """Test if host has DHCP reservation."""
        # Check current IP configuration
        ip_cmd = host.run("ip addr show | grep 'inet ' | grep -v '127.0.0.1' | head -1")
        if ip_cmd.rc == 0:
            # Parse IP address
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_cmd.stdout)
            if match:
                current_ip = match.group(1)
                
                # Check if this IP is from DHCP
                lease_files = [
                    "/var/lib/dhcp/dhclient.leases",
                    "/var/lib/dhclient/dhclient.leases"
                ]
                
                for lease_file in lease_files:
                    if host.file(lease_file).exists:
                        lease_content = host.file(lease_file).content_string
                        if current_ip in lease_content:
                            # IP is from DHCP
                            # Could check if it's always the same (reservation)
                            pass


class TestDNSServices:
    """Test DNS resolution and caching services."""
    
    def test_dns_resolver_configuration(self, host):
        """Test DNS resolver configuration."""
        resolv_conf = host.file("/etc/resolv.conf")
        assert resolv_conf.exists, "No /etc/resolv.conf file"
        
        content = resolv_conf.content_string
        
        # Should have nameservers
        nameservers = re.findall(r'nameserver\s+(\S+)', content)
        assert len(nameservers) > 0, "No nameservers configured"
        
        # Check for multiple nameservers (redundancy)
        if len(nameservers) < 2:
            pytest.warn("Only one nameserver configured, no redundancy")
        
        # Check for localhost nameserver (local caching)
        local_ns = ["127.0.0.1", "127.0.0.53", "::1"]
        has_local = any(ns in nameservers for ns in local_ns)
        
        if has_local:
            # Local DNS caching is configured
            pass
    
    def test_dns_caching_service(self, host):
        """Test for DNS caching service."""
        # Check for common DNS caching services
        dns_services = [
            "systemd-resolved",
            "dnsmasq",
            "unbound",
            "bind9",
            "named"
        ]
        
        caching_service = None
        for service in dns_services:
            svc = host.service(service)
            if svc.exists and svc.is_running:
                caching_service = service
                break
        
        if caching_service:
            # Verify it's listening on port 53
            dns_port = host.socket("udp://127.0.0.1:53") or \
                      host.socket("udp://127.0.0.53:53")
            
            if dns_port and dns_port.is_listening:
                pass  # DNS caching is working
            else:
                pytest.warn(f"{caching_service} running but not listening on port 53")
        else:
            pytest.warn("No DNS caching service running")
    
    def test_dns_performance(self, host):
        """Test DNS resolution performance."""
        # Test DNS response time
        dns_test = host.run("time nslookup google.com 2>&1 | grep real")
        if dns_test.rc == 0:
            # Parse time
            match = re.search(r'real\s+\d+m([\d.]+)s', dns_test.stdout)
            if match:
                response_time = float(match.group(1))
                
                # DNS should respond quickly
                if response_time > 1.0:
                    pytest.warn(f"Slow DNS response: {response_time}s")
    
    def test_dns_dnssec(self, host):
        """Test DNSSEC validation if configured."""
        # Check if DNSSEC validation is enabled
        # This depends on the DNS resolver being used
        
        # For systemd-resolved
        if host.service("systemd-resolved").exists:
            resolved_conf = host.file("/etc/systemd/resolved.conf")
            if resolved_conf.exists:
                if "DNSSEC=yes" in resolved_conf.content_string:
                    # DNSSEC is enabled
                    # Test DNSSEC validation
                    dnssec_test = host.run("dig +dnssec example.com")
                    if dnssec_test.rc == 0:
                        if "ad" in dnssec_test.stdout:
                            pass  # DNSSEC validation working
        
        # For unbound
        elif host.service("unbound").exists:
            unbound_conf = host.file("/etc/unbound/unbound.conf")
            if unbound_conf.exists:
                if "auto-trust-anchor-file" in unbound_conf.content_string:
                    pass  # DNSSEC likely configured


class TestNTPServices:
    """Test time synchronization services."""
    
    def test_ntp_service(self, host):
        """Test NTP service is running."""
        # Check for NTP services
        ntp_services = ["ntpd", "chrony", "systemd-timesyncd"]
        
        ntp_running = False
        ntp_service = None
        for service in ntp_services:
            svc = host.service(service)
            if svc.exists and svc.is_running:
                ntp_running = True
                ntp_service = service
                assert svc.is_enabled, f"{service} not enabled at boot"
                break
        
        assert ntp_running, "No NTP service running"
        return ntp_service
    
    def test_ntp_servers(self, host):
        """Test NTP server configuration."""
        # Check which NTP service is running
        ntp_service = None
        for service in ["ntpd", "chrony", "systemd-timesyncd"]:
            if host.service(service).is_running:
                ntp_service = service
                break
        
        if not ntp_service:
            pytest.skip("No NTP service running")
        
        # Check configuration based on service
        if ntp_service == "chrony":
            conf_file = host.file("/etc/chrony/chrony.conf")
            if conf_file.exists:
                config = conf_file.content_string
                servers = re.findall(r'server\s+(\S+)', config)
                assert len(servers) > 0, "No NTP servers configured"
                
                # Should have multiple servers
                if len(servers) < 3:
                    pytest.warn(f"Only {len(servers)} NTP servers configured")
        
        elif ntp_service == "systemd-timesyncd":
            conf_file = host.file("/etc/systemd/timesyncd.conf")
            if conf_file.exists:
                config = conf_file.content_string
                if "NTP=" in config:
                    # NTP servers configured
                    pass
        
        elif ntp_service == "ntpd":
            conf_file = host.file("/etc/ntp.conf")
            if conf_file.exists:
                config = conf_file.content_string
                servers = re.findall(r'server\s+(\S+)', config)
                assert len(servers) > 0, "No NTP servers configured"
    
    def test_time_synchronization(self, host):
        """Test that time is synchronized."""
        # Check time sync status
        timedatectl = host.run("timedatectl status")
        if timedatectl.rc == 0:
            output = timedatectl.stdout
            
            # Check NTP synchronized
            if "NTP synchronized: yes" in output or "System clock synchronized: yes" in output:
                pass  # Time is synchronized
            else:
                pytest.warn("System time not synchronized via NTP")
            
            # Check for time zone
            if "Time zone:" in output:
                # Extract timezone
                tz_match = re.search(r'Time zone:\s+(\S+)', output)
                if tz_match:
                    timezone = tz_match.group(1)
                    if timezone == "UTC":
                        pytest.warn("System using UTC, might want local timezone")
        else:
            # Fallback to ntpq or chronyc
            if host.run("which ntpq").rc == 0:
                ntp_status = host.run("ntpq -p")
                if ntp_status.rc == 0 and "*" in ntp_status.stdout:
                    pass  # At least one server is selected
            elif host.run("which chronyc").rc == 0:
                chrony_status = host.run("chronyc sources")
                if chrony_status.rc == 0 and "^*" in chrony_status.stdout:
                    pass  # At least one server is selected


class TestNetworkManager:
    """Test network management service."""
    
    def test_network_manager(self, host):
        """Test network management service."""
        # Check for network management service
        network_services = [
            "NetworkManager",
            "systemd-networkd",
            "networking"
        ]
        
        service_found = False
        for service in network_services:
            svc = host.service(service)
            if svc.exists and svc.is_running:
                service_found = True
                assert svc.is_enabled, f"{service} is not enabled"
                break
        
        assert service_found, "No network management service running"
    
    def test_network_configuration_files(self, host):
        """Test network configuration files exist."""
        # Check for network configuration
        config_locations = [
            "/etc/network/interfaces",
            "/etc/sysconfig/network-scripts/",
            "/etc/netplan/",
            "/etc/NetworkManager/system-connections/",
            "/etc/systemd/network/"
        ]
        
        config_found = False
        for location in config_locations:
            if host.file(location).exists:
                config_found = True
                break
        
        assert config_found, "No network configuration files found"
    
    def test_network_restart_capability(self, host):
        """Test network service can be restarted."""
        # Just check that network service exists and can be queried
        # Don't actually restart to avoid disrupting tests
        
        network_services = ["NetworkManager", "systemd-networkd", "networking"]
        
        for service in network_services:
            status_cmd = host.run(f"systemctl status {service} 2>/dev/null")
            if status_cmd.rc == 0:
                # Service exists and can be queried
                pass
                break


class TestMDNS:
    """Test mDNS/Avahi services."""
    
    def test_mdns_service(self, host):
        """Test if mDNS service is running."""
        # Check for Avahi daemon
        avahi = host.service("avahi-daemon")
        if avahi.exists:
            if avahi.is_running:
                # Check if listening on mDNS port
                mdns_port = host.socket("udp://0.0.0.0:5353")
                if mdns_port and mdns_port.is_listening:
                    pass  # mDNS is working
                else:
                    pytest.warn("Avahi running but not listening on port 5353")
            else:
                pytest.warn("Avahi installed but not running")
        else:
            # mDNS is optional
            pytest.skip("mDNS/Avahi not installed")
    
    def test_mdns_hostname(self, host):
        """Test mDNS hostname resolution."""
        if not host.service("avahi-daemon").is_running:
            pytest.skip("Avahi not running")
        
        # Get hostname
        hostname = host.run("hostname").stdout.strip()
        
        # Test .local resolution
        mdns_test = host.run(f"avahi-resolve -n {hostname}.local 2>/dev/null")
        if mdns_test.rc == 0:
            # mDNS resolution working
            pass
        else:
            pytest.warn("mDNS hostname resolution not working")


class TestSNMP:
    """Test SNMP service if configured."""
    
    def test_snmp_service(self, host):
        """Test SNMP daemon if installed."""
        snmpd = host.service("snmpd")
        if snmpd.exists:
            if snmpd.is_running:
                assert snmpd.is_enabled, "SNMP not enabled at boot"
                
                # Check if listening
                snmp_port = host.socket("udp://0.0.0.0:161")
                assert snmp_port.is_listening, "SNMP not listening on port 161"
            else:
                pytest.warn("SNMP installed but not running")
        else:
            pytest.skip("SNMP not installed")
    
    def test_snmp_configuration(self, host):
        """Test SNMP configuration security."""
        if not host.service("snmpd").exists:
            pytest.skip("SNMP not installed")
        
        snmp_conf = host.file("/etc/snmp/snmpd.conf")
        if snmp_conf.exists:
            config = snmp_conf.content_string
            
            # Check for default community strings
            if "public" in config:
                pytest.warn("Default 'public' community string found in SNMP config")
            if "private" in config:
                pytest.warn("Default 'private' community string found in SNMP config")
            
            # Check for SNMPv3 configuration
            if "createUser" in config or "usmUser" in config:
                pass  # SNMPv3 configured (more secure)
            else:
                pytest.warn("Consider using SNMPv3 for better security")