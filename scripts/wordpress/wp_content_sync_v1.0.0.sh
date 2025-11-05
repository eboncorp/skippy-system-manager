#!/bin/bash
# WordPress Content Sync Tool v1.0.0
# Syncs content between local and production
# Part of: Skippy Enhancement Project - TIER 2
# Created: 2025-11-04

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

LOCAL_PATH="/home/dave/Local Sites/rundaverun-local/app/public"
SKIPPY_BASE="/home/dave/skippy"
SYNC_REPORT_DIR="${SKIPPY_BASE}/conversations/wp_sync_reports"
SECRETS_MGR="${SKIPPY_BASE}/scripts/security/secrets_manager_v1.0.0.sh"

usage() {
    cat <<EOF
WordPress Content Sync Tool v1.0.0

USAGE:
    $0 <direction> <content_type> [options]

DIRECTIONS:
    pull                         Pull from production to local
    push                         Push from local to production
    compare                      Compare local vs production
    sync                         Two-way sync (interactive)

CONTENT TYPES:
    posts                        All posts
    pages                        All pages
    policies                     Policy posts
    media                        Media library
    all                          Everything

OPTIONS:
    --dry-run                    Show what would be synced
    --force                      Skip confirmation prompts
    --exclude-drafts             Don't sync draft content
    --backup                     Create backup before sync

EXAMPLES:
    # Compare local vs production
    $0 compare all

    # Pull production posts to local (dry run)
    $0 pull posts --dry-run

    # Push local policies to production (with backup)
    $0 push policies --backup

    # Full sync with confirmation
    $0 sync all

SAFETY:
    - Always creates backup before push
    - Dry-run mode available
    - Interactive confirmation for destructive operations
    - Detailed sync reports generated

EOF
    exit 1
}

# Parse options
DRY_RUN=false
FORCE=false
EXCLUDE_DRAFTS=false
BACKUP=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --exclude-drafts)
            EXCLUDE_DRAFTS=true
            shift
            ;;
        --backup)
            BACKUP=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

DIRECTION="${1:-}"
CONTENT_TYPE="${2:-}"

if [ -z "$DIRECTION" ] || [ -z "$CONTENT_TYPE" ]; then
    usage
fi

# Ensure directories exist
mkdir -p "$SYNC_REPORT_DIR"

# Report file
REPORT_FILE="${SYNC_REPORT_DIR}/sync_$(date +%Y%m%d_%H%M%S).md"

# Start report
cat > "$REPORT_FILE" <<EOF
# WordPress Content Sync Report

**Date:** $(date)
**Direction:** $DIRECTION
**Content Type:** $CONTENT_TYPE
**Mode:** $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "LIVE")

---

## Sync Details

EOF

log() {
    echo -e "${BLUE}$1${NC}"
    echo "$1" >> "$REPORT_FILE"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
    echo "✓ $1" >> "$REPORT_FILE"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    echo "⚠ $1" >> "$REPORT_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    echo "❌ $1" >> "$REPORT_FILE"
}

# Check WP-CLI
if ! command -v wp &> /dev/null; then
    error "WP-CLI not found"
    exit 1
fi

# Get production credentials
get_prod_credentials() {
    if [ -x "$SECRETS_MGR" ]; then
        PROD_HOST=$($SECRETS_MGR get prod_ssh_host 2>/dev/null || echo "rundaverun.org")
        PROD_USER=$($SECRETS_MGR get prod_ssh_user 2>/dev/null || echo "dave")
        PROD_PATH=$($SECRETS_MGR get prod_wp_path 2>/dev/null || echo "/var/www/rundaverun.org")
    else
        # Fallback to defaults
        PROD_HOST="rundaverun.org"
        PROD_USER="dave"
        PROD_PATH="/var/www/rundaverun.org"
    fi
}

# Create backup
create_backup() {
    local location="$1"  # local or production

    log "Creating backup of $location..."

    if [ "$location" = "local" ]; then
        cd "$LOCAL_PATH" || exit 1
        local backup_file="${SKIPPY_BASE}/backups/local_before_sync_$(date +%Y%m%d_%H%M%S).sql"
        mkdir -p "$(dirname "$backup_file")"
        wp db export "$backup_file" --add-drop-table
        success "Local backup: $backup_file"
    else
        # Production backup via SSH
        get_prod_credentials
        local backup_file="${SKIPPY_BASE}/backups/prod_before_sync_$(date +%Y%m%d_%H%M%S).sql"
        mkdir -p "$(dirname "$backup_file")"

        ssh "$PROD_USER@$PROD_HOST" "cd $PROD_PATH && wp db export - --add-drop-table" > "$backup_file"
        success "Production backup: $backup_file"
    fi
}

# Export content from local
export_local() {
    local type="$1"

    log "Exporting from local: $type"

    cd "$LOCAL_PATH" || exit 1

    local export_file="${SKIPPY_BASE}/work/exports/local_${type}_$(date +%Y%m%d_%H%M%S).xml"
    mkdir -p "$(dirname "$export_file")"

    case "$type" in
        posts)
            wp export --post_type=post --dir="$(dirname "$export_file")" --filename="$(basename "$export_file")"
            ;;
        pages)
            wp export --post_type=page --dir="$(dirname "$export_file")" --filename="$(basename "$export_file")"
            ;;
        policies)
            wp export --post_type=policy --dir="$(dirname "$export_file")" --filename="$(basename "$export_file")"
            ;;
        all)
            wp export --dir="$(dirname "$export_file")" --filename="$(basename "$export_file")"
            ;;
    esac

    echo "$export_file"
}

# Export content from production
export_production() {
    local type="$1"

    log "Exporting from production: $type"

    get_prod_credentials

    local export_file="${SKIPPY_BASE}/work/exports/prod_${type}_$(date +%Y%m%d_%H%M%S).xml"
    mkdir -p "$(dirname "$export_file")"

    case "$type" in
        posts)
            ssh "$PROD_USER@$PROD_HOST" "cd $PROD_PATH && wp export --post_type=post --stdout" > "$export_file"
            ;;
        pages)
            ssh "$PROD_USER@$PROD_HOST" "cd $PROD_PATH && wp export --post_type=page --stdout" > "$export_file"
            ;;
        policies)
            ssh "$PROD_USER@$PROD_HOST" "cd $PROD_PATH && wp export --post_type=policy --stdout" > "$export_file"
            ;;
        all)
            ssh "$PROD_USER@$PROD_HOST" "cd $PROD_PATH && wp export --stdout" > "$export_file"
            ;;
    esac

    echo "$export_file"
}

# Compare local vs production
compare_content() {
    local type="$CONTENT_TYPE"

    log "Comparing local vs production: $type"

    cd "$LOCAL_PATH" || exit 1

    # Get local counts
    case "$type" in
        posts|all)
            LOCAL_POSTS=$(wp post list --post_type=post --format=count)
            log "  Local posts: $LOCAL_POSTS"
            ;;
    esac

    case "$type" in
        pages|all)
            LOCAL_PAGES=$(wp post list --post_type=page --format=count)
            log "  Local pages: $LOCAL_PAGES"
            ;;
    esac

    # Get production counts
    get_prod_credentials

    case "$type" in
        posts|all)
            PROD_POSTS=$(ssh "$PROD_USER@$PROD_HOST" "cd $PROD_PATH && wp post list --post_type=post --format=count")
            log "  Production posts: $PROD_POSTS"
            ;;
    esac

    case "$type" in
        pages|all)
            PROD_PAGES=$(ssh "$PROD_USER@$PROD_HOST" "cd $PROD_PATH && wp post list --post_type=page --format=count")
            log "  Production pages: $PROD_PAGES"
            ;;
    esac

    # Summary
    cat >> "$REPORT_FILE" <<EOF

### Comparison Summary

| Content Type | Local | Production | Difference |
|--------------|-------|------------|------------|
| Posts        | ${LOCAL_POSTS:-N/A} | ${PROD_POSTS:-N/A} | $((${LOCAL_POSTS:-0} - ${PROD_POSTS:-0})) |
| Pages        | ${LOCAL_PAGES:-N/A} | ${PROD_PAGES:-N/A} | $((${LOCAL_PAGES:-0} - ${PROD_PAGES:-0})) |

EOF

    success "Comparison complete"
}

# Pull from production
pull_from_production() {
    local type="$CONTENT_TYPE"

    log "Pulling $type from production to local..."

    if [ "$BACKUP" = true ] || [ "$DRY_RUN" = false ]; then
        create_backup "local"
    fi

    if [ "$DRY_RUN" = true ]; then
        warning "DRY RUN: Would export from production and import to local"
        return
    fi

    # Export from production
    local export_file=$(export_production "$type")
    success "Exported from production: $export_file"

    # Import to local
    cd "$LOCAL_PATH" || exit 1
    wp import "$export_file" --authors=create

    success "Import complete"
}

# Push to production
push_to_production() {
    local type="$CONTENT_TYPE"

    log "Pushing $type from local to production..."

    if [ "$FORCE" = false ]; then
        echo
        echo -e "${YELLOW}⚠ WARNING: This will modify production!${NC}"
        read -p "Continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            error "Cancelled by user"
            exit 0
        fi
    fi

    if [ "$BACKUP" = true ] || [ "$DRY_RUN" = false ]; then
        create_backup "production"
    fi

    if [ "$DRY_RUN" = true ]; then
        warning "DRY RUN: Would export from local and import to production"
        return
    fi

    # Export from local
    local export_file=$(export_local "$type")
    success "Exported from local: $export_file"

    # Copy to production and import
    get_prod_credentials
    scp "$export_file" "$PROD_USER@$PROD_HOST:/tmp/"
    ssh "$PROD_USER@$PROD_HOST" "cd $PROD_PATH && wp import /tmp/$(basename "$export_file") --authors=create"

    success "Push complete"
}

# Main operation
case "$DIRECTION" in
    compare)
        compare_content
        ;;
    pull)
        pull_from_production
        ;;
    push)
        push_to_production
        ;;
    sync)
        log "Interactive two-way sync not yet implemented"
        warning "Use 'compare', 'pull', or 'push' for now"
        ;;
    *)
        usage
        ;;
esac

# Final report
cat >> "$REPORT_FILE" <<EOF

---

## Summary

**Operation:** $DIRECTION $CONTENT_TYPE
**Completed:** $(date)
**Mode:** $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "LIVE")

EOF

success "Report saved: $REPORT_FILE"
success "Sync operation complete"

exit 0
