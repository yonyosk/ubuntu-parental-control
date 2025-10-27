import os
import tarfile
import tempfile
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlacklistManager:
    """
    Manages downloading, parsing, and applying UT1 blacklists for content filtering.
    """
    
    # Base URL for UT1 blacklists
    BASE_URL = "https://dsi.ut-capitole.fr/blacklists/download"
    
    # Default blacklist categories to use
    DEFAULT_CATEGORIES = [
        'adult', 'agressif', 'gambling', 'hacking', 'malware',
        'phishing', 'porn', 'publicite', 'social_networks', 'warez'
    ]
    
    def __init__(self, db):
        """
        Initialize the BlacklistManager with a database connection.
        
        Args:
            db: ParentalControlDB instance
        """
        self.db = db
        self.temp_dir = Path(tempfile.gettempdir()) / 'ubuntu-parental-control'
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Database setup is now handled by ParentalControlDB class
    
    def get_available_categories(self) -> List[Dict[str, str]]:
        """
        Get a list of all available blacklist categories.
        
        Returns:
            List of dictionaries with category information
        """
        # This is a static list, but in a real implementation, you might want to 
        # fetch this from the server or a configuration file
        categories = [
            {'name': 'adult', 'description': 'Adult content'},
            {'name': 'agressif', 'description': 'Aggressive/violent content'},
            {'name': 'gambling', 'description': 'Online gambling sites'},
            {'name': 'hacking', 'description': 'Hacking/security sites'},
            {'name': 'malware', 'description': 'Malware distribution sites'},
            {'name': 'phishing', 'description': 'Phishing/fraud sites'},
            {'name': 'porn', 'description': 'Pornography'},
            {'name': 'publicite', 'description': 'Advertising/tracking'},
            {'name': 'social_networks', 'description': 'Social networks'},
            {'name': 'warez', 'description': 'Pirated content'},
            # Add more categories as needed
        ]
        return categories
    
    def download_blacklist(self, category: str, max_retries: int = 3) -> Optional[Path]:
        """
        Download a blacklist file for a specific category with retry logic.
        
        Args:
            category: The category to download
            max_retries: Maximum number of retry attempts
            
        Returns:
            Path to the downloaded file, or None if download failed
        """
        url = f"{self.BASE_URL}/{category}.tar.gz"
        output_file = self.temp_dir / f"{category}.tar.gz"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading blacklist: {category} (attempt {attempt + 1}/{max_retries})")
                
                # Use better timeout and headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Ubuntu Parental Control)'
                }
                
                response = requests.get(
                    url, 
                    stream=True, 
                    timeout=(10, 300),  # 10s connect, 300s read timeout
                    headers=headers
                )
                response.raise_for_status()
                
                # Validate content type if available
                content_type = response.headers.get('content-type', '').lower()
                if content_type and 'gzip' not in content_type and 'octet-stream' not in content_type:
                    logger.warning(f"Unexpected content type for {category}: {content_type}")
                
                # Download with progress logging
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                
                # Validate minimum file size
                if output_file.stat().st_size < 1024:  # Less than 1KB is suspicious
                    logger.error(f"Downloaded file {output_file} is too small ({output_file.stat().st_size} bytes)")
                    output_file.unlink(missing_ok=True)
                    continue
                
                logger.info(f"Downloaded {category} to {output_file} ({downloaded} bytes)")
                return output_file
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout downloading {category} on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to download {category} after {max_retries} attempts (timeout)")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error downloading {category} on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to download {category} after {max_retries} attempts: {e}")
            except Exception as e:
                logger.error(f"Unexpected error downloading {category}: {e}")
                if attempt == max_retries - 1:
                    return None
            
            # Clean up failed download
            if output_file.exists():
                output_file.unlink(missing_ok=True)
        
        return None
    
    def extract_blacklist(self, tar_path: Path, category: str) -> Optional[Path]:
        """
        Extract a downloaded blacklist tar.gz file and find the domains file.
        
        Args:
            tar_path: Path to the .tar.gz file
            category: The category being extracted
            
        Returns:
            Path to the domains file, or None if extraction failed
        """
        extract_dir = self.temp_dir / category
        extract_dir.mkdir(exist_ok=True)
        
        try:
            # Validate the tar file first
            if not tarfile.is_tarfile(tar_path):
                logger.error(f"Invalid tar file: {tar_path}")
                return None
                
            with tarfile.open(tar_path, 'r:gz') as tar:
                # Security check - prevent path traversal attacks
                def is_safe_path(path):
                    return not (path.startswith('/') or '..' in path)
                
                members = tar.getmembers()
                safe_members = [m for m in members if is_safe_path(m.name)]
                
                if len(safe_members) != len(members):
                    logger.warning(f"Filtered out {len(members) - len(safe_members)} unsafe paths from {tar_path}")
                
                tar.extractall(path=extract_dir, members=safe_members)
            
            # Find the domains file - try multiple common locations
            possible_paths = [
                extract_dir / category / 'domains',  # Standard structure
                extract_dir / 'domains',             # Direct in extract dir
                extract_dir / f'{category}.txt',     # Text file format
                extract_dir / category / f'{category}.txt',  # Category subdir with txt
            ]
            
            for domains_file in possible_paths:
                if domains_file.exists() and domains_file.stat().st_size > 0:
                    logger.info(f"Found domains file: {domains_file} ({domains_file.stat().st_size} bytes)")
                    return domains_file
                    
            # Search recursively for any file named 'domains' or containing domain data
            for file in extract_dir.rglob('*'):
                if file.is_file() and file.stat().st_size > 0:
                    # Check if filename suggests it contains domains
                    filename = file.name.lower()
                    if (filename in ['domains', 'domain.txt', 'blacklist.txt'] or
                        filename.endswith('.domains') or
                        (filename.endswith('.txt') and 'domain' in filename)):
                        logger.info(f"Found potential domains file: {file}")
                        return file
                        
            logger.error(f"No domains file found in {extract_dir}")
            # List contents for debugging
            try:
                contents = list(extract_dir.rglob('*'))
                logger.debug(f"Extract directory contents: {[str(f) for f in contents[:10]]}")
            except:
                pass
                
            return None
            
        except Exception as e:
            logger.error(f"Error extracting {tar_path}: {e}")
            return None
    
    def parse_domains_file(self, file_path: Path) -> Set[str]:
        """
        Parse a domains file and extract all valid domains.
        
        Args:
            file_path: Path to the domains file
            
        Returns:
            Set of domain strings
        """
        domains = set()
        line_count = 0
        valid_domains = 0
        
        try:
            import re
            # Domain validation regex (simplified but effective)
            domain_pattern = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+$')
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_count += 1
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#') or line.startswith('//'):
                        continue
                    
                    # Remove any comments at the end of the line
                    domain = line.split('#')[0].split('//')[0].strip()
                    
                    # Clean up the domain
                    domain = domain.lstrip('.').lstrip('*').strip()
                    domain = domain.lower()
                    
                    # Skip if empty after cleaning
                    if not domain:
                        continue
                    
                    # Basic validation - must contain at least one dot and be reasonable length
                    if ('.' in domain and 
                        len(domain) > 3 and 
                        len(domain) <= 253 and  # Max domain length
                        not domain.startswith('http') and
                        not domain.startswith('www.') and  # Remove www prefix
                        domain_pattern.match(domain)):
                        
                        domains.add(domain)
                        valid_domains += 1
                        
                        # Also add www. version for main domains
                        if not domain.startswith('www.') and domain.count('.') == 1:
                            domains.add(f"www.{domain}")
            
            logger.info(f"Parsed {valid_domains} valid domains from {line_count} lines in {file_path}")
            
        except Exception as e:
            logger.error(f"Error parsing domains file {file_path}: {e}")
        
        return domains
    
    # _bulk_insert_domains method removed - now using TinyDB add_blacklist_domains method
    
    def update_blacklist(self, category: str) -> Tuple[bool, int]:
        """
        Update a single blacklist category.
        
        Args:
            category: The category to update
            
        Returns:
            Tuple of (success, num_domains) where success is a boolean indicating
            if the update was successful, and num_domains is the number of domains
            added or updated.
        """
        try:
            # Download the blacklist
            tar_path = self.download_blacklist(category)
            if not tar_path or not tar_path.exists():
                logger.error(f"Failed to download blacklist for {category}")
                return False, 0
            
            # Extract the blacklist
            domains_file = self.extract_blacklist(tar_path, category)
            if not domains_file or not domains_file.exists():
                logger.error(f"Failed to extract blacklist for {category}")
                return False, 0
            
            # Parse the domains
            domains = self.parse_domains_file(domains_file)
            if not domains:
                logger.warning(f"No domains found in {domains_file}")
                return False, 0
            
            # Save to TinyDB database
            try:
                # Add or update the category
                self.db.add_blacklist_category(category, is_active=True)
                
                # Add domains to the database
                domains_list = list(domains)
                num_inserted = self.db.add_blacklist_domains(category, domains_list)
                
                logger.info(f"Updated blacklist '{category}' with {num_inserted} domains")
                return True, num_inserted
                
            except Exception as e:
                logger.error(f"Database error updating {category}: {e}")
                return False, 0
                
        except Exception as e:
            logger.error(f"Error updating blacklist {category}: {e}")
            return False, 0
    
    def update_all_blacklists(self) -> Dict[str, int]:
        """
        Update all active blacklist categories.
        
        Returns:
            Dictionary mapping category names to the number of domains updated
        """
        results = {}
        
        try:
            # Get active categories from TinyDB
            active_categories = self.db.get_blacklist_categories(active_only=True)
            active_category_names = [cat['name'] for cat in active_categories]
            
            # If no active categories, use defaults
            if not active_category_names:
                active_category_names = self.DEFAULT_CATEGORIES
                # Ensure default categories exist in the database
                for category in active_category_names:
                    self.db.add_blacklist_category(category, is_active=True)
            
            # Process each category
            for category_name in active_category_names:
                logger.info(f"Processing blacklist category: {category_name}")
                
                try:
                    # Use the existing update_blacklist method for each category
                    success, num_domains = self.update_blacklist(category_name)
                    
                    if success and num_domains > 0:
                        results[category_name] = num_domains
                        logger.info(f"Updated {category_name} with {num_domains} domains")
                    else:
                        logger.warning(f"Failed to update or no domains found for {category_name}")
                        results[category_name] = 0
                        
                except Exception as e:
                    logger.error(f"Error updating category {category_name}: {e}")
                    results[category_name] = 0
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to update blacklists: {e}")
            # Don't raise here, return partial results
            
        return results
    
    def get_blocked_domains(self, category: str = None) -> Set[str]:
        """
        Get all blocked domains, optionally filtered by category.
        
        Args:
            category: Optional category to filter by
            
        Returns:
            Set of blocked domains
        """
        domains = self.db.get_blacklist_domains(category)
        return set(domains)
    
    def is_domain_blocked(self, domain: str) -> Tuple[bool, List[str]]:
        """
        Check if a domain is blocked by any active blacklist.
        
        Args:
            domain: The domain to check (e.g., 'example.com')
            
        Returns:
            Tuple of (is_blocked, categories) where is_blocked is a boolean
            indicating if the domain is blocked, and categories is a list of
            category names that block this domain.
        """
        domain = domain.lower().strip()
        
        # Use the TinyDB method
        is_blocked, categories = self.db.is_domain_in_blacklist(domain)
        
        return is_blocked, categories
