# Backup Workflow Examples

**Use Cases**: Creating, verifying, and managing backups across different systems

**Tools Used**: wordpress_quick_backup, wp_db_export, ebon_full_status, run_remote_command

---

## WordPress Backups

### Quick Full Backup

**When to use**: Before making any risky changes to WordPress

```
Create a complete WordPress backup
```

**What it does**:
- Exports database to SQL file
- Archives wp-content directory (uploads, themes, plugins)
- Creates timestamped backup directory
- Location: `/home/dave/RunDaveRun/backups/full_backup_YYYYMMDD_HHMMSS/`

**Result**:
```
Backup complete: /home/dave/RunDaveRun/backups/full_backup_20251101_143022/
  ├── database.sql (WordPress database)
  └── wp_content.tar.gz (All uploads, themes, plugins)
```

### Database-Only Backup

**When to use**: Before database operations (search-replace, option changes)

```
Export the WordPress database
```

**What it does**:
- Exports only the database (faster than full backup)
- Timestamped SQL file
- Location: `/home/dave/RunDaveRun/backups/wp_db_backup_YYYYMMDD_HHMMSS.sql`

**Use case**: Quick backup before testing URL changes

### Daily Backup Schedule Recommendation

**Morning backup** (before starting work):
```
Create a WordPress database backup as a safety snapshot
```

**Before risky operations**:
```
Create a complete WordPress backup before making these changes
```

**Weekly full backup**:
```
Create a complete WordPress backup for weekly archive
```

---

## Skippy Scripts Backup

### Manual Backup to Ebon

**When to use**: Before major script reorganization or testing

```bash
# Manual terminal command
rsync -avz --progress /home/dave/skippy/scripts/ ebon@10.0.0.29:~/backups/skippy_scripts/
```

**Or via MCP**:
```
Run remote command on ebon to create backup directory:
mkdir -p ~/backups/skippy_scripts_$(date +%Y%m%d)
```

Then use scp or rsync (manual)

---

## System Configuration Backups

### Backup MCP Server Configuration

**When to use**: Before updating MCP server

```
Read the Claude for Desktop config file to save current state
```

**Manual backup**:
```bash
cp ~/.config/Claude/claude_desktop_config.json \
   ~/.config/Claude/claude_desktop_config.json.backup
```

### Backup Conversation Transcripts

**When to use**: Before cleanup or reorganization

```
List all conversation transcripts to document what exists:
ls -lh /home/dave/skippy/conversations/
```

**Manual backup**:
```bash
tar -czf ~/skippy/conversations_backup_$(date +%Y%m%d).tar.gz \
        ~/skippy/conversations/
```

---

## Ebon Server Backups

### Check Ebon Disk Space Before Backup

```
Show full ebon server status including disk usage
```

**What to check**:
- Available disk space (need enough room for backup)
- Current Docker container status
- System load

### Backup Jellyfin Configuration

```
Run remote command on ebon:
tar -czf ~/backups/jellyfin_config_$(date +%Y%m%d).tar.gz /path/to/jellyfin/config
```

**Important**: Replace `/path/to/jellyfin/config` with actual path

### Verify Ebon Backups Exist

```
Run remote command on ebon to list backups:
ls -lh ~/backups/
```

---

## Backup Verification

### Verify WordPress Backup Integrity

**After creating backup**:

1. **Check files exist**:
```
List files in /home/dave/RunDaveRun/backups/
```

2. **Check database backup size**:
```
Get file info for the latest database backup
```

**Typical sizes**:
- Database SQL: 5-50 MB (depends on content)
- wp-content archive: 50-500 MB (depends on uploads)

3. **Test database backup is valid SQL**:
```bash
# Manual test
head -50 /home/dave/RunDaveRun/backups/wp_db_backup_LATEST.sql
```

Should see SQL statements like:
```sql
CREATE TABLE IF NOT EXISTS...
INSERT INTO...
```

### Verify Backup Schedule

**Monthly check**:
```
List all backups and check dates:
ls -lht /home/dave/RunDaveRun/backups/ | head -20
```

**Should see**:
- Recent backups (within last week)
- Multiple backup dates (not just one old backup)
- Reasonable file sizes (not 0 bytes)

---

## Backup Restoration

### Restore WordPress Database

**When to use**: After failed update or corrupted data

**Steps**:

1. **Verify backup exists**:
```
List backup files to find the one to restore
```

2. **Create safety backup of current state**:
```
Export current database before restoring old backup
```

3. **Restore** (manual terminal command):
```bash
wp --path=/home/dave/RunDaveRun --allow-root db import \
   /home/dave/RunDaveRun/backups/wp_db_backup_YYYYMMDD_HHMMSS.sql
```

4. **Verify restoration**:
```
List posts to verify data is from the restored backup
```

### Restore wp-content Files

**When to use**: Lost files or corrupted uploads

```bash
# Manual terminal commands
cd /home/dave/RunDaveRun/
tar -xzf backups/full_backup_YYYYMMDD_HHMMSS/wp_content.tar.gz
```

---

## Automated Backup Ideas

### Cron Job for Daily Database Backup

**Future enhancement** - could add to MCP server:

```bash
# Add to crontab
0 2 * * * /usr/local/bin/wp --path=/home/dave/RunDaveRun --allow-root db export \
          /home/dave/RunDaveRun/backups/auto_db_backup_$(date +\%Y\%m\%d).sql
```

### Backup Rotation (Keep Last 30 Days)

**Future enhancement**:

```bash
# Delete backups older than 30 days
find /home/dave/RunDaveRun/backups/ -name "*.sql" -mtime +30 -delete
find /home/dave/RunDaveRun/backups/ -name "full_backup_*" -mtime +30 -exec rm -rf {} \;
```

---

## Backup Checklist

### Before Risky Operations

- [ ] WordPress full backup created
- [ ] Backup completed successfully (no errors)
- [ ] Verified backup files exist
- [ ] Checked backup file sizes are reasonable
- [ ] Know how to restore if needed

### Weekly Backup Routine

- [ ] Create full WordPress backup
- [ ] Verify ebon server has space
- [ ] Check conversation transcripts are saved
- [ ] Review old backups (delete if over 30 days old)
- [ ] Test one restoration (quarterly)

### Monthly Backup Audit

- [ ] List all backups and check dates
- [ ] Verify backup sizes are growing reasonably
- [ ] Test database backup integrity
- [ ] Clean up old backups (6+ months)
- [ ] Document backup locations

---

## Natural Language Examples

**Before WordPress update**:
```
"Create a complete WordPress backup before I update plugins"
```

**Quick safety backup**:
```
"Export the WordPress database as a quick backup"
```

**Check backup history**:
```
"Show me all WordPress backups from the last month"
```

**Verify backup**:
```
"Get file info for the latest WordPress backup to verify it completed"
```

**Before dangerous operation**:
```
"Create complete backups of both WordPress and the database before I proceed"
```

---

## Recovery Scenarios

### Scenario 1: Bad WordPress Update

**Problem**: Plugin update broke site

**Recovery**:
1. Verify you have backup from before update
2. Restore database from backup
3. Restore wp-content from backup
4. Test site works
5. Update plugin again (after checking compatibility)

### Scenario 2: Accidental Content Deletion

**Problem**: Deleted posts by mistake

**Recovery**:
1. Find latest backup
2. Restore database
3. Verify deleted content is restored
4. Export the recovered posts for safety

### Scenario 3: Corrupted Database

**Problem**: Database won't load

**Recovery**:
1. Try WordPress database repair (wp db repair)
2. If that fails, restore from latest backup
3. Verify data integrity
4. Create new backup of restored state

---

**Related Tools**:
- `wordpress_quick_backup` - Full WordPress backup
- `wp_db_export` - Database export
- `list_directory` - Check backup files exist
- `get_file_info` - Verify backup file size
- `run_remote_command` - Backup to ebon server
- `ebon_full_status` - Check ebon disk space

**Related Protocols**:
- WordPress Maintenance Protocol
- Script Creation Protocol (for backup scripts)
