#!/usr/bin/env python3
"""
Diagnose database issues - check file size and contents
"""
import sys
import json
from pathlib import Path

DB_PATH = '/var/lib/ubuntu-parental/control.json'

print("="*60)
print("DATABASE DIAGNOSTIC")
print("="*60)

# Check file size
db_file = Path(DB_PATH)
if not db_file.exists():
    print(f"ERROR: Database file doesn't exist: {DB_PATH}")
    sys.exit(1)

size_bytes = db_file.stat().st_size
size_mb = size_bytes / (1024 * 1024)
print(f"\nFile size: {size_bytes:,} bytes ({size_mb:.2f} MB)")

if size_mb > 10:
    print("⚠ WARNING: Database file is very large (>10MB)!")
    print("  This suggests a data accumulation issue.")

# Load and analyze contents
print("\nLoading database...")
try:
    with open(DB_PATH, 'r') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON: {e}")
    sys.exit(1)

print("\nTable sizes:")
for table_name in ['time_schedules', 'blocked_sites', 'activity_log', 'daily_usage', 'settings']:
    if table_name in data:
        count = len(data[table_name])
        print(f"  {table_name}: {count:,} records")
        if table_name == 'activity_log' and count > 10000:
            print(f"    ⚠ Activity log is very large ({count} records)")

# Show time schedules
print("\nTime Schedules:")
schedules = data.get('time_schedules', [])
if not schedules:
    print("  No schedules found")
else:
    for i, s in enumerate(schedules, 1):
        name = s.get('name', 'Unknown')
        start = s.get('start_time', '?')
        end = s.get('end_time', '?')
        days = s.get('days', [])
        active = '✓' if s.get('is_active') else '✗'
        print(f"  {i}. [{active}] {name}")
        print(f"     Time: {start} - {end}")
        print(f"     Days: {days}")
        print(f"     ID: {s.get('id')}")

# Check for duplicates
print("\nChecking for duplicate schedules...")
names = [s.get('name') for s in schedules]
if len(names) != len(set(names)):
    print("  ⚠ WARNING: Duplicate schedule names found")
    from collections import Counter
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    for dup in duplicates:
        print(f"    - '{dup}' appears multiple times")
else:
    print("  No duplicates found")

# Estimate what's taking up space
print("\nEstimating space usage:")
for table_name in data.keys():
    if isinstance(data[table_name], list):
        table_json = json.dumps(data[table_name])
        table_size_mb = len(table_json) / (1024 * 1024)
        print(f"  {table_name}: {table_size_mb:.2f} MB")

print("\n" + "="*60)
print("Diagnostic complete")
