# Claude Project Information

## Quick Reference for AI Agents

This is the Ubuntu Parental Control project. Follow the file organization rules in `/PROJECT_STRUCTURE.md`.

### File Placement Quick Reference

- **Test files** (`test_*.py`) → `tests/`
- **Demo/example files** (`demo_*.html`, `example_*.py`) → `examples/`
- **Diagnostic/debug tools** (`diagnose_*.py`, `debug_*.py`, `verify_*.sh`) → `tools/`
- **Source code** (production modules) → `src/parental_control/`
- **Documentation** → `docs/` (or root for main docs)
- **Installation/setup scripts** → Root directory
- **Blocking templates** → `templates/blocked/`
- **Static assets** → `static/css/`, `static/js/`, `static/images/`

### Critical Rules

1. **NEVER** create test files in the root directory
2. **NEVER** create demo files in the root directory
3. **NEVER** create diagnostic tools in the root directory
4. **ALWAYS** check `PROJECT_STRUCTURE.md` before creating new files
5. **ALWAYS** follow the naming conventions for each file type

### When in Doubt

Refer to the decision tree in `PROJECT_STRUCTURE.md` or ask the user.
