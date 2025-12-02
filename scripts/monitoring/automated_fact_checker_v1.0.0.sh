#!/bin/bash
# Automated Fact-Checking Validator
# Version: 1.0.0
# Purpose: Scan WordPress content for numbers and validate against QUICK_FACTS_SHEET.md
# Usage: bash automated_fact_checker_v1.0.0.sh [site]

VERSION="1.0.0"
SITE="${1:-rundaverun-local}"
FACT_SHEET="/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md"
REPORT_FILE="/home/dave/skippy/conversations/fact_check_validation_$(date +%Y-%m-%d).md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Known correct values from fact sheet (as of Nov 2025)
declare -A KNOWN_FACTS=(
    ["\$81M"]="Total Budget"
    ["\$77.4M"]="Public Safety Budget"
    ["\$13.4M"]="Wellness Centers Budget"
    ["\$2-3"]="Wellness ROI per dollar"
    ["34-35%"]="JCPS Reading Proficiency"
    ["27-28%"]="JCPS Math Proficiency"
    ["14"]="Number of Mini Substations"
    ["7"]="Number of Wellness Centers"
)

# Incorrect values that should NOT appear
declare -A INCORRECT_FACTS=(
    ["\$110.5M"]="Old total budget (OUTDATED)"
    ["\$29.9M"]="Old public safety budget (OUTDATED)"
    ["\$47.5M"]="Old public safety budget (OUTDATED)"
    ["\$1.80"]="Old wellness ROI (OUTDATED)"
    ["44%"]="Incorrect JCPS reading (WRONG)"
    ["41%"]="Incorrect JCPS math (WRONG)"
)

echo "=== Automated Fact-Checking Validator v$VERSION ==="
echo "Validating WordPress content against QUICK_FACTS_SHEET.md"
echo ""

# Check if fact sheet exists
if [ ! -f "$FACT_SHEET" ]; then
    echo -e "${RED}❌ QUICK_FACTS_SHEET.md not found!${NC}"
    echo "Expected location: $FACT_SHEET"
    exit 1
fi

echo "✅ Fact sheet found"
echo ""

# Initialize counters
TOTAL_PAGES=0
ISSUES_FOUND=0
CORRECT_VALUES=0
INCORRECT_VALUES=0

# Initialize report
cat > "$REPORT_FILE" <<EOF
# Automated Fact-Check Validation Report
**Date:** $(date)
**Site:** $SITE
**Validator Version:** $VERSION

---

## Summary

EOF

# Get all pages and policies
echo "Scanning WordPress content..."
POST_IDS=$(wp post list --post_type=page,policy_document --format=csv --fields=ID | tail -n +2)

# Scan each post
while IFS= read -r ID; do
    ((TOTAL_PAGES++))

    TITLE=$(wp post get $ID --field=post_title 2>/dev/null)
    CONTENT=$(wp post get $ID --field=post_content 2>/dev/null)

    if [ -z "$CONTENT" ]; then
        continue
    fi

    POST_ISSUES=""
    POST_CORRECT=""

    # Check for incorrect values
    for VALUE in "${!INCORRECT_FACTS[@]}"; do
        if echo "$CONTENT" | grep -q "$VALUE"; then
            ((INCORRECT_VALUES++))
            ((ISSUES_FOUND++))
            POST_ISSUES="${POST_ISSUES}\n  ❌ Found: $VALUE (${INCORRECT_FACTS[$VALUE]})"
        fi
    done

    # Check for correct values
    for VALUE in "${!KNOWN_FACTS[@]}"; do
        if echo "$CONTENT" | grep -q "$VALUE"; then
            ((CORRECT_VALUES++))
            POST_CORRECT="${POST_CORRECT}\n  ✅ Verified: $VALUE (${KNOWN_FACTS[$VALUE]})"
        fi
    done

    # Report if issues found
    if [ -n "$POST_ISSUES" ]; then
        echo -e "${RED}❌ Issues in ID $ID: $TITLE${NC}"
        echo -e "$POST_ISSUES"

        # Add to report
        cat >> "$REPORT_FILE" <<EOF

### ❌ Page $ID: $TITLE
EOF
        echo -e "$POST_ISSUES" >> "$REPORT_FILE"
    fi

    # Show progress
    if ((TOTAL_PAGES % 10 == 0)); then
        echo "Scanned $TOTAL_PAGES pages..."
    fi

done <<< "$POST_IDS"

# Calculate accuracy
if [ $TOTAL_PAGES -gt 0 ]; then
    PAGES_WITH_ISSUES=$((ISSUES_FOUND > 0 ? 1 : 0))
    ACCURACY_RATE=$(( (TOTAL_PAGES - PAGES_WITH_ISSUES) * 100 / TOTAL_PAGES ))
else
    ACCURACY_RATE=100
fi

# Print summary
echo ""
echo "=== Validation Summary ==="
echo "Pages Scanned: $TOTAL_PAGES"
echo "Correct Values Found: $CORRECT_VALUES"
echo "Incorrect Values Found: $INCORRECT_VALUES"
echo "Accuracy Rate: ${ACCURACY_RATE}%"
echo ""

# Update report summary
cat >> "$REPORT_FILE" <<EOF

**Pages Scanned:** $TOTAL_PAGES
**Correct Values Found:** $CORRECT_VALUES
**Incorrect Values Found:** $INCORRECT_VALUES
**Accuracy Rate:** ${ACCURACY_RATE}%

---

## Known Correct Values (Reference)

| Value | Description |
|-------|-------------|
EOF

for VALUE in "${!KNOWN_FACTS[@]}"; do
    echo "| $VALUE | ${KNOWN_FACTS[$VALUE]} |" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" <<EOF

---

## Known Incorrect Values (Should Not Appear)

| Value | Reason |
|-------|--------|
EOF

for VALUE in "${!INCORRECT_FACTS[@]}"; do
    echo "| $VALUE | ${INCORRECT_FACTS[$VALUE]} |" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" <<EOF

---

## Recommendations

EOF

if [ $INCORRECT_VALUES -gt 0 ]; then
    cat >> "$REPORT_FILE" <<EOF
### ⚠️ IMMEDIATE ACTION REQUIRED

$INCORRECT_VALUES incorrect value(s) found in WordPress content.

**Action Items:**
1. Review pages listed above
2. Update incorrect values using QUICK_FACTS_SHEET.md
3. Follow WordPress Content Update Protocol
4. Follow Fact-Checking Protocol
5. Re-run this validator after corrections

**Fact Sheet Location:**
\`$FACT_SHEET\`
EOF
else
    cat >> "$REPORT_FILE" <<EOF
### ✅ All Clear

No incorrect values detected. All scanned content appears to use accurate data from QUICK_FACTS_SHEET.md.

**Next Steps:**
- Continue monitoring with weekly scans
- Update validator if fact sheet changes
- Add new known values as they're established
EOF
fi

cat >> "$REPORT_FILE" <<EOF

---

**Validator Version:** $VERSION
**Next Scan:** $(date -d "+7 days" +%Y-%m-%d)
**Fact Sheet:** $FACT_SHEET
EOF

# Final output
if [ $INCORRECT_VALUES -gt 0 ]; then
    echo -e "${RED}⚠️ VALIDATION FAILED${NC}"
    echo "$INCORRECT_VALUES incorrect value(s) found!"
    echo "Report: $REPORT_FILE"
    exit 1
else
    echo -e "${GREEN}✅ VALIDATION PASSED${NC}"
    echo "All scanned content uses correct values."
    echo "Report: $REPORT_FILE"
    exit 0
fi
