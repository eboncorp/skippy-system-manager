# WordPress Update Protocol

**Version:** 1.0.0
**Last Updated:** 2026-01-17

---

## Overview

This protocol defines the mandatory steps for all WordPress content updates to ensure data integrity and recoverability.

---

## The 7-Step Update Process

Every WordPress update MUST follow these steps:

### Step 1: Create Session Directory

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"
cd "$SESSION_DIR"
```

**NEVER use `/tmp/`** - files are lost on reboot.

---

### Step 2: Backup Original Content

```bash
# Get current content from WordPress
wp post get {ID} --field=post_content > page_{ID}_before.html

# Verify backup created
ls -la page_{ID}_before.html
```

---

### Step 3: Validate Campaign Facts

Before making any changes involving numbers:

| Check | Source |
|-------|--------|
| Budget figures | `QUICK_FACTS_SHEET.md` |
| Statistics | `QUICK_FACTS_SHEET.md` |
| Dates | Verify with authoritative source |
| Names | Double-check spelling |

```bash
# Search for numbers in content
grep -E '\$[0-9]+|[0-9]+%' page_{ID}_before.html
```

---

### Step 4: Make Edits with Iterations

```bash
# First edit
cp page_{ID}_before.html page_{ID}_v1.html
# Make changes to v1...

# If more changes needed
cp page_{ID}_v1.html page_{ID}_v2.html
# Make changes to v2...

# Continue as needed (v3, v4, etc.)
```

---

### Step 5: Create Final Version

```bash
# When satisfied with edits
cp page_{ID}_v2.html page_{ID}_final.html

# Review final version
cat page_{ID}_final.html
```

---

### Step 6: Apply Update to WordPress

```bash
# Update the post
wp post update {ID} --post_content="$(cat page_{ID}_final.html)" --allow-root

# Flush caches
wp cache flush --allow-root
```

---

### Step 7: Verify with Diff (NEVER SKIP)

```bash
# Get actual state after update
wp post get {ID} --field=post_content > page_{ID}_after.html

# Compare final vs actual
diff page_{ID}_final.html page_{ID}_after.html

# Verify specific expected text
grep "expected text" page_{ID}_after.html
```

**Interpreting Diff Results:**
- No output = Success (identical)
- Minor whitespace = Usually OK, verify content
- Major differences = STOP, investigate before proceeding

---

## File Naming Convention

| Stage | Filename | Purpose |
|-------|----------|---------|
| Original | `page_{ID}_before.html` | Backup of original state |
| Iteration 1 | `page_{ID}_v1.html` | First edit |
| Iteration 2 | `page_{ID}_v2.html` | Second edit |
| Ready to Apply | `page_{ID}_final.html` | Reviewed and approved |
| Verified | `page_{ID}_after.html` | Actual state from WP |

---

## Session Documentation

Create README.md in session directory:

```markdown
# Session: {Description}

**Date:** $(date)
**Status:** Completed | In Progress | Failed

## Changes Made
- [List specific changes]

## Pages Modified
- Page {ID}: {Title}

## Verification
- diff result: Clean/Issues found
- Visual check: ✅/❌

## Rollback Command
\`\`\`bash
wp post update {ID} --post_content="$(cat page_{ID}_before.html)" --allow-root
\`\`\`
```

---

## Rollback Procedure

If issues found after update:

```bash
# Restore from before file
wp post update {ID} --post_content="$(cat page_{ID}_before.html)" --allow-root

# Flush caches
wp cache flush --allow-root

# Verify rollback
wp post get {ID} --field=post_content > page_{ID}_after_rollback.html
diff page_{ID}_before.html page_{ID}_after_rollback.html
```

---

## Production Updates

For production site, use SSH pattern:

```bash
SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun \
  git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com \
  'cd html && wp post update {ID} --post_content="$(cat /tmp/content.html)" --allow-root'
```

Always flush caches after production updates.

---

## Related

- Backup Workflow
- Deployment Workflow
- Content Migration Workflow
