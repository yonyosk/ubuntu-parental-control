# Project Structure

This document defines the organization and file placement conventions for the Ubuntu Parental Control project. **AI agents and developers should follow these guidelines when creating or moving files.**

## Directory Structure

```
ubuntu-parental-control/
├── src/                      # Source code (production)
│   └── parental_control/     # Main application package
├── tests/                    # All test files
├── examples/                 # Demo files and examples
├── tools/                    # Diagnostic, debug, and utility scripts
├── docs/                     # Documentation
├── templates/                # Blocking page templates
├── static/                   # Static assets (CSS, JS, images)
├── locales/                  # Internationalization files
├── .claude/                  # Claude AI configuration
└── .github/                  # GitHub workflows and templates
```

## File Placement Guidelines

### Source Code (`src/parental_control/`)
Place here:
- Production Python modules
- Core application logic
- Web interface templates (in `templates/` subdirectory)
- Package initialization files

**Examples:**
- `database.py`, `web_interface.py`, `blocking_server.py`
- Application templates like `login.html`, `index.html`

### Tests (`tests/`)
Place here:
- All test files (prefix with `test_`)
- Unit tests
- Integration tests
- End-to-end tests
- Test fixtures and helpers

**Naming convention:** `test_*.py`

**Examples:**
- `test_port_redirection.py`
- `test_network_enforcement.py`
- `test_time_restrictions.py`

### Examples (`examples/`)
Place here:
- Demo HTML files
- Sample configurations
- Example usage scripts
- Tutorial code
- Proof-of-concept implementations

**Naming convention:** `demo_*.html`, `example_*.py`

**Examples:**
- `demo_hebrew.html`
- `demo_blocking_page.html`
- `example_config.json`

### Tools (`tools/`)
Place here:
- Diagnostic scripts
- Debug utilities
- Database maintenance tools
- Installation verification scripts
- Development helpers
- Migration scripts

**Naming convention:** `diagnose_*.py`, `debug_*.py`, `verify_*.sh`, `migrate_*.py`

**Examples:**
- `diagnose_database.py`
- `debug_web_schedules.py`
- `verify_installation.sh`
- `diagnose_and_fix.sh`

### Documentation (`docs/`)
Place here:
- Feature documentation
- Architecture diagrams
- API documentation
- Porting guides
- Implementation notes

**Examples:**
- `features/blocking_pages_status.md`
- `windows-port/architecture.md`

### Root Directory
Keep in root **only**:
- Installation scripts (`install.sh`, `install_service.sh`)
- Service management scripts (`start_service.sh`, `stop_service.sh`)
- Setup scripts (`setup_iptables.sh`, `setup_root_ca.sh`)
- Configuration files (`requirements.txt`, `setup.py`)
- Service definitions (`ubuntu-parental-control.service`)
- Project documentation (`README.md`, `LICENSE`, `INSTALLATION.md`)
- Main documentation files (e.g., `PORT_REDIRECTION.md`, `TESTING_GUIDE.md`)

### Templates (`templates/`)
Place here:
- User-facing blocking page templates
- Custom block page layouts

**Organization:**
- `templates/blocked/` - Specific blocking pages (time_restricted, age_restricted, etc.)

### Static Assets (`static/`)
Place here:
- CSS files (`static/css/`)
- JavaScript files (`static/js/`)
- Images (`static/images/`)
- Fonts (`static/fonts/`)

### Locales (`locales/`)
Place here:
- Translation files (`.po`, `.mo` files)
- Language-specific resources

## Decision Tree for AI Agents

When creating a new file, ask:

1. **Is this production code?**
   - Yes → `src/parental_control/`

2. **Is this a test?**
   - Yes → `tests/`

3. **Is this a demo or example?**
   - Yes → `examples/`

4. **Is this a diagnostic, debug, or utility tool?**
   - Yes → `tools/`

5. **Is this documentation?**
   - Yes → `docs/` (or root if main docs like README.md)

6. **Is this a setup/installation script?**
   - Yes → Root directory

7. **Is this a blocking page template?**
   - Yes → `templates/blocked/`

8. **Is this a static asset?**
   - Yes → `static/css/`, `static/js/`, or `static/images/`

## Best Practices

1. **Test files**: Always prefix with `test_` and place in `tests/`
2. **Demo files**: Prefix with `demo_` or `example_` and place in `examples/`
3. **Tools**: Use descriptive prefixes (`diagnose_`, `debug_`, `verify_`) and place in `tools/`
4. **Documentation**: Keep feature-specific docs in `docs/`, main docs in root
5. **Keep root clean**: Only essential scripts and documentation in root directory
6. **Use subdirectories**: Organize within directories as needed (e.g., `docs/features/`, `static/css/`)

## AI Agent Instructions

When working on this project:

- ✅ **DO** follow the directory structure above
- ✅ **DO** use the decision tree to determine file placement
- ✅ **DO** follow naming conventions
- ✅ **DO** create subdirectories within the main directories if needed for organization
- ❌ **DON'T** place test files in the root directory
- ❌ **DON'T** place demo/example files in the root directory
- ❌ **DON'T** place diagnostic tools in the root directory
- ❌ **DON'T** create new top-level directories without discussion

## Migration Status

This structure was established on 2025-11-19. Files have been organized as follows:

- **Test files** moved from root → `tests/`
- **Demo files** moved from root → `examples/`
- **Diagnostic tools** moved from root → `tools/`

Any scripts or documentation referencing the old locations have been updated accordingly.
