#!/bin/bash
# Interactive SSH setup script for HP Z4 G4
# Run this in your own terminal for password prompts

set -e

TARGET="ebon@10.0.0.29"

echo "🔧 Interactive SSH Key Setup"
echo "============================="
echo
echo "This script will copy your SSH key to: $TARGET"
echo "You'll be prompted for the password."
echo
echo "Press Enter to continue or Ctrl+C to cancel..."
read

echo "🔑 Copying SSH key..."
ssh-copy-id "$TARGET"

echo
echo "✅ SSH key copied! Testing connection..."

if ssh -o BatchMode=yes "$TARGET" "echo 'SSH key authentication successful!'" 2>/dev/null; then
    echo "🎉 Success! SSH key authentication is working."
    echo
    echo "🔍 Getting system information from HP Z4 G4..."
    
    ssh "$TARGET" "
        echo '=== System Information ==='
        echo 'Hostname:' \$(hostname)
        echo 'User:' \$(whoami)
        echo 'OS:' \$(lsb_release -d 2>/dev/null | cut -f2 || uname -o)
        echo 'Kernel:' \$(uname -r)
        echo 'Uptime:' \$(uptime -p 2>/dev/null || uptime)
        echo
        
        echo '=== Hardware Resources ==='
        free -h
        echo
        df -h / /home 2>/dev/null | grep -v tmpfs
        echo
        
        echo '=== Network Configuration ==='
        ip -4 addr show | grep -E 'inet.*scope global' | awk '{print \$2, \$NF}'
        echo
        
        echo '=== Active Services ==='
        systemctl --no-pager status apache2 2>/dev/null | head -3 || echo 'Apache: not found'
        systemctl --no-pager status nginx 2>/dev/null | head -3 || echo 'Nginx: not found'
        systemctl --no-pager status docker 2>/dev/null | head -3 || echo 'Docker: not found'
        echo
        
        echo '=== Listening Ports ==='
        ss -tlnp 2>/dev/null | grep LISTEN | head -10
        echo
        
        echo '=== Web Server Details ==='
        ps aux | grep -E '[Aa]pache|[Nn]ginx|[Hh]ttpd' | grep -v grep || echo 'No web server processes found'
    "
    
else
    echo "❌ SSH key authentication failed. Please check the setup."
fi

echo
echo "🏠 Ready to install Home Server Master on this HP Z4 G4!"
echo "Run: scp home_server_installer.sh $TARGET:/tmp/ && ssh $TARGET"