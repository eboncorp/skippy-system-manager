# Database Operations Protocol

**Version:** 1.0.0
**Last Updated:** 2026-01-17

---

## Overview

Standard procedures for WordPress database operations including backups, restores, and migrations.

---

## Safety Rules

### Before ANY Database Operation:

1. **Create backup** - No exceptions
2. **Verify backup** - Confirm it's valid
3. **Document action** - Log what you're doing
4. **Test on local first** - If possible

### Read-Only Operations (Safe)

```bash
# List tables
wp db tables --allow-root

# Check database
wp db check --allow-root

# Query (SELECT only)
wp db query "SELECT ID, post_title FROM wp_posts WHERE post_type='page' LIMIT 10" --allow-root
```

---

## Backup Procedures

### Quick Backup

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_db"
mkdir -p "$SESSION_DIR"

wp db export "$SESSION_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql" --allow-root
```

### Compressed Backup (Recommended)

```bash
wp db export - --allow-root | gzip > "$SESSION_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
```

### Verify Backup

```bash
# Check file exists and has content
ls -lh "$SESSION_DIR"/db_backup_*.sql.gz

# Verify compression integrity
gunzip -t "$SESSION_DIR"/db_backup_*.sql.gz && echo "✅ Backup valid"

# Preview contents (optional)
gunzip -c "$SESSION_DIR"/db_backup_*.sql.gz | head -50
```

---

## Restore Procedures

### CRITICAL: Always backup current state first

```bash
# Backup current before restore
wp db export "$SESSION_DIR/db_pre_restore_$(date +%Y%m%d_%H%M%S).sql" --allow-root
```

### Restore from SQL

```bash
# Uncompressed
wp db import backup.sql --allow-root

# Compressed
gunzip -c backup.sql.gz | wp db import - --allow-root
```

### Post-Restore Steps

```bash
# Always run after restore
wp cache flush --allow-root
wp transient delete --all --allow-root
wp rewrite flush --allow-root

# Verify
wp post list --post_type=page --allow-root
wp db check --allow-root
```

---

## Search and Replace

### Dry Run First (ALWAYS)

```bash
wp search-replace 'old-string' 'new-string' --dry-run --allow-root
```

### Execute

```bash
wp search-replace 'old-string' 'new-string' --allow-root
```

### Common Use Cases

```bash
# URL migration
wp search-replace 'http://old-domain.com' 'https://new-domain.com' --dry-run --allow-root

# Fix broken links
wp search-replace '/old-path/' '/new-path/' --dry-run --allow-root

# Update email addresses
wp search-replace 'old@email.com' 'new@email.com' --dry-run --allow-root
```

---

## Table Operations

### List Tables

```bash
wp db tables --allow-root
```

### Optimize Tables

```bash
wp db optimize --allow-root
```

### Repair Tables

```bash
wp db repair --allow-root
```

### Check Table Size

```bash
wp db query "SELECT table_name, ROUND(data_length/1024/1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = DATABASE()
ORDER BY data_length DESC;" --allow-root
```

---

## Common Queries

### Find Posts by Content

```bash
wp db query "SELECT ID, post_title FROM wp_posts
WHERE post_content LIKE '%search-term%'
AND post_status = 'publish';" --allow-root
```

### List Recent Changes

```bash
wp db query "SELECT ID, post_title, post_modified
FROM wp_posts
WHERE post_type = 'page'
ORDER BY post_modified DESC
LIMIT 10;" --allow-root
```

### Check Post Meta

```bash
wp db query "SELECT meta_key, meta_value
FROM wp_postmeta
WHERE post_id = {ID};" --allow-root
```

---

## Production Database Access

### Via SSH

```bash
SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun \
  git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com \
  'cd html && wp db export /tmp/prod_backup.sql --allow-root'

# Copy to local
SSH_AUTH_SOCK="" scp ... :/tmp/prod_backup.sql ./
```

### Via MCP Tool

```bash
mcp__general-server__wp_db_export()
```

---

## Emergency Procedures

### Database Connection Failed

```bash
# Check MySQL status
sudo systemctl status mysql

# Restart if needed
sudo systemctl restart mysql

# Test connection
wp db check --allow-root
```

### Corrupted Database

```bash
# Repair
wp db repair --allow-root

# If repair fails, restore from backup
wp db import /path/to/last_good_backup.sql --allow-root
```

---

## Retention Policy

| Backup Type | Retention |
|-------------|-----------|
| Pre-operation | 7 days |
| Daily | 7 days |
| Weekly | 4 weeks |
| Monthly | 12 months |

---

## Related

- Backup Workflow
- Emergency Recovery Workflow
- WordPress Update Protocol
