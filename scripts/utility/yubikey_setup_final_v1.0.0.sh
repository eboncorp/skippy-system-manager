#!/bin/bash
# YubiKey Final Setup - Run when YubiKey arrives
# Integrates hardware authentication with existing session control

echo "🔑 YUBIKEY FINAL SETUP"
echo "====================="
echo "This script configures YubiKey authentication while keeping session control"
echo ""

if \! lsusb | grep -i yubico > /dev/null; then
    echo "❌ YubiKey not detected. Please insert your YubiKey and try again."
    exit 1
fi

echo "✅ YubiKey detected\!"
echo ""

# Step 1: Get YubiKey information
echo "📋 Getting YubiKey information..."
YUBIKEY_ID=$(ykpersonalize -1 -ofixed= -oserial-public 2>/dev/null | grep "public id" | cut -d: -f2 | tr -d ' ')

if [ -z "$YUBIKEY_ID" ]; then
    echo "Enter your YubiKey public ID (touch YubiKey button now):"
    read -r YUBIKEY_INPUT
    YUBIKEY_ID=$(echo "$YUBIKEY_INPUT" | cut -c1-12)
fi

echo "YubiKey ID: $YUBIKEY_ID"

# Step 2: Create YubiCloud API credentials (optional - for cloud validation)
echo ""
echo "🌐 YubiCloud Setup (Optional - Press Enter to skip)"
echo "For enhanced security, you can use YubiCloud API validation:"
echo "Visit: https://upgrade.yubico.com/getapikey/"
read -p "Enter Client ID (or press Enter to skip): " CLIENT_ID
read -p "Enter Secret Key (or press Enter to skip): " SECRET_KEY

# Step 3: Configure YubiKey authentication
echo ""
echo "🔧 Configuring YubiKey authentication..."

# Add user to YubiKey authorized users
echo "dave:$YUBIKEY_ID" | sudo tee /etc/yubico/authorized_yubikeys
sudo chmod 644 /etc/yubico/authorized_yubikeys

# Step 4: Create hybrid authentication system
sudo tee /etc/pam.d/sudo << 'PAM_EOF'
#%PAM-1.0
# Hybrid YubiKey + Session authentication for NexusController

# First check for active session (fast path)
auth [success=2 default=ignore] pam_exec.so quiet /usr/local/bin/check_claude_session.sh

# If no session, require YubiKey + password
auth required pam_yubico.so id=CLIENT_ID_PLACEHOLDER key=SECRET_KEY_PLACEHOLDER authfile=/etc/yubico/authorized_yubikeys

# Standard authentication stack
@include common-auth
@include common-account
@include common-session-noninteractive
PAM_EOF

# Replace placeholders if API keys provided
if [ \! -z "$CLIENT_ID" ] && [ \! -z "$SECRET_KEY" ]; then
    sudo sed -i "s/CLIENT_ID_PLACEHOLDER/$CLIENT_ID/g" /etc/pam.d/sudo
    sudo sed -i "s/SECRET_KEY_PLACEHOLDER/$SECRET_KEY/g" /etc/pam.d/sudo
else
    # Use offline validation
    sudo sed -i "s/id=CLIENT_ID_PLACEHOLDER key=SECRET_KEY_PLACEHOLDER //" /etc/pam.d/sudo
fi

# Step 5: Create session checker for PAM
sudo tee /usr/local/bin/check_claude_session.sh << 'SESSION_EOF'
#\!/bin/bash
# Check if Claude has an active session
SESSION_FILE="/tmp/claude_authorized_$(logname)"
MAX_SESSION_TIME=14400  # 4 hours

if [[ -f "$SESSION_FILE" ]]; then
    auth_time=$(cat "$SESSION_FILE")
    current_time=$(date +%s)
    elapsed=$((current_time - auth_time))
    
    if [[ $elapsed -le $MAX_SESSION_TIME ]]; then
        exit 0  # Session valid - allow access
    else
        rm -f "$SESSION_FILE"  # Clean up expired session
    fi
fi

exit 1  # No valid session - require YubiKey
SESSION_EOF

sudo chmod +x /usr/local/bin/check_claude_session.sh

# Step 6: Create management commands
cat > /home/dave/yubikey_status << 'EOF'
#!/bin/bash
echo "🔑 YubiKey Authentication Status"
echo "================================"
echo "YubiKey ID: $(cat /etc/yubico/authorized_yubikeys 2>/dev/null | cut -d: -f2 || echo 'Not configured')"
echo "Hardware Present: $(lsusb | grep -i yubico > /dev/null && echo 'Yes' || echo 'No')"
echo "Session Active: $(ls /tmp/claude_authorized_* 2>/dev/null && echo 'Yes' || echo 'No')"
echo ""
echo "Authentication modes:"
echo "1. Session active: Passwordless access"
echo "2. No session + YubiKey present: YubiKey required"
echo "3. No session + No YubiKey: Password required"
EOF

chmod +x /home/dave/yubikey_status
echo "✅ YubiKey setup complete!"
