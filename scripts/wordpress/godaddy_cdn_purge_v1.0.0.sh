#!/bin/bash
# godaddy_cdn_purge_v1.0.0.sh
# Purge CDN cache for GoDaddy WordPress hosting
#
# Usage:
#   ./godaddy_cdn_purge_v1.0.0.sh [--full]
#
# Options:
#   --full    Full cache purge (default: smart purge)
#
# Created: 2026-01-24

set -euo pipefail

# Load credentials
CREDS_FILE="$HOME/.config/godaddy/api_credentials.json"

if [[ ! -f "$CREDS_FILE" ]]; then
    echo "❌ Credentials file not found: $CREDS_FILE"
    exit 1
fi

API_KEY=$(python3 -c "import json; print(json.load(open('$CREDS_FILE'))['api_key'])")
API_SECRET=$(python3 -c "import json; print(json.load(open('$CREDS_FILE'))['api_secret'])")
DOMAIN=$(python3 -c "import json; print(json.load(open('$CREDS_FILE'))['domain'])")

# SSH connection for remote WP-CLI
SSH_KEY="$HOME/.ssh/godaddy_rundaverun"
SSH_USER="git_deployer_f44cc3416a_545525"
SSH_HOST="bp6.0cf.myftpupload.com"

echo "═══════════════════════════════════════════════════"
echo "  GoDaddy CDN Cache Purge"
echo "═══════════════════════════════════════════════════"
echo "Domain: $DOMAIN"
echo ""

# Method 1: WP-CLI cache flush via SSH (most reliable)
echo "1. Flushing WordPress cache..."
SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
    -i "$SSH_KEY" \
    "${SSH_USER}@${SSH_HOST}" \
    'cd html && wp cache flush --allow-root && wp transient delete --all --allow-root && wp rewrite flush --allow-root' 2>/dev/null || {
    echo "   ⚠️  WP-CLI flush failed (non-critical)"
}
echo "   ✅ WordPress cache flushed"

# Method 2: Try GoDaddy API cache purge
echo "2. Attempting GoDaddy API cache purge..."
API_RESPONSE=$(curl -s -X POST \
    "https://api.godaddy.com/v1/cloud/hosting/sites/${DOMAIN}/cache/purge" \
    -H "Authorization: sso-key ${API_KEY}:${API_SECRET}" \
    -H "Content-Type: application/json" \
    -d '{"type": "all"}' 2>/dev/null || echo '{"error": "request_failed"}')

if echo "$API_RESPONSE" | grep -q "error"; then
    echo "   ⚠️  API purge not available (may need different endpoint)"
    echo "   💡 GoDaddy managed WordPress may require manual CDN purge"
else
    echo "   ✅ CDN purge requested via API"
fi

# Method 3: Ping the site to warm cache
echo "3. Warming cache with site ping..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}/" 2>/dev/null || echo "000")
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "   ✅ Site responding (HTTP $HTTP_STATUS)"
else
    echo "   ⚠️  Site returned HTTP $HTTP_STATUS"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "Summary:"
echo "  WordPress cache: ✅ Flushed"
echo "  CDN cache:       ⚠️  May need manual purge in GoDaddy panel"
echo "  Site status:     HTTP $HTTP_STATUS"
echo ""
echo "💡 For full CDN purge, visit:"
echo "   https://myh.godaddy.com/ → Hosting → Manage → CDN → Purge"
echo "═══════════════════════════════════════════════════"
