"""
Port Redirector for Ubuntu Parental Control.
Redirects HTTP/HTTPS traffic from blocked domains to the blocking server.
"""

import subprocess
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class PortRedirector:
    """
    Redirects port 80 and 443 traffic to the blocking server using iptables NAT.
    This ensures users see friendly blocking pages instead of connection errors.
    """

    # Chain name for our NAT rules
    CHAIN_NAME = "PARENTAL_REDIRECT"

    def __init__(self, blocking_server_port: int = 8080):
        """
        Initialize the port redirector.

        Args:
            blocking_server_port: Port where the blocking server is running (default: 8080)
        """
        self.blocking_server_port = blocking_server_port
        self._ensure_chain_exists()

    def _run_iptables(self, args: List[str], table: str = 'nat') -> Tuple[bool, str]:
        """
        Run an iptables command.

        Args:
            args: List of arguments for iptables command
            table: iptables table to use (default: 'nat')

        Returns:
            Tuple of (success, output/error message)
        """
        try:
            cmd = ['iptables', '-t', table] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                # Check if error is because rule already exists (not a real error)
                if "already exists" in result.stderr or "does a matching rule exist" in result.stderr:
                    return True, result.stderr
                return False, result.stderr

        except Exception as e:
            logger.error(f"Error running iptables: {e}")
            return False, str(e)

    def _ensure_chain_exists(self):
        """Ensure our custom chain exists in the nat OUTPUT table."""
        # Create chain if it doesn't exist
        success, msg = self._run_iptables(['-N', self.CHAIN_NAME], table='nat')
        if success:
            logger.debug(f"Chain {self.CHAIN_NAME} created or already exists in nat table")
        else:
            logger.error(f"Failed to create chain: {msg}")
            return

        # Check if our chain is referenced in OUTPUT
        success, output = self._run_iptables(['-C', 'OUTPUT', '-j', self.CHAIN_NAME], table='nat')

        # If not referenced, add it
        if not success:
            success, msg = self._run_iptables(['-I', 'OUTPUT', '1', '-j', self.CHAIN_NAME], table='nat')
            if success:
                logger.info(f"Added {self.CHAIN_NAME} to OUTPUT chain in nat table")
            else:
                logger.error(f"Failed to add chain to OUTPUT: {msg}")

    def enable_redirection(self) -> bool:
        """
        Enable port redirection from 80/443 to blocking server port.

        This redirects HTTP (port 80) and HTTPS (port 443) traffic destined for
        127.0.0.1 (blocked domains) to the blocking server.

        Returns:
            True if successful
        """
        logger.info(f"Enabling port redirection to blocking server on port {self.blocking_server_port}")

        # First, clear any existing rules in our chain
        self._clear_rules()

        # Redirect HTTP (port 80) to blocking server
        success, msg = self._run_iptables([
            '-A', self.CHAIN_NAME,
            '-p', 'tcp',
            '-d', '127.0.0.1',
            '--dport', '80',
            '-j', 'REDIRECT',
            '--to-port', str(self.blocking_server_port)
        ], table='nat')

        if not success:
            logger.error(f"Failed to add HTTP redirect rule: {msg}")
            return False

        logger.info(f"HTTP (port 80) redirected to port {self.blocking_server_port}")

        # Redirect HTTPS (port 443) to blocking server
        success, msg = self._run_iptables([
            '-A', self.CHAIN_NAME,
            '-p', 'tcp',
            '-d', '127.0.0.1',
            '--dport', '443',
            '-j', 'REDIRECT',
            '--to-port', str(self.blocking_server_port)
        ], table='nat')

        if not success:
            logger.error(f"Failed to add HTTPS redirect rule: {msg}")
            return False

        logger.info(f"HTTPS (port 443) redirected to port {self.blocking_server_port}")
        logger.info("Port redirection enabled - blocked domains will show blocking pages")
        return True

    def disable_redirection(self) -> bool:
        """
        Remove port redirection rules.

        Returns:
            True if successful
        """
        logger.info("Disabling port redirection")

        # Clear all rules from our chain
        success = self._clear_rules()

        if success:
            logger.info("Port redirection disabled")
        else:
            logger.error("Failed to disable port redirection")

        return success

    def _clear_rules(self) -> bool:
        """
        Clear all rules from our custom chain.

        Returns:
            True if successful
        """
        # Flush the chain
        success, msg = self._run_iptables(['-F', self.CHAIN_NAME], table='nat')

        if not success:
            logger.error(f"Failed to flush chain: {msg}")
            return False

        logger.debug(f"Cleared all rules from {self.CHAIN_NAME}")
        return True

    def get_status(self) -> dict:
        """
        Get the current status of port redirection.

        Returns:
            Dictionary with status information
        """
        # Check if our chain has rules
        success, output = self._run_iptables(['-L', self.CHAIN_NAME, '-n', '-v'], table='nat')

        if not success:
            return {
                'enabled': False,
                'error': 'Failed to check status',
                'details': output
            }

        # Count rules (excluding chain header lines)
        lines = output.strip().split('\n')
        rule_count = len([line for line in lines if line and not line.startswith('Chain') and not line.startswith('pkts')])

        return {
            'enabled': rule_count > 0,
            'rule_count': rule_count,
            'blocking_server_port': self.blocking_server_port,
            'details': output
        }

    def cleanup(self) -> bool:
        """
        Complete cleanup of all port redirection rules.
        Call this when uninstalling the parental control system.

        Returns:
            True if successful
        """
        logger.info("Cleaning up port redirection system...")

        # Clear all rules from our chain
        self._clear_rules()

        # Remove chain from OUTPUT
        success, msg = self._run_iptables(['-D', 'OUTPUT', '-j', self.CHAIN_NAME], table='nat')
        if not success and "does a matching rule exist" not in msg:
            logger.warning(f"Failed to remove chain from OUTPUT: {msg}")

        # Delete the chain
        success, msg = self._run_iptables(['-X', self.CHAIN_NAME], table='nat')
        if not success and "does a matching rule exist" not in msg:
            logger.warning(f"Failed to delete chain: {msg}")
        else:
            logger.info("Port redirection cleanup complete")

        return True


def test_redirection():
    """Test function to verify port redirection setup."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    redirector = PortRedirector(blocking_server_port=8080)

    print("\n=== Port Redirector Test ===\n")

    # Get initial status
    print("1. Initial status:")
    status = redirector.get_status()
    print(f"   Enabled: {status['enabled']}")
    print(f"   Rules: {status.get('rule_count', 0)}")

    # Enable redirection
    print("\n2. Enabling port redirection...")
    success = redirector.enable_redirection()
    if success:
        print("   ✓ Port redirection enabled")
    else:
        print("   ✗ Failed to enable port redirection")
        return False

    # Check status
    print("\n3. Status after enabling:")
    status = redirector.get_status()
    print(f"   Enabled: {status['enabled']}")
    print(f"   Rules: {status.get('rule_count', 0)}")
    print(f"   Blocking server port: {status.get('blocking_server_port')}")

    # Show rules
    print("\n4. Current NAT rules:")
    print(status['details'])

    # Disable redirection
    print("\n5. Disabling port redirection...")
    success = redirector.disable_redirection()
    if success:
        print("   ✓ Port redirection disabled")
    else:
        print("   ✗ Failed to disable port redirection")

    # Final status
    print("\n6. Final status:")
    status = redirector.get_status()
    print(f"   Enabled: {status['enabled']}")
    print(f"   Rules: {status.get('rule_count', 0)}")

    print("\n=== Test Complete ===\n")
    return True


if __name__ == "__main__":
    import os

    # Check if running as root
    if os.geteuid() != 0:
        print("Error: This script must be run as root (iptables requires root privileges)")
        print("Try: sudo python3 port_redirector.py")
        exit(1)

    test_redirection()
