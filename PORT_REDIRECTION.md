# Port Redirection for Blocking Pages

## Overview

This document explains how the port redirection system works to ensure blocked websites show friendly blocking pages instead of connection errors.

## The Problem

When a website is blocked:
1. `/etc/hosts` redirects the domain to `127.0.0.1`
2. User's browser tries to connect to `127.0.0.1:80` (HTTP) or `127.0.0.1:443` (HTTPS)
3. **Blocking server runs on port 8080** (not 80 or 443)
4. **Result without redirection**: "Connection refused" error ❌

## The Solution: iptables Port Redirection

We use iptables NAT rules to redirect traffic from ports 80/443 to port 8080:

```
Browser request → 127.0.0.1:80  ─┐
                                  ├─→ iptables NAT → 127.0.0.1:8080 → Blocking Server
Browser request → 127.0.0.1:443 ─┘
```

## Architecture

### Components

1. **PortRedirector** (`src/parental_control/port_redirector.py`)
   - Manages iptables NAT rules
   - Creates `PARENTAL_REDIRECT` chain
   - Redirects port 80 → 8080
   - Redirects port 443 → 8080

2. **BlockingServer** (`src/parental_control/blocking_server.py`)
   - HTTP server on port 8080
   - Detects blocked domains
   - Redirects to `/blocked` page with parameters

3. **Blocking Pages** (`templates/blocked/`)
   - Hebrew/English bilingual templates
   - Theme support (default, dark, kids, teens)
   - User language switcher

### iptables Rules

When port redirection is **enabled**:

```bash
# Create custom chain
iptables -t nat -N PARENTAL_REDIRECT
iptables -t nat -I OUTPUT 1 -j PARENTAL_REDIRECT

# Redirect HTTP (port 80)
iptables -t nat -A PARENTAL_REDIRECT \
    -p tcp -d 127.0.0.1 --dport 80 \
    -j REDIRECT --to-port 8080

# Redirect HTTPS (port 443)
iptables -t nat -A PARENTAL_REDIRECT \
    -p tcp -d 127.0.0.1 --dport 443 \
    -j REDIRECT --to-port 8080
```

When port redirection is **disabled**:

```bash
# Flush rules
iptables -t nat -F PARENTAL_REDIRECT
```

## Usage

### Automatic (Recommended)

Port redirection is **automatically enabled** when the blocking server starts:

```python
from parental_control.parental_control import ParentalControl

pc = ParentalControl()
pc.start_blocking_server()  # Also enables port redirection
```

### Manual Control

```python
from parental_control.port_redirector import PortRedirector

# Create redirector
redirector = PortRedirector(blocking_server_port=8080)

# Enable redirection
redirector.enable_redirection()

# Check status
status = redirector.get_status()
print(f"Enabled: {status['enabled']}")
print(f"Rules: {status['rule_count']}")

# Disable redirection
redirector.disable_redirection()

# Complete cleanup (for uninstallation)
redirector.cleanup()
```

## Testing

### Test Script

Run the comprehensive test suite:

```bash
sudo python3 test_port_redirection.py
```

This tests:
- PortRedirector class functionality
- Integration with ParentalControl
- iptables rule creation/removal
- Blocking server startup/shutdown

### Manual Testing

1. **Start the service**:
   ```bash
   sudo ./start_service.sh
   ```

2. **Block a domain**:
   ```bash
   # Via web interface at http://localhost:5000
   # Or via CLI:
   sudo python3 -c "
   from parental_control.parental_control import ParentalControl
   pc = ParentalControl()
   pc.add_blocked_site('example.com')
   "
   ```

3. **Test HTTP**:
   ```bash
   curl http://example.com
   # Should show redirect to blocking page
   ```

4. **Test HTTPS**:
   ```bash
   curl https://example.com
   # Should show redirect to blocking page
   ```

5. **Test in browser**:
   - Open browser
   - Navigate to blocked domain
   - Should see beautiful blocking page (Hebrew/English)
   - Can switch language with dropdown

### Verify iptables Rules

Check current NAT rules:

```bash
sudo iptables -t nat -L PARENTAL_REDIRECT -n -v
```

Expected output:
```
Chain PARENTAL_REDIRECT (1 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 REDIRECT   tcp  --  *      *       0.0.0.0/0            127.0.0.1            tcp dpt:80 redir ports 8080
    0     0 REDIRECT   tcp  --  *      *       0.0.0.0/0            127.0.0.1            tcp dpt:443 redir ports 8080
```

## HTTPS Handling

### The HTTPS Challenge

When browsers connect to HTTPS sites, they expect:
1. SSL/TLS handshake
2. Valid certificate
3. Encrypted connection

Our blocking server on port 8080 is plain HTTP, so we can't provide proper HTTPS.

### Our Solution

1. **Port 443 redirected to port 8080** (via iptables)
2. **Blocking server detects HTTPS intent** (via headers)
3. **Shows blocking page via HTTP redirect**
4. **Browser follows redirect** (usually works)

### Limitations

- **Certificate warnings**: Some browsers may show SSL errors before redirecting
- **HSTS domains**: Sites with HSTS (HTTP Strict Transport Security) may not redirect
- **Certificate pinning**: Apps with pinned certificates will fail

### Workarounds

For problematic HTTPS sites:
1. Block at DNS level (already done via hosts file)
2. Show generic "blocked" message
3. User sees connection error (but site is still blocked)

## Security Considerations

### Permissions

- iptables requires **root privileges**
- Service must run as root
- Rules persist until explicitly removed

### Safety Features

1. **Custom chain**: All rules in `PARENTAL_REDIRECT` chain
2. **Atomic operations**: Rules added/removed atomically
3. **Cleanup on stop**: Rules removed when blocking server stops
4. **No system rules modified**: Only affects 127.0.0.1 traffic

### Persistence

- iptables rules are **not persistent** across reboots
- Service automatically re-applies rules on startup
- To make persistent: Use `iptables-persistent` package

```bash
# Optional: Make rules persistent
sudo apt-get install iptables-persistent
sudo netfilter-persistent save
```

## Troubleshooting

### Rules not working

1. **Check if running as root**:
   ```bash
   id
   # Should show uid=0(root)
   ```

2. **Verify iptables is installed**:
   ```bash
   which iptables
   ```

3. **Check for conflicting rules**:
   ```bash
   sudo iptables -t nat -L -n -v
   ```

4. **Review logs**:
   ```bash
   tail -f /var/log/ubuntu-parental-control.log
   ```

### Connection still refused

1. **Verify blocking server is running**:
   ```bash
   sudo netstat -tlnp | grep 8080
   # Should show Python listening on port 8080
   ```

2. **Test blocking server directly**:
   ```bash
   curl http://localhost:8080
   ```

3. **Check port redirection status**:
   ```python
   from parental_control.port_redirector import PortRedirector
   redirector = PortRedirector()
   print(redirector.get_status())
   ```

### Cleanup stuck rules

If rules persist after stopping:

```bash
# Manual cleanup
sudo iptables -t nat -D OUTPUT -j PARENTAL_REDIRECT
sudo iptables -t nat -F PARENTAL_REDIRECT
sudo iptables -t nat -X PARENTAL_REDIRECT
```

Or use the cleanup function:

```python
from parental_control.port_redirector import PortRedirector
redirector = PortRedirector()
redirector.cleanup()
```

## Integration with Service

### Service Startup Sequence

1. **Start Flask web interface** (port 5000)
2. **Start blocking server** (port 8080)
3. **Enable port redirection** (iptables)
4. **Update hosts file** (blocked domains → 127.0.0.1)

### Service Shutdown Sequence

1. **Disable port redirection** (iptables cleanup)
2. **Stop blocking server**
3. **Stop Flask web interface**

### Auto-restart on failure

The service monitors the blocking server and automatically restarts it if it crashes:

```python
# From start_service.sh
while self.running:
    time.sleep(10)
    if self.pc.blocking_server and not self.pc.blocking_server.is_running():
        logger.warning('Blocking server stopped unexpectedly, restarting...')
        self.pc.start_blocking_server(port=8080)
```

## Future Enhancements

### Potential Improvements

1. **True HTTPS support**:
   - Generate self-signed certificate
   - Run blocking server on port 443
   - Show blocking page over HTTPS

2. **Better HTTPS detection**:
   - Track original destination port
   - More reliable HTTPS indicators

3. **Per-domain redirection**:
   - Only redirect blocked domains
   - Allow other localhost services

4. **IPv6 support**:
   - Add ip6tables rules
   - Support IPv6 blocked domains

5. **Performance optimization**:
   - Connection pooling
   - Caching of blocking decisions

## Related Documentation

- [Blocking Page Development](docs/blocking-page-feature.md)
- [Time Restriction Enforcement](TIME_RESTRICTION_ENFORCEMENT.md)
- [Category Blocking](docs/category-blocking.md)

## License

Ubuntu Parental Control
Copyright (c) 2025
