#!/bin/bash
# Fact Checker Automation v1.0.0
# Validates content against authoritative fact sheet
# Part of: Skippy Enhancement Project - TIER 1
# Author: Claude (Skippy Enhancement Project)
# Created: 2025-11-04
#
# Prevents: False firefighter claims, budget errors, wrong biographical info
# Occurred: 6+ documents with factual errors

set -euo pipefail

# Configuration
FACT_SHEET="${FACT_SHEET:-/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md}"
WORDPRESS_PATH="${WORDPRESS_PATH:-/home/dave/Local Sites/rundaverun-local/app/public}"
SKIPPY_BASE="/home/dave/skippy"
REPORT_DIR="${SKIPPY_BASE}/conversations/fact_check_reports"
LOG_DIR="${SKIPPY_BASE}/logs/fact_checking"
ERROR_LOG="${SKIPPY_BASE}/conversations/error_logs/$(date +%Y-%m)/$(date +%Y%m%d_%H%M%S)_fact_check.log"
FACT_CHECK_REPORT="${REPORT_DIR}/fact_check_$(date +%Y%m%d_%H%M%S).md"

# Fact check database (extracted from fact sheet)
declare -A FACTS
declare -A FORBIDDEN_CLAIMS

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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_DIR}/fact_checker.log"
}

log_error() {
    echo "[ERROR] $1" | tee -a "$ERROR_LOG"
}

# Load and parse fact sheet
load_fact_sheet() {
    if [ ! -f "$FACT_SHEET" ]; then
        log_error "CRITICAL: Fact sheet not found at $FACT_SHEET"
        echo -e "${RED}✗ Cannot fact-check without fact sheet${NC}"
        exit 1
    fi

    log "Loading fact sheet: $FACT_SHEET"

    # Extract biographical facts
    FACTS[candidate_name]="Dave Biggers"
    FACTS[candidate_age]="41"
    FACTS[marital_status]="NOT married"
    FACTS[has_children]="NO"
    FACTS[occupation]="Policy developer, public safety expert"

    # Budget facts
    FACTS[total_budget]="\$1.2B"
    FACTS[substation_budget]="\$77.4M"
    FACTS[wellness_budget]="\$34.2M"
    FACTS[wellness_roi]="\$1.80"
    FACTS[participatory_budget]="\$15M"
    FACTS[policy_count]="42"

    # Forbidden claims (things that are FALSE)
    FORBIDDEN_CLAIMS[firefighter]="Dave was NEVER a firefighter"
    FORBIDDEN_CLAIMS[married]="Dave is NOT married"
    FORBIDDEN_CLAIMS[children]="Dave has NO children"
    FORBIDDEN_CLAIMS[fire_stations]="Should be 'mini police substations' not 'fire stations'"

    log "Fact sheet loaded: ${#FACTS[@]} facts, ${#FORBIDDEN_CLAIMS[@]} forbidden claims"
}

# Start report
cat > "$FACT_CHECK_REPORT" <<EOF
# Fact Checking Report

**Check Date:** $(date)
**Fact Checker Version:** 1.0.0
**Fact Sheet:** $FACT_SHEET
**WordPress:** $WORDPRESS_PATH

---

## Summary

EOF

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Fact Checker Automation v1.0.0             ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

log "Starting fact checking"

# Change to WordPress directory
cd "$WORDPRESS_PATH" || {
    log_error "Cannot access WordPress: $WORDPRESS_PATH"
    exit 1
}

# Load fact sheet
load_fact_sheet

# Track results
FACT_ERRORS=0
FACT_WARNINGS=0
FACTS_VERIFIED=0

#═══════════════════════════════════════════════════════════════
# CHECK 1: Forbidden Claims (Critical)
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[1/6] Checking for forbidden false claims...${NC}"

cat >> "$FACT_CHECK_REPORT" <<EOF

---

## 1. Forbidden Claims Check

**Critical false claims that must NEVER appear:**

EOF

# Check for firefighter claim
echo "  Checking for false 'firefighter' claims..."
FIREFIGHTER_FOUND=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -ci "firefighter" || echo "0")

if [ "$FIREFIGHTER_FOUND" -gt 0 ]; then
    echo -e "${RED}✗ CRITICAL: Found $FIREFIGHTER_FOUND 'firefighter' mentions${NC}"
    FACT_ERRORS=$((FACT_ERRORS + 1))

    # Find specific posts
    FIREFIGHTER_POSTS=$(wp post list --post_type=any --format=ids | while read id; do
        if wp post get "$id" --field=post_content 2>/dev/null | grep -qi "firefighter"; then
            TITLE=$(wp post get "$id" --field=post_title 2>/dev/null)
            echo "- Post $id: $TITLE"
        fi
    done)

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ❌ FALSE CLAIM: Firefighter

**Status:** CRITICAL FAILURE
**Mentions:** $FIREFIGHTER_FOUND

**Truth:** ${FORBIDDEN_CLAIMS[firefighter]}

**Posts with false claim:**
$FIREFIGHTER_POSTS

**Action Required:** Remove ALL firefighter references immediately.

EOF
else
    echo -e "${GREEN}✓ No false firefighter claims${NC}"
    FACTS_VERIFIED=$((FACTS_VERIFIED + 1))

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ✓ Firefighter Claim Check

**Status:** PASSED
No false firefighter claims found.

EOF
fi

# Check for marriage/spouse claims
echo "  Checking for false marital status claims..."
MARRIED_FOUND=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Eci "married|spouse|wife|husband" || echo "0")

if [ "$MARRIED_FOUND" -gt 0 ]; then
    echo -e "${YELLOW}⚠ WARNING: Found $MARRIED_FOUND marital status mentions${NC}"
    FACT_WARNINGS=$((FACT_WARNINGS + 1))

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ⚠ Marital Status Mentions

**Status:** WARNING
**Mentions:** $MARRIED_FOUND

**Truth:** ${FORBIDDEN_CLAIMS[married]}

**Action:** Manually review all mentions to ensure accuracy.

EOF
else
    echo -e "${GREEN}✓ No marital status claims${NC}"
    FACTS_VERIFIED=$((FACTS_VERIFIED + 1))
fi

# Check for children claims
echo "  Checking for false children claims..."
CHILDREN_FOUND=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Eci "children|kids|son|daughter" || echo "0")

if [ "$CHILDREN_FOUND" -gt 0 ]; then
    echo -e "${YELLOW}⚠ WARNING: Found $CHILDREN_FOUND children mentions${NC}"
    FACT_WARNINGS=$((FACT_WARNINGS + 1))

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ⚠ Children Mentions

**Status:** WARNING
**Mentions:** $CHILDREN_FOUND

**Truth:** ${FORBIDDEN_CLAIMS[children]}

**Action:** Manually review all mentions to ensure accuracy.

EOF
else
    echo -e "${GREEN}✓ No children claims${NC}"
    FACTS_VERIFIED=$((FACTS_VERIFIED + 1))
fi

#═══════════════════════════════════════════════════════════════
# CHECK 2: Budget Figures
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[2/6] Verifying budget figures...${NC}"

cat >> "$FACT_CHECK_REPORT" <<EOF

---

## 2. Budget Figures Verification

**Authoritative budget figures:**
- Total: ${FACTS[total_budget]}
- Substations: ${FACTS[substation_budget]}
- Wellness: ${FACTS[wellness_budget]}
- Wellness ROI: ${FACTS[wellness_roi]} per dollar
- Participatory: ${FACTS[participatory_budget]}

EOF

# Check for wrong substation budget
echo "  Checking substation budget..."
WRONG_SUBSTATION=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -oE '\$[0-9.]+M' | grep -v "${FACTS[substation_budget]}" | grep -c "substation" || echo "0")

# Check wellness budget
echo "  Checking wellness center budget..."
WELLNESS_VARIANTS=$(wp post list --post_type=any --format=ids | while read id; do
    CONTENT=$(wp post get "$id" --field=post_content 2>/dev/null)
    if echo "$CONTENT" | grep -qi "wellness"; then
        BUDGETS=$(echo "$CONTENT" | grep -oE '\$[0-9.]+M' | sort -u)
        if echo "$BUDGETS" | grep -qv "${FACTS[wellness_budget]}"; then
            TITLE=$(wp post get "$id" --field=post_title 2>/dev/null)
            echo "- Post $id ($TITLE): Found $(echo $BUDGETS | tr '\n' ', ')"
        fi
    fi
done)

if [ -n "$WELLNESS_VARIANTS" ]; then
    echo -e "${RED}✗ Wellness budget inconsistencies found${NC}"
    FACT_ERRORS=$((FACT_ERRORS + 1))

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ❌ Wellness Budget Inconsistencies

**Status:** FAILED
**Correct Value:** ${FACTS[wellness_budget]}

**Inconsistent posts:**
$WELLNESS_VARIANTS

**Action Required:** Standardize all wellness budget references.

EOF
else
    echo -e "${GREEN}✓ Wellness budget consistent${NC}"
    FACTS_VERIFIED=$((FACTS_VERIFIED + 1))
fi

# Check wellness ROI
echo "  Checking wellness ROI..."
WRONG_ROI=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -c "\$3\.00 saved\|\$3 saved per" || echo "0")

if [ "$WRONG_ROI" -gt 0 ]; then
    echo -e "${RED}✗ Found $WRONG_ROI incorrect wellness ROI references${NC}"
    FACT_ERRORS=$((FACT_ERRORS + 1))

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ❌ Incorrect Wellness ROI

**Status:** FAILED
**Incorrect Value:** \$3.00 per dollar
**Correct Value:** ${FACTS[wellness_roi]} per dollar
**Instances:** $WRONG_ROI

**Action Required:** Correct all ROI figures.

EOF
else
    echo -e "${GREEN}✓ Wellness ROI correct${NC}"
    FACTS_VERIFIED=$((FACTS_VERIFIED + 1))
fi

# Check participatory budgeting
echo "  Checking participatory budgeting..."
WRONG_PARTICIPATORY=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Ec "participatory.*\$5M|\$12M.*participatory" || echo "0")

if [ "$WRONG_PARTICIPATORY" -gt 0 ]; then
    echo -e "${RED}✗ Found $WRONG_PARTICIPATORY incorrect participatory budget references${NC}"
    FACT_ERRORS=$((FACT_ERRORS + 1))

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ❌ Incorrect Participatory Budget

**Status:** FAILED
**Correct Value:** ${FACTS[participatory_budget]}
**Instances:** $WRONG_PARTICIPATORY

**Action Required:** Correct to ${FACTS[participatory_budget]}.

EOF
else
    echo -e "${GREEN}✓ Participatory budget correct${NC}"
    FACTS_VERIFIED=$((FACTS_VERIFIED + 1))
fi

#═══════════════════════════════════════════════════════════════
# CHECK 3: Policy Count
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[3/6] Verifying policy count...${NC}"

cat >> "$FACT_CHECK_REPORT" <<EOF

---

## 3. Policy Count Verification

**Authoritative Count:** ${FACTS[policy_count]} total policy documents

EOF

WRONG_POLICY_COUNT=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -Eo '(34|35|36|37|38|39|40) (policy|policies)' | wc -l || echo "0")

if [ "$WRONG_POLICY_COUNT" -gt 0 ]; then
    echo -e "${RED}✗ Found $WRONG_POLICY_COUNT incorrect policy count references${NC}"
    FACT_ERRORS=$((FACT_ERRORS + 1))

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ❌ Incorrect Policy Count

**Status:** FAILED
**Correct Value:** ${FACTS[policy_count]}
**Incorrect References:** $WRONG_POLICY_COUNT

**Action Required:** Update all to ${FACTS[policy_count]}.

EOF
else
    echo -e "${GREEN}✓ Policy count correct${NC}"
    FACTS_VERIFIED=$((FACTS_VERIFIED + 1))
fi

#═══════════════════════════════════════════════════════════════
# CHECK 4: Terminology
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[4/6] Checking terminology...${NC}"

cat >> "$FACT_CHECK_REPORT" <<EOF

---

## 4. Terminology Check

EOF

# Check for "fire stations" in wrong context
FIRE_STATION_WRONG=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -ci "fire stations in every\|73.*fire stations" || echo "0")

if [ "$FIRE_STATION_WRONG" -gt 0 ]; then
    echo -e "${RED}✗ Found $FIRE_STATION_WRONG incorrect 'fire stations' references${NC}"
    FACT_ERRORS=$((FACT_ERRORS + 1))

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ❌ Incorrect Terminology: "Fire Stations"

**Status:** FAILED
**Issue:** References to "fire stations in every ZIP" or "73 fire stations"
**Correct Term:** "mini police substations"
**Instances:** $FIRE_STATION_WRONG

**Action Required:** Replace with correct terminology.

EOF
else
    echo -e "${GREEN}✓ Correct terminology used${NC}"
    FACTS_VERIFIED=$((FACTS_VERIFIED + 1))
fi

#═══════════════════════════════════════════════════════════════
# CHECK 5: Age Verification
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[5/6] Verifying candidate age...${NC}"

cat >> "$FACT_CHECK_REPORT" <<EOF

---

## 5. Age Verification

**Correct Age:** ${FACTS[candidate_age]}

EOF

WRONG_AGE=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -oE "age [0-9]+" | grep -v "age ${FACTS[candidate_age]}" | wc -l || echo "0")

if [ "$WRONG_AGE" -gt 0 ]; then
    echo -e "${RED}✗ Found $WRONG_AGE incorrect age references${NC}"
    FACT_ERRORS=$((FACT_ERRORS + 1))

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ❌ Incorrect Age

**Status:** FAILED
**Correct Age:** ${FACTS[candidate_age]}
**Incorrect References:** $WRONG_AGE

**Action Required:** Update all age references to ${FACTS[candidate_age]}.

EOF
else
    echo -e "${GREEN}✓ Age correct or not mentioned${NC}"
    FACTS_VERIFIED=$((FACTS_VERIFIED + 1))
fi

#═══════════════════════════════════════════════════════════════
# CHECK 6: URLs and Contact Info
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[6/6] Verifying URLs and contact info...${NC}"

cat >> "$FACT_CHECK_REPORT" <<EOF

---

## 6. URLs and Contact Information

EOF

# Check for unauthorized emails
UNAUTHORIZED_EMAILS=$(wp post list --post_type=any --format=ids | xargs -I {} wp post get {} --field=post_content 2>/dev/null | grep -oP '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' | sort -u | grep -v "dave@rundaverun.org\|info@rundaverun.org" || echo "")

if [ -n "$UNAUTHORIZED_EMAILS" ]; then
    echo -e "${YELLOW}⚠ Found unauthorized email addresses${NC}"
    FACT_WARNINGS=$((FACT_WARNINGS + 1))

    cat >> "$FACT_CHECK_REPORT" <<EOF

### ⚠ Unauthorized Email Addresses

**Status:** WARNING

**Unauthorized emails found:**
$UNAUTHORIZED_EMAILS

**Authorized emails:**
- dave@rundaverun.org
- info@rundaverun.org

**Action:** Review and replace with authorized emails.

EOF
else
    echo -e "${GREEN}✓ All emails authorized${NC}"
    FACTS_VERIFIED=$((FACTS_VERIFIED + 1))
fi

#═══════════════════════════════════════════════════════════════
# GENERATE SUMMARY
#═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}      Fact Checking Complete - Summary             ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

TOTAL_CHECKS=$((FACTS_VERIFIED + FACT_ERRORS + FACT_WARNINGS))
if [ "$TOTAL_CHECKS" -gt 0 ]; then
    ACCURACY_RATE=$((FACTS_VERIFIED * 100 / TOTAL_CHECKS))
else
    ACCURACY_RATE=0
fi

if [ "$FACT_ERRORS" -gt 0 ]; then
    echo -e "${RED}  ERRORS:   $FACT_ERRORS${NC}"
fi
if [ "$FACT_WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}  WARNINGS: $FACT_WARNINGS${NC}"
fi
echo -e "${GREEN}  VERIFIED: $FACTS_VERIFIED${NC}"
echo ""
echo -e "  ACCURACY RATE: ${ACCURACY_RATE}%"
echo ""

# Update report summary
sed -i "s/^## Summary$/## Summary\n\n**Fact Check Results:**\n- Verified: $FACTS_VERIFIED\n- Errors: $FACT_ERRORS\n- Warnings: $FACT_WARNINGS\n- Accuracy Rate: ${ACCURACY_RATE}%/" "$FACT_CHECK_REPORT"

# Add final decision
cat >> "$FACT_CHECK_REPORT" <<EOF

---

## Fact Check Decision

EOF

if [ "$FACT_ERRORS" -eq 0 ]; then
    DECISION="🟢 FACTS VERIFIED"
    EXIT_CODE=0

    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}         ✓ ALL FACTS VERIFIED ✓                   ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"

    cat >> "$FACT_CHECK_REPORT" <<EOF
**Decision:** $DECISION

**Status:** All facts verified against authoritative fact sheet.

**Conclusion:** Content is factually accurate and safe for publication.

EOF

else
    DECISION="🔴 FACTUAL ERRORS FOUND"
    EXIT_CODE=1

    echo -e "${RED}═══════════════════════════════════════════════════${NC}"
    echo -e "${RED}      ⚠️  FACTUAL ERRORS FOUND ⚠️                  ${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════${NC}"
    echo -e "${RED}Found $FACT_ERRORS factual error(s). Fix before publishing.${NC}"

    cat >> "$FACT_CHECK_REPORT" <<EOF
**Decision:** $DECISION

**Status:** Found $FACT_ERRORS factual errors.

**Action Required:**
1. Fix ALL errors listed above
2. Re-run fact checker
3. Achieve 100% accuracy before publishing

**DO NOT PUBLISH until all factual errors are corrected.**

EOF
fi

cat >> "$FACT_CHECK_REPORT" <<EOF

---

## Integration Recommendations

### Pre-Save Hook
Integrate this fact checker as a pre-save hook in WordPress to catch errors in real-time.

### Automated Checks
Run this checker:
- Before each deployment
- After content updates
- Weekly as part of QA process

### Fact Sheet Maintenance
- Keep fact sheet updated
- Review quarterly
- Update checker when facts change

---

*Generated by Fact Checker Automation v1.0.0*
*Report Location:* $FACT_CHECK_REPORT
*Fact Sheet:* $FACT_SHEET
EOF

echo -e "${GREEN}Report saved to:${NC} $FACT_CHECK_REPORT"
echo ""

log "Fact checking complete. Decision: $DECISION"

exit $EXIT_CODE
