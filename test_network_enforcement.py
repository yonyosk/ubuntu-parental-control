#!/usr/bin/env python3
"""
Test script for network-level time restriction enforcement.
Tests that iptables rules correctly block internet access during restricted times.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parental_control.network_enforcer import NetworkEnforcer
from parental_control.database import ParentalControlDB
from parental_control.time_management import TimeManager


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def print_section(text):
    """Print a formatted section."""
    print(f"\n--- {text} ---")


def check_root():
    """Check if running as root."""
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root")
        print("Please run: sudo python3 test_network_enforcement.py")
        sys.exit(1)


def test_internet_connectivity():
    """Test if internet is currently accessible."""
    print_section("Testing Internet Connectivity")

    test_commands = [
        ("ping -c 1 -W 2 8.8.8.8", "Ping Google DNS"),
        ("curl -s --connect-timeout 3 http://www.google.com", "HTTP request to Google"),
    ]

    results = []
    for cmd, description in test_commands:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                timeout=5
            )
            success = result.returncode == 0
            results.append(success)
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{status}: {description}")
        except subprocess.TimeoutExpired:
            results.append(False)
            print(f"✗ TIMEOUT: {description}")
        except Exception as e:
            results.append(False)
            print(f"✗ ERROR: {description} - {e}")

    # Internet is accessible if at least one test passed
    internet_works = any(results)
    print(f"\nInternet Status: {'✓ ACCESSIBLE' if internet_works else '✗ BLOCKED'}")
    return internet_works


def test_network_enforcer():
    """Test the NetworkEnforcer class."""
    print_header("NETWORK ENFORCER TEST")

    enforcer = NetworkEnforcer()

    # Show current status
    print_section("Current Status")
    status = enforcer.get_status()
    print(f"Enforcement enabled: {status['enabled']}")
    print(f"Rules count: {status['rules_count']}")

    # Test internet before blocking
    print_section("BEFORE Blocking")
    before_internet = test_internet_connectivity()

    # Enable blocking
    print_section("Enabling Time Restriction")
    success = enforcer.enable_time_restriction("Test blocking")
    if success:
        print("✓ Time restriction enabled")
    else:
        print("✗ Failed to enable time restriction")
        return False

    # Show rules
    print_section("Iptables Rules")
    status = enforcer.get_status()
    print(status.get('output', 'No output'))

    # Test internet after blocking
    print_section("AFTER Blocking")
    after_internet = test_internet_connectivity()

    # Verify blocking worked
    print_section("Verification")
    if before_internet and not after_internet:
        print("✓ SUCCESS: Internet was accessible, now blocked")
        result = True
    elif not before_internet and not after_internet:
        print("⚠ WARNING: Internet was already blocked before test")
        result = True
    elif before_internet and after_internet:
        print("✗ FAILURE: Internet is still accessible after blocking")
        result = False
    else:
        print("? UNCLEAR: Internet was not accessible before blocking")
        result = False

    # Disable blocking
    print_section("Disabling Time Restriction")
    success = enforcer.disable_time_restriction()
    if success:
        print("✓ Time restriction disabled")
    else:
        print("✗ Failed to disable time restriction")

    # Test internet after unblocking
    print_section("AFTER Unblocking")
    final_internet = test_internet_connectivity()

    if final_internet:
        print("\n✓ Internet access restored successfully")
    else:
        print("\n⚠ WARNING: Internet still not accessible")

    return result


def test_time_enforcement_daemon():
    """Test the time enforcement daemon."""
    print_header("TIME ENFORCEMENT DAEMON TEST")

    print("NOTE: This is a quick test. For full testing, use the service.")
    print("The daemon will check time restrictions and enforce them.")

    from parental_control.time_enforcer import TimeEnforcementDaemon

    # Create daemon instance
    daemon = TimeEnforcementDaemon(check_interval=5)

    # Get current time restriction status
    db = ParentalControlDB()
    tm = TimeManager(db)
    is_allowed, reason = tm.is_access_allowed()

    print(f"\nCurrent time restriction status:")
    print(f"  Allowed: {is_allowed}")
    print(f"  Reason: {reason}")

    if is_allowed:
        print("\n⚠ Time is currently ALLOWED")
        print("  The daemon will NOT block internet right now")
        print("  To test blocking, add a schedule that excludes current time")
    else:
        print("\n✓ Time is currently RESTRICTED")
        print("  The daemon SHOULD block internet")

    print("\nTo run the daemon in the background:")
    print("  sudo systemctl start ubuntu-parental-control")
    print("\nOr run it manually (Ctrl+C to stop):")
    print("  sudo python3 -m parental_control.time_enforcer")


def main():
    """Main function."""
    check_root()

    print_header("NETWORK ENFORCEMENT TEST SUITE")
    print("This script tests network-level time restriction enforcement.")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test":
            test_network_enforcer()
        elif command == "daemon":
            test_time_enforcement_daemon()
        elif command == "cleanup":
            print_section("Cleanup")
            enforcer = NetworkEnforcer()
            success = enforcer.cleanup()
            if success:
                print("✓ Cleanup successful")
            else:
                print("✗ Cleanup failed")
        elif command == "status":
            enforcer = NetworkEnforcer()
            status = enforcer.get_status()
            print_section("Current Status")
            print(f"Enforcement enabled: {status['enabled']}")
            print(f"Rules count: {status['rules_count']}")
            if status.get('output'):
                print("\nIptables rules:")
                print(status['output'])
        else:
            print(f"Unknown command: {command}")
            print_usage()
    else:
        print_usage()


def print_usage():
    """Print usage information."""
    print("\nUsage:")
    print("  sudo python3 test_network_enforcement.py <command>")
    print("\nCommands:")
    print("  test     - Test network enforcement (block/unblock internet)")
    print("  daemon   - Test time enforcement daemon")
    print("  status   - Show current enforcement status")
    print("  cleanup  - Remove all enforcement rules")
    print("\nExamples:")
    print("  sudo python3 test_network_enforcement.py test")
    print("  sudo python3 test_network_enforcement.py status")


if __name__ == '__main__':
    main()
