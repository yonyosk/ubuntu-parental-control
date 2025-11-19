#!/bin/bash
# Setup custom Root CA for Ubuntu Parental Control
# This allows the blocking server to present valid HTTPS certificates

set -e

echo "=========================================="
echo "Root CA Setup for Ubuntu Parental Control"
echo "=========================================="
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script must be run as root"
    echo "   Run: sudo ./setup_root_ca.sh"
    exit 1
fi

CERT_DIR="/opt/ubuntu-parental-control/certs"
CA_KEY="$CERT_DIR/ca.key"
CA_CERT="$CERT_DIR/ca.crt"

echo "1. Creating certificate directory..."
mkdir -p "$CERT_DIR"

echo ""
echo "2. Generating Root CA private key..."
openssl genrsa -out "$CA_KEY" 4096

echo ""
echo "3. Generating Root CA certificate..."
openssl req -x509 -new -nodes -key "$CA_KEY" -sha256 -days 3650 \
    -out "$CA_CERT" \
    -subj "/C=IL/ST=Israel/L=Tel Aviv/O=Ubuntu Parental Control/OU=Root CA/CN=Ubuntu Parental Control Root CA"

echo ""
echo "4. Installing Root CA as trusted certificate..."
# Copy to system trust store
cp "$CA_CERT" /usr/local/share/ca-certificates/ubuntu-parental-control-ca.crt

# Update CA certificates
update-ca-certificates

echo ""
echo "5. Setting permissions..."
chmod 600 "$CA_KEY"
chmod 644 "$CA_CERT"

echo ""
echo "=========================================="
echo "✅ ROOT CA SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Certificate details:"
echo "  CA Certificate: $CA_CERT"
echo "  CA Private Key: $CA_KEY"
echo ""
echo "The Root CA is now trusted system-wide."
echo ""
echo "For Firefox:"
echo "  Firefox uses its own certificate store."
echo "  Import the CA certificate manually:"
echo "  1. Open Firefox Settings → Privacy & Security → Certificates"
echo "  2. Click 'View Certificates' → 'Authorities' → 'Import'"
echo "  3. Select: $CA_CERT"
echo "  4. Check 'Trust this CA to identify websites'"
echo ""
echo "Note: You'll need to restart the blocking server for changes to take effect:"
echo "  sudo systemctl restart ubuntu-parental-control"
echo ""
