# HTTPS Blocking Setup

## The Challenge

When blocking HTTPS sites (like `https://facebook.com`), users will see an SSL certificate warning because:
1. The iptables redirect sends HTTPS traffic (port 443) to the blocking server (port 8080)
2. The blocking server runs HTTP, not HTTPS
3. The browser expects an HTTPS response with a valid certificate

## Solution Options

### Option 1: Accept Certificate Warnings (Current)

**Pros:**
- Simple, works out of the box
- No additional setup required

**Cons:**
- Users see "Your connection is not private" warnings
- Requires clicking through the warning to see the blocking page

**How it works:**
1. User tries to access `https://facebook.com`
2. Browser shows certificate warning
3. User clicks "Advanced" → "Accept the Risk"
4. User sees the Hebrew blocking page

### Option 2: Install Custom Root CA (Recommended)

This option installs a custom root certificate authority that the system (and browsers) trust.

**Pros:**
- No certificate warnings for blocked HTTPS sites
- Professional, seamless experience
- Works system-wide (for Chrome, system tools, etc.)

**Cons:**
- Requires manual Firefox configuration
- More complex setup
- Security consideration: Anyone with access to the CA private key can create trusted certificates

**Setup:**

```bash
# 1. Run the setup script
sudo ./setup_root_ca.sh

# 2. For Firefox users, manually import the certificate:
#    - Open Firefox Settings → Privacy & Security → Certificates
#    - Click "View Certificates" → "Authorities" → "Import"
#    - Select: /opt/ubuntu-parental-control/certs/ca.crt
#    - Check "Trust this CA to identify websites"

# 3. Restart the service
sudo systemctl restart ubuntu-parental-control
```

**Note:** This generates a root CA certificate that is trusted system-wide. Keep `/opt/ubuntu-parental-control/certs/ca.key` secure!

### Option 3: HTTPS Blocking Server (Future Enhancement)

A more advanced solution would be to:
1. Run the blocking server with HTTPS support
2. Dynamically generate certificates for each blocked domain
3. Sign them with the custom root CA

This requires:
- Python SSL/TLS library support
- On-the-fly certificate generation
- More complex server implementation

This is planned for future development.

## Current Recommendation

For most users, **Option 1** (accept certificate warnings) is sufficient for testing.

For production use or better user experience, use **Option 2** (install custom root CA).

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
