#!/bin/bash
# Display current Claude authorization status

AUTH_FILE="/tmp/claude_authorized_$(whoami)"
MANIFEST_FILE="/tmp/claude_permissions_$(whoami).json"
TRASH_DIR="/home/dave/.Trash"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 CLAUDE AUTHORIZATION STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check authorization
if [[ ! -f "$AUTH_FILE" ]]; then
    echo "Status: ❌ NOT AUTHORIZED"
    echo ""
    echo "Run 'authorize_claude' to grant permissions"
    exit 1
fi

# Check expiry
AUTH_TIME=$(cat "$AUTH_FILE")
CURRENT_TIME=$(date +%s)
ELAPSED=$((CURRENT_TIME - AUTH_TIME))
MAX_TIME=14400  # 4 hours

if [[ $ELAPSED -gt $MAX_TIME ]]; then
    EXPIRED_AGO=$((ELAPSED - MAX_TIME))
    HOURS=$((EXPIRED_AGO / 3600))
    MINUTES=$(((EXPIRED_AGO % 3600) / 60))

    echo "Status: ⏰ EXPIRED"
    echo "Expired: ${HOURS}h ${MINUTES}m ago"
    echo ""
    echo "Run 'authorize_claude' to renew authorization"
    exit 1
fi

# Active authorization
REMAINING=$((MAX_TIME - ELAPSED))
HOURS=$((REMAINING / 3600))
MINUTES=$(((REMAINING % 3600) / 60))
AUTH_DATE=$(date -d "@$AUTH_TIME" '+%Y-%m-%d %H:%M:%S')
EXPIRY_DATE=$(date -d "@$((AUTH_TIME + MAX_TIME))" '+%Y-%m-%d %H:%M:%S')

echo "Status: ✅ ACTIVE"
echo "Authorized: $AUTH_DATE"
echo "Expires: $EXPIRY_DATE"
echo "Remaining: ${HOURS}h ${MINUTES}m"
echo ""

# Show trash info
if [[ -d "$TRASH_DIR" ]]; then
    TRASH_COUNT=$(find "$TRASH_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    if [[ $TRASH_COUNT -gt 0 ]]; then
        echo "🗑️  Trash: $TRASH_COUNT deletion(s) in $TRASH_DIR"
        echo ""
        echo "Recent deletions:"
        find "$TRASH_DIR" -mindepth 1 -maxdepth 1 -type d -printf "   • %f\n" | sort -r | head -5
    else
        echo "🗑️  Trash: Empty ($TRASH_DIR)"
    fi
else
    echo "🗑️  Trash: Not yet created"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
