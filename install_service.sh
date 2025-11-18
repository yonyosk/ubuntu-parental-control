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
read -p "Install iptables-persistent to save rules across reboots? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo "Installing iptables-persistent..."
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq iptables-persistent
    echo "   ✓ iptables-persistent installed"
fi

# Start service
echo ""
echo "6. Starting service..."
systemctl start ubuntu-parental-control
sleep 3

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
