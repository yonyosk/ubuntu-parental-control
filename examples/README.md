# Examples

This directory contains demo files and examples for the Ubuntu Parental Control project.

## Demo Files

### Blocking Pages
- `demo_blocking_page.html` - Standalone demo of the blocking page with all themes
- `demo_hebrew.html` - Demo of Hebrew/English bilingual blocking page

## Purpose

These files are for:
- **Development** - Testing blocking page designs without running the full system
- **Documentation** - Showing how blocking pages look and work
- **Demonstrations** - Presenting the UI to users or stakeholders
- **Testing** - Verifying language switching and theme support

## Using Demo Files

### View in Browser

Simply open the HTML files in a web browser:

```bash
# From project root
firefox examples/demo_blocking_page.html
# or
chromium examples/demo_hebrew.html
```

### Features Demonstrated

**demo_blocking_page.html:**
- All blocking reasons (manual, category, age restriction, time restriction)
- All themes (default, dark, kids, teens)
- Language switching (Hebrew ⟷ English)
- Theme switching
- Responsive design

**demo_hebrew.html:**
- Hebrew/English bilingual interface
- RTL (right-to-left) text support
- Language switcher dropdown
- Cultural appropriateness for Hebrew users

## Adding New Examples

When adding new demo files:
1. Use naming convention: `demo_*.html`, `example_*.py`, etc.
2. Place in this directory (`examples/`)
3. Update this README with description
4. Keep examples simple and self-contained
5. Include comments explaining key features

## See Also

- `/docs/features/blocking_pages_status.md` - Blocking page implementation status
- `/templates/blocked/` - Production blocking page templates
- `/PROJECT_STRUCTURE.md` - Project organization guidelines
