#!/bin/bash
# Installation script for Ubuntu Parental Control with automatic iptables setup

set -e

echo "=========================================="
echo "Ubuntu Parental Control - Installation"
echo "=========================================="
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script must be run as root"
    echo "   Run: sudo ./install_service.sh"
    exit 1
fi

echo "✓ Running as root"
echo ""

# Check for conflicting ubuntu-parental-control Debian package FIRST
# (before trying to fix broken packages, since this package is fundamentally broken)
echo "Checking for package conflicts..."
if dpkg -l | grep -q "ubuntu-parental-control"; then
    echo "   - Removing conflicting Debian package ubuntu-parental-control..."
    # Force remove the package and its configuration
    dpkg --remove --force-remove-reinstreq ubuntu-parental-control 2>/dev/null || true
    apt-get remove -y ubuntu-parental-control 2>/dev/null || true
    apt-get purge -y ubuntu-parental-control 2>/dev/null || true
fi

# Now fix any remaining broken packages
if dpkg -l | grep -q "^iU\|^iF"; then
    echo "   - Fixing remaining broken packages..."
    dpkg --configure -a 2>/dev/null || true
    apt-get install -f -y 2>/dev/null || true
fi
echo "✓ Package system clean"
echo ""

# Setup Root CA for HTTPS blocking (if not already present)
echo "Checking for Root CA certificate..."
CA_CERT="/opt/ubuntu-parental-control/certs/ca.crt"
CA_KEY="/opt/ubuntu-parental-control/certs/ca.key"

if [ -f "$CA_CERT" ] && [ -f "$CA_KEY" ]; then
    echo "   ✓ Root CA already exists, skipping..."
else
    echo "   - Setting up Root CA for HTTPS blocking..."

    # Create certificate directory
    mkdir -p /opt/ubuntu-parental-control/certs

    # Generate Root CA private key
    openssl genrsa -out "$CA_KEY" 4096 2>/dev/null

    # Generate Root CA certificate
    openssl req -x509 -new -nodes -key "$CA_KEY" -sha256 -days 3650 \
        -out "$CA_CERT" \
        -subj "/C=IL/ST=Israel/L=Tel Aviv/O=Ubuntu Parental Control/OU=Root CA/CN=Ubuntu Parental Control Root CA" \
        2>/dev/null

    # Install as trusted certificate
    cp "$CA_CERT" /usr/local/share/ca-certificates/ubuntu-parental-control-ca.crt
    update-ca-certificates >/dev/null 2>&1

    # Set permissions
    chmod 600 "$CA_KEY"
    chmod 644 "$CA_CERT"

    echo "   ✓ Root CA created and installed"
    echo ""
    echo "   NOTE: For Firefox users, manually import the CA certificate:"
    echo "   1. Firefox Settings → Privacy & Security → Certificates → View Certificates"
    echo "   2. Authorities → Import → Select: $CA_CERT"
    echo "   3. Check 'Trust this CA to identify websites'"
    echo ""
fi

# Install location
INSTALL_DIR="/opt/ubuntu-parental-control"
SERVICE_FILE="/etc/systemd/system/ubuntu-parental-control.service"

# Stop existing service if running
echo "1. Stopping existing service (if running)..."
systemctl stop ubuntu-parental-control 2>/dev/null || echo "   - No existing service to stop"
sleep 2

# Kill any lingering processes
pkill -f "parental_control" 2>/dev/null || true
pkill -f "ubuntu-parental-control" 2>/dev/null || true
sleep 1

# Create installation directory
echo ""
echo "2. Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy files (excluding venv and cache)
echo ""
echo "3. Copying files to $INSTALL_DIR..."

# Kill any Python processes using files in the install directory
echo "   - Ensuring no processes are using installation files..."
pkill -f "$INSTALL_DIR" 2>/dev/null || true
sleep 2

# Copy files, excluding venv, cache, and other build artifacts
rsync -a --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
    src/ "$INSTALL_DIR/src/"
rsync -a templates/ "$INSTALL_DIR/templates/"
rsync -a static/ "$INSTALL_DIR/static/"
rsync -a locales/ "$INSTALL_DIR/locales/"
cp start_service.sh "$INSTALL_DIR/"
cp setup_iptables.sh "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/start_service.sh"
chmod +x "$INSTALL_DIR/setup_iptables.sh"

echo "   ✓ Files copied (excluding venv and cache files)"

# Install systemd service
echo ""
echo "4. Installing systemd service..."
cp ubuntu-parental-control.service "$SERVICE_FILE"
systemctl daemon-reload
echo "   ✓ Service installed"

# Enable service
echo ""
echo "5. Enabling service to start on boot..."
systemctl enable ubuntu-parental-control
echo "   ✓ Service enabled"

# Install iptables-persistent (optional but recommended)
echo ""
# Check if already installed
if dpkg -l | grep -q "^ii.*iptables-persistent"; then
    echo "iptables-persistent already installed, skipping..."
else
    read -p "Install iptables-persistent to save rules across reboots? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        echo "Installing iptables-persistent..."
        apt-get update -qq
        DEBIAN_FRONTEND=noninteractive apt-get install -y -qq iptables-persistent

        # Verify installation
        if dpkg -l | grep -q "^ii.*iptables-persistent"; then
            echo "   ✓ iptables-persistent installed"
        else
            echo "   ⚠ iptables-persistent installation had issues, but continuing..."
        fi
    fi
fi

# Start service
echo ""
echo "6. Starting service..."
systemctl start ubuntu-parental-control

# Wait for service to be active (max 5 seconds)
for i in {1..10}; do
    if systemctl is-active --quiet ubuntu-parental-control; then
        break
    fi
    sleep 0.5
done

# Check status
echo ""
echo "7. Checking service status..."
if systemctl is-active --quiet ubuntu-parental-control; then
    echo "   ✓ Service is running"
else
    echo "   ⚠ Service failed to start. Checking logs..."
    journalctl -u ubuntu-parental-control -n 20 --no-pager
    exit 1
fi

# Verify iptables
echo ""
echo "8. Verifying iptables setup..."
REFS=$(iptables -t nat -L PARENTAL_REDIRECT -n -v 2>/dev/null | grep "references" | grep -o "[0-9]* references")
if [[ "$REFS" == "1 references" ]]; then
    echo "   ✓ iptables configured correctly ($REFS)"
else
    echo "   ⚠ Warning: iptables shows $REFS - expected 1 references"
fi

# Save iptables rules if iptables-persistent is installed
if command -v netfilter-persistent &> /dev/null; then
    echo ""
    echo "9. Saving iptables rules..."
    netfilter-persistent save
    echo "   ✓ Rules saved (will persist across reboots)"
fi

# Summary
echo ""
echo "=========================================="
echo "✅ INSTALLATION COMPLETE"
echo "=========================================="
echo ""
echo "Service Status:"
systemctl status ubuntu-parental-control --no-pager -l | head -10
echo ""
echo "Access the admin panel at: http://localhost:5000"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status ubuntu-parental-control   # Check status"
echo "  sudo systemctl restart ubuntu-parental-control  # Restart service"
echo "  sudo systemctl stop ubuntu-parental-control     # Stop service"
echo "  sudo journalctl -u ubuntu-parental-control -f   # View logs"
echo ""
