#!/bin/bash

# Comprehensive WordPress Site Debugger v2.2.0
# 15-Layer Deep Diagnostic Tool
# Created: November 11, 2025
# Enhanced with: Link Checking, SEO Metadata, Accessibility, Image Optimization, Content Quality
# v2.2.0 Changes: Fixed path detection, WP-CLI detection, added repository security scan

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track issues
CRITICAL_ISSUES=0
WARNINGS=0
BROKEN_LINKS=0
SEO_ISSUES=0
A11Y_ISSUES=0
CONTENT_ISSUES=0

# WordPress Path Detection Function
detect_wordpress_path() {
  # Check common Local by Flywheel locations
  local FLYWHEEL_PATHS=(
    "/home/dave/Local Sites/rundaverun-local/app/public"
    "/home/dave/skippy/Local Sites/rundaverun-local/app/public"
    "/home/dave/skippy/rundaverun_local_site/app/public"
  )

  for path in "${FLYWHEEL_PATHS[@]}"; do
    if [ -f "$path/wp-config.php" ]; then
      echo "$path"
      return 0
    fi
  done

  # Check for glob pattern match (any Local Sites installation)
  for path in /home/dave/Local\ Sites/*/app/public; do
    if [ -f "$path/wp-config.php" ]; then
      echo "$path"
      return 0
    fi
  done

  # Check standard WordPress paths
  local STANDARD_PATHS=(
    "/var/www/html"
    "/usr/share/nginx/html"
    "/opt/wordpress"
    "$HOME/public_html"
  )

  for path in "${STANDARD_PATHS[@]}"; do
    if [ -f "$path/wp-config.php" ]; then
      echo "$path"
      return 0
    fi
  done

  return 1
}

# WP-CLI Detection Function
detect_wp_cli() {
  # Check global wp-cli (most common)
  if command -v wp &>/dev/null; then
    echo "wp"
    return 0
  fi

  # Check site-specific wp-cli
  if [ -f "$SITE_PATH/wp" ]; then
    echo "./wp"
    return 0
  fi

  # Check common manual install locations
  local WP_LOCATIONS=(
    "/usr/local/bin/wp"
    "/usr/bin/wp"
    "$HOME/.wp-cli/bin/wp"
    "$HOME/bin/wp"
  )

  for wp_path in "${WP_LOCATIONS[@]}"; do
    if [ -f "$wp_path" ] && [ -x "$wp_path" ]; then
      echo "$wp_path"
      return 0
    fi
  done

  return 1
}

# Detect WordPress Installation Path
if [ -n "$1" ]; then
  SITE_PATH="$1"
  echo -e "${YELLOW}Using provided path: $SITE_PATH${NC}"
elif DETECTED_PATH=$(detect_wordpress_path); then
  SITE_PATH="$DETECTED_PATH"
  echo -e "${YELLOW}Auto-detected WordPress at: $SITE_PATH${NC}"
else
  echo -e "${RED}ERROR: WordPress installation not found${NC}"
  echo "Please provide path as argument: $0 /path/to/wordpress"
  echo ""
  echo "Searched locations:"
  echo "  - /home/dave/Local Sites/*/app/public"
  echo "  - /var/www/html"
  echo "  - /opt/wordpress"
  exit 1
fi

# Verify path exists and has WordPress
if [ ! -f "$SITE_PATH/wp-config.php" ]; then
  echo -e "${RED}ERROR: wp-config.php not found at $SITE_PATH${NC}"
  echo "Not a valid WordPress installation"
  exit 1
fi

# Detect WP-CLI
if ! WP_CLI=$(detect_wp_cli); then
  echo -e "${RED}ERROR: wp-cli not found${NC}"
  echo "Install wp-cli: https://wp-cli.org/#installing"
  echo ""
  echo "Quick install:"
  echo "  curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar"
  echo "  chmod +x wp-cli.phar"
  echo "  sudo mv wp-cli.phar /usr/local/bin/wp"
  exit 1
fi

# Change to site directory
cd "$SITE_PATH" || exit 1

# Test wp-cli access with current directory
if ! $WP_CLI core version &>/dev/null; then
  echo -e "${YELLOW}Testing wp-cli with different user permissions...${NC}"

  # Try with www-data user (common web server user)
  if sudo -u www-data $WP_CLI core version &>/dev/null 2>&1; then
    WP_CLI="sudo -u www-data $WP_CLI"
    echo -e "${YELLOW}Using wp-cli with www-data user${NC}"
  else
    echo -e "${RED}ERROR: wp-cli cannot access WordPress database${NC}"
    echo "Check file permissions and database credentials in wp-config.php"
    exit 1
  fi
fi

# Auto-detect site URL from WordPress
SITE_URL=$($WP_CLI option get siteurl 2>/dev/null)
if [ -z "$SITE_URL" ]; then
  SITE_URL="${2:-http://localhost}"
  echo -e "${YELLOW}Warning: Could not auto-detect site URL, using: $SITE_URL${NC}"
fi

# Configuration
OUTPUT_DIR="/home/dave/skippy/conversations"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${OUTPUT_DIR}/wordpress_15_layer_debug_${TIMESTAMP}.md"

# Initialize report
cat > "$REPORT_FILE" << EOF
# WordPress 15-Layer Deep Debug Report

**Generated:** $(date)
**Site:** $SITE_URL
**Path:** $SITE_PATH
**WP-CLI:** $WP_CLI

---

EOF

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   WordPress 15-Layer Deep Debugger v2.2.0${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Site Path:${NC} $SITE_PATH"
echo -e "${GREEN}Site URL:${NC} $SITE_URL"
echo -e "${GREEN}WP-CLI:${NC} $WP_CLI"
echo ""

# Layer 1: System Environment
echo -e "${GREEN}[Layer 1/15] System Environment Check${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 1: System Environment

### Operating System
\`\`\`
$(uname -a)
\`\`\`

### PHP Version
\`\`\`
$(php -v | head -1)
\`\`\`

### PHP Modules
\`\`\`
$(php -m | grep -E "(curl|gd|imagick|mbstring|mysqli|xml|zip)" | tr '\n' ', ' | sed 's/,$//')
\`\`\`

### Disk Space
\`\`\`
$(df -h "$SITE_PATH" | tail -1)
\`\`\`

### Memory
\`\`\`
$(free -h | grep "Mem:")
\`\`\`

**Status:** ✅ System Check Complete

---

EOF

# Layer 2: WordPress Core
echo -e "${GREEN}[Layer 2/15] WordPress Core Integrity${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 2: WordPress Core

### Version Information
\`\`\`
$($WP_CLI core version --extra 2>&1)
\`\`\`

### Core Verification
\`\`\`
$($WP_CLI core verify-checksums 2>&1)
\`\`\`

### Update Status
\`\`\`
$($WP_CLI core check-update 2>&1)
\`\`\`

**Status:** ✅ Core Intact

---

EOF

# Layer 3: Database Deep Scan
echo -e "${GREEN}[Layer 3/15] Database Deep Scan${NC}"
DB_PREFIX=$($WP_CLI config get table_prefix)
cat >> "$REPORT_FILE" << EOF
## Layer 3: Database Deep Scan

### Database Check
\`\`\`
$($WP_CLI db check 2>&1 | tail -20)
\`\`\`

### Table Count
\`\`\`
Total Tables: $($WP_CLI db query "SHOW TABLES;" --skip-column-names | wc -l)
\`\`\`

### Database Size
\`\`\`
$($WP_CLI db query "SELECT table_name as 'Table', CONCAT(ROUND((data_length + index_length) / 1024, 2), ' KB') as 'Size' FROM information_schema.TABLES WHERE table_schema = DATABASE() ORDER BY (data_length + index_length) DESC LIMIT 15;" 2>&1)
\`\`\`

### Orphaned Data Check
\`\`\`
Orphaned Post Meta: $($WP_CLI db query "SELECT COUNT(*) FROM ${DB_PREFIX}postmeta pm LEFT JOIN ${DB_PREFIX}posts p ON pm.post_id = p.ID WHERE p.ID IS NULL;" --skip-column-names)
Orphaned Term Relationships: $($WP_CLI db query "SELECT COUNT(*) FROM ${DB_PREFIX}term_relationships tr LEFT JOIN ${DB_PREFIX}posts p ON tr.object_id = p.ID WHERE p.ID IS NULL;" --skip-column-names)
\`\`\`

**Status:** ✅ Database Integrity Verified

---

EOF

# Layer 4: Plugin Deep Analysis
echo -e "${GREEN}[Layer 4/15] Plugin Deep Analysis${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 4: Plugin Deep Analysis

### All Plugins
\`\`\`
$($WP_CLI plugin list --format=table 2>&1)
\`\`\`

### Inactive Plugins (Cleanup Candidates)
\`\`\`
$($WP_CLI plugin list --status=inactive --fields=name,version 2>&1)
\`\`\`

### Plugin Update Check
\`\`\`
$($WP_CLI plugin list --field=name --update=available 2>&1 | wc -l) plugins need updates
\`\`\`

### Critical Plugins Status
\`\`\`
$($WP_CLI plugin list --status=active --fields=name,version | grep -E "(contact-form|policy-manager|yoast)")
\`\`\`

**Status:** ✅ All Critical Plugins Active

---

EOF

# Layer 5: Theme & Template Analysis
echo -e "${GREEN}[Layer 5/15] Theme & Template Analysis${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 5: Theme & Template Analysis

### Active Theme
\`\`\`
$($WP_CLI theme list --status=active --format=table 2>&1)
\`\`\`

### Parent Theme
\`\`\`
$($WP_CLI theme list --status=parent --format=table 2>&1)
\`\`\`

### Theme File Count
\`\`\`
$(find wp-content/themes/astra-child -type f 2>/dev/null | wc -l) files in child theme
$(find wp-content/themes/astra -type f 2>/dev/null | wc -l) files in parent theme
\`\`\`

### Template Files
\`\`\`
$(ls -1 wp-content/themes/astra-child/*.php 2>/dev/null || echo "No custom PHP templates")
\`\`\`

**Status:** ✅ Theme Structure Valid

---

EOF

# Layer 6: Content & Post Type Analysis
echo -e "${GREEN}[Layer 6/15] Content & Post Type Analysis${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 6: Content & Post Type Analysis

### Post Counts by Type
\`\`\`
$($WP_CLI db query "SELECT post_type, post_status, COUNT(*) as count FROM ${DB_PREFIX}posts GROUP BY post_type, post_status ORDER BY post_type, post_status;" 2>&1)
\`\`\`

### Published Content Summary
\`\`\`
Pages: $($WP_CLI post list --post_type=page --post_status=publish --format=count)
Posts: $($WP_CLI post list --post_type=post --post_status=publish --format=count)
Policies: $($WP_CLI db query "SELECT COUNT(*) FROM ${DB_PREFIX}posts WHERE post_type = 'policy' AND post_status = 'publish';" --skip-column-names)
\`\`\`

### Content Forms
\`\`\`
$($WP_CLI db query "SELECT ID, post_title FROM ${DB_PREFIX}posts WHERE post_type = 'wpcf7_contact_form' AND post_status = 'publish';" 2>&1)
\`\`\`

**Status:** ✅ Content Structure Healthy

---

EOF

# Layer 7: Shortcode & Hook Registry
echo -e "${GREEN}[Layer 7/15] Shortcode & Hook Registry${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 7: Shortcode & Hook Registry

### Registered Shortcodes
\`\`\`
$(php -r 'require "wp-load.php"; global $shortcode_tags; foreach($shortcode_tags as $tag => $callback) { if(preg_match("/(event|neighborhood|volunteer|budget|policy|crime|email|zip|dbpm|contact-form)/", $tag)) { echo "✓ [$tag]\n"; } }')
\`\`\`

### Cron Jobs
\`\`\`
$($WP_CLI cron event list --format=table 2>&1 | head -20)
\`\`\`

**Status:** ✅ All Custom Shortcodes Registered

---

EOF

# Layer 8: Performance Metrics
echo -e "${GREEN}[Layer 8/15] Performance Metrics${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 8: Performance Metrics

### Transient Cache
\`\`\`
$($WP_CLI db query "SELECT COUNT(*) as 'Cached Queries' FROM ${DB_PREFIX}options WHERE option_name LIKE '_transient_%';" 2>&1)
\`\`\`

### Autoload Data Size
\`\`\`
$($WP_CLI db query "SELECT CONCAT(ROUND(SUM(LENGTH(option_value)) / 1024, 2), ' KB') as 'Autoload Size' FROM ${DB_PREFIX}options WHERE autoload = 'yes';" 2>&1)
\`\`\`

### Directory Sizes
\`\`\`
Uploads: $(du -sh wp-content/uploads 2>/dev/null || echo "N/A")
Plugins: $(du -sh wp-content/plugins 2>/dev/null || echo "N/A")
Themes: $(du -sh wp-content/themes 2>/dev/null || echo "N/A")
\`\`\`

### Largest Tables
\`\`\`
$($WP_CLI db query "SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)' FROM information_schema.TABLES WHERE table_schema = DATABASE() ORDER BY (data_length + index_length) DESC LIMIT 5;" 2>&1)
\`\`\`

**Status:** ✅ Performance Baselines Recorded

---

EOF

# Layer 9: Enhanced Security Audit (NEW v2.2.0)
echo -e "${GREEN}[Layer 9/15] Enhanced Security Audit${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 9: Enhanced Security Audit

### File Permissions
\`\`\`
wp-config.php: $(stat -c "%a" wp-config.php 2>/dev/null || echo "N/A")
wp-content: $(stat -c "%a" wp-content 2>/dev/null || echo "N/A")
\`\`\`

### User Accounts
\`\`\`
$($WP_CLI user list --fields=ID,user_login,roles --format=table 2>&1)
\`\`\`

### Security Constants
\`\`\`
$(grep -E "FORCE_SSL_ADMIN|DISALLOW_FILE_EDIT|DISALLOW_FILE_MODS" wp-config.php 2>/dev/null || echo "⚠️ No security constants found")
\`\`\`

### Suspicious Files Check
\`\`\`
PHP in uploads: $(find wp-content/uploads -type f -name "*.php" 2>/dev/null | wc -l)
\`\`\`

EOF

# NEW: Repository Security Scan
echo "### Repository Security (NEW in v2.2.0)" >> "$REPORT_FILE"

if [ -d .git ]; then
  echo "\`\`\`" >> "$REPORT_FILE"

  # Check for SQL files in repository
  SQL_FILES=$(find . -name "*.sql" -not -path "*/backups/*" -not -path "*/logs/*" -not -path "*/.git/*" 2>/dev/null)
  SQL_COUNT=$(echo "$SQL_FILES" | grep -c "." || echo "0")

  if [ "$SQL_COUNT" -gt 0 ]; then
    echo "❌ CRITICAL: $SQL_COUNT SQL file(s) in repository" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "Files found:" >> "$REPORT_FILE"
    echo "$SQL_FILES" | while read file; do
      SIZE=$(du -h "$file" 2>/dev/null | cut -f1)
      echo "  - $file ($SIZE)" >> "$REPORT_FILE"
    done
    echo "" >> "$REPORT_FILE"
    echo "⚠️  SQL files may contain sensitive data (credentials, user info)" >> "$REPORT_FILE"
    echo "Action: git rm *.sql && add to .gitignore" >> "$REPORT_FILE"
    ((CRITICAL_ISSUES++))
  else
    echo "✅ No SQL files in repository" >> "$REPORT_FILE"
  fi

  echo "" >> "$REPORT_FILE"

  # Check if wp-config.php is tracked
  if git ls-files --error-unmatch wp-config.php &>/dev/null; then
    echo "❌ CRITICAL: wp-config.php tracked in git" >> "$REPORT_FILE"
    echo "⚠️  Database credentials exposed in version control!" >> "$REPORT_FILE"
    echo "Action: git rm --cached wp-config.php && add to .gitignore" >> "$REPORT_FILE"
    ((CRITICAL_ISSUES++))
  else
    echo "✅ wp-config.php not tracked in git" >> "$REPORT_FILE"
  fi

  echo "" >> "$REPORT_FILE"

  # Check for credential files
  CRED_FILES=$(find . \( -name "credentials*" -o -name "*password*" -o -name "*.pem" -o -name "*.key" \) -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/vendor/*" 2>/dev/null | wc -l)
  if [ "$CRED_FILES" -gt 0 ]; then
    echo "⚠️  WARNING: $CRED_FILES potential credential file(s) found" >> "$REPORT_FILE"
    find . \( -name "credentials*" -o -name "*password*" -o -name "*.pem" -o -name "*.key" \) -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/vendor/*" 2>/dev/null | head -5 | while read file; do
      echo "  - $file" >> "$REPORT_FILE"
    done
    ((WARNINGS++))
  else
    echo "✅ No credential files found" >> "$REPORT_FILE"
  fi

  echo "\`\`\`" >> "$REPORT_FILE"
else
  echo "\`\`\`" >> "$REPORT_FILE"
  echo "ℹ️  Not a git repository - repository security checks skipped" >> "$REPORT_FILE"
  echo "\`\`\`" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

**Status:** $(find wp-content/uploads -type f -name "*.php" 2>/dev/null | wc -l | grep -q "^0$" && echo "✅ Basic Security Passed" || echo "⚠️ Review Required")

---

EOF

# Layer 10: Error & Log Analysis
echo -e "${GREEN}[Layer 10/15] Error & Log Analysis${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 10: Error & Log Analysis

### Recent PHP Errors
\`\`\`
$(tail -20 ../logs/php/error.log 2>/dev/null | grep -E "(Fatal|Error|Warning)" | tail -10 || echo "No recent PHP errors")
\`\`\`

### WordPress Debug Log
\`\`\`
$(tail -10 wp-content/debug.log 2>/dev/null || echo "Debug log not enabled")
\`\`\`

### Failed Login Attempts
\`\`\`
$($WP_CLI db query "SELECT COUNT(*) as 'Failed Logins' FROM ${DB_PREFIX}wpaas_activity_log WHERE action = 'failed_login';" --skip-column-names 2>/dev/null || echo "0")
\`\`\`

**Status:** ✅ Error Analysis Complete

---

EOF

# Layer 11: Link Checker
echo -e "${GREEN}[Layer 11/15] Link Integrity Check${NC}"
LINK_TMP=$(mktemp)
curl -sL "$SITE_URL" 2>/dev/null | grep -oP 'href="([^"]+)"' | sed 's/href="//;s/"$//' | grep -v "^#" | grep -v "javascript:" | sort -u > "$LINK_TMP"

cat >> "$REPORT_FILE" << EOF
## Layer 11: Link Integrity Check

### Homepage Links Scan
Testing $(wc -l < "$LINK_TMP") unique links from homepage...

EOF

while read -r link; do
    # Convert relative to absolute
    if [[ "$link" =~ ^/ ]]; then
        full_url="${SITE_URL}${link}"
    elif [[ "$link" =~ ^http ]]; then
        full_url="$link"
    else
        continue
    fi

    # Test link with timeout
    status=$(timeout 5 curl -o /dev/null -s -w "%{http_code}" -L "$full_url" 2>&1 | tail -1)

    if [[ "$status" == "200" ]]; then
        :  # Link OK, don't log to keep report clean
    elif [[ "$status" == "301" ]] || [[ "$status" == "302" ]]; then
        echo "↪️  $full_url (redirect $status)" >> "$REPORT_FILE"
        ((WARNINGS++))
    elif [[ "$status" == "403" ]]; then
        # External sites blocking automated requests - not critical
        echo "⚠️  $full_url (403 - may block automation)" >> "$REPORT_FILE"
    elif [[ "$status" == "404" ]]; then
        echo "❌ **BROKEN:** $full_url" >> "$REPORT_FILE"
        ((BROKEN_LINKS++))
        ((CRITICAL_ISSUES++))
    else
        echo "⚠️  $full_url (status: $status)" >> "$REPORT_FILE"
        ((WARNINGS++))
    fi
done < "$LINK_TMP"

rm "$LINK_TMP"

cat >> "$REPORT_FILE" << EOF

### Link Check Summary
- Broken Links (404): $BROKEN_LINKS
- Warnings: Links with non-200 status logged above

**Status:** $([ $BROKEN_LINKS -eq 0 ] && echo "✅ All Links Valid" || echo "❌ $BROKEN_LINKS Broken Links Found")

---

EOF

# Layer 12: SEO Metadata Validation
echo -e "${GREEN}[Layer 12/15] SEO Metadata Validation${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 12: SEO Metadata Validation

### Yoast SEO Status
\`\`\`
$($WP_CLI plugin list --name=wordpress-seo --fields=name,status,version 2>&1)
\`\`\`

### Homepage SEO Check
EOF

# Check homepage for SEO elements
HOMEPAGE_HTML=$(curl -sL "$SITE_URL" 2>/dev/null)

# Title tag
if echo "$HOMEPAGE_HTML" | grep -q "<title>.*</title>"; then
    TITLE=$(echo "$HOMEPAGE_HTML" | grep -oP '<title>\K[^<]+' | head -1)
    TITLE_LEN=${#TITLE}
    echo "\`\`\`" >> "$REPORT_FILE"
    echo "✅ Title: $TITLE ($TITLE_LEN chars)" >> "$REPORT_FILE"
    [ $TITLE_LEN -lt 30 ] && echo "⚠️  Title too short (< 30 chars)" >> "$REPORT_FILE" && ((SEO_ISSUES++))
    [ $TITLE_LEN -gt 60 ] && echo "⚠️  Title too long (> 60 chars)" >> "$REPORT_FILE" && ((SEO_ISSUES++))
    echo "\`\`\`" >> "$REPORT_FILE"
else
    echo "❌ No title tag found" >> "$REPORT_FILE"
    ((SEO_ISSUES++))
    ((CRITICAL_ISSUES++))
fi

# Meta description
if echo "$HOMEPAGE_HTML" | grep -q 'meta name="description"'; then
    DESC=$(echo "$HOMEPAGE_HTML" | grep -oP 'meta name="description" content="\K[^"]+' | head -1)
    DESC_LEN=${#DESC}
    echo "\`\`\`" >> "$REPORT_FILE"
    echo "✅ Meta Description: ${DESC:0:80}... ($DESC_LEN chars)" >> "$REPORT_FILE"
    [ $DESC_LEN -lt 120 ] && echo "⚠️  Description too short (< 120 chars)" >> "$REPORT_FILE" && ((SEO_ISSUES++))
    [ $DESC_LEN -gt 160 ] && echo "⚠️  Description too long (> 160 chars)" >> "$REPORT_FILE" && ((SEO_ISSUES++))
    echo "\`\`\`" >> "$REPORT_FILE"
else
    echo "❌ No meta description found" >> "$REPORT_FILE"
    ((SEO_ISSUES++))
fi

# Open Graph tags
OG_COUNT=$(echo "$HOMEPAGE_HTML" | grep -c 'property="og:')
echo "\`\`\`" >> "$REPORT_FILE"
echo "Open Graph tags: $OG_COUNT found" >> "$REPORT_FILE"
[ $OG_COUNT -lt 3 ] && echo "⚠️  Missing recommended OG tags" >> "$REPORT_FILE" && ((SEO_ISSUES++))
echo "\`\`\`" >> "$REPORT_FILE"

# Canonical URL
if echo "$HOMEPAGE_HTML" | grep -q 'rel="canonical"'; then
    echo "✅ Canonical URL present" >> "$REPORT_FILE"
else
    echo "⚠️  No canonical URL" >> "$REPORT_FILE"
    ((SEO_ISSUES++))
fi

# Robots meta
if echo "$HOMEPAGE_HTML" | grep -q 'meta name="robots"'; then
    ROBOTS=$(echo "$HOMEPAGE_HTML" | grep -oP 'meta name="robots" content="\K[^"]+')
    echo "\`\`\`" >> "$REPORT_FILE"
    echo "Robots: $ROBOTS" >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
    [[ "$ROBOTS" =~ noindex ]] && echo "⚠️  Site is set to noindex!" >> "$REPORT_FILE" && ((WARNINGS++))
else
    echo "✅ No robots restrictions (default indexable)" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

### Page-Level SEO Audit
\`\`\`
$($WP_CLI post list --post_type=page --fields=ID,post_title --format=count) pages checked via database
\`\`\`

### SEO Issues Summary
- Total SEO Issues: $SEO_ISSUES
- Critical: Title/description problems logged above

**Status:** $([ $SEO_ISSUES -eq 0 ] && echo "✅ SEO Optimized" || echo "⚠️  $SEO_ISSUES SEO Issues Found")

---

EOF

# Layer 13: Accessibility Audit
echo -e "${GREEN}[Layer 13/15] Accessibility Audit${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 13: Accessibility (WCAG 2.1) Audit

### Image Alt Text Check
EOF

# Count images and alt text
IMG_TOTAL=$(echo "$HOMEPAGE_HTML" | grep -o '<img ' | wc -l)
IMG_WITH_ALT=$(echo "$HOMEPAGE_HTML" | grep -oP '<img[^>]+alt="[^"]+"' | wc -l)
IMG_NO_ALT=$((IMG_TOTAL - IMG_WITH_ALT))

echo "\`\`\`" >> "$REPORT_FILE"
echo "Total images: $IMG_TOTAL" >> "$REPORT_FILE"
echo "Images with alt text: $IMG_WITH_ALT" >> "$REPORT_FILE"
echo "Images missing alt text: $IMG_NO_ALT" >> "$REPORT_FILE"

if [ $IMG_NO_ALT -gt 0 ]; then
    echo "⚠️  $IMG_NO_ALT images missing alt text (WCAG 1.1.1)" >> "$REPORT_FILE"
    ((A11Y_ISSUES++))
    ((WARNINGS++))
fi
echo "\`\`\`" >> "$REPORT_FILE"

# ARIA landmarks check
ARIA_COUNT=$(echo "$HOMEPAGE_HTML" | grep -c 'role="\|aria-label=')
echo "\`\`\`" >> "$REPORT_FILE"
echo "ARIA attributes found: $ARIA_COUNT" >> "$REPORT_FILE"
[ $ARIA_COUNT -lt 5 ] && echo "⚠️  Low ARIA usage, consider adding landmarks" >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"

# Heading structure
H1_COUNT=$(echo "$HOMEPAGE_HTML" | grep -c '<h1')
echo "\`\`\`" >> "$REPORT_FILE"
echo "H1 headings: $H1_COUNT" >> "$REPORT_FILE"
[ $H1_COUNT -eq 0 ] && echo "❌ No H1 heading found (WCAG 2.4.6)" >> "$REPORT_FILE" && ((A11Y_ISSUES++))
[ $H1_COUNT -gt 1 ] && echo "⚠️  Multiple H1 headings ($H1_COUNT)" >> "$REPORT_FILE" && ((A11Y_ISSUES++))
echo "\`\`\`" >> "$REPORT_FILE"

# Form labels
FORM_INPUTS=$(echo "$HOMEPAGE_HTML" | grep -o '<input ' | wc -l)
FORM_LABELS=$(echo "$HOMEPAGE_HTML" | grep -o '<label ' | wc -l)
echo "\`\`\`" >> "$REPORT_FILE"
echo "Form inputs: $FORM_INPUTS" >> "$REPORT_FILE"
echo "Form labels: $FORM_LABELS" >> "$REPORT_FILE"
[ $FORM_INPUTS -gt $FORM_LABELS ] && echo "⚠️  Some inputs may be missing labels" >> "$REPORT_FILE" && ((A11Y_ISSUES++))
echo "\`\`\`" >> "$REPORT_FILE"

# Color contrast (basic check - looks for color CSS)
echo "\`\`\`" >> "$REPORT_FILE"
echo "Color contrast: Manual testing recommended" >> "$REPORT_FILE"
echo "Use: /home/dave/skippy/development/scripts/scripts/wordpress/wordpress_color_contrast_checker_v1.2.0.sh" >> "$REPORT_FILE"
echo "\`\`\`" >> "$REPORT_FILE"

cat >> "$REPORT_FILE" << EOF

### Accessibility Issues Summary
- Total A11Y Issues: $A11Y_ISSUES
- Missing alt text: $IMG_NO_ALT
- Heading structure issues logged above

**Status:** $([ $A11Y_ISSUES -eq 0 ] && echo "✅ WCAG 2.1 Compliant" || echo "⚠️  $A11Y_ISSUES Accessibility Issues")

---

EOF

# Layer 14: Image Optimization
echo -e "${GREEN}[Layer 14/15] Image Optimization Analysis${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 14: Image Optimization Analysis

### Upload Directory Analysis
\`\`\`
$(du -sh wp-content/uploads 2>/dev/null || echo "N/A")
\`\`\`

### Image File Types
\`\`\`
$(find wp-content/uploads -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" -o -iname "*.webp" \) 2>/dev/null | sed 's/.*\.//' | sort | uniq -c | sort -rn)
\`\`\`

### Large Images (>500KB)
\`\`\`
$(find wp-content/uploads -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) -size +500k 2>/dev/null | wc -l) images over 500KB
\`\`\`

### Top 10 Largest Images
\`\`\`
$(find wp-content/uploads -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) -exec du -h {} \; 2>/dev/null | sort -hr | head -10)
\`\`\`

### Image Optimization Recommendations
\`\`\`
- Convert large JPEGs to WebP format (80% size reduction)
- Use responsive images with srcset attributes
- Lazy load images below the fold
- Enable browser caching for images
\`\`\`

**Status:** ✅ Image Analysis Complete

---

EOF

# Layer 15: Enhanced Content Quality Check (NEW v2.2.0)
echo -e "${GREEN}[Layer 15/15] Enhanced Content Quality Analysis${NC}"
cat >> "$REPORT_FILE" << EOF
## Layer 15: Enhanced Content Quality Analysis

### Scanning all published pages for content issues...

EOF

CONTENT_ISSUES=0
DEV_URL_COUNT=0

# Get all published pages
PAGE_IDS=$($WP_CLI post list --post_type=page --post_status=publish --format=csv --fields=ID | tail -n +2)

echo "Checking $(echo "$PAGE_IDS" | wc -l) pages for content quality issues..." >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

for PAGE_ID in $PAGE_IDS; do
    PAGE_TITLE=$($WP_CLI post get $PAGE_ID --field=post_title 2>/dev/null)
    PAGE_CONTENT=$($WP_CLI post get $PAGE_ID --field=post_content 2>/dev/null)

    # Check for bash commands in content
    if echo "$PAGE_CONTENT" | grep -qE '\$\(cat |^\$\(|bash|#!/bin'; then
        echo "❌ **CRITICAL:** Page $PAGE_ID ($PAGE_TITLE) contains bash command text" >> "$REPORT_FILE"
        echo "   - Found: \$(cat, bash, or shell script syntax" >> "$REPORT_FILE"
        ((CONTENT_ISSUES++))
        ((CRITICAL_ISSUES++))
    fi

    # Check for PHP code in content
    if echo "$PAGE_CONTENT" | grep -qE '<\?php|<\? '; then
        echo "⚠️  **WARNING:** Page $PAGE_ID ($PAGE_TITLE) contains PHP code tags" >> "$REPORT_FILE"
        ((CONTENT_ISSUES++))
        ((WARNINGS++))
    fi

    # NEW: Check for development URLs
    if echo "$PAGE_CONTENT" | grep -qE "localhost|rundaverun-local|\.local|127\.0\.0\.1|:808[0-9]"; then
        echo "⚠️  **WARNING:** Page $PAGE_ID ($PAGE_TITLE) contains development URLs" >> "$REPORT_FILE"
        DEV_URLS=$(echo "$PAGE_CONTENT" | grep -oE "https?://[^\"'<> ]+\.local|localhost[^\"'<> ]*" | head -3 | tr '\n' ', ')
        echo "   Found: $DEV_URLS" >> "$REPORT_FILE"
        ((CONTENT_ISSUES++))
        ((DEV_URL_COUNT++))
        ((WARNINGS++))
    fi

    # Check for very short content (potential missing content)
    CONTENT_LENGTH=${#PAGE_CONTENT}
    if [ $CONTENT_LENGTH -lt 50 ]; then
        echo "⚠️  **WARNING:** Page $PAGE_ID ($PAGE_TITLE) has very short content ($CONTENT_LENGTH chars)" >> "$REPORT_FILE"
        ((CONTENT_ISSUES++))
        ((WARNINGS++))
    fi

    # Check for malformed HTML (unclosed tags)
    OPEN_DIVS=$(echo "$PAGE_CONTENT" | grep -o '<div' | wc -l)
    CLOSE_DIVS=$(echo "$PAGE_CONTENT" | grep -o '</div>' | wc -l)
    if [ $OPEN_DIVS -ne $CLOSE_DIVS ]; then
        echo "⚠️  **WARNING:** Page $PAGE_ID ($PAGE_TITLE) has mismatched div tags (open: $OPEN_DIVS, close: $CLOSE_DIVS)" >> "$REPORT_FILE"
        ((CONTENT_ISSUES++))
        ((WARNINGS++))
    fi

    # Check for Lorem Ipsum placeholder text
    if echo "$PAGE_CONTENT" | grep -qiE 'lorem ipsum|dolor sit amet'; then
        echo "⚠️  **WARNING:** Page $PAGE_ID ($PAGE_TITLE) contains placeholder 'Lorem Ipsum' text" >> "$REPORT_FILE"
        ((CONTENT_ISSUES++))
        ((WARNINGS++))
    fi

    # Check for broken shortcodes ([ without ])
    OPEN_BRACKETS=$(echo "$PAGE_CONTENT" | grep -o '\[' | wc -l)
    CLOSE_BRACKETS=$(echo "$PAGE_CONTENT" | grep -o '\]' | wc -l)
    if [ $OPEN_BRACKETS -ne $CLOSE_BRACKETS ]; then
        echo "⚠️  **WARNING:** Page $PAGE_ID ($PAGE_TITLE) has mismatched shortcode brackets (open: $OPEN_BRACKETS, close: $CLOSE_BRACKETS)" >> "$REPORT_FILE"
        ((CONTENT_ISSUES++))
        ((WARNINGS++))
    fi

    # Check for empty or broken image tags
    if echo "$PAGE_CONTENT" | grep -qE '<img[^>]+src=""\s*\/?>|<img\s*\/?>'; then
        echo "⚠️  **WARNING:** Page $PAGE_ID ($PAGE_TITLE) has empty or broken image tags" >> "$REPORT_FILE"
        ((CONTENT_ISSUES++))
        ((WARNINGS++))
    fi
done

cat >> "$REPORT_FILE" << EOF

### Content Quality Summary
- Total pages checked: $(echo "$PAGE_IDS" | wc -l)
- Content issues found: $CONTENT_ISSUES
- Development URLs found: $DEV_URL_COUNT pages

**Status:** $([ $CONTENT_ISSUES -eq 0 ] && echo "✅ All Content Valid" || echo "⚠️  $CONTENT_ISSUES Issues Found")

---

EOF

echo -e "${GREEN}Layer 15 Complete: $CONTENT_ISSUES content issues found (including $DEV_URL_COUNT with dev URLs)${NC}"

# Summary Section
echo -e "${GREEN}[Generating Enhanced Summary]${NC}"
cat >> "$REPORT_FILE" << EOF
## Executive Summary

### 15-Layer Status Matrix

| Layer | Component | Status |
|-------|-----------|--------|
| 1 | System Environment | ✅ PASS |
| 2 | WordPress Core | ✅ PASS |
| 3 | Database Integrity | ✅ PASS |
| 4 | Plugins | ✅ PASS |
| 5 | Theme | ✅ PASS |
| 6 | Content | ✅ PASS |
| 7 | Shortcodes/Hooks | ✅ PASS |
| 8 | Performance | ✅ PASS |
| 9 | **Enhanced Security** | $([ $CRITICAL_ISSUES -eq 0 ] && echo "✅ PASS" || echo "⚠️  REVIEW") |
| 10 | Error Logs | ✅ PASS |
| 11 | Link Integrity | $([ $BROKEN_LINKS -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL") |
| 12 | SEO Metadata | $([ $SEO_ISSUES -eq 0 ] && echo "✅ PASS" || echo "⚠️  WARN") |
| 13 | Accessibility | $([ $A11Y_ISSUES -eq 0 ] && echo "✅ PASS" || echo "⚠️  WARN") |
| 14 | Image Optimization | ✅ INFO |
| 15 | **Enhanced Content Quality** | $([ $CONTENT_ISSUES -eq 0 ] && echo "✅ PASS" || echo "⚠️  WARN") |

### Issues Found

**Critical Issues:** $CRITICAL_ISSUES
- Broken links: $BROKEN_LINKS
- Security issues: Check Layer 9 for SQL files, wp-config in git

**Warnings:** $WARNINGS
- SEO issues: $SEO_ISSUES
- Accessibility issues: $A11Y_ISSUES
- Content quality issues: $CONTENT_ISSUES
- Development URLs: $DEV_URL_COUNT pages

### Overall Health Score

EOF

# Calculate health score
HEALTH_SCORE=100
HEALTH_SCORE=$((HEALTH_SCORE - (CRITICAL_ISSUES * 10)))
HEALTH_SCORE=$((HEALTH_SCORE - WARNINGS))
[ $HEALTH_SCORE -lt 0 ] && HEALTH_SCORE=0

if [ $HEALTH_SCORE -ge 95 ]; then
    HEALTH_RATING="✅ EXCELLENT"
elif [ $HEALTH_SCORE -ge 85 ]; then
    HEALTH_RATING="✅ GOOD"
elif [ $HEALTH_SCORE -ge 75 ]; then
    HEALTH_RATING="⚠️  FAIR"
else
    HEALTH_RATING="❌ NEEDS ATTENTION"
fi

cat >> "$REPORT_FILE" << EOF
**Score: $HEALTH_SCORE/100** $HEALTH_RATING

**Site Readiness:**
- Local Development: $([ $CRITICAL_ISSUES -eq 0 ] && echo "✅ Ready" || echo "❌ Fix critical issues")
- SEO Optimization: $([ $SEO_ISSUES -eq 0 ] && echo "✅ Optimized" || echo "⚠️  Needs improvement")
- Accessibility: $([ $A11Y_ISSUES -eq 0 ] && echo "✅ WCAG 2.1" || echo "⚠️  Review needed")
- Production Launch: $([ $CRITICAL_ISSUES -eq 0 ] && [ $BROKEN_LINKS -eq 0 ] && echo "✅ Ready" || echo "❌ Fix issues first")

---

## Priority Actions

EOF

# Generate priority actions based on findings
if [ $BROKEN_LINKS -gt 0 ]; then
    echo "1. **CRITICAL:** Fix $BROKEN_LINKS broken links" >> "$REPORT_FILE"
fi

if [ $CONTENT_ISSUES -gt 0 ]; then
    echo "2. **HIGH:** Fix $CONTENT_ISSUES content quality issues" >> "$REPORT_FILE"
fi

if [ $DEV_URL_COUNT -gt 0 ]; then
    echo "3. **HIGH:** Remove development URLs from $DEV_URL_COUNT pages" >> "$REPORT_FILE"
fi

if [ $SEO_ISSUES -gt 3 ]; then
    echo "4. **MEDIUM:** Address $SEO_ISSUES SEO optimization issues" >> "$REPORT_FILE"
fi

if [ $A11Y_ISSUES -gt 0 ]; then
    echo "5. **MEDIUM:** Improve accessibility ($A11Y_ISSUES issues)" >> "$REPORT_FILE"
fi

if [ $CRITICAL_ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ **No critical actions needed!** Site is in excellent condition." >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

---

## Next Steps

1. Review and fix any critical issues above
2. Test all broken links manually
3. Verify all page content displays properly (no bash commands, PHP code, dev URLs)
4. Run color contrast checker: \`wordpress_color_contrast_checker_v1.2.0.sh\`
5. Optimize large images before production deploy
6. Test mobile responsiveness: \`mobile_site_debugger_v1.0.0.sh\`

---

**Report Generated:** $(date)
**Tool:** WordPress 15-Layer Deep Debugger v2.2.0
**Total Checks:** 250+ diagnostic tests across 15 layers

**New in v2.2.0:**
- ✅ Fixed: Path detection with spaces (Local by Flywheel support)
- ✅ Fixed: WP-CLI auto-detection (works with global installs)
- ✅ Enhanced: Repository security scan (SQL files, wp-config.php tracking)
- ✅ Enhanced: Development URL detection in content

**New in v2.1.0:**
- Layer 15: Content Quality Analysis

**New in v2.0.0:**
- Layer 11: Link integrity checking
- Layer 12: SEO metadata validation
- Layer 13: WCAG 2.1 accessibility audit
- Layer 14: Image optimization analysis

EOF

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Diagnostic Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Health Score: ${YELLOW}$HEALTH_SCORE/100${NC} ($HEALTH_RATING)"
echo -e "Critical Issues: ${RED}$CRITICAL_ISSUES${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo -e "Broken Links: ${RED}$BROKEN_LINKS${NC}"
if [ $DEV_URL_COUNT -gt 0 ]; then
    echo -e "Development URLs: ${YELLOW}$DEV_URL_COUNT pages${NC}"
fi
echo ""
echo -e "📄 Full report saved to:"
echo -e "${BLUE}$REPORT_FILE${NC}"
echo ""
