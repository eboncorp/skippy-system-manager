# Backup & Restore - Quick Reference

**Protocols:** [Backup Strategy](../../conversations/backup_strategy_protocol.md), [WordPress Backup](../protocols/wordpress_backup_protocol.md)
**Priority:** CRITICAL
**Use:** Before ANY major changes

---

## 🎯 Golden Rule

**ALWAYS backup before:**
- Database changes
- Plugin updates
- Theme changes
- Content migrations
- Configuration changes
- Major deployments

---

## 💾 Quick Backup Commands

### WordPress Database
```bash
# Simple backup
wp db export backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
wp db export backup_$(date +%Y%m%d_%H%M%S).sql.gz --compress

# Backup to specific location
wp db export ~/backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Check backup size
ls -lh backup_*.sql
```

### WordPress Files
```bash
# Backup uploads directory
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz wp-content/uploads/

# Backup themes
tar -czf themes_backup_$(date +%Y%m%d).tar.gz wp-content/themes/

# Backup plugins
tar -czf plugins_backup_$(date +%Y%m%d).tar.gz wp-content/plugins/

# Full WordPress backup (excluding wp-content)
tar -czf wordpress_core_$(date +%Y%m%d).tar.gz \
  --exclude='wp-content' \
  --exclude='wp-config.php' \
  .
```

### Configuration Files
```bash
# Backup wp-config.php
cp wp-config.php wp-config.php.backup

# Backup .htaccess
cp .htaccess .htaccess.backup

# Backup entire configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  wp-config.php \
  .htaccess \
  .user.ini
```

---

## 🔄 Quick Restore Commands

### Database Restore
```bash
# Simple restore
wp db import backup_YYYYMMDD_HHMMSS.sql

# Restore with verification
wp db check  # Check before restore
wp db import backup_YYYYMMDD_HHMMSS.sql
wp db check  # Check after restore

# Restore compressed backup
gunzip -c backup_YYYYMMDD_HHMMSS.sql.gz | wp db import -

# Search and replace URLs (if needed)
wp search-replace 'oldurl.com' 'newurl.com'
```

### File Restore
```bash
# Restore uploads
tar -xzf uploads_backup_YYYYMMDD.tar.gz

# Restore specific file
tar -xzf backup.tar.gz path/to/specific/file

# Restore from session directory
cp ~/skippy/work/wordpress/rundaverun/[session]/page_105_before.html .
```

### Configuration Restore
```bash
# Restore wp-config.php
cp wp-config.php.backup wp-config.php

# Restore .htaccess
cp .htaccess.backup .htaccess

# Verify after restore
wp config list
cat .htaccess
```

---

## 📋 Pre-Change Backup Checklist

Before making changes:

- [ ] Create database backup
  ```bash
  wp db export ~/backups/pre_change_$(date +%Y%m%d_%H%M%S).sql
  ```

- [ ] Note current plugin versions
  ```bash
  wp plugin list > ~/backups/plugins_list_$(date +%Y%m%d).txt
  ```

- [ ] Note current theme
  ```bash
  wp theme list --status=active > ~/backups/active_theme_$(date +%Y%m%d).txt
  ```

- [ ] Document current state
  ```bash
  wp site info > ~/backups/site_info_$(date +%Y%m%d).txt
  ```

- [ ] Create session directory (for content changes)
  ```bash
  SESSION="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_change"
  mkdir -p "$SESSION"
  ```

---

## 🔍 Verify Backup Integrity

### After Creating Backup

```bash
# Check file exists and has size
ls -lh backup_*.sql
# Should show file with reasonable size (not 0 bytes)

# Quick content check
head -20 backup_*.sql
# Should show SQL statements

# Verify compressed backups
gunzip -t backup_*.sql.gz
# Should return nothing if valid

# Test restore (on test site if possible)
wp db import backup_*.sql --dry-run
```

---

## 📍 Backup Locations

### Default Locations
```
~/backups/                    ← Main backup directory
  ├── database/               ← Database backups
  ├── files/                  ← File backups
  └── config/                 ← Configuration backups

~/skippy/work/wordpress/[site]/[session]/
  ├── page_*_before.html      ← Content backups
  └── *_before.sql            ← Session-specific DB backups
```

### Check Backup Space
```bash
# Check backup directory size
du -sh ~/backups/

# Check available space
df -h ~/backups/

# List recent backups
ls -lht ~/backups/ | head -20
```

---

## 🕐 Backup Retention

### Recommended Retention
- **Daily backups:** Keep 7 days
- **Weekly backups:** Keep 4 weeks
- **Monthly backups:** Keep 12 months
- **Pre-change backups:** Keep 30 days

### Cleanup Old Backups
```bash
# Delete backups older than 30 days
find ~/backups/ -name "*.sql" -mtime +30 -delete
find ~/backups/ -name "*.tar.gz" -mtime +30 -delete

# Keep only last 10 backups
cd ~/backups
ls -t *.sql | tail -n +11 | xargs rm -f
```

---

## 🚨 Emergency Restore

### Site Completely Broken

**Step 1: Assess**
```bash
# Can you access SSH? ✓
# Can you reach database?
wp db check

# Can you access files?
ls -la
```

**Step 2: Find Latest Good Backup**
```bash
ls -lht ~/backups/*.sql | head -5
```

**Step 3: Restore Database**
```bash
# Create safety backup first!
wp db export safety_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
wp db import ~/backups/backup_[LATEST].sql

# Verify
wp db check
curl -I https://yoursite.com
```

**Step 4: Restore Files (if needed)**
```bash
# Restore from file backup
tar -xzf ~/backups/files_backup_[LATEST].tar.gz

# Or restore specific files from session
cp ~/skippy/work/wordpress/[site]/[session]/page_*_before.html .
```

**Step 5: Verify Site Works**
```bash
# Check site loads
curl https://yoursite.com

# Check admin accessible
wp admin

# Test key functionality
```

---

## 🔧 Automated Backups

### Existing Cron Jobs
```bash
# Check current backup jobs
crontab -l | grep backup

# Typical schedule:
0 3 * * * /home/dave/Scripts/full_home_backup.sh      # Daily 3 AM
0 2 * * * /home/dave/.nexus/backup.sh                 # Daily 2 AM
0 2 * * 0 /home/dave/Scripts/backup_google_photos.sh  # Weekly Sunday 2 AM
```

### Manual Backup Now
```bash
# Run daily backup script manually
bash /home/dave/Scripts/full_home_backup.sh

# Or create quick backup
wp db export ~/backups/manual_backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 📊 Backup Best Practices

### DO:
- ✅ Backup before every major change
- ✅ Test restores periodically
- ✅ Store backups off-site (cloud)
- ✅ Document what's in each backup
- ✅ Keep multiple backup copies
- ✅ Verify backup integrity
- ✅ Clean up old backups

### DON'T:
- ❌ Skip backups "because it's small change"
- ❌ Overwrite backups (use timestamps)
- ❌ Store only on same server
- ❌ Forget to test restores
- ❌ Keep backups forever (manage retention)
- ❌ Backup to /tmp/ (use session directories)

---

## 🎯 Backup by Change Type

### Content Update
```bash
SESSION="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_content"
mkdir -p "$SESSION"
wp post get [ID] --field=post_content > "$SESSION/page_[ID]_before.html"
# Make changes...
# Follow WordPress Content Update Protocol
```

### Plugin Update
```bash
# Backup before
wp db export ~/backups/pre_plugin_update_$(date +%Y%m%d).sql
wp plugin list > ~/backups/plugins_before.txt

# Update
wp plugin update [plugin-name]

# Verify
wp plugin list > ~/backups/plugins_after.txt
diff ~/backups/plugins_before.txt ~/backups/plugins_after.txt
```

### Theme Change
```bash
# Full backup before theme changes
wp db export ~/backups/pre_theme_change_$(date +%Y%m%d).sql
tar -czf ~/backups/themes_backup_$(date +%Y%m%d).tar.gz wp-content/themes/

# Change theme
wp theme activate [theme-name]

# Verify and test thoroughly
```

### Database Migration
```bash
# Always backup before DB migrations!
wp db export ~/backups/pre_migration_$(date +%Y%m%d_%H%M%S).sql

# Document migration
cat > ~/backups/migration_notes_$(date +%Y%m%d).txt <<EOF
Migration: [description]
Date: $(date)
Pre-backup: pre_migration_$(date +%Y%m%d_%H%M%S).sql
Expected changes: [list]
EOF

# Run migration
# ...

# Verify after
wp db check
```

---

## 🔗 Quick Backup Script

**Create this alias for quick backups:**

```bash
# Add to ~/.bashrc or ~/.zshrc
alias quick-backup='wp db export ~/backups/quick_backup_$(date +%Y%m%d_%H%M%S).sql && echo "✅ Backup created: ~/backups/quick_backup_$(date +%Y%m%d_%H%M%S).sql"'

# Usage:
# quick-backup
```

---

## 📞 Recovery Support

### If Restore Fails

1. **Check error messages carefully**
2. **Verify backup file integrity**
   ```bash
   head backup.sql  # Should show SQL
   tail backup.sql  # Should end properly
   ```
3. **Try different restore method**
   ```bash
   # Method 1: WP-CLI
   wp db import backup.sql

   # Method 2: MySQL direct
   mysql -u user -p database < backup.sql
   ```
4. **Check database connection**
   ```bash
   wp db check
   ```
5. **Verify database credentials**
   ```bash
   wp config get DB_NAME
   wp config get DB_USER
   ```

---

## 💡 Pro Tips

### 1. Name Backups Descriptively
```bash
# Good
wp db export ~/backups/pre_major_update_20251110.sql

# Better
wp db export ~/backups/pre_plugin_update_woocommerce_20251110_1430.sql
```

### 2. Keep Backup Log
```bash
cat > ~/backups/BACKUP_LOG.md <<EOF
## Backup Log

### 2025-11-10 14:30
- File: pre_plugin_update_woocommerce_20251110_1430.sql
- Reason: Updating WooCommerce 8.1 → 8.2
- Size: 125MB
- Status: ✅ Verified
EOF
```

### 3. Quick Restore Test
```bash
# Periodically test your restore process on dev/local
wp db import backup_latest.sql
wp search-replace 'production.com' 'local.test'
```

---

**Full Protocols:**
- conversations/backup_strategy_protocol.md
- documentation/protocols/wordpress_backup_protocol.md
- documentation/protocols/emergency_rollback_protocol.md
**Related:** emergency_rollback_quick_ref.md, deployment_checklist_quick_ref.md
