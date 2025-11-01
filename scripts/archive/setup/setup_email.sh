#!/bin/bash

# Email Configuration Setup Script
# Sets up ssmtp for Gmail

echo "==================================="
echo "Email Alert Configuration"
echo "==================================="
echo ""
echo "This will configure email alerts using Gmail SMTP"
echo ""
echo "Prerequisites:"
echo "1. Gmail account"
echo "2. App-specific password (not your regular password)"
echo "   Get it here: https://myaccount.google.com/apppasswords"
echo ""
read -p "Continue? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    exit 0
fi

read -p "Enter your Gmail address: " GMAIL
read -s -p "Enter your app-specific password: " PASSWORD
echo ""

# Backup existing config
sudo cp /etc/ssmtp/ssmtp.conf /etc/ssmtp/ssmtp.conf.bak 2>/dev/null

# Create ssmtp config
sudo tee /etc/ssmtp/ssmtp.conf > /dev/null << EOF
root=$GMAIL
mailhub=smtp.gmail.com:587
AuthUser=$GMAIL
AuthPass=$PASSWORD
UseSTARTTLS=YES
FromLineOverride=YES
hostname=$(hostname)
EOF

# Configure revaliases
sudo tee /etc/ssmtp/revaliases > /dev/null << EOF
root:$GMAIL:smtp.gmail.com:587
ebon:$GMAIL:smtp.gmail.com:587
EOF

echo "Testing email configuration..."
echo "This is a test email from your Ebon server monitoring system" | mail -s "Test Alert from Ebon Server" $GMAIL

if [ $? -eq 0 ]; then
    echo "✅ Email configuration successful!"
    echo ""
    echo "Enabling email alerts in monitoring scripts..."

    # Enable alerts in system_monitor.sh
    sed -i 's|# echo "$message" | mail|echo "$message" | mail|' /home/ebon/system_monitor.sh

    # Enable alerts in simple_backup.sh
    sed -i 's|# echo "Backup failed|echo "Backup failed|' /home/ebon/simple_backup.sh

    echo "✅ Email alerts enabled!"
else
    echo "❌ Email test failed. Please check your credentials."
fi