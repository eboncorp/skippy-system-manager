# Emergency Rollback Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-08
**Owner:** Claude Code / Dave
**Priority:** CRITICAL

---

## Context

When WordPress updates go wrong or content is accidentally deleted/corrupted, quick rollback procedures can restore functionality. This protocol provides emergency procedures for various rollback scenarios.

## Purpose

- Restore site functionality quickly
- Minimize downtime
- Recover from failed updates
- Provide step-by-step emergency procedures

---

## 🚨 Emergency Scenarios

### Scenario 1: Bad Content Update (Most Common)
**Symptoms:** Wrong content published, typos, incorrect data
**Impact:** Low - content issue only
**Recovery Time:** < 5 minutes

### Scenario 2: Multiple Pages Affected
**Symptoms:** Bulk update went wrong
**Impact:** Medium - multiple pages affected
**Recovery Time:** 5-15 minutes

### Scenario 3: Site Breaking Change
**Symptoms:** Site won't load, PHP errors, broken functionality
**Impact:** High - site down
**Recovery Time:** 15-30 minutes

### Scenario 4: Database Corruption
**Symptoms:** Database errors, can't access WordPress
**Impact:** Critical - site completely down
**Recovery Time:** 30-60 minutes

---

## Quick Recovery Decision Tree

```
Is the site loading?
├─ YES → Content issue (Scenario 1 or 2)
│   ├─ Single page wrong → Use Scenario 1 procedure
│   └─ Multiple pages wrong → Use Scenario 2 procedure
│
└─ NO → Site broken (Scenario 3 or 4)
    ├─ PHP errors showing → Use Scenario 3 procedure
    └─ Database errors → Use Scenario 4 procedure
```

---

## Scenario 1: Bad Content Update (Single Page)

### Step 1: Identify Problem

```bash
# Check current content
wp post get 105 --field=post_title
wp post get 105 --field=post_content | head -50
```

### Step 2: Find Last Good Version

```bash
# Find recent session directories
ls -lt /home/dave/skippy/work/wordpress/{site}/ | head -10

# Identify session with the update
cd [session_directory]
ls -la

# Check if _before file exists
ls -la *_before.html
```

### Step 3: Rollback

```bash
SESSION_DIR="[path to session directory]"

# Restore from before state
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_before.html")"

# Verify rollback
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after_rollback.html"
diff "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_after_rollback.html"
```

### Step 4: Verify Site

```bash
# Check page loads
curl -I http://site-url/page-slug/ | head -1

# Verify content
wp post get 105 --field=post_content | grep "expected text"
```

**Time to Recovery:** 2-5 minutes

---

## Scenario 2: Multiple Pages Affected

### Step 1: List Affected Pages

```bash
# Identify which pages need rollback
# Example: pages 105, 699, 716, 717
AFFECTED_IDS="105 699 716 717"
```

### Step 2: Find Session Directory

```bash
# Find recent bulk update session
ls -lt /home/dave/skippy/work/wordpress/{site}/ | grep -E "budget|bulk|multiple"

SESSION_DIR="[identified session directory]"
cd "$SESSION_DIR"
ls -la *_before.html
```

### Step 3: Rollback All Pages

```bash
# Rollback each page
for ID in $AFFECTED_IDS; do
  echo "Rolling back page $ID..."

  # Find before file (may be page_* or policy_*)
  BEFORE_FILE=$(ls -1 *_${ID}_before.html 2>/dev/null | head -1)

  if [ -f "$BEFORE_FILE" ]; then
    wp post update $ID --post_content="$(cat "$BEFORE_FILE")"
    echo "✅ Rolled back page $ID"
  else
    echo "⚠️ No backup found for page $ID"
  fi
done
```

### Step 4: Verify All Pages

```bash
# Check each page
for ID in $AFFECTED_IDS; do
  STATUS=$(wp post get $ID --field=post_status)
  TITLE=$(wp post get $ID --field=post_title)
  echo "Page $ID: $TITLE ($STATUS)"
done
```

**Time to Recovery:** 5-15 minutes

---

## Scenario 3: Site Breaking Change

### Step 1: Identify Error

```bash
# Check if WordPress loads
curl -I http://site-url/ | head -1

# Check for PHP errors
tail -50 /path/to/wordpress/wp-content/debug.log

# Or check server error log
sudo tail -50 /var/log/apache2/error.log
```

### Step 2: Quick Fixes First

```bash
# Try clearing caches
wp cache flush
wp rewrite flush

# Deactivate recently activated plugins
wp plugin list --status=active

# Deactivate suspect plugin
wp plugin deactivate plugin-name

# Test if site loads
curl -I http://site-url/ | head -1
```

### Step 3: Database Rollback (If needed)

```bash
# Find recent database backup
ls -lt /home/dave/skippy/work/wordpress/{site}/*/db_backup*.sql.gz | head -5

# Backup current state first
wp db export "/home/dave/skippy/emergency_pre_rollback_$(date +%Y%m%d_%H%M%S).sql"

# Restore from backup
BACKUP_FILE="[identified backup file]"
gunzip -c "$BACKUP_FILE" | wp db import -

# Flush caches
wp cache flush
wp rewrite flush
```

### Step 4: Verify Site Functionality

```bash
# Check homepage loads
curl -I http://site-url/ | head -1

# Check admin loads
curl -I http://site-url/wp-admin/ | head -1

# Test critical pages
for SLUG in "about-dave" "our-plan" "get-involved"; do
  curl -I "http://site-url/$SLUG/" | head -1
done
```

**Time to Recovery:** 15-30 minutes

---

## Scenario 4: Database Corruption

### Step 1: Confirm Database Issue

```bash
# Try to connect
wp db check

# Check database status
wp db query "SHOW TABLES;"
```

### Step 2: Find Latest Good Backup

```bash
# Search all session directories for database backups
find /home/dave/skippy/work/wordpress/{site}/ -name "db_backup*.sql.gz" -type f | sort -r | head -5

# Check backup dates
for file in $(find /home/dave/skippy/work/wordpress/{site}/ -name "db_backup*.sql.gz" | sort -r | head -3); do
  echo "$file: $(stat -c %y "$file")"
done
```

### Step 3: Restore Database

```bash
# ⚠️ CRITICAL: This overwrites entire database

# 1. Export corrupted database (for analysis)
wp db export "/home/dave/skippy/corrupted_db_$(date +%Y%m%d_%H%M%S).sql" 2>/dev/null || echo "Export failed"

# 2. Select backup
BACKUP_FILE="[chosen backup file]"

# 3. Decompress and import
gunzip -c "$BACKUP_FILE" | wp db import -

# 4. Repair tables
wp db repair

# 5. Optimize
wp db optimize
```

### Step 4: Comprehensive Verification

```bash
# Check database
wp db check

# Check tables
wp db query "SHOW TABLES;" | wc -l

# Check site loads
curl -I http://site-url/ | head -1

# Run diagnostic
bash /home/dave/skippy/scripts/wordpress/wordpress_comprehensive_diagnostic_v1.3.0.sh
```

**Time to Recovery:** 30-60 minutes

---

## Emergency Contact Information

If rollback fails or issues persist:

1. **GoDaddy Support:** (for production site)
   - Phone: [Add number]
   - Account: [Add account info]

2. **Backup Locations:**
   - Session directories: `/home/dave/skippy/work/wordpress/{site}/`
   - Emergency backups: `/home/dave/skippy/emergency_backup_*.sql`

3. **Critical Files:**
   - CLAUDE.md: `/home/dave/.claude/CLAUDE.md`
   - Protocols: `/home/dave/skippy/documentation/protocols/`
   - Quick Reference: `/home/dave/skippy/documentation/PROTOCOL_QUICK_REFERENCE.md`

---

## Prevention

To minimize need for emergency rollbacks:

1. **Always Test Locally First:**
   - Use rundaverun-local for testing
   - Only deploy to production after verification

2. **Create Backups Before Changes:**
   - Follow WordPress Backup Protocol
   - Verify backups created successfully

3. **Use Session Directories:**
   - Save _before state always
   - Save _after state for verification
   - Document changes in README.md

4. **Verify Updates:**
   - Run diff after every update
   - Check specific content present
   - Test page loads

---

## Post-Rollback Actions

After successful rollback:

1. **Document What Happened:**
```bash
cat > "/home/dave/skippy/conversations/emergency_rollback_$(date +%Y-%m-%d).md" <<EOF
# Emergency Rollback - $(date)

## Problem
[What went wrong]

## Solution
[How it was fixed]

## Rollback Procedure Used
Scenario [1/2/3/4]

## Recovery Time
[minutes]

## Prevention
[How to avoid this in future]
EOF
```

2. **Identify Root Cause:**
   - What caused the problem?
   - Was protocol followed correctly?
   - What can prevent recurrence?

3. **Update Protocols If Needed:**
   - Did protocol work well?
   - Should emergency procedure be improved?
   - Any gaps in current protocols?

---

## Quick Command Reference

```bash
# Find recent session directories
ls -lt /home/dave/skippy/work/wordpress/{site}/ | head -10

# Rollback single page
wp post update {ID} --post_content="$(cat session_dir/page_{ID}_before.html)"

# Rollback database
gunzip -c db_backup.sql.gz | wp db import -

# Clear caches
wp cache flush && wp rewrite flush

# Check site status
curl -I http://site-url/ | head -1

# Quick database backup
wp db export "/home/dave/skippy/emergency_$(date +%Y%m%d_%H%M%S).sql"

# Deactivate all plugins
wp plugin deactivate --all

# List recent database backups
find /home/dave/skippy/work/wordpress/{site}/ -name "db_backup*.sql.gz" | sort -r | head -5
```

---

## Related Protocols

- [WordPress Backup Protocol](wordpress_backup_protocol.md)
- [WordPress Content Update Protocol](wordpress_content_update_protocol.md)
- [Diagnostic & Debugging Protocol](diagnostic_debugging_protocol.md)
- [Verification Protocol](verification_protocol.md)

---

**Generated:** 2025-11-08
**Status:** Active - CRITICAL
**Next Review:** 2025-12-08

**🚨 BOOKMARK THIS PROTOCOL FOR EMERGENCIES!**
