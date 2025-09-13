"""
Helper functions and decorators for integration tests.
"""

import time
import functools
import pytest


def retry(max_attempts=3, delay=2, exceptions=(Exception,)):
    """
    Decorator to retry a test function on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay in seconds between attempts
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    else:
                        raise
            if last_exception:
                raise last_exception
        return wrapper
    return decorator


def check_command_output(host, command, timeout=None, expected_rc=0):
    """
    Execute a command and check its output with proper error handling.
    
    Args:
        host: Testinfra host object
        command: Command to execute
        timeout: Optional timeout for the command
        expected_rc: Expected return code (default: 0)
    
    Returns:
        Command result object
    
    Raises:
        AssertionError: If command fails or returns unexpected code
    """
    if timeout:
        result = host.run(f"timeout {timeout} {command}")
    else:
        result = host.run(command)
    
    if result.rc != expected_rc:
        error_msg = f"Command '{command}' failed with rc={result.rc}"
        if result.stderr:
            error_msg += f"\nStderr: {result.stderr}"
        if result.stdout:
            error_msg += f"\nStdout: {result.stdout}"
        raise AssertionError(error_msg)
    
    return result


def network_test(host, target_ip, test_type="ping", count=2, timeout=2):
    """
    Perform a network connectivity test.
    
    Args:
        host: Testinfra host object
        target_ip: IP address to test
        test_type: Type of test ("ping" or "curl")
        count: Number of ping attempts
        timeout: Timeout in seconds
    
    Returns:
        True if successful, False otherwise
    """
    if test_type == "ping":
        cmd = f"ping -c {count} -W {timeout} {target_ip}"
    elif test_type == "curl":
        cmd = f"curl --connect-timeout {timeout} -s -o /dev/null -w '%{{http_code}}' http://{target_ip}"
    else:
        raise ValueError(f"Unknown test type: {test_type}")
    
    result = host.run(cmd)
    
    if test_type == "ping":
        return result.rc == 0
    elif test_type == "curl":
        return result.rc == 0 and result.stdout.strip() in ["200", "301", "302"]
    
    return False


def assert_service_running(host, service_names, check_enabled=True):
    """
    Assert that at least one of the given services is running.
    
    Args:
        host: Testinfra host object
        service_names: List of possible service names
        check_enabled: Also check if service is enabled at boot
    
    Raises:
        AssertionError: If no service is running
    """
    if isinstance(service_names, str):
        service_names = [service_names]
    
    running_services = []
    for name in service_names:
        service = host.service(name)
        if service.exists and service.is_running:
            running_services.append(name)
            if check_enabled and not service.is_enabled:
                pytest.warn(f"Service {name} is running but not enabled at boot")
    
    assert running_services, f"None of these services are running: {service_names}"
    return running_services[0]


def validate_ip_in_subnet(ip_address, subnet):
    """
    Check if an IP address belongs to a given subnet.
    
    Args:
        ip_address: IP address string (e.g., "10.10.0.5")
        subnet: Subnet string (e.g., "10.10.0.0/16")
    
    Returns:
        True if IP is in subnet, False otherwise
    """
    import ipaddress
    try:
        ip = ipaddress.ip_address(ip_address)
        network = ipaddress.ip_network(subnet)
        return ip in network
    except (ValueError, TypeError):
        return False


def parse_config_value(config_string, key, delimiter="="):
    """
    Parse a configuration value from a string.
    
    Args:
        config_string: Configuration file content
        key: Key to search for
        delimiter: Delimiter between key and value
    
    Returns:
        Value if found, None otherwise
    """
    import re
    pattern = rf"{re.escape(key)}\s*{re.escape(delimiter)}\s*(.+)"
    match = re.search(pattern, config_string, re.MULTILINE)
    if match:
        return match.group(1).strip().strip('"').strip("'")
    return None