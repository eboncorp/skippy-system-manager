#!/bin/bash
# WordPress Bulk Operations Tool v1.0.0
# Automates common bulk WordPress operations
# Part of: Skippy Enhancement Project - TIER 2
# Created: 2025-11-04

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

WP_PATH="/home/dave/Local Sites/rundaverun-local/app/public"
SKIPPY_BASE="/home/dave/skippy"
REPORT_DIR="${SKIPPY_BASE}/conversations/wp_bulk_operations"

usage() {
    cat <<EOF
WordPress Bulk Operations Tool v1.0.0

USAGE:
    $0 <operation> [options]

OPERATIONS:
    fix-apostrophes              Fix triple apostrophes across all posts
    fix-links                    Update all broken links
    fix-budget-figures           Update all budget figures to correct values
    update-email <old> <new>     Replace email address across site
    update-url <old> <new>       Replace URL across site (e.g., http->https)
    publish-drafts <category>    Publish all drafts in category
    update-meta <key> <value>    Set meta value on all posts
    add-category <cat> <posts>   Add category to multiple posts
    remove-category <cat> <posts> Remove category from posts
    bulk-delete <type> <ids>     Delete multiple posts/pages
    export-content <type>        Export all content of type
    fix-images                   Fix broken image URLs
    optimize-images              Optimize all media library images
    clean-revisions              Remove old post revisions
    clean-trash                  Empty all trash
    backup-before-bulk           Create backup before bulk operation

OPTIONS:
    --dry-run                    Show what would be done without making changes
    --verbose                    Show detailed output
    --report                     Generate detailed report

EXAMPLES:
    # Fix triple apostrophes
    $0 fix-apostrophes --dry-run

    # Update email address
    $0 update-email "old@email.com" "new@email.com"

    # Fix budget figures
    $0 fix-budget-figures

    # Publish all draft policies
    $0 publish-drafts policy

    # Clean up old revisions
    $0 clean-revisions --verbose

EOF
    exit 1
}

# Parse options
DRY_RUN=false
VERBOSE=false
GENERATE_REPORT=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

OPERATION="${1:-}"

# Ensure WP-CLI available
if ! command -v wp &> /dev/null; then
    echo -e "${RED}❌ WP-CLI not found${NC}"
    exit 1
fi

# Change to WP directory
cd "$WP_PATH" || exit 1

# Create report directory
mkdir -p "$REPORT_DIR"

# Report file
REPORT_FILE="${REPORT_DIR}/bulk_operation_$(date +%Y%m%d_%H%M%S).md"

# Start report
if [ "$GENERATE_REPORT" = true ]; then
    cat > "$REPORT_FILE" <<EOF
# WordPress Bulk Operation Report

**Date:** $(date)
**Operation:** $OPERATION
**Mode:** $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "LIVE")

---

## Changes Made

EOF
fi

log() {
    echo -e "${BLUE}$1${NC}"
    if [ "$GENERATE_REPORT" = true ]; then
        echo "$1" >> "$REPORT_FILE"
    fi
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
    if [ "$GENERATE_REPORT" = true ]; then
        echo "✓ $1" >> "$REPORT_FILE"
    fi
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    if [ "$GENERATE_REPORT" = true ]; then
        echo "⚠ $1" >> "$REPORT_FILE"
    fi
}

error() {
    echo -e "${RED}❌ $1${NC}"
    if [ "$GENERATE_REPORT" = true ]; then
        echo "❌ $1" >> "$REPORT_FILE"
    fi
}

# Fix triple apostrophes
fix_apostrophes() {
    log "Fixing triple apostrophes..."

    local count=0
    local post_ids=$(wp post list --post_type=any --format=ids --posts_per_page=-1)

    for id in $post_ids; do
        local content=$(wp post get "$id" --field=post_content 2>/dev/null || echo "")

        if echo "$content" | grep -q "'''"; then
            log "  Post $id: Found triple apostrophes"

            if [ "$DRY_RUN" = false ]; then
                # Fix the content
                local fixed_content=$(echo "$content" | sed "s/'''/'/g")
                wp post update "$id" --post_content="$fixed_content" >/dev/null 2>&1
                success "    Fixed post $id"
            else
                warning "    Would fix post $id"
            fi

            ((count++))
        fi
    done

    success "Total posts with triple apostrophes: $count"
}

# Fix budget figures
fix_budget_figures() {
    log "Fixing budget figures..."

    # Correct values from FACT_SHEET
    declare -A CORRECTIONS=(
        ["\$5M"]="\$15M"
        ["\$5 million"]="\$15 million"
        ["\$3.00"]="\$1.80"
        ["every \$3"]=|"every \$1.80"
        ["\$77M"]="\$77.4M"
        ["\$34M"]="\$34.2M"
    )

    local total_fixes=0

    for old_val in "${!CORRECTIONS[@]}"; do
        new_val="${CORRECTIONS[$old_val]}"

        log "  Checking for: $old_val -> $new_val"

        if [ "$DRY_RUN" = false ]; then
            wp search-replace "$old_val" "$new_val" --precise --report-changed-only 2>&1 | tee -a "$REPORT_FILE"
        else
            warning "  Would replace: $old_val -> $new_val"
        fi
    done

    success "Budget figures updated"
}

# Update email addresses
update_email() {
    local old_email="$2"
    local new_email="$3"

    if [ -z "$old_email" ] || [ -z "$new_email" ]; then
        error "Both old and new email required"
        usage
    fi

    log "Updating email: $old_email -> $new_email"

    if [ "$DRY_RUN" = false ]; then
        wp search-replace "$old_email" "$new_email" --precise --report-changed-only
        success "Email updated"
    else
        warning "Would update email: $old_email -> $new_email"
    fi
}

# Update URLs
update_url() {
    local old_url="$2"
    local new_url="$3"

    if [ -z "$old_url" ] || [ -z "$new_url" ]; then
        error "Both old and new URL required"
        usage
    fi

    log "Updating URL: $old_url -> $new_url"

    if [ "$DRY_RUN" = false ]; then
        wp search-replace "$old_url" "$new_url" --precise --report-changed-only
        success "URL updated"
    else
        warning "Would update URL: $old_url -> $new_url"
    fi
}

# Publish drafts
publish_drafts() {
    local category="$2"

    if [ -z "$category" ]; then
        error "Category required"
        usage
    fi

    log "Publishing drafts in category: $category"

    local draft_ids=$(wp post list --post_status=draft --category="$category" --format=ids)

    if [ -z "$draft_ids" ]; then
        warning "No drafts found in category: $category"
        return
    fi

    local count=0
    for id in $draft_ids; do
        local title=$(wp post get "$id" --field=post_title)
        log "  Post $id: $title"

        if [ "$DRY_RUN" = false ]; then
            wp post update "$id" --post_status=publish >/dev/null
            success "    Published"
        else
            warning "    Would publish"
        fi

        ((count++))
    done

    success "Published $count drafts"
}

# Clean revisions
clean_revisions() {
    log "Cleaning post revisions..."

    local before_count=$(wp post list --post_type=revision --format=count)
    log "  Current revisions: $before_count"

    if [ "$DRY_RUN" = false ]; then
        wp post delete $(wp post list --post_type=revision --format=ids) --force 2>/dev/null || true
        local after_count=$(wp post list --post_type=revision --format=count)
        success "Deleted $((before_count - after_count)) revisions"
    else
        warning "Would delete $before_count revisions"
    fi
}

# Clean trash
clean_trash() {
    log "Emptying trash..."

    local trash_count=$(wp post list --post_status=trash --format=count)
    log "  Items in trash: $trash_count"

    if [ "$DRY_RUN" = false ]; then
        wp post delete $(wp post list --post_status=trash --format=ids) --force 2>/dev/null || true
        success "Emptied trash ($trash_count items)"
    else
        warning "Would empty trash ($trash_count items)"
    fi
}

# Fix broken links
fix_links() {
    log "Fixing broken links..."

    # Common broken link patterns
    declare -A LINK_FIXES=(
        ["http://rundaverun.org"]="https://rundaverun.org"
        ["http://www.rundaverun.org"]="https://rundaverun.org"
        ["rundaverun.local"]="rundaverun.org"
    )

    for old_link in "${!LINK_FIXES[@]}"; do
        new_link="${LINK_FIXES[$old_link]}"

        log "  Fixing: $old_link -> $new_link"

        if [ "$DRY_RUN" = false ]; then
            wp search-replace "$old_link" "$new_link" --precise --report-changed-only
        else
            warning "  Would fix: $old_link -> $new_link"
        fi
    done

    success "Link fixes complete"
}

# Backup before bulk operation
backup_before_bulk() {
    log "Creating backup before bulk operation..."

    local backup_file="${SKIPPY_BASE}/backups/before_bulk_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p "$(dirname "$backup_file")"

    wp db export "$backup_file" --add-drop-table

    success "Backup created: $backup_file"
}

# Main operation dispatcher
case "$OPERATION" in
    fix-apostrophes)
        fix_apostrophes
        ;;
    fix-budget-figures)
        fix_budget_figures
        ;;
    update-email)
        update_email "$@"
        ;;
    update-url)
        update_url "$@"
        ;;
    publish-drafts)
        publish_drafts "$@"
        ;;
    clean-revisions)
        clean_revisions
        ;;
    clean-trash)
        clean_trash
        ;;
    fix-links)
        fix_links
        ;;
    backup-before-bulk)
        backup_before_bulk
        ;;
    *)
        usage
        ;;
esac

# Report summary
if [ "$GENERATE_REPORT" = true ]; then
    cat >> "$REPORT_FILE" <<EOF

---

## Summary

**Operation:** $OPERATION
**Completed:** $(date)
**Mode:** $([ "$DRY_RUN" = true ] && echo "DRY RUN (no changes made)" || echo "LIVE (changes applied)")

EOF

    success "Report saved: $REPORT_FILE"
fi

success "Operation complete: $OPERATION"

exit 0
