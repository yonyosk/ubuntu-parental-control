"""
Activity logging module for Ubuntu Parental Control.
Tracks and reports on internet usage and access attempts.
"""

import datetime
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class ActivityLogger:
    """Handles logging and reporting of internet activity."""
    
    def __init__(self, db):
        """Initialize with database instance."""
        self.db = db
    
    # Database setup is now handled by TinyDB automatically
    
    def log_activity(self, domain: str, action: str, 
                    category: str = None, 
                    client_ip: str = None, 
                    user_agent: str = None,
                    **details) -> bool:
        """
        Log an internet access attempt.
        
        Args:
            domain: The domain being accessed
            action: 'blocked', 'allowed', or 'exception'
            category: The category of the domain (if known)
            client_ip: IP address of the client
            user_agent: User agent string of the client
            **details: Additional details to store as JSON
            
        Returns:
            True if logging was successful, False otherwise
        """
        try:
            return self.db.log_activity(
                domain=domain,
                action=action,
                category=category,
                client_ip=client_ip,
                user_agent=user_agent,
                details=details
            )
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return False
    
    def record_usage_time(self, minutes: int = 1) -> bool:
        """
        Record internet usage time for the current day.
        
        Args:
            minutes: Number of minutes to add to today's usage
            
        Returns:
            True if successful, False otherwise
        """
        if minutes <= 0:
            return False
            
        try:
            today = datetime.date.today().isoformat()
            return self.db.record_daily_usage(today, minutes)
        except Exception as e:
            logger.error(f"Error recording usage time: {e}")
            return False
    
    def get_activity_logs(self, 
                         start_date: str = None, 
                         end_date: str = None,
                         domain: str = None,
                         action: str = None,
                         category: str = None,
                         limit: int = 100,
                         offset: int = 0) -> List[Dict]:
        """
        Retrieve activity logs with optional filtering.
        
        Args:
            start_date: Filter logs after this date (YYYY-MM-DD)
            end_date: Filter logs before this date (YYYY-MM-DD)
            domain: Filter by domain
            action: Filter by action ('blocked', 'allowed', 'exception')
            category: Filter by category
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of activity log entries as dictionaries
        """
        try:
            return self.db.get_activity_logs(
                start_date=start_date,
                end_date=end_date,
                domain=domain,
                action=action,
                category=category,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Error retrieving activity logs: {e}")
            return []
            
    def get_activity_count(self, 
                          start_date: str = None, 
                          end_date: str = None,
                          domain: str = None,
                          action: str = None,
                          category: str = None) -> int:
        """
        Get the total count of activity logs matching the filters.
        
        Args:
            start_date: Filter logs after this date (YYYY-MM-DD)
            end_date: Filter logs before this date (YYYY-MM-DD)
            domain: Filter by domain
            action: Filter by action ('blocked', 'allowed', 'exception')
            category: Filter by category
            
        Returns:
            Total number of matching log entries
        """
        try:
            from tinydb import Query
            
            # Validate dates if provided
            if start_date:
                self._validate_date(start_date)
            if end_date:
                self._validate_date(end_date)
                
            # Build query conditions
            Log = Query()
            conditions = []
            
            if start_date:
                start_timestamp = start_date + 'T00:00:00'
                conditions.append(Log.timestamp >= start_timestamp)
            
            if end_date:
                end_timestamp = end_date + 'T23:59:59'
                conditions.append(Log.timestamp <= end_timestamp)
                
            if domain:
                conditions.append(Log.domain == domain)
                
            if action:
                conditions.append(Log.action == action)
                
            if category:
                conditions.append(Log.category == category)
            
            # Count efficiently using TinyDB count
            with self.db._lock:
                if conditions:
                    # Combine all conditions with AND
                    query = conditions[0]
                    for condition in conditions[1:]:
                        query = query & condition
                    return len(self.db.activity_log.search(query))
                else:
                    return len(self.db.activity_log)
                
        except Exception as e:
            logger.error(f"Error counting activity logs: {e}")
            return 0
            
    def get_usage_statistics(self, 
                           start_date: str = None, 
                           end_date: str = None) -> Dict:
        """
        Get usage statistics for the specified date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary containing usage statistics
        """
        try:
            from datetime import datetime, timedelta
            from tinydb import Query
            
            # Set default date range if not provided
            if not start_date:
                start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
            if not end_date:
                end_date = datetime.now().date().isoformat()
            
            # Get daily usage data using proper database methods
            # Use the database's built-in filtering for activity logs
            blocked_logs = self.db.get_activity_logs(
                start_date=start_date,
                end_date=end_date,
                action='blocked',
                limit=10000  # Large limit to get all results
            )
            
            # Get daily usage records by querying each day in the range
            filtered_usage = []
            current_date = datetime.fromisoformat(start_date).date()
            end_date_obj = datetime.fromisoformat(end_date).date()
            
            while current_date <= end_date_obj:
                date_str = current_date.isoformat()
                usage_data = self.db.get_daily_usage(date_str)
                if usage_data and usage_data.get('minutes_used', 0) > 0:
                    filtered_usage.append(usage_data)
                current_date += timedelta(days=1)
            
            # Calculate summary statistics
            total_usage = sum(day.get('minutes_used', 0) for day in filtered_usage)
            total_domains = sum(day.get('domains_accessed', 0) for day in filtered_usage)
            total_blocks = len(blocked_logs)  # Count of blocked attempts
            
            # Get most active days
            active_days = sorted(
                filtered_usage, 
                key=lambda x: x.get('domains_accessed', 0), 
                reverse=True
            )[:5]
            
            # Count blocked domains
            domain_blocks = {}
            for log in blocked_logs:
                domain = log.get('domain', '')
                domain_blocks[domain] = domain_blocks.get(domain, 0) + 1
            
            # Get top blocked domains
            top_blocked = [
                {'domain': domain, 'count': count}
                for domain, count in sorted(domain_blocks.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            return {
                'period': {
                    'start': start_date,
                    'end': end_date
                },
                'total_usage_minutes': total_usage,
                'total_domains_accessed': total_domains,
                'total_blocks': total_blocks,
                'daily_stats': filtered_usage,
                'top_active_days': [
                    {'date': day.get('date'), 'domains': day.get('domains_accessed', 0)} 
                    for day in active_days
                ],
                'top_blocked_domains': top_blocked
            }
                
        except Exception as e:
            logger.error(f"Error getting usage statistics: {e}")
            return {}
    
    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Remove old log entries to prevent database bloat.
        
        Args:
            days_to_keep: Number of days of logs to keep
            
        Returns:
            Number of rows deleted
        """
        try:
            from datetime import datetime, timedelta
            from tinydb import Query
            
            cutoff_date = (datetime.now().date() - timedelta(days=days_to_keep)).isoformat()
            cutoff_timestamp = cutoff_date + 'T23:59:59'
            
            # Use the database's thread-safe methods instead of direct access
            rows_deleted = 0
            
            # Delete old activity logs using proper database methods
            # Get logs older than cutoff date first
            old_logs = self.db.get_activity_logs(
                end_date=cutoff_date,
                limit=10000  # Large limit to get all old logs
            )
            
            # The database doesn't have a direct delete method for activity logs,
            # so we need to work with the TinyDB tables directly but safely
            with self.db._lock:
                # Delete old activity logs
                Log = Query()
                deleted_activity = self.db.activity_log.remove(
                    Log.timestamp < cutoff_timestamp
                )
                rows_deleted += len(deleted_activity)
                
                # Clean up daily usage older than cutoff
                Usage = Query()
                deleted_usage = self.db.daily_usage.remove(
                    Usage.date < cutoff_date
                )
                rows_deleted += len(deleted_usage)
            
            logger.info(f"Cleaned up {rows_deleted} old log entries older than {cutoff_date}")
            return rows_deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return 0
    
    def _validate_date(self, date_str: str) -> bool:
        """
        Validate date string format (YYYY-MM-DD).
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError as e:
            raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD")
    
    def get_daily_activity_summary(self, date: str = None) -> Dict:
        """
        Get a comprehensive summary of activity for a specific day.
        
        Args:
            date: Date in YYYY-MM-DD format. Defaults to today.
            
        Returns:
            Dictionary with daily activity summary
        """
        try:
            if not date:
                date = datetime.date.today().isoformat()
            else:
                self._validate_date(date)
            
            # Get all logs for the day
            day_logs = self.get_activity_logs(
                start_date=date,
                end_date=date,
                limit=10000
            )
            
            # Get usage data
            usage_data = self.db.get_daily_usage(date)
            
            # Calculate statistics
            total_attempts = len(day_logs)
            blocked_attempts = len([log for log in day_logs if log.get('action') == 'blocked'])
            allowed_attempts = len([log for log in day_logs if log.get('action') == 'allowed'])
            
            # Count unique domains
            unique_domains = set(log.get('domain', '') for log in day_logs if log.get('domain'))
            
            # Count by category
            category_stats = {}
            for log in day_logs:
                category = log.get('category', 'unknown')
                if category not in category_stats:
                    category_stats[category] = {'total': 0, 'blocked': 0, 'allowed': 0}
                category_stats[category]['total'] += 1
                category_stats[category][log.get('action', 'unknown')] += 1
            
            return {
                'date': date,
                'total_attempts': total_attempts,
                'blocked_attempts': blocked_attempts,
                'allowed_attempts': allowed_attempts,
                'unique_domains': len(unique_domains),
                'usage_minutes': usage_data.get('minutes_used', 0) if usage_data else 0,
                'category_breakdown': category_stats,
                'top_domains': [
                    {'domain': domain, 'attempts': len([log for log in day_logs if log.get('domain') == domain])}
                    for domain in list(unique_domains)[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting daily activity summary for {date}: {e}")
            return {}
