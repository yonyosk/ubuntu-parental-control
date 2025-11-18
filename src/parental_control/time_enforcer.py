#!/usr/bin/env python3
"""
Time restriction enforcement daemon for Ubuntu Parental Control.
Monitors time restrictions and enforces them at the network level.
"""

import time
import logging
import signal
import sys
from pathlib import Path

from parental_control.database import ParentalControlDB
from parental_control.time_management import TimeManager
from parental_control.network_enforcer import NetworkEnforcer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ubuntu-parental/time_enforcer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TimeEnforcementDaemon:
    """
    Daemon that monitors time restrictions and enforces them using iptables.
    """

    def __init__(self, check_interval: int = 60):
        """
        Initialize the enforcement daemon.

        Args:
            check_interval: How often to check restrictions (seconds)
        """
        self.check_interval = check_interval
        self.db = ParentalControlDB()
        self.time_manager = TimeManager(self.db)
        self.network_enforcer = NetworkEnforcer()
        self.running = False
        self.current_blocked_state = None

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def start(self):
        """Start the enforcement daemon."""
        logger.info("=" * 60)
        logger.info("Time Restriction Enforcement Daemon Starting")
        logger.info("=" * 60)
        logger.info(f"Check interval: {self.check_interval} seconds")

        # Ensure log directory exists
        Path('/var/log/ubuntu-parental').mkdir(parents=True, exist_ok=True)

        # Initialize enforcement state
        self._check_and_enforce()

        self.running = True
        logger.info("Daemon started successfully")

        # Main loop
        try:
            while self.running:
                time.sleep(self.check_interval)
                self._check_and_enforce()

        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}", exc_info=True)
            self.stop()

    def stop(self):
        """Stop the daemon and clean up."""
        logger.info("Stopping enforcement daemon...")
        self.running = False

        # Remove all blocking rules when daemon stops
        # This ensures internet access is restored if service stops
        try:
            self.network_enforcer.disable_time_restriction()
            logger.info("Removed all time restriction rules")
        except Exception as e:
            logger.error(f"Error removing rules during shutdown: {e}")

        logger.info("Daemon stopped")
        sys.exit(0)

    def _check_and_enforce(self):
        """Check time restrictions and enforce via iptables."""
        try:
            # Get current access status
            is_allowed, reason = self.time_manager.is_access_allowed()

            # Determine if we should block
            should_block = not is_allowed

            # Log current status (only on state change to avoid spam)
            if self.current_blocked_state != should_block:
                if should_block:
                    logger.warning(f"Time restriction activated: {reason}")
                else:
                    logger.info(f"Time restriction lifted: {reason}")

            # Apply or remove blocking based on status
            if should_block:
                # Internet should be blocked
                if not self._is_currently_blocked():
                    logger.info("Applying network blocking rules...")
                    success = self.network_enforcer.enable_time_restriction(reason)
                    if success:
                        logger.info("✓ Internet access blocked")
                        self.current_blocked_state = True
                    else:
                        logger.error("✗ Failed to block internet access")
            else:
                # Internet should be allowed
                if self._is_currently_blocked():
                    logger.info("Removing network blocking rules...")
                    success = self.network_enforcer.disable_time_restriction()
                    if success:
                        logger.info("✓ Internet access restored")
                        self.current_blocked_state = False
                    else:
                        logger.error("✗ Failed to restore internet access")

        except Exception as e:
            logger.error(f"Error checking/enforcing time restrictions: {e}", exc_info=True)

    def _is_currently_blocked(self) -> bool:
        """
        Check if internet is currently blocked by our rules.

        Returns:
            True if blocked
        """
        try:
            return self.network_enforcer.is_internet_blocked()
        except Exception as e:
            logger.error(f"Error checking block status: {e}")
            return False

    def get_status(self) -> dict:
        """
        Get current daemon status.

        Returns:
            Dictionary with status information
        """
        is_allowed, reason = self.time_manager.is_access_allowed()
        network_status = self.network_enforcer.get_status()

        return {
            'running': self.running,
            'access_allowed': is_allowed,
            'reason': reason,
            'network_blocked': network_status.get('enabled', False),
            'rules_count': network_status.get('rules_count', 0),
            'check_interval': self.check_interval
        }


def main():
    """Main entry point."""
    # Check if running as root
    import os
    if os.geteuid() != 0:
        print("ERROR: This daemon must be run as root (requires iptables access)")
        sys.exit(1)

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Time Restriction Enforcement Daemon')
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up all rules and exit'
    )
    args = parser.parse_args()

    if args.cleanup:
        logger.info("Cleanup mode - removing all enforcement rules")
        enforcer = NetworkEnforcer()
        success = enforcer.cleanup()
        if success:
            logger.info("Cleanup successful")
            sys.exit(0)
        else:
            logger.error("Cleanup failed")
            sys.exit(1)

    # Start daemon
    daemon = TimeEnforcementDaemon(check_interval=args.interval)
    daemon.start()


if __name__ == '__main__':
    main()
