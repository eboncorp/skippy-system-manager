#!/bin/bash
# Script Index Generator v1.0.0
# Creates searchable catalog of all scripts
# Part of: Skippy Enhancement Project - TIER 2
# Created: 2025-11-04

set -euo pipefail

SKIPPY_BASE="/home/dave/skippy"
SCRIPTS_DIR="${SKIPPY_BASE}/scripts"
INDEX_FILE="${SKIPPY_BASE}/SCRIPT_INDEX.md"

echo "Generating script index..."

# Count scripts
TOTAL=$(find "$SCRIPTS_DIR" -type f \( -name "*.sh" -o -name "*.py" \) 2>/dev/null | wc -l)

# Start index file
cat > "$INDEX_FILE" <<EOF
# Skippy Script Index

**Last Updated:** $(date)
**Total Scripts:** $TOTAL
**Location:** $SCRIPTS_DIR

---

## Quick Search

\`\`\`bash
# Find by keyword
grep -i "backup" $INDEX_FILE

# Find by category
grep "Category:" $INDEX_FILE | grep "wordpress"

# List all scripts
grep "###" $INDEX_FILE
\`\`\`

---

## All Scripts

EOF

# Generate index
find "$SCRIPTS_DIR" -type f \( -name "*.sh" -o -name "*.py" \) | sort | while IFS= read -r script; do
    NAME=$(basename "$script")
    REL_PATH=$(echo "$script" | sed "s|$SKIPPY_BASE/||")
    CATEGORY=$(dirname "$script" | sed "s|$SCRIPTS_DIR/||" | cut -d/ -f1)
    SIZE=$(du -h "$script" | cut -f1)

    # Extract description
    DESC=$(head -10 "$script" | grep -m1 "^#.*" | sed 's/^# *//' | sed 's/#!//' || echo "Script")

    cat >> "$INDEX_FILE" <<EOF

### $NAME
**Path:** \`$REL_PATH\`
**Category:** $CATEGORY
**Size:** $SIZE
**Description:** $DESC

EOF
done

echo "✓ Index generated: $INDEX_FILE"
echo "  Total scripts indexed: $TOTAL"

exit 0
