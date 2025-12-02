#!/bin/bash
###############################################################################
# WordPress Comprehensive Site Diagnostic
# Version: 1.0.0
# Created: 2025-11-07
# Protocol: wordpress_site_diagnostic_protocol.md
#
# Description:
#   Performs 7-layer diagnostic of WordPress site to detect issues that
#   surface-level checks miss (content corruption, navigation problems, etc.)
#
# Usage:
#   bash wordpress_comprehensive_diagnostic_v1.0.0.sh [site_url] [wp_path]
#
# Examples:
#   bash wordpress_comprehensive_diagnostic_v1.0.0.sh http://rundaverun-local.local
#   bash wordpress_comprehensive_diagnostic_v1.0.0.sh https://rundaverun.org /home/dave/html
#
# Exit Codes:
#   0 = All checks passed
#   1 = Critical issues found
#   2 = Warnings found (review recommended)
###############################################################################

set -euo pipefail

# Configuration
SITE_URL="${1:-http://localhost}"
WP_PATH="${2:-.}"
REPORT_FILE="/tmp/wp_diagnostic_$(date +%Y%m%d_%H%M%S).txt"
ISSUES_FOUND=0
WARNINGS_FOUND=0

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}" | tee -a "$REPORT_FILE"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$REPORT_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$REPORT_FILE"
    WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
}

log_error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$REPORT_FILE"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
}

log_info() {
    echo -e "  $1" | tee -a "$REPORT_FILE"
}

# Change to WordPress directory
cd "$WP_PATH" || { echo "Error: Cannot access $WP_PATH"; exit 1; }

# Initialize report
{
    echo "=========================================="
    echo "WordPress Comprehensive Diagnostic Report"
    echo "=========================================="
    echo "Site: $SITE_URL"
    echo "Path: $WP_PATH"
    echo "Date: $(date)"
    echo "Protocol: wordpress_site_diagnostic_protocol.md v1.0.0"
    echo "=========================================="
} > "$REPORT_FILE"

###############################################################################
# LAYER 1: Infrastructure Health
###############################################################################
log_header "LAYER 1: Infrastructure Health"

# Check site accessibility
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    log_success "Site accessible (HTTP 200)"
else
    log_error "Site returned HTTP $HTTP_CODE"
fi

# Check WordPress version
WP_VERSION=$(wp core version 2>/dev/null || echo "unknown")
log_info "WordPress version: $WP_VERSION"

# Check PHP version
PHP_VERSION=$(php -v 2>/dev/null | head -1 || echo "unknown")
log_info "PHP version: $PHP_VERSION"

# Check database connection
if wp db check >/dev/null 2>&1; then
    log_success "Database connection successful"
else
    log_error "Database connection failed"
fi

# Check disk space
DISK_FREE=$(df -h "$WP_PATH" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_FREE" -lt 90 ]; then
    log_success "Disk space: ${DISK_FREE}% used"
else
    log_warning "Disk space critical: ${DISK_FREE}% used"
fi

###############################################################################
# LAYER 2: Plugin & Theme Health
###############################################################################
log_header "LAYER 2: Plugin & Theme Health"

# Check active plugins
ACTIVE_PLUGINS=$(wp plugin list --status=active --format=count 2>/dev/null || echo 0)
log_info "Active plugins: $ACTIVE_PLUGINS"

# Check for plugin errors
ERROR_PLUGINS=$(wp plugin list --status=error --format=count 2>/dev/null || echo 0)
if [ "$ERROR_PLUGINS" -eq 0 ]; then
    log_success "No plugin errors"
else
    log_error "$ERROR_PLUGINS plugins have errors"
    wp plugin list --status=error --fields=name,version 2>/dev/null | tee -a "$REPORT_FILE"
fi

# Check active theme
ACTIVE_THEME=$(wp theme list --status=active --field=name 2>/dev/null || echo "unknown")
log_info "Active theme: $ACTIVE_THEME"

# Check for plugin database tables (example for dave-biggers-policy-manager)
DBPM_TABLES=$(wp db query "SHOW TABLES LIKE '%dbpm%'" 2>/dev/null | wc -l || echo 0)
if [ "$DBPM_TABLES" -gt 0 ]; then
    log_success "Plugin database tables found: $DBPM_TABLES"
else
    log_info "No plugin-specific tables found (may be normal)"
fi

###############################################################################
# LAYER 3: Content Integrity
###############################################################################
log_header "LAYER 3: Content Integrity"

# Check for bash command strings in pages
BASH_PAGES_RAW=$(wp db query "SELECT COUNT(*) as count FROM wp_posts WHERE post_type='page' AND post_content LIKE '%\$(cat%'" 2>/dev/null | tail -1)
BASH_PAGES=$(echo "$BASH_PAGES_RAW" | tr -d '[:space:]')
if [ "$BASH_PAGES" = "0" ] || [ -z "$BASH_PAGES" ]; then
    log_success "No bash command strings in page content"
else
    log_error "$BASH_PAGES pages contain bash command strings"
    wp db query "SELECT ID, post_title FROM wp_posts WHERE post_type='page' AND post_content LIKE '%\$(cat%'" 2>/dev/null | tee -a "$REPORT_FILE"
fi

# Check for PHP code in pages
PHP_PAGES=$(wp db query "SELECT COUNT(*) as count FROM wp_posts WHERE post_type='page' AND post_content LIKE '%<?php%'" 2>/dev/null | grep -v "count" | xargs)
if [ "$PHP_PAGES" = "0" ]; then
    log_success "No PHP code in page content"
else
    log_warning "$PHP_PAGES pages contain PHP code"
fi

# Check for empty critical pages (homepage, about, etc.)
CRITICAL_PAGE_IDS="105 107 337"  # Adjust for your site
for page_id in $CRITICAL_PAGE_IDS; do
    if wp post get "$page_id" >/dev/null 2>&1; then
        CONTENT_LENGTH=$(wp post get "$page_id" --field=post_content 2>/dev/null | wc -c)
        PAGE_TITLE=$(wp post get "$page_id" --field=post_title 2>/dev/null)
        if [ "$CONTENT_LENGTH" -gt 100 ]; then
            log_success "Page $page_id ($PAGE_TITLE): $CONTENT_LENGTH chars"
        else
            log_warning "Page $page_id ($PAGE_TITLE) suspiciously short: $CONTENT_LENGTH chars"
        fi
    fi
done

###############################################################################
# LAYER 4: Navigation & URL Structure
###############################################################################
log_header "LAYER 4: Navigation & URL Structure"

# Check rewrite rules exist
REWRITE_COUNT=$(wp rewrite list 2>/dev/null | wc -l || echo 0)
if [ "$REWRITE_COUNT" -gt 0 ]; then
    log_success "Rewrite rules exist: $REWRITE_COUNT rules"
else
    log_warning "No rewrite rules found - flush may be needed"
fi

# Test critical page URLs
CRITICAL_URLS=(
    "/"
    "/about-dave"
    "/our-plan"
    "/voter-education"
    "/policy-library"
)

for url_path in "${CRITICAL_URLS[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "${SITE_URL}${url_path}" 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        log_success "$url_path returns HTTP $response"
    elif [ "$response" = "404" ]; then
        log_error "$url_path returns HTTP 404"
    else
        log_warning "$url_path returns HTTP $response"
    fi
done

# Test policy document URLs (if applicable)
POLICY_COUNT=$(wp post list --post_type=policy_document --format=count 2>/dev/null || echo 0)
if [ "$POLICY_COUNT" -gt 0 ]; then
    log_info "Testing $POLICY_COUNT policy documents..."
    POLICY_404_COUNT=0
    wp post list --post_type=policy_document --format=csv --fields=post_name 2>/dev/null | tail -n +2 | head -5 | while read -r slug; do
        response=$(curl -s -o /dev/null -w "%{http_code}" "${SITE_URL}/policy/${slug}/" 2>/dev/null || echo "000")
        if [ "$response" != "200" ]; then
            log_warning "Policy $slug returns HTTP $response"
        fi
    done
fi

###############################################################################
# LAYER 5: Database Content Validation
###############################################################################
log_header "LAYER 5: Database Content Validation"

# Check post counts
PAGE_COUNT=$(wp post list --post_type=page --format=count 2>/dev/null || echo 0)
POST_COUNT=$(wp post list --post_type=post --format=count 2>/dev/null || echo 0)
POLICY_COUNT=$(wp post list --post_type=policy_document --format=count 2>/dev/null || echo 0)

log_info "Pages: $PAGE_COUNT"
log_info "Posts: $POST_COUNT"
log_info "Policies: $POLICY_COUNT"

# Check for orphaned content
ORPHANED=$(wp db query "SELECT COUNT(*) as count FROM wp_posts WHERE post_parent NOT IN (SELECT ID FROM wp_posts) AND post_parent != 0" 2>/dev/null | grep -v "count" | xargs || echo 0)
if [ "$ORPHANED" = "0" ]; then
    log_success "No orphaned content"
else
    log_warning "$ORPHANED orphaned posts found"
fi

# Check for duplicate slugs
DUPLICATES=$(wp db query "SELECT COUNT(*) as count FROM (SELECT post_name FROM wp_posts WHERE post_status = 'publish' GROUP BY post_name HAVING COUNT(*) > 1) as dupes" 2>/dev/null | grep -v "count" | xargs || echo 0)
if [ "$DUPLICATES" = "0" ]; then
    log_success "No duplicate slugs"
else
    log_warning "$DUPLICATES duplicate slugs found"
fi

# Check menu structure
MENU_COUNT=$(wp menu list --format=count 2>/dev/null || echo 0)
log_info "Menus configured: $MENU_COUNT"

###############################################################################
# LAYER 6: Frontend Rendering
###############################################################################
log_header "LAYER 6: Frontend Rendering"

# Check theme assets
THEME_CSS=$(find "wp-content/themes/${ACTIVE_THEME}" -name "*.css" 2>/dev/null | wc -l || echo 0)
THEME_JS=$(find "wp-content/themes/${ACTIVE_THEME}" -name "*.js" 2>/dev/null | wc -l || echo 0)
log_info "Theme CSS files: $THEME_CSS"
log_info "Theme JS files: $THEME_JS"

# Check plugin assets (example for dave-biggers-policy-manager)
if [ -d "wp-content/plugins/dave-biggers-policy-manager/assets" ]; then
    PLUGIN_CSS=$(find wp-content/plugins/dave-biggers-policy-manager/assets -name "*.css" 2>/dev/null | wc -l || echo 0)
    PLUGIN_JS=$(find wp-content/plugins/dave-biggers-policy-manager/assets -name "*.js" 2>/dev/null | wc -l || echo 0)
    log_success "Plugin assets found: $PLUGIN_CSS CSS, $PLUGIN_JS JS"
fi

# Check homepage rendering
HOMEPAGE_CONTENT=$(curl -s "$SITE_URL" 2>/dev/null)
HOMEPAGE_WORDS=$(echo "$HOMEPAGE_CONTENT" | wc -w)
if [ "$HOMEPAGE_WORDS" -gt 50 ]; then
    log_success "Homepage renders: $HOMEPAGE_WORDS words"
else
    log_error "Homepage suspiciously short: $HOMEPAGE_WORDS words"
fi

# Check for literal shortcodes in output (indicates they're not rendering)
SHORTCODE_CHECK=$(echo "$HOMEPAGE_CONTENT" | grep -o '\[.*\]' | head -1 || echo "")
if [ -z "$SHORTCODE_CHECK" ]; then
    log_success "No unrendered shortcodes detected"
else
    log_warning "Found literal shortcode in output: $SHORTCODE_CHECK"
fi

###############################################################################
# LAYER 7: User Experience Testing
###############################################################################
log_header "LAYER 7: User Experience Testing"

log_info "Manual verification required:"
log_info "  - Take screenshots of critical pages"
log_info "  - Test form submissions"
log_info "  - Verify mobile responsiveness"
log_info "  - Check navigation menu functionality"

###############################################################################
# Summary
###############################################################################
log_header "DIAGNOSTIC SUMMARY"

echo "" | tee -a "$REPORT_FILE"
if [ "$ISSUES_FOUND" -eq 0 ] && [ "$WARNINGS_FOUND" -eq 0 ]; then
    echo -e "${GREEN}✓ Site is healthy - no issues found${NC}" | tee -a "$REPORT_FILE"
    EXIT_CODE=0
elif [ "$ISSUES_FOUND" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Site has $WARNINGS_FOUND warnings (review recommended)${NC}" | tee -a "$REPORT_FILE"
    EXIT_CODE=2
else
    echo -e "${RED}✗ Site has $ISSUES_FOUND critical issues and $WARNINGS_FOUND warnings${NC}" | tee -a "$REPORT_FILE"
    EXIT_CODE=1
fi

echo "" | tee -a "$REPORT_FILE"
echo "Full report saved to: $REPORT_FILE" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

if [ "$ISSUES_FOUND" -gt 0 ]; then
    echo "Next steps:" | tee -a "$REPORT_FILE"
    echo "  1. Review issues in report above" | tee -a "$REPORT_FILE"
    echo "  2. Fix critical issues first" | tee -a "$REPORT_FILE"
    echo "  3. Re-run diagnostic to verify fixes" | tee -a "$REPORT_FILE"
    echo "  4. See wordpress_site_diagnostic_protocol.md for remediation steps" | tee -a "$REPORT_FILE"
fi

exit $EXIT_CODE
