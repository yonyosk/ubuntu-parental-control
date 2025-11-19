# HTTPS Blocking Setup

## Overview

Ubuntu Parental Control now supports **seamless HTTPS blocking** with dynamic certificate generation. When users try to access blocked HTTPS sites, they see the blocking page without certificate warnings (after initial setup).

## How It Works

The system uses a two-tier approach:

1. **HTTP Blocking (Port 8080)**: Handles HTTP traffic
   - iptables redirects port 80 → 8080
   - Simple HTTP server serves blocking pages

2. **HTTPS Blocking (Port 8443)**: Handles HTTPS traffic
   - iptables redirects port 443 → 8443
   - HTTPS server with SNI (Server Name Indication)
   - Dynamically generates SSL certificates for each blocked domain
   - Signs certificates with custom root CA

## Setup

### Step 1: Install Root CA (Required for HTTPS)

```bash
sudo ./setup_root_ca.sh
```

This creates a custom root certificate authority that will be used to sign domain certificates.

**What it does:**
- Generates 4096-bit RSA root CA certificate (10-year validity)
- Installs as trusted system-wide certificate
- Stores CA files in `/opt/ubuntu-parental-control/certs/`

### Step 2: Firefox Configuration (If using Firefox)

Firefox uses its own certificate store, so you need to manually import the CA:

1. Open Firefox → Settings → Privacy & Security → Certificates
2. Click "View Certificates" → "Authorities" → "Import"
3. Select: `/opt/ubuntu-parental-control/certs/ca.crt`
4. Check "Trust this CA to identify websites"
5. Click OK

### Step 3: Restart Service

```bash
sudo systemctl restart ubuntu-parental-control
```

The service will now start both HTTP and HTTPS blocking servers.

## How Dynamic Certificate Generation Works

When a user accesses a blocked HTTPS site (e.g., `https://facebook.com`):

1. Browser makes HTTPS connection to facebook.com
2. DNS resolves to 127.0.0.1 (from /etc/hosts)
3. iptables redirects port 443 → 8443
4. HTTPS blocking server receives connection
5. SNI callback detects requested domain ("facebook.com")
6. Certificate generator creates/retrieves certificate for facebook.com
7. Certificate is signed by root CA
8. Browser validates certificate chain (root CA is trusted)
9. No certificate warning - blocking page displays seamlessly

## Certificate Management

**Certificate Storage:**
- Root CA: `/opt/ubuntu-parental-control/certs/ca.crt` and `ca.key`
- Domain certs: `/opt/ubuntu-parental-control/certs/domains/*.crt`

**Automatic Cleanup:**
Certificates older than 30 days are automatically cleaned up to save disk space.

**Manual Certificate Generation:**
```bash
cd /opt/ubuntu-parental-control/src
python3 -m parental_control.cert_generator
```

## Testing

After setup, test with:

```bash
# HTTP - should work without warnings
curl http://facebook.com

# HTTPS - will show certificate warning in browser
# With root CA installed: no warning
# Without root CA: click through warning to see blocking page
firefox https://facebook.com
```

## Security Considerations

Installing a custom root CA means:
- The system trusts certificates signed by this CA
- If the CA private key is compromised, attackers could create trusted certificates
- Keep `/opt/ubuntu-parental-control/certs/ca.key` secure (already set to 600 permissions)
- Only install on systems you control

For parental control use cases, this is acceptable since:
- The system is controlled by the parent/administrator
- The CA is only used for blocking pages
- Benefits outweigh the minimal risk
