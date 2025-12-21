#!/bin/bash
# WordPress Health Check Automation Script

set -e

SITE_URL="https://rundaverun.org"
WP_AUTH_TOKEN="REDACTED"  # Archived - use environment variables instead
USERNAME="dave"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏥 WORDPRESS HEALTH CHECK - rundaverun.org"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Site Accessibility
echo "1️⃣ Testing site accessibility..."
if curl -s -o /dev/null -w "%{http_code}" "$SITE_URL" | grep -q "200"; then
    echo "   ✅ Site is accessible (HTTP 200)"
else
    echo "   ❌ Site is NOT accessible"
fi
echo ""

# Test 2: REST API Authentication
echo "2️⃣ Testing REST API authentication..."
RESPONSE=$(curl -s -u "$USERNAME:$WP_AUTH_TOKEN" "$SITE_URL/wp-json/wp/v2/users/me")
if echo "$RESPONSE" | grep -q '"id"'; then
    echo "   ✅ REST API authentication working"
    USER_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | cut -d: -f2)
    echo "   User ID: $USER_ID"
else
    echo "   ❌ REST API authentication FAILED"
    echo "   Response: $RESPONSE"
fi
echo ""

# Test 3: Check for roles restoration script
echo "3️⃣ Checking for roles restoration script..."
if curl -s "$SITE_URL/restore-wordpress-roles.php" | grep -q "WordPress"; then
    echo "   ✅ Restoration script exists"
else
    echo "   ❌ Restoration script NOT found"
fi
echo ""

# Test 4: Check CSS loading
echo "4️⃣ Checking CSS loading..."
HTML=$(curl -s "$SITE_URL")
if echo "$HTML" | grep -q "october-19-backup-css"; then
    echo "   ✅ MU plugin CSS found"
elif echo "$HTML" | grep -q "astra-child"; then
    echo "   ⚠️  Child theme CSS found (MU plugin not loading)"
else
    echo "   ❌ No custom CSS detected"
fi
echo ""

# Test 5: Check for PHP errors
echo "5️⃣ Checking for visible PHP errors..."
if echo "$HTML" | grep -qi "error\|warning\|notice"; then
    echo "   ⚠️  Possible PHP errors detected in output"
else
    echo "   ✅ No visible PHP errors"
fi
echo ""

# Test 6: Check menu order
echo "6️⃣ Checking navigation menu..."
if echo "$HTML" | grep -q "Our Plan.*Policy Library"; then
    echo "   ✅ Menu order appears correct"
else
    echo "   ⚠️  Menu order may be incorrect"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Health check complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
