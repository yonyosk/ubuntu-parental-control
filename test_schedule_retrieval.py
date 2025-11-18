#!/usr/bin/env python3
"""
Test what get_time_schedules actually returns
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parental_control.database import ParentalControlDB
from parental_control.time_management import TimeManager

print("="*60)
print("TESTING get_time_schedules() METHOD")
print("="*60)

db = ParentalControlDB()
tm = TimeManager(db)

print("\n1. Testing db.get_time_schedules(active_only=False):")
schedules = db.get_time_schedules(active_only=False)
print(f"   Type: {type(schedules)}")
print(f"   Count: {len(schedules)}")

if schedules:
    print("\n   Schedules returned:")
    for i, s in enumerate(schedules, 1):
        print(f"\n   Schedule {i}:")
        print(f"     Type: {type(s)}")
        if isinstance(s, dict):
            print(f"     Keys: {s.keys()}")
            print(f"     Name: {s.get('name')}")
            print(f"     Time: {s.get('start_time')} - {s.get('end_time')}")
            print(f"     Days: {s.get('days')}")
        else:
            print(f"     Value: {s}")
else:
    print("   NO SCHEDULES RETURNED!")

print("\n2. Testing tm.get_schedules(active_only=False):")
schedules2 = tm.get_schedules(active_only=False)
print(f"   Type: {type(schedules2)}")
print(f"   Count: {len(schedules2)}")

if schedules2:
    print("\n   Schedules returned:")
    for i, s in enumerate(schedules2, 1):
        print(f"\n   Schedule {i}:")
        print(f"     Name: {s.get('name') if isinstance(s, dict) else 'ERROR'}")
else:
    print("   NO SCHEDULES RETURNED!")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
