#!/bin/bash

# Setup Webhook Notifications (Alternative to Email)
echo "🔔 Setting up Webhook Notifications..."
echo "====================================="

echo ""
echo "Choose notification service:"
echo "1. Discord Webhook"
echo "2. Slack Webhook"
echo "3. Custom webhook URL"
echo "4. Cancel"
echo ""
read -p "Choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Discord Webhook Setup:"
        echo "1. Go to your Discord server settings"
        echo "2. Go to Integrations > Webhooks"
        echo "3. Create a new webhook"
        echo "4. Copy the webhook URL"
        echo ""
        read -p "Discord Webhook URL: " WEBHOOK_URL
        SERVICE="Discord"
        ;;
    2)
        echo ""
        echo "Slack Webhook Setup:"
        echo "1. Go to your Slack workspace"
        echo "2. Go to Apps > Incoming Webhooks"
        echo "3. Add to Slack and configure"
        echo "4. Copy the webhook URL"
        echo ""
        read -p "Slack Webhook URL: " WEBHOOK_URL
        SERVICE="Slack"
        ;;
    3)
        read -p "Custom Webhook URL: " WEBHOOK_URL
        SERVICE="Custom"
        ;;
    4)
        echo "Cancelled"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

if [ -z "$WEBHOOK_URL" ]; then
    echo "No webhook URL provided"
    exit 1
fi

# Create webhook notification script
cat > /home/ebon/send_webhook_alert.sh << EOF
#!/bin/bash

# Webhook Alert Sender
WEBHOOK_URL="$WEBHOOK_URL"
SERVICE="$SERVICE"

send_alert() {
    local severity=\$1
    local message=\$2
    local timestamp=\$(date '+%Y-%m-%d %H:%M:%S')

    # Format message based on service
    case "\$SERVICE" in
        "Discord")
            curl -H "Content-Type: application/json" \\
                 -X POST \\
                 -d "{\"content\":\"🚨 **Ebon Server Alert** 🚨\\n**\$severity**: \$message\\n**Time**: \$timestamp\"}" \\
                 "\$WEBHOOK_URL" > /dev/null 2>&1
            ;;
        "Slack")
            curl -H "Content-Type: application/json" \\
                 -X POST \\
                 -d "{\"text\":\"🚨 Ebon Server Alert\\n*Severity*: \$severity\\n*Message*: \$message\\n*Time*: \$timestamp\"}" \\
                 "\$WEBHOOK_URL" > /dev/null 2>&1
            ;;
        *)
            curl -H "Content-Type: application/json" \\
                 -X POST \\
                 -d "{\"severity\":\"\$severity\",\"message\":\"\$message\",\"timestamp\":\"\$timestamp\",\"server\":\"ebon\"}" \\
                 "\$WEBHOOK_URL" > /dev/null 2>&1
            ;;
    esac
}

# Use the function with provided arguments
send_alert "\$1" "\$2"
EOF

chmod +x /home/ebon/send_webhook_alert.sh

# Test the webhook
echo ""
echo "Testing webhook notification..."
/home/ebon/send_webhook_alert.sh "INFO" "Webhook notification system test from Ebon server"

echo ""
echo "✅ Webhook setup complete!"
echo ""
echo "To use webhook alerts instead of email:"
echo "1. Edit /home/ebon/system_monitor.sh"
echo "2. Replace email commands with:"
echo "   /home/ebon/send_webhook_alert.sh \"ERROR\" \"Your message\""
echo ""
echo "Would you like me to enable webhook alerts in monitoring scripts? (y/n)"
read -p "> " enable_webhook

if [ "$enable_webhook" = "y" ]; then
    # Update system monitor to use webhooks
    sed -i 's|# echo "$message" | mail.*|/home/ebon/send_webhook_alert.sh "$severity" "$message"|' /home/ebon/system_monitor.sh

    # Update backup script
    sed -i 's|# echo "Backup failed.*|/home/ebon/send_webhook_alert.sh "ERROR" "Backup failed at $(date). Check backup logs for details"|' /home/ebon/simple_backup.sh

    echo "✅ Webhook alerts enabled in monitoring scripts!"
else
    echo "Manual webhook setup available at: /home/ebon/send_webhook_alert.sh"
fi