#!/bin/bash
# Diagnostic script to verify ubuntu-parental-control installation

echo "=========================================="
echo "Ubuntu Parental Control Installation Check"
echo "=========================================="
echo ""

# 1. Check if the package is installed
echo "1. Checking if package is installed..."
pip3 show ubuntu-parental-control 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Package is installed"
else
    echo "✗ Package not found via pip3"
fi
echo ""

# 2. Find where the package is installed
echo "2. Finding installation location..."
INSTALL_PATH=$(python3 -c "import sys; import parental_control; print(parental_control.__file__)" 2>/dev/null)
if [ -n "$INSTALL_PATH" ]; then
    PACKAGE_DIR=$(dirname "$INSTALL_PATH")
    echo "✓ Package installed at: $PACKAGE_DIR"
else
    echo "✗ Cannot find parental_control module"
    echo "Trying alternative search..."
    find /usr/local/lib/python3*/dist-packages -name "parental_control" -type d 2>/dev/null
    find /usr/lib/python3*/dist-packages -name "parental_control" -type d 2>/dev/null
fi
echo ""

# 3. Check if new files exist
echo "3. Checking for new files..."
if [ -n "$PACKAGE_DIR" ]; then
    if [ -f "$PACKAGE_DIR/category_manager.py" ]; then
        echo "✓ category_manager.py exists"
    else
        echo "✗ category_manager.py NOT FOUND"
    fi

    if [ -f "$PACKAGE_DIR/templates/categories.html" ]; then
        echo "✓ templates/categories.html exists"
    else
        echo "✗ templates/categories.html NOT FOUND"
    fi
else
    echo "Skipping file check (package directory not found)"
fi
echo ""

# 4. Check if web_interface.py has the new routes
echo "4. Checking for new API routes in web_interface.py..."
if [ -n "$PACKAGE_DIR" ] && [ -f "$PACKAGE_DIR/web_interface.py" ]; then
    if grep -q "/api/categories" "$PACKAGE_DIR/web_interface.py"; then
        echo "✓ New /api/categories routes found"
    else
        echo "✗ New routes NOT FOUND in web_interface.py"
    fi

    if grep -q "def categories_page" "$PACKAGE_DIR/web_interface.py"; then
        echo "✓ categories_page() function found"
    else
        echo "✗ categories_page() function NOT FOUND"
    fi
else
    echo "Cannot check web_interface.py"
fi
echo ""

# 5. Check service status
echo "5. Checking service status..."
systemctl is-active ubuntu-parental-control 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Service is running"
    echo ""
    echo "Service details:"
    systemctl status ubuntu-parental-control --no-pager | head -20
else
    echo "✗ Service is not running"
fi
echo ""

# 6. Check which Python path the service is using
echo "6. Checking service Python path configuration..."
if [ -f /etc/systemd/system/ubuntu-parental-control.service ]; then
    echo "Service file location: /etc/systemd/system/ubuntu-parental-control.service"
    grep -E "(WorkingDirectory|PYTHONPATH|ExecStart)" /etc/systemd/system/ubuntu-parental-control.service
else
    echo "Service file not found in /etc/systemd/system/"
fi
echo ""

# 7. Check if /opt/ubuntu-parental-control exists and what version it has
echo "7. Checking /opt/ubuntu-parental-control directory..."
if [ -d /opt/ubuntu-parental-control ]; then
    echo "✓ /opt/ubuntu-parental-control exists"

    if [ -d /opt/ubuntu-parental-control/src ]; then
        echo "✓ src directory exists"

        if [ -f /opt/ubuntu-parental-control/src/parental_control/category_manager.py ]; then
            echo "✓ category_manager.py exists in /opt"
        else
            echo "✗ category_manager.py NOT FOUND in /opt"
        fi

        if [ -f /opt/ubuntu-parental-control/src/parental_control/templates/categories.html ]; then
            echo "✓ categories.html exists in /opt"
        else
            echo "✗ categories.html NOT FOUND in /opt"
        fi
    else
        echo "✗ src directory NOT FOUND"
    fi
else
    echo "✗ /opt/ubuntu-parental-control does not exist"
fi
echo ""

# 8. Check web interface accessibility
echo "8. Testing web interface..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:5000 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Web interface is responding"

    # Check if categories route exists
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/categories 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        echo "✓ /categories route exists (HTTP $HTTP_CODE)"
    else
        echo "✗ /categories route not found (HTTP $HTTP_CODE)"
    fi
else
    echo "✗ Cannot connect to web interface"
fi
echo ""

# 9. Check recent logs
echo "9. Recent service logs (last 20 lines)..."
journalctl -u ubuntu-parental-control -n 20 --no-pager 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Could not read journalctl, trying log file..."
    tail -20 /var/log/ubuntu-parental-control.log 2>/dev/null
fi
echo ""

echo "=========================================="
echo "Diagnostic complete!"
echo "=========================================="
