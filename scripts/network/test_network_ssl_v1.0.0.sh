#!/bin/bash
# Quick SSL Certificate Network Test
# Run this on both hotspot and WiFi to compare

SITE="claude.ai"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "=================================="
echo "SSL Certificate Test - $SITE"
echo "Time: $TIMESTAMP"
echo "=================================="
echo ""

# Get current network info
echo "Current Network:"
SSID=$(iwgetid -r 2>/dev/null || echo "Unknown")
GATEWAY=$(route -n | grep "^0.0.0.0" | awk '{print $2}')
IP=$(ip addr show wlp44s0 | grep "inet " | awk '{print $2}')
DNS=$(resolvectl status | grep "Current DNS Server" | head -1 | awk '{print $4}')

echo "  SSID: $SSID"
echo "  IP Address: $IP"
echo "  Gateway: $GATEWAY"
echo "  DNS Server: $DNS"
echo ""

# DNS resolution
echo "DNS Resolution:"
RESOLVED_IP=$(dig +short $SITE | head -1)
echo "  $SITE resolves to: $RESOLVED_IP"
echo ""

# Certificate check
echo "Certificate Information:"
CERT_INFO=$(echo | timeout 10 openssl s_client -connect ${SITE}:443 -servername $SITE 2>/dev/null | openssl x509 -noout -issuer -subject -dates 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$CERT_INFO"
    echo ""

    # Extract issuer
    ISSUER=$(echo "$CERT_INFO" | grep "issuer" | cut -d'=' -f2-)
    echo "Certificate Issuer: $ISSUER"

    # Check if it's Let's Encrypt (expected)
    if echo "$ISSUER" | grep -q "Let's Encrypt"; then
        echo "✓ Certificate is from Let's Encrypt (EXPECTED - GOOD)"
    else
        echo "✗ WARNING: Certificate is NOT from Let's Encrypt!"
        echo "  This suggests your network is intercepting HTTPS traffic"
    fi
else
    echo "✗ ERROR: Could not retrieve certificate"
fi

echo ""

# Test actual HTTPS connection
echo "Testing HTTPS Connection:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://${SITE}/ 2>/dev/null)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "  ✓ HTTPS connection successful (HTTP $HTTP_CODE)"
else
    echo "  ✗ HTTPS connection failed or unusual (HTTP $HTTP_CODE)"
fi

echo ""
echo "=================================="

# Save to log
LOG_FILE="/tmp/ssl_test_log.txt"
{
    echo "--- Test at $TIMESTAMP ---"
    echo "Network: $SSID (Gateway: $GATEWAY, DNS: $DNS)"
    echo "Certificate Issuer: $ISSUER"
    echo ""
} >> "$LOG_FILE"

echo "Results appended to: $LOG_FILE"
echo ""
