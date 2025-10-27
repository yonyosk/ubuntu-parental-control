"""
Safe, atomic hosts file management for Ubuntu Parental Control.
Prevents corruption of /etc/hosts and provides backup/restore functionality.
"""

import os
import shutil
import tempfile
import logging
import re
try:
    import fcntl
except ImportError:
    # Windows compatibility - fcntl is Unix-only
    fcntl = None
from datetime import datetime
from pathlib import Path
from typing import List, Set, Optional
import threading

logger = logging.getLogger(__name__)

class HostsFileManager:
    """
    Safe, atomic management of /etc/hosts file.
    Includes backup, validation, and corruption prevention.
    """
    
    def __init__(self, hosts_path: str = '/etc/hosts'):
        self.hosts_path = Path(hosts_path)
        self.backup_dir = Path('/var/lib/ubuntu-parental/backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        
        # Markers for our section in hosts file
        self.start_marker = "# Ubuntu Parental Control - START"
        self.end_marker = "# Ubuntu Parental Control - END"
        
        # Critical system entries that must never be removed
        self.system_entries = {
            '127.0.0.1': ['localhost', 'localhost.localdomain'],
            '::1': ['localhost', 'ip6-localhost', 'ip6-loopback'],
            'fe00::0': ['ip6-localnet'],
            'ff00::0': ['ip6-mcastprefix'],
            'ff02::1': ['ip6-allnodes'],
            'ff02::2': ['ip6-allrouters']
        }
    
    def backup_hosts_file(self) -> Optional[Path]:
        """Create a timestamped backup of the hosts file."""
        try:
            if not self.hosts_path.exists():
                logger.error(f"Hosts file does not exist: {self.hosts_path}")
                return None
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f"hosts_backup_{timestamp}"
            
            shutil.copy2(self.hosts_path, backup_path)
            logger.info(f"Created hosts file backup: {backup_path}")
            
            # Keep only last 10 backups
            self._cleanup_old_backups()
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to backup hosts file: {e}")
            return None
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Keep only the most recent backup files."""
        try:
            backup_files = sorted(
                [f for f in self.backup_dir.glob("hosts_backup_*")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove old backups
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            logger.warning(f"Error cleaning up old backups: {e}")
    
    def validate_hosts_content(self, content: str) -> bool:
        """Validate hosts file content to prevent corruption."""
        lines = content.strip().split('\n')
        
        # Check for required system entries
        has_localhost = False
        has_ipv6_localhost = False
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                ip, hostnames = parts[0], parts[1:]
                
                # Check for localhost entries
                if ip == '127.0.0.1' and 'localhost' in hostnames:
                    has_localhost = True
                if ip == '::1' and 'localhost' in hostnames:
                    has_ipv6_localhost = True
        
        if not has_localhost:
            logger.error("Validation failed: Missing 127.0.0.1 localhost entry")
            return False
            
        if not has_ipv6_localhost:
            logger.warning("Missing IPv6 localhost entry (not critical)")
        
        return True
    
    def read_hosts_file(self) -> Optional[str]:
        """Safely read the hosts file with file locking."""
        try:
            with open(self.hosts_path, 'r') as f:
                # Use advisory file locking if available (Unix only)
                if fcntl:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                content = f.read()
                if fcntl:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return content
        except Exception as e:
            logger.error(f"Error reading hosts file: {e}")
            return None
    
    def _extract_non_parental_lines(self, content: str) -> List[str]:
        """Extract all lines that are not managed by parental control."""
        lines = content.split('\n')
        result_lines = []
        in_parental_section = False
        
        for line in lines:
            # Check for our section markers
            if self.start_marker in line:
                in_parental_section = True
                continue
            elif self.end_marker in line:
                in_parental_section = False
                continue
            
            # Only keep lines outside our section
            if not in_parental_section:
                result_lines.append(line)
        
        # Ensure system entries are present
        self._ensure_system_entries(result_lines)
        
        return result_lines
    
    def _ensure_system_entries(self, lines: List[str]):
        """Ensure critical system entries are present."""
        existing_entries = set()
        
        # Parse existing entries
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[0]
                hostnames = parts[1:]
                existing_entries.add((ip, tuple(hostnames)))
        
        # Add missing system entries
        for ip, required_hostnames in self.system_entries.items():
            found = False
            for existing_ip, existing_hostnames in existing_entries:
                if existing_ip == ip and any(host in existing_hostnames for host in required_hostnames):
                    found = True
                    break
            
            if not found:
                entry_line = f"{ip}\t" + "\t".join(required_hostnames)
                lines.append(entry_line)
                logger.info(f"Added missing system entry: {entry_line}")
    
    def update_blocked_domains(self, domains: Set[str]) -> bool:
        """
        Update the hosts file with blocked domains using safe, atomic operations.
        
        Args:
            domains: Set of domain names to block
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Step 1: Create backup
                backup_path = self.backup_hosts_file()
                if not backup_path:
                    logger.error("Failed to create backup, aborting hosts file update")
                    return False
                
                # Step 2: Read current hosts file
                current_content = self.read_hosts_file()
                if current_content is None:
                    logger.error("Failed to read hosts file, aborting update")
                    return False
                
                # Step 3: Extract non-parental control lines
                preserved_lines = self._extract_non_parental_lines(current_content)
                
                # Step 4: Build new content
                new_lines = preserved_lines[:]
                
                # Add our section if we have domains to block
                if domains:
                    # Clean and validate domains
                    clean_domains = self._clean_domains(domains)
                    
                    new_lines.append("")  # Empty line before our section
                    new_lines.append(self.start_marker)
                    new_lines.append(f"# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    new_lines.append(f"# Blocking {len(clean_domains)} domains")
                    
                    # Add blocked domains (sorted for consistency)
                    for domain in sorted(clean_domains):
                        new_lines.append(f"127.0.0.1\t{domain}")
                    
                    new_lines.append(self.end_marker)
                    new_lines.append("")  # Empty line after our section
                
                # Step 5: Create new content and validate
                new_content = '\n'.join(new_lines)
                
                if not self.validate_hosts_content(new_content):
                    logger.error("New hosts content failed validation, aborting update")
                    return False
                
                # Step 6: Write atomically
                return self._write_hosts_file_atomic(new_content)
                
            except Exception as e:
                logger.error(f"Error updating blocked domains: {e}")
                return False
    
    def _clean_domains(self, domains: Set[str]) -> Set[str]:
        """Clean and validate domain names."""
        clean_domains = set()
        domain_pattern = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$')
        
        for domain in domains:
            domain = domain.strip().lower()
            
            # Skip empty or invalid domains
            if not domain or len(domain) > 253:
                continue
                
            # Skip localhost and system domains
            if domain in ['localhost', 'localhost.localdomain']:
                continue
            
            # Validate domain format
            if domain_pattern.match(domain):
                clean_domains.add(domain)
            else:
                logger.warning(f"Skipping invalid domain: {domain}")
        
        return clean_domains
    
    def _write_hosts_file_atomic(self, content: str) -> bool:
        """Write hosts file using atomic operations."""
        try:
            # Create temporary file in same filesystem for atomic move
            temp_dir = self.hosts_path.parent
            with tempfile.NamedTemporaryFile(mode='w', dir=temp_dir, delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            # Set correct permissions before moving
            os.chmod(tmp_path, 0o644)
            
            # Atomic move (this is the critical atomic operation)
            shutil.move(tmp_path, str(self.hosts_path))
            
            logger.info("Successfully updated hosts file")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write hosts file: {e}")
            
            # Clean up temporary file if it exists
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
            return False
    
    def restore_from_backup(self, backup_path: Optional[Path] = None) -> bool:
        """
        Restore hosts file from backup.
        
        Args:
            backup_path: Specific backup to restore from, or None for most recent
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                if backup_path is None:
                    # Find most recent backup
                    backup_files = sorted(
                        self.backup_dir.glob("hosts_backup_*"),
                        key=lambda x: x.stat().st_mtime,
                        reverse=True
                    )
                    
                    if not backup_files:
                        logger.error("No backup files found")
                        return False
                    
                    backup_path = backup_files[0]
                
                if not backup_path.exists():
                    logger.error(f"Backup file does not exist: {backup_path}")
                    return False
                
                # Validate backup content
                with open(backup_path, 'r') as f:
                    backup_content = f.read()
                
                if not self.validate_hosts_content(backup_content):
                    logger.error("Backup file failed validation")
                    return False
                
                # Restore using atomic operation
                return self._write_hosts_file_atomic(backup_content)
                
            except Exception as e:
                logger.error(f"Failed to restore from backup: {e}")
                return False
    
    def clear_blocked_domains(self) -> bool:
        """Remove all parental control entries from hosts file."""
        return self.update_blocked_domains(set())
    
    def get_current_blocked_domains(self) -> Set[str]:
        """Get currently blocked domains from hosts file."""
        try:
            content = self.read_hosts_file()
            if not content:
                return set()
            
            domains = set()
            lines = content.split('\n')
            in_parental_section = False
            
            for line in lines:
                if self.start_marker in line:
                    in_parental_section = True
                    continue
                elif self.end_marker in line:
                    in_parental_section = False
                    continue
                
                if in_parental_section:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2 and parts[0] == '127.0.0.1':
                            domains.add(parts[1])
            
            return domains
            
        except Exception as e:
            logger.error(f"Error getting current blocked domains: {e}")
            return set()