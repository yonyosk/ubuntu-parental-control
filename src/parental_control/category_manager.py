"""
Category Manager for Ubuntu Parental Control.
Provides unified interface for managing built-in and UT1 blacklist categories.
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class CategoryManager:
    """
    Unified category management system that combines:
    - Built-in categories (SOCIAL_MEDIA, GAMING, VIDEO)
    - UT1 blacklist categories (adult, gambling, porn, etc.)

    Provides consistent interface for:
    - Viewing all categories with status
    - Toggling blocking on/off
    - Updating UT1 categories
    - Progress tracking for downloads
    """

    # Built-in categories with their domains
    BUILTIN_CATEGORIES = {
        'social_media': {
            'name': 'Social Media',
            'description': 'Social networking sites like Facebook, Twitter, Instagram, TikTok',
            'icon': '📱',
            'category_type': 'social',
            'domains': [
                'facebook.com', 'www.facebook.com', 'fb.com',
                'twitter.com', 'www.twitter.com', 'x.com',
                'instagram.com', 'www.instagram.com',
                'tiktok.com', 'www.tiktok.com',
                'snapchat.com', 'www.snapchat.com',
                'linkedin.com', 'www.linkedin.com',
                'reddit.com', 'www.reddit.com',
                'pinterest.com', 'www.pinterest.com'
            ]
        },
        'gaming': {
            'name': 'Gaming',
            'description': 'Online gaming platforms like Steam, Roblox, Fortnite',
            'icon': '🎮',
            'category_type': 'entertainment',
            'domains': [
                'roblox.com', 'www.roblox.com',
                'minecraft.net', 'www.minecraft.net',
                'fortnite.com', 'www.fortnite.com',
                'steam.com', 'steampowered.com',
                'epicgames.com', 'www.epicgames.com',
                'twitch.tv', 'www.twitch.tv'
            ]
        },
        'video': {
            'name': 'Video Streaming',
            'description': 'Video streaming platforms like YouTube, Netflix, Disney+',
            'icon': '🎬',
            'category_type': 'entertainment',
            'domains': [
                'youtube.com', 'www.youtube.com', 'youtu.be',
                'netflix.com', 'www.netflix.com',
                'disneyplus.com', 'www.disneyplus.com',
                'hulu.com', 'www.hulu.com',
                'primevideo.com', 'www.primevideo.com',
                'hbomax.com', 'www.hbomax.com'
            ]
        }
    }

    # UT1 categories with descriptions
    UT1_CATEGORIES = {
        'adult': {
            'name': 'Adult Content',
            'description': 'Adult content websites',
            'icon': '🔞',
            'category_type': 'adult'
        },
        'agressif': {
            'name': 'Aggressive Content',
            'description': 'Aggressive, violent, or extremist content',
            'icon': '⚠️',
            'category_type': 'violence'
        },
        'gambling': {
            'name': 'Gambling',
            'description': 'Online gambling and betting sites',
            'icon': '🎰',
            'category_type': 'gambling'
        },
        'hacking': {
            'name': 'Hacking',
            'description': 'Hacking tools and security exploitation sites',
            'icon': '💻',
            'category_type': 'security'
        },
        'malware': {
            'name': 'Malware',
            'description': 'Malware distribution and potentially harmful sites',
            'icon': '🦠',
            'category_type': 'security'
        },
        'phishing': {
            'name': 'Phishing',
            'description': 'Phishing and fraud sites',
            'icon': '🎣',
            'category_type': 'security'
        },
        'porn': {
            'name': 'Pornography',
            'description': 'Pornographic content',
            'icon': '🔞',
            'category_type': 'adult'
        },
        'publicite': {
            'name': 'Advertising',
            'description': 'Advertising and tracking sites',
            'icon': '📢',
            'category_type': 'ads'
        },
        'social_networks': {
            'name': 'Social Networks (UT1)',
            'description': 'Social networking sites from UT1 blacklist',
            'icon': '📱',
            'category_type': 'social'
        },
        'warez': {
            'name': 'Pirated Content',
            'description': 'Pirated software, movies, and media',
            'icon': '🏴‍☠️',
            'category_type': 'piracy'
        }
    }

    def __init__(self, db, blacklist_manager=None):
        """
        Initialize CategoryManager.

        Args:
            db: ParentalControlDB instance
            blacklist_manager: BlacklistManager instance (optional)
        """
        self.db = db
        self.blacklist_manager = blacklist_manager
        self._progress_cache = {}  # In-memory cache for download progress
        self._progress_lock = threading.Lock()

        # Initialize built-in categories in database
        self._init_builtin_categories()

        # Initialize UT1 categories in database
        self._init_ut1_categories()

    def _init_builtin_categories(self):
        """Initialize built-in categories in the database if they don't exist."""
        from tinydb import Query
        Category = Query()

        for category_id, info in self.BUILTIN_CATEGORIES.items():
            # Check if category already exists
            existing = self.db.blacklist_categories.search(Category.name == category_id)

            if not existing:
                # Add new built-in category
                self.db.blacklist_categories.insert({
                    'name': category_id,
                    'display_name': info['name'],
                    'description': info['description'],
                    'icon': info['icon'],
                    'category_type': info['category_type'],
                    'source': 'built-in',
                    'is_active': False,
                    'domains_loaded': True,
                    'domain_count': len(info['domains']),
                    'update_status': 'updated',
                    'last_updated': datetime.now().isoformat(),
                    'created_at': datetime.now().isoformat()
                })
                logger.info(f"Initialized built-in category: {category_id}")

    def _init_ut1_categories(self):
        """Initialize UT1 categories in the database if they don't exist."""
        from tinydb import Query
        Category = Query()

        for category_id, info in self.UT1_CATEGORIES.items():
            # Check if category already exists
            existing = self.db.blacklist_categories.search(Category.name == category_id)

            if not existing:
                # Check if there are existing domains for this category
                existing_domains = self.db.get_blacklist_domains(category_id)
                domains_loaded = len(existing_domains) > 0

                # Add new UT1 category
                self.db.blacklist_categories.insert({
                    'name': category_id,
                    'display_name': info['name'],
                    'description': info['description'],
                    'icon': info['icon'],
                    'category_type': info['category_type'],
                    'source': 'ut1-blacklist',
                    'is_active': False,
                    'domains_loaded': domains_loaded,
                    'domain_count': len(existing_domains),
                    'update_status': 'not_downloaded' if not domains_loaded else 'updated',
                    'last_updated': None,
                    'created_at': datetime.now().isoformat()
                })
                logger.info(f"Initialized UT1 category: {category_id}")
            else:
                # Update existing category with new fields if missing
                cat_data = existing[0]
                updates = {}

                if 'source' not in cat_data:
                    updates['source'] = 'ut1-blacklist'
                if 'display_name' not in cat_data:
                    updates['display_name'] = info['name']
                if 'description' not in cat_data:
                    updates['description'] = info['description']
                if 'icon' not in cat_data:
                    updates['icon'] = info['icon']
                if 'category_type' not in cat_data:
                    updates['category_type'] = info['category_type']
                if 'domains_loaded' not in cat_data:
                    existing_domains = self.db.get_blacklist_domains(category_id)
                    updates['domains_loaded'] = len(existing_domains) > 0
                if 'update_status' not in cat_data:
                    updates['update_status'] = 'updated' if cat_data.get('domains_loaded', False) else 'not_downloaded'

                if updates:
                    self.db.blacklist_categories.update(updates, Category.name == category_id)
                    logger.info(f"Updated UT1 category metadata: {category_id}")

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """
        Get all categories (built-in + UT1) with their current status.

        Returns:
            List of category dictionaries with full metadata
        """
        categories = []
        all_cats = self.db.blacklist_categories.all()

        for cat in all_cats:
            category_id = cat['name']

            # Build unified category object
            category = {
                'id': category_id,
                'name': cat.get('display_name', cat['name']),
                'description': cat.get('description', ''),
                'icon': cat.get('icon', '📁'),
                'category_type': cat.get('category_type', 'other'),
                'source': cat.get('source', 'ut1-blacklist'),
                'is_blocked': cat.get('is_active', False),
                'domains_loaded': cat.get('domains_loaded', False),
                'domain_count': cat.get('domain_count', 0),
                'update_status': cat.get('update_status', 'not_downloaded'),
                'last_updated': cat.get('last_updated'),
                'needs_update': self._needs_update(cat)
            }

            categories.append(category)

        # Sort: built-in first, then by name
        categories.sort(key=lambda x: (x['source'] != 'built-in', x['name']))

        return categories

    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single category by ID.

        Args:
            category_id: Category identifier

        Returns:
            Category dictionary or None if not found
        """
        from tinydb import Query
        Category = Query()

        results = self.db.blacklist_categories.search(Category.name == category_id)
        if not results:
            return None

        cat = results[0]
        return {
            'id': category_id,
            'name': cat.get('display_name', cat['name']),
            'description': cat.get('description', ''),
            'icon': cat.get('icon', '📁'),
            'category_type': cat.get('category_type', 'other'),
            'source': cat.get('source', 'ut1-blacklist'),
            'is_blocked': cat.get('is_active', False),
            'domains_loaded': cat.get('domains_loaded', False),
            'domain_count': cat.get('domain_count', 0),
            'update_status': cat.get('update_status', 'not_downloaded'),
            'last_updated': cat.get('last_updated'),
            'needs_update': self._needs_update(cat)
        }

    def _needs_update(self, category_data: Dict, days: int = 7) -> bool:
        """
        Check if a category needs updating (older than N days).

        Args:
            category_data: Category data from database
            days: Number of days before update is needed

        Returns:
            True if category needs update, False otherwise
        """
        # Built-in categories never need updates
        if category_data.get('source') == 'built-in':
            return False

        # Not downloaded categories need download, not update
        if not category_data.get('domains_loaded', False):
            return False

        last_updated = category_data.get('last_updated')
        if not last_updated:
            return True

        try:
            last_update_date = datetime.fromisoformat(last_updated)
            cutoff_date = datetime.now() - timedelta(days=days)
            return last_update_date < cutoff_date
        except (ValueError, TypeError):
            return True

    def toggle_category_blocking(self, category_id: str, blocked: bool) -> Tuple[bool, str]:
        """
        Toggle category blocking status with immediate effect.

        Args:
            category_id: Category identifier
            blocked: True to block, False to unblock

        Returns:
            Tuple of (success, message)
        """
        from tinydb import Query
        Category = Query()

        try:
            # Check if category exists
            category = self.get_category(category_id)
            if not category:
                return False, f"Category '{category_id}' not found"

            # Check if domains are loaded (required for blocking)
            if blocked and not category['domains_loaded']:
                return False, f"Cannot block '{category['name']}' - domains not downloaded yet"

            # Update database
            self.db.blacklist_categories.update(
                {'is_active': blocked},
                Category.name == category_id
            )

            # Force flush to ensure persistence
            self.db.db.storage.flush()

            action = "blocked" if blocked else "unblocked"
            logger.info(f"Category '{category_id}' {action}")

            return True, f"Category '{category['name']}' {action} successfully"

        except Exception as e:
            logger.error(f"Error toggling category '{category_id}': {e}")
            return False, f"Error: {str(e)}"

    def get_category_domains(self, category_id: str, limit: int = 100, offset: int = 0, search: str = None) -> Dict[str, Any]:
        """
        Get domains for a category with pagination and search.

        Args:
            category_id: Category identifier
            limit: Number of domains per page
            offset: Starting offset
            search: Optional search term

        Returns:
            Dictionary with category info and paginated domains
        """
        category = self.get_category(category_id)
        if not category:
            return {'error': 'Category not found'}

        # Get domains based on source
        if category['source'] == 'built-in':
            # Built-in categories use hardcoded domain lists
            all_domains = self.BUILTIN_CATEGORIES[category_id]['domains']
        else:
            # UT1 categories use database
            all_domains = self.db.get_blacklist_domains(category_id)

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            all_domains = [d for d in all_domains if search_lower in d.lower()]

        # Calculate pagination
        total = len(all_domains)
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (offset // limit) + 1 if limit > 0 else 1

        # Get page of domains
        paginated_domains = all_domains[offset:offset + limit] if limit > 0 else all_domains

        return {
            'category': category,
            'domains': paginated_domains,
            'total': total,
            'page': current_page,
            'limit': limit,
            'total_pages': total_pages
        }

    def update_category(self, category_id: str) -> Tuple[bool, str, int]:
        """
        Update/download a UT1 category with progress tracking.

        Args:
            category_id: Category identifier

        Returns:
            Tuple of (success, message, domain_count)
        """
        from tinydb import Query
        Category = Query()

        try:
            # Check if category exists and is UT1
            category = self.get_category(category_id)
            if not category:
                return False, f"Category '{category_id}' not found", 0

            if category['source'] != 'ut1-blacklist':
                return False, f"Category '{category['name']}' is built-in and cannot be updated", 0

            if not self.blacklist_manager:
                return False, "Blacklist manager not available", 0

            # Set status to downloading
            self._set_update_status(category_id, 'downloading', 0)

            # Call blacklist manager to download and update
            logger.info(f"Starting update for category '{category_id}'")
            success, num_domains = self.blacklist_manager.update_blacklist(category_id)

            if success and num_domains > 0:
                # Update category metadata
                self.db.blacklist_categories.update(
                    {
                        'domains_loaded': True,
                        'domain_count': num_domains,
                        'update_status': 'updated',
                        'last_updated': datetime.now().isoformat()
                    },
                    Category.name == category_id
                )
                self.db.db.storage.flush()

                # Clear progress cache
                self._clear_update_status(category_id)

                logger.info(f"Successfully updated category '{category_id}' with {num_domains} domains")
                return True, f"Successfully updated '{category['name']}' with {num_domains:,} domains", num_domains
            else:
                # Update failed
                self._set_update_status(category_id, 'failed', 0, "Download or parsing failed")

                self.db.blacklist_categories.update(
                    {'update_status': 'failed'},
                    Category.name == category_id
                )
                self.db.db.storage.flush()

                logger.error(f"Failed to update category '{category_id}'")
                return False, f"Failed to update '{category['name']}'", 0

        except Exception as e:
            logger.error(f"Error updating category '{category_id}': {e}")
            self._set_update_status(category_id, 'failed', 0, str(e))
            return False, f"Error: {str(e)}", 0

    def _set_update_status(self, category_id: str, status: str, progress: int, message: str = None):
        """Set update status in progress cache."""
        with self._progress_lock:
            self._progress_cache[category_id] = {
                'status': status,
                'progress': progress,
                'message': message or f"Status: {status}",
                'timestamp': datetime.now().isoformat()
            }

    def _clear_update_status(self, category_id: str):
        """Clear update status from progress cache."""
        with self._progress_lock:
            if category_id in self._progress_cache:
                del self._progress_cache[category_id]

    def get_category_update_status(self, category_id: str) -> Dict[str, Any]:
        """
        Get current update status for progress tracking.

        Args:
            category_id: Category identifier

        Returns:
            Dictionary with status, progress, and message
        """
        with self._progress_lock:
            if category_id in self._progress_cache:
                return self._progress_cache[category_id].copy()

        # No active update, check database for last status
        category = self.get_category(category_id)
        if not category:
            return {'status': 'not_found', 'progress': 0, 'message': 'Category not found'}

        return {
            'status': category['update_status'],
            'progress': 100 if category['update_status'] == 'updated' else 0,
            'message': f"Last updated: {category['last_updated']}" if category['last_updated'] else "Not downloaded"
        }

    def bulk_toggle(self, category_ids: List[str], blocked: bool) -> Dict[str, Any]:
        """
        Toggle multiple categories at once.

        Args:
            category_ids: List of category identifiers
            blocked: True to block, False to unblock

        Returns:
            Dictionary with results
        """
        results = {
            'success': True,
            'updated_count': 0,
            'failed_count': 0,
            'errors': []
        }

        for category_id in category_ids:
            success, message = self.toggle_category_blocking(category_id, blocked)
            if success:
                results['updated_count'] += 1
            else:
                results['failed_count'] += 1
                results['errors'].append({'category_id': category_id, 'error': message})

        if results['failed_count'] > 0:
            results['success'] = False

        return results

    def bulk_update(self, category_ids: List[str]) -> Dict[str, Any]:
        """
        Update multiple UT1 categories at once.

        Args:
            category_ids: List of category identifiers

        Returns:
            Dictionary with results
        """
        results = {
            'success': True,
            'updated_count': 0,
            'failed_count': 0,
            'total_domains': 0,
            'results': {}
        }

        for category_id in category_ids:
            success, message, domain_count = self.update_category(category_id)

            results['results'][category_id] = {
                'success': success,
                'message': message,
                'domains': domain_count
            }

            if success:
                results['updated_count'] += 1
                results['total_domains'] += domain_count
            else:
                results['failed_count'] += 1

        if results['failed_count'] > 0:
            results['success'] = False

        return results
