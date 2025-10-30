# Windows Parental Control - System Architecture

## Document Information
- **Version**: 1.0
- **Last Updated**: 2025-10-28
- **Status**: Design Phase

---

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [System Components](#3-system-components)
4. [Platform Abstraction Layer](#4-platform-abstraction-layer)
5. [Data Architecture](#5-data-architecture)
6. [Security Architecture](#6-security-architecture)
7. [Deployment Architecture](#7-deployment-architecture)
8. [API Design](#8-api-design)
9. [Technology Stack](#9-technology-stack)
10. [Development Workflow](#10-development-workflow)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Layer                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Browser    │      │  System Tray │      │   CLI Tool   │  │
│  │  Interface   │      │     App      │      │   (Admin)    │  │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘  │
│         │                     │                      │           │
└─────────┼─────────────────────┼──────────────────────┼───────────┘
          │                     │                      │
          ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Flask Web Server (HTTP)                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │  Auth    │  │   API    │  │   Web    │  │  Static  │  │  │
│  │  │ Handler  │  │ Endpoints│  │  Views   │  │  Assets  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Blocking   │  │     Time     │  │   Activity   │          │
│  │   Manager    │  │   Manager    │  │    Logger    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Blacklist   │  │     DNS      │  │   Password   │          │
│  │   Manager    │  │   Manager    │  │   Manager    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Platform Abstraction Layer (PAL)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Hosts     │  │     DNS      │  │   Service    │          │
│  │   Manager    │  │   Manager    │  │   Manager    │          │
│  │  (Abstract)  │  │  (Abstract)  │  │  (Abstract)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│         ├─────────────────┼──────────────────┤                   │
│         │                 │                  │                   │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐          │
│  │   Windows    │  │   Windows    │  │   Windows    │          │
│  │    Impl.     │  │    Impl.     │  │    Impl.     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   TinyDB     │  │    Cache     │  │   Backups    │          │
│  │   (JSON)     │  │  (In-Memory) │  │   (Files)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    System Layer (Windows)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Hosts File  │  │   Registry   │  │  Windows     │          │
│  │              │  │              │  │   Service    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Network    │  │     File     │  │   Process    │          │
│  │  Interfaces  │  │    System    │  │  Management  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 System Context

**External Systems:**
- Windows Operating System (10/11)
- Network Infrastructure (DNS, Routers)
- Third-Party Blacklist Providers
- Windows Defender / Antivirus Software

**System Boundaries:**
- Operates locally on single Windows machine
- No cloud dependencies (except blacklist updates)
- No external service communication required
- All data stored locally

---

## 2. Architecture Principles

### 2.1 Design Principles

1. **Platform Abstraction**
   - Abstract OS-specific operations behind interfaces
   - Enable future cross-platform support (macOS, Linux)
   - Minimize platform-specific code in business logic

2. **Separation of Concerns**
   - Clear boundaries between layers
   - Single responsibility per component
   - Loose coupling, high cohesion

3. **Fail-Safe Design**
   - System errors should not break protection
   - Automatic recovery from failures
   - Comprehensive backup and restore

4. **Security by Design**
   - Minimize attack surface
   - Principle of least privilege
   - Defense in depth

5. **Simplicity**
   - Minimize dependencies
   - Clear, maintainable code
   - No over-engineering

6. **Performance**
   - Minimal resource usage
   - Efficient data structures
   - Lazy loading where appropriate

### 2.2 Quality Attributes

| Attribute | Priority | Target | Measurement |
|-----------|----------|--------|-------------|
| Security | Critical | High | Security audit, penetration testing |
| Reliability | Critical | 99.9% uptime | Service monitoring |
| Performance | High | <100MB RAM | Resource monitoring |
| Usability | High | <5min setup | User testing |
| Maintainability | High | >80% test coverage | Code metrics |
| Compatibility | Medium | Win 10/11 | Compatibility testing |

---

## 3. System Components

### 3.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Web Interface Module                          │
├─────────────────────────────────────────────────────────────────┤
│  ├─ web_interface.py          (Flask app, routes, views)        │
│  ├─ api_endpoints.py          (REST API for programmatic access)│
│  ├─ authentication.py         (Login, session management)        │
│  ├─ templates/                (Jinja2 HTML templates)            │
│  └─ static/                   (CSS, JS, images)                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Core Business Logic                            │
├─────────────────────────────────────────────────────────────────┤
│  ├─ parental_control.py       (Main orchestrator)                │
│  ├─ blocking_manager.py       (Website blocking logic)           │
│  ├─ time_manager.py           (Time limits & schedules)          │
│  ├─ activity_logger.py        (Activity tracking & reporting)    │
│  ├─ blacklist_manager.py      (Blacklist download & management)  │
│  ├─ dns_manager.py            (DNS configuration)                │
│  └─ password_manager.py       (Password hashing & verification)  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              Platform Abstraction Layer (PAL)                    │
├─────────────────────────────────────────────────────────────────┤
│  ├─ platform/                                                    │
│  │   ├─ __init__.py           (Platform detection)               │
│  │   ├─ base.py               (Abstract interfaces)              │
│  │   ├─ windows/                                                 │
│  │   │   ├─ hosts_manager.py  (Windows hosts file)               │
│  │   │   ├─ dns_manager.py    (Windows DNS via netsh/registry)   │
│  │   │   ├─ service_manager.py(Windows Service management)       │
│  │   │   ├─ path_manager.py   (Windows paths & permissions)      │
│  │   │   └─ process_manager.py(Process & privilege management)   │
│  │   └─ linux/                (Future: Linux implementations)    │
│  │       ├─ hosts_manager.py                                     │
│  │       └─ ...                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
├─────────────────────────────────────────────────────────────────┤
│  ├─ database.py               (TinyDB wrapper, data access)      │
│  ├─ models.py                 (Data models & schemas)            │
│  ├─ cache.py                  (In-memory caching)                │
│  └─ backup_manager.py         (Backup & restore)                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Utility Modules                               │
├─────────────────────────────────────────────────────────────────┤
│  ├─ validation.py             (Input validation & sanitization)  │
│  ├─ logging_config.py         (Logging configuration)            │
│  ├─ config.py                 (Configuration management)         │
│  └─ exceptions.py             (Custom exception classes)         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Windows Service Wrapper                        │
├─────────────────────────────────────────────────────────────────┤
│  ├─ service_main.py           (Windows service entry point)      │
│  ├─ service_installer.py      (Service installation script)      │
│  └─ service_config.py         (Service configuration)            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    System Tray Application                       │
├─────────────────────────────────────────────────────────────────┤
│  ├─ tray_app.py               (System tray icon & menu)          │
│  ├─ tray_icons/               (Icon resources)                   │
│  └─ notifications.py          (Windows notifications)            │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Descriptions

#### 3.2.1 Web Interface Module
**Responsibility**: Provide web-based user interface for configuration and monitoring

**Key Classes**:
- `WebApplication`: Flask application setup and configuration
- `AuthHandler`: Session management and authentication
- `DashboardController`: Main dashboard views and logic
- `APIController`: REST API endpoints

**Dependencies**: Flask, Flask-WTF (CSRF), Jinja2

#### 3.2.2 Core Business Logic

**ParentalControl** (Main Orchestrator)
- Coordinates all business logic components
- Provides unified API for web interface
- Handles cross-cutting concerns

**BlockingManager**
- Manual domain blocking/unblocking
- Category-based blocking
- Temporary exceptions
- Block checking logic

**TimeManager**
- Daily time limit tracking
- Schedule-based blocking
- Usage statistics
- Time reset logic

**ActivityLogger**
- Log blocked attempts
- Log allowed access
- Generate reports
- Export functionality

**BlacklistManager**
- Download blacklists from providers
- Parse and store blacklist data
- Update management
- Category management

**DNSManager** (Abstract)
- DNS configuration interface
- Safe DNS presets
- DNS validation

**PasswordManager**
- Password hashing (bcrypt recommended)
- Password verification
- Password strength validation

#### 3.2.3 Platform Abstraction Layer

**Base Interfaces** (`platform/base.py`):
```python
class HostsManagerBase(ABC):
    @abstractmethod
    def update_hosts(self, domains: Set[str]) -> bool

    @abstractmethod
    def backup_hosts(self) -> bool

    @abstractmethod
    def restore_hosts(self) -> bool

class DNSManagerBase(ABC):
    @abstractmethod
    def set_dns(self, primary: str, secondary: str) -> bool

    @abstractmethod
    def get_current_dns(self) -> Tuple[str, str]

class ServiceManagerBase(ABC):
    @abstractmethod
    def install_service(self) -> bool

    @abstractmethod
    def start_service(self) -> bool

    @abstractmethod
    def stop_service(self) -> bool
```

**Windows Implementations**:
- Use PyWin32 for Windows API access
- Use `subprocess` for netsh commands
- Use `winreg` for registry operations
- Use `ctypes` for privilege checks

#### 3.2.4 Data Layer

**Database** (TinyDB):
```
config.json
├─ settings
│  ├─ password_hash
│  ├─ protection_active
│  ├─ daily_limit_minutes
│  └─ ...
├─ blocked_sites
│  ├─ {domain, category, added_date}
│  └─ ...
├─ blacklist_categories
│  ├─ {name, is_active, domain_count, last_updated}
│  └─ ...
├─ time_schedules
│  ├─ {name, start_time, end_time, days, is_active}
│  └─ ...
└─ activity_logs
   ├─ {timestamp, domain, action, category, reason}
   └─ ...
```

**Cache** (In-Memory):
- Blacklist domains (for fast lookup)
- Current DNS settings
- Active schedules

---

## 4. Platform Abstraction Layer

### 4.1 Design Pattern

**Strategy Pattern** for platform-specific implementations:

```python
# platform/__init__.py
import platform
from .base import HostsManagerBase, DNSManagerBase, ServiceManagerBase

def get_hosts_manager() -> HostsManagerBase:
    system = platform.system()
    if system == 'Windows':
        from .windows.hosts_manager import WindowsHostsManager
        return WindowsHostsManager()
    elif system == 'Linux':
        from .linux.hosts_manager import LinuxHostsManager
        return LinuxHostsManager()
    else:
        raise NotImplementedError(f"Platform {system} not supported")

def get_dns_manager() -> DNSManagerBase:
    system = platform.system()
    if system == 'Windows':
        from .windows.dns_manager import WindowsDNSManager
        return WindowsDNSManager()
    # ... similar pattern
```

### 4.2 Windows-Specific Implementation Details

#### Hosts File Management
```python
# platform/windows/hosts_manager.py
class WindowsHostsManager(HostsManagerBase):
    HOSTS_PATH = r'C:\Windows\System32\drivers\etc\hosts'

    def update_hosts(self, domains: Set[str]) -> bool:
        # 1. Check admin privileges
        # 2. Create backup
        # 3. Read current hosts file
        # 4. Parse and preserve non-PC entries
        # 5. Add PC section with markers
        # 6. Write atomically using temp file
        # 7. Verify write success
```

**Challenges**:
- Windows file locking (use `msvcrt.locking` or `win32file`)
- UAC elevation required
- Windows Defender may flag modifications
- Need atomic operations to prevent corruption

#### DNS Management
```python
# platform/windows/dns_manager.py
class WindowsDNSManager(DNSManagerBase):
    def set_dns(self, primary: str, secondary: str) -> bool:
        # Option 1: Use netsh command
        # netsh interface ip set dns "Interface Name" static [DNS]

        # Option 2: Use Windows Registry
        # HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\{GUID}

        # Must handle:
        # - Multiple network interfaces
        # - Detect active interfaces
        # - Revert on failure
```

**Challenges**:
- Must modify all active network interfaces
- Interface names can change
- Need to store original DNS for revert
- May require network restart

#### Service Management
```python
# platform/windows/service_manager.py
class WindowsServiceManager(ServiceManagerBase):
    def install_service(self) -> bool:
        # Option 1: Use PyWin32 (win32serviceutil)
        # Option 2: Use NSSM (Non-Sucking Service Manager)
        # Option 3: Use sc.exe command
```

**Recommendation**: Use **NSSM** for simplicity:
- Easy installation: `nssm install ParentalControlService "C:\path\to\python.exe" "C:\path\to\service_main.py"`
- Automatic restart on failure
- Output redirection to log files
- Environment variable support

---

## 5. Data Architecture

### 5.1 Database Schema (TinyDB)

```json
{
  "settings": [
    {
      "password_hash": "sha256_hash_here",
      "protection_active": true,
      "daily_limit_minutes": 480,
      "reset_time": "00:00",
      "dns_type": "opendns",
      "dns_primary": "208.67.222.123",
      "dns_secondary": "208.67.220.123",
      "created_at": "2025-01-01T00:00:00",
      "updated_at": "2025-01-15T10:30:00"
    }
  ],

  "blocked_sites": [
    {
      "id": 1,
      "domain": "example.com",
      "category": "MANUAL",
      "added_date": "2025-01-15T10:00:00",
      "added_by": "admin"
    }
  ],

  "blacklist_categories": [
    {
      "id": 1,
      "name": "adult",
      "description": "Adult content",
      "is_active": true,
      "domain_count": 15000,
      "source_url": "https://...",
      "last_updated": "2025-01-15T00:00:00"
    }
  ],

  "blacklist_domains": [
    {
      "id": 1,
      "domain": "badsite.com",
      "category_id": 1,
      "category_name": "adult"
    }
  ],

  "time_schedules": [
    {
      "id": 1,
      "name": "School Hours",
      "start_time": "08:00",
      "end_time": "16:00",
      "days": [0, 1, 2, 3, 4],
      "is_active": true,
      "created_at": "2025-01-10T12:00:00"
    }
  ],

  "daily_usage": [
    {
      "date": "2025-01-15",
      "minutes_used": 120,
      "last_updated": "2025-01-15T14:30:00"
    }
  ],

  "activity_logs": [
    {
      "id": 1,
      "timestamp": "2025-01-15T14:30:45",
      "domain": "blockedsite.com",
      "action": "blocked",
      "category": "adult",
      "reason": "Blocked by adult content filter",
      "client_ip": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    }
  ]
}
```

### 5.2 Data Access Patterns

**Read-Heavy Operations**:
- Checking if domain is blocked (millions of times)
- Getting active schedules (frequent)
- Checking time limits (frequent)

**Optimization**:
- Cache blacklist domains in memory (Set for O(1) lookup)
- Cache active schedules in memory
- Lazy load activity logs (only when viewing reports)

**Write Operations**:
- Adding blocked sites (infrequent)
- Recording activity logs (frequent but async)
- Updating usage stats (frequent but batched)

### 5.3 Data Backup Strategy

**Automatic Backups**:
- Daily backup of config.json at midnight
- Keep last 7 daily backups
- Keep last 4 weekly backups (Sunday)
- Backup before any major operation

**Backup Location**:
`%ProgramData%\ParentalControl\backups\`

**Restore Priority**:
1. Most recent successful backup
2. Previous day backup
3. Last known good configuration
4. Factory defaults

---

## 6. Security Architecture

### 6.1 Security Layers

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Authentication & Authorization                │
│  - Password hashing (bcrypt)                            │
│  - Session management with secure tokens                │
│  - Rate limiting on login attempts                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Input Validation & Sanitization               │
│  - Whitelist-based validation                           │
│  - Domain name validation (regex)                       │
│  - SQL injection prevention (N/A - using JSON)          │
│  - XSS prevention (template escaping)                   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Privilege Management                          │
│  - Service runs as LocalSystem                          │
│  - Web interface requires admin password                │
│  - File permissions (ACLs on config files)              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Tamper Protection                             │
│  - Service protection (cannot be killed easily)         │
│  - Hosts file monitoring (detect external changes)      │
│  - DNS setting monitoring and reversion                 │
│  - Configuration file integrity checks                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 5: Audit & Logging                               │
│  - All configuration changes logged                     │
│  - Failed login attempts logged                         │
│  - Service events logged to Windows Event Log           │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Password Security

**Requirements**:
- Minimum 8 characters (configurable)
- Hashed with bcrypt (work factor 12)
- Stored in database (not in code or config)
- Session tokens cryptographically secure

```python
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8'))
```

### 6.3 Session Security

```python
import secrets

def generate_session_token() -> str:
    return secrets.token_urlsafe(32)  # 256-bit token

# Session storage
sessions = {
    'token_abc123': {
        'user': 'admin',
        'created_at': datetime.now(),
        'last_activity': datetime.now(),
        'ip_address': '127.0.0.1'
    }
}

# Session timeout: 4 hours
SESSION_TIMEOUT = 14400  # seconds
```

### 6.4 File System Security

**Configuration Files**:
- Location: `%ProgramData%\ParentalControl\`
- Permissions: SYSTEM (Full), Administrators (Full), Users (Read)
- Prevent modification by non-admin users

**Hosts File**:
- Backup before modification
- Atomic write operations
- Verify integrity after write
- Restore from backup on corruption

### 6.5 Network Security

**Web Interface**:
- Bind to localhost only by default (`127.0.0.1:5000`)
- HTTPS optional (self-signed certificate)
- CSRF protection enabled
- Security headers (X-Frame-Options, CSP, etc.)

**DNS Security**:
- Validate DNS server addresses
- Test DNS before applying
- Revert on failure
- Monitor for external DNS changes

---

## 7. Deployment Architecture

### 7.1 Installation Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. MSI Installer Execution                             │
│     - Check Windows version compatibility               │
│     - Check administrator privileges                    │
│     - Check Python runtime (embedded or system)         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  2. File Extraction                                     │
│     - C:\Program Files\ParentalControl\                │
│       ├─ python\ (embedded Python 3.10)                │
│       ├─ app\                                           │
│       │  ├─ src\                                        │
│       │  ├─ templates\                                  │
│       │  ├─ static\                                     │
│       │  └─ config\                                     │
│       └─ nssm.exe (service wrapper)                     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  3. Data Directory Setup                                │
│     - %ProgramData%\ParentalControl\                   │
│       ├─ config.json (created on first run)            │
│       ├─ logs\                                          │
│       └─ backups\                                       │
│     - Set proper ACLs                                   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  4. Service Installation                                │
│     - Install Windows Service (NSSM)                    │
│     - Configure service to auto-start                   │
│     - Start service                                     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  5. Initial Configuration                               │
│     - Launch browser to http://localhost:5000           │
│     - First-time setup wizard                           │
│     - Set admin password                                │
│     - Apply default safe settings (optional)            │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Runtime Architecture

```
Windows Startup
      │
      ▼
┌─────────────────────────────────────┐
│  Windows Service                    │
│  (ParentalControlService)           │
│                                     │
│  Runs as: LocalSystem               │
│  Startup: Automatic                 │
│  Recovery: Restart on failure       │
└──────────┬──────────────────────────┘
           │
           ├─────────────────────────────┐
           │                             │
           ▼                             ▼
┌──────────────────────┐    ┌──────────────────────┐
│  Flask Web Server    │    │  Background Tasks    │
│  Port: 5000          │    │                      │
│  Bind: 127.0.0.1     │    │  - DNS monitoring    │
│  Threads: 4          │    │  - Hosts monitoring  │
└──────────────────────┘    │  - Usage tracking    │
                            │  - Blacklist updates │
                            │  - Log rotation      │
                            └──────────────────────┘

User Login
      │
      ▼
┌─────────────────────────────────────┐
│  System Tray Application            │
│  (Optional, auto-start)             │
│                                     │
│  - Quick status indicator           │
│  - Open dashboard                   │
│  - Quick enable/disable             │
└─────────────────────────────────────┘
```

### 7.3 Update Mechanism

**Auto-Update Flow**:
1. Service checks for updates daily (configurable)
2. Download update package (signed)
3. Verify signature and checksum
4. Stop service
5. Backup current installation
6. Extract update
7. Restart service
8. Verify successful update

**Manual Update**:
- Download new MSI installer
- Run installer (will detect existing installation)
- Upgrade in-place
- Preserve configuration and data

---

## 8. API Design

### 8.1 Internal API (Business Logic)

```python
class ParentalControl:
    """Main facade for all parental control operations"""

    def __init__(self):
        self.db = Database()
        self.hosts_manager = get_hosts_manager()
        self.dns_manager = get_dns_manager()
        self.blocking_manager = BlockingManager(self.db, self.hosts_manager)
        self.time_manager = TimeManager(self.db)
        self.activity_logger = ActivityLogger(self.db)

    # Website Blocking
    def block_domain(self, domain: str, category: str = 'MANUAL') -> bool
    def unblock_domain(self, domain: str) -> bool
    def is_domain_blocked(self, domain: str) -> Tuple[bool, List[str]]
    def get_blocked_domains(self) -> List[Dict]

    # Category Blocking
    def block_category(self, category_name: str) -> bool
    def unblock_category(self, category_name: str) -> bool
    def get_available_categories(self) -> List[Dict]

    # Time Management
    def set_daily_limit(self, minutes: int) -> bool
    def get_daily_limit(self) -> int
    def get_todays_usage(self) -> int
    def add_schedule(self, name: str, start: str, end: str, days: List[int]) -> bool
    def remove_schedule(self, schedule_id: int) -> bool

    # DNS Management
    def set_dns(self, dns_type: str, primary: str = None, secondary: str = None) -> bool
    def get_dns_settings(self) -> Dict

    # Activity & Reports
    def get_activity_logs(self, start_date: str = None, end_date: str = None) -> List[Dict]
    def export_activity_logs(self, format: str = 'csv') -> bytes

    # System
    def is_protection_active(self) -> bool
    def set_protection_active(self, active: bool) -> bool
    def verify_password(self, password: str) -> bool
    def set_password(self, password: str) -> bool
```

### 8.2 REST API (Web Interface)

**Base URL**: `http://localhost:5000/api/v1/`

**Authentication**: Session-based (cookie)

#### Endpoints

```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/session

GET    /api/v1/status
GET    /api/v1/settings
PUT    /api/v1/settings

GET    /api/v1/blocking/domains
POST   /api/v1/blocking/domains
DELETE /api/v1/blocking/domains/{domain}

GET    /api/v1/blocking/categories
POST   /api/v1/blocking/categories/{category}/enable
POST   /api/v1/blocking/categories/{category}/disable

GET    /api/v1/time/limit
PUT    /api/v1/time/limit
GET    /api/v1/time/usage
GET    /api/v1/time/schedules
POST   /api/v1/time/schedules
DELETE /api/v1/time/schedules/{id}

GET    /api/v1/dns
PUT    /api/v1/dns

GET    /api/v1/activity/logs
GET    /api/v1/activity/export
```

**Example Response**:
```json
{
  "success": true,
  "data": {
    "domains": [
      {
        "domain": "example.com",
        "category": "MANUAL",
        "added_date": "2025-01-15T10:00:00"
      }
    ]
  },
  "error": null
}
```

---

## 9. Technology Stack

### 9.1 Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.10+ | Core application |
| Web Framework | Flask | 2.3+ | Web interface |
| Database | TinyDB | 4.7+ | JSON database |
| Windows API | PyWin32 | Latest | Windows integration |
| Service Wrapper | NSSM | 2.24+ | Windows service |
| Installer | WiX Toolset | 3.11+ | MSI creation |
| Password Hashing | bcrypt | Latest | Secure passwords |

### 9.2 Development Dependencies

| Tool | Purpose |
|------|---------|
| pytest | Unit testing |
| pytest-cov | Code coverage |
| black | Code formatting |
| flake8 | Linting |
| mypy | Type checking |
| Sphinx | Documentation |

### 9.3 Python Dependencies

```
Flask>=2.3.0
tinydb>=4.7.0
pywin32>=305
bcrypt>=4.0.0
requests>=2.28.0
python-dateutil>=2.8.0
Jinja2>=3.1.0
Werkzeug>=2.3.0
```

### 9.4 Embedded vs System Python

**Recommendation**: Embed Python with application

**Advantages**:
- No dependency on system Python
- Consistent environment
- Easier deployment
- Version control

**Implementation**:
- Use Python embeddable package
- Include all dependencies
- Total size: ~50-70 MB

---

## 10. Development Workflow

### 10.1 Project Structure

```
parental-control-windows/
├── src/
│   ├── parental_control/
│   │   ├── __init__.py
│   │   ├── core/                    # Core business logic
│   │   │   ├── parental_control.py
│   │   │   ├── blocking_manager.py
│   │   │   ├── time_manager.py
│   │   │   ├── activity_logger.py
│   │   │   └── ...
│   │   ├── platform/                # Platform abstraction
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── windows/
│   │   │   │   ├── hosts_manager.py
│   │   │   │   ├── dns_manager.py
│   │   │   │   └── ...
│   │   │   └── linux/               # Future
│   │   ├── data/                    # Data layer
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── cache.py
│   │   ├── web/                     # Web interface
│   │   │   ├── app.py
│   │   │   ├── routes/
│   │   │   ├── templates/
│   │   │   └── static/
│   │   ├── service/                 # Windows service
│   │   │   ├── service_main.py
│   │   │   └── service_installer.py
│   │   └── utils/                   # Utilities
│   │       ├── validation.py
│   │       ├── logging_config.py
│   │       └── config.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── system/
├── installer/
│   ├── wix/                         # WiX installer files
│   └── scripts/
├── docs/
├── requirements.txt
├── requirements-dev.txt
├── setup.py
└── README.md
```

### 10.2 Development Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/yourorg/parental-control-windows.git
cd parental-control-windows

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Run tests
pytest

# 5. Run development server (requires admin)
python -m src.parental_control.web.app
```

### 10.3 Testing Strategy

**Unit Tests**:
- Test each component in isolation
- Mock external dependencies (file system, Windows API)
- Target: >80% code coverage

**Integration Tests**:
- Test component interactions
- Test database operations
- Test API endpoints

**System Tests**:
- End-to-end scenarios
- Test on real Windows systems
- Test service installation/uninstallation

**Manual Tests**:
- Compatibility testing (different Windows versions)
- Security testing
- User acceptance testing

### 10.4 Build Process

```bash
# 1. Run tests
pytest tests/

# 2. Build Python package
python setup.py sdist bdist_wheel

# 3. Create embedded Python package
# - Download Python embeddable zip
# - Extract and include dependencies

# 4. Build MSI installer (WiX)
candle installer\wix\product.wxs
light -out ParentalControl.msi product.wixobj

# 5. Sign installer (code signing certificate)
signtool sign /f cert.pfx /p password ParentalControl.msi

# 6. Test installation on clean VM
```

### 10.5 CI/CD Pipeline

**GitHub Actions Workflow**:
```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest --cov
      - run: flake8 src/

  build:
    needs: test
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build MSI
        run: |
          # Build steps here
      - uses: actions/upload-artifact@v2
        with:
          name: installer
          path: ParentalControl.msi
```

---

## 11. Performance Considerations

### 11.1 Performance Requirements

| Metric | Target | Critical |
|--------|--------|----------|
| Service memory usage | <100 MB | <150 MB |
| Service CPU (idle) | <2% | <5% |
| Web page load time | <2s | <5s |
| Hosts file update | <5s (10K domains) | <10s |
| Domain lookup | <1ms | <10ms |
| Service startup | <10s | <30s |

### 11.2 Optimization Strategies

**Memory Optimization**:
- Cache only active blacklist domains
- Lazy load activity logs
- Periodic cache cleanup
- Use generators for large datasets

**CPU Optimization**:
- Async operations for I/O
- Batch database writes
- Efficient domain matching (Set lookup)
- Debounce frequent operations

**Disk I/O Optimization**:
- Batch log writes
- Async file operations
- Compress old logs
- Efficient JSON serialization

---

## 12. Monitoring & Observability

### 12.1 Logging Strategy

**Log Levels**:
- **ERROR**: Service failures, critical errors
- **WARNING**: Non-critical issues, recoverable errors
- **INFO**: Important events (config changes, blocks)
- **DEBUG**: Detailed diagnostic information

**Log Destinations**:
1. Application logs: `%ProgramData%\ParentalControl\logs\app.log`
2. Windows Event Log: Application category
3. Web access logs: `%ProgramData%\ParentalControl\logs\access.log`

**Log Rotation**:
- Daily rotation
- Keep last 30 days
- Compress old logs

### 12.2 Health Monitoring

**Service Health Checks**:
- Web server responding
- Database accessible
- Hosts file intact
- DNS settings correct
- Sufficient disk space

**Metrics to Track**:
- Service uptime
- Number of blocked requests
- Number of configuration changes
- Error rates
- Response times

---

## 13. Security Considerations (Implementation)

### 13.1 Code Security Practices

**Input Validation**:
```python
def validate_domain(domain: str) -> str:
    # Whitelist approach
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    if not re.match(pattern, domain):
        raise ValidationError("Invalid domain format")
    if len(domain) > 253:
        raise ValidationError("Domain too long")
    return domain.lower().strip()
```

**SQL Injection Prevention**:
- N/A (using JSON database)

**XSS Prevention**:
- Jinja2 auto-escaping enabled
- Use `|safe` filter only when necessary
- Sanitize user inputs

**CSRF Protection**:
- Flask-WTF CSRF tokens
- SameSite cookie attribute

### 13.2 Deployment Security

**File Permissions**:
- Application files: Read-only for users
- Configuration: Admins only
- Logs: Admins read, system write

**Network Security**:
- Bind web server to localhost only
- No external network exposure by default
- Optional HTTPS with self-signed cert

**Service Security**:
- Run as LocalSystem (required for hosts/DNS modification)
- Service cannot be stopped by non-admins
- Protected process (optional)

---

## Appendix A: Design Decisions

### Decision Log

| Decision | Date | Rationale | Alternatives Considered |
|----------|------|-----------|------------------------|
| Use TinyDB instead of SQLite | 2025-01-01 | Simpler, no SQL injection risk, JSON human-readable | SQLite (more complex), MongoDB (overkill) |
| Use NSSM for service wrapper | 2025-01-01 | Simplicity, automatic restart, good logging | PyWin32 service (complex), sc.exe (limited features) |
| Embed Python with application | 2025-01-01 | No system Python dependency, version control | System Python (dependency issues) |
| Use bcrypt for passwords | 2025-01-01 | Industry standard, configurable work factor | SHA-256 (too fast), Argon2 (newer but bcrypt proven) |
| Platform abstraction layer | 2025-01-01 | Enable future cross-platform support | Platform-specific code only (Windows-only forever) |

---

## Appendix B: Future Enhancements

### Phase 2 Features (Post-MVP)
1. Application blocking (block specific executables)
2. Advanced reporting with charts
3. Profile management (multiple children)
4. Browser extension for HTTPS filtering
5. Mobile app for remote monitoring

### Phase 3 Features
1. Network-wide filtering (router integration)
2. AI-based content classification
3. Screen time limits with forced logout
4. Remote management API
5. Multi-device management

---

**Document Version**: 1.0
**Last Updated**: 2025-10-28
**Next Review**: Before development sprint 1
