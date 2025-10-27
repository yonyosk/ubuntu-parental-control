# src/parental_control/__init__.py
import os
from pathlib import Path

# Global configuration
CONFIG_DIR = '/etc/ubuntu-parental'
LOG_DIR = '/var/log/ubuntu-parental'
DB_DIR = '/var/lib/ubuntu-parental'

# Ensure directories exist
for directory in [CONFIG_DIR, LOG_DIR, DB_DIR]:
    os.makedirs(directory, exist_ok=True)

# Database path
DB_PATH = Path(DB_DIR) / 'control.db'

# Log file path
LOG_PATH = Path(LOG_DIR) / 'access.log'

# Version
__version__ = '1.0.0'
