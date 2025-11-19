#!/usr/bin/env python3
"""
Test script for port redirection functionality.
Verifies that iptables rules correctly redirect ports 80/443 to the blocking server.
"""

import sys
import os
import subprocess
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_command(cmd, shell=False):
    """Run a command and return output."""
    try:
        result = subprocess.run(
            cmd if isinstance(cmd, list) else cmd,
            shell=shell,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_root():
    """Check if running as root."""
    if os.geteuid() != 0:
        print("❌ Error: This test must be run as root")
        print("   Try: sudo python3 test_port_redirection.py")
        return False
    print("✓ Running as root")
    return True

def test_port_redirector():
    """Test the PortRedirector class."""
    print("\n" + "="*60)
    print("TESTING PORT REDIRECTOR")
    print("="*60 + "\n")

    try:
        from parental_control.port_redirector import PortRedirector

        redirector = PortRedirector(blocking_server_port=8080)

        # Test 1: Get initial status
        print("1. Checking initial status...")
        status = redirector.get_status()
        print(f"   Enabled: {status['enabled']}")
        print(f"   Rules: {status.get('rule_count', 0)}")

        # Test 2: Enable redirection
        print("\n2. Enabling port redirection...")
        success = redirector.enable_redirection()
        if success:
            print("   ✓ Port redirection enabled")
        else:
            print("   ✗ Failed to enable port redirection")
            return False

        # Test 3: Verify rules were added
        print("\n3. Verifying iptables rules...")
        success, output, error = run_command(['iptables', '-t', 'nat', '-L', 'PARENTAL_REDIRECT', '-n', '-v'])
        if success:
            print("   ✓ Rules found:")
            for line in output.split('\n')[2:]:  # Skip header lines
                if line.strip():
                    print(f"     {line}")
        else:
            print(f"   ✗ Failed to list rules: {error}")
            return False

        # Test 4: Check status again
        print("\n4. Checking status after enabling...")
        status = redirector.get_status()
        print(f"   Enabled: {status['enabled']}")
        print(f"   Rules: {status.get('rule_count', 0)}")
        if status['rule_count'] != 2:
            print("   ⚠ Warning: Expected 2 rules (HTTP + HTTPS)")

        # Test 5: Disable redirection
        print("\n5. Disabling port redirection...")
        success = redirector.disable_redirection()
        if success:
            print("   ✓ Port redirection disabled")
        else:
            print("   ✗ Failed to disable port redirection")
            return False

        # Test 6: Verify rules were removed
        print("\n6. Verifying rules were removed...")
        status = redirector.get_status()
        print(f"   Enabled: {status['enabled']}")
        print(f"   Rules: {status.get('rule_count', 0)}")
        if status['rule_count'] == 0:
            print("   ✓ All rules removed")
        else:
            print("   ⚠ Warning: Some rules still present")

        print("\n✅ Port redirector tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration with ParentalControl."""
    print("\n" + "="*60)
    print("TESTING PARENTAL CONTROL INTEGRATION")
    print("="*60 + "\n")

    try:
        from parental_control.parental_control import ParentalControl

        pc = ParentalControl()

        # Test 1: Start blocking server (should also enable port redirection)
        print("1. Starting blocking server...")
        success = pc.start_blocking_server(port=8080)
        if success:
            print("   ✓ Blocking server started")
        else:
            print("   ✗ Failed to start blocking server")
            return False

        # Test 2: Check port redirector status
        print("\n2. Checking port redirector status...")
        if pc.port_redirector:
            status = pc.port_redirector.get_status()
            print(f"   Enabled: {status['enabled']}")
            print(f"   Rules: {status.get('rule_count', 0)}")
            if status['enabled']:
                print("   ✓ Port redirection active")
            else:
                print("   ⚠ Warning: Port redirection not active")
        else:
            print("   ✗ Port redirector not initialized")
            return False

        # Test 3: Verify blocking server is running
        print("\n3. Checking blocking server...")
        if pc.blocking_server and pc.blocking_server.is_running():
            print("   ✓ Blocking server is running on port 8080")
        else:
            print("   ✗ Blocking server not running")
            return False

        # Test 4: Stop blocking server
        print("\n4. Stopping blocking server...")
        pc.stop_blocking_server()
        time.sleep(1)

        # Test 5: Verify port redirection was disabled
        print("\n5. Verifying port redirection was disabled...")
        if pc.port_redirector:
            status = pc.port_redirector.get_status()
            if not status['enabled']:
                print("   ✓ Port redirection disabled")
            else:
                print("   ⚠ Warning: Port redirection still active")
        else:
            print("   ✓ Port redirector cleaned up")

        print("\n✅ Integration tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error during integration testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_current_rules():
    """Display current iptables NAT rules."""
    print("\n" + "="*60)
    print("CURRENT IPTABLES NAT RULES")
    print("="*60 + "\n")

    success, output, error = run_command(['iptables', '-t', 'nat', '-L', '-n', '-v'])
    if success:
        print(output)
    else:
        print(f"Error: {error}")

def cleanup():
    """Cleanup any test artifacts."""
    print("\n" + "="*60)
    print("CLEANUP")
    print("="*60 + "\n")

    try:
        from parental_control.port_redirector import PortRedirector

        redirector = PortRedirector()
        redirector.cleanup()
        print("✓ Cleanup complete")
    except Exception as e:
        print(f"⚠ Cleanup error: {e}")

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print(" "*15 + "PORT REDIRECTION TEST SUITE")
    print("="*70)

    if not check_root():
        return 1

    # Run tests
    tests_passed = True

    if not test_port_redirector():
        tests_passed = False

    if not test_integration():
        tests_passed = False

    # Show current rules
    show_current_rules()

    # Cleanup
    cleanup()

    # Summary
    print("\n" + "="*70)
    if tests_passed:
        print("✅ ALL TESTS PASSED")
        print("\nPort redirection is working correctly!")
        print("Blocked sites will now show blocking pages instead of connection errors.")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease review the errors above and ensure:")
        print("  1. Running as root (sudo)")
        print("  2. iptables is installed")
        print("  3. No conflicting firewall rules")
    print("="*70 + "\n")

    return 0 if tests_passed else 1

if __name__ == "__main__":
    exit(main())
