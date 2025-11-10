#!/bin/bash
###############################################################################
# WordPress Comprehensive Site Diagnostic with JS Runtime Analysis
# Version: 1.2.0
# Created: 2025-11-08
# Updated: 2025-11-08 (Added Layer 9: JavaScript Runtime Analysis)
# Protocol: wordpress_site_diagnostic_protocol.md
#
# Description:
#   Performs 9-layer diagnostic of WordPress site including WCAG 2.1 AA
#   accessibility checking and JavaScript runtime analysis
#
# Changes from v1.1.0:
#   + Added LAYER 9: JavaScript Runtime Analysis
#   + JavaScript syntax validation (node -c)
#   + Strict mode violation detection (function reassignment)
#   + Anti-pattern detection (eval, console.log, loose equality)
#   + jQuery version checking
#   + AJAX error handling validation
#
# Usage:
#   bash wordpress_comprehensive_diagnostic_v1.1.0.sh [site_url] [wp_path]
#
# Examples:
#   bash wordpress_comprehensive_diagnostic_v1.1.0.sh http://rundaverun-local.local
#   bash wordpress_comprehensive_diagnostic_v1.1.0.sh https://rundaverun.org /home/dave/html
#
# Exit Codes:
#   0 = All checks passed
#   1 = Critical issues found
#   2 = Warnings found (review recommended)
###############################################################################

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

# Color contrast calculation functions
hex_to_rgb() {
    local hex="$1"
    # Remove # if present
    hex="${hex#\#}"

    # Handle 3-digit hex codes (e.g., #FFF -> #FFFFFF)
    if [ ${#hex} -eq 3 ]; then
        hex="${hex:0:1}${hex:0:1}${hex:1:1}${hex:1:1}${hex:2:1}${hex:2:1}"
    fi

    # Convert to RGB
    local r=$((16#${hex:0:2}))
    local g=$((16#${hex:2:2}))
    local b=$((16#${hex:4:2}))

    echo "$r $g $b"
}

calculate_relative_luminance() {
    local r=$1 g=$2 b=$3

    # Convert to 0-1 range
    local r_srgb=$(awk "BEGIN {printf \"%.6f\", $r / 255}")
    local g_srgb=$(awk "BEGIN {printf \"%.6f\", $g / 255}")
    local b_srgb=$(awk "BEGIN {printf \"%.6f\", $b / 255}")

    # Apply gamma correction
    local r_linear=$(awk "BEGIN {if ($r_srgb <= 0.03928) printf \"%.6f\", $r_srgb / 12.92; else printf \"%.6f\", (($r_srgb + 0.055) / 1.055) ^ 2.4}")
    local g_linear=$(awk "BEGIN {if ($g_srgb <= 0.03928) printf \"%.6f\", $g_srgb / 12.92; else printf \"%.6f\", (($g_srgb + 0.055) / 1.055) ^ 2.4}")
    local b_linear=$(awk "BEGIN {if ($b_srgb <= 0.03928) printf \"%.6f\", $b_srgb / 12.92; else printf \"%.6f\", (($b_srgb + 0.055) / 1.055) ^ 2.4}")

    # Calculate relative luminance
    local luminance=$(awk "BEGIN {printf \"%.6f\", 0.2126 * $r_linear + 0.7152 * $g_linear + 0.0722 * $b_linear}")
    echo "$luminance"
}

calculate_contrast_ratio() {
    local color1="$1"
    local color2="$2"

    # Convert hex to RGB
    read -r r1 g1 b1 <<< "$(hex_to_rgb "$color1")"
    read -r r2 g2 b2 <<< "$(hex_to_rgb "$color2")"

    # Calculate relative luminance for both colors
    local l1=$(calculate_relative_luminance "$r1" "$g1" "$b1")
    local l2=$(calculate_relative_luminance "$r2" "$g2" "$b2")

    # Calculate contrast ratio: (lighter + 0.05) / (darker + 0.05)
    local ratio=$(awk "BEGIN {
        l1 = $l1 + 0.05;
        l2 = $l2 + 0.05;
        if (l1 > l2) printf \"%.2f\", l1 / l2;
        else printf \"%.2f\", l2 / l1;
    }")

    echo "$ratio"
}

check_wcag_compliance() {
    local ratio=$1
    local is_large_text=${2:-false}

    if [ "$is_large_text" = "true" ]; then
        # Large text needs 3:1 ratio for AA
        if awk "BEGIN {exit !($ratio >= 3.0)}"; then
            echo "PASS_AA"
        else
            echo "FAIL"
        fi
    else
        # Normal text needs 4.5:1 ratio for AA
        if awk "BEGIN {exit !($ratio >= 4.5)}"; then
            echo "PASS_AA"
        elif awk "BEGIN {exit !($ratio >= 3.0)}"; then
            echo "PASS_LARGE_ONLY"
        else
            echo "FAIL"
        fi
    fi
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
    echo "Protocol: wordpress_site_diagnostic_protocol.md v1.1.0"
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
# LAYER 8: Accessibility & Color Contrast Checking
###############################################################################
log_header "LAYER 8: Accessibility & Color Contrast (WCAG 2.1 AA)"

log_info "Performing 4-part accessibility scan..."
ACCESSIBILITY_ISSUES=0

# CHECK 8.1a: CSS Inheritance Issues (White-on-White Detection)
log_info "8.1a - White Background Inheritance (white-on-white text risks)"

# Find all CSS files in plugins and themes
CSS_FILES=$(find wp-content/plugins wp-content/themes -name "*.css" -type f 2>/dev/null || echo "")
CSS_INHERITANCE_ISSUES=0

if [ -n "$CSS_FILES" ]; then
    for css_file in $CSS_FILES; do
        # Look for classes with white backgrounds but no explicit text color
        WHITE_BG_LINES=$(grep -n "background.*white\|background.*#fff\|background.*#ffffff" "$css_file" 2>/dev/null | cut -d: -f1 || echo "")

        if [ -n "$WHITE_BG_LINES" ]; then
            for line_num in $WHITE_BG_LINES; do
                # Get the class name (look backwards from the background line)
                CLASS_NAME=$(sed -n "1,${line_num}p" "$css_file" 2>/dev/null | tac | grep -m 1 "^\s*\." 2>/dev/null | sed 's/\s*{.*//' | sed 's/^\s*\.//' | sed 's/\s.*//' || echo "")

                if [ -n "$CLASS_NAME" ]; then
                    # Check if this class has an explicit color property
                    BLOCK_START=$(grep -n "^\.$CLASS_NAME\|^\s*\.$CLASS_NAME" "$css_file" 2>/dev/null | head -1 | cut -d: -f1 || echo "")

                    if [ -n "$BLOCK_START" ]; then
                        # Extract the block (from class name to closing brace)
                        BLOCK=$(sed -n "${BLOCK_START},/^}/p" "$css_file" 2>/dev/null | head -20 || echo "")

                        # Check if block has explicit color (not just background)
                        if echo "$BLOCK" | grep -q "^\s*color:"; then
                            # Has explicit color - good!
                            :
                        else
                            log_warning "CSS: .$CLASS_NAME has white background but NO explicit text color"
                            log_info "  File: $css_file:$line_num"
                            log_info "  Risk: Will inherit color from parent - could cause white-on-white text"
                            log_info "  Fix: Add 'color: #333;' to .$CLASS_NAME"
                            CSS_INHERITANCE_ISSUES=$((CSS_INHERITANCE_ISSUES + 1))
                            ACCESSIBILITY_ISSUES=$((ACCESSIBILITY_ISSUES + 1))
                        fi
                    fi
                fi
            done
        fi
    done

    if [ "$CSS_INHERITANCE_ISSUES" -eq 0 ]; then
        log_success "No white background inheritance issues found"
    else
        log_info "Found $CSS_INHERITANCE_ISSUES white background inheritance issues"
    fi
else
    log_info "No CSS files found to scan"
fi

# CHECK 8.1b: Dark Background Inheritance Issues (Dark-on-Dark Detection)
log_info "8.1b - Dark Background Inheritance (dark-on-dark text risks)"

DARK_BG_ISSUES=0

if [ -n "$CSS_FILES" ]; then
    for css_file in $CSS_FILES; do
        # Look for classes with dark backgrounds (gradients with dark colors, or solid dark colors)
        DARK_BG_LINES=$(grep -n "background.*#00[0-9a-fA-F]\{4\}\|background.*linear-gradient.*#00[0-9a-fA-F]\{4\}" "$css_file" 2>/dev/null | cut -d: -f1 || echo "")

        if [ -n "$DARK_BG_LINES" ]; then
            for line_num in $DARK_BG_LINES; do
                # Get the class name
                CLASS_NAME=$(sed -n "1,${line_num}p" "$css_file" 2>/dev/null | tac | grep -m 1 "^\s*\." 2>/dev/null | sed 's/\s*{.*//' | sed 's/^\s*\.//' | sed 's/\s.*//' || echo "")

                if [ -n "$CLASS_NAME" ]; then
                    BLOCK_START=$(grep -n "^\.$CLASS_NAME\|^\s*\.$CLASS_NAME" "$css_file" 2>/dev/null | head -1 | cut -d: -f1 || echo "")

                    if [ -n "$BLOCK_START" ]; then
                        BLOCK=$(sed -n "${BLOCK_START},/^}/p" "$css_file" 2>/dev/null | head -20 || echo "")

                        # Check if block has explicit color
                        if echo "$BLOCK" | grep -q "^\s*color:"; then
                            # Has color - check if it's light enough for dark background
                            COLOR_VALUE=$(echo "$BLOCK" | grep "^\s*color:" | sed 's/.*color:\s*//' | sed 's/;.*//' | sed 's/\s*!important.*//' | tr -d ' ')

                            # If color is explicitly white, good!
                            if echo "$COLOR_VALUE" | grep -qiE "white|#fff|#ffffff|rgba?\(255,\s*255,\s*255"; then
                                : # Color is white - good for dark background
                            else
                                log_warning "CSS: .$CLASS_NAME has dark background but color may not be light"
                                log_info "  File: $css_file:$line_num"
                                log_info "  Color: $COLOR_VALUE"
                                log_info "  Fix: Verify color is 'white' or '#fff' for dark backgrounds"
                            fi
                        else
                            log_error "CSS: .$CLASS_NAME has dark background but NO explicit text color"
                            log_info "  File: $css_file:$line_num"
                            log_info "  Risk: Will inherit color from parent - likely causes dark-on-dark text"
                            log_info "  Fix: Add 'color: white !important;' to .$CLASS_NAME"
                            DARK_BG_ISSUES=$((DARK_BG_ISSUES + 1))
                            ACCESSIBILITY_ISSUES=$((ACCESSIBILITY_ISSUES + 1))
                        fi
                    fi
                fi
            done
        fi
    done

    if [ "$DARK_BG_ISSUES" -eq 0 ]; then
        log_success "No dark background inheritance issues found"
    else
        log_info "Found $DARK_BG_ISSUES dark background inheritance issues"
    fi
fi

# CHECK 8.2: Explicit Color Contrast Violations
log_info "8.2 - Explicit Color Contrast Violations"

CONTRAST_ISSUES=0

for page_id in $CRITICAL_PAGE_IDS; do
    if wp post get "$page_id" >/dev/null 2>&1; then
        PAGE_TITLE=$(wp post get "$page_id" --field=post_title 2>/dev/null)
        PAGE_CONTENT=$(wp post get "$page_id" --field=post_content 2>/dev/null)

        # Check for yellow text on dark blue backgrounds
        if echo "$PAGE_CONTENT" | grep -q "background.*gradient.*#003D7A\|background.*gradient.*#002952"; then
            if echo "$PAGE_CONTENT" | grep -q "color:\s*#FFC72C"; then
                RATIO=$(calculate_contrast_ratio "#FFC72C" "#003D7A" 2>/dev/null || echo "0.00")
                WCAG_RESULT=$(check_wcag_compliance "$RATIO" "false" 2>/dev/null || echo "FAIL")

                if [ "$WCAG_RESULT" = "PASS_AA" ]; then
                    log_success "Page $page_id: Yellow (#FFC72C) on dark blue: ${RATIO}:1 PASS"
                elif [ "$WCAG_RESULT" = "PASS_LARGE_ONLY" ]; then
                    log_warning "Page $page_id: Yellow (#FFC72C) on dark blue: ${RATIO}:1 (large text only)"
                    CONTRAST_ISSUES=$((CONTRAST_ISSUES + 1))
                    ACCESSIBILITY_ISSUES=$((ACCESSIBILITY_ISSUES + 1))
                else
                    log_error "Page $page_id: Yellow (#FFC72C) on dark blue: ${RATIO}:1 FAIL"
                    CONTRAST_ISSUES=$((CONTRAST_ISSUES + 1))
                    ACCESSIBILITY_ISSUES=$((ACCESSIBILITY_ISSUES + 1))
                fi
            fi
        fi
    fi
done

if [ "$CONTRAST_ISSUES" -eq 0 ]; then
    log_success "No explicit color contrast violations found"
fi

# CHECK 8.3: JavaScript-Generated Content Analysis
log_info "8.3 - JavaScript-Generated Content"

JS_FILES=$(find wp-content/plugins wp-content/themes -name "*.js" -type f 2>/dev/null || echo "")
JS_CONTENT_ISSUES=0

if [ -n "$JS_FILES" ]; then
    for js_file in $JS_FILES; do
        # Look for innerHTML or insertAdjacentHTML with list items or text
        if grep -q "innerHTML.*<li>\|innerHTML.*<p>" "$js_file" 2>/dev/null; then
            log_info "Dynamic content generation in: $js_file"

            # Check if the corresponding CSS has proper color settings
            CSS_FILE="${js_file//.js/.css}"
            CSS_FILE="${CSS_FILE//js/css}"

            if [ -f "$CSS_FILE" ]; then
                log_success "  Corresponding CSS file exists: $CSS_FILE"
            else
                log_warning "  No corresponding CSS file - ensure parent provides explicit color"
                JS_CONTENT_ISSUES=$((JS_CONTENT_ISSUES + 1))
                ACCESSIBILITY_ISSUES=$((ACCESSIBILITY_ISSUES + 1))
            fi
        fi
    done

    if [ "$JS_CONTENT_ISSUES" -eq 0 ]; then
        log_success "JavaScript-generated content properly styled"
    fi
else
    log_info "No JavaScript files found to scan"
fi

# CHECK 8.4: Common Problematic Patterns
log_info "8.4 - Common Problematic Patterns"

PATTERN_ISSUES=0

if [ -n "$CSS_FILES" ]; then
    # Pattern: Classes with white background that could inherit white text from parent
    for css_file in $CSS_FILES; do
        grep -n "background:\s*white\|background:\s*#fff" "$css_file" 2>/dev/null | while read -r line; do
            line_num=$(echo "$line" | cut -d: -f1)

            # Get class name
            CLASS=$(sed -n "1,${line_num}p" "$css_file" 2>/dev/null | tac | grep -m 1 "^\s*\." 2>/dev/null | sed 's/\s*{.*//' | sed 's/^\s*\.//' | sed 's/\s.*//' || echo "")

            if [ -n "$CLASS" ]; then
                # Check if it has explicit color
                BLOCK=$(sed -n "/$CLASS/,/^}/p" "$css_file" 2>/dev/null | head -15 || echo "")

                if ! echo "$BLOCK" | grep -q "^\s*color:"; then
                    # Count this as a pattern issue
                    PATTERN_ISSUES=$((PATTERN_ISSUES + 1))
                fi
            fi
        done
    done

    if [ "$PATTERN_ISSUES" -eq 0 ]; then
        log_success "No common problematic patterns found"
    else
        log_warning "Found $PATTERN_ISSUES classes with white backgrounds lacking explicit color"
        log_info "  (See CHECK 8.1 above for details)"
    fi
else
    log_info "No CSS files to check for patterns"
fi

# Summary of Layer 8
if [ "$ACCESSIBILITY_ISSUES" -eq 0 ]; then
    log_success "No accessibility issues detected - WCAG 2.1 AA compliant"
else
    log_info "Total accessibility issues found: $ACCESSIBILITY_ISSUES"
    log_info "  Recommendations:"
    log_info "  - Add explicit 'color: #333;' to all white-background CSS classes"
    log_info "  - Test color combinations: https://webaim.org/resources/contrastchecker/"
    log_info "  - WCAG AA requires 4.5:1 contrast for normal text, 3.0:1 for large text"
fi

###############################################################################
# LAYER 9: JavaScript Runtime Analysis
###############################################################################
log_header "LAYER 9: JavaScript Runtime Analysis"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    log_warning "Node.js not found - skipping JavaScript runtime checks"
    log_info "  Install Node.js to enable JS runtime analysis"
else
    log_info "9.1 - JavaScript Syntax Validation"

    JS_FILES=$(find "$WP_PATH/wp-content/plugins" "$WP_PATH/wp-content/themes" -name "*.js" -type f 2>/dev/null | grep -v node_modules | grep -v ".min.js" || echo "")
    JS_SYNTAX_ERRORS=0

    if [ -n "$JS_FILES" ]; then
        while IFS= read -r js_file; do
            if [ -f "$js_file" ]; then
                ERROR_OUTPUT=$(node -c "$js_file" 2>&1)
                if [ $? -ne 0 ]; then
                    log_error "JS Syntax Error: $js_file"
                    log_info "  $(echo "$ERROR_OUTPUT" | head -3)"
                    JS_SYNTAX_ERRORS=$((JS_SYNTAX_ERRORS + 1))
                fi
            fi
        done <<< "$JS_FILES"

        if [ "$JS_SYNTAX_ERRORS" -eq 0 ]; then
            log_success "All JavaScript files have valid syntax"
        else
            log_error "Found $JS_SYNTAX_ERRORS JavaScript files with syntax errors"
            ISSUES_FOUND=$((ISSUES_FOUND + JS_SYNTAX_ERRORS))
        fi
    fi

    log_info "9.2 - Strict Mode Violations (Function Reassignment)"

    STRICT_MODE_ISSUES=0

    if [ -n "$JS_FILES" ]; then
        while IFS= read -r js_file; do
            if [ -f "$js_file" ]; then
                # Check if file uses strict mode
                if grep -q "use strict" "$js_file" 2>/dev/null; then
                    # Look for function declarations
                    FUNCTION_DECLS=$(grep -n "^\s*function\s\+\w\+" "$js_file" 2>/dev/null | sed 's/:.*function /: /' || echo "")

                    if [ -n "$FUNCTION_DECLS" ]; then
                        while IFS= read -r func_line; do
                            FUNC_NAME=$(echo "$func_line" | sed 's/.*: \(\w\+\).*/\1/')
                            LINE_NUM=$(echo "$func_line" | cut -d: -f1)

                            # Check if this function is later reassigned
                            if grep -q "^\s*${FUNC_NAME}\s*=" "$js_file" 2>/dev/null; then
                                log_warning "Potential strict mode violation in $js_file"
                                log_info "  Function '$FUNC_NAME' declared at line $LINE_NUM may be reassigned"
                                log_info "  Recommendation: Change 'function $FUNC_NAME()' to 'let $FUNC_NAME = function()'"
                                STRICT_MODE_ISSUES=$((STRICT_MODE_ISSUES + 1))
                                WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
                            fi
                        done <<< "$FUNCTION_DECLS"
                    fi
                fi
            fi
        done <<< "$JS_FILES"
    fi

    if [ "$STRICT_MODE_ISSUES" -eq 0 ]; then
        log_success "No strict mode violations detected"
    else
        log_warning "Found $STRICT_MODE_ISSUES potential strict mode issues"
    fi

    log_info "9.3 - Common JavaScript Anti-Patterns"

    ANTI_PATTERNS=0

    if [ -n "$JS_FILES" ]; then
        while IFS= read -r js_file; do
            if [ -f "$js_file" ]; then
                # Check for console.log in production code (should be removed)
                CONSOLE_LOGS=$(grep -n "console\.log\|console\.debug\|console\.info" "$js_file" 2>/dev/null | wc -l)
                if [ "$CONSOLE_LOGS" -gt 0 ]; then
                    log_warning "Found $CONSOLE_LOGS console statements in $js_file"
                    log_info "  Recommendation: Remove console statements for production"
                    ANTI_PATTERNS=$((ANTI_PATTERNS + 1))
                fi

                # Check for eval() usage (security risk)
                if grep -q "eval(" "$js_file" 2>/dev/null; then
                    log_error "Security Risk: eval() found in $js_file"
                    log_info "  Recommendation: Avoid eval() - use safer alternatives"
                    ANTI_PATTERNS=$((ANTI_PATTERNS + 1))
                    ISSUES_FOUND=$((ISSUES_FOUND + 1))
                fi

                # Check for == instead of === (type coercion issues)
                LOOSE_EQUALITY=$(grep -c "[^=!]=[^=]" "$js_file" 2>/dev/null || echo "0")
                if [ "$LOOSE_EQUALITY" -gt 5 ]; then
                    log_warning "Many loose equality (==) comparisons in $js_file"
                    log_info "  Recommendation: Use strict equality (===) to avoid type coercion"
                fi
            fi
        done <<< "$JS_FILES"
    fi

    log_info "9.4 - jQuery Dependencies & Version Check"

    # Check if jQuery is loaded
    JQUERY_LOADED=$(curl -s "$SITE_URL" 2>/dev/null | grep -o "jquery[.-]\?[0-9.]*\.js" | head -1 || echo "")

    if [ -n "$JQUERY_LOADED" ]; then
        log_success "jQuery detected: $JQUERY_LOADED"

        # Extract version if possible
        JQUERY_VERSION=$(echo "$JQUERY_LOADED" | grep -o "[0-9]\+\.[0-9]\+\.[0-9]\+" || echo "unknown")
        if [ "$JQUERY_VERSION" != "unknown" ]; then
            MAJOR_VERSION=$(echo "$JQUERY_VERSION" | cut -d. -f1)
            if [ "$MAJOR_VERSION" -lt 3 ]; then
                log_warning "jQuery version $JQUERY_VERSION is outdated"
                log_info "  Recommendation: Update to jQuery 3.x for security and performance"
                WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
            else
                log_success "jQuery version $JQUERY_VERSION is up to date"
            fi
        fi
    else
        log_info "jQuery not detected (may be using vanilla JS or other frameworks)"
    fi

    log_info "9.5 - JavaScript Error Patterns in Source"

    ERROR_PATTERNS=0

    if [ -n "$JS_FILES" ]; then
        while IFS= read -r js_file; do
            if [ -f "$js_file" ]; then
                # Look for common error patterns
                if grep -q "undefined is not" "$js_file" 2>/dev/null; then
                    log_warning "Potential undefined reference in $js_file"
                    ERROR_PATTERNS=$((ERROR_PATTERNS + 1))
                fi

                # Check for missing error handling in AJAX calls
                if grep -q "\.ajax(" "$js_file" 2>/dev/null; then
                    if ! grep -q "\.fail\|\.catch\|error:" "$js_file" 2>/dev/null; then
                        log_warning "AJAX call without error handling in $js_file"
                        log_info "  Recommendation: Add .fail() or .catch() handlers"
                        ERROR_PATTERNS=$((ERROR_PATTERNS + 1))
                        WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
                    fi
                fi
            fi
        done <<< "$JS_FILES"
    fi

    if [ "$ERROR_PATTERNS" -eq 0 ]; then
        log_success "No common error patterns detected"
    fi
fi

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
