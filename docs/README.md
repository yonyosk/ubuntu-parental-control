# Documentation Index

This directory contains all project documentation including specifications, architecture documents, and feature documentation.

## Structure

```
docs/
├── features/           # Feature-specific documentation
│   └── blocking-page/  # Custom blocking page feature
├── windows-port/       # Windows version development docs
├── user/               # User guides (coming soon)
└── api/                # API documentation (coming soon)
```

## Quick Links

### Platform Documentation

#### Windows Port
The Windows version of Ubuntu Parental Control is currently in development.

- **[Product Requirements Document (PRD)](windows-port/PRD.md)** - Complete product specification including features, user stories, technical requirements, and success metrics
- **[Architecture Document](windows-port/ARCHITECTURE.md)** - System architecture, component design, platform abstraction layer, and technology stack
- **[Task List](windows-port/TASK_LIST.md)** - Detailed development roadmap with 136 tasks organized into 10 phases (12-week timeline)

**Status**: Planning Phase
**Target Platforms**: Windows 10 (1909+), Windows 11
**Estimated Effort**: 12 weeks (1 developer)

### Feature Documentation

#### Blocking Page Feature
Custom blocking page that provides user-friendly feedback when access is blocked.

- **[Project Overview](features/blocking-page/01_project_overview.md)** - Feature goals and scope
- **[Technical Architecture](features/blocking-page/02_technical_architecture.md)** - Implementation details
- **[Design Specifications](features/blocking-page/03_design_specifications.md)** - UI/UX specifications
- **[Development Roadmap](features/blocking-page/04_development_roadmap.md)** - Implementation plan
- **[Database Schema](features/blocking-page/05_database_schema.md)** - Data structure
- **[Risk Mitigation](features/blocking-page/06_risk_mitigation.md)** - Risk analysis and mitigation
- **[Full PRD](features/blocking-page/PRD.md)** - Complete product requirements

**Status**: Planned

## Documentation Guidelines

### For Contributors

When adding new documentation:

1. **Place it in the appropriate directory**:
   - Platform-specific docs → `platform-name/`
   - Feature specs → `features/feature-name/`
   - User guides → `user/`
   - API docs → `api/`

2. **Use Markdown format** (`.md` files)
   - GitHub-flavored markdown
   - Include table of contents for long documents
   - Use relative links between documents

3. **Follow naming conventions**:
   - Use lowercase with hyphens: `my-document.md`
   - Use descriptive names: `installation-guide.md` not `guide.md`
   - Number sequential docs: `01_overview.md`, `02_architecture.md`

4. **Update this index** when adding new major documentation

### Document Types

- **PRD (Product Requirements Document)**: Product vision, features, user stories, requirements
- **Architecture**: Technical design, system components, data flow
- **Task List**: Development roadmap, task breakdown, estimates
- **User Guide**: End-user instructions and tutorials
- **API Reference**: Technical API documentation
- **Design Specs**: UI/UX specifications and mockups

## Documentation Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| Windows Port PRD | Complete | 2025-10-28 |
| Windows Port Architecture | Complete | 2025-10-28 |
| Windows Port Task List | Complete | 2025-10-28 |
| Blocking Page Specs | Complete | 2025-10-30 |
| User Guide | Planned | - |
| API Reference | Planned | - |

## Contributing to Documentation

We welcome documentation improvements! Please:

1. Check existing documentation before creating new docs
2. Follow the style and format of existing documents
3. Keep documents up to date as features are implemented
4. Link related documents together
5. Submit documentation updates via pull requests

## Need Help?

- **For usage questions**: See the [main README](../README.md)
- **For development**: See platform-specific documentation
- **For contributions**: See [CONTRIBUTING.md](../CONTRIBUTING.md) (if available)
- **For issues**: Open an issue on GitHub

---

**Last Updated**: 2025-10-30
**Maintained By**: Project Contributors
