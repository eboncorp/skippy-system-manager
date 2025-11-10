# WordPress Content Update Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-08
**Owner:** Claude Code / Dave

---

## Context

WordPress content updates (pages, posts, policies) require careful handling to prevent data loss, maintain accuracy, and ensure quality. This protocol defines the standard workflow for all WordPress content modifications.

## Purpose

- Prevent data loss through systematic backups
- Maintain audit trail of all changes
- Ensure content accuracy and quality
- Enable easy rollback if needed
- Verify updates succeeded

---

## When to Use This Protocol

**MANDATORY for:**
- ✅ Updating page content (homepage, about, policy pages)
- ✅ Updating post content (blog posts, news)
- ✅ Updating policy documents
- ✅ Bulk content updates
- ✅ Content migrations (markdown to HTML, etc.)
- ✅ Fixing typos, errors, or inaccuracies

**NOT needed for:**
- ❌ Reading content (wp post get for research)
- ❌ Checking page status
- ❌ Plugin/theme modifications (different protocol)

---

## Prerequisites

### Before Starting:
- [ ] Know the post/page ID(s) to update
- [ ] Have source content or know what changes to make
- [ ] Verify you have WordPress write permissions
- [ ] Know which site (rundaverun, rundaverun-local)
- [ ] Have fact-checked data if updating numbers/claims

### Required Tools:
- wp-cli installed and working
- Access to session directory structure
- Text editing tools (sed, awk, or manual edits)

---

## Standard Workflow

### Phase 1: Preparation

#### Step 1: Create Work Session Directory

```bash
# For production site updates
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_descriptive_name"
mkdir -p "$SESSION_DIR"

# For local development site updates
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_descriptive_name"
mkdir -p "$SESSION_DIR"

echo "Session directory: $SESSION_DIR"
```

**Naming Convention:**
- `homepage_roi_update` - Good
- `policy_699_budget_fix` - Good
- `page_updates` - Too vague
- `fixes` - Too vague

#### Step 2: Identify Target Content

```bash
# List all pages
wp post list --post_type=page --format=table

# List all policies (custom post type 'policy_document')
wp post list --post_type=policy_document --format=table

# Get specific post info
wp post get 105 --format=json | jq '.ID, .post_title, .post_status'
```

#### Step 3: Backup Original Content

```bash
# Save current content
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# Save metadata too (useful for reference)
wp post get 105 --format=json > "$SESSION_DIR/page_105_metadata.json"

# For multiple items
for ID in 105 699 716; do
  wp post get $ID --field=post_content > "$SESSION_DIR/resource_${ID}_before.html"
done
```

---

### Phase 2: Content Modification

#### Step 4: Create Updated Content

**Option A: Simple Text Replacement**
```bash
# Single replacement
cat "$SESSION_DIR/page_105_before.html" | \
  sed 's/old text/new text/g' > "$SESSION_DIR/page_105_v1.html"

# Multiple replacements
cat "$SESSION_DIR/page_105_before.html" | \
  sed 's/old1/new1/g' | \
  sed 's/old2/new2/g' | \
  sed 's/old3/new3/g' > "$SESSION_DIR/page_105_v1.html"
```

**Option B: Manual Editing**
```bash
# Copy to editor-friendly name
cp "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_v1.html"

# Edit manually (opens in default editor)
nano "$SESSION_DIR/page_105_v1.html"

# Or use your preferred editor
code "$SESSION_DIR/page_105_v1.html"
```

**Option C: Markdown to HTML Conversion**
```bash
# Copy source markdown
cp /source/policy.md "$SESSION_DIR/source.md"

# Convert to HTML
python3 <<PYEOF > "$SESSION_DIR/converted_v1.html"
import markdown
with open("$SESSION_DIR/source.md") as f:
    content = f.read()
html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
print(html)
PYEOF
```

**Option D: Fact-Checked Data Update**
```bash
# Reference fact sheet first!
cat /home/dave/rundaverun/campaign/FACT_SHEET.md

# Then make updates based on authoritative source
cat "$SESSION_DIR/policy_699_before.html" | \
  sed 's/\$110\.5M/\$81M/g' | \
  sed 's/\$1\.80/\$2-3/g' > "$SESSION_DIR/policy_699_v1.html"
```

#### Step 5: Review and Iterate

```bash
# Review changes
diff "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_v1.html"

# If more changes needed, create v2
cat "$SESSION_DIR/page_105_v1.html" | \
  sed 's/additional/changes/g' > "$SESSION_DIR/page_105_v2.html"

# Continue until satisfied
# v3, v4, etc. as needed
```

#### Step 6: Create Final Version

```bash
# Copy final iteration to "final" version
cp "$SESSION_DIR/page_105_v2.html" "$SESSION_DIR/page_105_final.html"

# Final review before applying
cat "$SESSION_DIR/page_105_final.html"
diff "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_final.html"
```

---

### Phase 3: Application

#### Step 7: Apply Update to WordPress

```bash
# Apply the update
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# Verify command succeeded
if [ $? -eq 0 ]; then
  echo "✅ Update command succeeded"
else
  echo "❌ Update command failed - investigate before proceeding"
  exit 1
fi
```

**For multiple items:**
```bash
for ID in 699 716 717; do
  echo "Updating resource $ID..."
  wp post update $ID --post_content="$(cat "$SESSION_DIR/resource_${ID}_final.html")"
  if [ $? -ne 0 ]; then
    echo "❌ Failed to update $ID - stopping"
    exit 1
  fi
  echo "✅ Updated $ID"
done
```

---

### Phase 4: Verification

#### Step 8: Verify Update Succeeded

```bash
# Get actual content from WordPress after update
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"

# Compare final vs actual (should be identical or minimal differences)
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# If differences exist, investigate:
# - WordPress may have sanitized/formatted HTML
# - Plugins may have filtered content
# - Encoding issues may have occurred
```

#### Step 9: Verify Specific Changes

```bash
# Check specific text/numbers were updated
grep "expected text" "$SESSION_DIR/page_105_after.html"

# Verify old text is gone
if grep -q "old text" "$SESSION_DIR/page_105_after.html"; then
  echo "❌ Old text still present - update may have failed"
else
  echo "✅ Old text removed successfully"
fi

# Verify new text is present
if grep -q "new text" "$SESSION_DIR/page_105_after.html"; then
  echo "✅ New text added successfully"
else
  echo "❌ New text not found - update may have failed"
fi
```

#### Step 10: Visual/Functional Verification

**Automated checks:**
```bash
# Run WordPress health check
bash /home/dave/skippy/scripts/wordpress/wordpress_comprehensive_diagnostic_v1.3.0.sh

# Check for broken links
wp post get 105 --field=post_content | grep -o 'href="[^"]*"' | while read link; do
  echo "Found link: $link"
done
```

**Manual checks (User must do):**
- [ ] Page renders correctly in browser
- [ ] Images display properly
- [ ] Links work correctly
- [ ] Mobile view looks good
- [ ] No JavaScript errors

---

### Phase 5: Documentation

#### Step 11: Document Changes

```bash
cat > "$SESSION_DIR/README.md" <<EOF
# WordPress Content Update - [Brief Description]

**Date:** $(date)
**Site:** [rundaverun / rundaverun-local]
**Resources Modified:** [Page 105, Policy 699, etc.]

## Changes Made

- Change 1: Description
- Change 2: Description
- Change 3: Description

## Resources Updated

| ID | Type | Title | Changes |
|----|------|-------|---------|
| 105 | Page | Homepage | Updated ROI figures |
| 699 | Policy | Budget Summary | Fixed budget numbers |

## Files in This Session

- page_105_before.html - Original content
- page_105_v1.html - First iteration
- page_105_v2.html - Second iteration
- page_105_final.html - Final version applied
- page_105_after.html - Verified actual state

## Verification

\`\`\`bash
diff page_105_final.html page_105_after.html
# Output: [no differences] or [expected differences noted]
\`\`\`

## Fact-Checking Sources

- Source 1: /home/dave/rundaverun/campaign/FACT_SHEET.md
- Source 2: [Other sources if applicable]

## Status

✅ Completed successfully
[or]
⚠️ Completed with notes: [describe any issues]
[or]
❌ Failed: [describe failure and next steps]

## Next Steps

- [Any follow-up tasks if needed]
EOF
```

---

## Complete Example: Homepage Budget Update

```bash
# 1. Create session
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_homepage_budget_update"
mkdir -p "$SESSION_DIR"

# 2. Backup original
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# 3. Check fact sheet for correct numbers
cat /home/dave/rundaverun/campaign/FACT_SHEET.md | grep -i budget

# 4. Make changes
cat "$SESSION_DIR/page_105_before.html" | \
  sed 's/\$110\.5M/\$81M/g' | \
  sed 's/\$47\.5M/\$77\.4M/g' > "$SESSION_DIR/page_105_v1.html"

# 5. Review changes
diff "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_v1.html"

# 6. Create final version
cp "$SESSION_DIR/page_105_v1.html" "$SESSION_DIR/page_105_final.html"

# 7. Apply update
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# 8. Verify update
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# 9. Verify specific changes
grep "\$81M" "$SESSION_DIR/page_105_after.html" && echo "✅ Budget 1 updated"
grep "\$77.4M" "$SESSION_DIR/page_105_after.html" && echo "✅ Budget 2 updated"

# 10. Document
cat > "$SESSION_DIR/README.md" <<EOF
# Homepage Budget Update
Date: $(date)
Updated budget figures to match fact sheet
Status: ✅ Verified successful
EOF

echo "✅ Session complete: $SESSION_DIR"
```

---

## Rollback Procedures

### If Update Failed or Was Incorrect:

```bash
# Rollback to original
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_before.html")"

# Verify rollback
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_rolledback.html"
diff "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_rolledback.html"
```

### If Need to Restore from Previous Session:

```bash
# Find previous session
ls -lt /home/dave/skippy/work/wordpress/rundaverun-local/ | grep homepage

# Restore from previous session
PREV_SESSION="/home/dave/skippy/work/wordpress/rundaverun-local/20251107_120000_homepage_update"
wp post update 105 --post_content="$(cat "$PREV_SESSION/page_105_before.html")"
```

---

## Common Scenarios

### Scenario 1: Fix Typo on Single Page

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_fix_typo_page_337"
mkdir -p "$SESSION_DIR"
wp post get 337 --field=post_content > "$SESSION_DIR/page_337_before.html"
cat "$SESSION_DIR/page_337_before.html" | sed 's/teh/the/g' > "$SESSION_DIR/page_337_v1.html"
cp "$SESSION_DIR/page_337_v1.html" "$SESSION_DIR/page_337_final.html"
wp post update 337 --post_content="$(cat "$SESSION_DIR/page_337_final.html")"
wp post get 337 --field=post_content > "$SESSION_DIR/page_337_after.html"
diff "$SESSION_DIR/page_337_final.html" "$SESSION_DIR/page_337_after.html"
```

### Scenario 2: Update Budget Numbers Across Multiple Policies

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_budget_standardization"
mkdir -p "$SESSION_DIR"

# Reference fact sheet
cat /home/dave/rundaverun/campaign/FACT_SHEET.md > "$SESSION_DIR/FACT_SHEET_reference.md"

# Process each policy
for ID in 699 700 716 717; do
  wp post get $ID --field=post_content > "$SESSION_DIR/policy_${ID}_before.html"
  cat "$SESSION_DIR/policy_${ID}_before.html" | \
    sed 's/\$110\.5M/\$81M/g' > "$SESSION_DIR/policy_${ID}_v1.html"
  cp "$SESSION_DIR/policy_${ID}_v1.html" "$SESSION_DIR/policy_${ID}_final.html"
  wp post update $ID --post_content="$(cat "$SESSION_DIR/policy_${ID}_final.html")"
  wp post get $ID --field=post_content > "$SESSION_DIR/policy_${ID}_after.html"
  diff "$SESSION_DIR/policy_${ID}_final.html" "$SESSION_DIR/policy_${ID}_after.html"
done
```

### Scenario 3: Convert Markdown to HTML for New Policy

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_new_policy_import"
mkdir -p "$SESSION_DIR"

# Copy source
cp /home/dave/rundaverun/campaign/downloads/policy_documents/HOUSING_POLICY.md "$SESSION_DIR/source.md"

# Convert
python3 <<PYEOF > "$SESSION_DIR/converted_v1.html"
import markdown
with open("$SESSION_DIR/source.md") as f:
    content = f.read()
html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
print(html)
PYEOF

# Review
cat "$SESSION_DIR/converted_v1.html"

# Apply
cp "$SESSION_DIR/converted_v1.html" "$SESSION_DIR/converted_final.html"
wp post update 331 --post_content="$(cat "$SESSION_DIR/converted_final.html")"
wp post get 331 --field=post_content > "$SESSION_DIR/policy_331_after.html"
```

---

## Pre-Flight Checklist

Before starting WordPress content update:
- [ ] Created session directory
- [ ] Identified page/post IDs
- [ ] Checked fact sheet for authoritative data (if updating numbers)
- [ ] Have clear idea of what changes to make

During update:
- [ ] Saved "before" state
- [ ] Created and reviewed iterations (v1, v2, etc.)
- [ ] Created "final" version
- [ ] Applied update to WordPress
- [ ] Saved "after" state for verification

After update:
- [ ] Ran diff to verify update succeeded
- [ ] Verified specific changes present
- [ ] Checked for broken links/errors
- [ ] Documented changes in README.md
- [ ] Reported session directory to user

---

## Error Handling

### If wp post update fails:

```bash
# Check WordPress is accessible
wp core version

# Check post exists
wp post get 105

# Check permissions
wp eval 'echo current_user_can("edit_posts") ? "yes" : "no";'

# Try with --skip-plugins if plugin conflict suspected
wp post update 105 --post_content="$(cat file.html)" --skip-plugins
```

### If content looks wrong after update:

1. Check diff between final and after
2. Look for WordPress HTML sanitization
3. Check for plugin content filters
4. Verify encoding (UTF-8)
5. Rollback if necessary

---

## Best Practices

### DO:
✅ Always create session directory first
✅ Always backup before making changes
✅ Always verify after applying updates
✅ Always document what changed and why
✅ Always check fact sheet for numbers/claims
✅ Use descriptive session names
✅ Save multiple iterations (v1, v2, v3)

### DON'T:
❌ Update WordPress content without backups
❌ Skip verification step
❌ Use /tmp/ for work files
❌ Copy numbers from existing WordPress content (use fact sheet)
❌ Make changes directly without reviewing first
❌ Forget to document changes

---

## Related Protocols

- [Work Files Preservation Protocol](../WORK_FILES_PRESERVATION_PROTOCOL.md) - Session directory structure
- [Verification Protocol](verification_protocol.md) - Verification procedures
- [Fact-Checking Protocol](fact_checking_protocol.md) - Data accuracy verification
- [WordPress Backup Protocol](wordpress_backup_protocol.md) - Backup before changes
- [Emergency Rollback Protocol](emergency_rollback_protocol.md) - If updates fail
- [Multi-Site WordPress Protocol](multi_site_wordpress_protocol.md) - Local vs production
- [Diagnostic & Debugging Protocol](diagnostic_debugging_protocol.md) - Troubleshooting issues

---

## Quick Reference

### Standard Update Flow:
```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/{site}/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"
wp post get {ID} --field=post_content > "$SESSION_DIR/{resource}_{id}_before.html"
cat "$SESSION_DIR/{resource}_{id}_before.html" | sed 's/old/new/g' > "$SESSION_DIR/{resource}_{id}_v1.html"
cp "$SESSION_DIR/{resource}_{id}_v1.html" "$SESSION_DIR/{resource}_{id}_final.html"
wp post update {ID} --post_content="$(cat "$SESSION_DIR/{resource}_{id}_final.html")"
wp post get {ID} --field=post_content > "$SESSION_DIR/{resource}_{id}_after.html"
diff "$SESSION_DIR/{resource}_{id}_final.html" "$SESSION_DIR/{resource}_{id}_after.html"
```

---

**Generated:** 2025-11-08
**Status:** Active
**Next Review:** 2025-12-08
```
