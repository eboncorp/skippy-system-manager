#!/bin/bash
# Code Snippet Manager v1.0.0
# Manage and quickly insert code snippets
# Part of: Skippy Enhancement Project - TIER 2
# Created: 2025-11-04

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SKIPPY_BASE="/home/dave/skippy"
SNIPPETS_DIR="${SKIPPY_BASE}/.snippets"
SNIPPETS_INDEX="${SNIPPETS_DIR}/index.json"

usage() {
    cat <<EOF
Code Snippet Manager v1.0.0

USAGE:
    $0 <command> [options]

COMMANDS:
    list [category]              List all snippets (optionally by category)
    show <name>                  Show snippet content
    add <name> <file>            Add snippet from file
    add-stdin <name>             Add snippet from stdin
    insert <name>                Insert snippet (outputs to stdout)
    delete <name>                Remove snippet
    search <keyword>             Search snippets
    categories                   List all categories
    export <name> <file>         Export snippet to file
    init                         Initialize snippet library with defaults

CATEGORIES:
    bash, python, wordpress, sql, git, deployment, security, backup

EXAMPLES:
    # List all snippets
    $0 list

    # List WordPress snippets
    $0 list wordpress

    # Show a snippet
    $0 show wp-db-query

    # Insert snippet into script
    $0 insert error-handler >> my_script.sh

    # Add new snippet
    $0 add my-snippet snippet.sh

    # Add from clipboard/stdin
    echo "code here" | $0 add-stdin test-snippet

    # Search for snippet
    $0 search "database"

EOF
    exit 1
}

# Ensure directory structure
init_snippets() {
    mkdir -p "$SNIPPETS_DIR"

    if [ -f "$SNIPPETS_INDEX" ]; then
        echo -e "${YELLOW}Snippet library already initialized${NC}"
        return
    fi

    # Create index
    cat > "$SNIPPETS_INDEX" <<'EOF'
{
  "created": "2025-11-04",
  "snippets": {}
}
EOF

    # Add default snippets
    create_default_snippets

    echo -e "${GREEN}✓ Snippet library initialized${NC}"
    echo "  Location: $SNIPPETS_DIR"
}

# Create default useful snippets
create_default_snippets() {
    # Bash error handler
    cat > "${SNIPPETS_DIR}/bash-error-handler.sh" <<'EOF'
# Error handler for bash scripts
set -euo pipefail

error_handler() {
    local line_number=$1
    echo "Error on line $line_number"
    exit 1
}

trap 'error_handler ${LINENO}' ERR
EOF
    add_snippet_to_index "bash-error-handler" "bash" "Standard bash error handling setup"

    # Bash colors
    cat > "${SNIPPETS_DIR}/bash-colors.sh" <<'EOF'
# Color codes for bash output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color

# Usage:
# echo -e "${RED}Error message${NC}"
# echo -e "${GREEN}Success message${NC}"
EOF
    add_snippet_to_index "bash-colors" "bash" "Color codes for terminal output"

    # Bash logging
    cat > "${SNIPPETS_DIR}/bash-logging.sh" <<'EOF'
# Logging functions for bash scripts
LOG_FILE="${LOG_FILE:-/var/log/script.log}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" | tee -a "$LOG_FILE"
}
EOF
    add_snippet_to_index "bash-logging" "bash" "Logging functions with timestamps"

    # WordPress DB query
    cat > "${SNIPPETS_DIR}/wp-db-query.sh" <<'EOF'
# WordPress database query with WP-CLI
wp db query "SELECT * FROM wp_posts WHERE post_status='publish' LIMIT 10"

# With variables
POST_TYPE="post"
wp db query "SELECT ID, post_title FROM wp_posts WHERE post_type='${POST_TYPE}'"

# Export to CSV
wp db query "SELECT * FROM wp_posts" --csv > export.csv
EOF
    add_snippet_to_index "wp-db-query" "wordpress" "WP-CLI database query examples"

    # WordPress search-replace
    cat > "${SNIPPETS_DIR}/wp-search-replace.sh" <<'EOF'
# WordPress search and replace
wp search-replace "old-value" "new-value" --precise --report-changed-only

# Dry run first
wp search-replace "old-value" "new-value" --dry-run

# Specific tables
wp search-replace "old" "new" wp_posts wp_postmeta --precise
EOF
    add_snippet_to_index "wp-search-replace" "wordpress" "WP-CLI search and replace"

    # Git commit with message
    cat > "${SNIPPETS_DIR}/git-commit.sh" <<'EOF'
# Git commit with multi-line message
git commit -m "$(cat <<'COMMITMSG'
Brief description of changes

Detailed explanation of what changed and why.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
COMMITMSG
)"
EOF
    add_snippet_to_index "git-commit" "git" "Git commit with formatted message"

    # Backup with rotation
    cat > "${SNIPPETS_DIR}/backup-rotation.sh" <<'EOF'
# Backup with automatic rotation
BACKUP_DIR="/home/dave/skippy/backups"
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S).tar.gz"
KEEP_DAYS=30

# Create backup
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}" /path/to/data

# Delete old backups
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +$KEEP_DAYS -delete
EOF
    add_snippet_to_index "backup-rotation" "backup" "Create backup with automatic rotation"

    # Security audit log entry
    cat > "${SNIPPETS_DIR}/audit-log.sh" <<'EOF'
# Security audit log entry
AUDIT_LOG="/home/dave/skippy/logs/security/audit_trail.log"
ACTION="$1"
DETAILS="$2"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$USER] [$ACTION] $DETAILS" >> "$AUDIT_LOG"
EOF
    add_snippet_to_index "audit-log" "security" "Write to security audit log"

    # Python error handling
    cat > "${SNIPPETS_DIR}/python-error-handler.py" <<'EOF'
# Python error handling with logging
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('script.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

try:
    # Your code here
    pass
except Exception as e:
    logging.error(f"Error: {e}")
    raise
EOF
    add_snippet_to_index "python-error-handler" "python" "Python error handling with logging"

    # SQL backup
    cat > "${SNIPPETS_DIR}/mysql-backup.sh" <<'EOF'
# MySQL database backup
DB_NAME="database_name"
DB_USER="username"
DB_PASS="password"
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"

mysqldump -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" > "$BACKUP_FILE"

# With compression
mysqldump -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" | gzip > "${BACKUP_FILE}.gz"
EOF
    add_snippet_to_index "mysql-backup" "sql" "MySQL database backup command"

    # Deployment checklist
    cat > "${SNIPPETS_DIR}/deployment-checklist.sh" <<'EOF'
# Deployment checklist script
echo "Pre-deployment checklist:"
echo "[ ] Run tests"
echo "[ ] Create backup"
echo "[ ] Validate content"
echo "[ ] Check for errors"
echo "[ ] Review changes"
echo
read -p "All checks passed? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    exit 1
fi
EOF
    add_snippet_to_index "deployment-checklist" "deployment" "Interactive deployment checklist"
}

# Add snippet to index
add_snippet_to_index() {
    local name="$1"
    local category="$2"
    local description="$3"

    if [ ! -f "$SNIPPETS_INDEX" ]; then
        init_snippets
    fi

    local temp=$(mktemp)
    jq --arg name "$name" \
       --arg category "$category" \
       --arg desc "$description" \
       '.snippets[$name] = {category: $category, description: $desc, created: now|todate}' \
       "$SNIPPETS_INDEX" > "$temp"
    mv "$temp" "$SNIPPETS_INDEX"
}

# List snippets
list_snippets() {
    local category="${1:-}"

    if [ ! -f "$SNIPPETS_INDEX" ]; then
        echo -e "${YELLOW}No snippets found. Run: $0 init${NC}"
        exit 0
    fi

    echo -e "${BLUE}Code Snippets:${NC}"
    echo

    if [ -z "$category" ]; then
        # List all
        jq -r '.snippets | to_entries[] |
            "Name: \(.key)\n  Category: \(.value.category)\n  Description: \(.value.description)\n"' \
            "$SNIPPETS_INDEX"
    else
        # Filter by category
        jq -r --arg cat "$category" \
            '.snippets | to_entries[] | select(.value.category == $cat) |
            "Name: \(.key)\n  Description: \(.value.description)\n"' \
            "$SNIPPETS_INDEX"
    fi
}

# Show snippet content
show_snippet() {
    local name="$1"

    if [ -z "$name" ]; then
        echo -e "${RED}Snippet name required${NC}"
        usage
    fi

    local snippet_file="${SNIPPETS_DIR}/${name}.sh"
    if [ ! -f "$snippet_file" ]; then
        snippet_file="${SNIPPETS_DIR}/${name}.py"
    fi

    if [ ! -f "$snippet_file" ]; then
        echo -e "${RED}Snippet not found: $name${NC}"
        exit 1
    fi

    echo -e "${BLUE}Snippet: $name${NC}"
    echo "─────────────────────────────────────"
    cat "$snippet_file"
    echo "─────────────────────────────────────"
}

# Insert snippet (output to stdout)
insert_snippet() {
    local name="$1"

    if [ -z "$name" ]; then
        echo -e "${RED}Snippet name required${NC}" >&2
        usage
    fi

    local snippet_file="${SNIPPETS_DIR}/${name}.sh"
    if [ ! -f "$snippet_file" ]; then
        snippet_file="${SNIPPETS_DIR}/${name}.py"
    fi

    if [ ! -f "$snippet_file" ]; then
        echo -e "${RED}Snippet not found: $name${NC}" >&2
        exit 1
    fi

    cat "$snippet_file"
}

# Add snippet from file
add_snippet() {
    local name="$1"
    local file="$2"

    if [ -z "$name" ] || [ -z "$file" ]; then
        echo -e "${RED}Name and file required${NC}"
        usage
    fi

    if [ ! -f "$file" ]; then
        echo -e "${RED}File not found: $file${NC}"
        exit 1
    fi

    # Determine extension
    local ext="${file##*.}"
    local snippet_file="${SNIPPETS_DIR}/${name}.${ext}"

    cp "$file" "$snippet_file"

    echo -e "${BLUE}Category for snippet:${NC}"
    read -p "Category (bash/python/wordpress/sql/git/deployment/security/backup): " category
    read -p "Description: " description

    add_snippet_to_index "$name" "$category" "$description"

    echo -e "${GREEN}✓ Snippet added: $name${NC}"
}

# Add snippet from stdin
add_snippet_stdin() {
    local name="$1"

    if [ -z "$name" ]; then
        echo -e "${RED}Snippet name required${NC}"
        usage
    fi

    echo -e "${BLUE}Enter snippet code (Ctrl+D when done):${NC}"
    local snippet_file="${SNIPPETS_DIR}/${name}.sh"
    cat > "$snippet_file"

    echo -e "${BLUE}Category for snippet:${NC}"
    read -p "Category: " category
    read -p "Description: " description

    add_snippet_to_index "$name" "$category" "$description"

    echo -e "${GREEN}✓ Snippet added: $name${NC}"
}

# Delete snippet
delete_snippet() {
    local name="$1"

    if [ -z "$name" ]; then
        echo -e "${RED}Snippet name required${NC}"
        usage
    fi

    read -p "Delete snippet '$name'? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled"
        exit 0
    fi

    # Remove file
    rm -f "${SNIPPETS_DIR}/${name}".{sh,py} 2>/dev/null || true

    # Remove from index
    local temp=$(mktemp)
    jq --arg name "$name" 'del(.snippets[$name])' "$SNIPPETS_INDEX" > "$temp"
    mv "$temp" "$SNIPPETS_INDEX"

    echo -e "${GREEN}✓ Snippet deleted: $name${NC}"
}

# Search snippets
search_snippets() {
    local keyword="$1"

    if [ -z "$keyword" ]; then
        echo -e "${RED}Search keyword required${NC}"
        usage
    fi

    echo -e "${BLUE}Searching for: $keyword${NC}"
    echo

    # Search in index
    jq -r --arg kw "$keyword" \
        '.snippets | to_entries[] |
        select(.key | contains($kw) or .value.description | contains($kw)) |
        "Name: \(.key)\n  Category: \(.value.category)\n  Description: \(.value.description)\n"' \
        "$SNIPPETS_INDEX"

    # Search in files
    echo -e "${BLUE}Content matches:${NC}"
    grep -l -i "$keyword" "${SNIPPETS_DIR}"/*.{sh,py} 2>/dev/null | while read -r file; do
        echo "  $(basename "$file")"
    done
}

# List categories
list_categories() {
    if [ ! -f "$SNIPPETS_INDEX" ]; then
        echo -e "${YELLOW}No snippets found${NC}"
        exit 0
    fi

    echo -e "${BLUE}Categories:${NC}"
    jq -r '.snippets | [.[].category] | unique | .[]' "$SNIPPETS_INDEX" | while read -r cat; do
        local count=$(jq -r --arg cat "$cat" \
            '.snippets | [.[] | select(.category == $cat)] | length' \
            "$SNIPPETS_INDEX")
        echo "  $cat ($count snippets)"
    done
}

# Export snippet
export_snippet() {
    local name="$1"
    local output_file="$2"

    if [ -z "$name" ] || [ -z "$output_file" ]; then
        echo -e "${RED}Name and output file required${NC}"
        usage
    fi

    insert_snippet "$name" > "$output_file"
    echo -e "${GREEN}✓ Exported to: $output_file${NC}"
}

# Main command dispatcher
COMMAND="${1:-}"

case "$COMMAND" in
    init)
        init_snippets
        ;;
    list)
        list_snippets "${2:-}"
        ;;
    show)
        show_snippet "${2:-}"
        ;;
    insert)
        insert_snippet "${2:-}"
        ;;
    add)
        add_snippet "${2:-}" "${3:-}"
        ;;
    add-stdin)
        add_snippet_stdin "${2:-}"
        ;;
    delete)
        delete_snippet "${2:-}"
        ;;
    search)
        search_snippets "${2:-}"
        ;;
    categories)
        list_categories
        ;;
    export)
        export_snippet "${2:-}" "${3:-}"
        ;;
    *)
        usage
        ;;
esac

exit 0
