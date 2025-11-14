#!/usr/bin/env python3
"""
Diagnose database issues - TinyDB format aware
"""
import sys
import json
from pathlib import Path

DB_PATH = '/var/lib/ubuntu-parental/control.json'

print("="*60)
print("DATABASE DIAGNOSTIC (TinyDB Format)")
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

# Load database
print("\nLoading database...")
try:
    with open(DB_PATH, 'r') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON: {e}")
    sys.exit(1)

# Analyze all tables
print("\nAll tables in database:")
total_records = 0
for table_name in sorted(data.keys()):
    table_data = data[table_name]

    if isinstance(table_data, dict):
        count = len(table_data)
        total_records += count
        print(f"  {table_name}: {count:,} records")
        if count > 10000:
            print(f"    ⚠ Very large table!")
    elif isinstance(table_data, list):
        count = len(table_data)
        total_records += count
        print(f"  {table_name}: {count:,} records (list format)")
    else:
        print(f"  {table_name}: {type(table_data)}")

print(f"\nTotal records across all tables: {total_records:,}")

# Analyze space usage
print("\nSpace usage by table:")
for table_name in sorted(data.keys()):
    table_json = json.dumps(data[table_name])
    size_mb = len(table_json) / (1024 * 1024)
    size_kb = len(table_json) / 1024

    if size_mb >= 1:
        print(f"  {table_name}: {size_mb:.2f} MB ⚠ LARGE")
    elif size_kb >= 100:
        print(f"  {table_name}: {size_kb:.2f} KB")
    else:
        print(f"  {table_name}: {len(table_json)} bytes")

    # For large tables, analyze individual records
    if size_mb > 1:
        table_data = data[table_name]
        if isinstance(table_data, dict):
            print(f"    Analyzing large records in {table_name}...")
            # Check first 5 records
            for key in list(table_data.keys())[:5]:
                record = table_data[key]
                record_size = len(json.dumps(record))
                if record_size > 100000:  # > 100KB
                    print(f"      Record ID {key}: {record_size / 1024:.2f} KB (HUGE!)")
                    if isinstance(record, dict):
                        # Find large fields
                        for field, value in record.items():
                            field_size = len(json.dumps(value))
                            if field_size > 50000:  # > 50KB
                                print(f"        Field '{field}': {field_size / 1024:.2f} KB")
                                # If it's a list, show count
                                if isinstance(value, list):
                                    print(f"          (list with {len(value)} items)")

# Show time schedules
print("\n" + "="*60)
print("TIME SCHEDULES DETAIL")
print("="*60)

schedules_data = data.get('time_schedules', {})

if isinstance(schedules_data, dict):
    schedules = list(schedules_data.values())
    print(f"Found {len(schedules)} schedules")

    for schedule_id, schedule in schedules_data.items():
        print(f"\nSchedule ID: {schedule_id}")
        if isinstance(schedule, dict):
            print(f"  Name: {schedule.get('name', 'N/A')}")
            print(f"  Time: {schedule.get('start_time', '?')} - {schedule.get('end_time', '?')}")
            print(f"  Days: {schedule.get('days', [])}")
            print(f"  Active: {schedule.get('is_active', False)}")
            print(f"  Created: {schedule.get('created_at', 'N/A')}")
        else:
            print(f"  ⚠ WARNING: Invalid schedule data type: {type(schedule)}")
            print(f"  Value: {str(schedule)[:200]}")
else:
    print(f"⚠ WARNING: Schedules stored in unexpected format: {type(schedules_data)}")

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)

# Recommendations
if size_mb > 50:
    print("\n⚠ CRITICAL: Database is very large (>50MB)")
    print("  Recommendations:")
    print("  1. Check for data accumulation bugs")
    print("  2. Implement automatic cleanup of old records")
    print("  3. Consider archiving old data")
