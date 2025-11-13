#!/usr/bin/env python3
"""
Test script for time restrictions in Ubuntu Parental Control.
This script helps verify that time restrictions are working correctly.
"""

import sys
import os
import datetime
import requests
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from parental_control.database import Database
from parental_control.time_management import TimeManager

class TimeRestrictionTester:
    """Test time restriction functionality."""

    def __init__(self):
        self.db = Database()
        self.time_manager = TimeManager(self.db)

    def print_header(self, text):
        """Print a formatted header."""
        print("\n" + "="*60)
        print(f"  {text}")
        print("="*60)

    def print_section(self, text):
        """Print a formatted section."""
        print(f"\n--- {text} ---")

    def show_current_status(self):
        """Display current time and access status."""
        self.print_header("CURRENT STATUS")

        now = datetime.datetime.now()
        print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Day of week: {now.strftime('%A')} (weekday={now.weekday()})")

        is_allowed, reason = self.time_manager.is_access_allowed()
        status = "✓ ALLOWED" if is_allowed else "✗ BLOCKED"
        print(f"\nAccess Status: {status}")
        print(f"Reason: {reason}")

        # Show usage
        usage = self.time_manager.get_todays_usage()
        limit = self.time_manager.get_daily_limit()
        print(f"\nToday's usage: {usage} minutes")
        if limit and limit['is_active']:
            print(f"Daily limit: {limit['time_limit_minutes']} minutes")
            remaining = limit['time_limit_minutes'] - usage
            print(f"Remaining: {remaining} minutes")

    def show_schedules(self):
        """Display all time schedules."""
        self.print_section("Active Time Schedules")

        schedules = self.time_manager.get_schedules(active_only=False)
        if not schedules:
            print("No schedules configured.")
            return

        days_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

        for idx, schedule in enumerate(schedules, 1):
            active = "✓" if schedule.get('is_active') else "✗"
            days = ", ".join([days_map[d] for d in sorted(schedule.get('days', []))])
            print(f"\n{idx}. [{active}] {schedule.get('name')}")
            print(f"   Time: {schedule.get('start_time')} - {schedule.get('end_time')}")
            print(f"   Days: {days}")

    def add_test_schedule(self, block_now=True):
        """Add a test schedule that blocks or allows current time."""
        self.print_section("Adding Test Schedule")

        now = datetime.datetime.now()
        current_weekday = now.weekday()

        if block_now:
            # Create a schedule that does NOT include current time (to block)
            # Set allowed time 2 hours from now for 1 hour
            start = (now + datetime.timedelta(hours=2)).strftime('%H:%M')
            end = (now + datetime.timedelta(hours=3)).strftime('%H:%M')
            name = "Test Schedule (Should Block Now)"
            print(f"Creating schedule that EXCLUDES current time...")
        else:
            # Create a schedule that includes current time (to allow)
            # Set allowed time from 1 hour ago to 1 hour from now
            start = (now - datetime.timedelta(hours=1)).strftime('%H:%M')
            end = (now + datetime.timedelta(hours=1)).strftime('%H:%M')
            name = "Test Schedule (Should Allow Now)"
            print(f"Creating schedule that INCLUDES current time...")

        days = [current_weekday]  # Only today

        success = self.time_manager.add_schedule(
            name=name,
            start_time=start,
            end_time=end,
            days=days,
            is_active=True
        )

        if success:
            print(f"✓ Added: {name}")
            print(f"  Time: {start} - {end}")
            print(f"  Days: {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][current_weekday]}")
            return True
        else:
            print(f"✗ Failed to add schedule")
            return False

    def test_blocking_server(self):
        """Test if the blocking server is enforcing time restrictions."""
        self.print_section("Testing Blocking Server")

        # Check if server is running
        try:
            response = requests.get('http://localhost:8080',
                                   headers={'Host': 'www.example.com'},
                                   timeout=5)
            print(f"✓ Blocking server is running (port 8080)")
            print(f"  Status code: {response.status_code}")

            # Check if we got blocked or allowed
            if response.status_code == 403:
                print(f"  Result: REQUEST BLOCKED")
            elif response.status_code == 200 and 'blocked' in response.text.lower():
                print(f"  Result: REQUEST BLOCKED (block page shown)")
            else:
                print(f"  Result: REQUEST ALLOWED")

            return True
        except requests.exceptions.ConnectionError:
            print(f"✗ Blocking server is NOT running on port 8080")
            print(f"  Start it with: sudo python3 -m parental_control.blocking_server")
            return False
        except Exception as e:
            print(f"✗ Error testing blocking server: {e}")
            return False

    def test_web_interface(self):
        """Test if the web interface is accessible."""
        self.print_section("Testing Web Interface")

        try:
            response = requests.get('http://localhost:5000', timeout=5)
            print(f"✓ Web interface is running (port 5000)")
            print(f"  Access at: http://localhost:5000")
            return True
        except requests.exceptions.ConnectionError:
            print(f"✗ Web interface is NOT running on port 5000")
            print(f"  Start it with: sudo python3 src/app.py")
            return False
        except Exception as e:
            print(f"✗ Error testing web interface: {e}")
            return False

    def cleanup_test_schedules(self):
        """Remove test schedules."""
        self.print_section("Cleanup")

        schedules = self.time_manager.get_schedules(active_only=False)
        removed = 0

        for schedule in schedules:
            if 'Test Schedule' in schedule.get('name', ''):
                # Delete via database
                self.db.delete_time_schedule(schedule.get('id'))
                print(f"✓ Removed: {schedule.get('name')}")
                removed += 1

        if removed == 0:
            print("No test schedules to remove.")
        else:
            print(f"\nRemoved {removed} test schedule(s)")

    def run_full_test(self):
        """Run complete test suite."""
        self.print_header("TIME RESTRICTION TEST SUITE")
        print("This script will test if time restrictions are working correctly.\n")

        # Step 1: Show current status
        self.show_current_status()
        self.show_schedules()

        # Step 2: Test servers
        self.test_blocking_server()
        self.test_web_interface()

        # Step 3: Offer to run interactive test
        print("\n" + "="*60)
        print("INTERACTIVE TESTING")
        print("="*60)
        print("\nWould you like to add a test schedule to verify blocking?")
        print("1. Add schedule that BLOCKS current time")
        print("2. Add schedule that ALLOWS current time")
        print("3. Skip")
        print("4. Cleanup test schedules")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == '1':
            if self.add_test_schedule(block_now=True):
                print("\n✓ Test schedule added!")
                print("\nNext steps:")
                print("1. Check status again (option 5 from menu)")
                print("2. Try accessing a website through the blocking server")
                print("3. You should see it blocked with reason: 'Outside of allowed schedule'")
        elif choice == '2':
            if self.add_test_schedule(block_now=False):
                print("\n✓ Test schedule added!")
                print("\nNext steps:")
                print("1. Check status again (option 5 from menu)")
                print("2. Try accessing a website through the blocking server")
                print("3. You should see it ALLOWED")
        elif choice == '4':
            self.cleanup_test_schedules()

def print_menu():
    """Print the main menu."""
    print("\n" + "="*60)
    print("  TIME RESTRICTION TESTING MENU")
    print("="*60)
    print("1. Show current status")
    print("2. Show all schedules")
    print("3. Add test schedule (blocks current time)")
    print("4. Add test schedule (allows current time)")
    print("5. Test blocking server")
    print("6. Test web interface")
    print("7. Cleanup test schedules")
    print("8. Run full test suite")
    print("9. Exit")

def main():
    """Main function."""
    tester = TimeRestrictionTester()

    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        tester.run_full_test()
        return

    while True:
        print_menu()
        choice = input("\nEnter choice (1-9): ").strip()

        if choice == '1':
            tester.show_current_status()
        elif choice == '2':
            tester.show_schedules()
        elif choice == '3':
            tester.add_test_schedule(block_now=True)
        elif choice == '4':
            tester.add_test_schedule(block_now=False)
        elif choice == '5':
            tester.test_blocking_server()
        elif choice == '6':
            tester.test_web_interface()
        elif choice == '7':
            tester.cleanup_test_schedules()
        elif choice == '8':
            tester.run_full_test()
        elif choice == '9':
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
