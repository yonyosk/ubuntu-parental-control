"""
Input validation and sanitization utilities for Ubuntu Parental Control.
"""

import re
import logging
from typing import Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

class InputValidator:
    """Handles input validation and sanitization."""
    
    # Domain regex pattern (more restrictive)
    DOMAIN_PATTERN = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    )
    
    # IP address pattern
    IP_PATTERN = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )
    
    # Time pattern (HH:MM)
    TIME_PATTERN = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    
    # Safe string pattern (alphanumeric, spaces, basic punctuation)
    SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.()]+$')
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize a general string input."""
        if not isinstance(value, str):
            raise ValidationError("Input must be a string")
        
        # Strip whitespace
        value = value.strip()
        
        # Check length
        if len(value) > max_length:
            raise ValidationError(f"Input too long (max {max_length} characters)")
        
        # Remove control characters and most special chars
        # Allow only alphanumeric, spaces, and basic punctuation
        sanitized = re.sub(r'[^\w\s\-_.()@]', '', value)
        
        return sanitized
    
    @staticmethod
    def validate_domain(domain: str) -> str:
        """Validate and sanitize a domain name."""
        if not isinstance(domain, str):
            raise ValidationError("Domain must be a string")
        
        # Strip whitespace and convert to lowercase
        domain = domain.strip().lower()
        
        if not domain:
            raise ValidationError("Domain cannot be empty")
        
        if len(domain) > 253:
            raise ValidationError("Domain name too long")
        
        # Remove protocol if present
        if '://' in domain:
            try:
                parsed = urlparse(f"http://{domain}" if not domain.startswith(('http://', 'https://')) else domain)
                domain = parsed.netloc or parsed.path.split('/')[0]
            except Exception:
                raise ValidationError("Invalid URL format")
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove path if present
        if '/' in domain:
            domain = domain.split('/')[0]
        
        # Remove port if present
        if ':' in domain and not InputValidator.IP_PATTERN.match(domain):
            domain = domain.split(':')[0]
        
        # Validate domain format
        if not InputValidator.DOMAIN_PATTERN.match(domain):
            raise ValidationError("Invalid domain format")
        
        # Additional checks
        if domain.startswith('.') or domain.endswith('.'):
            raise ValidationError("Domain cannot start or end with a dot")
        
        if '..' in domain:
            raise ValidationError("Domain cannot contain consecutive dots")
        
        return domain
    
    @staticmethod
    def validate_ip_address(ip: str) -> str:
        """Validate an IP address."""
        if not isinstance(ip, str):
            raise ValidationError("IP address must be a string")
        
        ip = ip.strip()
        
        if not InputValidator.IP_PATTERN.match(ip):
            raise ValidationError("Invalid IP address format")
        
        # Additional validation - check ranges
        parts = ip.split('.')
        for part in parts:
            num = int(part)
            if num < 0 or num > 255:
                raise ValidationError("Invalid IP address range")
        
        return ip
    
    @staticmethod
    def validate_time(time_str: str) -> str:
        """Validate time format (HH:MM)."""
        if not isinstance(time_str, str):
            raise ValidationError("Time must be a string")
        
        time_str = time_str.strip()
        
        if not InputValidator.TIME_PATTERN.match(time_str):
            raise ValidationError("Invalid time format (use HH:MM)")
        
        return time_str
    
    @staticmethod
    def validate_integer(value, min_val: int = None, max_val: int = None) -> int:
        """Validate an integer value."""
        try:
            if isinstance(value, str):
                value = value.strip()
            int_val = int(value)
        except (ValueError, TypeError):
            raise ValidationError("Invalid integer value")
        
        if min_val is not None and int_val < min_val:
            raise ValidationError(f"Value must be at least {min_val}")
        
        if max_val is not None and int_val > max_val:
            raise ValidationError(f"Value must be at most {max_val}")
        
        return int_val
    
    @staticmethod
    def validate_category_name(category: str) -> str:
        """Validate a blacklist category name."""
        if not isinstance(category, str):
            raise ValidationError("Category name must be a string")
        
        category = category.strip().lower()
        
        if not category:
            raise ValidationError("Category name cannot be empty")
        
        if len(category) > 50:
            raise ValidationError("Category name too long")
        
        # Allow only alphanumeric chars, hyphens, and underscores
        if not re.match(r'^[a-z0-9_-]+$', category):
            raise ValidationError("Category name contains invalid characters")
        
        return category
    
    @staticmethod
    def validate_schedule_name(name: str) -> str:
        """Validate a schedule name."""
        if not isinstance(name, str):
            raise ValidationError("Schedule name must be a string")
        
        name = name.strip()
        
        if not name:
            raise ValidationError("Schedule name cannot be empty")
        
        if len(name) > 100:
            raise ValidationError("Schedule name too long")
        
        # Allow alphanumeric, spaces, and basic punctuation
        if not InputValidator.SAFE_STRING_PATTERN.match(name):
            raise ValidationError("Schedule name contains invalid characters")
        
        return name
    
    @staticmethod
    def validate_day_numbers(days: List[int]) -> List[int]:
        """Validate day numbers (0-6, Monday-Sunday)."""
        if not isinstance(days, list):
            raise ValidationError("Days must be a list")
        
        if not days:
            raise ValidationError("At least one day must be selected")
        
        valid_days = []
        for day in days:
            try:
                day_int = int(day)
                if day_int < 0 or day_int > 6:
                    raise ValidationError("Invalid day number (must be 0-6)")
                valid_days.append(day_int)
            except (ValueError, TypeError):
                raise ValidationError("Day numbers must be integers")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_days = []
        for day in valid_days:
            if day not in seen:
                seen.add(day)
                unique_days.append(day)
        
        return unique_days
    
    @staticmethod
    def sanitize_sql_like_string(value: str) -> str:
        """Sanitize strings that might be used in SQL LIKE queries."""
        if not isinstance(value, str):
            raise ValidationError("Input must be a string")
        
        # Escape SQL wildcards and special characters
        value = value.replace('%', '\\%')
        value = value.replace('_', '\\_')
        value = value.replace("'", "''")
        value = value.replace('"', '""')
        
        return value
    
    @staticmethod
    def validate_dns_type(dns_type: str) -> str:
        """Validate DNS type selection."""
        valid_types = ['system', 'opendns', 'cloudflare', 'google', 'custom']
        
        if not isinstance(dns_type, str):
            raise ValidationError("DNS type must be a string")
        
        dns_type = dns_type.strip().lower()
        
        if dns_type not in valid_types:
            raise ValidationError(f"Invalid DNS type. Must be one of: {', '.join(valid_types)}")
        
        return dns_type