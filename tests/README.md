# Tests

This directory contains all test files for the Ubuntu Parental Control project.

## Test Files

### Time Restrictions
- `test_time_restrictions.py` - Interactive test suite for time restriction features
- `test_add_schedule.py` - Tests for adding time schedules
- `test_schedule_retrieval.py` - Tests for retrieving schedules from database
- `test_db_persistence.py` - Tests for database persistence

### Network Enforcement
- `test_network_enforcement.py` - Tests for network-level blocking using iptables
- `test_port_redirection.py` - Tests for port redirection (80/443 → 8080)

### Web Interface
- `test_blocking_page_only.py` - Tests for blocking page display
- `test_language_setting.py` - Tests for language settings and i18n

## Running Tests

All tests should be run with root privileges since they interact with system-level features (iptables, network, etc.):

```bash
# Run a specific test
sudo python3 tests/test_time_restrictions.py

# Run with specific options
sudo python3 tests/test_network_enforcement.py test
sudo python3 tests/test_time_restrictions.py --auto
```

## Test Coverage

These tests cover:
- ✅ Time restriction logic
- ✅ Network enforcement (iptables)
- ✅ Port redirection
- ✅ Database operations
- ✅ Blocking pages
- ✅ Language settings
- ✅ Schedule management

## Adding New Tests

When adding new tests:
1. Follow naming convention: `test_*.py`
2. Place in this directory (`tests/`)
3. Add documentation to this README
4. Update `TESTING_GUIDE.md` if it's a major feature test
5. Ensure tests can run independently
6. Include cleanup code to restore system state

## See Also

- `/TESTING_GUIDE.md` - Comprehensive testing documentation
- `/PROJECT_STRUCTURE.md` - Project organization guidelines
