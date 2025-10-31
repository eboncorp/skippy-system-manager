#!/bin/bash
# Enhanced Claude Authorization System v2.0
# Grants Claude permission to work autonomously with safety guardrails

set -e

# Configuration
AUTH_FILE="/tmp/claude_authorized_$(whoami)"
MANIFEST_FILE="/tmp/claude_permissions_$(whoami).json"
TRASH_DIR="/home/dave/.Trash"
DURATION_HOURS=4
DURATION_SECONDS=$((DURATION_HOURS * 3600))

# Create trash directory if it doesn't exist
mkdir -p "$TRASH_DIR"

# Get current timestamp
TIMESTAMP=$(date +%s)
EXPIRY=$((TIMESTAMP + DURATION_SECONDS))
EXPIRY_READABLE=$(date -d "@$EXPIRY" '+%Y-%m-%d %H:%M:%S')

# Create authorization file
echo "$TIMESTAMP" > "$AUTH_FILE"
chmod 600 "$AUTH_FILE"

# Create permission manifest (JSON format for easy parsing)
cat > "$MANIFEST_FILE" << EOF
{
  "authorized_at": $TIMESTAMP,
  "expires_at": $EXPIRY,
  "duration_hours": $DURATION_HOURS,
  "authorized_by": "$(whoami)",
  "permissions": {
    "allowed_without_asking": [
      "write_files",
      "edit_files",
      "create_files",
      "create_directories",
      "git_commit",
      "git_push",
      "deploy_production",
      "run_scripts",
      "modify_configs",
      "install_packages",
      "restart_services",
      "database_operations_non_destructive",
      "clear_caches",
      "download_files",
      "upload_files",
      "api_calls",
      "wordpress_operations",
      "github_actions"
    ],
    "auto_trash_instead_of_delete": [
      "delete_files",
      "delete_directories",
      "remove_database_rows"
    ],
    "always_ask_permission": [
      "permanent_deletion",
      "password_changes",
      "credential_modifications",
      "user_account_changes",
      "drop_database_tables",
      "drop_databases",
      "format_disks",
      "system_critical_changes"
    ],
    "trash_directory": "$TRASH_DIR",
    "trash_retention_days": 30
  },
  "metadata": {
    "version": "2.0",
    "created": "$(date -Iseconds)"
  }
}
EOF

chmod 600 "$MANIFEST_FILE"

# Display authorization status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔓 CLAUDE AUTHORIZATION GRANTED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏰ Duration: $DURATION_HOURS hours"
echo "📅 Expires: $EXPIRY_READABLE"
echo "🗑️  Trash: $TRASH_DIR"
echo ""
echo "✅ ALLOWED without asking:"
echo "   • Write/edit/create files and directories"
echo "   • Git operations (commit, push)"
echo "   • Deploy to production"
echo "   • Run scripts and install packages"
echo "   • Restart services and clear caches"
echo "   • Database operations (SELECT, UPDATE, INSERT)"
echo "   • WordPress and GitHub operations"
echo ""
echo "🗑️  AUTO-TRASH (instead of permanent delete):"
echo "   • File deletions → moved to ~/.Trash/"
echo "   • Directory deletions → moved to ~/.Trash/"
echo "   • Database row deletions → exported to backup first"
echo ""
echo "❌ ALWAYS requires your permission:"
echo "   • Permanent deletions (rm -rf, DROP, etc.)"
echo "   • Password or credential changes"
echo "   • User account modifications"
echo "   • System-critical operations"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Commands:"
echo "   revoke_claude        - End authorization immediately"
echo "   claude_auth_status   - Check current authorization status"
echo ""
