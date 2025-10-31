# Backup Strategy Protocol

**Date Created**: 2025-10-28
**Purpose**: Standardized backup procedures before major operations
**Authority**: User authorization via `/home/dave/scripts/system/authorize_claude`

## Overview

This protocol defines when and how to create backups before performing potentially risky operations. The reorganization of 300+ files and 60+ directories showed the value of comprehensive backups.

## When to Backup

### Always Backup Before

**Critical Operations** (Require authorization):
- ✅ Mass file/directory renaming (10+ items)
- ✅ Directory structure reorganization
- ✅ Database modifications
- ✅ WordPress core/plugin updates
- ✅ Production deployments
- ✅ Git operations affecting main branch
- ✅ Configuration file changes
- ✅ Permission changes affecting multiple files
- ✅ Automated bulk operations

**High-Risk Operations** (Backup recommended):
- Deleting files (even one important file)
- Moving files between directories
- Search and replace operations
- Script execution affecting multiple files
- System configuration changes

**Medium-Risk Operations** (Consider backup):
- Creating new features
- Updating content
- Installing new packages
- Changing WordPress theme

### Don't Need Backup

- Reading files
- Viewing configurations
- Running diagnostic commands
- Creating new files (not replacing)
- Git status/log/diff commands

## Backup Locations

### Standard Backup Directory
**Location**: `/home/dave/reorganization_backup/` (or project-specific backup dir)

### Project-Specific Backups

```
/home/dave/
├── reorganization_backup/          - System-wide reorganizations
├── rundaverun/backups/             - Campaign project backups
├── skippy/backups/                 - Skippy project backups
└── [project]/backups/              - Project-specific backups
```

### Backup Naming Convention

**Format**: `backup_YYYY-MM-DD_HHMM_description/`

**Examples**:
- `backup_2025-10-28_1430_before_file_rename/`
- `backup_2025-10-28_1500_pre_wordpress_update/`
- `backup_2025-10-28_1600_before_deployment/`

## Backup Types

### 1. Directory Structure Backup

**When**: Before mass renames, moves, or reorganization

**What to Backup**:
```bash
# Create directory map
find /target/directory -type d | sort > backup_dir/directory_structure_before.txt

# Create file list with details
find /target/directory -type f -ls > backup_dir/file_list_before.txt

# List symlinks
find /target/directory -type l > backup_dir/symlinks_before.txt
```

**Example** (from recent reorganization):
```bash
mkdir -p /home/dave/reorganization_backup

# Directory structure
find /home/dave -maxdepth 3 -type d 2>/dev/null | sort > /home/dave/reorganization_backup/directory_structure_before.txt

# Symlinks
find /home/dave -maxdepth 1 -type l > /home/dave/reorganization_backup/symlinks_before.txt

# File count
find /home/dave -maxdepth 3 -type f 2>/dev/null | wc -l > /home/dave/reorganization_backup/file_count_before.txt
```

### 2. Configuration Backup

**When**: Before changing configs

**What to Backup**:
```bash
# Copy config files
cp /path/to/config.conf backup_dir/config.conf.backup

# Or entire config directory
cp -r /path/to/config/ backup_dir/config_backup/
```

**Example**:
```bash
# WordPress config
cp "/home/dave/Local Sites/rundaverun-local/app/public/wp-config.php" \
   "/home/dave/rundaverun/backups/wp-config_$(date +%Y%m%d_%H%M%S).php"

# Claude config
cp /home/dave/.claude/CLAUDE.md \
   /home/dave/reorganization_backup/CLAUDE.md.backup
```

### 3. Database Backup

**When**: Before WordPress updates, content changes, or deployments

**WordPress Database**:
```bash
# Using WP-CLI
cd "/home/dave/Local Sites/rundaverun-local/app/public"
wp db export /home/dave/rundaverun/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql --allow-root

# Verify backup created
ls -lh /home/dave/rundaverun/backups/db_backup_*.sql | tail -1
```

**MySQL Database (if direct access)**:
```bash
mysqldump -u username -p database_name > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 4. File Content Backup

**When**: Before bulk file modifications

**Full Copy**:
```bash
# Copy entire directory
cp -r /source/directory /backup/directory_$(date +%Y%m%d_%H%M%S)

# Or use rsync for better control
rsync -av --progress /source/directory/ /backup/directory_$(date +%Y%m%d_%H%M%S)/
```

**Compressed Backup**:
```bash
# Create tar.gz archive
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz /path/to/directory

# Verify archive
tar -tzf backup_$(date +%Y%m%d_%H%M%S).tar.gz | head -20
```

**Example**:
```bash
# Backup campaign directory before changes
tar -czf /home/dave/rundaverun/backups/campaign_$(date +%Y%m%d_%H%M%S).tar.gz \
         /home/dave/rundaverun/campaign/
```

### 5. Git Snapshot

**When**: Before experimental changes

**Create Checkpoint**:
```bash
# Commit current state
git add .
git commit -m "[Checkpoint] Before major changes - $(date +%Y-%m-%d)"

# Tag for easy reference
git tag -a checkpoint_$(date +%Y%m%d_%H%M%S) -m "Checkpoint before [operation]"

# Create backup branch
git branch backup_$(date +%Y%m%d_%H%M%S)
```

**Rollback if Needed**:
```bash
# Return to checkpoint
git checkout checkpoint_tag

# Or restore from backup branch
git checkout backup_branch_name
```

## Backup Procedures by Operation Type

### Mass File Rename (300+ files)

```bash
#!/bin/bash
# Create comprehensive backup

BACKUP_DIR="/home/dave/reorganization_backup"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Creating backup before mass rename..."

# 1. Directory structure
find /home/dave -maxdepth 3 -type d 2>/dev/null | sort > "$BACKUP_DIR/directory_structure_before.txt"

# 2. File list
find /home/dave -maxdepth 3 -type f 2>/dev/null | sort > "$BACKUP_DIR/file_list_before.txt"

# 3. Symlinks
find /home/dave -maxdepth 1 -type l > "$BACKUP_DIR/symlinks_before.txt"

# 4. Document the operation
cat > "$BACKUP_DIR/operation_log_$DATE.txt" << EOF
Operation: Mass file rename
Date: $(date)
Target: /home/dave/
Scope: All files and directories
Backup created: $BACKUP_DIR
EOF

echo "✅ Backup complete: $BACKUP_DIR"
```

### WordPress Update

```bash
#!/bin/bash
# WordPress backup before update

SITE_PATH="/home/dave/Local Sites/rundaverun-local/app/public"
BACKUP_DIR="/home/dave/rundaverun/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Creating WordPress backup..."

# 1. Database
cd "$SITE_PATH"
wp db export "$BACKUP_DIR/db_pre_update_$DATE.sql" --allow-root

# 2. wp-content
tar -czf "$BACKUP_DIR/wp_content_pre_update_$DATE.tar.gz" "$SITE_PATH/wp-content"

# 3. Config
cp "$SITE_PATH/wp-config.php" "$BACKUP_DIR/wp-config_pre_update_$DATE.php"

# 4. Core version
wp core version --allow-root > "$BACKUP_DIR/wp_version_before_$DATE.txt"

# 5. Plugin list
wp plugin list --allow-root > "$BACKUP_DIR/plugins_before_$DATE.txt"

echo "✅ WordPress backup complete: $BACKUP_DIR"
```

### Production Deployment

```bash
#!/bin/bash
# Backup before deployment

BACKUP_DIR="/home/dave/rundaverun/backups/deployment_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating pre-deployment backup..."

# 1. Git state
git log -1 > "$BACKUP_DIR/git_log_before.txt"
git status > "$BACKUP_DIR/git_status_before.txt"
git diff > "$BACKUP_DIR/git_diff_before.txt"

# 2. Database (local)
cd "/home/dave/Local Sites/rundaverun-local/app/public"
wp db export "$BACKUP_DIR/local_db_before.sql" --allow-root

# 3. Files being deployed
git diff --name-only > "$BACKUP_DIR/files_being_deployed.txt"

# 4. Deployment checklist
cat > "$BACKUP_DIR/deployment_checklist.txt" << EOF
Pre-Deployment Checklist:
[ ] Local site tested
[ ] Database backed up
[ ] Git committed
[ ] Production database backed up (manual)
[ ] Deployment time: $(date)
EOF

echo "✅ Pre-deployment backup complete: $BACKUP_DIR"
```

## Backup Verification

### Always Verify Backups

After creating backup:
```bash
# 1. Check backup exists
ls -lh /path/to/backup

# 2. Check backup size (should not be 0)
du -sh /path/to/backup

# 3. For archives, test extraction
tar -tzf backup.tar.gz | head -10

# 4. For database, test import syntax
wp db import backup.sql --dry-run --allow-root
```

### Backup Integrity Checklist

- [ ] Backup directory/file exists
- [ ] Backup has non-zero size
- [ ] Backup timestamp is current
- [ ] Archive can be listed/extracted
- [ ] Database backup has valid SQL
- [ ] Critical files included
- [ ] Permissions preserved (if relevant)

## Authorization Protocol

### When Authorization Required

Operations requiring `/home/dave/scripts/system/authorize_claude`:
1. Mass file/directory operations (10+ items)
2. Production deployments
3. Database modifications
4. System configuration changes
5. Any operation that could cause data loss

### Authorization Command

```bash
# Run authorization script
bash /home/dave/scripts/system/authorize_claude

# Or use slash command (after Claude restart)
/authorize_claude
```

### Authorization Window

- **Duration**: 4 hours
- **Scope**: Sensitive operations
- **Verification**: Script confirms grant window

### Working Within Authorization

1. ✅ Create backups first
2. ✅ Document what you're doing
3. ✅ Verify each critical step
4. ✅ Test when possible
5. ✅ Report completion to user

## Restoration Procedures

### Restore from Backup

**Directory Structure**:
```bash
# Review what's in backup
cat /path/to/backup/directory_structure_before.txt

# Manual restoration (if needed)
# Review differences and manually recreate structure
```

**Configuration Files**:
```bash
# Restore config
cp /backup/path/config.conf.backup /original/path/config.conf

# Verify restoration
diff /backup/path/config.conf.backup /original/path/config.conf
```

**Database**:
```bash
# WordPress database restore
cd "/home/dave/Local Sites/rundaverun-local/app/public"
wp db reset --yes --allow-root
wp db import /path/to/backup/database.sql --allow-root

# Verify
wp db check --allow-root
```

**Files**:
```bash
# From archive
tar -xzf backup.tar.gz -C /restore/location

# From directory copy
cp -r /backup/directory/* /original/location/

# Using rsync
rsync -av --progress /backup/directory/ /original/location/
```

**Git**:
```bash
# Restore from checkpoint
git checkout checkpoint_tag

# Or hard reset (CAREFUL!)
git reset --hard backup_branch_name
```

## Backup Retention

### Keep Backups

**Critical Operation Backups**: Permanent
- Directory reorganizations
- Major version updates
- Production deployments (at least 30 days)

**Regular Backups**: 30 days
- Content updates
- Configuration changes
- Feature additions

**Automated Backups**: 7 days rolling
- Daily backups
- Hourly snapshots (if configured)

### Cleanup Old Backups

```bash
# Find backups older than 30 days
find /backup/directory -name "backup_*" -mtime +30

# Review before deleting
find /backup/directory -name "backup_*" -mtime +30 -ls

# Delete after review
find /backup/directory -name "backup_*" -mtime +30 -delete
```

### Critical Backup Archive

Keep permanent archives:
```bash
/home/dave/archives/critical_backups/
├── 2025-10-28_directory_reorganization/
├── 2025-11-XX_wordpress_major_update/
└── [other critical milestones]
```

## Automation

### Backup Script Template

```bash
#!/bin/bash
# Generic backup script template
# Version: 1.0.0
# Save to: /home/dave/skippy/scripts/backup/

OPERATION_NAME="description"
SOURCE_DIR="/path/to/source"
BACKUP_BASE="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE/backup_${DATE}_${OPERATION_NAME}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "========================================="
echo "Creating backup before: $OPERATION_NAME"
echo "Date: $(date)"
echo "Source: $SOURCE_DIR"
echo "Backup: $BACKUP_DIR"
echo "========================================="

# 1. Directory structure
find "$SOURCE_DIR" -type d | sort > "$BACKUP_DIR/directories.txt"

# 2. File list
find "$SOURCE_DIR" -type f -ls > "$BACKUP_DIR/files.txt"

# 3. Copy files (if needed)
# cp -r "$SOURCE_DIR" "$BACKUP_DIR/data/"

# 4. Create archive (if needed)
# tar -czf "$BACKUP_DIR/archive.tar.gz" "$SOURCE_DIR"

# 5. Create operation log
cat > "$BACKUP_DIR/operation_log.txt" << EOF
Operation: $OPERATION_NAME
Date: $(date)
Source: $SOURCE_DIR
Backup Location: $BACKUP_DIR
Created By: $(whoami)
EOF

# Verify backup
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo ""
echo "✅ Backup complete!"
echo "Location: $BACKUP_DIR"
echo "Size: $BACKUP_SIZE"
echo ""

# Return backup path for use in scripts
echo "$BACKUP_DIR"
```

## Integration with Other Protocols

### With Script Protocol
Scripts that modify files should:
1. Include backup step in script
2. Verify backup before proceeding
3. Log backup location

### With Git Protocol
Before risky git operations:
1. Create git checkpoint
2. Consider filesystem backup too
3. Document in commit message

### With Error Protocol
If operation fails:
1. Note backup location in error log
2. Document restoration steps
3. Keep backup until verified resolved

## Best Practices

### Before Major Operations

1. ✅ Assess risk level
2. ✅ Determine backup scope
3. ✅ Run authorization if needed
4. ✅ Create appropriate backups
5. ✅ Verify backups created
6. ✅ Document backup location
7. ✅ Proceed with operation
8. ✅ Create "after" snapshot
9. ✅ Compare before/after
10. ✅ Keep backup until verified

### Backup Documentation

Always document:
- What was backed up
- When it was backed up
- Why it was backed up
- Where backup is stored
- How to restore
- Retention period

### Communication with User

Inform user:
- "Creating backup before [operation]..."
- "Backup created at [location]"
- "Backup size: [size]"
- "Operation proceeding..."
- "Operation complete"
- "Backup retained at [location] for [period]"

---

**This protocol is part of the persistent memory system.**
**Reference before any potentially risky operation.**
