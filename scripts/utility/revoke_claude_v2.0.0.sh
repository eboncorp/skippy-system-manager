#!/bin/bash
# Revoke Claude authorization immediately

AUTH_FILE="/tmp/claude_authorized_$(whoami)"
MANIFEST_FILE="/tmp/claude_permissions_$(whoami).json"

echo "🔒 Revoking Claude authorization..."

# Remove authorization files
rm -f "$AUTH_FILE"
rm -f "$MANIFEST_FILE"

echo "✅ Authorization revoked"
echo "💡 Run 'authorize_claude' to grant access again"
