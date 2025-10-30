# Technical Architecture - Enhanced Blocked Pages

## System Architecture Overview

The enhanced blocked page system builds upon the existing Ubuntu Parental Control infrastructure while adding new components for reliability, interactivity, and customization.

---

## Current Architecture Analysis

### Existing Components

#### 1. Hosts File Manager (`src/parental_control/hosts_manager.py`)
**Purpose**: Modifies `/etc/hosts` to redirect blocked domains to localhost

**Key Methods**:
- `update_blocked_domains()` (lines 188-247): Atomic hosts file updates
- `_write_hosts_file_atomic()` (lines 273-301): Safe file operations with backup
- Backup management with 10-file retention

**Current Flow**:
```
Blocked domain request → /etc/hosts lookup → 127.0.0.1 redirect
```

#### 2. Blocking Server (`src/parental_control/blocking_server.py`)
**Purpose**: HTTP server that intercepts blocked requests and serves friendly pages

**Key Components**:
- `BlockingHandler` (lines 16-104): HTTP request handler
- `BlockingServer` (lines 106-146): Server lifecycle management
- Port: 8080 (configurable)

**Current Flow**:
```
Browser → 127.0.0.1:8080 → BlockingHandler → Flask /blocked route
```

#### 3. Web Interface (`src/parental_control/web_interface.py`)
**Purpose**: Admin panel and blocked page serving

**Key Routes**:
- `/blocked` (lines 1036-1049): Serves blocked page template
- Parameters: url, reason, category, time_restriction, auto_refresh

#### 4. Access Control (`src/parental_control/parental_control.py`)
**Purpose**: Determines if domain should be blocked

**Key Methods**:
- `is_access_allowed()` (lines 365-436): Main access control logic
- `is_domain_blocked()` (lines 490-524): Domain blocking check
- Returns: (is_allowed: bool, reason: str)

---

## Proposed Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/HTTPS Request
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   /etc/hosts Redirect                        │
│              127.0.0.1 blocked-site.com                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Enhanced Blocking Server (Port 8080)                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │   Watchdog Service (Auto-restart, Health Checks)       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │   HTTPS Handler (Self-signed certificate)              │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │   Request Router                                        │ │
│  │   ├─ Static Assets (CSS, JS, Images)                   │ │
│  │   ├─ Template Selector (determines which template)     │ │
│  │   └─ API Endpoints (access requests, feedback)         │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask Application (Port 5000)                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │   New Routes:                                           │ │
│  │   • /blocked/time-restricted                           │ │
│  │   • /blocked/category                                  │ │
│  │   • /blocked/manual                                    │ │
│  │   • /blocked/age-restricted                            │ │
│  │   • /api/request-access                                │ │
│  │   • /api/submit-feedback                               │ │
│  │   • /admin/customize-blocked-pages                     │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              TinyDB Database (JSON)                          │
│  • access_requests (new)                                     │
│  • blocked_page_customizations (new)                         │
│  • alternative_sites (new)                                   │
│  • blocked_sites (existing)                                  │
│  • activity_log (existing)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## New Components

### 1. Enhanced Blocking Server v2

**File**: `src/parental_control/blocking_server_v2.py`

**Features**:
- HTTPS support with self-signed certificates
- Health check endpoint (`/health`)
- Graceful shutdown handling
- Port conflict detection and resolution
- Request logging and analytics
- Static asset serving
- Template caching

**Key Classes**:

```python
class EnhancedBlockingServer:
    """Enhanced HTTP(S) server with health monitoring"""

    def __init__(self, port=8080, enable_https=True):
        self.port = port
        self.enable_https = enable_https
        self.health_status = "healthy"

    def start_with_watchdog(self):
        """Start server with automatic restart on failure"""
        pass

    def generate_ssl_certificate(self):
        """Generate self-signed SSL certificate"""
        pass

    def check_port_availability(self):
        """Check if port is available, find alternative if not"""
        pass

    def serve_forever_with_health_checks(self):
        """Run server with periodic health checks"""
        pass

class EnhancedBlockingHandler(BaseHTTPRequestHandler):
    """HTTP request handler with routing and template selection"""

    def do_GET(self):
        """Handle GET requests with smart routing"""
        pass

    def do_POST(self):
        """Handle POST requests for access requests"""
        pass

    def select_template(self, domain, block_info):
        """Determine which template to use based on block reason"""
        pass

    def serve_static_asset(self, path):
        """Serve CSS, JS, images with proper caching"""
        pass
```

### 2. Blocked Page Manager

**File**: `src/parental_control/blocked_page_manager.py`

**Purpose**: Centralized logic for template selection and customization

**Key Classes**:

```python
class BlockedPageManager:
    """Manages blocked page templates and customization"""

    def __init__(self, db: ParentalControlDB):
        self.db = db
        self.template_cache = {}

    def get_blocked_page_context(self, domain: str,
                                 block_reason: str,
                                 block_category: str = None,
                                 time_restriction: str = None) -> dict:
        """
        Build context dict for template rendering

        Returns:
            {
                'template_type': 'time_restricted|category|manual|age_restricted',
                'domain': str,
                'reason': str,
                'category': str,
                'custom_message': str,
                'theme': str,
                'show_timer': bool,
                'show_request_button': bool,
                'alternatives': list,
                'next_available_time': datetime,
                'educational_content': str
            }
        """
        pass

    def select_template_type(self, block_reason: str,
                           block_category: str = None) -> str:
        """Determine which template to use"""
        if 'time' in block_reason.lower():
            return 'time_restricted'
        elif block_category:
            return 'category'
        elif 'manual' in block_reason.lower():
            return 'manual'
        else:
            return 'age_restricted'

    def get_customization(self) -> dict:
        """Retrieve parent customization settings"""
        pass

    def get_alternative_sites(self, category: str) -> list:
        """Get alternative websites for blocked category"""
        pass

    def get_educational_content(self, category: str, age_group: str) -> str:
        """Get age-appropriate educational content"""
        pass
```

### 3. Access Request Handler

**File**: `src/parental_control/access_request_handler.py`

**Purpose**: Process and manage temporary access requests

**Key Classes**:

```python
class AccessRequestHandler:
    """Handle user requests for temporary access"""

    def __init__(self, db: ParentalControlDB):
        self.db = db

    def submit_request(self, domain: str, user: str,
                      reason: str, duration: int) -> str:
        """
        Submit access request

        Args:
            domain: Requested domain
            user: Username requesting access
            reason: Why access is needed
            duration: Minutes of access requested

        Returns:
            request_id: Unique identifier for request
        """
        pass

    def get_pending_requests(self) -> list:
        """Get all pending access requests"""
        pass

    def approve_request(self, request_id: str,
                       approved_duration: int = None) -> bool:
        """Approve access request and grant temporary exception"""
        pass

    def deny_request(self, request_id: str, reason: str = None) -> bool:
        """Deny access request with optional explanation"""
        pass

    def notify_parent(self, request_id: str):
        """Send notification to parent (email, SMS, app push)"""
        pass

    def check_auto_approval_rules(self, domain: str, user: str) -> bool:
        """Check if request matches auto-approval criteria"""
        pass
```

### 4. Watchdog Service

**File**: `src/parental_control/watchdog_service.py`

**Purpose**: Monitor blocking server health and restart if needed

**Key Classes**:

```python
class BlockingServerWatchdog:
    """Monitor and restart blocking server"""

    def __init__(self, check_interval=30):
        self.check_interval = check_interval
        self.server_process = None
        self.consecutive_failures = 0

    def start_monitoring(self):
        """Begin health check loop"""
        pass

    def check_server_health(self) -> bool:
        """Ping server health endpoint"""
        try:
            response = requests.get('http://localhost:8080/health', timeout=5)
            return response.status_code == 200
        except:
            return False

    def restart_server(self):
        """Kill and restart blocking server"""
        pass

    def send_alert(self, message: str):
        """Alert admin of server issues"""
        pass
```

---

## Directory Structure Changes

```
src/parental_control/
├── blocking_server_v2.py           # NEW: Enhanced blocking server
├── blocked_page_manager.py         # NEW: Template selection logic
├── access_request_handler.py       # NEW: Access request processing
├── watchdog_service.py             # NEW: Health monitoring
├── templates/
│   ├── blocked/                    # NEW: Blocked page templates
│   │   ├── base_blocked.html       # Base template with common elements
│   │   ├── time_restricted.html    # Time-based blocking
│   │   ├── category_blocked.html   # Category blocking
│   │   ├── manual_block.html       # Manual blocks
│   │   ├── age_restricted.html     # Age-inappropriate content
│   │   └── custom.html             # Custom parent messages
│   ├── components/                 # NEW: Reusable components
│   │   ├── blocked_header.html     # Header with logo
│   │   ├── access_request_form.html # Access request form
│   │   ├── schedule_display.html   # Visual schedule
│   │   ├── countdown_timer.html    # Timer widget
│   │   └── alternatives_list.html  # Alternative suggestions
│   ├── admin/                      # NEW: Admin customization
│   │   ├── customize_blocked_pages.html
│   │   └── access_requests_dashboard.html
│   └── blocked.html                # EXISTING: Keep for backward compatibility
├── static/
│   ├── css/
│   │   ├── blocked_pages.css       # NEW: Main blocked page styles
│   │   ├── themes/                 # NEW: Theme variations
│   │   │   ├── kids.css            # Playful, colorful theme
│   │   │   ├── teens.css           # Modern, minimalist theme
│   │   │   ├── default.css         # Standard theme
│   │   │   └── dark.css            # Dark mode theme
│   │   └── admin.css               # EXISTING
│   ├── js/
│   │   ├── blocked_interactions.js # NEW: Interactive features
│   │   ├── countdown_timer.js      # NEW: Countdown logic
│   │   ├── access_request.js       # NEW: Request form handling
│   │   └── schedule_display.js     # NEW: Schedule visualization
│   ├── images/
│   │   ├── illustrations/          # NEW: SVG illustrations
│   │   │   ├── time_blocked.svg
│   │   │   ├── category_blocked.svg
│   │   │   ├── manual_block.svg
│   │   │   └── age_restricted.svg
│   │   └── icons/                  # NEW: Custom icons
│   │       ├── clock.svg
│   │       ├── shield.svg
│   │       ├── lock.svg
│   │       └── warning.svg
│   └── fonts/                      # NEW: Web fonts (optional)
└── certificates/                   # NEW: SSL certificates
    ├── localhost.crt
    └── localhost.key
```

---

## API Endpoints

### New Flask Routes

#### 1. Blocked Page Routes

```python
# Time-restricted blocking
@app.route('/blocked/time-restricted')
def blocked_time_restricted():
    """Show time-based blocking page"""
    domain = request.args.get('domain')
    next_available = request.args.get('next_available')
    return render_template('blocked/time_restricted.html', ...)

# Category-based blocking
@app.route('/blocked/category')
def blocked_category():
    """Show category-based blocking page"""
    domain = request.args.get('domain')
    category = request.args.get('category')
    return render_template('blocked/category_blocked.html', ...)

# Manual blocking
@app.route('/blocked/manual')
def blocked_manual():
    """Show manually blocked page with custom message"""
    domain = request.args.get('domain')
    custom_message = get_custom_message()
    return render_template('blocked/manual_block.html', ...)

# Age-restricted content
@app.route('/blocked/age-restricted')
def blocked_age_restricted():
    """Show age-restriction page"""
    domain = request.args.get('domain')
    age_requirement = request.args.get('age')
    return render_template('blocked/age_restricted.html', ...)
```

#### 2. Access Request API

```python
# Submit access request
@app.route('/api/request-access', methods=['POST'])
def api_request_access():
    """
    POST data:
    {
        "domain": "example.com",
        "user": "username",
        "reason": "Need for homework",
        "duration": 30
    }

    Returns:
    {
        "success": true,
        "request_id": "abc123",
        "status": "pending"
    }
    """
    pass

# Get request status
@app.route('/api/request-status/<request_id>')
def api_request_status(request_id):
    """
    Returns:
    {
        "status": "pending|approved|denied",
        "parent_response": "string",
        "granted_until": "datetime"
    }
    """
    pass

# Parent approval/denial
@app.route('/api/respond-to-request', methods=['POST'])
@login_required
def api_respond_to_request():
    """
    POST data:
    {
        "request_id": "abc123",
        "action": "approve|deny",
        "duration": 30,
        "message": "Approved for homework"
    }
    """
    pass
```

#### 3. Feedback API

```python
# Submit incorrect blocking report
@app.route('/api/submit-feedback', methods=['POST'])
def api_submit_feedback():
    """
    POST data:
    {
        "domain": "example.com",
        "feedback_type": "incorrect_block|bug|suggestion",
        "message": "This is an educational site"
    }
    """
    pass
```

#### 4. Admin Customization API

```python
# Get customization settings
@app.route('/api/admin/customization')
@login_required
def api_get_customization():
    """
    Returns:
    {
        "theme": "default",
        "custom_message": "string",
        "show_timer": true,
        "show_request_button": true,
        "logo_url": "/static/custom/logo.png"
    }
    """
    pass

# Update customization
@app.route('/api/admin/customization', methods=['POST'])
@login_required
def api_update_customization():
    """
    POST data:
    {
        "theme": "kids|teens|default|dark",
        "custom_message": "Contact your parent",
        "show_timer": true,
        "show_request_button": true
    }
    """
    pass

# Upload custom logo
@app.route('/api/admin/upload-logo', methods=['POST'])
@login_required
def api_upload_logo():
    """Handle logo file upload"""
    pass
```

---

## Technology Stack

### Backend

**Core**:
- Python 3.8+
- Flask 2.0+
- TinyDB 4.7+

**New Dependencies**:
```python
# requirements.txt additions
cryptography>=36.0.0      # SSL certificate generation
watchdog>=2.1.0           # File system monitoring
pillow>=9.0.0             # Image processing for logos
markdown>=3.3.0           # Markdown rendering for custom messages
bleach>=4.1.0             # HTML sanitization
python-i18n>=0.3.9        # Internationalization
```

### Frontend

**CSS Framework**: Tailwind CSS 3.x
- Utility-first approach
- Easy customization
- Small bundle size with purging
- Dark mode support built-in

**JavaScript**: Alpine.js 3.x (or Vue.js 3.x)
- Lightweight (15KB gzipped)
- Declarative syntax
- No build step required
- Good for progressive enhancement

**Icons**: Phosphor Icons or Lucide
- Modern, consistent design
- SVG-based
- Customizable size and color
- Open source

**Animations**:
- CSS transitions and animations
- Lottie (optional for complex animations)
- Lightweight and performant

### Development Tools

**Testing**:
- pytest for unit tests
- Selenium for browser testing
- pytest-flask for Flask testing
- coverage.py for code coverage

**Code Quality**:
- pylint for linting
- black for formatting
- mypy for type checking

**Build Tools**:
- npm for frontend dependencies
- webpack (optional) for asset bundling
- PostCSS for CSS processing

---

## Security Considerations

### 1. HTTPS Certificate Handling

**Challenge**: Self-signed certificates cause browser warnings

**Solutions**:
1. **Generate trusted local certificate**:
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes \
     -keyout localhost.key -out localhost.crt \
     -days 365 -subj "/CN=localhost"
   ```

2. **Add certificate to system trust store**:
   - Linux: `/usr/local/share/ca-certificates/`
   - Windows: Certificate Manager
   - macOS: Keychain Access

3. **Fallback to HTTP**: If HTTPS fails, serve over HTTP with warning

### 2. Input Validation

**Access Request Form**:
- Sanitize all user inputs
- Validate domain names
- Limit message length
- Prevent XSS attacks

```python
import bleach

def sanitize_access_request(data):
    return {
        'domain': bleach.clean(data['domain']),
        'reason': bleach.clean(data['reason'], tags=[]),
        'duration': min(int(data['duration']), 480)  # Max 8 hours
    }
```

### 3. Rate Limiting

**Prevent abuse of access request system**:
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/request-access', methods=['POST'])
@limiter.limit("5 per hour")  # Max 5 requests per hour
def api_request_access():
    pass
```

### 4. Authentication

**Admin endpoints require authentication**:
- All customization endpoints
- Access request responses
- Analytics access

**Session security**:
- CSRF protection (flask-wtf)
- Secure session cookies
- Session timeout (30 minutes)

---

## Performance Optimization

### 1. Template Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_compiled_template(template_name):
    return jinja_env.get_template(template_name)
```

### 2. Static Asset Optimization

- Minify CSS and JavaScript
- Compress images (use WebP format)
- Enable gzip compression
- Set far-future cache headers

```python
@app.route('/static/<path:filename>')
def serve_static(filename):
    response = send_from_directory('static', filename)
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response
```

### 3. Database Query Optimization

```python
# Cache blocked domains list
@lru_cache(maxsize=1)
def get_blocked_domains_cached():
    return db.get_all_blocked_domains()

# Clear cache when domains updated
def update_blocked_domains(domains):
    db.update_domains(domains)
    get_blocked_domains_cached.cache_clear()
```

### 4. Lazy Loading

**Load resources only when needed**:
- Defer non-critical JavaScript
- Lazy load images
- Use async/defer for scripts

```html
<!-- Defer non-critical JS -->
<script src="/static/js/access_request.js" defer></script>

<!-- Lazy load images -->
<img src="/static/images/placeholder.svg"
     data-src="/static/images/illustration.svg"
     loading="lazy" />
```

---

## Monitoring and Logging

### 1. Health Check Endpoint

```python
@app.route('/health')
def health_check():
    """Health check for monitoring"""
    checks = {
        'database': check_database_connection(),
        'blocking_server': check_blocking_server(),
        'disk_space': check_disk_space()
    }

    if all(checks.values()):
        return jsonify({'status': 'healthy', 'checks': checks}), 200
    else:
        return jsonify({'status': 'unhealthy', 'checks': checks}), 503
```

### 2. Structured Logging

```python
import logging
import json

class StructuredLogger:
    def log_blocked_request(self, domain, reason, user_agent):
        log_data = {
            'event': 'blocked_request',
            'domain': domain,
            'reason': reason,
            'user_agent': user_agent,
            'timestamp': datetime.now().isoformat()
        }
        logging.info(json.dumps(log_data))

    def log_access_request(self, request_id, domain, user):
        log_data = {
            'event': 'access_request',
            'request_id': request_id,
            'domain': domain,
            'user': user,
            'timestamp': datetime.now().isoformat()
        }
        logging.info(json.dumps(log_data))
```

### 3. Metrics Collection

Track key metrics:
- Blocked page views by type
- Access request volume
- Request approval rate
- Average response time
- Server uptime

---

## Deployment Strategy

### 1. Systemd Service Updates

**New service file**: `ubuntu-parental-control-watchdog.service`

```ini
[Unit]
Description=Ubuntu Parental Control Watchdog
After=network.target ubuntu-parental-control.service
Requires=ubuntu-parental-control.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m parental_control.watchdog_service
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Migration Script

**File**: `scripts/migrate_to_v2.py`

```python
def migrate_database():
    """Add new tables for v2 features"""
    # Add access_requests table
    # Add blocked_page_customizations table
    # Add alternative_sites table
    pass

def backup_old_templates():
    """Backup existing blocked.html"""
    pass

def generate_ssl_certificates():
    """Generate initial SSL certificates"""
    pass

def update_systemd_services():
    """Install watchdog service"""
    pass
```

### 3. Rollback Plan

Keep old blocking server for rollback:
- Rename `blocking_server.py` to `blocking_server_v1.py`
- Keep old template at `templates/blocked_v1.html`
- Configuration flag to switch versions

---

## Testing Strategy

### 1. Unit Tests

```python
# test_blocked_page_manager.py
def test_template_selection():
    manager = BlockedPageManager(db)
    template = manager.select_template_type('time restriction', None)
    assert template == 'time_restricted'

def test_customization_loading():
    manager = BlockedPageManager(db)
    custom = manager.get_customization()
    assert 'theme' in custom
    assert 'custom_message' in custom
```

### 2. Integration Tests

```python
# test_blocking_flow.py
def test_full_blocking_flow(client):
    # Simulate blocked request
    response = client.get('http://blocked-site.com')

    # Should redirect to blocked page
    assert response.status_code == 302
    assert '/blocked/' in response.location

    # Follow redirect
    response = client.get(response.location)
    assert b'Page Blocked' in response.data
```

### 3. Browser Tests (Selenium)

```python
# test_browser_interaction.py
def test_access_request_submission(driver):
    driver.get('http://localhost:8080/blocked/category?domain=test.com')

    # Fill out access request form
    driver.find_element_by_id('request-reason').send_keys('Homework')
    driver.find_element_by_id('request-duration').send_keys('30')
    driver.find_element_by_id('submit-request').click()

    # Verify success message
    message = driver.find_element_by_class('success-message')
    assert 'Request submitted' in message.text
```

---

## Documentation Requirements

### 1. Developer Documentation
- API reference
- Component documentation
- Database schema
- Setup instructions

### 2. User Documentation
- Installation guide
- Customization tutorial
- Troubleshooting guide
- FAQ

### 3. Admin Documentation
- Configuration options
- Monitoring guide
- Backup and restore procedures

---

## Next Steps

1. Review and approve architecture
2. Create detailed API specifications
3. Design database migrations
4. Set up development environment
5. Begin Phase 1 implementation

---

**Document Version**: 1.0
**Last Updated**: 2025-10-30
**Status**: Draft - Pending Technical Review
