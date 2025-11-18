#!/bin/bash
# Pre-start script to ensure iptables is configured before service starts

set -e

echo "Setting up iptables port redirection for Ubuntu Parental Control..."

# Function to check if chain exists
chain_exists() {
    iptables -t nat -L "$1" -n &>/dev/null
}

# Function to check if jump rule exists
jump_exists() {
    iptables -t nat -C OUTPUT -j PARENTAL_REDIRECT &>/dev/null
}

# Clean up old rules if they exist
if chain_exists PARENTAL_REDIRECT; then
    echo "Cleaning up existing PARENTAL_REDIRECT chain..."
    iptables -t nat -F PARENTAL_REDIRECT 2>/dev/null || true
    iptables -t nat -D OUTPUT -j PARENTAL_REDIRECT 2>/dev/null || true
    iptables -t nat -X PARENTAL_REDIRECT 2>/dev/null || true
fi

# Create chain
echo "Creating PARENTAL_REDIRECT chain..."
iptables -t nat -N PARENTAL_REDIRECT

# Add jump from OUTPUT to our chain
echo "Hooking chain to OUTPUT..."
iptables -t nat -I OUTPUT 1 -j PARENTAL_REDIRECT

# Add redirect rules
echo "Adding HTTP redirect rule (80 -> 8080)..."
iptables -t nat -A PARENTAL_REDIRECT -p tcp -d 127.0.0.1 --dport 80 -j REDIRECT --to-port 8080

echo "Adding HTTPS redirect rule (443 -> 8080)..."
iptables -t nat -A PARENTAL_REDIRECT -p tcp -d 127.0.0.1 --dport 443 -j REDIRECT --to-port 8080

# Verify
echo ""
echo "Verification:"
iptables -t nat -L PARENTAL_REDIRECT -n -v | head -5

# Check references
REFS=$(iptables -t nat -L PARENTAL_REDIRECT -n -v 2>/dev/null | grep "references" | grep -o "[0-9]* references")
if [[ "$REFS" == "1 references" ]]; then
    echo "✓ Chain is properly hooked (1 reference)"
    exit 0
else
    echo "⚠ Warning: Chain shows $REFS - expected 1 references"
    exit 1
fi
