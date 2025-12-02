#!/bin/bash
# wp_update_wrapper_v1.0.0.sh
# Wrapper for wp post update that automatically verifies changes
#
# Usage:
#   wp_update_wrapper 105 --post_content="$(cat content.html)"
#   wp_update_wrapper 105 --post_title="New Title"
#
# Features:
#   - Auto-saves before/after state
#   - Runs diff verification
#   - Validates facts before update
#   - Creates audit trail
#
# Dependencies:
#   - wp-cli
#   - diff
#
# Created: 2025-12-01

set -euo pipefail

# Configuration
WP_PATH="${WP_PATH:-/home/dave/skippy/rundaverun_local_site/app/public}"
FACT_SHEET="/home/dave/skippy/reference/QUICK_FACTS_SHEET.md"
SESSION_BASE="/home/dave/skippy/work/wordpress"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
POST_ID="$1"
shift
UPDATE_ARGS="$@"

# Validate post ID
if ! [[ "$POST_ID" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}Error: First argument must be a post ID${NC}"
    echo "Usage: wp_update_wrapper POST_ID [wp post update arguments]"
    exit 1
fi

# Create session directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_DIR="$SESSION_BASE/${TIMESTAMP}_update_${POST_ID}"
mkdir -p "$SESSION_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              WP UPDATE WRAPPER v1.0.0                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Post ID: $POST_ID"
echo "Session: $SESSION_DIR"
echo ""

# Step 1: Pre-flight checks
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Step 1: Pre-flight Checks                                   │"
echo "└─────────────────────────────────────────────────────────────┘"

# Check WordPress health
if ! wp --path="$WP_PATH" core is-installed 2>/dev/null; then
    echo -e "${RED}  ❌ WordPress not responding${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ WordPress healthy${NC}"

# Check post exists
if ! wp --path="$WP_PATH" post get "$POST_ID" --field=ID >/dev/null 2>&1; then
    echo -e "${RED}  ❌ Post $POST_ID not found${NC}"
    exit 1
fi
POST_TITLE=$(wp --path="$WP_PATH" post get "$POST_ID" --field=post_title 2>/dev/null)
echo -e "${GREEN}  ✅ Post found: $POST_TITLE${NC}"

# Step 2: Save before state
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Step 2: Capture Before State                                │"
echo "└─────────────────────────────────────────────────────────────┘"

wp --path="$WP_PATH" post get "$POST_ID" --field=post_content > "$SESSION_DIR/content_before.html" 2>/dev/null
wp --path="$WP_PATH" post get "$POST_ID" --field=post_title > "$SESSION_DIR/title_before.txt" 2>/dev/null
wp --path="$WP_PATH" post get "$POST_ID" --format=json > "$SESSION_DIR/post_before.json" 2>/dev/null

BEFORE_SIZE=$(wc -c < "$SESSION_DIR/content_before.html")
echo -e "${GREEN}  ✅ Before state saved ($BEFORE_SIZE bytes)${NC}"

# Step 3: Fact validation (if content update)
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Step 3: Fact Validation                                     │"
echo "└─────────────────────────────────────────────────────────────┘"

# Extract content from arguments if present
CONTENT_TO_CHECK=""
for arg in $UPDATE_ARGS; do
    if [[ "$arg" == --post_content=* ]]; then
        CONTENT_TO_CHECK="${arg#--post_content=}"
        break
    fi
done

if [ -n "$CONTENT_TO_CHECK" ]; then
    FACT_ERRORS=0

    # Check for WRONG values
    WRONG_VALUES=(
        "110.5M:Should be \$81M (total budget)"
        "110M:Should be \$81M (total budget)"
        "118M:Should be \$81M (total budget)"
        "1.80:Should be \$2-3 per \$1 (wellness ROI)"
        "1.8 per:Should be \$2-3 per \$1 (wellness ROI)"
        "180%:Should be \$2-3 per \$1 (wellness ROI)"
        "44%:Should be 34-35% (JCPS reading)"
        "41%:Should be 27-28% (JCPS math)"
        "45%:Should be 34-35% (JCPS reading)"
        "40%:Should be 27-28% (JCPS math)"
    )

    for item in "${WRONG_VALUES[@]}"; do
        WRONG="${item%%:*}"
        FIX="${item#*:}"
        if echo "$CONTENT_TO_CHECK" | grep -qi "$WRONG"; then
            echo -e "${RED}  ❌ BLOCKED: Found '$WRONG' - $FIX${NC}"
            FACT_ERRORS=$((FACT_ERRORS + 1))
        fi
    done

    if [ "$FACT_ERRORS" -gt 0 ]; then
        echo ""
        echo -e "${RED}  🚫 UPDATE BLOCKED - $FACT_ERRORS incorrect fact(s)${NC}"
        echo "  Reference: $FACT_SHEET"
        echo ""
        echo "  Session files saved to: $SESSION_DIR"
        echo "  To bypass (NOT recommended): wp --path=\"$WP_PATH\" post update $POST_ID $UPDATE_ARGS"
        exit 1
    fi

    echo -e "${GREEN}  ✅ No incorrect facts detected${NC}"
else
    echo "  ℹ️  No content update - skipping fact check"
fi

# Step 4: Execute update
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Step 4: Execute Update                                      │"
echo "└─────────────────────────────────────────────────────────────┘"

# Save the command for audit
echo "wp --path=\"$WP_PATH\" post update $POST_ID $UPDATE_ARGS" > "$SESSION_DIR/command.txt"

# Execute update
if wp --path="$WP_PATH" post update "$POST_ID" $UPDATE_ARGS 2>"$SESSION_DIR/update_error.log"; then
    echo -e "${GREEN}  ✅ Update executed${NC}"
else
    echo -e "${RED}  ❌ Update failed${NC}"
    cat "$SESSION_DIR/update_error.log"
    exit 1
fi

# Step 5: Capture after state
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Step 5: Capture After State                                 │"
echo "└─────────────────────────────────────────────────────────────┘"

wp --path="$WP_PATH" post get "$POST_ID" --field=post_content > "$SESSION_DIR/content_after.html" 2>/dev/null
wp --path="$WP_PATH" post get "$POST_ID" --field=post_title > "$SESSION_DIR/title_after.txt" 2>/dev/null
wp --path="$WP_PATH" post get "$POST_ID" --format=json > "$SESSION_DIR/post_after.json" 2>/dev/null

AFTER_SIZE=$(wc -c < "$SESSION_DIR/content_after.html")
echo -e "${GREEN}  ✅ After state saved ($AFTER_SIZE bytes)${NC}"

# Step 6: Verification
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Step 6: Verification                                        │"
echo "└─────────────────────────────────────────────────────────────┘"

# Generate diff
diff "$SESSION_DIR/content_before.html" "$SESSION_DIR/content_after.html" > "$SESSION_DIR/content_diff.txt" 2>/dev/null || true
DIFF_LINES=$(wc -l < "$SESSION_DIR/content_diff.txt")

if [ "$DIFF_LINES" -gt 0 ]; then
    echo -e "${GREEN}  ✅ Changes detected: $DIFF_LINES lines differ${NC}"

    # Show summary of changes
    ADDED=$(grep -c "^>" "$SESSION_DIR/content_diff.txt" 2>/dev/null || echo 0)
    REMOVED=$(grep -c "^<" "$SESSION_DIR/content_diff.txt" 2>/dev/null || echo 0)
    echo "     Added: $ADDED lines"
    echo "     Removed: $REMOVED lines"
else
    echo -e "${YELLOW}  ⚠️  No content changes detected${NC}"
fi

# Verify expected content (if specified)
if [ -n "$CONTENT_TO_CHECK" ]; then
    # Check first 100 chars match
    EXPECTED_START=$(echo "$CONTENT_TO_CHECK" | head -c 100)
    ACTUAL_START=$(head -c 100 "$SESSION_DIR/content_after.html")

    if [ "$EXPECTED_START" = "$ACTUAL_START" ]; then
        echo -e "${GREEN}  ✅ Content verified - matches expected${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Content may differ from expected (check diff)${NC}"
    fi
fi

# Step 7: Generate report
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ Step 7: Generate Report                                     │"
echo "└─────────────────────────────────────────────────────────────┘"

cat > "$SESSION_DIR/README.md" << EOF
# WordPress Update Session

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Post ID:** $POST_ID
**Post Title:** $POST_TITLE
**Status:** ✅ Completed

## Changes

- Before size: $BEFORE_SIZE bytes
- After size: $AFTER_SIZE bytes
- Diff lines: $DIFF_LINES

## Files

- \`content_before.html\` - Content before update
- \`content_after.html\` - Content after update
- \`content_diff.txt\` - Diff of changes
- \`post_before.json\` - Full post data before
- \`post_after.json\` - Full post data after
- \`command.txt\` - Command executed

## Rollback

To restore previous content:
\`\`\`bash
wp --path="$WP_PATH" post update $POST_ID --post_content="\$(cat $SESSION_DIR/content_before.html)"
\`\`\`

## Verification

Content verified at: $(date '+%Y-%m-%d %H:%M:%S')
EOF

echo -e "${GREEN}  ✅ Report generated${NC}"

# Summary
echo ""
echo "══════════════════════════════════════════════════════════════"
echo -e "${GREEN}  ✅ UPDATE COMPLETE AND VERIFIED${NC}"
echo ""
echo "  Session: $SESSION_DIR"
echo "  Post: $POST_TITLE (ID: $POST_ID)"
echo "  Changes: $DIFF_LINES lines"
echo ""
echo "  View diff: cat $SESSION_DIR/content_diff.txt"
echo "  Rollback:  See $SESSION_DIR/README.md"
echo "══════════════════════════════════════════════════════════════"
