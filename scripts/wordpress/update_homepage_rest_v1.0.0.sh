#!/bin/bash
# Update Homepage via WordPress REST API
# This script updates page ID 105 (homepage) with improved content

# Configuration
SITE_URL="https://rundaverun.org"
PAGE_ID="105"
USERNAME="${WP_ADMIN_USERNAME:?Set WP_ADMIN_USERNAME environment variable}"
PASSWORD="${WP_ADMIN_PASSWORD:?Set WP_ADMIN_PASSWORD environment variable}"
HTML_FILE="UPDATED_HOMEPAGE_LOUISVILLE_COLORS.html"

# Read the HTML content and escape it for JSON
CONTENT=$(cat "$HTML_FILE" | jq -Rs .)

# Create JSON payload
JSON_PAYLOAD=$(cat <<EOF
{
  "content": $CONTENT,
  "status": "publish"
}
EOF
)

# Update the page using REST API
curl -X POST \
  -H "Content-Type: application/json" \
  -u "$USERNAME:$PASSWORD" \
  -d "$JSON_PAYLOAD" \
  "$SITE_URL/wp-json/wp/v2/pages/$PAGE_ID"

echo ""
echo "✅ Homepage update complete!"
echo "Visit: $SITE_URL to see changes"
