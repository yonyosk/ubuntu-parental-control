"""
Network enforcement module for Ubuntu Parental Control.
Uses iptables to enforce time restrictions at the network level.
"""

import subprocess
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class NetworkEnforcer:
    """
    Enforces parental control restrictions at the network level using iptables.
    """

    # Chain name for our rules
    CHAIN_NAME = "PARENTAL_CONTROL"

    def __init__(self):
        """Initialize the network enforcer."""
        self._ensure_chain_exists()

    def _run_iptables(self, args: List[str]) -> Tuple[bool, str]:
        """
        Run an iptables command.

        Args:
            args: List of arguments for iptables command

        Returns:
            Tuple of (success, output/error message)
        """
        try:
            cmd = ['iptables'] + args
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
        """Ensure our custom chain exists in the OUTPUT table."""
        # Create chain if it doesn't exist
        success, msg = self._run_iptables(['-N', self.CHAIN_NAME])
        if success:
            logger.debug(f"Chain {self.CHAIN_NAME} created or already exists")
        else:
            logger.error(f"Failed to create chain: {msg}")
            return

        # Check if our chain is referenced in OUTPUT
        success, output = self._run_iptables(['-C', 'OUTPUT', '-j', self.CHAIN_NAME])

        # If not referenced, add it
        if not success:
            success, msg = self._run_iptables(['-I', 'OUTPUT', '1', '-j', self.CHAIN_NAME])
            if success:
                logger.info(f"Added {self.CHAIN_NAME} to OUTPUT chain")
            else:
                logger.error(f"Failed to add chain to OUTPUT: {msg}")

    def enable_time_restriction(self, reason: str = "Time restriction active") -> bool:
        """
        Block all internet traffic (time restriction enforcement).

        Args:
            reason: Reason for blocking (logged)

        Returns:
            True if successful
        """
        logger.info(f"Enabling time restriction: {reason}")

        # First, clear any existing rules in our chain
        self._clear_rules()

        # Allow localhost traffic (lo interface)
        success, msg = self._run_iptables([
            '-A', self.CHAIN_NAME,
            '-o', 'lo',
            '-j', 'ACCEPT'
        ])
        if not success:
            logger.error(f"Failed to add localhost rule: {msg}")
            return False

        # Allow established connections to finish gracefully
        success, msg = self._run_iptables([
            '-A', self.CHAIN_NAME,
            '-m', 'state',
            '--state', 'ESTABLISHED,RELATED',
            '-j', 'ACCEPT'
        ])
        if not success:
            logger.error(f"Failed to add established connections rule: {msg}")

        # Allow local network (192.168.0.0/16, 172.16.0.0/12, 10.0.0.0/8)
        for network in ['192.168.0.0/16', '172.16.0.0/12', '10.0.0.0/8']:
            success, msg = self._run_iptables([
                '-A', self.CHAIN_NAME,
                '-d', network,
                '-j', 'ACCEPT'
            ])
            if not success:
                logger.warning(f"Failed to add local network rule for {network}: {msg}")

        # Allow DNS (so system doesn't break completely)
        for port in ['53']:
            success, msg = self._run_iptables([
                '-A', self.CHAIN_NAME,
                '-p', 'udp',
                '--dport', port,
                '-j', 'ACCEPT'
            ])
            if not success:
                logger.warning(f"Failed to add DNS rule: {msg}")

            success, msg = self._run_iptables([
                '-A', self.CHAIN_NAME,
                '-p', 'tcp',
                '--dport', port,
                '-j', 'ACCEPT'
            ])
            if not success:
                logger.warning(f"Failed to add DNS TCP rule: {msg}")

        # REJECT all other outbound traffic (this blocks internet)
        # Using REJECT instead of DROP to give immediate feedback
        success, msg = self._run_iptables([
            '-A', self.CHAIN_NAME,
            '-j', 'REJECT',
            '--reject-with', 'icmp-net-prohibited'
        ])
        if not success:
            logger.error(f"Failed to add reject rule: {msg}")
            return False

        logger.info("Time restriction enabled - internet access blocked")
        return True

    def disable_time_restriction(self) -> bool:
        """
        Remove time restriction (allow internet traffic).

        Returns:
            True if successful
        """
        logger.info("Disabling time restriction")

        # Clear all rules from our chain
        success = self._clear_rules()

        if success:
            logger.info("Time restriction disabled - internet access allowed")
        else:
            logger.error("Failed to disable time restriction")

        return success

    def _clear_rules(self) -> bool:
        """
        Clear all rules from our custom chain.

        Returns:
            True if successful
        """
        # Flush all rules in our chain
        success, msg = self._run_iptables(['-F', self.CHAIN_NAME])
        if not success:
            logger.error(f"Failed to flush chain: {msg}")
            return False

        return True

    def get_status(self) -> dict:
        """
        Get current enforcement status.

        Returns:
            Dictionary with status information
        """
        # List rules in our chain
        success, output = self._run_iptables(['-L', self.CHAIN_NAME, '-n', '-v'])

        if not success:
            return {
                'enabled': False,
                'error': output,
                'rules_count': 0
            }

        # Count rules (excluding chain header lines)
        lines = output.strip().split('\n')
        # Skip the 2 header lines
        rule_lines = [line for line in lines[2:] if line.strip()]
        rules_count = len(rule_lines)

        # If we have rules (other than just the chain itself), restriction is enabled
        # We expect: localhost, established, local networks, DNS, and REJECT = multiple rules
        enabled = rules_count > 0

        return {
            'enabled': enabled,
            'rules_count': rules_count,
            'output': output
        }

    def cleanup(self) -> bool:
        """
        Remove all parental control rules and chains.
        Should be called during uninstallation.

        Returns:
            True if successful
        """
        logger.info("Cleaning up network enforcement rules")

        # Remove reference from OUTPUT chain
        success, msg = self._run_iptables(['-D', 'OUTPUT', '-j', self.CHAIN_NAME])
        if not success and "does a matching rule exist" not in msg:
            logger.warning(f"Failed to remove chain from OUTPUT: {msg}")

        # Flush our chain
        success, msg = self._run_iptables(['-F', self.CHAIN_NAME])
        if not success:
            logger.warning(f"Failed to flush chain: {msg}")

        # Delete our chain
        success, msg = self._run_iptables(['-X', self.CHAIN_NAME])
        if not success:
            logger.warning(f"Failed to delete chain: {msg}")
            return False

        logger.info("Network enforcement cleanup complete")
        return True

    def is_internet_blocked(self) -> bool:
        """
        Check if internet is currently blocked by our rules.

        Returns:
            True if internet is blocked
        """
        status = self.get_status()
        return status.get('enabled', False)
