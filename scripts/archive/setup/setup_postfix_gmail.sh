#!/bin/bash

# Setup Postfix with Gmail Relay - More Reliable Than SSMTP
echo "📧 Setting up Postfix with Gmail relay..."
echo "========================================"

# Install postfix
echo "Installing Postfix..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y postfix mailutils sasl2-bin

# Configure postfix for Gmail relay
echo "Configuring Postfix..."

# Main configuration
sudo tee /etc/postfix/main.cf > /dev/null << 'EOF'
# Basic configuration
myhostname = ebon.local
mydomain = ebon.local
myorigin = $mydomain
mydestination = localhost.localdomain, localhost
relayhost = [smtp.gmail.com]:587

# TLS configuration
smtp_use_tls = yes
smtp_sasl_auth_enable = yes
smtp_sasl_security_options = noanonymous
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache

# Network configuration
inet_interfaces = loopback-only
inet_protocols = ipv4
EOF

echo ""
echo "Please provide Gmail credentials:"
read -p "Gmail address (eboncorp@gmail.com): " GMAIL_USER
GMAIL_USER=${GMAIL_USER:-eboncorp@gmail.com}

echo "You need a Gmail App Password (16 characters, no spaces)"
echo "Get it from: https://myaccount.google.com/apppasswords"
read -s -p "App Password: " GMAIL_PASS
echo ""

# Create password file
echo "Creating credentials file..."
echo "[smtp.gmail.com]:587 $GMAIL_USER:$GMAIL_PASS" | sudo tee /etc/postfix/sasl_passwd > /dev/null

# Secure the password file
sudo chmod 600 /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd

# Enable and start postfix
sudo systemctl enable postfix
sudo systemctl restart postfix

# Test the configuration
echo ""
echo "Testing email configuration..."
sleep 2

if echo "Test email from Ebon server monitoring system" | mail -s "Postfix Test from Ebon" "$GMAIL_USER"; then
    echo "✅ Email sent successfully!"
    echo ""
    echo "Enabling email alerts in monitoring scripts..."

    # Enable email alerts in system monitor
    sed -i 's|# echo "$message" | mail|echo "$message" | mail|' /home/ebon/system_monitor.sh

    # Enable email alerts in backup script
    sed -i 's|# echo "Backup failed|echo "Backup failed|' /home/ebon/simple_backup.sh

    echo "✅ Email alerts enabled!"
    echo ""
    echo "📧 Email setup complete!"
    echo "Alerts will be sent to: $GMAIL_USER"
else
    echo "❌ Email test failed."
    echo ""
    echo "Common issues:"
    echo "1. Make sure 2FA is enabled on your Gmail account"
    echo "2. Generate an App Password (not your regular password)"
    echo "3. App Password should be 16 characters without spaces"
    echo ""
    echo "Check postfix logs:"
    echo "sudo journalctl -u postfix -n 20"
fi