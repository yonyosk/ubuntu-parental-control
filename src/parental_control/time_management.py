"""
Time management module for Ubuntu Parental Control.
Handles internet access schedules and usage limits.
"""

import datetime
import time
import logging
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class TimeManager:
    """Manages time-based internet access restrictions."""
    
    def __init__(self, db):
        """Initialize with database instance."""
        self.db = db
    
    # Database setup is now handled by TinyDB automatically
    
    # Schedule management methods
    def add_schedule(self, name: str, start_time: str, end_time: str, 
                     days: List[int], is_active: bool = True) -> bool:
        """Add a new internet access schedule."""
        try:
            # Validate time format
            self._parse_time(start_time)
            self._parse_time(end_time)
            
            # Validate days (0-6, Monday-Sunday)
            if not all(0 <= day <= 6 for day in days):
                logger.error("Invalid day values. Must be 0-6 (Monday-Sunday)")
                return False
            
            return self.db.add_time_schedule(
                name=name,
                start_time=start_time,
                end_time=end_time,
                days=days,
                is_active=is_active
            )
        except Exception as e:
            logger.error(f"Error adding schedule: {e}")
            return False
    
    def get_schedules(self, active_only: bool = True) -> List[Dict]:
        """Get all schedules."""
        try:
            return self.db.get_time_schedules(active_only=active_only)
        except Exception as e:
            logger.error(f"Error getting schedules: {e}")
            return []
    
    # Usage limit methods
    def set_daily_limit(self, minutes: int, reset_time: str = "00:00") -> bool:
        """Set daily internet usage limit."""
        try:
            return self.db.set_daily_usage_limit(minutes, reset_time)
        except Exception as e:
            logger.error(f"Error setting daily limit: {e}")
            return False
    
    def get_daily_limit(self) -> Optional[Dict]:
        """Get current daily usage limit."""
        try:
            return self.db.get_daily_usage_limit()
        except Exception as e:
            logger.error(f"Error getting daily limit: {e}")
            return None
    
    # Usage tracking methods
    def record_usage(self, minutes: int = 1) -> bool:
        """Record internet usage time."""
        today = datetime.date.today().isoformat()
        
        try:
            return self.db.record_daily_usage(today, minutes)
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
            return False
    
    def get_todays_usage(self) -> int:
        """Get today's internet usage in minutes."""
        today = datetime.date.today().isoformat()
        
        try:
            usage_data = self.db.get_daily_usage(today)
            # Return just the minutes if it's a dict, otherwise return the value
            if isinstance(usage_data, dict):
                return usage_data.get('minutes_used', 0)
            return usage_data
        except Exception as e:
            logger.error(f"Error getting today's usage: {e}")
            return 0
    
    # Access control methods
    def is_access_allowed(self) -> Tuple[bool, str]:
        """
        Check if internet access is currently allowed.
        
        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check time-based schedules
        if not self._check_schedules():
            return False, "Outside of allowed schedule"
        
        # Check daily usage limit
        limit = self.get_daily_limit()
        if limit and limit['is_active']:
            if self.get_todays_usage() >= limit['time_limit_minutes']:
                return False, "Daily usage limit reached"
        
        return True, "Access allowed"
    
    def _check_schedules(self) -> bool:
        """Check if current time is within any active schedule."""
        now = datetime.datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        try:
            schedules = self.db.get_time_schedules(active_only=True)
            
            for schedule in schedules:
                # Check if current day is in the schedule
                if current_weekday in schedule.get('days', []):
                    if self._is_time_in_schedule(current_time, schedule):
                        return True
                        
                # Check previous day for overnight schedules
                # If it's Monday (0), check Sunday (6). Otherwise, check previous day.
                prev_weekday = 6 if current_weekday == 0 else current_weekday - 1
                if prev_weekday in schedule.get('days', []):
                    if self._is_time_in_overnight_schedule(current_time, schedule):
                        return True
            
            return False
                
        except Exception as e:
            logger.error(f"Error checking schedules: {e}")
            return True  # Default to allowing access on error
    
    def _parse_time(self, time_str: str) -> datetime.time:
        """Parse time string to datetime.time object."""
        try:
            return datetime.datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            logger.error(f"Invalid time format: {time_str}")
            return datetime.time(0, 0)  # Default to midnight
    
    def _is_time_in_schedule(self, current_time: datetime.time, schedule: Dict) -> bool:
        """Check if current time is within schedule for the same day."""
        start_time = self._parse_time(schedule['start_time'])
        end_time = self._parse_time(schedule['end_time'])
        
        # Normal schedule (doesn't cross midnight)
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            # Overnight schedule (crosses midnight)
            # e.g., 22:00 to 06:00 - current day portion (22:00 to 23:59)
            return current_time >= start_time
    
    def _is_time_in_overnight_schedule(self, current_time: datetime.time, schedule: Dict) -> bool:
        """Check if current time is within an overnight schedule from previous day."""
        start_time = self._parse_time(schedule['start_time'])
        end_time = self._parse_time(schedule['end_time'])
        
        # Only check if this is an overnight schedule
        if start_time > end_time:
            # Check the next day portion (00:00 to end_time)
            return current_time <= end_time
        
        return False
