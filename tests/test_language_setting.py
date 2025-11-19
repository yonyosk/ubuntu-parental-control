#!/usr/bin/env python3
"""
Test script for language setting functionality
"""
import sys
import os
import tempfile

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from parental_control.database import ParentalControlDB

def test_language_setting():
    """Test the language setting functionality"""
    print("Testing language setting functionality...")

    # Use a temporary database file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_db_path = f.name

    try:
        # Initialize database
        print(f"1. Creating test database at {temp_db_path}")
        db = ParentalControlDB(temp_db_path)

        # Test 1: Check default language is 'he' (Hebrew)
        print("2. Testing default language...")
        default_lang = db.get_default_language()
        assert default_lang == 'he', f"Expected default language 'he', got '{default_lang}'"
        print(f"   ✓ Default language is correctly set to: {default_lang}")

        # Test 2: Change language to English
        print("3. Changing language to English...")
        success = db.set_default_language('en')
        assert success, "Failed to set language to 'en'"
        print("   ✓ Language changed successfully")

        # Test 3: Verify language was changed
        print("4. Verifying language change...")
        current_lang = db.get_default_language()
        assert current_lang == 'en', f"Expected 'en', got '{current_lang}'"
        print(f"   ✓ Language verified: {current_lang}")

        # Test 4: Change back to Hebrew
        print("5. Changing language back to Hebrew...")
        success = db.set_default_language('he')
        assert success, "Failed to set language to 'he'"
        current_lang = db.get_default_language()
        assert current_lang == 'he', f"Expected 'he', got '{current_lang}'"
        print(f"   ✓ Language changed back to: {current_lang}")

        # Test 5: Try invalid language
        print("6. Testing invalid language handling...")
        success = db.set_default_language('invalid')
        assert not success, "Should have rejected invalid language"
        # Language should remain 'he'
        current_lang = db.get_default_language()
        assert current_lang == 'he', f"Language should still be 'he', got '{current_lang}'"
        print("   ✓ Invalid language correctly rejected")

        # Test 6: Test migration - create old database without default_language
        print("7. Testing migration from old database format...")
        db.close()

        # Manually create old format settings
        from tinydb import TinyDB
        old_db = TinyDB(temp_db_path)
        settings_table = old_db.table('settings')
        settings_table.truncate()
        settings_table.insert({
            'id': 1,
            'daily_limit_minutes': None,
            'protection_active': True
            # Note: no 'default_language' field
        })
        old_db.close()

        # Re-open with ParentalControlDB - should auto-migrate
        db = ParentalControlDB(temp_db_path)
        migrated_lang = db.get_default_language()
        assert migrated_lang == 'he', f"Migration should set default to 'he', got '{migrated_lang}'"
        print(f"   ✓ Migration successful, default language added: {migrated_lang}")

        db.close()

        print("\n✅ All tests passed!")
        return True

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_db_path)
            print(f"\nCleaned up test database: {temp_db_path}")
        except:
            pass

if __name__ == '__main__':
    success = test_language_setting()
    sys.exit(0 if success else 1)
