#!/bin/bash

# RunDaveRun.org Homepage Update Script
# Applies the Louisville colors update to the live WordPress site
# Date: October 18, 2025

echo "============================================"
echo "RunDaveRun.org - Louisville Colors Update"
echo "============================================"
echo ""

# Configuration
WP_USER="dave"
WP_SITE="https://rundaverun.org"
HTML_FILE="/home/dave/Documents/Government/budgets/RunDaveRun/campaign/UPDATED_HOMEPAGE_LOUISVILLE_COLORS.html"
PAGE_ID="7"  # Homepage ID

echo "IMPORTANT: You need to create a WordPress Application Password first!"
echo ""
echo "To create an Application Password:"
echo "1. Go to: https://rundaverun.org/wp-admin/profile.php"
echo "2. Scroll down to 'Application Passwords'"
echo "3. Enter name: 'Claude Code Update'"
echo "4. Click 'Add New Application Password'"
echo "5. Copy the generated password (format: xxxx xxxx xxxx xxxx xxxx xxxx)"
echo "6. Come back here and run this script again with the password"
echo ""
echo "Or, you can manually apply the update:"
echo "1. Go to: https://rundaverun.org/wp-admin/post.php?post=7&action=edit"
echo "2. Switch to HTML/Code editor"
echo "3. Copy contents from: $HTML_FILE"
echo "4. Paste into WordPress editor"
echo "5. Click 'Update'"
echo ""
echo "============================================"

# Check if application password is provided
if [ -z "$1" ]; then
    echo ""
    echo "Usage: $0 <application-password>"
    echo "Example: $0 'abcd efgh ijkl mnop qrst uvwx'"
    echo ""
    exit 1
fi

APP_PASS="$1"

echo ""
echo "Testing WordPress connection..."
USER_CHECK=$(curl -s -X GET "$WP_SITE/wp-json/wp/v2/users/me" -u "$WP_USER:$APP_PASS" | jq -r '.name // empty')

if [ -z "$USER_CHECK" ]; then
    echo "❌ Authentication failed!"
    echo "Please check your application password and try again."
    exit 1
fi

echo "✅ Connected as: $USER_CHECK"
echo ""

echo "Reading updated homepage HTML..."
if [ ! -f "$HTML_FILE" ]; then
    echo "❌ HTML file not found: $HTML_FILE"
    exit 1
fi

CONTENT=$(cat "$HTML_FILE")
echo "✅ HTML file loaded ($(echo "$CONTENT" | wc -c) bytes)"
echo ""

echo "Creating backup of current homepage..."
BACKUP_FILE="/home/dave/Documents/Government/budgets/RunDaveRun/campaign/homepage_backup_$(date +%Y%m%d_%H%M%S).html"
curl -s -X GET "$WP_SITE/wp-json/wp/v2/pages/$PAGE_ID?context=edit" -u "$WP_USER:$APP_PASS" | jq -r '.content.rendered' > "$BACKUP_FILE"
echo "✅ Backup saved to: $BACKUP_FILE"
echo ""

echo "Preparing update payload..."
JSON_PAYLOAD=$(jq -n --arg content "$CONTENT" '{content: $content}')

echo "Uploading new homepage to WordPress..."
RESPONSE=$(curl -s -X POST "$WP_SITE/wp-json/wp/v2/pages/$PAGE_ID" \
  -u "$WP_USER:$APP_PASS" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD")

# Check if update was successful
PAGE_TITLE=$(echo "$RESPONSE" | jq -r '.title.rendered // empty')

if [ -z "$PAGE_TITLE" ]; then
    echo "❌ Update failed!"
    echo "Response: $RESPONSE"
    exit 1
fi

echo "✅ Homepage updated successfully!"
echo "✅ Page: $PAGE_TITLE"
echo ""

echo "============================================"
echo "🎉 UPDATE COMPLETE!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Visit: $WP_SITE"
echo "2. Hard refresh (Ctrl+Shift+R) to clear cache"
echo "3. Test on mobile device"
echo "4. Update donation button URL (currently placeholder)"
echo "5. Update social media links (currently placeholder)"
echo "6. Set up email form (currently placeholder)"
echo ""
echo "For detailed instructions, see:"
echo "- HOW_TO_APPLY_UPDATE.md"
echo "- IMPLEMENTATION_SUMMARY.md"
echo ""
echo "Your backup is saved at: $BACKUP_FILE"
echo ""
