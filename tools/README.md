# Tools

This directory contains diagnostic, debug, and utility scripts for the Ubuntu Parental Control project.

## Diagnostic Tools

### Database Diagnostics
- `diagnose_database.py` - Check database integrity and contents
- `diagnose_db_v2.py` - Enhanced database diagnostics with detailed output

### Web Interface Debugging
- `debug_web_schedules.py` - Debug schedule retrieval in web interface

### System Diagnostics
- `diagnose_and_fix.sh` - Comprehensive diagnostic and automatic fix script
  - Cleans up processes
  - Checks ports
  - Resets iptables rules
  - Verifies database access
  - Provides actionable next steps

### Installation Verification
- `verify_installation.sh` - Verify installation is correct and complete
  - Checks file installation
  - Verifies service status
  - Tests web interface accessibility
  - Reviews recent logs

## Running Tools

Most tools require root privileges:

```bash
# Database diagnostics
sudo python3 tools/diagnose_database.py
sudo python3 tools/diagnose_db_v2.py

# Web schedule debugging
sudo python3 tools/debug_web_schedules.py

# System diagnostics and auto-fix
sudo ./tools/diagnose_and_fix.sh

# Installation verification
sudo ./tools/verify_installation.sh
```

## When to Use

### diagnose_and_fix.sh
Use when:
- Service won't start
- Ports are in use
- iptables rules are broken
- System is in an inconsistent state

### verify_installation.sh
Use when:
- After updating to a new version
- Changes not showing up
- Verifying deployment

### diagnose_database.py / diagnose_db_v2.py
Use when:
- Database errors occur
- Data seems corrupted
- Settings not persisting
- Schedules not working

### debug_web_schedules.py
Use when:
- Web interface shows wrong schedules
- Schedule data not displaying
- Debugging schedule-related issues

## Development Guidelines

When adding new tools:
1. Use descriptive prefixes: `diagnose_*`, `debug_*`, `verify_*`, `migrate_*`
2. Place in this directory (`tools/`)
3. Make scripts executable: `chmod +x tools/your_script.sh`
4. Add usage documentation in script header
5. Include error handling and helpful output
6. Update this README with description

## Tool Categories

### Diagnostic Tools (`diagnose_*`)
- Analyze system state
- Report problems
- Provide actionable information
- May auto-fix issues

### Debug Tools (`debug_*`)
- Help troubleshoot specific features
- Show detailed internal state
- Aid in development
- Verbose output for investigation

### Verification Tools (`verify_*`)
- Check installation correctness
- Validate configuration
- Confirm proper operation
- Quick health checks

### Migration Tools (`migrate_*`)
- Database schema updates
- Data format conversions
- Version upgrades
- Backward compatibility

## See Also

- `/INSTALLATION.md` - Installation and troubleshooting guide
- `/TESTING_GUIDE.md` - Testing procedures
- `/PROJECT_STRUCTURE.md` - Project organization guidelines
