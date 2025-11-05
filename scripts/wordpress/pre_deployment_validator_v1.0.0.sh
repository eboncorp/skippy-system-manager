#!/bin/bash
# WordPress Pre-Deployment Validator v1.0.0
# Comprehensive validation before deploying to production
# Part of: Skippy Enhancement Project - TIER 1 Priority
# Author: Claude (Skippy Enhancement Project)
# Created: 2025-11-04
#
# This validator would have prevented:
# - False firefighter claims
# - Budget inconsistencies across 6+ documents
# - Broken links (19.7% failure rate)
# - Triple apostrophe errors
# - Wrong email addresses
# - Missing fact-checking
# - Deployment verification gaps

set -euo pipefail

# Configuration
WORDPRESS_PATH="${WORDPRESS_PATH:-/home/dave/Local Sites/rundaverun-local/app/public}"
FACT_SHEET="${FACT_SHEET:-/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md}"
SKIPPY_BASE="/home/dave/skippy"
REPORT_DIR="${SKIPPY_BASE}/conversations/deployment_validation_reports"
LOG_DIR="${SKIPPY_BASE}/logs/deployment_validation"
ERROR_LOG="${SKIPPY_BASE}/conversations/error_logs/$(date +%Y-%m)/$(date +%Y%m%d_%H%M%S)_deployment_validation.log"
VALIDATION_REPORT="${REPORT_DIR}/deployment_validation_$(date +%Y%m%d_%H%M%S).md"

# Validation thresholds
MAX_BROKEN_LINKS=0          # Zero tolerance for broken links
MAX_FACTUAL_ERRORS=0        # Zero tolerance for factual errors
MAX_BUDGET_ERRORS=0         # Zero tolerance for budget inconsistencies
MAX_CRITICAL_ISSUES=0       # Zero tolerance for critical issues
WARN_SPELLING_ERRORS=10     # Warning threshold for spelling

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create directories
mkdir -p "$REPORT_DIR" "$LOG_DIR" "$(dirname "$ERROR_LOG")"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_DIR}/validator.log"
}

log_error() {
    echo "[ERROR] $1" | tee -a "$ERROR_LOG"
}

# Load fact sheet data
load_fact_sheet() {
    if [ ! -f "$FACT_SHEET" ]; then
        log_error "CRITICAL: Fact sheet not found at $FACT_SHEET"
        echo -e "${RED}✗ CRITICAL: Cannot validate without fact sheet${NC}"
        exit 1
    fi

    log "Loading fact sheet: $FACT_SHEET"

    # Extract key facts (adjust patterns based on actual fact sheet format)
    CANDIDATE_NAME=$(grep -i "full name" "$FACT_SHEET" | head -1 || echo "Dave Biggers")
    CANDIDATE_AGE=$(grep -i "age" "$FACT_SHEET" | grep -oP '\d+' | head -1 || echo "41")
    MARITAL_STATUS=$(grep -i "marital\|married" "$FACT_SHEET" | head -1 || echo "NOT married")
    HAS_CHILDREN=$(grep -i "children" "$FACT_SHEET" | head -1 || echo "NO children")
    TOTAL_BUDGET=$(grep -i "campaign budget\|total budget" "$FACT_SHEET" | grep -oP '\$[\d.]+[BMK]' | head -1 || echo "\$1.2B")

    # Policy-specific facts
    SUBSTATION_BUDGET=$(grep -i "substation" "$FACT_SHEET" | grep -oP '\$[\d.]+M' | head -1 || echo "\$77.4M")
    WELLNESS_BUDGET=$(grep -i "wellness.*investment\|wellness centers" "$FACT_SHEET" | grep -oP '\$[\d.]+M' | head -1 || echo "\$34.2M")
    WELLNESS_ROI=$(grep -i "wellness.*ROI\|saved per.*spent" "$FACT_SHEET" | grep -oP '\$[\d.]+' | head -1 || echo "\$1.80")
    PARTICIPATORY_BUDGET=$(grep -i "participatory budget" "$FACT_SHEET" | grep -oP '\$[\d]+M' | head -1 || echo "\$15M")
    POLICY_COUNT=$(grep -i "policy documents\|total.*policies" "$FACT_SHEET" | grep -oP '\d+' | head -1 || echo "42")

    # Email addresses
    VALID_EMAILS=$(grep -i "@rundaverun.org" "$FACT_SHEET" | grep -oP '[a-zA-Z0-9._%+-]+@rundaverun\.org' || echo "dave@rundaverun.org info@rundaverun.org")

    # URLs
    SITE_URL="https://rundaverun.org"

    log "Fact sheet loaded successfully"
}

# Start report
cat > "$VALIDATION_REPORT" <<EOF
# WordPress Pre-Deployment Validation Report

**Validation Date:** $(date)
**Validator Version:** 1.0.0
**WordPress Path:** $WORDPRESS_PATH
**Fact Sheet:** $FACT_SHEET

---

## Validation Summary

EOF

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  WordPress Pre-Deployment Validator v1.0.0       ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

log "Starting WordPress pre-deployment validation"

# Change to WordPress directory
cd "$WORDPRESS_PATH" || {
    log_error "Cannot access WordPress directory: $WORDPRESS_PATH"
    exit 1
}

# Track validation results
CRITICAL_ERRORS=0
HIGH_ERRORS=0
MEDIUM_ERRORS=0
LOW_ERRORS=0
WARNINGS=0
CHECKS_PASSED=0
CHECKS_FAILED=0

# Load fact sheet
load_fact_sheet

#═══════════════════════════════════════════════════════════════
# CHECK 1: Factual Content Validation
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[1/12] Validating factual content...${NC}"

log "Checking for factual errors"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 1. Factual Content Validation

EOF

FACTUAL_ERRORS=0

# Check for false "firefighter" claim
FIREFIGHTER_MENTIONS=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -ci "firefighter" 2>/dev/null || echo "0")
FIREFIGHTER_MENTIONS=$(echo "$FIREFIGHTER_MENTIONS" | tr -d '\n' | grep -o '[0-9]*' | head -1)
FIREFIGHTER_MENTIONS=${FIREFIGHTER_MENTIONS:-0}

if [ "$FIREFIGHTER_MENTIONS" -gt 0 ]; then
    echo -e "${RED}✗ CRITICAL: Found 'firefighter' mentions ($FIREFIGHTER_MENTIONS)${NC}"
    log_error "CRITICAL: Firefighter mentions found (Dave was never a firefighter)"
    CRITICAL_ERRORS=$((CRITICAL_ERRORS + 1))
    FACTUAL_ERRORS=$((FACTUAL_ERRORS + 1))

    # List posts with firefighter mentions
    FIREFIGHTER_POSTS=$(wp post list --post_type=any --format=ids | while read id; do
        if wp post get "$id" --field=post_content 2>/dev/null | grep -qi "firefighter"; then
            echo "- Post $id: $(wp post get "$id" --field=post_title 2>/dev/null || echo 'Unknown')"
        fi
    done)

    cat >> "$VALIDATION_REPORT" <<EOF
### ❌ CRITICAL: False "Firefighter" Claims

**Status:** FAILED
**Severity:** CRITICAL
**Count:** $FIREFIGHTER_MENTIONS mentions found

**Posts with incorrect claims:**
$FIREFIGHTER_POSTS

**Correct Information:** Dave Biggers is a public safety expert and policy developer, NOT a former firefighter.

**Action Required:** Remove all firefighter references before deployment.

EOF
else
    echo -e "${GREEN}✓ No false firefighter claims${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))

    cat >> "$VALIDATION_REPORT" <<EOF
### ✓ Biographical Information

**Status:** PASSED
No false firefighter claims found.

EOF
fi

# Check for "fire stations" vs "mini police substations"
FIRE_STATION_WRONG=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -ci "fire stations in every" 2>/dev/null || echo "0")
FIRE_STATION_WRONG=$(echo "$FIRE_STATION_WRONG" | tr -d '\n' | grep -o '[0-9]*' | head -1)
FIRE_STATION_WRONG=${FIRE_STATION_WRONG:-0}

if [ "$FIRE_STATION_WRONG" -gt 0 ]; then
    echo -e "${RED}✗ Found incorrect 'fire stations' terminology ($FIRE_STATION_WRONG)${NC}"
    CRITICAL_ERRORS=$((CRITICAL_ERRORS + 1))
    FACTUAL_ERRORS=$((FACTUAL_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ❌ Incorrect Terminology: "Fire Stations"

**Status:** FAILED
**Severity:** CRITICAL
**Count:** $FIRE_STATION_WRONG instances

**Issue:** Content refers to "fire stations" when it should say "mini police substations."

**Action Required:** Replace all instances with correct terminology.

EOF
else
    echo -e "${GREEN}✓ Correct substation terminology${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

# Check marital status / children claims
MARRIED_MENTIONS=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Ei "married|spouse|wife" | wc -l 2>/dev/null || echo "0")
MARRIED_MENTIONS=$(echo "$MARRIED_MENTIONS" | tr -d '\n' | grep -o '[0-9]*' | head -1)
MARRIED_MENTIONS=${MARRIED_MENTIONS:-0}

CHILDREN_MENTIONS=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Ei "children|kids|son|daughter" | wc -l 2>/dev/null || echo "0")
CHILDREN_MENTIONS=$(echo "$CHILDREN_MENTIONS" | tr -d '\n' | grep -o '[0-9]*' | head -1)
CHILDREN_MENTIONS=${CHILDREN_MENTIONS:-0}

if [ "$MARRIED_MENTIONS" -gt 0 ] || [ "$CHILDREN_MENTIONS" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Warning: Found family status mentions (married: $MARRIED_MENTIONS, children: $CHILDREN_MENTIONS)${NC}"
    WARNINGS=$((WARNINGS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ⚠ Family Status Mentions

**Status:** WARNING
**Married mentions:** $MARRIED_MENTIONS
**Children mentions:** $CHILDREN_MENTIONS

**Correct Information:** Dave is NOT married and has NO children.

**Action:** Manually review these mentions to ensure accuracy.

EOF
fi

#═══════════════════════════════════════════════════════════════
# CHECK 2: Budget Consistency Validation
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[2/12] Validating budget figures...${NC}"

log "Checking budget consistency"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 2. Budget Consistency Validation

EOF

BUDGET_ERRORS=0

# Check for wrong substation budget
WRONG_SUBSTATION=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Eo '\$[0-9.]+M' | grep -v "$SUBSTATION_BUDGET" | grep -Ei "substation" -c 2>/dev/null || echo "0")
WRONG_SUBSTATION=$(echo "$WRONG_SUBSTATION" | tr -d '\n' | grep -o '[0-9]*' | head -1)
WRONG_SUBSTATION=${WRONG_SUBSTATION:-0}

# Check total budget mentions
BUDGET_MENTIONS=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Eo '\$1\.2B|\$1\.2 billion' -c 2>/dev/null || echo "0")
BUDGET_MENTIONS=$(echo "$BUDGET_MENTIONS" | tr -d '\n' | grep -o '[0-9]*' | head -1)
BUDGET_MENTIONS=${BUDGET_MENTIONS:-0}

echo -e "${GREEN}✓ Found $BUDGET_MENTIONS total budget mentions${NC}"

# Check for wellness center budget inconsistencies
WELLNESS_MENTIONS=$(wp post list --post_type=any --format=ids | while read id; do
    CONTENT=$(wp post get "$id" --field=post_content 2>/dev/null || echo "")
    if echo "$CONTENT" | grep -qi "wellness"; then
        BUDGET_VALS=$(echo "$CONTENT" | grep -Eo '\$[0-9.]+M' | sort -u)
        if echo "$BUDGET_VALS" | grep -qv "$WELLNESS_BUDGET"; then
            echo "Post $id: Found wellness budget variations: $(echo $BUDGET_VALS | tr '\n' ' ')"
        fi
    fi
done)

if [ -n "$WELLNESS_MENTIONS" ]; then
    echo -e "${YELLOW}⚠ Wellness budget inconsistencies found${NC}"
    BUDGET_ERRORS=$((BUDGET_ERRORS + 1))
    HIGH_ERRORS=$((HIGH_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ⚠ Wellness Center Budget Inconsistencies

**Status:** FAILED
**Severity:** HIGH
**Correct Value:** $WELLNESS_BUDGET

**Inconsistent posts:**
$WELLNESS_MENTIONS

**Action Required:** Standardize all wellness center budget references to $WELLNESS_BUDGET.

EOF
else
    echo -e "${GREEN}✓ Wellness budget consistent${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

# Check wellness ROI
WRONG_ROI=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Ei "wellness.*\$3\.00|\$3 saved" -c 2>/dev/null || echo "0")
WRONG_ROI=$(echo "$WRONG_ROI" | tr -d '\n' | grep -o '[0-9]*' | head -1)
WRONG_ROI=${WRONG_ROI:-0}

if [ "$WRONG_ROI" -gt 0 ]; then
    echo -e "${RED}✗ Found incorrect wellness ROI ($WRONG_ROI instances of \$3.00 instead of $WELLNESS_ROI)${NC}"
    BUDGET_ERRORS=$((BUDGET_ERRORS + 1))
    CRITICAL_ERRORS=$((CRITICAL_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ❌ Incorrect Wellness Center ROI

**Status:** FAILED
**Severity:** CRITICAL
**Incorrect Value:** \$3.00 saved per dollar
**Correct Value:** $WELLNESS_ROI saved per dollar
**Instances:** $WRONG_ROI

**Action Required:** Correct all ROI figures to $WELLNESS_ROI.

EOF
else
    echo -e "${GREEN}✓ Wellness ROI correct${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

# Check participatory budgeting
WRONG_PARTICIPATORY=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Ei "participatory.*\$5M|\$12M.*participatory" -c 2>/dev/null || echo "0")
WRONG_PARTICIPATORY=$(echo "$WRONG_PARTICIPATORY" | tr -d '\n' | grep -o '[0-9]*' | head -1)
WRONG_PARTICIPATORY=${WRONG_PARTICIPATORY:-0}

if [ "$WRONG_PARTICIPATORY" -gt 0 ]; then
    echo -e "${RED}✗ Found incorrect participatory budget ($WRONG_PARTICIPATORY instances)${NC}"
    BUDGET_ERRORS=$((BUDGET_ERRORS + 1))
    CRITICAL_ERRORS=$((CRITICAL_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ❌ Incorrect Participatory Budgeting Amount

**Status:** FAILED
**Severity:** CRITICAL
**Correct Value:** $PARTICIPATORY_BUDGET
**Instances:** $WRONG_PARTICIPATORY found with wrong amounts

**Action Required:** Standardize to $PARTICIPATORY_BUDGET.

EOF
else
    echo -e "${GREEN}✓ Participatory budget correct${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

#═══════════════════════════════════════════════════════════════
# CHECK 3: Link Validation
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[3/12] Validating internal links...${NC}"

log "Checking for broken links"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 3. Link Validation

EOF

# Extract all internal links
INTERNAL_LINKS=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -oP 'href="(/[^"]*)"' | sort -u)

TOTAL_LINKS=$(echo "$INTERNAL_LINKS" | wc -l)
BROKEN_LINKS=0
BROKEN_LINK_LIST=""

echo "  Testing $TOTAL_LINKS internal links..."

while IFS= read -r link; do
    if [ -n "$link" ]; then
        LINK_PATH=$(echo "$link" | sed 's/href="//; s/"$//')

        # Check if link resolves to a post/page
        if ! wp post list --post_type=any --name="${LINK_PATH##*/}" --format=count 2>/dev/null | grep -q "^[1-9]"; then
            BROKEN_LINKS=$((BROKEN_LINKS + 1))
            BROKEN_LINK_LIST="${BROKEN_LINK_LIST}\n- $LINK_PATH"
        fi
    fi
done <<< "$INTERNAL_LINKS"

if [ "$BROKEN_LINKS" -gt "$MAX_BROKEN_LINKS" ]; then
    echo -e "${RED}✗ Found $BROKEN_LINKS broken links${NC}"
    CRITICAL_ERRORS=$((CRITICAL_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ❌ Broken Internal Links

**Status:** FAILED
**Severity:** CRITICAL
**Total Links Tested:** $TOTAL_LINKS
**Broken Links:** $BROKEN_LINKS
**Failure Rate:** $(( BROKEN_LINKS * 100 / TOTAL_LINKS ))%

**Broken links:**
$(echo -e "$BROKEN_LINK_LIST")

**Action Required:** Fix all broken links before deployment.

EOF
else
    echo -e "${GREEN}✓ All links valid ($TOTAL_LINKS tested)${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ✓ Link Validation

**Status:** PASSED
**Total Links Tested:** $TOTAL_LINKS
**Broken Links:** 0

EOF
fi

#═══════════════════════════════════════════════════════════════
# CHECK 4: Email Address Validation
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[4/12] Validating email addresses...${NC}"

log "Checking email addresses"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 4. Email Address Validation

EOF

# Find all email addresses
ALL_EMAILS=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -oP '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' | sort -u)

INVALID_EMAILS=0
INVALID_EMAIL_LIST=""

while IFS= read -r email; do
    if [ -n "$email" ]; then
        # Check if email is in valid list
        if ! echo "$VALID_EMAILS" | grep -q "$email"; then
            INVALID_EMAILS=$((INVALID_EMAILS + 1))
            INVALID_EMAIL_LIST="${INVALID_EMAIL_LIST}\n- $email"

            # Find which posts contain this email
            POSTS_WITH_EMAIL=$(wp post list --post_type=any --format=ids | while read id; do
                if wp post get "$id" --field=post_content 2>/dev/null | grep -q "$email"; then
                    echo "  Post $id: $(wp post get "$id" --field=post_title 2>/dev/null)"
                fi
            done)

            INVALID_EMAIL_LIST="${INVALID_EMAIL_LIST}\n${POSTS_WITH_EMAIL}"
        fi
    fi
done <<< "$ALL_EMAILS"

if [ "$INVALID_EMAILS" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $INVALID_EMAILS unauthorized email addresses${NC}"
    MEDIUM_ERRORS=$((MEDIUM_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ⚠ Unauthorized Email Addresses

**Status:** WARNING
**Severity:** MEDIUM
**Count:** $INVALID_EMAILS

**Valid emails:** $(echo "$VALID_EMAILS" | tr ' ' ', ')

**Unauthorized emails found:**
$(echo -e "$INVALID_EMAIL_LIST")

**Action Required:** Replace with authorized campaign emails.

EOF
else
    echo -e "${GREEN}✓ All email addresses valid${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ✓ Email Addresses

**Status:** PASSED
All email addresses are authorized.

EOF
fi

#═══════════════════════════════════════════════════════════════
# CHECK 5: URL Validation (http vs https)
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[5/12] Validating URL protocols...${NC}"

log "Checking for insecure HTTP URLs"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 5. URL Protocol Validation

EOF

# Find HTTP URLs (should be HTTPS)
HTTP_URLS=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -oP 'http://rundaverun\.(org|local)' | wc -l 2>/dev/null || echo "0")
HTTP_URLS=$(echo "$HTTP_URLS" | tr -d '\n' | grep -o '[0-9]*' | head -1)
HTTP_URLS=${HTTP_URLS:-0}

if [ "$HTTP_URLS" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $HTTP_URLS insecure HTTP URLs${NC}"
    MEDIUM_ERRORS=$((MEDIUM_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ⚠ Insecure HTTP URLs

**Status:** WARNING
**Severity:** MEDIUM
**Count:** $HTTP_URLS

**Issue:** URLs using http:// instead of https://

**Action Required:** Replace all http:// with https://

EOF
else
    echo -e "${GREEN}✓ All URLs use HTTPS${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ✓ URL Protocols

**Status:** PASSED
All URLs use secure HTTPS protocol.

EOF
fi

#═══════════════════════════════════════════════════════════════
# CHECK 6: Development URL Check
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[6/12] Checking for development URLs...${NC}"

log "Checking for local development URLs"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 6. Development URL Check

EOF

# Find local/dev URLs
DEV_URLS=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -oP '(localhost|127\.0\.0\.1|\.local|rundaverun-local)' | wc -l 2>/dev/null || echo "0")
DEV_URLS=$(echo "$DEV_URLS" | tr -d '\n' | grep -o '[0-9]*' | head -1)
DEV_URLS=${DEV_URLS:-0}

if [ "$DEV_URLS" -gt 0 ]; then
    echo -e "${RED}✗ CRITICAL: Found $DEV_URLS development URLs in content${NC}"
    CRITICAL_ERRORS=$((CRITICAL_ERRORS + 1))

    # Find specific posts
    DEV_URL_POSTS=$(wp post list --post_type=any --format=ids | while read id; do
        if wp post get "$id" --field=post_content 2>/dev/null | grep -qE '(localhost|127\.0\.0\.1|\.local|rundaverun-local)'; then
            echo "- Post $id: $(wp post get "$id" --field=post_title 2>/dev/null)"
        fi
    done)

    cat >> "$VALIDATION_REPORT" <<EOF

### ❌ Development URLs Found

**Status:** FAILED
**Severity:** CRITICAL
**Count:** $DEV_URLS

**Posts with development URLs:**
$DEV_URL_POSTS

**Action Required:** Replace ALL development URLs with production URL: $SITE_URL

EOF
else
    echo -e "${GREEN}✓ No development URLs found${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ✓ Development URLs

**Status:** PASSED
No development URLs found in content.

EOF
fi

#═══════════════════════════════════════════════════════════════
# CHECK 7: Punctuation Errors
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[7/12] Checking for punctuation errors...${NC}"

log "Checking for common punctuation errors"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 7. Punctuation Error Check

EOF

# Check for triple apostrophes
TRIPLE_APOST=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -c "'''" || echo "0")

if [ "$TRIPLE_APOST" -gt 0 ]; then
    echo -e "${RED}✗ Found $TRIPLE_APOST triple apostrophe errors${NC}"
    HIGH_ERRORS=$((HIGH_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ❌ Triple Apostrophe Errors

**Status:** FAILED
**Severity:** HIGH
**Count:** $TRIPLE_APOST

**Issue:** Text contains ''' instead of '

**Action Required:** Replace all ''' with '

EOF
else
    echo -e "${GREEN}✓ No triple apostrophe errors${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

# Check for spaces before punctuation
SPACE_PUNCT=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -c " \." || echo "0")

if [ "$SPACE_PUNCT" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $SPACE_PUNCT spaces before punctuation${NC}"
    WARNINGS=$((WARNINGS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ⚠ Spaces Before Punctuation

**Status:** WARNING
**Count:** $SPACE_PUNCT

**Action:** Remove spaces before punctuation marks.

EOF
fi

#═══════════════════════════════════════════════════════════════
# CHECK 8: PHP Code Exposure
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[8/12] Checking for exposed PHP code...${NC}"

log "Checking for PHP code in content"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 8. PHP Code Exposure Check

EOF

# Check for PHP tags in content
PHP_EXPOSED=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -c "<?php" || echo "0")

if [ "$PHP_EXPOSED" -gt 0 ]; then
    echo -e "${RED}✗ CRITICAL: Found $PHP_EXPOSED instances of exposed PHP code${NC}"
    CRITICAL_ERRORS=$((CRITICAL_ERRORS + 1))

    PHP_POSTS=$(wp post list --post_type=any --format=ids | while read id; do
        if wp post get "$id" --field=post_content 2>/dev/null | grep -q "<?php"; then
            echo "- Post $id: $(wp post get "$id" --field=post_title 2>/dev/null)"
        fi
    done)

    cat >> "$VALIDATION_REPORT" <<EOF

### ❌ Exposed PHP Code

**Status:** FAILED
**Severity:** CRITICAL
**Count:** $PHP_EXPOSED

**Posts with PHP code:**
$PHP_POSTS

**Issue:** PHP code visible in content instead of being executed.

**Action Required:** Replace PHP code with hardcoded values or shortcodes.

EOF
else
    echo -e "${GREEN}✓ No exposed PHP code${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ✓ PHP Code Check

**Status:** PASSED
No exposed PHP code found.

EOF
fi

#═══════════════════════════════════════════════════════════════
# CHECK 9: Shortcode Placeholder Check
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[9/12] Checking for shortcode placeholders...${NC}"

log "Checking for unprocessed shortcode placeholders"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 9. Shortcode Placeholder Check

EOF

# Check for common placeholders that might be interpreted as shortcodes
PLACEHOLDERS=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -cE '\[(NAME|NUMBER|DATE|EMAIL|ADDRESS)\]' || echo "0")

if [ "$PLACEHOLDERS" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $PLACEHOLDERS potential shortcode placeholders${NC}"
    MEDIUM_ERRORS=$((MEDIUM_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ⚠ Shortcode Placeholders

**Status:** WARNING
**Severity:** MEDIUM
**Count:** $PLACEHOLDERS

**Issue:** Square bracket placeholders [NAME], [EMAIL], etc. may be processed as shortcodes.

**Action Required:** Escape square brackets with HTML entities (&#91; and &#93;) if they're meant as placeholders.

EOF
else
    echo -e "${GREEN}✓ No problematic placeholders${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

#═══════════════════════════════════════════════════════════════
# CHECK 10: Policy Count Validation
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[10/12] Validating policy count...${NC}"

log "Checking policy count accuracy"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 10. Policy Count Validation

EOF

# Check for wrong policy counts
WRONG_POLICY_COUNT=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Eo '(34|35|36|37|38|39|40) (policy|policies)' | grep -v "$POLICY_COUNT" -c 2>/dev/null || echo "0")
WRONG_POLICY_COUNT=$(echo "$WRONG_POLICY_COUNT" | tr -d '\n' | grep -o '[0-9]*' | head -1)
WRONG_POLICY_COUNT=${WRONG_POLICY_COUNT:-0}

if [ "$WRONG_POLICY_COUNT" -gt 0 ]; then
    echo -e "${RED}✗ Found $WRONG_POLICY_COUNT incorrect policy count references${NC}"
    HIGH_ERRORS=$((HIGH_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ❌ Incorrect Policy Count

**Status:** FAILED
**Severity:** HIGH
**Correct Value:** $POLICY_COUNT total policy documents
**Incorrect References:** $WRONG_POLICY_COUNT

**Action Required:** Update all policy count references to $POLICY_COUNT.

EOF
else
    echo -e "${GREEN}✓ Policy count correct${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ✓ Policy Count

**Status:** PASSED
All policy count references are correct ($POLICY_COUNT).

EOF
fi

#═══════════════════════════════════════════════════════════════
# CHECK 11: Privacy Policy Status
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[11/12] Checking privacy policy status...${NC}"

log "Checking privacy policy"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 11. Privacy Policy Check

EOF

# Check if privacy policy is published
PRIVACY_STATUS=$(wp post list --post_type=page --name=privacy-policy --field=post_status 2>/dev/null || echo "not_found")

if [ "$PRIVACY_STATUS" = "publish" ]; then
    echo -e "${GREEN}✓ Privacy policy is published${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ✓ Privacy Policy

**Status:** PASSED
Privacy policy is published and accessible.

EOF
elif [ "$PRIVACY_STATUS" = "draft" ]; then
    echo -e "${RED}✗ Privacy policy is in draft status${NC}"
    CRITICAL_ERRORS=$((CRITICAL_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ❌ Privacy Policy Status

**Status:** FAILED
**Severity:** CRITICAL

**Issue:** Privacy policy exists but is in DRAFT status.

**Action Required:** Publish privacy policy before deployment.

EOF
else
    echo -e "${RED}✗ Privacy policy not found${NC}"
    CRITICAL_ERRORS=$((CRITICAL_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ❌ Privacy Policy Missing

**Status:** FAILED
**Severity:** CRITICAL

**Issue:** Privacy policy page not found.

**Action Required:** Create and publish privacy policy before deployment.

EOF
fi

#═══════════════════════════════════════════════════════════════
# CHECK 12: Default WordPress Content
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[12/12] Checking for default WordPress content...${NC}"

log "Checking for default posts/pages"

cat >> "$VALIDATION_REPORT" <<EOF

---

## 12. Default Content Check

EOF

# Check for "Hello world!" post
HELLO_WORLD=$(wp post list --post_type=post --s="Hello world" --format=count 2>/dev/null || echo "0")

# Check for Sample Page
SAMPLE_PAGE=$(wp post list --post_type=page --s="Sample Page" --format=count 2>/dev/null || echo "0")

DEFAULT_CONTENT=$((HELLO_WORLD + SAMPLE_PAGE))

if [ "$DEFAULT_CONTENT" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $DEFAULT_CONTENT default WordPress items${NC}"
    LOW_ERRORS=$((LOW_ERRORS + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ⚠ Default WordPress Content

**Status:** WARNING
**Severity:** LOW
**Count:** $DEFAULT_CONTENT

**Found:**
- "Hello world!" posts: $HELLO_WORLD
- "Sample Page" pages: $SAMPLE_PAGE

**Action Required:** Delete default WordPress content before deployment.

EOF
else
    echo -e "${GREEN}✓ No default WordPress content${NC}"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))

    cat >> "$VALIDATION_REPORT" <<EOF

### ✓ Default Content

**Status:** PASSED
No default WordPress content found.

EOF
fi

#═══════════════════════════════════════════════════════════════
# GENERATE FINAL SUMMARY
#═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}            Validation Complete - Results           ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

TOTAL_ERRORS=$((CRITICAL_ERRORS + HIGH_ERRORS + MEDIUM_ERRORS + LOW_ERRORS))
TOTAL_CHECKS=$((CHECKS_PASSED + CHECKS_FAILED + TOTAL_ERRORS))

if [ "$TOTAL_CHECKS" -gt 0 ]; then
    PASS_RATE=$((CHECKS_PASSED * 100 / TOTAL_CHECKS))
else
    PASS_RATE=0
fi

if [ "$CRITICAL_ERRORS" -gt 0 ]; then
    echo -e "${RED}  CRITICAL: $CRITICAL_ERRORS${NC}"
fi
if [ "$HIGH_ERRORS" -gt 0 ]; then
    echo -e "${RED}  HIGH:     $HIGH_ERRORS${NC}"
fi
if [ "$MEDIUM_ERRORS" -gt 0 ]; then
    echo -e "${YELLOW}  MEDIUM:   $MEDIUM_ERRORS${NC}"
fi
if [ "$LOW_ERRORS" -gt 0 ]; then
    echo -e "${YELLOW}  LOW:      $LOW_ERRORS${NC}"
fi
if [ "$WARNINGS" -gt 0 ]; then
    echo -e "  WARNINGS: $WARNINGS"
fi
echo ""
echo -e "  CHECKS PASSED: $CHECKS_PASSED"
echo -e "  TOTAL ISSUES:  $TOTAL_ERRORS"
echo -e "  PASS RATE:     ${PASS_RATE}%"
echo ""

# Update report with final summary
sed -i "s/^## Validation Summary$/## Validation Summary\n\n**Total Checks:** $TOTAL_CHECKS\n**Checks Passed:** $CHECKS_PASSED\n**Critical Errors:** $CRITICAL_ERRORS\n**High Errors:** $HIGH_ERRORS\n**Medium Errors:** $MEDIUM_ERRORS\n**Low Errors:** $LOW_ERRORS\n**Warnings:** $WARNINGS\n**Pass Rate:** ${PASS_RATE}%/" "$VALIDATION_REPORT"

# Add deployment decision
cat >> "$VALIDATION_REPORT" <<EOF

---

## Deployment Decision

EOF

if [ "$CRITICAL_ERRORS" -gt 0 ]; then
    DECISION="🔴 DEPLOYMENT BLOCKED"
    REASON="Critical errors must be fixed before deployment."
    EXIT_CODE=2

    echo -e "${RED}═══════════════════════════════════════════════════${NC}"
    echo -e "${RED}         ⛔ DEPLOYMENT BLOCKED ⛔                    ${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════${NC}"
    echo -e "${RED}$CRITICAL_ERRORS critical error(s) must be fixed first.${NC}"
    echo ""

    cat >> "$VALIDATION_REPORT" <<EOF
**Decision:** $DECISION

**Reason:** $REASON

**Critical Issues:** $CRITICAL_ERRORS must be resolved before deployment.

**Required Actions:**
1. Fix all CRITICAL errors listed above
2. Re-run this validator
3. Achieve 0 critical errors before deploying

**DO NOT DEPLOY until all critical errors are resolved.**

EOF

elif [ "$HIGH_ERRORS" -gt 0 ]; then
    DECISION="🟡 DEPLOYMENT NOT RECOMMENDED"
    REASON="High-priority errors should be fixed first."
    EXIT_CODE=1

    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}     ⚠️  DEPLOYMENT NOT RECOMMENDED ⚠️            ${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}$HIGH_ERRORS high-priority error(s) should be fixed.${NC}"
    echo ""

    cat >> "$VALIDATION_REPORT" <<EOF
**Decision:** $DECISION

**Reason:** $REASON

**High-Priority Issues:** $HIGH_ERRORS should be resolved.

**Recommended Actions:**
1. Fix all HIGH errors listed above
2. Review MEDIUM and LOW errors
3. Re-run validator for final check
4. Proceed with deployment only if necessary

**Deployment is possible but not recommended.**

EOF

elif [ "$MEDIUM_ERRORS" -gt 0 ] || [ "$LOW_ERRORS" -gt 0 ]; then
    DECISION="🟢 DEPLOYMENT APPROVED WITH WARNINGS"
    REASON="Minor issues exist but deployment is safe."
    EXIT_CODE=0

    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}    ✓ DEPLOYMENT APPROVED (with warnings)         ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Note: $((MEDIUM_ERRORS + LOW_ERRORS)) minor issue(s) should be fixed when convenient.${NC}"
    echo ""

    cat >> "$VALIDATION_REPORT" <<EOF
**Decision:** $DECISION

**Reason:** $REASON

**Minor Issues:** $MEDIUM_ERRORS medium + $LOW_ERRORS low priority errors exist.

**Post-Deployment Actions:**
1. Note all MEDIUM and LOW errors
2. Create issues/tickets to fix them
3. Fix in next update cycle

**Deployment is approved. Site is safe to deploy.**

EOF

else
    DECISION="🟢 DEPLOYMENT APPROVED"
    REASON="All validations passed successfully."
    EXIT_CODE=0

    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}         ✓ DEPLOYMENT APPROVED ✓                  ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}All validation checks passed!${NC}"
    echo ""

    cat >> "$VALIDATION_REPORT" <<EOF
**Decision:** $DECISION

**Reason:** $REASON

**Status:** All validation checks passed successfully!

**Next Steps:**
1. Proceed with deployment
2. Verify deployment success
3. Monitor for any post-deployment issues

**Site is ready for production deployment.**

EOF
fi

cat >> "$VALIDATION_REPORT" <<EOF

---

## Next Steps

1. **Review this report carefully**
2. **Fix all errors** based on priority (CRITICAL → HIGH → MEDIUM → LOW)
3. **Re-run validator** after fixes: \`$0\`
4. **Deploy only when** all critical errors are resolved

---

## Validation Log

- **Report Location:** $VALIDATION_REPORT
- **Log File:** ${LOG_DIR}/validator.log
- **WordPress Path:** $WORDPRESS_PATH
- **Fact Sheet:** $FACT_SHEET

---

*Generated by WordPress Pre-Deployment Validator v1.0.0*
*Part of: Skippy Enhancement Project*
*Next validation: Before each deployment*
EOF

echo -e "${GREEN}Full report saved to:${NC} $VALIDATION_REPORT"
echo ""

log "Pre-deployment validation complete. Decision: $DECISION"

# Exit with appropriate code
exit $EXIT_CODE
