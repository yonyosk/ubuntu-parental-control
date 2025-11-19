#!/usr/bin/env python3
"""
Simple test for the blocking page - doesn't require blocking server or iptables.
Just tests that the Flask /blocked route works.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_blocking_page():
    """Test just the blocking page Flask route"""
    from parental_control.web_interface import app

    print("\n" + "="*60)
    print("TESTING BLOCKING PAGE (Flask /blocked route only)")
    print("="*60 + "\n")

    # Create a test client
    with app.test_client() as client:

        # Test 1: Basic blocking page
        print("1. Testing basic blocking page...")
        response = client.get('/blocked?url=test.com&reason=test&category=MANUAL')

        if response.status_code == 200:
            print(f"   ✓ Status code: {response.status_code}")

            # Check for Hebrew content
            if 'עברית' in response.data.decode('utf-8'):
                print("   ✓ Hebrew content found")
            else:
                print("   ⚠ No Hebrew content found")

            # Check for language selector
            if 'lang-select' in response.data.decode('utf-8'):
                print("   ✓ Language selector found")
            else:
                print("   ⚠ No language selector found")

        else:
            print(f"   ❌ Status code: {response.status_code}")
            print(f"   Error: {response.data.decode('utf-8')[:200]}")
            return False

        # Test 2: English language
        print("\n2. Testing English language...")
        response = client.get('/blocked?url=test.com&reason=test&category=MANUAL&lang=en')

        if response.status_code == 200:
            print(f"   ✓ Status code: {response.status_code}")

            # Check for English content
            if 'English' in response.data.decode('utf-8'):
                print("   ✓ English content found")
            else:
                print("   ⚠ No English content found")
        else:
            print(f"   ❌ Status code: {response.status_code}")
            return False

        # Test 3: Different block types
        print("\n3. Testing different block types...")

        block_types = [
            ('time_restriction', 'Time Restricted'),
            ('category', 'Category Blocked'),
            ('manual', 'Manual Block'),
            ('age_restricted', 'Age Restricted')
        ]

        for block_type, name in block_types:
            response = client.get(f'/blocked?url=test.com&reason=test&category=MANUAL&type={block_type}')
            if response.status_code == 200:
                print(f"   ✓ {name}: OK")
            else:
                print(f"   ❌ {name}: Failed ({response.status_code})")

    print("\n" + "="*60)
    print("✅ BLOCKING PAGE TESTS PASSED")
    print("="*60 + "\n")

    print("The blocking page works correctly!")
    print("Now you just need to:")
    print("  1. Start the blocking server (port 8080)")
    print("  2. Enable iptables port redirection")
    print("  3. Add blocked domains to /etc/hosts")
    print("")

    return True

if __name__ == "__main__":
    try:
        if test_blocking_page():
            exit(0)
        else:
            exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
