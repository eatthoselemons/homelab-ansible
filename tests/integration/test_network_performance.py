"""
Network performance and optimization validation tests using testinfra.
Tests MTU, bonding, buffers, and other performance-related configurations.
"""

import pytest
import re


class TestNetworkBonding:
    """Test network bonding/LAG configuration."""
    
    def test_bond_interface_exists(self, host):
        """Test that bond0 interface exists and is configured."""
        bond = host.interface("bond0")
        
        if not bond.exists:
            # Bonding might not be configured on all hosts
            pytest.skip("No bond interface configured")
        
        # Check bond is up
        bond_status = host.run("ip link show bond0")
        assert bond_status.rc == 0, "Cannot get bond0 status"
        assert "state UP" in bond_status.stdout, "bond0 is not UP"
    
    def test_bond_slaves(self, host):
        """Test bond has slave interfaces."""
        if not host.interface("bond0").exists:
            pytest.skip("No bond interface configured")
        
        # Check bonding mode and slaves
        bonding_file = host.file("/proc/net/bonding/bond0")
        if bonding_file.exists:
            content = bonding_file.content_string
            
            # Check for bonding mode
            assert "Bonding Mode:" in content, "No bonding mode information"
            
            # Common bonding modes
            acceptable_modes = [
                "load balancing (round-robin)",
                "fault-tolerance (active-backup)",
                "IEEE 802.3ad Dynamic link aggregation",
                "transmit load balancing",
                "adaptive load balancing"
            ]
            
            mode_found = any(mode in content for mode in acceptable_modes)
            assert mode_found, "Unknown or invalid bonding mode"
            
            # Check for slave interfaces
            slaves = re.findall(r'Slave Interface: (\S+)', content)
            assert len(slaves) >= 2, f"Bond should have at least 2 slaves, found: {slaves}"
            
            # Check slave status
            for slave in slaves:
                assert f"MII Status: up" in content, f"Slave {slave} is not up"
    
    def test_bond_redundancy(self, host):
        """Test bond redundancy configuration."""
        if not host.interface("bond0").exists:
            pytest.skip("No bond interface configured")
        
        bonding_file = host.file("/proc/net/bonding/bond0")
        if bonding_file.exists:
            content = bonding_file.content_string
            
            # Check MII monitoring is enabled
            if "MII Polling Interval" in content:
                match = re.search(r'MII Polling Interval \(ms\): (\d+)', content)
                if match:
                    interval = int(match.group(1))
                    assert interval > 0 and interval <= 1000, \
                        f"MII polling interval {interval}ms is not optimal"
    
    def test_bond_performance(self, host):
        """Test bond performance settings."""
        if not host.interface("bond0").exists:
            pytest.skip("No bond interface configured")
        
        # Check bond transmit hash policy for 802.3ad
        bonding_file = host.file("/proc/net/bonding/bond0")
        if bonding_file.exists:
            content = bonding_file.content_string
            
            if "802.3ad" in content:
                # For 802.3ad, check hash policy
                if "Transmit Hash Policy:" in content:
                    # layer3+4 is generally best for most workloads
                    if "layer3+4" not in content and "layer2+3" not in content:
                        pytest.warn("Bond hash policy may not be optimal for performance")
    
    def test_bond_failover(self, host):
        """Test bond failover configuration."""
        if not host.interface("bond0").exists:
            pytest.skip("No bond interface configured")
        
        bonding_file = host.file("/proc/net/bonding/bond0")
        if bonding_file.exists:
            content = bonding_file.content_string
            
            # Check primary slave configuration for active-backup
            if "active-backup" in content:
                if "Primary Slave:" in content:
                    match = re.search(r'Primary Slave: (\S+)', content)
                    if match and match.group(1) != "None":
                        # Primary slave is configured
                        pass
                    else:
                        pytest.warn("No primary slave configured for active-backup bond")


class TestNetworkPerformance:
    """Test network performance and MTU settings."""
    
    def test_mtu_configuration(self, host):
        """Test MTU settings on network interfaces."""
        # Check main interfaces
        interfaces_to_check = ["bond0", "eth0", "eth1", "enp1s0", "ens3"]
        
        for iface in interfaces_to_check:
            if host.interface(iface).exists:
                mtu_cmd = host.run(f"cat /sys/class/net/{iface}/mtu")
                if mtu_cmd.rc == 0:
                    mtu = int(mtu_cmd.stdout.strip())
                    
                    # Standard MTU is 1500, Jumbo frames are 9000
                    assert mtu >= 1500, f"MTU on {iface} is too small: {mtu}"
                    
                    if mtu > 1500:
                        # Jumbo frames configured
                        assert mtu <= 9000, f"MTU on {iface} is unusually large: {mtu}"
                        pytest.warn(f"Jumbo frames enabled on {iface}: MTU={mtu}")
    
    def test_mtu_consistency(self, host):
        """Test MTU consistency across VLAN interfaces."""
        # Get base interface
        base_interface = None
        for iface in ["bond0", "eth0", "eth1"]:
            if host.interface(iface).exists:
                base_interface = iface
                break
        
        if not base_interface:
            pytest.skip("No base interface found")
        
        # Get base MTU
        base_mtu_cmd = host.run(f"cat /sys/class/net/{base_interface}/mtu")
        if base_mtu_cmd.rc == 0:
            base_mtu = int(base_mtu_cmd.stdout.strip())
            
            # Check VLAN interfaces have same or smaller MTU
            vlan_interfaces = host.run(f"ls /sys/class/net/ | grep '{base_interface}\\.'").stdout.split()
            
            for vlan_if in vlan_interfaces:
                vlan_mtu_cmd = host.run(f"cat /sys/class/net/{vlan_if.strip()}/mtu")
                if vlan_mtu_cmd.rc == 0:
                    vlan_mtu = int(vlan_mtu_cmd.stdout.strip())
                    assert vlan_mtu <= base_mtu, \
                        f"VLAN {vlan_if} MTU ({vlan_mtu}) larger than base ({base_mtu})"
    
    def test_network_buffers(self, host):
        """Test network buffer settings."""
        # Check for optimized network buffers
        buffer_settings = [
            "/proc/sys/net/core/rmem_max",
            "/proc/sys/net/core/wmem_max",
            "/proc/sys/net/ipv4/tcp_rmem",
            "/proc/sys/net/ipv4/tcp_wmem"
        ]
        
        for setting in buffer_settings:
            if host.file(setting).exists:
                value = host.file(setting).content_string.strip()
                # Just verify they're readable, actual values depend on use case
                assert value, f"Network buffer setting {setting} is empty"
    
    def test_network_queue_settings(self, host):
        """Test network queue optimization."""
        # Check netdev_max_backlog
        backlog_file = host.file("/proc/sys/net/core/netdev_max_backlog")
        if backlog_file.exists:
            backlog = int(backlog_file.content_string.strip())
            
            # Default is usually 1000, should be higher for performance
            if backlog < 5000:
                pytest.warn(f"netdev_max_backlog ({backlog}) may be too low for optimal performance")
    
    def test_interrupt_coalescing(self, host):
        """Test interrupt coalescing settings."""
        # Check main interfaces for interrupt coalescing
        interfaces = ["bond0", "eth0", "eth1"]
        
        for iface in interfaces:
            if host.interface(iface).exists:
                # Check ethtool coalescing settings
                coal_cmd = host.run(f"ethtool -c {iface} 2>/dev/null")
                if coal_cmd.rc == 0:
                    # Just verify we can get coalescing info
                    if "Coalesce parameters" in coal_cmd.stdout:
                        pass  # Coalescing info available
    
    def test_tcp_congestion_control(self, host):
        """Test TCP congestion control algorithm."""
        # Check current congestion control
        cc_file = host.file("/proc/sys/net/ipv4/tcp_congestion_control")
        if cc_file.exists:
            cc_algo = cc_file.content_string.strip()
            
            # Modern algorithms for better performance
            modern_algos = ["bbr", "cubic", "htcp"]
            
            if cc_algo not in modern_algos:
                pytest.warn(f"TCP congestion control '{cc_algo}' may not be optimal")
    
    def test_tcp_optimization(self, host):
        """Test TCP optimization settings."""
        tcp_settings = {
            "/proc/sys/net/ipv4/tcp_fastopen": "3",  # Enable TCP Fast Open
            "/proc/sys/net/ipv4/tcp_tw_reuse": "1",  # Reuse TIME_WAIT sockets
            "/proc/sys/net/ipv4/tcp_fin_timeout": None,  # Should be < 60
        }
        
        for setting, expected in tcp_settings.items():
            if host.file(setting).exists:
                value = host.file(setting).content_string.strip()
                
                if setting.endswith("fin_timeout"):
                    timeout = int(value)
                    if timeout > 60:
                        pytest.warn(f"TCP FIN timeout ({timeout}s) may be too high")
                elif expected and value != expected:
                    pytest.warn(f"{setting} is {value}, recommended: {expected}")


class TestNetworkOffloading:
    """Test network offloading features."""
    
    def test_checksum_offloading(self, host):
        """Test checksum offloading is enabled."""
        interfaces = ["bond0", "eth0", "eth1"]
        
        for iface in interfaces:
            if host.interface(iface).exists:
                # Check offloading features
                features_cmd = host.run(f"ethtool -k {iface} 2>/dev/null | grep -E 'rx-checksumming|tx-checksumming'")
                if features_cmd.rc == 0:
                    # Check if checksumming is on
                    if "on" not in features_cmd.stdout:
                        pytest.warn(f"Checksum offloading may be disabled on {iface}")
    
    def test_tso_gso_offloading(self, host):
        """Test TSO/GSO offloading."""
        interfaces = ["bond0", "eth0", "eth1"]
        
        for iface in interfaces:
            if host.interface(iface).exists:
                # Check TSO/GSO
                features_cmd = host.run(f"ethtool -k {iface} 2>/dev/null | grep -E 'tcp-segmentation-offload|generic-segmentation-offload'")
                if features_cmd.rc == 0:
                    # These should generally be enabled for performance
                    if "off" in features_cmd.stdout:
                        pytest.warn(f"TSO/GSO may be disabled on {iface}")
    
    def test_receive_packet_steering(self, host):
        """Test Receive Packet Steering (RPS) configuration."""
        interfaces = ["bond0", "eth0", "eth1"]
        
        for iface in interfaces:
            if host.interface(iface).exists:
                # Check RPS configuration
                rps_file = f"/sys/class/net/{iface}/queues/rx-0/rps_cpus"
                if host.file(rps_file).exists:
                    rps_cpus = host.file(rps_file).content_string.strip()
                    
                    # If RPS is disabled, value will be 00000000
                    if rps_cpus == "00000000" or rps_cpus == "0":
                        pytest.warn(f"RPS not configured on {iface}")


class TestNetworkLatency:
    """Test network latency optimization."""
    
    def test_local_latency(self, host):
        """Test local network latency."""
        # Test latency to router
        ping_cmd = host.run("ping -c 10 -i 0.2 10.10.0.1 2>/dev/null | tail -1")
        if ping_cmd.rc == 0 and "avg" in ping_cmd.stdout:
            # Parse average latency
            match = re.search(r'min/avg/max/mdev = [\d.]+/([\d.]+)/', ping_cmd.stdout)
            if match:
                avg_latency = float(match.group(1))
                
                # Local network should be < 5ms
                if avg_latency > 5.0:
                    pytest.warn(f"High local network latency: {avg_latency}ms")
    
    def test_interrupt_affinity(self, host):
        """Test network interrupt CPU affinity."""
        # Check if irqbalance is running
        irqbalance = host.service("irqbalance")
        if irqbalance.exists:
            if not irqbalance.is_running:
                pytest.warn("irqbalance not running, may affect network performance")
        else:
            # Check manual IRQ affinity
            irq_files = host.run("ls /proc/irq/*/smp_affinity 2>/dev/null").stdout.split()
            if irq_files:
                # Just verify IRQ affinity files exist
                pass