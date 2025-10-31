#!/bin/bash
# WiFi Network Diagnostic Script
# Helps diagnose SSL certificate issues with home WiFi

set -e

OUTPUT_FILE="/tmp/wifi_diagnostics_$(date +%Y%m%d_%H%M%S).txt"

echo "=================================="
echo "Network Diagnostic Tool"
echo "=================================="
echo ""
echo "Output will be saved to: $OUTPUT_FILE"
echo ""

{
    echo "=== NETWORK DIAGNOSTICS ==="
    echo "Timestamp: $(date)"
    echo ""

    echo "=== Current Network Interface ==="
    ip addr show wlp44s0
    echo ""

    echo "=== Current SSID ==="
    iwgetid -r || echo "Could not determine SSID"
    echo ""

    echo "=== Gateway/Router ==="
    route -n | grep "^0.0.0.0"
    echo ""

    echo "=== DNS Configuration ==="
    resolvectl status | head -20
    echo ""

    echo "=== DNS Resolution Test (claude.ai) ==="
    dig claude.ai +short
    nslookup claude.ai
    echo ""

    echo "=== SSL Certificate Check (Command Line) ==="
    echo "Certificate chain from openssl:"
    timeout 10 openssl s_client -connect claude.ai:443 -servername claude.ai 2>&1 </dev/null | grep -A 20 "Certificate chain"
    echo ""

    echo "Certificate issuer details:"
    echo | timeout 10 openssl s_client -connect claude.ai:443 -servername claude.ai 2>/dev/null | openssl x509 -noout -issuer -subject -dates
    echo ""

    echo "=== Full Certificate Details ==="
    echo | timeout 10 openssl s_client -connect claude.ai:443 -servername claude.ai 2>/dev/null | openssl x509 -noout -text | head -50
    echo ""

    echo "=== curl SSL Test ==="
    curl -v https://claude.ai 2>&1 | grep -E "(Server certificate|issuer|subject|start date|expire date|SSL certificate)"
    echo ""

    echo "=== Check for Proxy Settings ==="
    env | grep -i proxy || echo "No proxy environment variables set"
    echo ""

    echo "=== Router/Gateway Check ==="
    GATEWAY=$(route -n | grep "^0.0.0.0" | awk '{print $2}')
    echo "Gateway IP: $GATEWAY"
    ping -c 3 $GATEWAY
    echo ""

    echo "=== DNS Server Check ==="
    DNS_SERVER=$(resolvectl status | grep "Current DNS Server" | head -1 | awk '{print $4}')
    echo "Primary DNS: $DNS_SERVER"
    dig @$DNS_SERVER claude.ai +short
    echo ""

    echo "=== Check System CA Certificates ==="
    ls -lh /etc/ssl/certs/ca-certificates.crt
    echo ""

    echo "=== Browser Certificate Database ==="
    if [ -f ~/.pki/nssdb/cert9.db ]; then
        ls -lh ~/.pki/nssdb/cert9.db
        echo "Chrome/Chromium cert database exists"
    else
        echo "No Chrome/Chromium cert database found"
    fi

    if [ -d ~/.mozilla ]; then
        find ~/.mozilla -name "cert9.db" -ls 2>/dev/null | head -5
    fi
    echo ""

    echo "=== Test Alternative DNS ==="
    echo "Testing with Google DNS (8.8.8.8):"
    dig @8.8.8.8 claude.ai +short
    echo ""
    echo "Testing with Cloudflare DNS (1.1.1.1):"
    dig @1.1.1.1 claude.ai +short
    echo ""

} 2>&1 | tee "$OUTPUT_FILE"

echo ""
echo "=================================="
echo "Diagnostics complete!"
echo "Results saved to: $OUTPUT_FILE"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. If on WiFi and seeing cert errors, run: cat $OUTPUT_FILE"
echo "2. Compare certificate issuer - should be 'Let's Encrypt'"
echo "3. If different issuer, your router is doing SSL inspection"
echo ""
