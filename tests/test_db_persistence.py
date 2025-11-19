#!/usr/bin/env python3
"""
Quick test to verify database write/read operations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parental_control.database import ParentalControlDB
import time

print("="*60)
print("DATABASE WRITE/READ TEST")
print("="*60)

# Test 1: Write a schedule
print("\n1. Creating database instance and adding schedule...")
db1 = ParentalControlDB()
success = db1.add_time_schedule(
    name="Test Schedule DB Check",
    start_time="10:00",
    end_time="11:00",
    days=[1, 2, 3],
    is_active=True
)
print(f"   Add schedule result: {success}")

# Test 2: Read with same instance
print("\n2. Reading schedules with SAME database instance...")
schedules1 = db1.get_time_schedules(active_only=False)
found1 = any(s.get('name') == "Test Schedule DB Check" for s in schedules1)
print(f"   Found schedule: {found1}")
print(f"   Total schedules: {len(schedules1)}")

# Test 3: Read with NEW instance (simulates page refresh)
print("\n3. Reading schedules with NEW database instance (simulates page refresh)...")
db2 = ParentalControlDB()
schedules2 = db2.get_time_schedules(active_only=False)
found2 = any(s.get('name') == "Test Schedule DB Check" for s in schedules2)
print(f"   Found schedule: {found2}")
print(f"   Total schedules: {len(schedules2)}")

if found2:
    print("\n✓ SUCCESS: Database persistence is working!")
else:
    print("\n✗ FAILURE: Schedule not found after creating new DB instance")
    print("\n   This means the flush isn't working properly.")
    print("   Checking what's in the schedules...")
    for s in schedules2:
        print(f"   - {s.get('name')}")

# Cleanup
print("\n4. Cleaning up test schedule...")
for s in schedules2:
    if s.get('name') == "Test Schedule DB Check":
        db2.delete_time_schedule(s.get('id'))
        print("   Cleaned up")

print("\nTest complete!")
