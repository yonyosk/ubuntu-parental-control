import subprocess
from pathlib import Path
import os
import sys
import logging
import hashlib
import datetime
import time
from typing import List, Dict, Tuple, Optional, Set, Any

# Set up logger
logger = logging.getLogger(__name__)

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from .database import ParentalControlDB
    from .blacklist_manager import BlacklistManager
    from .category_manager import CategoryManager
    from .time_management import TimeManager
    from .activity_logger import ActivityLogger
    from .hosts_manager import HostsFileManager
    from .port_redirector import PortRedirector
except ImportError:
    from parental_control.database import ParentalControlDB
    from parental_control.blacklist_manager import BlacklistManager
    from parental_control.category_manager import CategoryManager
    from parental_control.time_management import TimeManager
    from parental_control.activity_logger import ActivityLogger
    from parental_control.hosts_manager import HostsFileManager
    from parental_control.port_redirector import PortRedirector

class WebsiteCategory:
    SOCIAL_MEDIA = {
        'facebook.com': ['www.facebook.com', 'm.facebook.com', 'fb.com'],
        'instagram.com': ['www.instagram.com'],
        'twitter.com': ['www.twitter.com', 'x.com'],
        'tiktok.com': ['www.tiktok.com'],
        'snapchat.com': ['www.snapchat.com']
    }
    
    GAMING = {
        'roblox.com': ['www.roblox.com', 'web.roblox.com'],
        'minecraft.net': ['www.minecraft.net'],
        'epicgames.com': ['www.epicgames.com'],
        'steampowered.com': ['www.steampowered.com', 'store.steampowered.com'],
        'discord.com': ['www.discord.com', 'discord.gg']
    }
    
    VIDEO = {
        'youtube.com': ['www.youtube.com', 'youtu.be', 'm.youtube.com'],
        'twitch.tv': ['www.twitch.tv'],
        'vimeo.com': ['www.vimeo.com'],
        'dailymotion.com': ['www.dailymotion.com']
    }

class ParentalControl:
    def __init__(self):
        self.db_path = Path('/var/lib/ubuntu-parental/control.json')
        self._ensure_database_directory()

        # Initialize new database layer
        self.db = ParentalControlDB(str(self.db_path))

        # Initialize managers with new database
        self.blacklist_manager = BlacklistManager(self.db)
        self.category_manager = CategoryManager(self.db, self.blacklist_manager)
        self.time_manager = TimeManager(self.db)
        self.activity_logger = ActivityLogger(self.db)
        self.hosts_manager = HostsFileManager()

        # Initialize blocking server and port redirector
        self.blocking_server = None
        self.port_redirector = None
    
    def _ensure_database_directory(self):
        """Ensure database directory exists with proper permissions."""
        try:
            # Create directory
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Set proper permissions (readable/writable by owner, readable by group)
            import stat
            import os
            
            dir_path = str(self.db_path.parent)
            
            # Set directory permissions: owner rwx, group r-x, others ---
            os.chmod(dir_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
            
            # If database file exists, set its permissions too
            if self.db_path.exists():
                os.chmod(str(self.db_path), stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
                
            logging.info(f"Database directory permissions set: {dir_path}")
            
        except Exception as e:
            logging.error(f"Error setting database directory permissions: {e}")
            # Don't fail completely - let the database creation attempt proceed
            pass

    # Database setup is now handled by ParentalControlDB class
    
    def is_protection_active(self) -> bool:
        """Check if parental control protection is currently active."""
        try:
            settings = self.db.get_settings()
            return settings.get('protection_active', True)
        except Exception as e:
            logging.error(f"Error checking protection status: {e}")
            return True  # Default to active for safety
    
    def set_protection_active(self, active: bool) -> bool:
        """Enable or disable parental control protection."""
        try:
            return self.db.update_settings(protection_active=active)
        except Exception as e:
            logging.error(f"Error setting protection status: {e}")
            return False

    def verify_password(self, password: str) -> bool:
        """Verify the admin password."""
        if not password:
            return False
            
        try:
            # Get stored password hash from database
            settings = self.db.get_settings()
            stored_hash = settings.get('password_hash')
            
            # If no password is set, DENY access - force setup through web interface
            if not stored_hash:
                logging.error("No password configured - access denied")
                return False
            
            # Hash the provided password and compare
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            is_valid = password_hash == stored_hash
            
            if is_valid:
                logging.info("Password verification successful")
            else:
                logging.warning("Password verification failed")
            
            return is_valid
            
        except Exception as e:
            logging.error(f"Error verifying password: {e}")
            return False

    def set_password(self, new_password: str) -> bool:
        """Set the admin password."""
        if not new_password or len(new_password) < 4:
            logging.error("Password must be at least 4 characters")
            return False
            
        try:
            # Hash the password
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            # Store in database
            success = self.db.update_settings(password_hash=password_hash)
            
            if success:
                logging.info("Admin password updated successfully")
            else:
                logging.error("Failed to update password in database")
                
            return success
            
        except Exception as e:
            logging.error(f"Error setting password: {e}")
            return False
    
    def has_password_set(self) -> bool:
        """Check if admin password is configured."""
        try:
            settings = self.db.get_settings()
            return bool(settings.get('password_hash'))
        except Exception as e:
            logging.error(f"Error checking password status: {e}")
            # Don't assume no password on database errors - this prevents
            # accidental first-time setup mode when there are permission issues
            raise Exception(f"Database access error: {e}")

    def block_category(self, category_dict: Dict[str, List[str]]):
        """Block all domains in a category"""
        for main_domain in category_dict.keys():
            self.add_blocked_site(main_domain)

    def _detect_category(self, domain: str) -> str:
        """Detect category of a domain"""
        all_categories = {
            'SOCIAL_MEDIA': WebsiteCategory.SOCIAL_MEDIA,
            'GAMING': WebsiteCategory.GAMING,
            'VIDEO': WebsiteCategory.VIDEO
        }
        
        for category_name, domains in all_categories.items():
            if domain in domains:
                return category_name
        return "OTHER"

    def add_blocked_site(self, domain: str):
        """Add a site to the blocked list"""
        category = self._detect_category(domain)
        if self.db.add_blocked_site(domain, category):
            return self._update_hosts_file()
        return False

    def get_blocked_domains(self) -> List[str]:
        """Get all blocked domains from database and blacklists."""
        # Get manually blocked sites
        blocked_sites = self.db.get_blocked_sites()
        domains = [site['domain'] for site in blocked_sites]

        # Get domains from active UT1 blacklist categories
        blacklist_domains = self.db.get_blacklist_domains()
        domains.extend(blacklist_domains)

        # Get domains from active built-in categories
        active_categories = self.db.get_blacklist_categories(active_only=True)
        for category in active_categories:
            if category.get('source') == 'built-in':
                category_id = category['name']
                if category_id in self.category_manager.BUILTIN_CATEGORIES:
                    builtin_domains = self.category_manager.BUILTIN_CATEGORIES[category_id]['domains']
                    domains.extend(builtin_domains)

        return list(set(domains))  # Remove duplicates
    
    def get_blocked_categories(self) -> List[str]:
        """Get list of blocked categories."""
        try:
            categories = self.db.get_blacklist_categories(active_only=True)
            return [cat['name'] for cat in categories]
        except Exception as e:
            logging.error(f"Error getting blocked categories: {e}")
            return []
    
    def get_blocked_sites(self) -> List[Dict]:
        """Get list of manually blocked sites."""
        try:
            return self.db.get_blocked_sites()
        except Exception as e:
            logging.error(f"Error getting blocked sites: {e}")
            return []
    
    def _update_hosts_file(self) -> bool:
        """Update the hosts file with all blocked domains using safe atomic operations."""
        try:
            blocked_domains = self.get_blocked_domains()
            domains_set = set(blocked_domains) if blocked_domains else set()
            
            success = self.hosts_manager.update_blocked_domains(domains_set)
            
            if success:
                logger.info(f"Successfully updated hosts file with {len(domains_set)} blocked domains")
            else:
                logger.error("Failed to update hosts file")
                
            return success
            
        except Exception as e:
            logger.error(f"Error updating hosts file: {e}")
            return False

    def temporarily_unblock(self, domain: str, duration_minutes: int, password: str) -> bool:
        """Temporarily unblock a site with parent password"""
        # Password verification is disabled for now
        # if hashlib.sha256(password.encode()).hexdigest() != self.password_hash:
        #     return False
        
        expiry = datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)
        if self.db.add_temporary_exception(domain, expiry.isoformat()):
            self._remove_domain_block(domain)
            return True
        return False

    def _remove_domain_block(self, domain: str):
        """Remove domain from hosts file"""
        subprocess.run([
            'sed', '-i', f'/{domain}/d', '/etc/hosts'
        ])
    
    # Blacklist Management Methods
    
    def block_categories_from_blacklist(self, category_names: List[str]) -> Dict[str, int]:
        """
        Block domains from multiple blacklist categories in a single operation.
        
        Args:
            category_names: List of blacklist category names to block
            
        Returns:
            Dictionary mapping category names to the number of domains blocked
        """
        results = {}
        
        for category in category_names:
            domains = self.blacklist_manager.get_blocked_domains(category)
            if domains:
                # Add domains directly to the database (bulk operation)
                count = 0
                for domain in domains:
                    if self.db.add_blocked_site(domain, category):
                        count += 1
                results[category] = count
                logging.info(f"Blocked {count} domains from category: {category}")
            else:
                results[category] = 0
                logging.warning(f"No domains found for category: {category}")
        
        # Update hosts file once after all categories are processed
        if any(count > 0 for count in results.values()):
            success = self._update_hosts_file()
            if not success:
                logging.error("Failed to update hosts file after blocking categories")
        
        return results

    def update_blacklist(self, category: str) -> Tuple[bool, int]:
        """
        Update a blacklist category.
        
        Args:
            category: The category to update
            
        Returns:
            Tuple of (success, num_domains) where success is a boolean indicating
            if the update was successful, and num_domains is the number of domains
            added or updated.
        """
        return self.blacklist_manager.update_blacklist(category)
    
    def update_all_blacklists(self) -> Dict[str, int]:
        """
        Update all active blacklist categories.
        
        Returns:
            Dictionary mapping category names to the number of domains updated
        """
        return self.blacklist_manager.update_all_blacklists()
    
    def get_available_blacklist_categories(self) -> List[Dict[str, str]]:
        """
        Get a list of all available blacklist categories.
        
        Returns:
            List of dictionaries with category information
        """
        return self.blacklist_manager.get_available_categories()
    
    def get_active_blacklist_categories(self) -> List[Dict[str, Any]]:
        """
        Get all active blacklist categories.
        
        Returns:
            List of dictionaries with active category information
        """
        return self.db.get_blacklist_categories(active_only=True)
    
    def set_blacklist_categories(self, categories: List[str]) -> bool:
        """
        Set which blacklist categories are active.
        
        Args:
            categories: List of category names to activate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.db.set_blacklist_categories(categories)
        except Exception as e:
            logging.error(f"Error updating blacklist categories: {e}")
            return False
    
    def is_access_allowed(self, domain: str = None, client_ip: str = None, 
                         user_agent: str = None) -> Tuple[bool, str]:
        """
        Check if internet access is allowed based on all restrictions.
        
        Args:
            domain: Optional domain to check against blacklists
            client_ip: IP address of the client making the request
            user_agent: User agent string of the client
            
        Returns:
            Tuple of (is_allowed, reason) where reason explains the decision
        """
        # Check time-based restrictions first
        time_allowed, time_reason = self.time_manager.is_access_allowed()
        if not time_allowed:
            # Log the blocked access attempt
            if domain:
                self.activity_logger.log_activity(
                    domain=domain,
                    action='blocked',
                    category='time_restriction',
                    client_ip=client_ip,
                    user_agent=user_agent,
                    reason=time_reason
                )
            return False, time_reason
            
        # Check domain against blacklists if provided
        if domain:
            # Check manually blocked sites first
            if self.db.is_site_blocked(domain):
                reason = "Blocked by manual site blocking"
                # Log the blocked access attempt
                self.activity_logger.log_activity(
                    domain=domain,
                    action='blocked',
                    category='manual_block',
                    client_ip=client_ip,
                    user_agent=user_agent,
                    reason=reason
                )
                return False, reason
            
            # Check blacklist categories
            is_blocked, categories = self.blacklist_manager.is_domain_blocked(domain)
            if is_blocked:
                reason = f"Blocked by categories: {', '.join(categories)}"
                # Log the blocked access attempt
                self.activity_logger.log_activity(
                    domain=domain,
                    action='blocked',
                    category=','.join(categories) if categories else 'blacklist',
                    client_ip=client_ip,
                    user_agent=user_agent,
                    reason=reason
                )
                return False, reason
        
        # Log allowed access
        if domain:
            self.activity_logger.log_activity(
                domain=domain,
                action='allowed',
                client_ip=client_ip,
                user_agent=user_agent
            )
            
            # Record usage time (1 minute per request as a simple approximation)
            self.activity_logger.record_usage_time(minutes=1)
        
        return True, "Access allowed"
    
    def start_blocking_server(self, port=8080, https_port=8443, use_https=True):
        """Start the blocking server for friendly block pages"""
        try:
            from .blocking_server import BlockingServer

            if self.blocking_server and self.blocking_server.is_running():
                logger.info("Blocking server already running")
                return True

            # Start the blocking server with HTTP and HTTPS support
            self.blocking_server = BlockingServer(self, port=port, https_port=https_port, use_https=use_https)
            success = self.blocking_server.start()

            if success:
                logger.info(f"Blocking server started on HTTP port {port}")
                if use_https:
                    logger.info(f"Blocking server started on HTTPS port {https_port}")

                # Update hosts file to redirect blocked domains to 127.0.0.1
                self.update_hosts_for_blocking_server(port)

                # Enable port redirection (80 -> 8080, 443 -> 8443) using iptables
                if not self.port_redirector:
                    self.port_redirector = PortRedirector(blocking_server_port=port)

                redirect_success = self.port_redirector.enable_redirection()
                if redirect_success:
                    logger.info(f"Port redirection enabled (80 -> {port}, 443 -> {https_port})")
                else:
                    logger.warning("Failed to enable port redirection - blocked pages may not display")

            return success

        except Exception as e:
            logger.error(f"Failed to start blocking server: {e}")
            return False
    
    def stop_blocking_server(self):
        """Stop the blocking server and disable port redirection"""
        if self.blocking_server:
            self.blocking_server.stop()
            self.blocking_server = None
            logger.info("Blocking server stopped")

        # Disable port redirection
        if self.port_redirector:
            self.port_redirector.disable_redirection()
            logger.info("Port redirection disabled")
    
    def update_hosts_for_blocking_server(self, port=8080):
        """Update hosts file to redirect blocked domains to blocking server"""
        try:
            # Get blocked domains
            blocked_domains = self.get_blocked_domains()
            domains_set = set(blocked_domains) if blocked_domains else set()
            
            # Use the safe hosts manager to update with blocking server redirect
            # This would need to be extended in HostsFileManager to support custom IPs
            success = self.hosts_manager.update_blocked_domains(domains_set)
            
            if success:
                logger.info(f"Updated hosts file for blocking server on port {port}")
            else:
                logger.error("Failed to update hosts file for blocking server")
                
            return success
            
        except Exception as e:
            logger.error(f"Error updating hosts file for blocking server: {e}")
            return False
        
    def is_domain_blocked(self, domain: str) -> Tuple[bool, List[str]]:
        """
        Check if a domain is blocked by manual blocking or any active blacklist.
        
        Args:
            domain: The domain to check (e.g., 'example.com')
            
        Returns:
            Tuple of (is_blocked, categories) where is_blocked is a boolean
            indicating if the domain is blocked, and categories is a list of
            category names that block this domain.
        """
        # Check manual blocking first (with subdomain support)
        domain_lower = domain.lower().strip()
        
        # Check exact match first
        if self.db.is_site_blocked(domain_lower):
            blocked_sites = self.db.get_blocked_sites()
            manual_site = next((site for site in blocked_sites if site.get('domain') == domain_lower), None)
            category = manual_site.get('category', 'MANUAL') if manual_site else 'MANUAL'
            return True, [category]
        
        # Check if any parent domain is manually blocked
        # e.g., www.youtube.com -> youtube.com -> com
        parts = domain_lower.split('.')
        for i in range(1, len(parts)):
            parent_domain = '.'.join(parts[i:])
            if self.db.is_site_blocked(parent_domain):
                blocked_sites = self.db.get_blocked_sites()
                manual_site = next((site for site in blocked_sites if site.get('domain') == parent_domain), None)
                category = manual_site.get('category', 'MANUAL') if manual_site else 'MANUAL'
                return True, [category]

        # Check built-in categories
        active_categories = self.db.get_blacklist_categories(active_only=True)
        for category in active_categories:
            if category.get('source') == 'built-in':
                category_id = category['name']
                if category_id in self.category_manager.BUILTIN_CATEGORIES:
                    builtin_domains = self.category_manager.BUILTIN_CATEGORIES[category_id]['domains']
                    # Check if domain or any parent domain matches
                    if domain_lower in builtin_domains:
                        return True, [category.get('display_name', category_id)]
                    # Check parent domains
                    for i in range(1, len(parts)):
                        parent_domain = '.'.join(parts[i:])
                        if parent_domain in builtin_domains:
                            return True, [category.get('display_name', category_id)]

        # Check UT1 blacklist categories
        return self.blacklist_manager.is_domain_blocked(domain_lower)
        
    def get_dns_settings(self):
        """Get current DNS settings from system and database"""
        try:
            # Get database settings as fallback
            db_settings = self.db.get_dns_settings()
            
            # Try to read actual system DNS settings
            system_dns = self._get_system_dns_settings()
            
            # Merge system and database settings
            if system_dns:
                # Update database with actual system settings
                result = {
                    'dns_type': system_dns.get('dns_type', db_settings.get('dns_type', 'system')),
                    'primary_dns': system_dns.get('primary_dns', db_settings.get('primary_dns', '')),
                    'secondary_dns': system_dns.get('secondary_dns', db_settings.get('secondary_dns', ''))
                }
                
                # Update database to match system
                self.db.set_dns_settings(
                    result['dns_type'], 
                    result['primary_dns'], 
                    result['secondary_dns']
                )
                
                return result
            else:
                # Fallback to database settings if system read fails
                return db_settings
                
        except Exception as e:
            logging.error(f"Error getting DNS settings: {e}")
            # Return database settings as fallback
            return self.db.get_dns_settings()
    
    def _get_system_dns_settings(self):
        """Read actual DNS settings from the system"""
        try:
            dns_servers = []
            
            # Method 1: Try resolvectl (modern Ubuntu)
            if os.path.exists('/usr/bin/resolvectl') or os.path.exists('/bin/resolvectl'):
                try:
                    result = subprocess.run(['resolvectl', 'status'], 
                                          capture_output=True, text=True, check=True)
                    
                    # Parse resolvectl output for DNS servers
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if 'DNS Servers:' in line:
                            # Extract DNS servers from the line
                            dns_part = line.split('DNS Servers:')[1].strip()
                            if dns_part:
                                dns_servers.extend(dns_part.split())
                        elif line.startswith('DNS Servers:'):
                            dns_part = line.replace('DNS Servers:', '').strip()
                            if dns_part:
                                dns_servers.extend(dns_part.split())
                        elif 'Current DNS Server:' in line:
                            dns_part = line.split('Current DNS Server:')[1].strip()
                            if dns_part:
                                dns_servers.append(dns_part)
                                
                except subprocess.CalledProcessError:
                    pass
            
            # Method 2: Try reading /etc/resolv.conf
            if not dns_servers and os.path.exists('/etc/resolv.conf'):
                try:
                    with open('/etc/resolv.conf', 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith('nameserver'):
                                parts = line.split()
                                if len(parts) >= 2:
                                    dns_servers.append(parts[1])
                except Exception:
                    pass
            
            # Clean up and deduplicate DNS servers
            dns_servers = [dns for dns in dns_servers if self._is_valid_ip(dns)]
            dns_servers = list(dict.fromkeys(dns_servers))  # Remove duplicates while preserving order
            
            if not dns_servers:
                return None
            
            # Determine DNS type based on the servers
            primary_dns = dns_servers[0] if dns_servers else ''
            secondary_dns = dns_servers[1] if len(dns_servers) > 1 else ''
            
            # Detect DNS type based on known DNS servers
            dns_type = 'custom'
            if primary_dns in ['208.67.222.123', '208.67.220.123']:
                dns_type = 'opendns'
            elif primary_dns in ['1.1.1.3', '1.0.0.3']:
                dns_type = 'cloudflare'
            elif primary_dns in ['8.8.8.8', '8.8.4.4']:
                dns_type = 'google'
            elif (not primary_dns or 
                  primary_dns.startswith('192.168.') or 
                  primary_dns.startswith('10.') or
                  primary_dns.startswith('172.16.') or
                  primary_dns == '127.0.0.53'):  # systemd-resolved
                dns_type = 'system'
            
            return {
                'dns_type': dns_type,
                'primary_dns': primary_dns,
                'secondary_dns': secondary_dns
            }
            
        except Exception as e:
            logging.error(f"Error reading system DNS settings: {e}")
            return None
    
    def set_dns_settings(self, dns_type, primary_dns=None, secondary_dns=None):
        """Update DNS settings in database and apply system changes"""
        # Validate DNS type
        if dns_type not in ['opendns', 'cloudflare', 'google', 'custom', 'system']:
            raise ValueError("Invalid DNS type. Must be 'opendns', 'cloudflare', 'google', 'custom', or 'system'")
        
        # For preset DNS types, we'll use predefined values
        if dns_type in ['opendns', 'cloudflare', 'google']:
            # These types don't require user-provided DNS addresses
            pass
        elif dns_type == 'custom':
            # Custom requires at least primary DNS
            if not primary_dns or not self._is_valid_ip(primary_dns):
                raise ValueError("Custom DNS type requires a valid primary DNS IP address")
            # Validate secondary DNS if provided
            if secondary_dns and not self._is_valid_ip(secondary_dns):
                raise ValueError("Invalid secondary DNS IP address")
        elif dns_type == 'system':
            # For system DNS, we don't change anything - just store the type
            logger.info("Using system default DNS settings")
        
        # Store the provided values (may be None for preset types)
        stored_primary = primary_dns or ''
        stored_secondary = secondary_dns or ''
        
        # Store current settings for rollback
        current_settings = self.get_dns_settings()
        
        # Update settings in database first
        if self.db.set_dns_settings(dns_type, stored_primary, stored_secondary):
            # Apply the new DNS settings only if not 'system' type
            if dns_type != 'system':
                try:
                    self._apply_dns_settings(dns_type, stored_primary, stored_secondary)
                    return True
                except Exception as e:
                    logger.error(f"Failed to apply DNS settings: {e}")
                    # Revert database changes if system application fails
                    try:
                        if current_settings:
                            self.db.set_dns_settings(
                                current_settings.get('dns_type', 'system'),
                                current_settings.get('primary_dns', ''),
                                current_settings.get('secondary_dns', '')
                            )
                    except Exception as revert_error:
                        logger.error(f"Failed to revert DNS settings: {revert_error}")
                    return False
            else:
                # For system DNS, just return success
                return True
        return False
    
    def _is_valid_ip(self, ip_address):
        """Validate an IP address"""
        if not ip_address or not isinstance(ip_address, str):
            return False
            
        import re
        pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if not re.match(pattern, ip_address.strip()):
            return False
            
        try:
            parts = ip_address.strip().split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False
    
    def _apply_dns_settings(self, dns_type, primary_dns, secondary_dns=None):
        """Apply DNS settings to the system"""
        try:
            # Get the actual DNS servers to use based on type
            if dns_type == 'opendns':
                primary = '208.67.222.123'  # OpenDNS FamilyShield
                secondary = '208.67.220.123'
            elif dns_type == 'cloudflare':
                primary = '1.1.1.3'  # Cloudflare for Families
                secondary = '1.0.0.3'
            elif dns_type == 'google':
                primary = '8.8.8.8'  # Google DNS
                secondary = '8.8.4.4'
            elif dns_type == 'custom':
                primary = primary_dns or ''
                secondary = secondary_dns or ''
            else:  # system
                # Reset to system defaults (will use DHCP)
                primary = ''
                secondary = ''
            
            # Get active network interfaces
            def get_active_interfaces():
                try:
                    result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                          capture_output=True, text=True, check=True)
                    interfaces = set()
                    for line in result.stdout.split('\n'):
                        if 'dev' in line:
                            parts = line.split()
                            dev_index = parts.index('dev')
                            if dev_index + 1 < len(parts):
                                interfaces.add(parts[dev_index + 1])
                    return list(interfaces)
                except:
                    # Fallback to common interface names
                    return ['eth0', 'enp0s3', 'wlan0', 'wlp2s0']
            
            # Try using resolvectl first (modern Ubuntu 18.04+)
            if os.path.exists('/usr/bin/resolvectl') or os.path.exists('/bin/resolvectl'):
                interfaces = get_active_interfaces()
                
                if primary:
                    # Set DNS for each active interface
                    for interface in interfaces:
                        try:
                            dns_servers = [primary]
                            if secondary:
                                dns_servers.append(secondary)
                            
                                    # Use resolvectl to set DNS
                            cmd = ['sudo', 'resolvectl', 'dns', interface] + dns_servers
                            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                            logger.info(f"Set DNS {dns_servers} for interface {interface}")
                            if result.stderr:
                                logger.warning(f"DNS setting warning for {interface}: {result.stderr}")
                        except subprocess.CalledProcessError as e:
                            logger.warning(f"Failed to set DNS for interface {interface}: {e}")
                            if hasattr(e, 'stderr') and e.stderr:
                                logger.warning(f"Error details: {e.stderr}")
                            continue
                    
                    # Flush DNS cache
                    try:
                        subprocess.run(['sudo', 'resolvectl', 'flush-caches'], check=True)
                    except subprocess.CalledProcessError:
                        pass
                else:
                    # Reset to DHCP for all interfaces
                    for interface in interfaces:
                        try:
                            subprocess.run(['sudo', 'resolvectl', 'revert', interface], 
                                         check=True, capture_output=True)
                        except subprocess.CalledProcessError:
                            continue
                    
                    # Flush DNS cache
                    try:
                        subprocess.run(['sudo', 'resolvectl', 'flush-caches'], check=True)
                    except subprocess.CalledProcessError:
                        pass
            
            # Fallback to /etc/resolv.conf method
            else:
                # Backup original resolv.conf if it exists and isn't our backup
                if os.path.exists('/etc/resolv.conf') and not os.path.exists('/etc/resolv.conf.backup'):
                    subprocess.run(['sudo', 'cp', '/etc/resolv.conf', '/etc/resolv.conf.backup'])
                
                # Write new resolv.conf
                resolv_content = "# Generated by Ubuntu Parental Control\n"
                if primary:
                    resolv_content += f"nameserver {primary}\n"
                if secondary:
                    resolv_content += f"nameserver {secondary}\n"
                
                # Write to temporary file first, then move
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
                    tmp_file.write(resolv_content)
                    tmp_path = tmp_file.name
                
                subprocess.run(['sudo', 'mv', tmp_path, '/etc/resolv.conf'], check=True)
                subprocess.run(['sudo', 'chmod', '644', '/etc/resolv.conf'], check=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to apply DNS settings: {e}")
            raise Exception(f"Failed to apply DNS settings: {e}")
        except Exception as e:
            logging.error(f"Unexpected error applying DNS settings: {e}")
            raise Exception(f"Failed to apply DNS settings: {e}")