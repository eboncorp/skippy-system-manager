#!/bin/bash
# Media Sync Verifier v1.0.0
# Verifies all media files referenced in WordPress content exist on production
#
# Purpose: Catch missing uploads, images, downloads before/after deployments
# Usage: media_sync_verifier_v1.0.0.sh [--fix] [--verbose]
#
# Options:
#   --fix      Automatically upload missing files to production
#   --verbose  Show detailed progress
#   --local-only  Only check local files exist (skip production)
#
# Created: 2026-01-13
# Part of: Skippy WordPress Deployment Tools

set -euo pipefail

#═══════════════════════════════════════════════════════════════
# CONFIGURATION
#═══════════════════════════════════════════════════════════════

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
LOCAL_WP="/home/dave/skippy/websites/rundaverun/local_site/rundaverun_local_site/app/public"
LOCAL_UPLOADS="$LOCAL_WP/wp-content/uploads"
PROD_HOST="git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com"
PROD_PATH="html/wp-content/uploads"
SSH_KEY="$HOME/.ssh/godaddy_rundaverun"
PROD_URL="https://rundaverun.org"

# Session
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_media_verification"
REPORT_FILE=""
MISSING_FILES=()
ORPHANED_REFS=()

# Options
FIX_MODE=false
VERBOSE=false
LOCAL_ONLY=false

#═══════════════════════════════════════════════════════════════
# FUNCTIONS
#═══════════════════════════════════════════════════════════════

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

verbose() {
    if $VERBOSE; then
        echo -e "  ${BLUE}→${NC} $1"
    fi
}

ssh_cmd() {
    SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
        -i "$SSH_KEY" "$PROD_HOST" "$1" 2>/dev/null
}

scp_upload() {
    local src="$1"
    local dest="$2"
    SSH_AUTH_SOCK="" scp -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
        -i "$SSH_KEY" "$src" "${PROD_HOST}:${dest}" 2>/dev/null
}

show_help() {
    cat << 'EOF'
Media Sync Verifier v1.0.0
==========================

Verifies WordPress media files are synced between local and production.

USAGE:
    media_sync_verifier_v1.0.0.sh [OPTIONS]

OPTIONS:
    --fix           Automatically upload missing files to production
    --verbose       Show detailed progress for each file
    --local-only    Only verify local files exist (skip production check)
    --help          Show this help message

CHECKS PERFORMED:
    1. Extract all media URLs from WordPress page/post content
    2. Verify each referenced file exists locally
    3. Verify each file exists on production (HTTP HEAD request)
    4. Compare local uploads directory with production
    5. Report orphaned references (URLs pointing to non-existent files)
    6. Report missing files (local exists but not on production)

EXAMPLES:
    # Full verification
    ./media_sync_verifier_v1.0.0.sh

    # Verify and fix missing files
    ./media_sync_verifier_v1.0.0.sh --fix

    # Verbose output
    ./media_sync_verifier_v1.0.0.sh --verbose

OUTPUT:
    Creates session directory with:
    - verification_report.md
    - missing_files.txt
    - orphaned_references.txt

EOF
    exit 0
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fix)
                FIX_MODE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --local-only)
                LOCAL_ONLY=true
                shift
                ;;
            --help|-h)
                show_help
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

setup_session() {
    mkdir -p "$SESSION_DIR"
    REPORT_FILE="$SESSION_DIR/verification_report.md"

    cat > "$REPORT_FILE" << EOF
# Media Sync Verification Report
**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Mode:** $(if $FIX_MODE; then echo "Fix"; else echo "Report Only"; fi)

---

EOF

    log "Session: $SESSION_DIR"
}

#═══════════════════════════════════════════════════════════════
# VERIFICATION FUNCTIONS
#═══════════════════════════════════════════════════════════════

extract_media_urls() {
    log "Extracting media URLs from WordPress content..."

    local urls_file="$SESSION_DIR/referenced_urls.txt"

    # Get all published posts and pages content
    cd "$LOCAL_WP"
    wp post list --post_type=page,post --post_status=publish --field=ID 2>/dev/null | while read -r post_id; do
        wp post get "$post_id" --field=post_content 2>/dev/null
    done | grep -oE '(src|href)="[^"]*wp-content/uploads[^"]*"' \
         | sed 's/.*"\([^"]*\)"/\1/' \
         | sort -u > "$urls_file"

    # Also check for data attributes and background images
    wp post list --post_type=page,post --post_status=publish --field=ID 2>/dev/null | while read -r post_id; do
        wp post get "$post_id" --field=post_content 2>/dev/null
    done | grep -oE 'url\([^)]*wp-content/uploads[^)]*\)' \
         | sed "s/url(['\"]\\?\\([^)'\"]*\\)['\"]\\?)/\\1/" \
         >> "$urls_file"

    sort -u "$urls_file" -o "$urls_file"

    local count=$(wc -l < "$urls_file")
    success "Found $count unique media references in content"

    echo "## Media References in Content" >> "$REPORT_FILE"
    echo "- **Total unique URLs:** $count" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

verify_local_files() {
    log "Verifying local files exist..."

    local urls_file="$SESSION_DIR/referenced_urls.txt"
    local missing_local=0

    while IFS= read -r url; do
        # Convert URL to local path
        local rel_path="${url#/}"
        local local_path="$LOCAL_WP/$rel_path"

        if [[ ! -f "$local_path" ]]; then
            ORPHANED_REFS+=("$url")
            ((missing_local++))
            verbose "Missing locally: $url"
        fi
    done < "$urls_file"

    if [[ $missing_local -eq 0 ]]; then
        success "All referenced files exist locally"
    else
        warn "$missing_local files referenced but missing locally (orphaned references)"
    fi

    echo "## Local File Verification" >> "$REPORT_FILE"
    echo "- **Orphaned references:** $missing_local" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

verify_production_files() {
    if $LOCAL_ONLY; then
        log "Skipping production verification (--local-only)"
        return
    fi

    log "Verifying files exist on production..."

    local urls_file="$SESSION_DIR/referenced_urls.txt"
    local missing_prod=0
    local checked=0
    local total=$(wc -l < "$urls_file")

    while IFS= read -r url; do
        ((checked++))

        # Build full URL
        local full_url="${PROD_URL}${url}"

        # HTTP HEAD request to check existence
        local status=$(curl -s -o /dev/null -w "%{http_code}" --head "$full_url" 2>/dev/null || echo "000")

        if [[ "$status" != "200" ]]; then
            MISSING_FILES+=("$url")
            ((missing_prod++))
            verbose "Missing on production ($status): $url"
        fi

        # Progress indicator every 50 files
        if [[ $((checked % 50)) -eq 0 ]]; then
            log "  Checked $checked/$total files..."
        fi
    done < "$urls_file"

    if [[ $missing_prod -eq 0 ]]; then
        success "All referenced files exist on production"
    else
        error "$missing_prod files missing on production"
    fi

    echo "## Production File Verification" >> "$REPORT_FILE"
    echo "- **Missing on production:** $missing_prod" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

compare_upload_directories() {
    if $LOCAL_ONLY; then
        return
    fi

    log "Comparing upload directories..."

    # Get local file list
    find "$LOCAL_UPLOADS" -type f -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \
        -o -name "*.gif" -o -name "*.webp" -o -name "*.pdf" -o -name "*.zip" \
        2>/dev/null | sed "s|$LOCAL_UPLOADS/||" | sort > "$SESSION_DIR/local_files.txt"

    # Get production file list
    ssh_cmd "cd $PROD_PATH && find . -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.gif' -o -name '*.webp' -o -name '*.pdf' -o -name '*.zip' \)" \
        | sed 's|^\./||' | sort > "$SESSION_DIR/prod_files.txt"

    # Compare
    comm -23 "$SESSION_DIR/local_files.txt" "$SESSION_DIR/prod_files.txt" > "$SESSION_DIR/missing_on_prod.txt"
    comm -13 "$SESSION_DIR/local_files.txt" "$SESSION_DIR/prod_files.txt" > "$SESSION_DIR/extra_on_prod.txt"

    local missing_count=$(wc -l < "$SESSION_DIR/missing_on_prod.txt")
    local extra_count=$(wc -l < "$SESSION_DIR/extra_on_prod.txt")
    local local_count=$(wc -l < "$SESSION_DIR/local_files.txt")
    local prod_count=$(wc -l < "$SESSION_DIR/prod_files.txt")

    echo "## Directory Comparison" >> "$REPORT_FILE"
    echo "- **Local files:** $local_count" >> "$REPORT_FILE"
    echo "- **Production files:** $prod_count" >> "$REPORT_FILE"
    echo "- **Missing on production:** $missing_count" >> "$REPORT_FILE"
    echo "- **Extra on production:** $extra_count" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    if [[ $missing_count -gt 0 ]]; then
        warn "$missing_count files exist locally but not on production"

        # Add to missing files array
        while IFS= read -r file; do
            MISSING_FILES+=("/wp-content/uploads/$file")
        done < "$SESSION_DIR/missing_on_prod.txt"
    else
        success "Upload directories are in sync"
    fi
}

fix_missing_files() {
    if ! $FIX_MODE; then
        return
    fi

    if [[ ${#MISSING_FILES[@]} -eq 0 ]]; then
        log "No missing files to fix"
        return
    fi

    log "Uploading ${#MISSING_FILES[@]} missing files to production..."

    local fixed=0
    local failed=0

    for url in "${MISSING_FILES[@]}"; do
        local rel_path="${url#/wp-content/uploads/}"
        local local_file="$LOCAL_UPLOADS/$rel_path"
        local remote_dir="$PROD_PATH/$(dirname "$rel_path")"

        if [[ -f "$local_file" ]]; then
            # Ensure remote directory exists
            ssh_cmd "mkdir -p $remote_dir"

            # Upload file
            if scp_upload "$local_file" "$PROD_PATH/$rel_path"; then
                ((fixed++))
                verbose "Uploaded: $rel_path"
            else
                ((failed++))
                error "Failed to upload: $rel_path"
            fi
        fi
    done

    success "Uploaded $fixed files to production"
    if [[ $failed -gt 0 ]]; then
        error "Failed to upload $failed files"
    fi

    echo "## Fix Results" >> "$REPORT_FILE"
    echo "- **Files uploaded:** $fixed" >> "$REPORT_FILE"
    echo "- **Upload failures:** $failed" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

generate_report() {
    log "Generating report..."

    # Save missing files list
    if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
        printf '%s\n' "${MISSING_FILES[@]}" > "$SESSION_DIR/missing_files.txt"

        echo "## Missing Files" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
        head -20 "$SESSION_DIR/missing_files.txt" >> "$REPORT_FILE"
        if [[ ${#MISSING_FILES[@]} -gt 20 ]]; then
            echo "... and $((${#MISSING_FILES[@]} - 20)) more" >> "$REPORT_FILE"
        fi
        echo '```' >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    fi

    # Save orphaned references
    if [[ ${#ORPHANED_REFS[@]} -gt 0 ]]; then
        printf '%s\n' "${ORPHANED_REFS[@]}" > "$SESSION_DIR/orphaned_references.txt"

        echo "## Orphaned References" >> "$REPORT_FILE"
        echo "These URLs are in page content but files don't exist:" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
        head -20 "$SESSION_DIR/orphaned_references.txt" >> "$REPORT_FILE"
        if [[ ${#ORPHANED_REFS[@]} -gt 20 ]]; then
            echo "... and $((${#ORPHANED_REFS[@]} - 20)) more" >> "$REPORT_FILE"
        fi
        echo '```' >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    fi

    # Summary
    echo "---" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    if [[ ${#MISSING_FILES[@]} -eq 0 && ${#ORPHANED_REFS[@]} -eq 0 ]]; then
        echo "## ✅ All Checks Passed" >> "$REPORT_FILE"
        echo "Media files are fully synced between local and production." >> "$REPORT_FILE"
    else
        echo "## ⚠️ Issues Found" >> "$REPORT_FILE"
        echo "- Missing files: ${#MISSING_FILES[@]}" >> "$REPORT_FILE"
        echo "- Orphaned references: ${#ORPHANED_REFS[@]}" >> "$REPORT_FILE"
        if ! $FIX_MODE; then
            echo "" >> "$REPORT_FILE"
            echo "Run with \`--fix\` to upload missing files." >> "$REPORT_FILE"
        fi
    fi

    echo "" >> "$REPORT_FILE"
    echo "---" >> "$REPORT_FILE"
    echo "*Report generated: $(date '+%Y-%m-%d %H:%M:%S')*" >> "$REPORT_FILE"
}

show_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  MEDIA SYNC VERIFICATION SUMMARY"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    if [[ ${#MISSING_FILES[@]} -eq 0 && ${#ORPHANED_REFS[@]} -eq 0 ]]; then
        echo -e "  ${GREEN}✓ ALL CHECKS PASSED${NC}"
        echo "  Media files are fully synced."
    else
        if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
            echo -e "  ${RED}✗ Missing on production: ${#MISSING_FILES[@]} files${NC}"
        fi
        if [[ ${#ORPHANED_REFS[@]} -gt 0 ]]; then
            echo -e "  ${YELLOW}⚠ Orphaned references: ${#ORPHANED_REFS[@]} URLs${NC}"
        fi
    fi

    echo ""
    echo "  Report: $REPORT_FILE"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
}

#═══════════════════════════════════════════════════════════════
# MAIN
#═══════════════════════════════════════════════════════════════

main() {
    parse_args "$@"

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  Media Sync Verifier v1.0.0"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    setup_session
    extract_media_urls
    verify_local_files
    verify_production_files
    compare_upload_directories
    fix_missing_files
    generate_report
    show_summary
}

main "$@"
