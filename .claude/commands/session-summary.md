---
description: Generate comprehensive session summary with file changes, verification results, and rollback instructions
argument-hint: "[optional: session_directory_path]"
allowed-tools: ["Bash", "Read", "Write", "Glob"]
---

# Session Summary Generator

Automatically create comprehensive README.md documentation for work sessions.

## Instructions

When this skill is invoked, generate a complete session summary:

### 1. Identify Session Directory
Ask the user or auto-detect:
```bash
# Most recent session
LATEST_SESSION=$(ls -dt /home/dave/skippy/work/*/* 2>/dev/null | head -1)

# Or specify
SESSION_DIR="/home/dave/skippy/work/{category}/{timestamp_description}"

# Verify exists
if [ ! -d "$SESSION_DIR" ]; then
  echo "ERROR: Session directory not found"
  exit 1
fi
```

### 2. Analyze Session Contents
```bash
cd "$SESSION_DIR"

# List all files
echo "Files in session:"
ls -la

# Categorize files
BEFORE_FILES=$(ls *_before.* 2>/dev/null)
ITERATION_FILES=$(ls *_v[0-9]*.* 2>/dev/null)
FINAL_FILES=$(ls *_final.* 2>/dev/null)
AFTER_FILES=$(ls *_after.* 2>/dev/null)
LOG_FILES=$(ls *.log 2>/dev/null)
REPORT_FILES=$(ls *.md 2>/dev/null | grep -v README)
```

### 3. Extract Session Metadata
```bash
# Parse directory name for info
DIR_NAME=$(basename "$SESSION_DIR")
TIMESTAMP=$(echo "$DIR_NAME" | cut -d_ -f1-2)
DESCRIPTION=$(echo "$DIR_NAME" | cut -d_ -f3-)

# Convert timestamp
SESSION_DATE=$(date -d "${TIMESTAMP:0:8} ${TIMESTAMP:9:2}:${TIMESTAMP:11:2}:${TIMESTAMP:13:2}" "+%B %d, %Y at %H:%M:%S" 2>/dev/null || echo "$TIMESTAMP")

# Determine session type
if echo "$SESSION_DIR" | grep -q "wordpress"; then
  SESSION_TYPE="WordPress Content Update"
elif echo "$SESSION_DIR" | grep -q "security"; then
  SESSION_TYPE="Security Audit"
elif echo "$SESSION_DIR" | grep -q "scripts"; then
  SESSION_TYPE="Script Development"
elif echo "$SESSION_DIR" | grep -q "git"; then
  SESSION_TYPE="Git Operations"
else
  SESSION_TYPE="General Work Session"
fi
```

### 4. Analyze Changes Made
```bash
# For WordPress sessions, extract post IDs
if [ -n "$BEFORE_FILES" ]; then
  echo "Resources modified:"
  for f in $BEFORE_FILES; do
    # Extract ID from filename (page_105_before.html -> 105)
    ID=$(echo "$f" | grep -o '[0-9]\+')
    echo "- Post/Page ID: $ID"
  done
fi

# Check if diffs were run
if [ -n "$AFTER_FILES" ] && [ -n "$FINAL_FILES" ]; then
  echo "Verification status: Changes were verified"
else
  echo "WARNING: No verification files found"
fi
```

### 4b. Extract WordPress-Specific Context (NEW)
```bash
# For WordPress sessions, extract additional context
if echo "$SESSION_DIR" | grep -q "wordpress"; then

  # Extract page/post IDs from filenames
  PAGE_IDS=$(ls *_{before,final,after}.* 2>/dev/null | grep -oP '(page|post|policy)_\K\d+' | sort -u)

  # Find related fact-check records
  for PAGE_ID in $PAGE_IDS; do
    FACT_CHECK=$(find ~/.claude/content-vault/fact-checks/ -name "${PAGE_ID}_*.fact-checked" 2>/dev/null | head -1)
    if [ -n "$FACT_CHECK" ]; then
      FACT_CHECK_TIME=$(stat -c %y "$FACT_CHECK" | cut -d' ' -f1,2 | cut -d'.' -f1)
      FACT_COUNT=$(jq -r '.facts_verified | length' "$FACT_CHECK" 2>/dev/null || echo "unknown")
      echo "Fact-check for page ${PAGE_ID}: ${FACT_COUNT} facts verified at ${FACT_CHECK_TIME}"
    fi
  done

  # Find related approval records
  for PAGE_ID in $PAGE_IDS; do
    APPROVAL=$(find ~/.claude/content-vault/approvals/ -name "${PAGE_ID}_*.approved" 2>/dev/null | head -1)
    if [ -n "$APPROVAL" ]; then
      APPROVER=$(jq -r '.approver' "$APPROVAL" 2>/dev/null || echo "unknown")
      APPROVAL_TIME=$(jq -r '.timestamp' "$APPROVAL" 2>/dev/null || echo "unknown")
      APPROVAL_NOTES=$(jq -r '.notes' "$APPROVAL" 2>/dev/null || echo "")
      echo "Approval for page ${PAGE_ID}: by ${APPROVER} at ${APPROVAL_TIME}"
      [ -n "$APPROVAL_NOTES" ] && echo "  Notes: ${APPROVAL_NOTES}"
    fi
  done

  # Find audit trail records
  AUDIT_MONTH=$(date +%Y-%m)
  for PAGE_ID in $PAGE_IDS; do
    AUDIT_RECORDS=$(find ~/.claude/content-vault/audit-log/${AUDIT_MONTH}/ -name "${PAGE_ID}_*.audit" 2>/dev/null | wc -l)
    [ $AUDIT_RECORDS -gt 0 ] && echo "Audit trail: ${AUDIT_RECORDS} record(s) for page ${PAGE_ID}"
  done
fi
```

### 5. Generate Comprehensive README
```bash
cat > "$SESSION_DIR/README.md" <<EOF
# Session: ${DESCRIPTION//_/ }

**Created:** $SESSION_DATE
**Type:** $SESSION_TYPE
**Directory:** $SESSION_DIR

---

## Overview
{Brief description of what was accomplished in this session}

## Resources Modified
EOF

# Add modified resources
if [ -n "$BEFORE_FILES" ]; then
  for f in $BEFORE_FILES; do
    ID=$(echo "$f" | grep -o '[0-9]\+')
    TYPE=$(echo "$f" | sed 's/_[0-9].*$//')
    echo "- **${TYPE^} $ID**" >> "$SESSION_DIR/README.md"
  done
fi

cat >> "$SESSION_DIR/README.md" <<EOF

## Changes Made
1. {First change description}
2. {Second change description}
3. {Additional changes...}

## Files in This Session

### Original State (Before)
EOF

for f in $BEFORE_FILES; do
  echo "- \`$f\` - Original content before any modifications" >> "$SESSION_DIR/README.md"
done

cat >> "$SESSION_DIR/README.md" <<EOF

### Iterations
EOF

for f in $ITERATION_FILES; do
  VERSION=$(echo "$f" | grep -o 'v[0-9]\+')
  echo "- \`$f\` - Edit iteration $VERSION" >> "$SESSION_DIR/README.md"
done

cat >> "$SESSION_DIR/README.md" <<EOF

### Final Version
EOF

for f in $FINAL_FILES; do
  echo "- \`$f\` - Final version applied to system" >> "$SESSION_DIR/README.md"
done

cat >> "$SESSION_DIR/README.md" <<EOF

### Verification (After)
EOF

for f in $AFTER_FILES; do
  echo "- \`$f\` - Actual state after update (for verification)" >> "$SESSION_DIR/README.md"
done

cat >> "$SESSION_DIR/README.md" <<EOF

## Verification Results
EOF

# Run diffs and capture results
if [ -n "$FINAL_FILES" ] && [ -n "$AFTER_FILES" ]; then
  FINAL_FILE=$(echo "$FINAL_FILES" | head -1)
  AFTER_FILE=$(echo "$AFTER_FILES" | head -1)

  DIFF_RESULT=$(diff "$FINAL_FILE" "$AFTER_FILE" 2>&1)

  if [ -z "$DIFF_RESULT" ]; then
    echo "✅ **VERIFIED:** Updates applied successfully (no differences between final and after)" >> "$SESSION_DIR/README.md"
  else
    echo "⚠️ **DIFFERENCES FOUND:** Review required" >> "$SESSION_DIR/README.md"
    echo '```' >> "$SESSION_DIR/README.md"
    echo "$DIFF_RESULT" | head -20 >> "$SESSION_DIR/README.md"
    echo '```' >> "$SESSION_DIR/README.md"
  fi
else
  echo "⚠️ **NOT VERIFIED:** Missing final or after files" >> "$SESSION_DIR/README.md"
fi

cat >> "$SESSION_DIR/README.md" <<EOF

## Status
- [ ] Changes applied
- [ ] Verification completed
- [ ] Documentation updated
- [ ] Notified user

## Rollback Instructions
If you need to revert these changes:
\`\`\`bash
EOF

for f in $BEFORE_FILES; do
  ID=$(echo "$f" | grep -o '[0-9]\+')
  echo "wp post update $ID --post_content=\"\$(cat $SESSION_DIR/$f)\"" >> "$SESSION_DIR/README.md"
done

cat >> "$SESSION_DIR/README.md" <<EOF
\`\`\`

## Session Statistics
- **Total files:** $(ls -1 | wc -l)
- **Before files:** $(echo "$BEFORE_FILES" | wc -w)
- **Iterations:** $(echo "$ITERATION_FILES" | wc -w)
- **Final files:** $(echo "$FINAL_FILES" | wc -w)
- **After files:** $(echo "$AFTER_FILES" | wc -w)
- **Session size:** $(du -sh . | cut -f1)

## Notes
{Any additional notes, observations, or follow-up tasks}

---
*Session documented by Claude Code Session Summary Generator*
*Report generated: $(date)*
EOF

echo "README.md generated successfully at $SESSION_DIR/README.md"
```

### 6. Add to Session Index
```bash
# Append to master session log
SESSION_LOG="/home/dave/skippy/work/SESSION_LOG.md"

if [ ! -f "$SESSION_LOG" ]; then
  cat > "$SESSION_LOG" <<EOF
# Work Session Log
Chronological log of all work sessions.

---
EOF
fi

cat >> "$SESSION_LOG" <<EOF

## $SESSION_DATE
**Type:** $SESSION_TYPE
**Directory:** $SESSION_DIR
**Summary:** ${DESCRIPTION//_/ }
**Files:** $(ls -1 "$SESSION_DIR" | wc -l) files, $(du -sh "$SESSION_DIR" | cut -f1)

EOF
```

### 7. Quick Summary Mode
For rapid documentation without full analysis:
```bash
# Minimal README
cat > "$SESSION_DIR/README.md" <<EOF
# ${DESCRIPTION//_/ }
**Date:** $(date)
**Path:** $SESSION_DIR
**Status:** ✅ Completed

Files:
$(ls -1)
EOF
```

## Usage
- `/session-summary` - Generate comprehensive session documentation
- Auto-analyzes session contents
- Creates rollback instructions
- Verifies changes were successful
- Maintains session index log

## Best Practices
- Run at END of every work session
- Ensures documentation is complete before moving on
- Provides rollback safety net
- Maintains audit trail of all changes

## Integration with Other Skills
- **After /wp-deploy:** Generate summary of deployment
- **After /security-audit:** Document findings
- **After /git-branches:** Record branch analysis results
- **Before session end:** Always generate summary
