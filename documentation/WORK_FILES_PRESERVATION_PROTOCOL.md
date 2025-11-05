# Work Files Preservation Protocol

**Version:** 1.0
**Created:** November 4, 2025
**Purpose:** Preserve temporary work files with automatic 30-day cleanup
**Status:** Active Protocol

---

## Problem Statement

When Claude works on files, temporary versions are often saved to `/tmp/` which:
- Gets cleared on system reboot
- Makes it impossible to revert to previous versions
- Loses work history when troubleshooting
- No audit trail of changes made

**Solution:** Use a dedicated work directory with automatic 30-day retention policy.

---

## Standard Work Directory Structure

### Primary Work Location
```
/home/dave/skippy/work/
├── wordpress/           # WordPress site work
│   └── rundaverun/      # Project-specific subdirectory
├── scripts/             # Script development work
├── documents/           # Document processing work
└── archive/             # Files moved after 30 days
```

### Per-Session Subdirectories
Each work session should create a dated subdirectory:

```
/home/dave/skippy/work/wordpress/rundaverun/YYYYMMDD_HHMMSS_description/
```

**Example:**
```
/home/dave/skippy/work/wordpress/rundaverun/20251104_083000_volunteer_script_fixes/
├── post_941_before.html
├── post_941_v1.html
├── post_941_v2.html
├── post_941_final.html
├── post_942_before.html
├── post_942_final.html
└── session_notes.txt
```

---

## Implementation Guide

### Step 1: Create Work Directory Structure

```bash
# Create main directories
mkdir -p /home/dave/skippy/work/{wordpress,scripts,documents,archive}
mkdir -p /home/dave/skippy/work/wordpress/rundaverun

# Set proper permissions
chmod 755 /home/dave/skippy/work
```

### Step 2: Use in Claude Sessions

When Claude needs to save temporary work files:

**OLD WAY (DON'T DO THIS):**
```bash
wp post get 941 --field=post_content > /tmp/post_941.html
```

**NEW WAY (DO THIS):**
```bash
# Create session directory with timestamp and description
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_volunteer_fixes"
mkdir -p "$SESSION_DIR"

# Save work files there
wp post get 941 --field=post_content > "$SESSION_DIR/post_941_before.html"
wp post get 941 --field=post_content | sed 's/foo/bar/g' > "$SESSION_DIR/post_941_v1.html"
wp post get 941 --field=post_content | sed 's/baz/qux/g' > "$SESSION_DIR/post_941_final.html"

# Add session notes
cat > "$SESSION_DIR/session_notes.txt" <<EOF
Session: Volunteer Script Fixes
Date: $(date)
Posts Modified: 941, 942
Changes:
- Removed false "former firefighter" claim
- Changed "fire stations" to "mini police substations"
EOF
```

### Step 3: Automatic Cleanup Script

Create cleanup script at `/home/dave/skippy/scripts/cleanup_work_files.sh`:

```bash
#!/bin/bash
# Work Files Cleanup - Remove files older than 30 days
# Auto-runs daily via cron

WORK_DIR="/home/dave/skippy/work"
ARCHIVE_DIR="/home/dave/skippy/work/archive"
LOG_FILE="/home/dave/skippy/logs/work_cleanup.log"

# Ensure log directory exists
mkdir -p /home/dave/skippy/logs

# Log start
echo "[$(date)] Starting work files cleanup..." >> "$LOG_FILE"

# Find directories older than 30 days and move to archive
find "$WORK_DIR" -mindepth 2 -maxdepth 3 -type d -mtime +30 ! -path "*/archive/*" | while read -r dir; do
    # Get relative path
    rel_path="${dir#$WORK_DIR/}"

    # Create archive subdirectory structure
    archive_path="$ARCHIVE_DIR/$rel_path"
    mkdir -p "$(dirname "$archive_path")"

    # Move to archive with timestamp
    archive_name="$(basename "$dir")_archived_$(date +%Y%m%d)"
    mv "$dir" "$(dirname "$archive_path")/$archive_name"

    echo "[$(date)] Archived: $rel_path -> archive/$(dirname "$rel_path")/$archive_name" >> "$LOG_FILE"
done

# Delete archived files older than 90 days (total retention: 120 days)
find "$ARCHIVE_DIR" -type d -mtime +90 | while read -r dir; do
    rm -rf "$dir"
    echo "[$(date)] Deleted archived directory: ${dir#$ARCHIVE_DIR/}" >> "$LOG_FILE"
done

# Log completion with stats
WORK_SIZE=$(du -sh "$WORK_DIR" 2>/dev/null | cut -f1)
ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)
echo "[$(date)] Cleanup complete. Work dir: $WORK_SIZE, Archive dir: $ARCHIVE_SIZE" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
```

Make it executable:
```bash
chmod +x /home/dave/skippy/scripts/cleanup_work_files.sh
```

### Step 4: Setup Automatic Daily Cleanup

Add to crontab to run daily at 3 AM:

```bash
# Edit crontab
crontab -e

# Add this line:
0 3 * * * /home/dave/skippy/scripts/cleanup_work_files.sh
```

---

## Usage Examples

### Example 1: WordPress Post Editing

```bash
# Setup
SESSION="$(date +%Y%m%d_%H%M%S)_budget_fixes"
WORK="/home/dave/skippy/work/wordpress/rundaverun/$SESSION"
mkdir -p "$WORK"

# Save original
wp post get 699 --field=post_content > "$WORK/post_699_original.html"

# Work through versions
cat "$WORK/post_699_original.html" | sed 's/$110.5M/$81M/g' > "$WORK/post_699_v1.html"
cat "$WORK/post_699_v1.html" | sed 's/$47.5M/$77.4M/g' > "$WORK/post_699_v2.html"

# Verify before updating
diff "$WORK/post_699_original.html" "$WORK/post_699_v2.html" > "$WORK/changes.diff"

# Apply final version
wp post update 699 --post_content="$(cat "$WORK/post_699_v2.html")"

# Save final state
wp post get 699 --field=post_content > "$WORK/post_699_final.html"

# Document changes
cat > "$WORK/README.md" <<EOF
# Budget Fixes Session
Date: $(date)
Posts: 699
Changes: Updated budget figures to match fact sheet
Status: Completed successfully
EOF
```

### Example 2: Multiple Post Updates

```bash
# Setup
SESSION="$(date +%Y%m%d_%H%M%S)_volunteer_scripts"
WORK="/home/dave/skippy/work/wordpress/rundaverun/$SESSION"
mkdir -p "$WORK"

# Process multiple posts
for POST_ID in 941 942; do
    # Save before
    wp post get $POST_ID --field=post_content > "$WORK/post_${POST_ID}_before.html"

    # Apply fixes
    cat "$WORK/post_${POST_ID}_before.html" | \
        sed 's/former firefighter/public safety expert/g' | \
        sed 's/fire stations/mini police substations/g' > \
        "$WORK/post_${POST_ID}_fixed.html"

    # Update
    wp post update $POST_ID --post_content="$(cat "$WORK/post_${POST_ID}_fixed.html")"

    # Save after
    wp post get $POST_ID --field=post_content > "$WORK/post_${POST_ID}_after.html"
done

# Summary
cat > "$WORK/summary.txt" <<EOF
Session: Volunteer Script Corrections
Posts Updated: 941, 942
Files: $(ls -1 "$WORK" | wc -l) files saved
Size: $(du -sh "$WORK" | cut -f1)
EOF
```

### Example 3: Script Development

```bash
# Setup
SESSION="$(date +%Y%m%d_%H%M%S)_new_backup_script"
WORK="/home/dave/skippy/work/scripts/$SESSION"
mkdir -p "$WORK"

# Iterative development
cat > "$WORK/backup_v1.sh" <<'EOF'
#!/bin/bash
# Version 1 - Basic backup
tar -czf backup.tar.gz /data
EOF

cat > "$WORK/backup_v2.sh" <<'EOF'
#!/bin/bash
# Version 2 - Added date
DATE=$(date +%Y%m%d)
tar -czf backup_$DATE.tar.gz /data
EOF

cat > "$WORK/backup_v3_final.sh" <<'EOF'
#!/bin/bash
# Version 3 - Added rotation
DATE=$(date +%Y%m%d)
tar -czf backup_$DATE.tar.gz /data
find /backups -name "backup_*.tar.gz" -mtime +7 -delete
EOF

# Copy final version to scripts
cp "$WORK/backup_v3_final.sh" /home/dave/skippy/scripts/backup.sh
chmod +x /home/dave/skippy/scripts/backup.sh
```

---

## Retrieval and Rollback

### Find Previous Version

```bash
# List all work sessions
ls -lt /home/dave/skippy/work/wordpress/rundaverun/

# Search for specific post
find /home/dave/skippy/work -name "*post_941*" -type f

# Search by date
find /home/dave/skippy/work -name "*20251104*" -type d

# Search in archives
find /home/dave/skippy/work/archive -name "*volunteer*" -type d
```

### Rollback Changes

```bash
# Find the session directory
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/20251104_083000_volunteer_fixes"

# View original version
cat "$SESSION_DIR/post_941_before.html"

# Rollback to original
wp post update 941 --post_content="$(cat "$SESSION_DIR/post_941_before.html")"

# Or rollback to specific version
wp post update 941 --post_content="$(cat "$SESSION_DIR/post_941_v1.html")"
```

### Compare Versions

```bash
# Compare before/after
diff "$SESSION_DIR/post_941_before.html" "$SESSION_DIR/post_941_after.html"

# Compare specific versions
diff "$SESSION_DIR/post_941_v1.html" "$SESSION_DIR/post_941_v2.html"

# Show what changed
diff -u "$SESSION_DIR/post_941_before.html" "$SESSION_DIR/post_941_after.html" | less
```

---

## Best Practices

### Naming Conventions

**Session Directories:**
```
YYYYMMDD_HHMMSS_descriptive_name
```

Examples:
- `20251104_083000_volunteer_script_fixes`
- `20251104_140500_budget_standardization`
- `20251104_193000_broken_links_repair`

**File Naming:**
```
{resource}_{id}_{stage}.{ext}
```

Examples:
- `post_941_before.html`
- `post_941_v1.html`
- `post_941_v2.html`
- `post_941_final.html`
- `post_941_after.html` (actual state after update)

### Version Progression

1. **before** - Original state before any changes
2. **v1, v2, v3...** - Iterative development versions
3. **final** - Final version before applying
4. **after** - Actual state after applying (verification)

### Documentation Requirements

Each session directory should include:

1. **README.md** or **session_notes.txt**
   - What was changed
   - Why it was changed
   - Which posts/files were affected
   - Success/failure status

2. **changes.diff** (optional)
   - Diff of changes made
   - Helps with verification

3. **verification.txt** (optional)
   - Commands run to verify
   - Test results

---

## Integration with Claude

### Claude Instructions

When Claude is working on file modifications, it should:

1. **Create session directory at start:**
   ```bash
   SESSION_DIR="/home/dave/skippy/work/{project}/{subproject}/$(date +%Y%m%d_%H%M%S)_{description}"
   mkdir -p "$SESSION_DIR"
   ```

2. **Save all intermediate files:**
   - Before state
   - Each iteration
   - Final version
   - After state (verification)

3. **Document the work:**
   - Create README.md or session_notes.txt
   - Include commands run
   - Note any issues encountered

4. **Report location to user:**
   ```
   Work files saved to: /home/dave/skippy/work/wordpress/rundaverun/20251104_083000_volunteer_fixes/
   ```

### Claude Code Reference

Add to `/home/dave/.claude/CLAUDE.md`:

```markdown
## Work Files Preservation

When editing files, NEVER use /tmp/ for work files.

**ALWAYS use:** `/home/dave/skippy/work/{project}/{subproject}/YYYYMMDD_HHMMSS_description/`

**Process:**
1. Create session directory with timestamp and description
2. Save original state: `{resource}_{id}_before.{ext}`
3. Save iterations: `{resource}_{id}_v1.{ext}`, `v2`, etc.
4. Save final: `{resource}_{id}_final.{ext}`
5. Apply changes
6. Save verification: `{resource}_{id}_after.{ext}`
7. Create README.md documenting changes

**Example:**
```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_fix_name"
mkdir -p "$SESSION_DIR"
wp post get 941 --field=post_content > "$SESSION_DIR/post_941_before.html"
# ... work ...
echo "Fixed volunteer scripts" > "$SESSION_DIR/README.md"
```

Files are automatically archived after 30 days and deleted after 120 days.
```

---

## Maintenance Tasks

### Weekly Review
```bash
# Check work directory size
du -sh /home/dave/skippy/work

# Count sessions
find /home/dave/skippy/work -mindepth 3 -maxdepth 3 -type d | wc -l

# See recent sessions
ls -lt /home/dave/skippy/work/wordpress/rundaverun/ | head -10
```

### Monthly Cleanup Verification
```bash
# Check cleanup log
tail -50 /home/dave/skippy/logs/work_cleanup.log

# Verify archived files
ls -lt /home/dave/skippy/work/archive/ | head -20

# Check disk usage
df -h /home/dave/skippy/
```

### Manual Cleanup (if needed)
```bash
# Archive specific session manually
SESSION="/home/dave/skippy/work/wordpress/rundaverun/20251001_120000_old_session"
mv "$SESSION" /home/dave/skippy/work/archive/wordpress/rundaverun/

# Delete very old archives
find /home/dave/skippy/work/archive -type d -mtime +120 -exec rm -rf {} +
```

---

## Retention Policy Summary

| Location | Retention | Purpose |
|----------|-----------|---------|
| `/home/dave/skippy/work/` | 30 days | Active work files |
| `/home/dave/skippy/work/archive/` | 90 days (120 total) | Historical reference |
| `/home/dave/skippy/logs/work_cleanup.log` | Indefinite | Audit trail |

**Total Retention:** 120 days from creation

---

## Troubleshooting

### Work Directory Getting Too Large

```bash
# Find largest sessions
du -sh /home/dave/skippy/work/*/* | sort -h | tail -10

# Manually archive large old sessions
find /home/dave/skippy/work -type d -mtime +15 -size +100M
```

### Can't Find Old Files

```bash
# Search everywhere
find /home/dave/skippy/work -name "*post_941*"

# Check archives
find /home/dave/skippy/work/archive -name "*volunteer*"

# Check cleanup log
grep "post_941" /home/dave/skippy/logs/work_cleanup.log
```

### Need to Extend Retention

Edit cleanup script and change `+30` to desired days:
```bash
find "$WORK_DIR" -mindepth 2 -maxdepth 3 -type d -mtime +30
#                                                          ^^^
# Change to +45 for 45 days, +60 for 60 days, etc.
```

---

## Quick Reference

### Setup Commands
```bash
# Initial setup
mkdir -p /home/dave/skippy/work/{wordpress/rundaverun,scripts,documents,archive}
mkdir -p /home/dave/skippy/logs

# Create cleanup script (copy from protocol)
nano /home/dave/skippy/scripts/cleanup_work_files.sh
chmod +x /home/dave/skippy/scripts/cleanup_work_files.sh

# Add to cron
crontab -e
# Add: 0 3 * * * /home/dave/skippy/scripts/cleanup_work_files.sh
```

### Daily Usage
```bash
# Start session
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# Save work files
{command} > "$SESSION_DIR/filename_stage.ext"

# Document
echo "What changed" > "$SESSION_DIR/README.md"
```

### Finding Files
```bash
# Recent sessions
ls -lt /home/dave/skippy/work/wordpress/rundaverun/ | head

# Search by name
find /home/dave/skippy/work -name "*pattern*"

# Search by date
find /home/dave/skippy/work -name "*20251104*"
```

---

**Status:** Active Protocol
**Maintained By:** Dave
**Review Date:** Monthly
**Last Updated:** November 4, 2025
