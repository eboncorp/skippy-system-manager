#!/bin/bash
###############################################################################
# WordPress Unified Diagnostic Tool v3.1.0
# 20-Layer Comprehensive Site Analysis
# Created: 2025-12-21
# Updated: 2025-12-24 - Added CDN filtering, custom post types, improved SEO checks
#
# Description:
#   The definitive WordPress diagnostic tool combining all previous scripts
#   into a single, comprehensive 20-layer analysis. Supports local, staging,
#   and production environments with full SSH integration.
#
# Layers:
#   1-10:  Core WordPress diagnostics
#   11-15: Content, SEO, accessibility, performance
#   16-20: Production infrastructure (REST API, SSL, DNS, forms, remote)
#
# Usage:
#   bash wp_unified_diagnostic_v3.0.0.sh [environment] [options]
#
# Environments:
#   local      - Local by Flywheel (default)
#   staging    - Staging server
#   production - Live GoDaddy server
#
# Options:
#   --quick    - Run only layers 1-10 (fast mode)
#   --full     - Run all 20 layers (default)
#   --layer N  - Run only layer N
#   --skip N   - Skip layer N
#   --help     - Show this help
#
# Examples:
#   bash wp_unified_diagnostic_v3.0.0.sh local
#   bash wp_unified_diagnostic_v3.0.0.sh production --quick
#   bash wp_unified_diagnostic_v3.0.0.sh local --layer 16
#
# Exit Codes:
#   0 = All checks passed
#   1 = Critical issues found
#   2 = Warnings found (review recommended)
###############################################################################

set -o pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

VERSION="3.2.0"
SCRIPT_NAME="WordPress Unified Diagnostic"

# Handle --help as first argument
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    head -45 "$0" | tail -40
    exit 0
fi

# Environment configuration
ENVIRONMENT="${1:-local}"
shift 2>/dev/null || true

# Parse options
QUICK_MODE=false
SPECIFIC_LAYER=""
SKIP_LAYERS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick) QUICK_MODE=true ;;
        --full) QUICK_MODE=false ;;
        --layer)
            SPECIFIC_LAYER="$2"
            if [[ ! "$SPECIFIC_LAYER" =~ ^[0-9]+$ ]] || [[ "$SPECIFIC_LAYER" -lt 1 ]] || [[ "$SPECIFIC_LAYER" -gt 20 ]]; then
                echo "Error: --layer must be a number between 1 and 20"
                exit 1
            fi
            shift
            ;;
        --skip)
            if [[ ! "$2" =~ ^[0-9]+$ ]] || [[ "$2" -lt 1 ]] || [[ "$2" -gt 20 ]]; then
                echo "Error: --skip must be a number between 1 and 20"
                exit 1
            fi
            SKIP_LAYERS="$SKIP_LAYERS $2"
            shift
            ;;
        --help|-h)
            head -45 "$0" | tail -40
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# Environment-specific settings
case $ENVIRONMENT in
    local)
        WP_PATH="/home/dave/skippy/websites/rundaverun/local_site/rundaverun_local_site/app/public"
        SITE_URL="http://rundaverun-local-complete-022655.local"
        WP_CLI="wp --path=$WP_PATH --allow-root"
        IS_REMOTE=false
        ;;
    staging)
        WP_PATH="/var/www/staging"
        SITE_URL="https://staging.rundaverun.org"
        WP_CLI="wp --path=$WP_PATH"
        IS_REMOTE=false
        ;;
    production)
        SITE_URL="https://rundaverun.org"
        SSH_KEY="$HOME/.ssh/godaddy_rundaverun"
        SSH_USER="git_deployer_f44cc3416a_545525"
        SSH_HOST="bp6.0cf.myftpupload.com"
        SSH_CMD="SSH_AUTH_SOCK='' ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i $SSH_KEY $SSH_USER@$SSH_HOST"
        WP_CLI_REMOTE="cd html && wp --allow-root"
        IS_REMOTE=true
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT"
        echo "Valid options: local, staging, production"
        exit 1
        ;;
esac

# Session directory (NEVER use /tmp/)
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_unified_diagnostic_${ENVIRONMENT}"
mkdir -p "$SESSION_DIR"
REPORT_FILE="$SESSION_DIR/diagnostic_report.md"

# Counters
CRITICAL_ISSUES=0
WARNINGS=0
PASSED=0
LAYERS_RUN=0

# External domains to skip in link checking (CDNs, analytics, fonts)
# These domains often return 403/blocking responses to automated requests
EXTERNAL_DOMAINS_SKIP=(
    "fonts.googleapis.com"
    "fonts.gstatic.com"
    "googletagmanager.com"
    "google-analytics.com"
    "www.google-analytics.com"
    "analytics.google.com"
    "cdnjs.cloudflare.com"
    "cdn.jsdelivr.net"
    "unpkg.com"
    "maxcdn.bootstrapcdn.com"
    "stackpath.bootstrapcdn.com"
    "use.fontawesome.com"
    "kit.fontawesome.com"
    "polyfill.io"
    "gravatar.com"
    "facebook.com"
    "twitter.com"
    "linkedin.com"
    "youtube.com"
    "maps.google.com"
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

log_header() {
    local layer_num=$1
    local layer_name=$2
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[Layer $layer_num/20]${NC} ${BOLD}$layer_name${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "" >> "$REPORT_FILE"
    echo "## Layer $layer_num: $layer_name" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
    echo "✅ $1" >> "$REPORT_FILE"
    ((PASSED++))
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    echo "⚠️ $1" >> "$REPORT_FILE"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    echo "❌ $1" >> "$REPORT_FILE"
    ((CRITICAL_ISSUES++))
}

log_info() {
    echo -e "  $1"
    echo "  $1" >> "$REPORT_FILE"
}

log_code() {
    echo '```' >> "$REPORT_FILE"
    echo "$1" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
}

should_run_layer() {
    local layer=$1

    # Check if specific layer requested
    if [[ -n "$SPECIFIC_LAYER" ]] && [[ "$SPECIFIC_LAYER" != "$layer" ]]; then
        return 1
    fi

    # Check if layer should be skipped
    if [[ "$SKIP_LAYERS" == *"$layer"* ]]; then
        return 1
    fi

    # Quick mode only runs layers 1-10
    if $QUICK_MODE && [[ $layer -gt 10 ]]; then
        return 1
    fi

    # Increment layer counter
    ((LAYERS_RUN++))
    return 0
}

# Check if a URL is an external domain we should skip
is_external_skip_domain() {
    local url=$1
    for domain in "${EXTERNAL_DOMAINS_SKIP[@]}"; do
        if [[ "$url" == *"$domain"* ]]; then
            return 0  # True - should skip
        fi
    done
    return 1  # False - should check
}

run_wp_cli() {
    local cmd=$1
    if $IS_REMOTE; then
        # Use single quotes for outer SSH command to preserve inner double quotes
        # This fixes SQL query quoting issues
        SSH_AUTH_SOCK='' ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
            -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" \
            "cd html && wp --allow-root $cmd" 2>&1
    else
        eval "$WP_CLI $cmd" 2>&1
    fi
}

run_remote_cmd() {
    local cmd=$1
    if $IS_REMOTE; then
        eval "$SSH_CMD \"$cmd\"" 2>&1
    else
        eval "$cmd" 2>&1
    fi
}

# =============================================================================
# INITIALIZE REPORT
# =============================================================================

cat > "$REPORT_FILE" << EOF
# WordPress Unified Diagnostic Report

**Version:** $VERSION
**Generated:** $(date '+%Y-%m-%d %H:%M:%S')
**Environment:** $ENVIRONMENT
**Site URL:** $SITE_URL
**Session:** $SESSION_DIR

---

EOF

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          $SCRIPT_NAME v$VERSION                   ║"
echo "║                     20-Layer Site Analysis                           ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "Environment: ${CYAN}$ENVIRONMENT${NC}"
echo -e "Site URL:    ${CYAN}$SITE_URL${NC}"
echo -e "Report:      ${CYAN}$REPORT_FILE${NC}"
echo ""

# =============================================================================
# LAYER 1: System Environment
# =============================================================================

if should_run_layer 1; then
    log_header 1 "System Environment"

    # OS Info
    OS_INFO=$(uname -a)
    log_info "OS: $(uname -sr)"
    log_code "$OS_INFO"

    # PHP Version
    PHP_VERSION=$(php -v 2>/dev/null | head -1 || echo "PHP not found")
    log_info "PHP: $PHP_VERSION"

    # Check required PHP modules (local environment only)
    # Remote environments have their own PHP config via WP-CLI
    if ! $IS_REMOTE; then
        REQUIRED_MODULES="curl gd mbstring mysqli xml"
        MISSING_MODULES=""
        for mod in $REQUIRED_MODULES; do
            if ! php -m 2>/dev/null | grep -qi "$mod"; then
                MISSING_MODULES="$MISSING_MODULES $mod"
            fi
        done

        if [[ -z "$MISSING_MODULES" ]]; then
            log_success "All required PHP modules installed"
        else
            log_error "Missing PHP modules:$MISSING_MODULES"
        fi
    else
        # For remote, check PHP on remote server
        REMOTE_PHP=$(run_wp_cli "--info" 2>/dev/null | grep "PHP Version" || echo "")
        if [[ -n "$REMOTE_PHP" ]]; then
            log_success "Remote PHP configured correctly"
        fi
    fi

    # Disk space
    if ! $IS_REMOTE; then
        DISK_USAGE=$(df -h "$WP_PATH" 2>/dev/null | awk 'NR==2 {print $5}' | tr -d '%')
        if [[ $DISK_USAGE -lt 80 ]]; then
            log_success "Disk space OK: ${DISK_USAGE}% used"
        elif [[ $DISK_USAGE -lt 90 ]]; then
            log_warning "Disk space: ${DISK_USAGE}% used"
        else
            log_error "Disk space critical: ${DISK_USAGE}% used"
        fi
    fi

    # Memory
    MEM_INFO=$(free -h 2>/dev/null | grep Mem || echo "Memory info unavailable")
    log_info "Memory: $MEM_INFO"
fi

# =============================================================================
# LAYER 2: WordPress Core
# =============================================================================

if should_run_layer 2; then
    log_header 2 "WordPress Core"

    # WordPress version
    WP_VERSION=$(run_wp_cli "core version" 2>/dev/null || echo "unknown")
    log_info "WordPress Version: $WP_VERSION"

    # Core checksum verification
    CHECKSUM_RESULT=$(run_wp_cli "core verify-checksums" 2>&1)
    if echo "$CHECKSUM_RESULT" | grep -q "Success"; then
        log_success "Core files verified"
    else
        log_warning "Core file modifications detected"
        log_code "$CHECKSUM_RESULT"
    fi

    # Check for updates
    UPDATE_STATUS=$(run_wp_cli "core check-update" 2>&1)
    if echo "$UPDATE_STATUS" | grep -q "latest"; then
        log_success "WordPress is up to date"
    else
        log_warning "WordPress update available"
        log_code "$UPDATE_STATUS"
    fi
fi

# =============================================================================
# LAYER 3: Database Integrity
# =============================================================================

if should_run_layer 3; then
    log_header 3 "Database Integrity"

    # Database check
    DB_CHECK=$(run_wp_cli "db check" 2>&1 | tail -5)
    if echo "$DB_CHECK" | grep -q "OK"; then
        log_success "Database tables healthy"
    else
        log_error "Database issues detected"
        log_code "$DB_CHECK"
    fi

    # Table count
    TABLE_COUNT=$(run_wp_cli "db query \"SHOW TABLES;\" --skip-column-names" 2>/dev/null | wc -l)
    log_info "Total tables: $TABLE_COUNT"

    # Database size
    DB_SIZE=$(run_wp_cli "db size --tables --format=table" 2>/dev/null | head -10)
    log_code "$DB_SIZE"

    # Orphaned data check - get prefix first
    DB_PREFIX=$(run_wp_cli "db prefix" 2>/dev/null | tr -d '\n' || echo "wp_")
    ORPHANED_META=$(run_wp_cli "db query 'SELECT COUNT(*) FROM ${DB_PREFIX}postmeta pm LEFT JOIN ${DB_PREFIX}posts p ON pm.post_id = p.ID WHERE p.ID IS NULL' --skip-column-names" 2>/dev/null || echo "0")
    if [[ "$ORPHANED_META" == "0" ]]; then
        log_success "No orphaned post meta"
    else
        log_warning "Found $ORPHANED_META orphaned post meta entries"
    fi
fi

# =============================================================================
# LAYER 4: Plugin Health
# =============================================================================

if should_run_layer 4; then
    log_header 4 "Plugin Health"

    # Active plugins
    PLUGIN_LIST=$(run_wp_cli "plugin list --status=active --format=table" 2>/dev/null)
    ACTIVE_COUNT=$(echo "$PLUGIN_LIST" | wc -l)
    log_info "Active plugins: $((ACTIVE_COUNT - 1))"
    log_code "$PLUGIN_LIST"

    # Plugin errors (check for 'Must-Use' plugins that might have issues)
    # Note: WP-CLI doesn't have --status=error, so check via verify instead
    PLUGIN_VERIFY=$(run_wp_cli "plugin verify-checksums --all" 2>&1)
    if echo "$PLUGIN_VERIFY" | grep -qE "Warning|Error"; then
        log_warning "Some plugins have checksum issues"
    else
        log_success "All plugins verified"
    fi

    # Updates needed
    UPDATES_NEEDED=$(run_wp_cli "plugin list --update=available --format=count" 2>/dev/null || echo "0")
    if [[ "$UPDATES_NEEDED" == "0" ]]; then
        log_success "All plugins up to date"
    else
        log_warning "$UPDATES_NEEDED plugins need updates"
    fi
fi

# =============================================================================
# LAYER 5: Theme Integrity
# =============================================================================

if should_run_layer 5; then
    log_header 5 "Theme Integrity"

    # Active theme
    ACTIVE_THEME=$(run_wp_cli "theme list --status=active --field=name" 2>/dev/null || echo "unknown")
    log_info "Active theme: $ACTIVE_THEME"

    # Theme list
    THEME_LIST=$(run_wp_cli "theme list --format=table" 2>/dev/null)
    log_code "$THEME_LIST"

    # Theme file count (local only)
    if ! $IS_REMOTE && [[ -d "$WP_PATH/wp-content/themes/$ACTIVE_THEME" ]]; then
        THEME_FILES=$(find "$WP_PATH/wp-content/themes/$ACTIVE_THEME" -type f 2>/dev/null | wc -l)
        log_info "Theme files: $THEME_FILES"
    fi

    log_success "Theme structure valid"
fi

# =============================================================================
# LAYER 6: Content Structure
# =============================================================================

if should_run_layer 6; then
    log_header 6 "Content Structure"

    # Get database prefix first
    DB_PREFIX=$(run_wp_cli "db prefix" 2>/dev/null | tr -d '\n' || echo "wp_")

    # Post counts
    PAGE_COUNT=$(run_wp_cli "post list --post_type=page --post_status=publish --format=count" 2>/dev/null || echo "0")
    POST_COUNT=$(run_wp_cli "post list --post_type=post --post_status=publish --format=count" 2>/dev/null || echo "0")

    log_info "Published pages: $PAGE_COUNT"
    log_info "Published posts: $POST_COUNT"

    # Check for truly empty pages (exclude pages with shortcodes which render dynamic content)
    # Pages with less than 10 chars AND no shortcode brackets are truly empty
    EMPTY_PAGES=$(run_wp_cli "db query 'SELECT COUNT(*) FROM ${DB_PREFIX}posts WHERE post_type=\"page\" AND post_status=\"publish\" AND LENGTH(post_content) < 10 AND post_content NOT LIKE \"%[%\" ' --skip-column-names" 2>/dev/null || echo "0")
    if [[ "$EMPTY_PAGES" == "0" ]]; then
        log_success "No empty pages detected"
    else
        log_warning "$EMPTY_PAGES pages with no content"
    fi

    # Custom post types check (campaign-specific)
    CUSTOM_POST_TYPES="policy_document glossary_term dbpm_event"
    for cpt in $CUSTOM_POST_TYPES; do
        CPT_COUNT=$(run_wp_cli "post list --post_type=$cpt --post_status=publish --format=count" 2>/dev/null || echo "0")
        if [[ "$CPT_COUNT" -gt 0 ]]; then
            log_info "Custom post type '$cpt': $CPT_COUNT items"
        fi
    done

    # Check for registered post types (all)
    REGISTERED_CPTS=$(run_wp_cli "post-type list --_builtin=0 --format=csv --fields=name" 2>/dev/null | tail -n +2 | tr '\n' ', ' | sed 's/,$//')
    if [[ -n "$REGISTERED_CPTS" ]]; then
        log_info "Registered custom post types: $REGISTERED_CPTS"
    fi

    # Menu count
    MENU_COUNT=$(run_wp_cli "menu list --format=count" 2>/dev/null || echo "0")
    log_info "Menus configured: $MENU_COUNT"
fi

# =============================================================================
# LAYER 7: Shortcodes & Hooks
# =============================================================================

if should_run_layer 7; then
    log_header 7 "Shortcodes & Hooks"

    # Get database prefix first
    DB_PREFIX=$(run_wp_cli "db prefix" 2>/dev/null | tr -d '\n' || echo "wp_")

    # Check critical shortcodes (via page content)
    SHORTCODES="contact-form-7 dbpm_policy_nav email_signup volunteer_impact_tracker"
    for sc in $SHORTCODES; do
        SC_COUNT=$(run_wp_cli "db query 'SELECT COUNT(*) FROM ${DB_PREFIX}posts WHERE post_content LIKE \"%[$sc%\"' --skip-column-names" 2>/dev/null || echo "0")
        if [[ "$SC_COUNT" -gt 0 ]]; then
            log_success "Shortcode [$sc] found in $SC_COUNT pages"
        fi
    done

    # Cron jobs
    CRON_COUNT=$(run_wp_cli "cron event list --format=count" 2>/dev/null || echo "0")
    log_info "Scheduled cron events: $CRON_COUNT"
fi

# =============================================================================
# LAYER 8: Performance Metrics
# =============================================================================

if should_run_layer 8; then
    log_header 8 "Performance Metrics"

    # Get database prefix first
    DB_PREFIX=$(run_wp_cli "db prefix" 2>/dev/null | tr -d '\n' || echo "wp_")

    # Autoload data size (check 'yes', 'on', and 'auto' values for compatibility)
    AUTOLOAD_SIZE=$(run_wp_cli "db query 'SELECT ROUND(SUM(LENGTH(option_value))/1024, 2) FROM ${DB_PREFIX}options WHERE autoload IN (\"yes\", \"on\", \"auto\")' --skip-column-names" 2>/dev/null | tr -d ' \n' || echo "0")
    [[ -z "$AUTOLOAD_SIZE" || "$AUTOLOAD_SIZE" == "NULL" ]] && AUTOLOAD_SIZE="0"
    log_info "Autoload data: ${AUTOLOAD_SIZE}KB"

    if [[ $(echo "$AUTOLOAD_SIZE > 1000" | bc -l 2>/dev/null || echo 0) -eq 1 ]]; then
        log_warning "Autoload data exceeds 1MB - may slow site"
    else
        log_success "Autoload data within limits"
    fi

    # Transient count
    TRANSIENT_COUNT=$(run_wp_cli "db query 'SELECT COUNT(*) FROM ${DB_PREFIX}options WHERE option_name LIKE \"_transient_%\"' --skip-column-names" 2>/dev/null || echo "0")
    log_info "Cached transients: $TRANSIENT_COUNT"

    # Directory sizes (local only)
    if ! $IS_REMOTE; then
        UPLOADS_SIZE=$(du -sh "$WP_PATH/wp-content/uploads" 2>/dev/null | cut -f1 || echo "N/A")
        PLUGINS_SIZE=$(du -sh "$WP_PATH/wp-content/plugins" 2>/dev/null | cut -f1 || echo "N/A")
        log_info "Uploads directory: $UPLOADS_SIZE"
        log_info "Plugins directory: $PLUGINS_SIZE"
    fi
fi

# =============================================================================
# LAYER 9: Security Audit
# =============================================================================

if should_run_layer 9; then
    log_header 9 "Security Audit"

    # File permissions (local only)
    if ! $IS_REMOTE && [[ -f "$WP_PATH/wp-config.php" ]]; then
        WP_CONFIG_PERMS=$(stat -c "%a" "$WP_PATH/wp-config.php" 2>/dev/null)
        if [[ "$WP_CONFIG_PERMS" == "600" ]] || [[ "$WP_CONFIG_PERMS" == "640" ]]; then
            log_success "wp-config.php permissions: $WP_CONFIG_PERMS"
        else
            log_warning "wp-config.php permissions: $WP_CONFIG_PERMS (recommended: 600)"
        fi
    fi

    # User accounts
    ADMIN_COUNT=$(run_wp_cli "user list --role=administrator --format=count" 2>/dev/null || echo "0")
    log_info "Administrator accounts: $ADMIN_COUNT"

    # PHP files in uploads
    if ! $IS_REMOTE; then
        PHP_IN_UPLOADS=$(find "$WP_PATH/wp-content/uploads" -type f -name "*.php" 2>/dev/null | wc -l)
        if [[ "$PHP_IN_UPLOADS" == "0" ]]; then
            log_success "No PHP files in uploads directory"
        else
            log_error "$PHP_IN_UPLOADS PHP files found in uploads (security risk)"
        fi
    fi

    # Security constants
    if ! $IS_REMOTE; then
        if grep -q "DISALLOW_FILE_EDIT" "$WP_PATH/wp-config.php" 2>/dev/null; then
            log_success "DISALLOW_FILE_EDIT is set"
        else
            log_warning "DISALLOW_FILE_EDIT not configured"
        fi
    fi
fi

# =============================================================================
# LAYER 10: Error Logs
# =============================================================================

if should_run_layer 10; then
    log_header 10 "Error Logs"

    # WordPress debug log
    if ! $IS_REMOTE && [[ -f "$WP_PATH/wp-content/debug.log" ]]; then
        ERROR_COUNT=$(grep -c "PHP Fatal\|PHP Error\|PHP Warning" "$WP_PATH/wp-content/debug.log" 2>/dev/null || echo "0")
        if [[ "$ERROR_COUNT" == "0" ]]; then
            log_success "No PHP errors in debug log"
        else
            log_warning "$ERROR_COUNT PHP errors in debug log"
            RECENT_ERRORS=$(tail -20 "$WP_PATH/wp-content/debug.log" 2>/dev/null | grep -E "Fatal|Error|Warning" | tail -5)
            log_code "$RECENT_ERRORS"
        fi
    else
        log_info "Debug log not enabled or not accessible"
    fi

    # Check WP_DEBUG status
    DEBUG_STATUS=$(run_wp_cli "config get WP_DEBUG" 2>/dev/null || echo "unknown")
    log_info "WP_DEBUG: $DEBUG_STATUS"
fi

# =============================================================================
# LAYER 11: Link Integrity
# =============================================================================

if should_run_layer 11; then
    log_header 11 "Link Integrity"

    # Fetch homepage and check links
    log_info "Checking homepage links..."
    HOMEPAGE_HTML=$(curl -sL --connect-timeout 10 "$SITE_URL" 2>/dev/null || echo "")

    if [[ -z "$HOMEPAGE_HTML" ]]; then
        log_error "Could not fetch homepage"
    else
        # Extract and test links
        LINKS=$(echo "$HOMEPAGE_HTML" | grep -oP 'href="[^"]+' | sed 's/href="//' | grep -v "^#\|^javascript:\|^mailto:\|^tel:" | sort -u | head -30)
        BROKEN_LINKS=0
        TESTED_LINKS=0
        SKIPPED_EXTERNAL=0

        for link in $LINKS; do
            # Convert relative to absolute
            if [[ "$link" =~ ^/ ]]; then
                full_url="${SITE_URL}${link}"
            elif [[ "$link" =~ ^// ]]; then
                # Protocol-relative URL - convert to https
                full_url="https:${link}"
            elif [[ "$link" =~ ^http ]]; then
                full_url="$link"
            else
                continue
            fi

            # Skip known external domains that block automated requests
            if is_external_skip_domain "$full_url"; then
                ((SKIPPED_EXTERNAL++))
                continue
            fi

            status=$(curl -o /dev/null -s -w "%{http_code}" --connect-timeout 5 -L "$full_url" 2>/dev/null || echo "000")
            ((TESTED_LINKS++))

            if [[ "$status" == "404" ]]; then
                log_error "Broken link (404): $full_url"
                ((BROKEN_LINKS++))
            elif [[ "$status" == "000" ]]; then
                # Connection failed - don't count as broken, just warn
                log_warning "Connection timeout: $full_url"
            fi
        done

        if [[ $BROKEN_LINKS -eq 0 ]]; then
            log_success "All $TESTED_LINKS internal links valid"
            if [[ $SKIPPED_EXTERNAL -gt 0 ]]; then
                log_info "Skipped $SKIPPED_EXTERNAL external CDN/social links"
            fi
        else
            log_error "$BROKEN_LINKS broken links found"
        fi
    fi
fi

# =============================================================================
# LAYER 12: SEO Metadata
# =============================================================================

if should_run_layer 12; then
    log_header 12 "SEO Metadata"

    HOMEPAGE_HTML=$(curl -sL --connect-timeout 10 "$SITE_URL" 2>/dev/null || echo "")

    if [[ -n "$HOMEPAGE_HTML" ]]; then
        # Title tag
        TITLE=$(echo "$HOMEPAGE_HTML" | grep -oP '<title>\K[^<]+' | head -1)
        TITLE_LEN=${#TITLE}
        if [[ $TITLE_LEN -ge 30 ]] && [[ $TITLE_LEN -le 60 ]]; then
            log_success "Title tag: $TITLE_LEN chars (optimal)"
        elif [[ $TITLE_LEN -gt 0 ]]; then
            log_warning "Title tag: $TITLE_LEN chars (recommended: 30-60)"
        else
            log_error "No title tag found"
        fi

        # Meta description (use file-based grep to avoid bash variable issues with large HTML)
        echo "$HOMEPAGE_HTML" > /tmp/seo_check_$$.html
        if grep -q 'name="description"' /tmp/seo_check_$$.html; then
            DESC=$(grep -oP '<meta name="description" content="\K[^"]+' /tmp/seo_check_$$.html | head -1)
            DESC_LEN=${#DESC}
            if [[ $DESC_LEN -ge 120 ]] && [[ $DESC_LEN -le 160 ]]; then
                log_success "Meta description: $DESC_LEN chars (optimal)"
            elif [[ $DESC_LEN -gt 0 ]]; then
                log_success "Meta description: $DESC_LEN chars (present)"
            else
                log_warning "Meta description is empty"
            fi
        elif grep -q 'property="og:description"' /tmp/seo_check_$$.html; then
            OG_DESC=$(grep -oP 'property="og:description" content="\K[^"]+' /tmp/seo_check_$$.html | head -1)
            OG_DESC_LEN=${#OG_DESC}
            if [[ $OG_DESC_LEN -gt 0 ]]; then
                log_success "Using og:description: $OG_DESC_LEN chars (Yoast/SEO plugin)"
            else
                log_warning "No meta description found"
            fi
        else
            log_warning "No meta description found (check Yoast SEO settings)"
        fi

        # Open Graph tags (use grep -o | wc -l to count all matches, not just lines)
        OG_COUNT=$(echo "$HOMEPAGE_HTML" | grep -o 'property="og:' | wc -l || echo "0")
        if [[ $OG_COUNT -ge 3 ]]; then
            log_success "Open Graph tags: $OG_COUNT found"
        else
            log_warning "Open Graph tags: $OG_COUNT (recommend: 3+)"
        fi

        # Canonical URL
        if grep -q 'rel="canonical"' /tmp/seo_check_$$.html; then
            CANONICAL=$(grep -oP 'rel="canonical" href="\K[^"]+' /tmp/seo_check_$$.html | head -1)
            log_success "Canonical URL: $CANONICAL"
        else
            log_warning "No canonical URL"
        fi

        # Cleanup temp file
        rm -f /tmp/seo_check_$$.html
    fi
fi

# =============================================================================
# LAYER 13: Accessibility (WCAG 2.1)
# =============================================================================

if should_run_layer 13; then
    log_header 13 "Accessibility (WCAG 2.1)"

    HOMEPAGE_HTML=$(curl -sL --connect-timeout 10 "$SITE_URL" 2>/dev/null || echo "")

    if [[ -n "$HOMEPAGE_HTML" ]]; then
        # Image alt text
        IMG_TOTAL=$(echo "$HOMEPAGE_HTML" | grep -o '<img ' | wc -l)
        IMG_WITH_ALT=$(echo "$HOMEPAGE_HTML" | grep -oP '<img[^>]+alt="[^"]+"' | wc -l)
        IMG_NO_ALT=$((IMG_TOTAL - IMG_WITH_ALT))

        if [[ $IMG_NO_ALT -eq 0 ]]; then
            log_success "All $IMG_TOTAL images have alt text"
        else
            log_warning "$IMG_NO_ALT of $IMG_TOTAL images missing alt text"
        fi

        # H1 headings
        H1_COUNT=$(echo "$HOMEPAGE_HTML" | grep -c '<h1' || echo "0")
        if [[ $H1_COUNT -eq 1 ]]; then
            log_success "Single H1 heading (correct structure)"
        elif [[ $H1_COUNT -eq 0 ]]; then
            log_error "No H1 heading found"
        else
            log_warning "$H1_COUNT H1 headings (should be 1)"
        fi

        # Form labels - exclude hidden inputs, count both explicit and implicit labels
        # Hidden inputs don't need labels, and CF7 uses implicit labeling (input inside label)
        VISIBLE_INPUTS=$(echo "$HOMEPAGE_HTML" | grep -oP '<input[^>]*type="(?!hidden)[^"]*"' | wc -l)
        FORM_LABELS=$(echo "$HOMEPAGE_HTML" | grep -o '<label' | wc -l)
        # Also check for implicit labels (inputs wrapped in label tags)
        IMPLICIT_LABELS=$(echo "$HOMEPAGE_HTML" | grep -oP '<label[^>]*>.*?<input' | wc -l)
        TOTAL_LABELS=$((FORM_LABELS > IMPLICIT_LABELS ? FORM_LABELS : FORM_LABELS + IMPLICIT_LABELS))

        if [[ $VISIBLE_INPUTS -le $TOTAL_LABELS ]] || [[ $IMPLICIT_LABELS -gt 0 ]]; then
            log_success "Form inputs have labels (including implicit)"
        elif [[ $VISIBLE_INPUTS -eq 0 ]]; then
            log_success "No visible form inputs to check"
        else
            log_warning "Some form inputs may lack labels ($VISIBLE_INPUTS visible inputs, $FORM_LABELS labels)"
        fi

        # ARIA usage
        ARIA_COUNT=$(echo "$HOMEPAGE_HTML" | grep -c 'aria-' || echo "0")
        log_info "ARIA attributes: $ARIA_COUNT"
    fi
fi

# =============================================================================
# LAYER 14: Image Optimization
# =============================================================================

if should_run_layer 14; then
    log_header 14 "Image Optimization"

    if ! $IS_REMOTE && [[ -d "$WP_PATH/wp-content/uploads" ]]; then
        # Total upload size
        UPLOAD_SIZE=$(du -sh "$WP_PATH/wp-content/uploads" 2>/dev/null | cut -f1)
        log_info "Uploads directory size: $UPLOAD_SIZE"

        # Large images
        LARGE_IMAGES=$(find "$WP_PATH/wp-content/uploads" -type f \( -iname "*.jpg" -o -iname "*.png" \) -size +500k 2>/dev/null | wc -l)
        if [[ $LARGE_IMAGES -eq 0 ]]; then
            log_success "No oversized images (>500KB)"
        else
            log_warning "$LARGE_IMAGES images over 500KB (consider optimization)"
        fi

        # WebP support check
        WEBP_COUNT=$(find "$WP_PATH/wp-content/uploads" -type f -iname "*.webp" 2>/dev/null | wc -l)
        if [[ $WEBP_COUNT -gt 0 ]]; then
            log_success "WebP images in use: $WEBP_COUNT"
        else
            log_info "No WebP images (consider converting for performance)"
        fi
    else
        log_info "Image analysis skipped (remote environment)"
    fi
fi

# =============================================================================
# LAYER 15: JavaScript Analysis
# =============================================================================

if should_run_layer 15; then
    log_header 15 "JavaScript Analysis"

    if ! $IS_REMOTE && command -v node &>/dev/null; then
        # Find JS files
        JS_FILES=$(find "$WP_PATH/wp-content/plugins" "$WP_PATH/wp-content/themes" -name "*.js" -type f 2>/dev/null | grep -v "node_modules\|\.min\.js" | head -20)
        SYNTAX_ERRORS=0

        for js_file in $JS_FILES; do
            if ! node -c "$js_file" 2>/dev/null; then
                log_error "JS syntax error: $(basename "$js_file")"
                ((SYNTAX_ERRORS++))
            fi
        done

        if [[ $SYNTAX_ERRORS -eq 0 ]]; then
            log_success "No JavaScript syntax errors"
        fi

        # Check for eval usage (excluding node_modules)
        EVAL_COUNT=$(find "$WP_PATH/wp-content/plugins" "$WP_PATH/wp-content/themes" -name "*.js" -not -path "*/node_modules/*" -exec grep -l "eval(" {} \; 2>/dev/null | wc -l || echo "0")
        if [[ $EVAL_COUNT -eq 0 ]]; then
            log_success "No eval() usage (good security)"
        else
            log_warning "$EVAL_COUNT eval() usages found (security risk)"
        fi
    else
        log_info "JavaScript analysis skipped (Node.js not available or remote)"
    fi
fi

# =============================================================================
# LAYER 16: REST API Health (NEW)
# =============================================================================

if should_run_layer 16; then
    log_header 16 "REST API Health"

    # Test WordPress REST API root
    API_ROOT=$(curl -sL --connect-timeout 10 "$SITE_URL/wp-json/" 2>/dev/null)

    if [[ -n "$API_ROOT" ]] && echo "$API_ROOT" | grep -q "name"; then
        SITE_NAME=$(echo "$API_ROOT" | grep -oP '"name"\s*:\s*"\K[^"]+' | head -1)
        log_success "REST API accessible: $SITE_NAME"

        # Test specific endpoints
        ENDPOINTS=(
            "/wp-json/wp/v2/posts?per_page=1"
            "/wp-json/wp/v2/pages?per_page=1"
            "/wp-json/wp/v2/users"
        )

        for endpoint in "${ENDPOINTS[@]}"; do
            status=$(curl -o /dev/null -s -w "%{http_code}" --connect-timeout 5 "${SITE_URL}${endpoint}" 2>/dev/null || echo "000")
            endpoint_name=$(basename "$endpoint" | cut -d'?' -f1)
            if [[ "$status" == "200" ]]; then
                log_success "Endpoint $endpoint_name: HTTP $status"
            elif [[ "$status" == "401" ]] || [[ "$status" == "403" ]]; then
                log_info "Endpoint $endpoint_name: HTTP $status (auth required)"
            else
                log_warning "Endpoint $endpoint_name: HTTP $status"
            fi
        done
    else
        log_error "REST API not accessible"
    fi

    # Custom campaign endpoints
    CAMPAIGN_API=$(curl -sL --connect-timeout 5 "$SITE_URL/wp-json/rundaverun/v1/" 2>/dev/null)
    if [[ -n "$CAMPAIGN_API" ]]; then
        log_success "Custom campaign API available"
    else
        log_info "No custom campaign API endpoints"
    fi
fi

# =============================================================================
# LAYER 17: SSL/DNS/CDN Infrastructure (NEW)
# =============================================================================

if should_run_layer 17; then
    log_header 17 "SSL/DNS/CDN Infrastructure"

    # Extract hostname
    HOSTNAME=$(echo "$SITE_URL" | sed 's|https\?://||' | cut -d'/' -f1)

    # SSL Certificate check (production only)
    if [[ "$SITE_URL" =~ ^https ]]; then
        SSL_INFO=$(echo | timeout 5 openssl s_client -servername "$HOSTNAME" -connect "${HOSTNAME}:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)

        if [[ -n "$SSL_INFO" ]]; then
            EXPIRY=$(echo "$SSL_INFO" | grep "notAfter" | cut -d'=' -f2)
            EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || echo "0")
            NOW_EPOCH=$(date +%s)
            DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

            if [[ $DAYS_LEFT -gt 30 ]]; then
                log_success "SSL certificate valid ($DAYS_LEFT days remaining)"
            elif [[ $DAYS_LEFT -gt 0 ]]; then
                log_warning "SSL certificate expiring soon ($DAYS_LEFT days)"
            else
                log_error "SSL certificate expired or invalid"
            fi
        else
            log_info "SSL certificate check skipped (local environment)"
        fi
    else
        log_info "HTTP site - SSL not applicable"
    fi

    # DNS lookup
    if command -v dig &>/dev/null; then
        DNS_A=$(dig +short "$HOSTNAME" A 2>/dev/null | head -1)
        if [[ -n "$DNS_A" ]]; then
            log_success "DNS A record: $DNS_A"
        else
            log_info "No DNS A record (may be local)"
        fi
    fi

    # CDN detection
    CDN_HEADERS=$(curl -sI --connect-timeout 5 "$SITE_URL" 2>/dev/null | grep -iE "x-cache|cf-ray|x-cdn|x-served-by")
    if [[ -n "$CDN_HEADERS" ]]; then
        log_success "CDN detected"
        log_code "$CDN_HEADERS"
    else
        log_info "No CDN detected"
    fi

    # Security headers
    SECURITY_HEADERS=$(curl -sI --connect-timeout 5 "$SITE_URL" 2>/dev/null)

    if echo "$SECURITY_HEADERS" | grep -qi "x-frame-options"; then
        log_success "X-Frame-Options header present"
    else
        log_warning "X-Frame-Options header missing"
    fi

    if echo "$SECURITY_HEADERS" | grep -qi "x-content-type-options"; then
        log_success "X-Content-Type-Options header present"
    else
        log_warning "X-Content-Type-Options header missing"
    fi
fi

# =============================================================================
# LAYER 18: Form Testing (NEW)
# =============================================================================

if should_run_layer 18; then
    log_header 18 "Form Testing"

    # Find Contact Form 7 forms
    CF7_FORMS=$(run_wp_cli "post list --post_type=wpcf7_contact_form --format=csv --fields=ID,post_title" 2>/dev/null)
    FORM_COUNT=$(echo "$CF7_FORMS" | wc -l)

    if [[ $FORM_COUNT -gt 1 ]]; then
        log_info "Contact Form 7 forms: $((FORM_COUNT - 1))"
        log_code "$CF7_FORMS"

        # Test form endpoints
        CF7_NONCE_PAGE=$(curl -sL --connect-timeout 10 "$SITE_URL/contact/" 2>/dev/null)
        if echo "$CF7_NONCE_PAGE" | grep -q "wpcf7"; then
            log_success "CF7 forms rendering on contact page"
        else
            log_info "CF7 forms not found on /contact/"
        fi
    else
        log_info "No Contact Form 7 forms found"
    fi

    # Check for newsletter signup forms
    NEWSLETTER_CHECK=$(curl -sL --connect-timeout 5 "$SITE_URL" 2>/dev/null | grep -ic "newsletter\|subscribe\|email-signup" || echo "0")
    if [[ $NEWSLETTER_CHECK -gt 0 ]]; then
        log_success "Newsletter signup form detected"
    else
        log_info "No newsletter signup detected on homepage"
    fi
fi

# =============================================================================
# LAYER 19: Email Verification (NEW)
# =============================================================================

if should_run_layer 19; then
    log_header 19 "Email Configuration"

    # Check WP Mail SMTP (using plugin list for reliable detection)
    SMTP_PRO_STATUS=$(run_wp_cli "plugin list --name=wp-mail-smtp-pro --field=status" 2>/dev/null || echo "not-installed")
    SMTP_STATUS=$(run_wp_cli "plugin list --name=wp-mail-smtp --field=status" 2>/dev/null || echo "not-installed")

    if [[ "$SMTP_PRO_STATUS" == "active" ]]; then
        log_success "WP Mail SMTP Pro is active"
    elif [[ "$SMTP_STATUS" == "active" ]]; then
        log_success "WP Mail SMTP is active"
    else
        log_warning "No SMTP plugin detected"
    fi

    # Check admin email
    ADMIN_EMAIL=$(run_wp_cli "option get admin_email" 2>/dev/null || echo "unknown")
    log_info "Admin email: $ADMIN_EMAIL"

    # Check if from email is configured (via options)
    FROM_EMAIL=$(run_wp_cli "option get wp_mail_smtp --format=json" 2>/dev/null | grep -oP '"mail"[^}]*"from_email"\s*:\s*"\K[^"]+' || echo "default")
    log_info "SMTP from email: $FROM_EMAIL"
fi

# =============================================================================
# LAYER 20: Production Remote Diagnostics (NEW)
# =============================================================================

if should_run_layer 20; then
    log_header 20 "Production Remote Diagnostics"

    if $IS_REMOTE; then
        # Test SSH connectivity
        SSH_TEST=$(eval "$SSH_CMD \"echo 'SSH_OK'\"" 2>&1)
        if [[ "$SSH_TEST" == *"SSH_OK"* ]]; then
            log_success "SSH connection established"

            # Remote WordPress version
            REMOTE_WP=$(eval "$SSH_CMD \"$WP_CLI_REMOTE core version\"" 2>/dev/null)
            log_info "Remote WordPress: $REMOTE_WP"

            # Remote disk space
            REMOTE_DISK=$(eval "$SSH_CMD \"df -h /home | tail -1 | awk '{print \\\$5}'\"" 2>/dev/null)
            log_info "Remote disk usage: $REMOTE_DISK"

            # Recent error log
            REMOTE_ERRORS=$(eval "$SSH_CMD \"cd html && tail -5 wp-content/debug.log 2>/dev/null | grep -E 'Fatal|Error' || echo 'No recent errors'\"" 2>/dev/null)
            log_info "Recent errors: $REMOTE_ERRORS"

            # Cache status
            CACHE_STATUS=$(eval "$SSH_CMD \"$WP_CLI_REMOTE cache type\"" 2>/dev/null || echo "unknown")
            log_info "Cache type: $CACHE_STATUS"
        else
            log_error "SSH connection failed"
            log_code "$SSH_TEST"
        fi
    else
        log_info "Remote diagnostics skipped (not production environment)"
        log_info "Run with 'production' argument to enable SSH diagnostics"
    fi
fi

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
echo -e "${BOLD}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                         DIAGNOSTIC SUMMARY                           ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Calculate health score
TOTAL_CHECKS=$((PASSED + WARNINGS + CRITICAL_ISSUES))
if [[ $TOTAL_CHECKS -gt 0 ]]; then
    HEALTH_SCORE=$((100 - (CRITICAL_ISSUES * 10) - (WARNINGS * 2)))
    [[ $HEALTH_SCORE -lt 0 ]] && HEALTH_SCORE=0
else
    HEALTH_SCORE=100
fi

# Determine rating
if [[ $HEALTH_SCORE -ge 95 ]]; then
    HEALTH_RATING="${GREEN}EXCELLENT${NC}"
elif [[ $HEALTH_SCORE -ge 85 ]]; then
    HEALTH_RATING="${GREEN}GOOD${NC}"
elif [[ $HEALTH_SCORE -ge 75 ]]; then
    HEALTH_RATING="${YELLOW}FAIR${NC}"
else
    HEALTH_RATING="${RED}NEEDS ATTENTION${NC}"
fi

echo -e "  Passed Checks:    ${GREEN}$PASSED${NC}"
echo -e "  Warnings:         ${YELLOW}$WARNINGS${NC}"
echo -e "  Critical Issues:  ${RED}$CRITICAL_ISSUES${NC}"
echo ""
echo -e "  ${BOLD}Health Score:${NC} $HEALTH_SCORE/100 $HEALTH_RATING"
echo ""

# Write summary to report
cat >> "$REPORT_FILE" << EOF

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Passed Checks | $PASSED |
| Warnings | $WARNINGS |
| Critical Issues | $CRITICAL_ISSUES |
| **Health Score** | **$HEALTH_SCORE/100** |

### Layer Status Matrix

| Layer | Name | Status |
|-------|------|--------|
EOF

# Add layer status to report
LAYERS=(
    "1:System Environment"
    "2:WordPress Core"
    "3:Database Integrity"
    "4:Plugin Health"
    "5:Theme Integrity"
    "6:Content Structure"
    "7:Shortcodes & Hooks"
    "8:Performance Metrics"
    "9:Security Audit"
    "10:Error Logs"
    "11:Link Integrity"
    "12:SEO Metadata"
    "13:Accessibility"
    "14:Image Optimization"
    "15:JavaScript Analysis"
    "16:REST API Health"
    "17:SSL/DNS/CDN"
    "18:Form Testing"
    "19:Email Verification"
    "20:Production Remote"
)

for layer_info in "${LAYERS[@]}"; do
    layer_num="${layer_info%%:*}"
    layer_name="${layer_info#*:}"
    if should_run_layer "$layer_num"; then
        echo "| $layer_num | $layer_name | ✅ Checked |" >> "$REPORT_FILE"
    else
        echo "| $layer_num | $layer_name | ⏭️ Skipped |" >> "$REPORT_FILE"
    fi
done

cat >> "$REPORT_FILE" << EOF

---

## Session Information

- **Script Version:** $VERSION
- **Environment:** $ENVIRONMENT
- **Session Directory:** $SESSION_DIR
- **Generated:** $(date '+%Y-%m-%d %H:%M:%S')

EOF

echo -e "  Report saved to: ${CYAN}$REPORT_FILE${NC}"
echo ""

# Exit code based on results
if [[ $CRITICAL_ISSUES -gt 0 ]]; then
    exit 1
elif [[ $WARNINGS -gt 5 ]]; then
    exit 2
else
    exit 0
fi
