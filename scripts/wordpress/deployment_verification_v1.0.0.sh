#!/bin/bash
# Deployment Verification System v1.0.0
# Verifies content was successfully deployed to production
# Part of: Skippy Enhancement Project - TIER 1
# Author: Claude (Skippy Enhancement Project)
# Created: 2025-11-04
#
# Prevents the problem: "Content fixed locally but never deployed"
# Occurred: 3+ times (Nov 3 fact-check fixes still missing)

set -euo pipefail

# Configuration
LOCAL_WP="${LOCAL_WP:-/home/dave/Local Sites/rundaverun-local/app/public}"
PRODUCTION_URL="${PRODUCTION_URL:-https://rundaverun.org}"
SKIPPY_BASE="/home/dave/skippy"
REPORT_DIR="${SKIPPY_BASE}/conversations/deployment_verification_reports"
LOG_DIR="${SKIPPY_BASE}/logs/deployment_verification"
ERROR_LOG="${SKIPPY_BASE}/conversations/error_logs/$(date +%Y-%m)/$(date +%Y%m%d_%H%M%S)_deployment_verification.log"
VERIFICATION_REPORT="${REPORT_DIR}/deployment_verification_$(date +%Y%m%d_%H%M%S).md"

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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_DIR}/verifier.log"
}

log_error() {
    echo "[ERROR] $1" | tee -a "$ERROR_LOG"
}

# Start report
cat > "$VERIFICATION_REPORT" <<EOF
# Deployment Verification Report

**Verification Date:** $(date)
**Verifier Version:** 1.0.0
**Local WordPress:** $LOCAL_WP
**Production URL:** $PRODUCTION_URL

---

## Summary

EOF

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Deployment Verification System v1.0.0         ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

log "Starting deployment verification"

# Track results
MISMATCHES=0
VERIFIED=0
WARNINGS=0

#═══════════════════════════════════════════════════════════════
# STEP 1: Get Local Content Snapshot
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[1/5] Creating local content snapshot...${NC}"

cd "$LOCAL_WP" || {
    log_error "Cannot access local WordPress: $LOCAL_WP"
    exit 1
}

# Get all published posts/pages
LOCAL_POSTS=$(wp post list --post_type=any --post_status=publish --format=json 2>/dev/null || echo "[]")
LOCAL_COUNT=$(echo "$LOCAL_POSTS" | jq '. | length')

echo "  Found $LOCAL_COUNT published posts/pages locally"
log "Local content: $LOCAL_COUNT items"

# Store critical content checksums
TEMP_DIR="/tmp/deployment_verify_$(date +%s)"
mkdir -p "$TEMP_DIR"

echo "$LOCAL_POSTS" | jq -r '.[] | "\(.ID),\(.post_title),\(.post_modified)"' > "$TEMP_DIR/local_inventory.csv"

#═══════════════════════════════════════════════════════════════
# STEP 2: Fetch Production Content
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[2/5] Fetching production content...${NC}"

# Try to fetch via WordPress REST API
PRODUCTION_POSTS=$(curl -s "${PRODUCTION_URL}/wp-json/wp/v2/posts?per_page=100" 2>/dev/null || echo "[]")
PRODUCTION_PAGES=$(curl -s "${PRODUCTION_URL}/wp-json/wp/v2/pages?per_page=100" 2>/dev/null || echo "[]")

PROD_POST_COUNT=$(echo "$PRODUCTION_POSTS" | jq '. | length' 2>/dev/null || echo "0")
PROD_PAGE_COUNT=$(echo "$PRODUCTION_PAGES" | jq '. | length' 2>/dev/null || echo "0")
PROD_TOTAL=$((PROD_POST_COUNT + PROD_PAGE_COUNT))

if [ "$PROD_TOTAL" -eq 0 ]; then
    echo -e "${RED}✗ Cannot fetch production content via REST API${NC}"
    log_error "REST API not accessible or returned no content"

    cat >> "$VERIFICATION_REPORT" <<EOF

### ⚠️ Production Content Access

**Status:** WARNING
**Issue:** Cannot access production content via REST API

**Possible Causes:**
1. REST API disabled
2. Authentication required
3. Firewall blocking
4. Site not yet deployed

**Recommendation:** Manually verify deployment or configure REST API access.

EOF

    WARNINGS=$((WARNINGS + 1))
else
    echo "  Found $PROD_TOTAL items on production ($PROD_POST_COUNT posts, $PROD_PAGE_COUNT pages)"
    log "Production content: $PROD_TOTAL items"
fi

#═══════════════════════════════════════════════════════════════
# STEP 3: Compare Content Counts
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[3/5] Comparing content counts...${NC}"

cat >> "$VERIFICATION_REPORT" <<EOF

---

## Content Count Comparison

| Metric | Local | Production | Status |
|--------|-------|------------|--------|
| Total Items | $LOCAL_COUNT | $PROD_TOTAL | $([ "$LOCAL_COUNT" -eq "$PROD_TOTAL" ] && echo "✓ Match" || echo "⚠ Mismatch") |

EOF

if [ "$LOCAL_COUNT" -ne "$PROD_TOTAL" ]; then
    DIFF=$((LOCAL_COUNT - PROD_TOTAL))
    echo -e "${YELLOW}⚠ Content count mismatch: $DIFF items difference${NC}"
    MISMATCHES=$((MISMATCHES + 1))

    cat >> "$VERIFICATION_REPORT" <<EOF

**Warning:** Local has $LOCAL_COUNT items but production has $PROD_TOTAL items.
**Difference:** $DIFF items

**Possible causes:**
- New content not yet deployed
- Content deleted on production
- Sync incomplete

EOF
else
    echo -e "${GREEN}✓ Content counts match${NC}"
    VERIFIED=$((VERIFIED + 1))
fi

#═══════════════════════════════════════════════════════════════
# STEP 4: Verify Critical Content
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[4/5] Verifying critical content...${NC}"

cat >> "$VERIFICATION_REPORT" <<EOF

---

## Critical Content Verification

EOF

# Check homepage
echo "  Checking homepage..."
HOMEPAGE_LOCAL=$(wp post get $(wp option get page_on_front 2>/dev/null) --field=post_title 2>/dev/null || echo "Not set")
HOMEPAGE_PROD=$(curl -s "$PRODUCTION_URL" | grep -oP '<title>\K[^<]+' | head -1 || echo "Unable to fetch")

echo "    Local homepage: $HOMEPAGE_LOCAL"
echo "    Production homepage: $HOMEPAGE_PROD"

# Check fact sheet critical items
if [ -f "/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md" ]; then
    echo "  Checking critical facts on production..."

    # Check for false firefighter claim
    if curl -s "$PRODUCTION_URL" | grep -qi "firefighter"; then
        echo -e "${RED}✗ CRITICAL: 'firefighter' found on production${NC}"
        MISMATCHES=$((MISMATCHES + 1))

        cat >> "$VERIFICATION_REPORT" <<EOF

### ❌ False Firefighter Claim on Production

**Status:** CRITICAL FAILURE
**Issue:** Production site contains "firefighter" references

**Action Required:** Immediately update production to remove false claims.

EOF
    else
        echo -e "${GREEN}✓ No false firefighter claims on production${NC}"
        VERIFIED=$((VERIFIED + 1))
    fi

    # Check budget figures
    echo "  Verifying budget figures..."

    PROD_HTML=$(curl -s "$PRODUCTION_URL/policy")

    # Check for wrong wellness ROI
    if echo "$PROD_HTML" | grep -q "\$3\.00 saved\|\$3 saved per"; then
        echo -e "${RED}✗ Wrong wellness ROI on production (\$3.00 instead of \$1.80)${NC}"
        MISMATCHES=$((MISMATCHES + 1))

        cat >> "$VERIFICATION_REPORT" <<EOF

### ❌ Incorrect Wellness ROI on Production

**Status:** FAILURE
**Issue:** Production shows \$3.00 ROI instead of \$1.80

**Action Required:** Update production with correct wellness center ROI.

EOF
    else
        echo -e "${GREEN}✓ Wellness ROI appears correct${NC}"
        VERIFIED=$((VERIFIED + 1))
    fi
fi

#═══════════════════════════════════════════════════════════════
# STEP 5: Check Recent Modifications
#═══════════════════════════════════════════════════════════════

echo -e "${YELLOW}[5/5] Checking recent modifications...${NC}"

cat >> "$VERIFICATION_REPORT" <<EOF

---

## Recent Modifications Check

EOF

# Get recently modified local content
RECENT_LOCAL=$(wp post list --post_type=any --post_status=publish --orderby=modified --order=DESC --posts_per_page=10 --format=table --fields=ID,post_title,post_modified 2>/dev/null)

echo "  Recently modified locally:"
echo "$RECENT_LOCAL" | head -5

cat >> "$VERIFICATION_REPORT" <<EOF

### Recently Modified Content (Local)

\`\`\`
$RECENT_LOCAL
\`\`\`

**Recommendation:** Verify these items exist on production with recent modification dates.

EOF

# Check if specific posts from recent fixes exist on production
echo "  Verifying specific critical posts..."

CRITICAL_POSTS=(941 942 701 709 246)  # Posts from recent fixes

for POST_ID in "${CRITICAL_POSTS[@]}"; do
    LOCAL_TITLE=$(wp post get "$POST_ID" --field=post_title 2>/dev/null || echo "Not found")
    LOCAL_MODIFIED=$(wp post get "$POST_ID" --field=post_modified 2>/dev/null || echo "N/A")

    if [ "$LOCAL_TITLE" != "Not found" ]; then
        echo "    Post $POST_ID: $LOCAL_TITLE (modified: $LOCAL_MODIFIED)"

        # Try to fetch from production
        PROD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${PRODUCTION_URL}/?p=${POST_ID}")

        if [ "$PROD_STATUS" = "200" ]; then
            echo -e "      ${GREEN}✓ Exists on production${NC}"
            VERIFIED=$((VERIFIED + 1))
        else
            echo -e "      ${RED}✗ Not found on production (HTTP $PROD_STATUS)${NC}"
            MISMATCHES=$((MISMATCHES + 1))

            cat >> "$VERIFICATION_REPORT" <<EOF

**⚠️ Post $POST_ID Missing on Production:**
- Title: $LOCAL_TITLE
- Local Modified: $LOCAL_MODIFIED
- Production Status: HTTP $PROD_STATUS (Not Found)

EOF
        fi
    fi
done

#═══════════════════════════════════════════════════════════════
# GENERATE SUMMARY
#═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}       Verification Complete - Summary             ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

TOTAL_CHECKS=$((VERIFIED + MISMATCHES))
if [ "$TOTAL_CHECKS" -gt 0 ]; then
    SUCCESS_RATE=$((VERIFIED * 100 / TOTAL_CHECKS))
else
    SUCCESS_RATE=0
fi

if [ "$MISMATCHES" -gt 0 ]; then
    echo -e "${RED}  MISMATCHES: $MISMATCHES${NC}"
fi
if [ "$WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}  WARNINGS:   $WARNINGS${NC}"
fi
echo -e "${GREEN}  VERIFIED:   $VERIFIED${NC}"
echo ""
echo -e "  SUCCESS RATE: ${SUCCESS_RATE}%"
echo ""

# Update report summary
sed -i "s/^## Summary$/## Summary\n\n**Verification Results:**\n- Verified: $VERIFIED\n- Mismatches: $MISMATCHES\n- Warnings: $WARNINGS\n- Success Rate: ${SUCCESS_RATE}%/" "$VERIFICATION_REPORT"

# Add final assessment
cat >> "$VERIFICATION_REPORT" <<EOF

---

## Deployment Assessment

EOF

if [ "$MISMATCHES" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    ASSESSMENT="🟢 DEPLOYMENT VERIFIED"
    REASON="All checks passed. Local and production are in sync."
    EXIT_CODE=0

    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        ✓ DEPLOYMENT VERIFIED ✓                    ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"

    cat >> "$VERIFICATION_REPORT" <<EOF
**Assessment:** $ASSESSMENT

**Status:** All verification checks passed successfully.

**Conclusion:** Local and production content are in sync. Deployment was successful.

EOF

elif [ "$MISMATCHES" -gt 0 ]; then
    ASSESSMENT="🔴 DEPLOYMENT SYNC ISSUES"
    REASON="Found $MISMATCHES mismatches between local and production."
    EXIT_CODE=1

    echo -e "${RED}═══════════════════════════════════════════════════${NC}"
    echo -e "${RED}      ⚠️  DEPLOYMENT SYNC ISSUES ⚠️                ${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════${NC}"
    echo -e "${RED}Found $MISMATCHES mismatch(es). Review report for details.${NC}"

    cat >> "$VERIFICATION_REPORT" <<EOF
**Assessment:** $ASSESSMENT

**Status:** Found $MISMATCHES mismatches between local and production.

**Issue:** Local and production content are NOT in sync.

**Action Required:**
1. Review mismatches listed above
2. Re-deploy affected content
3. Run verification again

**DO NOT consider deployment complete until all mismatches are resolved.**

EOF

else
    ASSESSMENT="🟡 DEPLOYMENT PARTIALLY VERIFIED"
    REASON="Found $WARNINGS warnings but no critical mismatches."
    EXIT_CODE=0

    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}    ⚠️ DEPLOYMENT PARTIALLY VERIFIED ⚠️          ${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Found $WARNINGS warning(s). Manual verification recommended.${NC}"

    cat >> "$VERIFICATION_REPORT" <<EOF
**Assessment:** $ASSESSMENT

**Status:** Found $WARNINGS warnings but no critical mismatches.

**Recommendation:** Manually verify deployment was successful.

EOF
fi

cat >> "$VERIFICATION_REPORT" <<EOF

---

## Recommendations

### Immediate Actions
1. **Review all mismatches** and warnings in this report
2. **Re-deploy any missing content** identified above
3. **Run this verifier again** after making corrections
4. **Document any deployment issues** for process improvement

### Process Improvements
1. **Automate deployment** to reduce manual errors
2. **Use deployment tracking** to record what was deployed when
3. **Run pre-deployment validator** before every deployment
4. **Run this post-deployment verifier** after every deployment
5. **Keep deployment log** of all changes deployed

### Next Verification
**Recommended:** After each deployment or weekly

---

## Deployment Checklist Integration

This verifier should be the LAST step in your deployment process:

1. ✓ Make changes locally
2. ✓ Run pre-deployment validator
3. ✓ Fix all critical errors
4. ✓ Deploy to production
5. ✓ **Run THIS verifier** ← You are here
6. ✓ Confirm all checks passed
7. ✓ Monitor for issues

---

*Generated by Deployment Verification System v1.0.0*
*Report Location:* $VERIFICATION_REPORT
*Next verification:* After next deployment or in 7 days
EOF

echo -e "${GREEN}Report saved to:${NC} $VERIFICATION_REPORT"
echo ""

# Cleanup
rm -rf "$TEMP_DIR"

log "Deployment verification complete. Assessment: $ASSESSMENT"

exit $EXIT_CODE
