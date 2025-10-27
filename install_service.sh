#!/bin/bash
# Ubuntu Parental Control Service Installation Script

set -e

echo "=== Ubuntu Parental Control Service Installation ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (use sudo)"
    exit 1
fi

# Configuration
INSTALL_DIR="/opt/ubuntu-parental-control"
SERVICE_NAME="ubuntu-parental-control"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "1. Creating installation directory..."
mkdir -p "$INSTALL_DIR"
mkdir -p /var/lib/ubuntu-parental
mkdir -p /var/log

echo "2. Copying files to installation directory..."
cp -r "$CURRENT_DIR/src" "$INSTALL_DIR/"
cp "$CURRENT_DIR/start_service.sh" "$INSTALL_DIR/"
cp "$CURRENT_DIR/stop_service.sh" "$INSTALL_DIR/"

echo "3. Setting permissions..."
chmod +x "$INSTALL_DIR/start_service.sh"
chmod +x "$INSTALL_DIR/stop_service.sh"
chown -R root:root "$INSTALL_DIR"

echo "4. Installing systemd service..."
cp "$CURRENT_DIR/ubuntu-parental-control.service" "/etc/systemd/system/"
systemctl daemon-reload

echo "5. Enabling service for auto-start..."
systemctl enable "$SERVICE_NAME"

echo "6. Starting service..."
systemctl start "$SERVICE_NAME"

echo "7. Checking service status..."
sleep 2
systemctl status "$SERVICE_NAME" --no-pager

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "Service Status:"
echo "  • Service Name: $SERVICE_NAME"
echo "  • Installation Dir: $INSTALL_DIR"
echo "  • Config File: /var/lib/ubuntu-parental/control.json"
echo "  • Log File: /var/log/ubuntu-parental-control.log"
echo ""
echo "Service Commands:"
echo "  • Start:   sudo systemctl start $SERVICE_NAME"
echo "  • Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  • Restart: sudo systemctl restart $SERVICE_NAME"
echo "  • Status:  sudo systemctl status $SERVICE_NAME"
echo "  • Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Web Interface:"
echo "  • The blocking server is now running automatically"
echo "  • Access web interface: http://localhost:5000"
echo "  • Blocked sites will show friendly pages"
echo ""
echo "The Ubuntu Parental Control service will now:"
echo "  ✅ Start automatically at boot"
echo "  ✅ Run the blocking server continuously"
echo "  ✅ Show friendly block pages for blocked sites"
echo "  ✅ Restart automatically if it crashes"
echo ""
