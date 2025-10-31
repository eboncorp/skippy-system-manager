#!/bin/bash
# SSH connection helper for HP Z4 G4

set -euo pipefail

SERVER="10.0.0.29"

echo "🔧 HP Z4 G4 SSH Connection Helper"
echo "=================================="
echo
echo "Server: $SERVER"
echo "OS: Ubuntu Linux (OpenSSH 8.9)"
echo
echo "To connect manually, use:"
echo "  ssh username@$SERVER"
echo
echo "Common usernames to try:"
echo "  • Your first name (lowercase)"
echo "  • admin"
echo "  • root"
echo "  • hp"
echo "  • ubuntu"
echo "  • dave (if that's your name)"
echo
echo "If you know the username, I can connect for you:"
read -p "Enter username (or press Enter to skip): " USERNAME

if [ -n "$USERNAME" ]; then
    echo
    echo "Connecting as $USERNAME..."
    echo "You'll be prompted for the password."
    exec ssh "$USERNAME@$SERVER"
else
    echo
    echo "To connect manually:"
    echo "1. Open a new terminal"
    echo "2. Run: ssh username@$SERVER"
    echo "3. Enter password when prompted"
    echo
    echo "Once connected, you can:"
    echo "  • Check system: htop, df -h, free -h"
    echo "  • See what's running: ps aux, systemctl status"
    echo "  • Check the web server: sudo systemctl status apache2"
    echo "  • Install your home server: wget your-installer-script"
fi