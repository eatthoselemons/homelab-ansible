#!/usr/bin/env python3
"""
Infrastructure validation framework for integration tests.
Provides a clean, maintainable way to write validation logic.
"""

import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.name} - {self.message}"


class RemoteHost:
    """Wrapper for executing commands on remote hosts via SSH."""
    
    def __init__(self, hostname: str, ansible_vars: Dict[str, str]):
        self.hostname = hostname
        self.ansible_host = ansible_vars.get('ansible_host', hostname)
        self.ansible_user = ansible_vars.get('ansible_user', 'vagrant')
        self.ansible_port = ansible_vars.get('ansible_port', '22')
        self.ansible_key = ansible_vars.get('ansible_ssh_private_key_file')
    
    def execute(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Execute command on remote host."""
        ssh_cmd = [
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-p', self.ansible_port,
        ]
        
        if self.ansible_key:
            ssh_cmd.extend(['-i', self.ansible_key])
        
        ssh_cmd.extend([
            f'{self.ansible_user}@{self.ansible_host}',
            command
        ])
        
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists on remote host."""
        code, _, _ = self.execute(f"test -e {path}")
        return code == 0
    
    def file_contains(self, path: str, content: str) -> bool:
        """Check if file contains specific content."""
        code, _, _ = self.execute(f"grep -q '{content}' {path}")
        return code == 0
    
    def service_is_running(self, service: str) -> bool:
        """Check if systemd service is running."""
        code, _, _ = self.execute(f"systemctl is-active {service}")
        return code == 0
    
    def service_is_enabled(self, service: str) -> bool:
        """Check if systemd service is enabled."""
        code, _, _ = self.execute(f"systemctl is-enabled {service}")
        return code == 0
    
    def interface_exists(self, interface: str) -> bool:
        """Check if network interface exists."""
        code, _, _ = self.execute(f"ip link show {interface}")
        return code == 0
    
    def interface_is_up(self, interface: str) -> bool:
        """Check if network interface is up."""
        code, stdout, _ = self.execute(f"ip link show {interface}")
        if code == 0:
            return 'state UP' in stdout
        return False
    
    def interface_has_ip(self, interface: str, ip: str) -> bool:
        """Check if interface has specific IP address."""
        code, stdout, _ = self.execute(f"ip addr show {interface}")
        if code == 0:
            return ip in stdout
        return False
    
    def can_ping(self, target: str, count: int = 3) -> bool:
        """Check if host can ping target."""
        code, _, _ = self.execute(f"ping -c {count} -W 2 {target}")
        return code == 0
    
    def port_is_listening(self, port: int, protocol: str = 'tcp') -> bool:
        """Check if port is listening."""
        code, stdout, _ = self.execute(f"ss -ln{protocol[0]} | grep -q ':{port}'")
        return code == 0
    
    def package_is_installed(self, package: str) -> bool:
        """Check if package is installed (supports apt/yum/dnf)."""
        # Try dpkg first (Debian/Ubuntu)
        code, _, _ = self.execute(f"dpkg -l {package} 2>/dev/null | grep -q '^ii'")
        if code == 0:
            return True
        
        # Try rpm (RHEL/CentOS/Fedora)
        code, _, _ = self.execute(f"rpm -q {package}")
        return code == 0
    
    def get_interface_ips(self, interface: str) -> List[str]:
        """Get all IP addresses for an interface."""
        code, stdout, _ = self.execute(f"ip -o addr show {interface} | awk '{{print $4}}'")
        if code == 0:
            return stdout.strip().split('\n')
        return []
    
    def get_interface_state(self, interface: str) -> Dict[str, Any]:
        """Get detailed interface state."""
        state = {
            'exists': self.interface_exists(interface),
            'is_up': False,
            'ips': [],
            'mtu': None,
            'mac': None
        }
        
        if state['exists']:
            state['is_up'] = self.interface_is_up(interface)
            state['ips'] = self.get_interface_ips(interface)
            
            # Get MTU
            code, stdout, _ = self.execute(f"cat /sys/class/net/{interface}/mtu 2>/dev/null")
            if code == 0:
                state['mtu'] = int(stdout.strip())
            
            # Get MAC address
            code, stdout, _ = self.execute(f"cat /sys/class/net/{interface}/address 2>/dev/null")
            if code == 0:
                state['mac'] = stdout.strip()
        
        return state


class BaseValidator(ABC):
    """Base class for all validators."""
    
    def __init__(self, inventory_file: str):
        self.inventory_file = inventory_file
        self.hosts = self._parse_inventory()
        self.results = []
    
    def _parse_inventory(self) -> Dict[str, RemoteHost]:
        """Parse Ansible inventory file."""
        hosts = {}
        current_host = None
        
        with open(self.inventory_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('['):
                    continue
                
                # Parse host line
                parts = line.split()
                if parts:
                    hostname = parts[0]
                    ansible_vars = {}
                    
                    # Parse ansible variables
                    for part in parts[1:]:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            ansible_vars[key] = value.strip('"\'')
                    
                    hosts[hostname] = RemoteHost(hostname, ansible_vars)
        
        return hosts
    
    def check(self, name: str, condition: bool, 
              success_msg: str = "Check passed",
              failure_msg: str = "Check failed",
              details: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Record a validation check result."""
        message = success_msg if condition else failure_msg
        result = ValidationResult(name, condition, message, details)
        self.results.append(result)
        logger.info(str(result))
        return result
    
    def check_all_hosts(self, check_func, *args, **kwargs):
        """Run a check function on all hosts."""
        for hostname, host in self.hosts.items():
            result = check_func(host, *args, **kwargs)
            self.check(
                f"{hostname}: {kwargs.get('name', check_func.__name__)}",
                result,
                success_msg=kwargs.get('success_msg', f"Check passed on {hostname}"),
                failure_msg=kwargs.get('failure_msg', f"Check failed on {hostname}")
            )
    
    @abstractmethod
    def validate(self) -> bool:
        """Run validation checks. Must be implemented by subclasses."""
        pass
    
    def run(self) -> bool:
        """Execute validation and return overall result."""
        logger.info(f"Starting validation for {self.__class__.__name__}")
        logger.info(f"Found {len(self.hosts)} hosts in inventory")
        
        try:
            self.validate()
        except Exception as e:
            logger.error(f"Validation error: {e}")
            self.check("Exception", False, failure_msg=str(e))
        
        # Print summary
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total checks: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if failed > 0:
            print("\nFailed checks:")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.name}: {result.message}")
        
        success = failed == 0
        if success:
            print("\n✅ ALL VALIDATION CHECKS PASSED")
        else:
            print("\n❌ VALIDATION FAILED")
        
        return success


class NetworkingValidator(BaseValidator):
    """Validator for networking configuration."""
    
    def validate(self) -> bool:
        """Validate networking setup."""
        
        # Check bond interface on all hosts
        for hostname, host in self.hosts.items():
            # Check bond0 exists and is up
            self.check(
                f"{hostname}: bond0 interface",
                host.interface_exists("bond0") and host.interface_is_up("bond0"),
                success_msg=f"bond0 is up on {hostname}",
                failure_msg=f"bond0 is not configured properly on {hostname}"
            )
            
            # Check VLAN interfaces
            for vlan in [10, 20, 30]:
                vlan_if = f"bond0.{vlan}"
                self.check(
                    f"{hostname}: VLAN {vlan}",
                    host.interface_exists(vlan_if),
                    success_msg=f"VLAN {vlan} interface exists",
                    failure_msg=f"VLAN {vlan} interface missing"
                )
            
            # Check connectivity to gateways
            gateways = {
                "Management": "10.10.0.1",
                "Private": "10.20.0.1",
                "Public": "10.30.0.1"
            }
            
            for network, gateway in gateways.items():
                self.check(
                    f"{hostname}: {network} gateway",
                    host.can_ping(gateway),
                    success_msg=f"Can reach {network} gateway ({gateway})",
                    failure_msg=f"Cannot reach {network} gateway ({gateway})"
                )
            
            # Check bridge configuration
            self.check(
                f"{hostname}: bridge-utils installed",
                host.package_is_installed("bridge-utils"),
                success_msg="bridge-utils package installed",
                failure_msg="bridge-utils package not installed"
            )
            
            # Check for network configuration files
            config_files = [
                "/etc/netplan/01-netcfg.yaml",
                "/etc/network/interfaces"
            ]
            
            has_config = any(host.file_exists(f) for f in config_files)
            self.check(
                f"{hostname}: network configuration",
                has_config,
                success_msg="Network configuration files present",
                failure_msg="No network configuration files found"
            )


class StorageValidator(BaseValidator):
    """Validator for storage configuration."""
    
    def validate(self) -> bool:
        """Validate storage setup."""
        
        for hostname, host in self.hosts.items():
            # Check LVM tools installed
            self.check(
                f"{hostname}: LVM tools",
                host.package_is_installed("lvm2"),
                success_msg="LVM2 package installed",
                failure_msg="LVM2 package not installed"
            )
            
            # Check volume groups
            code, stdout, _ = host.execute("vgs --noheadings -o vg_name")
            if code == 0 and stdout.strip():
                vgs = stdout.strip().split('\n')
                self.check(
                    f"{hostname}: volume groups",
                    len(vgs) > 0,
                    success_msg=f"Found {len(vgs)} volume group(s): {', '.join(vgs)}",
                    failure_msg="No volume groups found"
                )
            
            # Check mounted filesystems
            important_mounts = ["/", "/var", "/home"]
            for mount in important_mounts:
                code, stdout, _ = host.execute(f"mountpoint -q {mount}")
                self.check(
                    f"{hostname}: {mount} mounted",
                    code == 0,
                    success_msg=f"{mount} is mounted",
                    failure_msg=f"{mount} is not mounted"
                )
            
            # Check disk space
            code, stdout, _ = host.execute("df -h /")
            if code == 0:
                # Parse df output to check available space
                lines = stdout.strip().split('\n')
                if len(lines) > 1:
                    # Extract percentage used
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        used_percent = parts[4].rstrip('%')
                        try:
                            used = int(used_percent)
                            self.check(
                                f"{hostname}: root filesystem space",
                                used < 90,
                                success_msg=f"Root filesystem {used}% used",
                                failure_msg=f"Root filesystem critically full ({used}% used)"
                            )
                        except ValueError:
                            pass
            
            # Check for ZFS if expected
            code, _, _ = host.execute("which zfs")
            if code == 0:
                code, stdout, _ = host.execute("zpool list -H -o name")
                if code == 0 and stdout.strip():
                    pools = stdout.strip().split('\n')
                    self.check(
                        f"{hostname}: ZFS pools",
                        len(pools) > 0,
                        success_msg=f"Found {len(pools)} ZFS pool(s): {', '.join(pools)}",
                        failure_msg="No ZFS pools found"
                    )


class HarvesterValidator(BaseValidator):
    """Validator for Harvester cluster."""
    
    def validate(self) -> bool:
        """Validate Harvester setup."""
        
        for hostname, host in self.hosts.items():
            # Check if kubectl is available
            self.check(
                f"{hostname}: kubectl",
                host.execute("which kubectl")[0] == 0,
                success_msg="kubectl is installed",
                failure_msg="kubectl not found"
            )
            
            # Check Harvester services
            harvester_services = [
                "rke2-server",
                "rke2-agent",
                "harvester",
                "rancher"
            ]
            
            for service in harvester_services:
                if host.service_is_running(service):
                    self.check(
                        f"{hostname}: {service}",
                        True,
                        success_msg=f"{service} service is running"
                    )
                    break
            else:
                self.check(
                    f"{hostname}: Harvester services",
                    False,
                    failure_msg="No Harvester services running"
                )
            
            # Check cluster connectivity
            code, stdout, _ = host.execute("kubectl get nodes 2>/dev/null")
            self.check(
                f"{hostname}: cluster access",
                code == 0,
                success_msg="Can access Kubernetes cluster",
                failure_msg="Cannot access Kubernetes cluster"
            )
            
            if code == 0:
                # Check node status
                node_count = len([l for l in stdout.split('\n')[1:] if l.strip()])
                self.check(
                    f"{hostname}: cluster nodes",
                    node_count > 0,
                    success_msg=f"Cluster has {node_count} node(s)",
                    failure_msg="No nodes in cluster"
                )


class VyOSValidator(BaseValidator):
    """Validator for VyOS router configuration."""
    
    def validate(self) -> bool:
        """Validate VyOS setup."""
        
        for hostname, host in self.hosts.items():
            # Check if this is a VyOS system
            code, stdout, _ = host.execute("cat /etc/version 2>/dev/null")
            is_vyos = code == 0 and 'VyOS' in stdout
            
            if not is_vyos:
                # Try to check if it's a different router OS
                code, stdout, _ = host.execute("uname -a")
                self.check(
                    f"{hostname}: VyOS system",
                    False,
                    failure_msg=f"Not a VyOS system (detected: {stdout.strip()[:50]})"
                )
                continue
            
            self.check(
                f"{hostname}: VyOS system",
                True,
                success_msg=f"VyOS system detected: {stdout.strip()}"
            )
            
            # Check VyOS configuration mode access
            code, _, _ = host.execute("which vyos-cfg-cmd-wrapper")
            self.check(
                f"{hostname}: VyOS config tools",
                code == 0,
                success_msg="VyOS configuration tools available",
                failure_msg="VyOS configuration tools not found"
            )
            
            # Check network interfaces configured
            interfaces_to_check = ["eth0", "eth1"]  # WAN and LAN
            for iface in interfaces_to_check:
                self.check(
                    f"{hostname}: {iface} configured",
                    host.interface_exists(iface) and host.interface_is_up(iface),
                    success_msg=f"Interface {iface} is up",
                    failure_msg=f"Interface {iface} not configured"
                )
            
            # Check VLAN interfaces
            for vlan in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                vlan_if = f"eth1.{vlan}"
                if host.interface_exists(vlan_if):
                    self.check(
                        f"{hostname}: VLAN {vlan}",
                        True,
                        success_msg=f"VLAN {vlan} configured"
                    )
            
            # Check firewall is configured
            code, stdout, _ = host.execute("sudo iptables -L -n | head -20")
            has_rules = code == 0 and len(stdout.strip().split('\n')) > 10
            self.check(
                f"{hostname}: firewall rules",
                has_rules,
                success_msg="Firewall rules configured",
                failure_msg="No firewall rules found"
            )
            
            # Check NAT is configured
            code, stdout, _ = host.execute("sudo iptables -t nat -L -n | head -20")
            has_nat = code == 0 and 'MASQUERADE' in stdout
            self.check(
                f"{hostname}: NAT configuration",
                has_nat,
                success_msg="NAT/masquerade configured",
                failure_msg="NAT not configured"
            )
            
            # Check DHCP server
            code, _, _ = host.execute("ps aux | grep -q '[d]hcpd\\|[d]nsmasq'")
            self.check(
                f"{hostname}: DHCP server",
                code == 0,
                success_msg="DHCP server running",
                failure_msg="DHCP server not running"
            )
            
            # Check DNS forwarding
            code, _, _ = host.execute("ps aux | grep -q '[d]nsmasq\\|[p]dns\\|[u]nbound'")
            self.check(
                f"{hostname}: DNS forwarding",
                code == 0,
                success_msg="DNS forwarding service running",
                failure_msg="DNS forwarding not configured"
            )
            
            # Check routing table
            code, stdout, _ = host.execute("ip route show")
            if code == 0:
                has_default = 'default via' in stdout
                route_count = len(stdout.strip().split('\n'))
                self.check(
                    f"{hostname}: routing table",
                    has_default and route_count > 5,
                    success_msg=f"Routing configured ({route_count} routes)",
                    failure_msg="Routing table incomplete"
                )


# Validator registry
VALIDATORS = {
    'networking': NetworkingValidator,
    'storage': StorageValidator,
    'harvester': HarvesterValidator,
    'harvester_single': HarvesterValidator,
    'harvester_cluster': HarvesterValidator,
    'vyos': VyOSValidator,
    'vyos_config': VyOSValidator,
}


def main():
    """Main entry point for validation."""
    parser = argparse.ArgumentParser(description='Infrastructure validation framework')
    parser.add_argument('section', help='Test section to validate')
    parser.add_argument('inventory', help='Ansible inventory file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get validator class for section
    validator_class = VALIDATORS.get(args.section)
    if not validator_class:
        print(f"ERROR: No validator found for section '{args.section}'")
        print(f"Available sections: {', '.join(VALIDATORS.keys())}")
        sys.exit(1)
    
    # Run validation
    validator = validator_class(args.inventory)
    success = validator.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()