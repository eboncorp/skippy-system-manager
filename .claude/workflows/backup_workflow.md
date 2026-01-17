# Backup Workflow

**Version:** 1.0.0
**Last Updated:** 2026-01-17

---

## Overview

Standard workflow for creating and verifying backups across the Skippy system.

---

## Backup Types

| Type | Frequency | Retention | Location |
|------|-----------|-----------|----------|
| WordPress Database | Before changes | 30 days | `work/wordpress/` |
| WordPress Files | Weekly | 4 weeks | `work/wordpress/` |
| Configuration Files | On change | 5 versions | `~/.claude/auto-backups/` |
| Session Work | Continuous | 30 days | `work/{category}/` |

---

## WordPress Database Backup

### Step 1: Create Session Directory
```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_backup"
mkdir -p "$SESSION_DIR"
```

### Step 2: Export Database
```bash
wp db export "$SESSION_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql" --allow-root
```

### Step 3: Compress
```bash
gzip "$SESSION_DIR"/db_backup_*.sql
```

### Step 4: Verify
```bash
gunzip -t "$SESSION_DIR"/db_backup_*.sql.gz && echo "✅ Backup valid"
```

---

## WordPress Files Backup

### Full Site Backup
```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_files_backup"
mkdir -p "$SESSION_DIR"

# Backup uploads
tar -czf "$SESSION_DIR/uploads_$(date +%Y%m%d).tar.gz" wp-content/uploads/

# Backup themes
tar -czf "$SESSION_DIR/themes_$(date +%Y%m%d).tar.gz" wp-content/themes/

# Backup plugins
tar -czf "$SESSION_DIR/plugins_$(date +%Y%m%d).tar.gz" wp-content/plugins/
```

---

## Configuration Backup

Handled automatically by `post_edit_backup.sh` hook for:
- `~/.claude/CLAUDE.md`
- `~/.claude/settings.json`
- Project CLAUDE.md files

Manual backup:
```bash
cp ~/.claude/CLAUDE.md ~/.claude/auto-backups/CLAUDE.md.$(date +%Y%m%d_%H%M%S).bak
```

---

## Verification Checklist

- [ ] Backup file exists
- [ ] File size > 0
- [ ] Compression valid (gunzip -t)
- [ ] Can list contents (tar -tzf)
- [ ] Documented in session README

---

## Restore Procedures

### Database Restore
```bash
# Backup current first
wp db export emergency_current.sql --allow-root

# Restore
gunzip -c backup.sql.gz | wp db import - --allow-root

# Flush caches
wp cache flush --allow-root
wp rewrite flush --allow-root
```

### File Restore
```bash
# Extract to temporary location first
tar -xzf backup.tar.gz -C /tmp/restore_check/

# Verify contents, then copy to destination
cp -r /tmp/restore_check/* destination/
```

---

## Automation

Weekly backups are handled by cron:
```
0 3 * * 0 /home/dave/skippy/scripts/backup/weekly_backup_v1.0.0.sh
```

---

## Related

- Emergency Rollback Workflow
- WordPress Update Workflow
