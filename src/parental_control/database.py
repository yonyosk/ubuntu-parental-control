"""
Database abstraction layer for Ubuntu Parental Control.
Provides a unified interface for data storage using TinyDB.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import threading

logger = logging.getLogger(__name__)

class ParentalControlDB:
    """
    Database abstraction layer using TinyDB for JSON storage.
    Thread-safe and provides methods for all data operations.
    """
    
    def __init__(self, db_path: str = '/var/lib/ubuntu-parental/control.json'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use caching middleware for better performance
        self.db = TinyDB(
            str(self.db_path),
            storage=CachingMiddleware(JSONStorage),
            indent=2,
            ensure_ascii=False
        )
        
        # Thread lock for concurrent access
        self._lock = threading.RLock()
        
        # Initialize tables
        self._init_tables()
    
    def _init_tables(self):
        """Initialize all required tables."""
        # Create tables if they don't exist
        self.blocked_sites = self.db.table('blocked_sites')
        self.temporary_exceptions = self.db.table('temporary_exceptions')
        self.dns_settings = self.db.table('dns_settings')
        self.activity_log = self.db.table('activity_log')
        self.time_schedules = self.db.table('time_schedules')
        self.settings = self.db.table('settings')
        self.blacklist_categories = self.db.table('blacklist_categories')
        self.blacklist_domains = self.db.table('blacklist_domains')
        self.daily_usage = self.db.table('daily_usage')
        
        # Initialize default settings if empty
        if not self.settings.all():
            self.settings.insert({
                'id': 1,
                'daily_limit_minutes': None,
                'protection_active': True,
                'default_language': 'he',  # Hebrew is default
                'created_at': datetime.now().isoformat()
            })
        else:
            # Migrate existing settings to include default_language if missing
            settings = self.settings.all()
            if settings and 'default_language' not in settings[0]:
                Setting = Query()
                self.settings.update({'default_language': 'he'}, Setting.id == 1)
        
        # Initialize default DNS settings if empty
        if not self.dns_settings.all():
            self.dns_settings.insert({
                'id': 1,
                'dns_type': 'system',
                'primary_dns': '8.8.8.8',
                'secondary_dns': '8.8.4.4',
                'updated_at': datetime.now().isoformat()
            })
    
    def close(self):
        """Close the database connection."""
        self.db.close()
    
    # Blocked Sites Management
    def add_blocked_site(self, domain: str, category: str = None) -> bool:
        """Add a site to the blocked list."""
        with self._lock:
            try:
                # Check if already exists
                Site = Query()
                if self.blocked_sites.search(Site.domain == domain):
                    return False
                
                self.blocked_sites.insert({
                    'domain': domain,
                    'category': category,
                    'date_added': datetime.now().isoformat()
                })
                # Force flush to disk to ensure persistence across instances
                self.db.storage.flush()
                return True
            except Exception as e:
                logger.error(f"Error adding blocked site: {e}")
                return False
    
    def remove_blocked_site(self, domain: str) -> bool:
        """Remove a site from the blocked list."""
        with self._lock:
            try:
                Site = Query()
                removed = self.blocked_sites.remove(Site.domain == domain)
                # Force flush to disk to ensure persistence across instances
                self.db.storage.flush()
                return len(removed) > 0
            except Exception as e:
                logger.error(f"Error removing blocked site: {e}")
                return False
    
    def get_blocked_sites(self) -> List[Dict]:
        """Get all blocked sites."""
        with self._lock:
            return self.blocked_sites.all()
    
    def is_site_blocked(self, domain: str) -> bool:
        """Check if a site is blocked."""
        with self._lock:
            Site = Query()
            return bool(self.blocked_sites.search(Site.domain == domain))
    
    # Temporary Exceptions Management
    def add_temporary_exception(self, domain: str, expiry_time: str) -> bool:
        """Add a temporary exception for a domain."""
        with self._lock:
            try:
                self.temporary_exceptions.insert({
                    'domain': domain,
                    'expiry_time': expiry_time,
                    'created_at': datetime.now().isoformat()
                })
                return True
            except Exception as e:
                logger.error(f"Error adding temporary exception: {e}")
                return False
    
    def get_active_exceptions(self) -> List[Dict]:
        """Get all active temporary exceptions."""
        with self._lock:
            current_time = datetime.now().isoformat()
            Exception = Query()
            return self.temporary_exceptions.search(Exception.expiry_time > current_time)
    
    def cleanup_expired_exceptions(self) -> int:
        """Remove expired temporary exceptions."""
        with self._lock:
            current_time = datetime.now().isoformat()
            Exception = Query()
            removed = self.temporary_exceptions.remove(Exception.expiry_time <= current_time)
            return len(removed)
    
    # DNS Settings Management
    def get_dns_settings(self) -> Optional[Dict]:
        """Get current DNS settings."""
        with self._lock:
            settings = self.dns_settings.all()
            return settings[-1] if settings else None
    
    def set_dns_settings(self, dns_type: str, primary_dns: str, secondary_dns: str = None) -> bool:
        """Update DNS settings."""
        with self._lock:
            try:
                self.dns_settings.insert({
                    'dns_type': dns_type,
                    'primary_dns': primary_dns,
                    'secondary_dns': secondary_dns,
                    'updated_at': datetime.now().isoformat()
                })
                return True
            except Exception as e:
                logger.error(f"Error setting DNS settings: {e}")
                return False
    
    # Activity Logging
    def log_activity(self, domain: str, action: str, category: str = None, 
                    client_ip: str = None, user_agent: str = None, **details) -> bool:
        """Log an activity."""
        with self._lock:
            try:
                self.activity_log.insert({
                    'timestamp': datetime.now().isoformat(),
                    'domain': domain,
                    'action': action,
                    'category': category,
                    'client_ip': client_ip,
                    'user_agent': user_agent,
                    'details': details
                })
                return True
            except Exception as e:
                logger.error(f"Error logging activity: {e}")
                return False
    
    def get_activity_logs(self, start_date: str = None, end_date: str = None, 
                         domain: str = None, action: str = None, 
                         category: str = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get activity logs with filtering."""
        with self._lock:
            Activity = Query()
            conditions = []
            
            if start_date:
                conditions.append(Activity.timestamp >= start_date)
            if end_date:
                conditions.append(Activity.timestamp <= end_date)
            if domain:
                conditions.append(Activity.domain == domain)
            if action:
                conditions.append(Activity.action == action)
            if category:
                conditions.append(Activity.category == category)
            
            if conditions:
                # Combine conditions with AND
                combined_condition = conditions[0]
                for condition in conditions[1:]:
                    combined_condition = combined_condition & condition
                results = self.activity_log.search(combined_condition)
            else:
                results = self.activity_log.all()
            
            # Sort by timestamp (newest first) and apply pagination
            missing_timestamps = [
                entry for entry in results
                if not isinstance(entry.get('timestamp'), str) or not entry.get('timestamp')
            ]
            if missing_timestamps:
                logger.warning(
                    "Found %d activity log entries missing timestamp; applying resilient sort",
                    len(missing_timestamps)
                )
            try:
                results.sort(key=lambda x: str(x.get('timestamp', '')), reverse=True)
            except Exception as e:
                logger.warning(f"Error sorting activity logs by timestamp: {e}")
            return results[offset:offset + limit]
    
    # Time Schedules Management
    def add_time_schedule(self, name: str, start_time: str, end_time: str,
                         days: List[int], is_active: bool = True) -> bool:
        """Add a time schedule."""
        with self._lock:
            try:
                self.time_schedules.insert({
                    'name': name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'days': days,
                    'is_active': is_active,
                    'created_at': datetime.now().isoformat()
                })
                self.db.storage.flush()  # Flush to disk immediately
                return True
            except Exception as e:
                logger.error(f"Error adding time schedule: {e}")
                return False
    
    def get_time_schedules(self, active_only: bool = True) -> List[Dict]:
        """Get time schedules."""
        with self._lock:
            if active_only:
                Schedule = Query()
                return self.time_schedules.search(Schedule.is_active == True)
            return self.time_schedules.all()
    
    def update_time_schedule(self, schedule_id: int, **updates) -> bool:
        """Update a time schedule."""
        with self._lock:
            try:
                # Update by document ID, not by field query
                updated = self.time_schedules.update(updates, doc_ids=[schedule_id])
                self.db.storage.flush()  # Flush to disk immediately
                return len(updated) > 0
            except Exception as e:
                logger.error(f"Error updating time schedule: {e}")
                return False

    def delete_time_schedule(self, schedule_id: int) -> bool:
        """Delete a time schedule."""
        with self._lock:
            try:
                # Delete by document ID, not by field query
                removed = self.time_schedules.remove(doc_ids=[schedule_id])
                self.db.storage.flush()  # Flush to disk immediately
                return len(removed) > 0
            except Exception as e:
                logger.error(f"Error deleting time schedule: {e}")
                return False

    # Daily Usage Tracking
    def record_daily_usage(self, date_str: str, minutes: int) -> bool:
        """Record or update daily usage."""
        with self._lock:
            try:
                Usage = Query()
                existing = self.daily_usage.search(Usage.date == date_str)
                
                if existing:
                    # Update existing record
                    current_usage = existing[0].get('minutes_used', 0)
                    self.daily_usage.update(
                        {
                            'minutes_used': current_usage + minutes,
                            'last_updated': datetime.now().isoformat()
                        },
                        Usage.date == date_str
                    )
                else:
                    # Create new record
                    self.daily_usage.insert({
                        'date': date_str,
                        'minutes_used': minutes,
                        'domains_accessed': 0,
                        'blocks_count': 0,
                        'last_updated': datetime.now().isoformat()
                    })
                self.db.storage.flush()  # Flush to disk immediately
                return True
            except Exception as e:
                logger.error(f"Error recording daily usage: {e}")
                return False
    
    def get_daily_usage(self, date_str: str) -> Dict:
        """Get usage for a specific date."""
        with self._lock:
            Usage = Query()
            result = self.daily_usage.search(Usage.date == date_str)
            return result[0] if result else {'date': date_str, 'minutes_used': 0}
    
    def set_daily_usage_limit(self, minutes: int, reset_time: str = "00:00") -> bool:
        """Set daily internet usage limit."""
        with self._lock:
            try:
                # Update or create daily usage limit setting
                limit_data = {
                    'time_limit_minutes': minutes,
                    'reset_time': reset_time,
                    'is_active': True,
                    'updated_at': datetime.now().isoformat()
                }
                
                # Check if limit setting already exists
                existing = self.settings.search(Query().daily_limit_minutes.exists())
                if existing:
                    self.settings.update(limit_data, Query().daily_limit_minutes.exists())
                else:
                    # Add to existing settings or create new
                    settings = self.settings.all()
                    if settings:
                        # Update existing settings record
                        self.settings.update(limit_data, Query().id == 1)
                    else:
                        # Create new settings record
                        limit_data['id'] = 1
                        limit_data['protection_active'] = True
                        limit_data['created_at'] = datetime.now().isoformat()
                        self.settings.insert(limit_data)

                self.db.storage.flush()  # Flush to disk immediately
                return True
            except Exception as e:
                logger.error(f"Error setting daily usage limit: {e}")
                return False
    
    def get_daily_usage_limit(self) -> Optional[Dict]:
        """Get current daily usage limit settings."""
        with self._lock:
            try:
                settings = self.settings.all()
                if settings and 'time_limit_minutes' in settings[0]:
                    return {
                        'time_limit_minutes': settings[0].get('time_limit_minutes'),
                        'reset_time': settings[0].get('reset_time', '00:00'),
                        'is_active': settings[0].get('is_active', True)
                    }
                return None
            except Exception as e:
                logger.error(f"Error getting daily usage limit: {e}")
                return None
    
    # Settings Management
    def get_settings(self) -> Dict:
        """Get current settings."""
        with self._lock:
            settings = self.settings.all()
            return settings[0] if settings else {}
    
    def update_settings(self, **updates) -> bool:
        """Update settings."""
        with self._lock:
            try:
                if self.settings.all():
                    Setting = Query()
                    self.settings.update(updates, Setting.id == 1)
                else:
                    updates['id'] = 1
                    self.settings.insert(updates)
                # Force flush to disk
                self.db.storage.flush()
                return True
            except Exception as e:
                logger.error(f"Error updating settings: {e}")
                return False

    def get_default_language(self) -> str:
        """Get the default language for blocking pages."""
        settings = self.get_settings()
        return settings.get('default_language', 'he')  # Hebrew is default

    def set_default_language(self, language: str) -> bool:
        """Set the default language for blocking pages."""
        if language not in ['he', 'en']:
            logger.error(f"Invalid language: {language}")
            return False
        return self.update_settings(default_language=language)

    # Blacklist Management
    def add_blacklist_category(self, name: str, is_active: bool = True) -> bool:
        """Add or update a blacklist category."""
        with self._lock:
            try:
                Category = Query()
                existing = self.blacklist_categories.search(Category.name == name)
                
                if existing:
                    # Preserve existing domain_count when updating
                    current_data = existing[0]
                    self.blacklist_categories.update(
                        {
                            'is_active': is_active,
                            'last_updated': datetime.now().isoformat(),
                            'domain_count': current_data.get('domain_count', 0)
                        },
                        Category.name == name
                    )
                else:
                    self.blacklist_categories.insert({
                        'name': name,
                        'is_active': is_active,
                        'last_updated': datetime.now().isoformat(),
                        'domain_count': 0
                    })
                return True
            except Exception as e:
                logger.error(f"Error adding blacklist category: {e}")
                return False
    
    def get_blacklist_categories(self, active_only: bool = True) -> List[Dict]:
        """Get blacklist categories."""
        with self._lock:
            if active_only:
                Category = Query()
                return self.blacklist_categories.search(Category.is_active == True)
            else:
                return self.blacklist_categories.all()
    
    def set_blacklist_categories(self, category_names: List[str]) -> bool:
        """Set which blacklist categories are active."""
        with self._lock:
            try:
                # First, deactivate all categories
                self.blacklist_categories.update({'is_active': False})
                
                # Then activate the selected ones
                for category_name in category_names:
                    Category = Query()
                    existing = self.blacklist_categories.search(Category.name == category_name)
                    
                    if existing:
                        # Update existing category
                        self.blacklist_categories.update(
                            {'is_active': True, 'last_updated': datetime.now().isoformat()},
                            Category.name == category_name
                        )
                    else:
                        # Add new category
                        self.add_blacklist_category(category_name, is_active=True)
                
                return True
            except Exception as e:
                logger.error(f"Error setting blacklist categories: {e}")
                return False
    
    def add_blacklist_domains(self, category: str, domains: List[str]) -> int:
        """Add domains to a blacklist category."""
        with self._lock:
            try:
                # First, remove all existing domains for this category to avoid duplicates
                Domain = Query()
                self.blacklist_domains.remove(Domain.category == category)
                
                # Prepare bulk insert data
                current_time = datetime.now().isoformat()
                domains_to_insert = [
                    {
                        'domain': domain.strip().lower(),
                        'category': category,
                        'added_at': current_time
                    }
                    for domain in domains if domain.strip()
                ]
                
                # Bulk insert all domains
                if domains_to_insert:
                    self.blacklist_domains.insert_multiple(domains_to_insert)
                    added_count = len(domains_to_insert)
                    logger.info(f"Bulk inserted {added_count} domains for category {category}")
                else:
                    added_count = 0
                
                # Update category domain count
                Category = Query()
                self.blacklist_categories.update(
                    {'domain_count': added_count, 'last_updated': current_time},
                    Category.name == category
                )
                
                return added_count
            except Exception as e:
                logger.error(f"Error adding blacklist domains: {e}")
                return 0
    
    def get_blacklist_domains(self, category: str = None) -> List[str]:
        """Get domains from blacklists.

        Args:
            category: Specific category to get domains from. If None, returns domains
                     from all ACTIVE categories only.
        """
        with self._lock:
            if category:
                Domain = Query()
                results = self.blacklist_domains.search(Domain.category == category)
            else:
                # Only return domains from active categories
                active_categories = self.get_blacklist_categories(active_only=True)
                active_category_names = [cat['name'] for cat in active_categories]

                if not active_category_names:
                    return []

                Domain = Query()
                results = self.blacklist_domains.search(Domain.category.one_of(active_category_names))

            return [item['domain'] for item in results]
    
    def is_domain_in_blacklist(self, domain: str) -> tuple[bool, List[str]]:
        """Check if domain is in any ACTIVE blacklist category.

        Returns:
            Tuple of (is_blocked, list of active categories that block this domain)
        """
        with self._lock:
            Domain = Query()
            domain = domain.lower().strip()

            # Get active categories to filter results
            active_categories = self.get_blacklist_categories(active_only=True)
            active_category_names = [cat['name'] for cat in active_categories]

            if not active_category_names:
                return False, []

            # Check exact match first
            results = self.blacklist_domains.search(Domain.domain == domain)

            # If no exact match, check if any parent domain is blocked
            if not results:
                # Remove subdomains one by one and check
                # e.g., www.example.com -> example.com -> com
                parts = domain.split('.')
                for i in range(1, len(parts)):
                    parent_domain = '.'.join(parts[i:])
                    parent_results = self.blacklist_domains.search(Domain.domain == parent_domain)
                    if parent_results:
                        results.extend(parent_results)
                        break

            # Filter results to only include active categories
            active_results = [item for item in results if item['category'] in active_category_names]
            categories = [item['category'] for item in active_results]
            return bool(categories), categories
    
    # Utility Methods
    def backup_data(self, backup_path: str) -> bool:
        """Create a backup of all data."""
        try:
            backup_data = {
                'blocked_sites': self.blocked_sites.all(),
                'temporary_exceptions': self.temporary_exceptions.all(),
                'dns_settings': self.dns_settings.all(),
                'activity_log': self.activity_log.all(),
                'time_schedules': self.time_schedules.all(),
                'settings': self.settings.all(),
                'blacklist_categories': self.blacklist_categories.all(),
                'blacklist_domains': self.blacklist_domains.all(),
                'daily_usage': self.daily_usage.all(),
                'backup_timestamp': datetime.now().isoformat()
            }
            
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def restore_data(self, backup_path: str) -> bool:
        """Restore data from backup."""
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            # Clear existing data
            self.db.truncate()
            
            # Restore each table
            for table_name, data in backup_data.items():
                if table_name != 'backup_timestamp' and data:
                    table = self.db.table(table_name)
                    table.insert_multiple(data)
            
            return True
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        with self._lock:
            return {
                'blocked_sites': len(self.blocked_sites),
                'temporary_exceptions': len(self.temporary_exceptions),
                'dns_settings': len(self.dns_settings),
                'activity_log': len(self.activity_log),
                'time_schedules': len(self.time_schedules),
                'settings': len(self.settings),
                'blacklist_categories': len(self.blacklist_categories),
                'blacklist_domains': len(self.blacklist_domains),
                'daily_usage': len(self.daily_usage),
                'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            }
