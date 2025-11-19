#!/usr/bin/env python3
"""
Debug script to simulate what the web interface does
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parental_control.parental_control import ParentalControl

print("="*60)
print("SIMULATING WEB INTERFACE /time-management ROUTE")
print("="*60)

try:
    print("\n1. Creating ParentalControl instance...")
    pc = ParentalControl()
    print("   ✓ ParentalControl created")

    print("\n2. Getting schedules...")
    schedules = pc.time_manager.get_schedules(active_only=False)
    print(f"   Type: {type(schedules)}")
    print(f"   Count: {len(schedules)}")

    print("\n3. Schedule details:")
    if schedules:
        for i, s in enumerate(schedules, 1):
            print(f"\n   Schedule {i}:")
            print(f"     Name: {s.get('name')}")
            print(f"     Time: {s.get('start_time')} - {s.get('end_time')}")
            print(f"     Days: {s.get('days')}")
            print(f"     Active: {s.get('is_active')}")
    else:
        print("   ⚠ NO SCHEDULES RETURNED")

    print("\n4. Getting today's usage...")
    today_usage = pc.time_manager.get_todays_usage()
    print(f"   Today's usage: {today_usage} minutes")

    print("\n5. Getting daily limit...")
    daily_limit = pc.time_manager.get_daily_limit()
    print(f"   Daily limit: {daily_limit}")

    print("\n6. Getting access status...")
    is_allowed, status_reason = pc.time_manager.is_access_allowed()
    print(f"   Allowed: {is_allowed}")
    print(f"   Reason: {status_reason}")

    print("\n7. What would be passed to template:")
    print(f"   schedules: {len(schedules)} items")
    print(f"   today_usage: {today_usage}")
    print(f"   daily_limit: {daily_limit}")
    print(f"   is_allowed: {is_allowed}")
    print(f"   status_reason: {status_reason}")

    print("\n" + "="*60)
    print("✓ ALL DATA RETRIEVED SUCCESSFULLY")
    print("="*60)

    if not schedules:
        print("\n⚠ WARNING: Schedules list is empty!")
        print("  This would cause the web interface to show 'No schedules configured'")
    else:
        print(f"\n✓ SUCCESS: {len(schedules)} schedules would be displayed")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
