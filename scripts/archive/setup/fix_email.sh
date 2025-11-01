#!/bin/bash

# Fix Email Configuration
echo "🔧 Fixing email configuration..."

# Check what's currently configured
echo "Current ssmtp configuration:"
sudo cat /etc/ssmtp/ssmtp.conf 2>/dev/null || echo "No config found"

echo ""
echo "Testing different email approaches..."

# Method 1: Test current ssmtp setup
echo "Testing current ssmtp setup..."
echo "Test email from Ebon server" | mail -s "Test Email 1" eboncorp@gmail.com 2>&1 | head -3

# Method 2: Try with sendmail directly
echo ""
echo "Testing sendmail directly..."
echo -e "Subject: Test Email 2\nFrom: ebon@ebon\nTo: eboncorp@gmail.com\n\nTest email from Ebon server via sendmail" | sendmail eboncorp@gmail.com 2>&1 | head -3

# Method 3: Check mail queue
echo ""
echo "Checking mail queue..."
mailq 2>/dev/null || echo "No mail queue available"

# Method 4: Check system logs for mail errors
echo ""
echo "Recent mail-related errors:"
journalctl -u ssmtp --since "1 hour ago" -n 5 --no-pager 2>/dev/null || echo "No ssmtp logs"

# Show recommendations
echo ""
echo "📧 Email Setup Recommendations:"
echo "================================"
echo ""
echo "Option 1: Use a simple SMTP relay service"
echo "- Install postfix with Gmail relay"
echo "- More reliable than ssmtp"
echo ""
echo "Option 2: Use external notification service"
echo "- Pushover, Slack, Discord webhooks"
echo "- More reliable for alerts"
echo ""
echo "Option 3: File-based alerts only"
echo "- Alerts go to /home/ebon/monitor_alerts.log"
echo "- Check manually or with log monitoring"
echo ""
echo "Current alert file status:"
ls -la /home/ebon/monitor_alerts.log 2>/dev/null || echo "No alerts file yet"
echo ""
echo "Would you like me to:"
echo "1. Set up Postfix with Gmail relay (recommended)"
echo "2. Configure webhook notifications"
echo "3. Keep file-based alerts only"