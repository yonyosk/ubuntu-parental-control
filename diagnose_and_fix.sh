#!/bin/bash
# Diagnostic and fix script for Ubuntu Parental Control

echo "======================================"
echo "UBUNTU PARENTAL CONTROL DIAGNOSTICS"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ ERROR: This script must be run as root"
    echo "   Run: sudo ./diagnose_and_fix.sh"
    exit 1
fi

echo "✓ Running as root"
echo ""

# Step 1: Kill existing processes
echo "1. Cleaning up existing processes..."
pkill -9 -f "parental_control" 2>/dev/null && echo "   ✓ Killed parental control processes" || echo "   - No processes to kill"
sleep 2

# Step 2: Check ports
echo ""
echo "2. Checking ports..."
PORT_5000=$(lsof -ti :5000)
PORT_8080=$(lsof -ti :8080)

if [ -n "$PORT_5000" ]; then
    echo "   ⚠ Port 5000 in use by PID $PORT_5000"
    kill -9 $PORT_5000 2>/dev/null && echo "   ✓ Killed process on port 5000"
else
    echo "   ✓ Port 5000 is free"
fi

if [ -n "$PORT_8080" ]; then
    echo "   ⚠ Port 8080 in use by PID $PORT_8080"
    kill -9 $PORT_8080 2>/dev/null && echo "   ✓ Killed process on port 8080"
else
    echo "   ✓ Port 8080 is free"
fi

# Step 3: Clean iptables
echo ""
echo "3. Cleaning iptables rules..."
iptables -t nat -D OUTPUT -j PARENTAL_REDIRECT 2>/dev/null && echo "   ✓ Removed OUTPUT jump rule" || echo "   - No OUTPUT jump rule to remove"
iptables -t nat -F PARENTAL_REDIRECT 2>/dev/null && echo "   ✓ Flushed PARENTAL_REDIRECT chain" || echo "   - Chain already empty"
iptables -t nat -X PARENTAL_REDIRECT 2>/dev/null && echo "   ✓ Deleted PARENTAL_REDIRECT chain" || echo "   - Chain already deleted"

# Step 4: Create iptables rules properly
echo ""
echo "4. Creating iptables rules..."
iptables -t nat -N PARENTAL_REDIRECT 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ Created PARENTAL_REDIRECT chain"
else
    echo "   - Chain already exists"
fi

iptables -t nat -I OUTPUT 1 -j PARENTAL_REDIRECT
if [ $? -eq 0 ]; then
    echo "   ✓ Hooked chain to OUTPUT"
else
    echo "   ⚠ Failed to hook chain to OUTPUT"
fi

iptables -t nat -A PARENTAL_REDIRECT -p tcp -d 127.0.0.1 --dport 80 -j REDIRECT --to-port 8080
if [ $? -eq 0 ]; then
    echo "   ✓ Added HTTP redirect rule (80 -> 8080)"
else
    echo "   ⚠ Failed to add HTTP redirect rule"
fi

iptables -t nat -A PARENTAL_REDIRECT -p tcp -d 127.0.0.1 --dport 443 -j REDIRECT --to-port 8080
if [ $? -eq 0 ]; then
    echo "   ✓ Added HTTPS redirect rule (443 -> 8080)"
else
    echo "   ⚠ Failed to add HTTPS redirect rule"
fi

# Step 5: Verify iptables
echo ""
echo "5. Verifying iptables setup..."
echo "   OUTPUT chain:"
iptables -t nat -L OUTPUT -n -v | head -5 | sed 's/^/     /'

echo ""
echo "   PARENTAL_REDIRECT chain:"
iptables -t nat -L PARENTAL_REDIRECT -n -v | sed 's/^/     /'

# Check if chain has references
REFS=$(iptables -t nat -L PARENTAL_REDIRECT -n -v | grep "references" | grep -o "[0-9]* references")
if [[ "$REFS" == "1 references" ]]; then
    echo "   ✓ Chain is properly hooked (1 reference)"
elif [[ "$REFS" == "0 references" ]]; then
    echo "   ❌ Chain is NOT hooked (0 references)"
    echo "   Attempting manual fix..."
    iptables -t nat -I OUTPUT 1 -j PARENTAL_REDIRECT
else
    echo "   ⚠ Unexpected reference count: $REFS"
fi

# Step 6: Test database
echo ""
echo "6. Testing database access..."
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from parental_control.database import ParentalControlDB
    db = ParentalControlDB('/var/lib/ubuntu-parental/control.json')
    lang = db.get_default_language()
    print(f'   ✓ Database accessible, default language: {lang}')
    db.close()
except Exception as e:
    print(f'   ❌ Database error: {e}')
"

# Step 7: Check Flask
echo ""
echo "7. Checking Flask installation..."
python3 -c "import flask; print(f'   ✓ Flask version: {flask.__version__}')" 2>/dev/null || echo "   ❌ Flask not installed"

# Summary
echo ""
echo "======================================"
echo "DIAGNOSTIC COMPLETE"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Start the service:"
echo "   sudo python3 -m parental_control.web_interface"
echo ""
echo "2. In another terminal, test the blocking page:"
echo "   curl 'http://localhost:5000/blocked?url=test.com&reason=test&category=MANUAL'"
echo ""
echo "3. Check if blocking server started:"
echo "   sudo netstat -tlnp | grep 8080"
echo ""
echo "4. Verify iptables:"
echo "   sudo iptables -t nat -L PARENTAL_REDIRECT -n -v"
echo ""
