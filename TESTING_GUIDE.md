# Testing Time Restrictions - Quick Guide

This guide will help you verify that time restrictions are working correctly in the Ubuntu Parental Control system.

## Prerequisites

1. Make sure the services are running:
   ```bash
   # Check if services are running
   sudo systemctl status ubuntu-parental-control

   # Or start them manually
   cd /home/user/ubuntu-parental-control
   sudo bash start_service.sh
   ```

2. Verify both servers are accessible:
   - Web Interface: http://localhost:5000
   - Blocking Server: http://localhost:8080

## Quick Test (Automated)

Run the automated test script:

```bash
cd /home/user/ubuntu-parental-control
sudo python3 test_time_restrictions.py --auto
```

This will:
- Show current time and access status
- Display existing schedules
- Test if blocking server is running
- Offer to add test schedules

## Manual Testing Methods

### Method 1: Using the Test Script (Interactive)

```bash
cd /home/user/ubuntu-parental-control
sudo python3 test_time_restrictions.py
```

Then use the menu:
1. Check current status (option 1)
2. Add a test schedule that blocks current time (option 3)
3. Check status again - should show BLOCKED
4. Test via blocking server (option 5)
5. Cleanup when done (option 7)

### Method 2: Using the Web Interface

1. Open http://localhost:5000/time-management in your browser
2. Check the **Current Status** section at the top
   - Shows if internet is currently allowed or blocked
   - Shows the reason if blocked

3. Add a test schedule:
   - Click "Add New Schedule"
   - Name: "Test Block"
   - Start time: 2 hours from now
   - End time: 3 hours from now
   - Select today's day
   - Save

4. Check status again - should show "Outside of allowed schedule"

### Method 3: Testing via HTTP Requests

Test the blocking server directly:

```bash
# Test with curl
curl -H "Host: www.example.com" http://localhost:8080

# If blocked, you'll get a block page
# If allowed, request will be proxied
```

### Method 4: Using Python Directly

```python
from parental_control.database import Database
from parental_control.time_management import TimeManager

db = Database()
tm = TimeManager(db)

# Check current status
is_allowed, reason = tm.is_access_allowed()
print(f"Allowed: {is_allowed}, Reason: {reason}")

# Show schedules
schedules = tm.get_schedules()
for s in schedules:
    print(f"{s['name']}: {s['start_time']} - {s['end_time']}")
```

## Testing Scenarios

### Scenario 1: Block Current Time

**Setup:**
- Create a schedule that does NOT include current time
- For example, if it's 14:00, create schedule for 16:00-17:00

**Expected Result:**
- Status should show "Outside of allowed schedule"
- Web requests should be blocked
- Block page should be displayed

**Test:**
```bash
# Add schedule (via web interface or script)
# Then test:
curl -H "Host: www.google.com" http://localhost:8080
# Should see block page
```

### Scenario 2: Allow Current Time

**Setup:**
- Create a schedule that INCLUDES current time
- For example, if it's 14:00, create schedule for 13:00-15:00

**Expected Result:**
- Status should show "Access allowed"
- Web requests should be proxied
- No block page

### Scenario 3: Daily Usage Limit

**Setup:**
```bash
# Set daily limit via Python
from parental_control.database import Database
from parental_control.time_management import TimeManager

db = Database()
tm = TimeManager(db)

# Set 60 minute limit
tm.set_daily_limit(60)

# Simulate 61 minutes of usage
for i in range(61):
    tm.record_usage(1)

# Check status
is_allowed, reason = tm.is_access_allowed()
print(f"Allowed: {is_allowed}, Reason: {reason}")
# Should show "Daily usage limit reached"
```

### Scenario 4: Overnight Schedule

**Setup:**
- Create schedule that crosses midnight (e.g., 22:00 - 06:00)
- Test before midnight and after midnight

**Expected:**
- Both times should be within allowed schedule

## Verification Checklist

Use this checklist to verify time restrictions are working:

- [ ] Blocking server is running (port 8080)
- [ ] Web interface is accessible (port 5000)
- [ ] Can view current status in web interface
- [ ] Can create a schedule via web interface
- [ ] Status correctly shows "blocked" when outside schedule
- [ ] Status correctly shows "allowed" when inside schedule
- [ ] Block page is displayed when accessing blocked content
- [ ] Block page shows correct reason (time restriction)
- [ ] Daily usage limit is enforced
- [ ] Overnight schedules work correctly
- [ ] Inactive schedules are ignored

## Troubleshooting

### Services Not Running

```bash
# Check status
sudo systemctl status ubuntu-parental-control

# View logs
sudo journalctl -u ubuntu-parental-control -f

# Restart
sudo systemctl restart ubuntu-parental-control
```

### Database Issues

```bash
# Check if database exists
ls -la /var/lib/ubuntu-parental/control.json

# View database contents
sudo cat /var/lib/ubuntu-parental/control.json | python3 -m json.tool
```

### Port Conflicts

```bash
# Check what's using port 8080
sudo netstat -tulpn | grep 8080

# Check what's using port 5000
sudo netstat -tulpn | grep 5000
```

### Time Not Blocking

**Common causes:**
1. No schedules defined (default is ALLOW all)
2. Schedule includes current time
3. Blocking server not running
4. Browser cached response
5. Request not going through blocking server

**Debug steps:**
```bash
# 1. Check current status
sudo python3 test_time_restrictions.py
# Select option 1

# 2. View active schedules
# Select option 2

# 3. Test blocking server
# Select option 5

# 4. Check logs
sudo journalctl -u ubuntu-parental-control -n 50
```

## Understanding Schedule Logic

**Important:** Schedules define when access is ALLOWED, not blocked.

- If NO schedules exist → Access is ALLOWED by default
- If schedules exist → Access is ALLOWED only during scheduled times
- All other times → Access is BLOCKED

**Example:**
- Schedule: Mon-Fri, 09:00-17:00
- Result: Internet allowed 9am-5pm on weekdays, blocked all other times

## Next Steps

After verifying time restrictions work:

1. Remove test schedules (option 7 in test script)
2. Create your real schedules via web interface
3. Set appropriate daily usage limits
4. Monitor logs to ensure everything works as expected

## Getting Help

If time restrictions aren't working:
1. Run the test script and share output
2. Check system logs
3. Verify service is running
4. Check database contents
5. Review this guide's troubleshooting section
