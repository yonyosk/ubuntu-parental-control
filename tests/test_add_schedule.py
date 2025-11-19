#!/usr/bin/env python3
"""
Test adding a schedule directly (simulating web form submission)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parental_control.parental_control import ParentalControl

print("="*60)
print("TEST: Adding Schedule Directly")
print("="*60)

pc = ParentalControl()

print("\nBefore adding:")
schedules_before = pc.time_manager.get_schedules(active_only=False)
print(f"  Schedule count: {len(schedules_before)}")

print("\nAdding new schedule 'Evening Test'...")
success = pc.time_manager.add_schedule(
    name="Evening Test",
    start_time="18:00",
    end_time="21:00",
    days=[0],  # Monday
    is_active=True
)
print(f"  Add result: {success}")

print("\nAfter adding:")
schedules_after = pc.time_manager.get_schedules(active_only=False)
print(f"  Schedule count: {len(schedules_after)}")

if len(schedules_after) > len(schedules_before):
    print("\n✓ SUCCESS: Schedule was added")
    new_schedule = schedules_after[-1]
    print(f"  Name: {new_schedule.get('name')}")
    print(f"  Time: {new_schedule.get('start_time')} - {new_schedule.get('end_time')}")
else:
    print("\n✗ FAILURE: Schedule was not added")

# Cleanup
if success:
    print("\nCleaning up test schedule...")
    # Find and remove the test schedule
    for s in schedules_after:
        if s.get('name') == "Evening Test":
            pc.db.delete_time_schedule(s.get('id'))
            print("  ✓ Test schedule removed")
            break
