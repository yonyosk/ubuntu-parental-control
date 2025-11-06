#!/bin/bash
# Ubuntu Parental Control - Installation and Update Script
# This script installs or updates the Ubuntu Parental Control service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/ubuntu-parental-control"
SERVICE_NAME="ubuntu-parental-control"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Ubuntu Parental Control - Install/Update${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Detect if this is an update or fresh install
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Existing installation detected. This will UPDATE the installation.${NC}"
    IS_UPDATE=true
else
    echo -e "${GREEN}No existing installation found. This will INSTALL the service.${NC}"
    IS_UPDATE=false
fi
echo ""

# Stop service if it's running
if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
    echo -e "${YELLOW}Stopping ${SERVICE_NAME} service...${NC}"
    systemctl stop $SERVICE_NAME
    echo -e "${GREEN}✓ Service stopped${NC}"
fi

# Create installation directory
echo -e "${BLUE}Creating installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
echo -e "${GREEN}✓ Directory created: $INSTALL_DIR${NC}"

# Copy files
echo -e "${BLUE}Copying application files...${NC}"

# Copy source directory (excluding venv, cache, and other unnecessary files)
if [ -d "$SCRIPT_DIR/src" ]; then
    # Use rsync if available (better for excluding patterns), otherwise use cp with filtering
    if command -v rsync &> /dev/null; then
        rsync -av --delete \
            --exclude='venv/' \
            --exclude='__pycache__/' \
            --exclude='*.pyc' \
            --exclude='*.pyo' \
            --exclude='*.pyd' \
            --exclude='.DS_Store' \
            --exclude='*.egg-info/' \
            "$SCRIPT_DIR/src/" "$INSTALL_DIR/src/"
    else
        # Fallback to cp with manual exclusion
        mkdir -p "$INSTALL_DIR/src"
        cd "$SCRIPT_DIR/src"
        find . -type f -not -path "*/venv/*" -not -path "*/__pycache__/*" -not -name "*.pyc" -not -name "*.pyo" | \
            while read file; do
                mkdir -p "$INSTALL_DIR/src/$(dirname "$file")"
                cp "$file" "$INSTALL_DIR/src/$file"
            done
        cd "$SCRIPT_DIR"
    fi
    echo -e "${GREEN}✓ Copied src directory (excluded venv and cache files)${NC}"
else
    echo -e "${RED}Error: src directory not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Copy service scripts
for script in start_service.sh stop_service.sh; do
    if [ -f "$SCRIPT_DIR/$script" ]; then
        cp "$SCRIPT_DIR/$script" "$INSTALL_DIR/"
        chmod +x "$INSTALL_DIR/$script"
        echo -e "${GREEN}✓ Copied $script${NC}"
    else
        echo -e "${YELLOW}Warning: $script not found${NC}"
    fi
done

# Copy systemd service file
echo -e "${BLUE}Installing systemd service...${NC}"
if [ -f "$SCRIPT_DIR/${SERVICE_NAME}.service" ]; then
    cp "$SCRIPT_DIR/${SERVICE_NAME}.service" "$SERVICE_FILE"
    echo -e "${GREEN}✓ Service file installed${NC}"
else
    echo -e "${RED}Error: ${SERVICE_NAME}.service not found${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${BLUE}Creating system directories...${NC}"
mkdir -p /var/lib/ubuntu-parental
mkdir -p /var/log
mkdir -p /var/run
echo -e "${GREEN}✓ System directories created${NC}"

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip3 install -r "$SCRIPT_DIR/requirements.txt" > /dev/null 2>&1
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}Warning: requirements.txt not found, attempting to install from setup.py...${NC}"
    pip3 install Flask requests python-dateutil typing-extensions setuptools tinydb > /dev/null 2>&1
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
fi

# Reload systemd daemon
echo -e "${BLUE}Reloading systemd daemon...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd daemon reloaded${NC}"

# Enable service to start on boot
if [ "$IS_UPDATE" = false ]; then
    echo -e "${BLUE}Enabling service to start on boot...${NC}"
    systemctl enable $SERVICE_NAME
    echo -e "${GREEN}✓ Service enabled${NC}"
fi

# Start the service
echo -e "${BLUE}Starting ${SERVICE_NAME} service...${NC}"
systemctl start $SERVICE_NAME

# Wait a moment for the service to start
sleep 2

# Check service status
if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✓ Service started successfully${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo -e "${YELLOW}Checking service status:${NC}"
    systemctl status $SERVICE_NAME --no-pager || true
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
if [ "$IS_UPDATE" = true ]; then
    echo -e "${GREEN}Update completed successfully!${NC}"
else
    echo -e "${GREEN}Installation completed successfully!${NC}"
fi
echo -e "${GREEN}=========================================${NC}"
echo ""

# Show service status
echo -e "${BLUE}Service Status:${NC}"
systemctl status $SERVICE_NAME --no-pager | head -15

echo ""
echo -e "${BLUE}Quick Reference:${NC}"
echo -e "  Web Interface: ${GREEN}http://localhost:5000${NC}"
echo -e "  Service status: ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "  View logs:      ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo -e "  Restart:        ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC}"
echo -e "  Stop:           ${YELLOW}sudo systemctl stop $SERVICE_NAME${NC}"
echo ""
echo -e "${BLUE}To update in the future:${NC}"
echo -e "  1. ${YELLOW}cd $SCRIPT_DIR && git pull${NC}"
echo -e "  2. ${YELLOW}sudo ./install.sh${NC}"
echo ""

# Verify new features
echo -e "${BLUE}Verifying new features...${NC}"
if [ -f "$INSTALL_DIR/src/parental_control/category_manager.py" ]; then
    echo -e "${GREEN}✓ category_manager.py installed${NC}"
else
    echo -e "${RED}✗ category_manager.py not found${NC}"
fi

if [ -f "$INSTALL_DIR/src/parental_control/templates/categories.html" ]; then
    echo -e "${GREEN}✓ categories.html template installed${NC}"
else
    echo -e "${RED}✗ categories.html not found${NC}"
fi

# Check if new routes exist in web_interface.py
if grep -q "/api/categories" "$INSTALL_DIR/src/parental_control/web_interface.py" 2>/dev/null; then
    echo -e "${GREEN}✓ New API routes detected in web_interface.py${NC}"
else
    echo -e "${RED}✗ New API routes not found in web_interface.py${NC}"
fi

echo ""
echo -e "${GREEN}All done! 🎉${NC}"
