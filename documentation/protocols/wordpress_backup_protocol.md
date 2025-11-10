# WordPress Backup Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-08
**Owner:** Claude Code / Dave

---

## Context

Before making WordPress changes, create backups to enable quick rollback if needed. This protocol defines when and how to backup WordPress content and databases.

## Purpose

- Enable quick rollback if updates fail
- Preserve known-good states
- Provide safety net for risky operations
- Document backup procedures

---

## When to Backup

### MANDATORY Backups:
- ✅ Before bulk updates (multiple pages/posts)
- ✅ Before risky operations (experimental changes)
- ✅ Before production deployments
- ✅ Before database modifications
- ✅ Before plugin updates

### OPTIONAL Backups (Already Covered):
- ⏭️ Single page updates (session directory `_before` files sufficient)
- ⏭️ Local site changes (can rebuild from production)

---

## Backup Types

### 1. Content Backup (Session Directory)

**Used for:** Single/multiple content updates

```bash
# Included in standard WordPress update workflow
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"
```

**Restore:**
```bash
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_before.html")"
```

### 2. Database Backup (Full)

**Used for:** Major changes, bulk operations, production deployments

```bash
# Create database backup
wp db export "$SESSION_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"

# Compress to save space
gzip "$SESSION_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
```

**Restore:**
```bash
# Decompress
gunzip db_backup_20251108_120000.sql.gz

# Import (CAUTION: Overwrites current database)
wp db import db_backup_20251108_120000.sql
```

### 3. Files Backup (Uploads)

**Used for:** Media changes, theme modifications

```bash
# Backup uploads directory
tar -czf "$SESSION_DIR/uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz" \
  wp-content/uploads/

# Backup specific theme
tar -czf "$SESSION_DIR/theme_backup.tar.gz" \
  wp-content/themes/astra-child/
```

**Restore:**
```bash
# Extract to original location
tar -xzf uploads_backup_20251108_120000.tar.gz -C /path/to/wordpress/
```

---

## Standard Backup Workflow

### For Major Content Updates:

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/{site}/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# 1. Backup all pages being modified
for ID in 105 699 716 717; do
  wp post get $ID --field=post_content > "$SESSION_DIR/backup_page_${ID}.html"
done

# 2. Create database snapshot (optional, for major changes)
wp db export "$SESSION_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
gzip "$SESSION_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"

# 3. Document what's backed up
cat > "$SESSION_DIR/BACKUP_INFO.md" <<EOF
# Backup Information
Date: $(date)
Pages backed up: 105, 699, 716, 717
Database backup: Yes (compressed)
Files backup: No
EOF
```

### For Production Deployment:

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_production_deployment"
mkdir -p "$SESSION_DIR"

# 1. Full database backup
wp db export "$SESSION_DIR/production_db_backup.sql"
gzip "$SESSION_DIR/production_db_backup.sql"

# 2. Backup modified files/content
# (depends on what's being deployed)

# 3. Document
cat > "$SESSION_DIR/BACKUP_INFO.md" <<EOF
# Production Deployment Backup
Date: $(date)
Database: Full backup (compressed)
Size: $(du -h "$SESSION_DIR/production_db_backup.sql.gz" | cut -f1)
Purpose: Pre-deployment safety backup
EOF
```

---

## Backup Verification

After creating backup:

```bash
# Verify backup file exists and has content
if [ -f "$SESSION_DIR/db_backup_*.sql.gz" ]; then
  SIZE=$(du -h "$SESSION_DIR"/db_backup_*.sql.gz | cut -f1)
  echo "✅ Database backup created: $SIZE"
else
  echo "❌ Database backup FAILED"
fi

# Test backup can be read
gunzip -t "$SESSION_DIR"/db_backup_*.sql.gz && \
  echo "✅ Backup file integrity verified" || \
  echo "❌ Backup file corrupted"
```

---

## Rollback Procedures

### Rollback Single Page:

```bash
# Using session directory backup
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_before.html")"

# Verify rollback
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after_rollback.html"
diff "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_after_rollback.html"
```

### Rollback Database:

```bash
# ⚠️ CAUTION: This overwrites the entire database

# 1. Create current state backup first
wp db export "$SESSION_DIR/before_rollback_$(date +%Y%m%d_%H%M%S).sql"

# 2. Decompress backup
gunzip db_backup_20251108_120000.sql.gz

# 3. Import backup
wp db import db_backup_20251108_120000.sql

# 4. Flush caches
wp cache flush
wp rewrite flush

# 5. Verify site works
curl -I http://site-url/ | head -1
```

---

## Backup Retention

**Session Directory Backups:**
- Retained with session files (30 days + 90 days archived)
- Cleaned automatically via work files cleanup cron

**Manual Backups:**
- Keep production backups for 90 days
- Keep pre-deployment backups indefinitely (or until next deployment)

---

## Emergency Backup

If something goes wrong and you need quick backup:

```bash
# Quick database backup
wp db export "/home/dave/skippy/emergency_backup_$(date +%Y%m%d_%H%M%S).sql"

# Quick content backup (specific pages)
for ID in 105 699 716; do
  wp post get $ID --field=post_content > "/home/dave/skippy/emergency_page_${ID}_$(date +%Y%m%d_%H%M%S).html"
done
```

---

## Backup Checklist

Before major WordPress changes:
- [ ] Created session directory
- [ ] Backed up all pages/posts being modified
- [ ] Created database backup (if bulk changes)
- [ ] Compressed database backup
- [ ] Verified backup file integrity
- [ ] Documented what's backed up
- [ ] Tested backup can be read

---

## Best Practices

### DO:
✅ Always backup before risky operations
✅ Compress database backups (save space)
✅ Verify backups after creation
✅ Document what's backed up
✅ Test restore procedures periodically
✅ Keep production backups separate

### DON'T:
❌ Skip backups for "quick" production changes
❌ Delete backups immediately after updates
❌ Assume backups worked without verification
❌ Store backups only in session directories (for critical data)
❌ Forget to document backup location

---

## Related Protocols

- [WordPress Content Update Protocol](wordpress_content_update_protocol.md)
- [Emergency Rollback Protocol](emergency_rollback_protocol.md)
- [Multi-Site WordPress Protocol](multi_site_wordpress_protocol.md)
- [Safety and Backup Protocol](safety_backup_protocol.md)

---

## Quick Reference

```bash
# Content backup (individual pages)
wp post get {ID} --field=post_content > "$SESSION_DIR/backup_page_{ID}.html"

# Database backup
wp db export "$SESSION_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
gzip "$SESSION_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"

# Files backup
tar -czf "$SESSION_DIR/files_backup.tar.gz" wp-content/uploads/

# Verify backup
gunzip -t backup.sql.gz && echo "✅ Valid" || echo "❌ Corrupted"

# Rollback page
wp post update {ID} --post_content="$(cat backup_page.html")"

# Rollback database (CAUTION)
wp db import backup.sql
```

---

**Generated:** 2025-11-08
**Status:** Active
**Next Review:** 2025-12-08
