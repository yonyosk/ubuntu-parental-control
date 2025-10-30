# Database Schema - Enhanced Blocked Pages

## Overview

Ubuntu Parental Control uses TinyDB, a lightweight document-oriented database stored as JSON. This document defines the schema changes required for the enhanced blocked pages feature.

**Database Location**: `/var/lib/ubuntu-parental/control.json`
**Database Type**: TinyDB (JSON-based)
**Format**: Document-oriented (NoSQL)

---

## Existing Tables (No Changes)

These tables remain unchanged but are listed for reference:

### 1. `blocked_sites`
Manually blocked websites by parents

```python
{
    "domain": str,           # Domain name (e.g., "facebook.com")
    "category": str,         # Category (e.g., "SOCIAL_MEDIA")
    "date_added": str,       # ISO datetime string
    "added_by": str          # Username who added it (optional)
}
```

**Example**:
```json
{
    "domain": "facebook.com",
    "category": "SOCIAL_MEDIA",
    "date_added": "2025-01-15T14:30:00",
    "added_by": "parent"
}
```

---

### 2. `blacklist_domains`
Domains from UT1 blacklist categories

```python
{
    "domain": str,           # Domain name
    "category": str          # Blacklist category
}
```

**Example**:
```json
{
    "domain": "gambling-site.com",
    "category": "gambling"
}
```

---

### 3. `blacklist_categories`
Active/inactive blacklist categories

```python
{
    "category": str,         # Category name
    "active": bool,          # Whether category is enabled
    "description": str       # Category description
}
```

**Example**:
```json
{
    "category": "adult",
    "active": true,
    "description": "Adult content websites"
}
```

---

### 4. `activity_log`
Logging of blocking activity

```python
{
    "domain": str,           # Accessed domain
    "action": str,           # "blocked" or "allowed"
    "category": str,         # Block category
    "timestamp": str,        # ISO datetime string
    "client_ip": str,        # Client IP address
    "reason": str,           # Reason for action
    "user_agent": str        # Browser user agent (optional)
}
```

---

### 5. `time_schedules`
Time-based access restrictions

```python
{
    "name": str,             # Schedule name
    "enabled": bool,         # Whether schedule is active
    "days": list,            # Days of week [0-6, 0=Monday]
    "start_time": str,       # Start time "HH:MM"
    "end_time": str,         # End time "HH:MM"
    "categories": list,      # Affected categories
    "domains": list          # Specific domains (optional)
}
```

---

### 6. `settings`
Global system settings

```python
{
    "setting_name": str,     # Setting key
    "setting_value": any     # Setting value (various types)
}
```

---

### 7. `temporary_exceptions`
Temporary access grants

```python
{
    "domain": str,           # Domain with temporary access
    "expires_at": str,       # ISO datetime string
    "reason": str,           # Reason for exception
    "granted_by": str        # Who granted it
}
```

---

### 8. `daily_usage`
Daily screen time tracking

```python
{
    "date": str,             # Date "YYYY-MM-DD"
    "domain": str,           # Domain accessed
    "duration_seconds": int, # Time spent
    "category": str          # Domain category
}
```

---

## New Tables

### 9. `access_requests` (NEW)
User requests for temporary access to blocked sites

**Purpose**: Track when users request access to blocked websites, allowing parents to approve or deny requests.

**Schema**:
```python
{
    "request_id": str,          # Unique identifier (UUID)
    "domain": str,              # Requested domain
    "user": str,                # Username making request
    "reason": str,              # User's explanation (max 500 chars)
    "duration_requested": int,  # Minutes of access requested
    "submitted_at": str,        # ISO datetime string
    "status": str,              # "pending", "approved", "denied"
    "responded_at": str,        # ISO datetime string (null if pending)
    "responded_by": str,        # Parent username (null if pending)
    "parent_response": str,     # Parent's message to user (optional)
    "granted_duration": int,    # Actual minutes granted (may differ from requested)
    "grant_expires_at": str,    # ISO datetime when access expires
    "client_ip": str,           # IP address of requester
    "user_agent": str,          # Browser user agent
    "block_reason": str,        # Why domain was blocked
    "block_category": str       # Category that triggered block
}
```

**Example - Pending Request**:
```json
{
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "domain": "youtube.com",
    "user": "johnny",
    "reason": "I need to watch a tutorial video for my science project on photosynthesis",
    "duration_requested": 30,
    "submitted_at": "2025-10-30T15:45:00",
    "status": "pending",
    "responded_at": null,
    "responded_by": null,
    "parent_response": null,
    "granted_duration": null,
    "grant_expires_at": null,
    "client_ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0",
    "block_reason": "time_restriction",
    "block_category": "VIDEO"
}
```

**Example - Approved Request**:
```json
{
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "domain": "youtube.com",
    "user": "johnny",
    "reason": "I need to watch a tutorial video for my science project on photosynthesis",
    "duration_requested": 30,
    "submitted_at": "2025-10-30T15:45:00",
    "status": "approved",
    "responded_at": "2025-10-30T15:50:00",
    "responded_by": "mom",
    "parent_response": "Approved for homework. Stay focused!",
    "granted_duration": 30,
    "grant_expires_at": "2025-10-30T16:20:00",
    "client_ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0",
    "block_reason": "time_restriction",
    "block_category": "VIDEO"
}
```

**Example - Denied Request**:
```json
{
    "request_id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901",
    "domain": "instagram.com",
    "user": "sarah",
    "reason": "want to check messages",
    "duration_requested": 60,
    "submitted_at": "2025-10-30T16:00:00",
    "status": "denied",
    "responded_at": "2025-10-30T16:05:00",
    "responded_by": "dad",
    "parent_response": "Not during homework time. You can check after dinner.",
    "granted_duration": null,
    "grant_expires_at": null,
    "client_ip": "192.168.1.101",
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
    "block_reason": "category_block",
    "block_category": "SOCIAL_MEDIA"
}
```

**Indexes**:
- `status` (for querying pending requests)
- `user` (for user's request history)
- `domain` (for per-domain request patterns)
- `submitted_at` (for chronological sorting)

**Queries**:
```python
# Get all pending requests
pending = db.table('access_requests').search(
    Query().status == 'pending'
)

# Get requests by user
user_requests = db.table('access_requests').search(
    Query().user == 'johnny'
)

# Get recent requests (last 7 days)
recent = db.table('access_requests').search(
    Query().submitted_at >= seven_days_ago
)

# Get approval rate
all_requests = db.table('access_requests').all()
approved = [r for r in all_requests if r['status'] == 'approved']
approval_rate = len(approved) / len(all_requests) * 100
```

---

### 10. `blocked_page_customizations` (NEW)
Parent customization settings for blocked pages

**Purpose**: Store parent preferences for how blocked pages appear and behave.

**Schema**:
```python
{
    "customization_id": str,    # Unique identifier (default: "default")
    "theme": str,               # "default", "dark", "kids", "teens"
    "custom_message": str,      # Custom message for manual blocks (max 1000 chars)
    "custom_logo_path": str,    # Path to custom logo image (optional)
    "show_timer": bool,         # Show countdown timer on time-restricted pages
    "show_request_button": bool,# Show "Request Access" button
    "show_alternatives": bool,  # Show alternative site suggestions
    "show_schedule": bool,      # Show schedule on time-restricted pages
    "show_educational_content": bool,  # Show digital wellness tips
    "language": str,            # Language code (e.g., "en", "es", "fr")
    "auto_approval_enabled": bool,     # Enable auto-approval rules
    "require_reason": bool,     # Require reason for access requests
    "min_reason_length": int,   # Minimum characters for request reason
    "notification_email": str,  # Email for access request notifications (optional)
    "notification_enabled": bool,      # Enable email notifications
    "updated_at": str,          # Last update timestamp
    "updated_by": str           # Who made the update
}
```

**Example - Default Customization**:
```json
{
    "customization_id": "default",
    "theme": "default",
    "custom_message": "This website has been blocked. If you need access, please talk to your parent.",
    "custom_logo_path": null,
    "show_timer": true,
    "show_request_button": true,
    "show_alternatives": true,
    "show_schedule": true,
    "show_educational_content": true,
    "language": "en",
    "auto_approval_enabled": false,
    "require_reason": true,
    "min_reason_length": 20,
    "notification_email": "parent@example.com",
    "notification_enabled": true,
    "updated_at": "2025-10-30T12:00:00",
    "updated_by": "admin"
}
```

**Example - Kids Theme**:
```json
{
    "customization_id": "default",
    "theme": "kids",
    "custom_message": "Oops! This website isn't available right now. Ask your parent if you need help! 😊",
    "custom_logo_path": "/static/uploads/family_logo.png",
    "show_timer": true,
    "show_request_button": true,
    "show_alternatives": true,
    "show_schedule": false,
    "show_educational_content": true,
    "language": "en",
    "auto_approval_enabled": false,
    "require_reason": true,
    "min_reason_length": 10,
    "notification_email": "mom@example.com",
    "notification_enabled": true,
    "updated_at": "2025-10-30T14:00:00",
    "updated_by": "mom"
}
```

**Queries**:
```python
# Get current customization
customization = db.table('blocked_page_customizations').get(
    Query().customization_id == 'default'
)

# Update customization
db.table('blocked_page_customizations').update(
    {'theme': 'dark', 'updated_at': datetime.now().isoformat()},
    Query().customization_id == 'default'
)
```

---

### 11. `alternative_sites` (NEW)
Suggested alternative websites for blocked categories

**Purpose**: Provide educational or appropriate alternatives when sites are blocked.

**Schema**:
```python
{
    "alternative_id": str,      # Unique identifier (UUID)
    "name": str,                # Site name (e.g., "Khan Academy")
    "url": str,                 # Full URL
    "description": str,         # Brief description (max 200 chars)
    "blocked_category": str,    # Category this is alternative for
    "target_age_min": int,      # Minimum age (null for all ages)
    "target_age_max": int,      # Maximum age (null for all ages)
    "educational": bool,        # Whether site is educational
    "enabled": bool,            # Whether to show this alternative
    "sort_order": int,          # Display order (lower = first)
    "added_at": str,            # ISO datetime string
    "added_by": str,            # Who added it ("system" or username)
    "icon_url": str             # Icon/logo URL (optional)
}
```

**Example - Educational Alternative**:
```json
{
    "alternative_id": "alt-001",
    "name": "Khan Academy",
    "url": "https://www.khanacademy.org",
    "description": "Free educational videos and exercises on many subjects",
    "blocked_category": "VIDEO",
    "target_age_min": 6,
    "target_age_max": null,
    "educational": true,
    "enabled": true,
    "sort_order": 1,
    "added_at": "2025-10-30T12:00:00",
    "added_by": "system",
    "icon_url": "https://cdn.kastatic.org/images/apple-touch-icon-72x72.png"
}
```

**Example - Social Alternative**:
```json
{
    "alternative_id": "alt-015",
    "name": "Scratch",
    "url": "https://scratch.mit.edu",
    "description": "Create and share interactive stories, games, and animations",
    "blocked_category": "SOCIAL_MEDIA",
    "target_age_min": 8,
    "target_age_max": 16,
    "educational": true,
    "enabled": true,
    "sort_order": 2,
    "added_at": "2025-10-30T12:00:00",
    "added_by": "system",
    "icon_url": "https://scratch.mit.edu/images/logo_sm.png"
}
```

**Pre-populated Alternatives** (System Defaults):

**Category: VIDEO**
- Khan Academy (educational videos)
- TED-Ed (educational talks)
- National Geographic Kids (nature videos)
- NASA Kids' Club (space videos)

**Category: SOCIAL_MEDIA**
- Scratch (creative community)
- Kidzworld (safe social network for kids)
- Grom Social (parent-approved social network)

**Category: GAMING**
- Code.org (coding games)
- Typing Club (typing games)
- PBS Kids Games (educational games)
- Math Playground (math games)

**Queries**:
```python
# Get alternatives for category
alternatives = db.table('alternative_sites').search(
    (Query().blocked_category == 'VIDEO') &
    (Query().enabled == True)
)

# Get age-appropriate alternatives
alternatives = db.table('alternative_sites').search(
    (Query().blocked_category == category) &
    (Query().target_age_min <= user_age) &
    ((Query().target_age_max >= user_age) | (Query().target_age_max == None))
)

# Sort by order
alternatives.sort(key=lambda x: x['sort_order'])
```

---

### 12. `auto_approval_rules` (NEW)
Rules for automatically approving access requests

**Purpose**: Define patterns for automatic approval of requests without parent intervention.

**Schema**:
```python
{
    "rule_id": str,             # Unique identifier (UUID)
    "rule_name": str,           # Human-readable name
    "enabled": bool,            # Whether rule is active
    "priority": int,            # Rule priority (higher = checked first)
    "conditions": dict,         # Conditions to match
    "action": str,              # "auto_approve" or "notify_only"
    "grant_duration": int,      # Minutes to grant if approved
    "max_uses_per_day": int,    # Maximum times rule can trigger per day (null = unlimited)
    "applies_to_users": list,   # Usernames (empty = all users)
    "applies_to_domains": list, # Domain patterns (empty = all domains)
    "applies_to_categories": list,  # Categories (empty = all)
    "time_restrictions": dict,  # When rule applies
    "created_at": str,          # ISO datetime string
    "created_by": str,          # Who created the rule
    "last_used_at": str,        # Last time rule triggered
    "use_count": int            # How many times rule has triggered
}
```

**Example - Homework Time Auto-Approval**:
```json
{
    "rule_id": "rule-001",
    "rule_name": "Homework Research Auto-Approve",
    "enabled": true,
    "priority": 10,
    "conditions": {
        "reason_contains": ["homework", "project", "assignment", "research"],
        "duration_max": 60,
        "min_reason_length": 30
    },
    "action": "auto_approve",
    "grant_duration": 30,
    "max_uses_per_day": 3,
    "applies_to_users": ["johnny", "sarah"],
    "applies_to_domains": [],
    "applies_to_categories": ["VIDEO", "SOCIAL_MEDIA"],
    "time_restrictions": {
        "days": [0, 1, 2, 3, 4],
        "start_time": "15:00",
        "end_time": "18:00"
    },
    "created_at": "2025-10-30T12:00:00",
    "created_by": "mom",
    "last_used_at": "2025-10-30T16:45:00",
    "use_count": 12
}
```

**Example - Educational Sites Always Allowed**:
```json
{
    "rule_id": "rule-002",
    "rule_name": "Educational Sites Auto-Approve",
    "enabled": true,
    "priority": 20,
    "conditions": {
        "educational_domains": true
    },
    "action": "auto_approve",
    "grant_duration": 120,
    "max_uses_per_day": null,
    "applies_to_users": [],
    "applies_to_domains": [
        "*.edu",
        "khanacademy.org",
        "coursera.org",
        "edx.org",
        "wikipedia.org"
    ],
    "applies_to_categories": [],
    "time_restrictions": null,
    "created_at": "2025-10-30T12:00:00",
    "created_by": "dad",
    "last_used_at": "2025-10-30T14:20:00",
    "use_count": 45
}
```

**Queries**:
```python
# Get active rules in priority order
rules = db.table('auto_approval_rules').search(
    Query().enabled == True
)
rules.sort(key=lambda x: x['priority'], reverse=True)

# Check if rule can be used today
def can_use_rule(rule_id, user):
    rule = db.table('auto_approval_rules').get(Query().rule_id == rule_id)
    if rule['max_uses_per_day'] is None:
        return True

    today = datetime.now().date().isoformat()
    uses_today = db.table('access_requests').count(
        (Query().status == 'approved') &
        (Query().user == user) &
        (Query().submitted_at >= today) &
        (Query().auto_approved_by_rule == rule_id)
    )
    return uses_today < rule['max_uses_per_day']
```

---

### 13. `educational_content` (NEW)
Digital wellness tips and educational content

**Purpose**: Store educational messages to display on blocked pages.

**Schema**:
```python
{
    "content_id": str,          # Unique identifier (UUID)
    "content_type": str,        # "tip", "fact", "resource"
    "title": str,               # Title/headline (max 100 chars)
    "content": str,             # Main content (max 500 chars)
    "category": str,            # Related category (null = all)
    "age_group": str,           # "kids" (6-11), "teens" (12-17), "all"
    "language": str,            # Language code
    "icon": str,                # Icon name/emoji
    "link_url": str,            # External link (optional)
    "link_text": str,           # Link text (optional)
    "enabled": bool,            # Whether to show this content
    "priority": int,            # Display priority
    "view_count": int,          # How many times shown
    "last_shown_at": str,       # Last displayed timestamp
    "created_at": str,          # ISO datetime string
    "created_by": str           # Who created it
}
```

**Example - Screen Time Tip**:
```json
{
    "content_id": "edu-001",
    "content_type": "tip",
    "title": "Take a Break!",
    "content": "The 20-20-20 rule: Every 20 minutes, look at something 20 feet away for 20 seconds. This helps your eyes rest from screen time.",
    "category": null,
    "age_group": "all",
    "language": "en",
    "icon": "👀",
    "link_url": "https://www.aoa.org/healthy-eyes/eye-health-for-life/computer-vision-syndrome",
    "link_text": "Learn more about eye health",
    "enabled": true,
    "priority": 5,
    "view_count": 127,
    "last_shown_at": "2025-10-30T16:00:00",
    "created_at": "2025-10-30T12:00:00",
    "created_by": "system"
}
```

**Example - Social Media Fact (Teens)**:
```json
{
    "content_id": "edu-015",
    "content_type": "fact",
    "title": "Did You Know?",
    "content": "Studies show that taking breaks from social media can improve mood, reduce anxiety, and help you sleep better. Try focusing on offline activities!",
    "category": "SOCIAL_MEDIA",
    "age_group": "teens",
    "language": "en",
    "icon": "🧠",
    "link_url": "https://www.commonsensemedia.org/social-media",
    "link_text": "Social media tips for teens",
    "enabled": true,
    "priority": 8,
    "view_count": 89,
    "last_shown_at": "2025-10-30T15:30:00",
    "created_at": "2025-10-30T12:00:00",
    "created_by": "system"
}
```

**Example - Resource (Kids)**:
```json
{
    "content_id": "edu-030",
    "content_type": "resource",
    "title": "Be Internet Awesome!",
    "content": "Learn how to be safe, smart, and kind online with Google's free internet safety program designed just for kids.",
    "category": null,
    "age_group": "kids",
    "language": "en",
    "icon": "🛡️",
    "link_url": "https://beinternetawesome.withgoogle.com",
    "link_text": "Play Internet Safety Games",
    "enabled": true,
    "priority": 10,
    "view_count": 45,
    "last_shown_at": "2025-10-30T14:00:00",
    "created_at": "2025-10-30T12:00:00",
    "created_by": "system"
}
```

**Queries**:
```python
# Get random educational content
def get_random_content(category=None, age_group='all'):
    query = (Query().enabled == True) & (Query().age_group.one_of([age_group, 'all']))

    if category:
        query &= (Query().category.one_of([category, None]))

    content = db.table('educational_content').search(query)

    if content:
        # Weight by priority and inverse of view_count
        return weighted_random_choice(content)
    return None

# Update view count
db.table('educational_content').update(
    {
        'view_count': content['view_count'] + 1,
        'last_shown_at': datetime.now().isoformat()
    },
    Query().content_id == content_id
)
```

---

### 14. `user_feedback` (NEW)
User feedback on blocked pages and incorrect blocks

**Purpose**: Allow users to report issues and provide feedback.

**Schema**:
```python
{
    "feedback_id": str,         # Unique identifier (UUID)
    "feedback_type": str,       # "incorrect_block", "bug", "suggestion"
    "domain": str,              # Domain related to feedback
    "category": str,            # Block category (if applicable)
    "user": str,                # Username submitting feedback
    "message": str,             # Feedback message (max 1000 chars)
    "submitted_at": str,        # ISO datetime string
    "status": str,              # "new", "reviewed", "resolved", "dismissed"
    "reviewed_at": str,         # ISO datetime string (null if not reviewed)
    "reviewed_by": str,         # Who reviewed it
    "admin_notes": str,         # Admin notes (optional)
    "action_taken": str,        # What was done (optional)
    "client_ip": str,           # IP address
    "user_agent": str           # Browser user agent
}
```

**Example - Incorrect Block Report**:
```json
{
    "feedback_id": "fb-001",
    "feedback_type": "incorrect_block",
    "domain": "scratch.mit.edu",
    "category": "SOCIAL_MEDIA",
    "user": "johnny",
    "message": "This website is for learning to code, not social media. My teacher assigned us to use it for computer class.",
    "submitted_at": "2025-10-30T14:30:00",
    "status": "reviewed",
    "reviewed_at": "2025-10-30T15:00:00",
    "reviewed_by": "mom",
    "admin_notes": "Good catch! This is an educational site.",
    "action_taken": "Added to whitelist",
    "client_ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0"
}
```

---

## Migration Script

### Migration Process

**File**: `scripts/migrate_database_v2.py`

```python
#!/usr/bin/env python3
"""
Database migration script for Enhanced Blocked Pages v2
"""

import sys
import os
from datetime import datetime
from tinydb import TinyDB, Query
import uuid
import shutil

DB_PATH = '/var/lib/ubuntu-parental/control.json'
BACKUP_DIR = '/var/lib/ubuntu-parental/backups/'

def backup_database():
    """Create backup before migration"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'db_backup_{timestamp}.json')

    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(DB_PATH, backup_path)

    print(f"✓ Database backed up to: {backup_path}")
    return backup_path

def create_new_tables(db):
    """Create new tables with default data"""

    # 1. Create access_requests table (empty)
    db.table('access_requests')
    print("✓ Created 'access_requests' table")

    # 2. Create blocked_page_customizations table with defaults
    customizations = db.table('blocked_page_customizations')
    customizations.insert({
        'customization_id': 'default',
        'theme': 'default',
        'custom_message': 'This website has been blocked. If you need access, please talk to your parent.',
        'custom_logo_path': None,
        'show_timer': True,
        'show_request_button': True,
        'show_alternatives': True,
        'show_schedule': True,
        'show_educational_content': True,
        'language': 'en',
        'auto_approval_enabled': False,
        'require_reason': True,
        'min_reason_length': 20,
        'notification_email': None,
        'notification_enabled': False,
        'updated_at': datetime.now().isoformat(),
        'updated_by': 'system'
    })
    print("✓ Created 'blocked_page_customizations' table with defaults")

    # 3. Create alternative_sites table with default alternatives
    alternatives = db.table('alternative_sites')
    default_alternatives = get_default_alternatives()
    for alt in default_alternatives:
        alternatives.insert(alt)
    print(f"✓ Created 'alternative_sites' table with {len(default_alternatives)} defaults")

    # 4. Create auto_approval_rules table (empty)
    db.table('auto_approval_rules')
    print("✓ Created 'auto_approval_rules' table")

    # 5. Create educational_content table with default content
    education = db.table('educational_content')
    default_content = get_default_educational_content()
    for content in default_content:
        education.insert(content)
    print(f"✓ Created 'educational_content' table with {len(default_content)} defaults")

    # 6. Create user_feedback table (empty)
    db.table('user_feedback')
    print("✓ Created 'user_feedback' table")

def get_default_alternatives():
    """Return default alternative sites"""
    return [
        # VIDEO alternatives
        {
            'alternative_id': str(uuid.uuid4()),
            'name': 'Khan Academy',
            'url': 'https://www.khanacademy.org',
            'description': 'Free educational videos and exercises',
            'blocked_category': 'VIDEO',
            'target_age_min': 6,
            'target_age_max': None,
            'educational': True,
            'enabled': True,
            'sort_order': 1,
            'added_at': datetime.now().isoformat(),
            'added_by': 'system',
            'icon_url': None
        },
        {
            'alternative_id': str(uuid.uuid4()),
            'name': 'TED-Ed',
            'url': 'https://ed.ted.com',
            'description': 'Educational videos from experts',
            'blocked_category': 'VIDEO',
            'target_age_min': 10,
            'target_age_max': None,
            'educational': True,
            'enabled': True,
            'sort_order': 2,
            'added_at': datetime.now().isoformat(),
            'added_by': 'system',
            'icon_url': None
        },
        # SOCIAL_MEDIA alternatives
        {
            'alternative_id': str(uuid.uuid4()),
            'name': 'Scratch',
            'url': 'https://scratch.mit.edu',
            'description': 'Create and share interactive projects',
            'blocked_category': 'SOCIAL_MEDIA',
            'target_age_min': 8,
            'target_age_max': 16,
            'educational': True,
            'enabled': True,
            'sort_order': 1,
            'added_at': datetime.now().isoformat(),
            'added_by': 'system',
            'icon_url': None
        },
        # GAMING alternatives
        {
            'alternative_id': str(uuid.uuid4()),
            'name': 'Code.org',
            'url': 'https://code.org',
            'description': 'Learn computer science through fun games',
            'blocked_category': 'GAMING',
            'target_age_min': 6,
            'target_age_max': None,
            'educational': True,
            'enabled': True,
            'sort_order': 1,
            'added_at': datetime.now().isoformat(),
            'added_by': 'system',
            'icon_url': None
        }
    ]

def get_default_educational_content():
    """Return default educational content"""
    return [
        {
            'content_id': str(uuid.uuid4()),
            'content_type': 'tip',
            'title': 'Take a Break!',
            'content': 'The 20-20-20 rule: Every 20 minutes, look at something 20 feet away for 20 seconds.',
            'category': None,
            'age_group': 'all',
            'language': 'en',
            'icon': '👀',
            'link_url': None,
            'link_text': None,
            'enabled': True,
            'priority': 5,
            'view_count': 0,
            'last_shown_at': None,
            'created_at': datetime.now().isoformat(),
            'created_by': 'system'
        },
        {
            'content_id': str(uuid.uuid4()),
            'content_type': 'fact',
            'title': 'Digital Wellness',
            'content': 'Studies show that taking breaks from screens can improve your mood and help you sleep better!',
            'category': None,
            'age_group': 'all',
            'language': 'en',
            'icon': '🧠',
            'link_url': None,
            'link_text': None,
            'enabled': True,
            'priority': 5,
            'view_count': 0,
            'last_shown_at': None,
            'created_at': datetime.now().isoformat(),
            'created_by': 'system'
        }
    ]

def verify_migration(db):
    """Verify all tables exist"""
    required_tables = [
        'access_requests',
        'blocked_page_customizations',
        'alternative_sites',
        'auto_approval_rules',
        'educational_content',
        'user_feedback'
    ]

    for table_name in required_tables:
        table = db.table(table_name)
        if table.all() is None:
            print(f"✗ Table '{table_name}' not found!")
            return False

    print("✓ All tables verified")
    return True

def main():
    """Main migration process"""
    print("=" * 60)
    print("Enhanced Blocked Pages v2 - Database Migration")
    print("=" * 60)

    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"✗ Database not found at {DB_PATH}")
        sys.exit(1)

    # Backup database
    print("\n[1/4] Backing up database...")
    backup_path = backup_database()

    # Open database
    print("\n[2/4] Opening database...")
    db = TinyDB(DB_PATH)
    print("✓ Database opened")

    # Create new tables
    print("\n[3/4] Creating new tables...")
    try:
        create_new_tables(db)
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        print(f"Restore from backup: {backup_path}")
        sys.exit(1)

    # Verify migration
    print("\n[4/4] Verifying migration...")
    if not verify_migration(db):
        print(f"✗ Verification failed! Restore from backup: {backup_path}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ Migration completed successfully!")
    print("=" * 60)
    print(f"\nBackup saved at: {backup_path}")
    print("You can now use the enhanced blocked pages features.")

if __name__ == '__main__':
    main()
```

---

## Rollback Procedure

If migration fails or issues arise:

1. **Stop Services**:
   ```bash
   sudo systemctl stop ubuntu-parental-control
   sudo systemctl stop ubuntu-parental-control-watchdog
   ```

2. **Restore Backup**:
   ```bash
   sudo cp /var/lib/ubuntu-parental/backups/db_backup_TIMESTAMP.json \
          /var/lib/ubuntu-parental/control.json
   ```

3. **Restart Services**:
   ```bash
   sudo systemctl start ubuntu-parental-control
   ```

---

## Database Maintenance

### Regular Backups
- Automatic backup before any migration
- Retain last 30 days of backups
- Compress backups older than 7 days

### Data Retention
- **access_requests**: Keep 90 days
- **activity_log**: Keep 90 days
- **user_feedback**: Keep indefinitely until resolved
- **educational_content**: Keep indefinitely (track view_count)

### Cleanup Script

```python
def cleanup_old_data(db, days=90):
    """Remove old access requests and activity logs"""
    from datetime import timedelta

    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

    # Remove old access requests
    requests_table = db.table('access_requests')
    removed_requests = requests_table.remove(
        Query().submitted_at < cutoff_date
    )

    # Remove old activity logs
    activity_table = db.table('activity_log')
    removed_logs = activity_table.remove(
        Query().timestamp < cutoff_date
    )

    print(f"Removed {len(removed_requests)} old access requests")
    print(f"Removed {len(removed_logs)} old activity logs")
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-30
**Status**: Draft - Pending Review
