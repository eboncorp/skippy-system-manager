#!/bin/bash
# Claude Authorization Checker - Use this in scripts to verify authorization

check_claude_authorization() {
    local AUTH_FILE="/tmp/claude_authorized_$(whoami)"
    local MANIFEST_FILE="/tmp/claude_permissions_$(whoami).json"

    # Check if authorization file exists
    if [[ ! -f "$AUTH_FILE" ]]; then
        echo "❌ Not authorized - run 'authorize_claude' first"
        return 1
    fi

    # Check if authorization has expired
    local AUTH_TIME=$(cat "$AUTH_FILE")
    local CURRENT_TIME=$(date +%s)
    local ELAPSED=$((CURRENT_TIME - AUTH_TIME))
    local MAX_TIME=14400  # 4 hours

    if [[ $ELAPSED -gt $MAX_TIME ]]; then
        echo "⏰ Authorization expired (${ELAPSED}s ago) - run 'authorize_claude' again"
        return 1
    fi

    # Calculate time remaining
    local REMAINING=$((MAX_TIME - ELAPSED))
    local HOURS=$((REMAINING / 3600))
    local MINUTES=$(((REMAINING % 3600) / 60))

    echo "✅ Authorized (${HOURS}h ${MINUTES}m remaining)"
    return 0
}

# Check if a specific operation is allowed
check_permission() {
    local operation="$1"
    local MANIFEST_FILE="/tmp/claude_permissions_$(whoami).json"

    if [[ ! -f "$MANIFEST_FILE" ]]; then
        echo "❌ No permission manifest found"
        return 1
    fi

    # Check in allowed list
    if grep -q "\"$operation\"" "$MANIFEST_FILE" 2>/dev/null; then
        return 0
    fi

    return 1
}

# Trash a file instead of deleting it
trash_file() {
    local file="$1"
    local TRASH_DIR="/home/dave/.Trash"

    if [[ ! -e "$file" ]]; then
        echo "❌ File doesn't exist: $file"
        return 1
    fi

    # Create trash directory if needed
    mkdir -p "$TRASH_DIR"

    # Create timestamped trash subdirectory
    local TRASH_SUBDIR="$TRASH_DIR/$(date +%Y-%m-%d_%H-%M-%S)"
    mkdir -p "$TRASH_SUBDIR"

    # Move to trash
    local BASENAME=$(basename "$file")
    mv "$file" "$TRASH_SUBDIR/$BASENAME"

    echo "🗑️  Moved to trash: $TRASH_SUBDIR/$BASENAME"
    return 0
}

# Main execution if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    check_claude_authorization
fi
