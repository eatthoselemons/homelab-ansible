#!/usr/bin/env python3
"""
Runner script for integration tests using pytest and testinfra.
This provides a clean interface to run infrastructure validation tests.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def setup_environment():
    """Ensure test environment is ready."""
    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Check for required packages
    try:
        import pytest
        import testinfra
    except ImportError:
        print("ERROR: Required packages not installed")
        print("Please run: pip install -r tests/requirements.txt")
        sys.exit(1)


def run_tests(args):
    """Run the integration tests."""
    pytest_args = [
        "pytest",
        "-v",  # Verbose output
        "--tb=short",  # Shorter traceback format
    ]
    
    # Add test directory
    test_dir = Path(__file__).parent / "integration"
    
    # Select specific test files based on section
    if args.section:
        test_file = test_dir / f"test_{args.section}.py"
        if test_file.exists():
            pytest_args.append(str(test_file))
        else:
            print(f"ERROR: No tests found for section '{args.section}'")
            print(f"Available sections: networking, storage, vyos, harvester")
            sys.exit(1)
    else:
        pytest_args.append(str(test_dir))
    
    # Add inventory file
    if args.inventory:
        pytest_args.extend(["--inventory", args.inventory])
    
    # Add parallel execution if requested
    if args.parallel:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # Add HTML report if requested
    if args.html_report:
        pytest_args.extend(["--html", args.html_report, "--self-contained-html"])
    
    # Add timeout
    if args.timeout:
        pytest_args.extend(["--timeout", str(args.timeout)])
    
    # Add markers/tags
    if args.mark:
        pytest_args.extend(["-m", args.mark])
    
    # Show test output
    if args.capture_no:
        pytest_args.append("-s")
    
    # Run only failed tests from last run
    if args.lf:
        pytest_args.append("--lf")
    
    # Stop on first failure
    if args.exitfirst:
        pytest_args.append("-x")
    
    # Run pytest
    print(f"Running: {' '.join(pytest_args)}")
    result = subprocess.run(pytest_args)
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run integration tests for homelab infrastructure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  %(prog)s --inventory tests/inventory/test.ini
  
  # Run specific section
  %(prog)s --section networking --inventory tests/inventory/test.ini
  
  # Run tests in parallel
  %(prog)s --parallel 4 --inventory tests/inventory/test.ini
  
  # Generate HTML report
  %(prog)s --html-report test-report.html --inventory tests/inventory/test.ini
  
  # Run with timeout per test
  %(prog)s --timeout 60 --inventory tests/inventory/test.ini
  
Available test sections:
  - networking: Network interfaces, VLANs, connectivity
  - storage: LVM, filesystems, mounts
  - vyos: Router configuration, firewall, NAT
  - harvester: Kubernetes cluster, services
        """
    )
    
    parser.add_argument(
        "--section", "-s",
        help="Test section to run (networking, storage, vyos, harvester)"
    )
    parser.add_argument(
        "--inventory", "-i",
        help="Path to Ansible inventory file",
        default="tests/inventory/test.ini"
    )
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        metavar="NUM",
        help="Run tests in parallel with NUM workers"
    )
    parser.add_argument(
        "--html-report",
        help="Generate HTML test report"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout per test in seconds"
    )
    parser.add_argument(
        "--mark", "-m",
        help="Run tests matching given mark expression"
    )
    parser.add_argument(
        "--capture-no",
        action="store_true",
        help="Don't capture test output (show print statements)"
    )
    parser.add_argument(
        "--lf", "--last-failed",
        action="store_true",
        help="Run only tests that failed in the last run"
    )
    parser.add_argument(
        "-x", "--exitfirst",
        action="store_true",
        help="Stop on first test failure"
    )
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="List available tests without running them"
    )
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    if args.list_tests:
        # List available tests
        pytest_args = ["pytest", "--collect-only", "-q"]
        test_dir = Path(__file__).parent / "integration"
        pytest_args.append(str(test_dir))
        subprocess.run(pytest_args)
        return 0
    
    # Run tests
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())