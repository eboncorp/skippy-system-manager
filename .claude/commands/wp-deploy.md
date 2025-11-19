# WordPress Deployment Automation

Automate WordPress content deployment with built-in safety checks and session management.

## Instructions

When this skill is invoked, help the user deploy WordPress content with these automated steps:

### 1. Session Setup (MANDATORY)
```bash
# Determine deployment type
# - If editing local site: rundaverun-local
# - If editing production: rundaverun

SESSION_DIR="/home/dave/skippy/work/wordpress/{site}/$(date +%Y%m%d_%H%M%S)_{description}"
mkdir -p "$SESSION_DIR"
```

Ask the user:
- Which site? (local or production)
- Brief description for session directory name
- Which page/post IDs to update

### 2. Pre-Deployment Checks
Before any changes:
- Verify WordPress path exists and is accessible
- Test WP-CLI connectivity: `wp --path="..." db check`
- Confirm site URL matches expectations
- Check that Local by Flywheel is running (for local site)

### 3. Backup Original State
For each resource being modified:
```bash
wp post get {ID} --field=post_content > "$SESSION_DIR/page_{ID}_before.html"
```

### 4. Content Validation
CRITICAL: Before applying any content changes:
- Check for numbers/statistics in the new content
- Cross-reference against `/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md`
- Flag any discrepancies for user review
- Known correct values:
  - Total Budget: $81M (NOT $110.5M)
  - Public Safety Budget: $77.4M
  - Wellness Center ROI: $2-3 per $1 spent (NOT $1.80)
  - JCPS Reading: 34-35% (NOT 44%)
  - JCPS Math: 27-28% (NOT 41%)

### 5. Apply Changes
Save each iteration:
```bash
# v1, v2, v3... for each edit
# final version before applying
cp "$SESSION_DIR/page_{ID}_v{N}.html" "$SESSION_DIR/page_{ID}_final.html"

# Apply
wp post update {ID} --post_content="$(cat "$SESSION_DIR/page_{ID}_final.html")"
```

### 6. Verification (CRITICAL)
```bash
# Database verification
wp post get {ID} --field=post_content > "$SESSION_DIR/page_{ID}_after.html"
diff "$SESSION_DIR/page_{ID}_final.html" "$SESSION_DIR/page_{ID}_after.html"

# HTTP verification (if site is running)
SITE_URL=$(wp option get siteurl)
curl -I "$SITE_URL/?p={ID}" | grep "HTTP"
```

### 7. Documentation
Auto-generate README.md:
```bash
cat > "$SESSION_DIR/README.md" <<EOF
# Session: {Description}
**Date:** $(date)
**Resources Modified:** {list}
**Changes Made:** {summary}
**Status:** {verified/failed}
**Verification:** diff output
EOF
```

### 8. Rollback Support
If anything fails, provide rollback command:
```bash
wp post update {ID} --post_content="$(cat "$SESSION_DIR/page_{ID}_before.html")"
```

## Key Reminders
- NEVER use /tmp/ for any files
- ALWAYS save _before, _v{N}, _final, and _after versions
- ALWAYS run diff to verify updates
- Document everything in README.md
- Report session directory path to user at completion

## Usage Examples
- `/wp-deploy` - Start interactive deployment session
- User specifies: "Update homepage wellness stats"
- Skill handles: session creation, backups, validation, verification, documentation
