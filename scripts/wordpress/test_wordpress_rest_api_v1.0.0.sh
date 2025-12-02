#!/bin/bash

# WordPress REST API Testing Script
# Tests REST API authentication and permissions

# Configuration
SITE_URL="https://rundaverun.org"
USERNAME="rundaverun"

echo "=========================================="
echo "WordPress REST API Testing Tool"
echo "=========================================="
echo ""
echo "Site: $SITE_URL"
echo "User: $USERNAME"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if REST API is accessible
echo "Test 1: Checking REST API availability..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL/wp-json/")

if [ "$RESPONSE" -eq 200 ]; then
    echo -e "${GREEN}✓ REST API is accessible (HTTP 200)${NC}"
else
    echo -e "${RED}✗ REST API returned HTTP $RESPONSE${NC}"
fi
echo ""

# Test 2: Check authentication endpoint
echo "Test 2: Testing authentication endpoint..."
echo "Note: You'll need to enter your password when prompted"
echo ""

read -sp "Enter password for $USERNAME: " PASSWORD
echo ""
echo ""

# Test authenticated request to /wp/v2/users/me
echo "Testing GET /wp/v2/users/me with Basic Auth..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -u "$USERNAME:$PASSWORD" \
    "$SITE_URL/wp-json/wp/v2/users/me")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

echo "Response Code: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Authentication successful!${NC}"
    echo ""
    echo "User Details:"
    echo "$BODY" | grep -o '"name":"[^"]*"' | cut -d: -f2
    echo "$BODY" | grep -o '"id":[0-9]*' | cut -d: -f2
    echo "$BODY" | grep -o '"capabilities":{[^}]*}' | head -1
else
    echo -e "${RED}✗ Authentication failed${NC}"
    echo ""
    echo "Response:"
    echo "$BODY"
fi
echo ""

# Test 3: Try to list posts
echo "Test 3: Testing GET /wp/v2/posts (requires edit_posts capability)..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -u "$USERNAME:$PASSWORD" \
    "$SITE_URL/wp-json/wp/v2/posts?per_page=1")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Can read posts (HTTP 200)${NC}"
else
    echo -e "${RED}✗ Cannot read posts (HTTP $HTTP_CODE)${NC}"
    echo "$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')"
fi
echo ""

# Test 4: Application Password test (if available)
echo "Test 4: Testing Application Password support..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    "$SITE_URL/wp-json/wp/v2/users/me/application-passwords")

if [ "$RESPONSE" -eq 200 ] || [ "$RESPONSE" -eq 401 ]; then
    echo -e "${GREEN}✓ Application Passwords endpoint exists${NC}"
    echo "  (You may need to create an app password in WordPress admin)"
else
    echo -e "${YELLOW}⚠ Application Passwords may not be available (HTTP $RESPONSE)${NC}"
fi
echo ""

echo "=========================================="
echo "Testing complete!"
echo "=========================================="
echo ""
echo "If authentication failed, check:"
echo "1. Username and password are correct"
echo "2. Run the PHP diagnostic script for detailed permission info"
echo "3. Check for security plugins blocking REST API"
echo "4. Review WordPress error logs"
