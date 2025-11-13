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

print("\nAll tables in database:")
for table_name in data.keys():
    if isinstance(data[table_name], list):
        count = len(data[table_name])
        print(f"  {table_name}: {count:,} records")
        if count > 10000:
            print(f"    ⚠ Very large table ({count} records)")
    else:
        print(f"  {table_name}: {type(data[table_name])}")

# Show time schedules
print("\nTime Schedules:")
schedules = data.get('time_schedules', [])
if not schedules:
    print("  No schedules found")
else:
    print(f"  Found {len(schedules)} schedules")
    print(f"  Data type: {type(schedules)}")
    for i, s in enumerate(schedules, 1):
        print(f"\n  Schedule {i}:")
        print(f"    Type: {type(s)}")

        if isinstance(s, dict):
            name = s.get('name', 'Unknown')
            start = s.get('start_time', '?')
            end = s.get('end_time', '?')
            days = s.get('days', [])
            active = '✓' if s.get('is_active') else '✗'
            print(f"    [{active}] {name}")
            print(f"    Time: {start} - {end}")
            print(f"    Days: {days}")
            print(f"    ID: {s.get('id')}")
        elif isinstance(s, str):
            print(f"    ⚠ WARNING: Schedule stored as STRING (corrupted)")
            print(f"    Value: {s[:200]}...")  # First 200 chars
        else:
            print(f"    ⚠ WARNING: Unknown data type")
            print(f"    Value: {str(s)[:200]}...")

# Check for duplicates (only if schedules are dicts)
print("\nChecking for duplicate schedules...")
try:
    if schedules and isinstance(schedules[0], dict):
        names = [s.get('name') for s in schedules if isinstance(s, dict)]
        if len(names) != len(set(names)):
            print("  ⚠ WARNING: Duplicate schedule names found")
            from collections import Counter
            duplicates = [name for name, count in Counter(names).items() if count > 1]
            for dup in duplicates:
                print(f"    - '{dup}' appears multiple times")
        else:
            print("  No duplicates found")
    else:
        print("  Cannot check for duplicates (data corrupted)")
except Exception as e:
    print(f"  Error checking duplicates: {e}")

# Estimate what's taking up space
print("\nEstimating space usage:")
for table_name in data.keys():
    if isinstance(data[table_name], list):
        table_json = json.dumps(data[table_name])
        table_size_mb = len(table_json) / (1024 * 1024)
        table_size_kb = len(table_json) / 1024

        if table_size_mb >= 1:
            print(f"  {table_name}: {table_size_mb:.2f} MB ⚠")
        elif table_size_kb >= 100:
            print(f"  {table_name}: {table_size_kb:.2f} KB")
        else:
            print(f"  {table_name}: {len(table_json)} bytes")

        # If a table is very large, check if it's a single huge record
        if table_size_mb > 1 and len(data[table_name]) < 100:
            print(f"    ⚠ WARNING: Large table with few records - checking individual sizes...")
            for idx, record in enumerate(data[table_name][:5]):  # Check first 5
                record_size = len(json.dumps(record))
                if record_size > 100000:  # > 100KB
                    print(f"      Record {idx}: {record_size / 1024:.2f} KB (HUGE!)")
                    if isinstance(record, dict):
                        # Show which fields are large
                        for key, value in record.items():
                            field_size = len(json.dumps(value))
                            if field_size > 50000:  # > 50KB
                                print(f"        Field '{key}': {field_size / 1024:.2f} KB")

print("\n" + "="*60)
print("Diagnostic complete")
