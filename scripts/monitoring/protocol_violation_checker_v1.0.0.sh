#!/bin/bash
# Protocol Violation Detection Script
# Version: 1.0.0
# Purpose: Audit recent work sessions for protocol compliance
# Usage: bash protocol_violation_checker_v1.0.0.sh [days_to_check]

VERSION="1.0.0"
DAYS_TO_CHECK="${1:-7}"  # Default: check last 7 days
WORK_DIR="/home/dave/skippy/work"
REPORT_FILE="/home/dave/skippy/conversations/protocol_violations_$(date +%Y-%m-%d).md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TOTAL_SESSIONS=0
VIOLATIONS_FOUND=0
TMP_USAGE=0
MISSING_AFTER=0
MISSING_README=0
NO_SESSION_DIR=0

echo "=== Protocol Violation Checker v$VERSION ==="
echo "Checking last $DAYS_TO_CHECK days of work sessions..."
echo ""

# Find session directories from last N days
SESSION_DIRS=$(find "$WORK_DIR" -mindepth 3 -maxdepth 3 -type d -mtime -$DAYS_TO_CHECK | sort)

if [ -z "$SESSION_DIRS" ]; then
  echo "No sessions found in last $DAYS_TO_CHECK days."
  exit 0
fi

# Initialize report
cat > "$REPORT_FILE" <<EOF
# Protocol Violation Report
**Date:** $(date)
**Period:** Last $DAYS_TO_CHECK days
**Checker Version:** $VERSION

---

## Summary

EOF

# Check each session
while IFS= read -r session; do
  ((TOTAL_SESSIONS++))
  SESSION_NAME=$(basename "$session")
  SESSION_PATH=$(dirname "$session" | xargs basename)/$(basename "$session")

  # Check 1: /tmp/ usage
  if find "$session" -type f -exec grep -l "/tmp/" {} \; 2>/dev/null | grep -q .; then
    ((TMP_USAGE++))
    ((VIOLATIONS_FOUND++))
    echo -e "${RED}❌ /tmp/ usage${NC} in $SESSION_PATH"
  fi

  # Check 2: Missing _after files
  HAS_FINAL=$(find "$session" -name "*_final.html" | wc -l)
  HAS_AFTER=$(find "$session" -name "*_after.html" | wc -l)

  if [ "$HAS_FINAL" -gt 0 ] && [ "$HAS_AFTER" -eq 0 ]; then
    ((MISSING_AFTER++))
    ((VIOLATIONS_FOUND++))
    echo -e "${RED}❌ Missing _after.html${NC} in $SESSION_PATH"
  fi

  # Check 3: Missing README.md
  if [ ! -f "$session/README.md" ] && [ ! -f "$session/session_notes.txt" ]; then
    ((MISSING_README++))
    ((VIOLATIONS_FOUND++))
    echo -e "${YELLOW}⚠️  Missing README.md${NC} in $SESSION_PATH"
  fi

done <<< "$SESSION_DIRS"

# Calculate compliance rate
if [ $TOTAL_SESSIONS -gt 0 ]; then
  COMPLIANCE_RATE=$(( (TOTAL_SESSIONS - VIOLATIONS_FOUND) * 100 / TOTAL_SESSIONS ))
else
  COMPLIANCE_RATE=100
fi

# Print summary
echo ""
echo "=== Violation Summary ==="
echo "Total Sessions: $TOTAL_SESSIONS"
echo "Sessions with Violations: $VIOLATIONS_FOUND"
echo "Compliance Rate: ${COMPLIANCE_RATE}%"
echo ""
echo "Violation Breakdown:"
echo "  /tmp/ usage: $TMP_USAGE"
echo "  Missing _after files: $MISSING_AFTER"
echo "  Missing README.md: $MISSING_README"
echo ""

# Add to report
cat >> "$REPORT_FILE" <<EOF
**Total Sessions Checked:** $TOTAL_SESSIONS
**Sessions with Violations:** $VIOLATIONS_FOUND
**Compliance Rate:** ${COMPLIANCE_RATE}%

### Violation Breakdown

| Violation Type | Count |
|----------------|-------|
| /tmp/ usage | $TMP_USAGE |
| Missing _after.html files | $MISSING_AFTER |
| Missing README.md | $MISSING_README |

---

## Detailed Findings

EOF

# Add detailed findings to report
while IFS= read -r session; do
  SESSION_NAME=$(basename "$session")
  SESSION_PATH=$(dirname "$session" | xargs basename)/$(basename "$session")

  VIOLATIONS_IN_SESSION=""

  # Check violations again for report
  if find "$session" -type f -exec grep -l "/tmp/" {} \; 2>/dev/null | grep -q .; then
    VIOLATIONS_IN_SESSION="${VIOLATIONS_IN_SESSION}\n  - ❌ Uses /tmp/ directory"
  fi

  HAS_FINAL=$(find "$session" -name "*_final.html" | wc -l)
  HAS_AFTER=$(find "$session" -name "*_after.html" | wc -l)

  if [ "$HAS_FINAL" -gt 0 ] && [ "$HAS_AFTER" -eq 0 ]; then
    VIOLATIONS_IN_SESSION="${VIOLATIONS_IN_SESSION}\n  - ❌ Missing _after.html verification files"
  fi

  if [ ! -f "$session/README.md" ] && [ ! -f "$session/session_notes.txt" ]; then
    VIOLATIONS_IN_SESSION="${VIOLATIONS_IN_SESSION}\n  - ⚠️  Missing README.md documentation"
  fi

  # Add to report if violations found
  if [ -n "$VIOLATIONS_IN_SESSION" ]; then
    cat >> "$REPORT_FILE" <<EOF
### $SESSION_PATH
EOF
    echo -e "$VIOLATIONS_IN_SESSION" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
  fi

done <<< "$SESSION_DIRS"

# Add recommendations
cat >> "$REPORT_FILE" <<EOF

---

## Recommendations

### If /tmp/ usage detected:
1. Review CLAUDE.md prohibition on /tmp/ usage
2. Update sessions to use SESSION_DIR instead
3. Add /tmp/ detection to pre-commit hooks

### If _after.html files missing:
1. Emphasize Step 6 (Verification) in protocols
2. Add verification to session checklist
3. Review Verification Protocol

### If README.md files missing:
1. Add README creation to session checklist
2. Review Report Generation Protocol
3. Consider making README.md mandatory

---

**Compliance Target:** 100%
**Current Rate:** ${COMPLIANCE_RATE}%
**Gap:** $((100 - COMPLIANCE_RATE))%

**Next Check:** $(date -d "+7 days" +%Y-%m-%d)
EOF

# Final output
if [ "$VIOLATIONS_FOUND" -gt 0 ]; then
  echo -e "${RED}⚠️  Protocol violations detected!${NC}"
  echo "Report saved to: $REPORT_FILE"
  exit 1
else
  echo -e "${GREEN}✅ All sessions compliant!${NC}"
  echo "Report saved to: $REPORT_FILE"
  exit 0
fi
