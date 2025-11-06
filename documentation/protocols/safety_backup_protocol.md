# Safety and Backup Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

Prevent data loss and enable recovery. This protocol defines automatic safety measures Claude follows.

## Purpose

- Prevent accidental data loss
- Enable undo/rollback
- Create audit trail
- Build confidence in operations

---

## Automatic Safety Measures

### 1. Work Files (Never /tmp/)
```
Always use: /home/dave/skippy/work/{project}/
Never use: /tmp/ (lost on reboot)

Benefits:
- Persistent across reboots
- 30-day retention
- Searchable history
- Recovery possible
```

### 2. Before/After Files
```
For every file edit:
- Save {file}_before.{ext}
- Create iterations {file}_v1.{ext}
- Save {file}_final.{ext}
- Verify {file}_after.{ext}

Enables: Rollback, comparison, audit
```

### 3. Dry-Run First
```
For risky operations:
- Run with --dry-run flag first
- Show what would happen
- Ask for confirmation
- Then execute for real
```

### 4. Verification After Changes
```
After critical operations:
- Verify files exist
- Check for errors
- Compare expected vs actual
- Run health checks
```

---

## Before Dangerous Operations

### Database Changes
```
Before:
- Create database backup
- Document current state
- Test on staging if possible

After:
- Verify changes applied
- Test functionality
- Keep backup for 30 days
```

### Bulk File Operations
```
Before:
- Run with --dry-run
- Show affected files count
- Ask confirmation if > 100 files

During:
- Create backup if deleting
- Track operations in database (utilities)

After:
- Verify count matches expected
- Check for errors in log
```

### Production Deployments
```
Before:
- Run pre-deployment validator
- Create database backup
- Document current state

During:
- Use deployment scripts
- Track each step

After:
- Run post-deployment verification
- Run health checks
- Test critical features
```

### Git Force Operations
```
Will ask permission for:
- git push --force
- git reset --hard
- git clean -fd

Never without explicit user approval
```

---

## Built-In Safeguards

### 1. Path Validation
```python
# Prevents directory traversal attacks
validate_path('/some/path', must_exist=True)
safe_path_join(base_dir, 'subdir', 'file')
```

### 2. Permission Checks
```bash
# Before file operations
if [[ ! -w "$directory" ]]; then
    echo "Error: No write permission"
    exit 1
fi
```

### 3. Backup Creation
```bash
# Before destructive operations
if [[ -f "$file" ]]; then
    cp "$file" "$file.backup.$(date +%Y%m%d_%H%M%S)"
fi
```

### 4. Confirmation for Bulk Operations
```bash
# If affecting > 100 files
echo "This will affect $count files"
read -p "Continue? (yes/no): " confirm
```

---

## Recovery Options

### Undo File Edits
```bash
# Find the before file
ls ~/skippy/work/wordpress/rundaverun/20251106_*/post_*_before.html

# Restore it
wp post update 145 --post_content="$(cat post_145_before.html)"
```

### Undo File Organization (with utilities)
```python
from utilities.common.database import OperationDatabase

db = OperationDatabase()
db.undo_last_operation()  # Restores files!
```

### Undo Git Commits
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - Claude will ask first
git reset --hard HEAD~1
```

### Restore from Work Files
```bash
# All work sessions are saved
ls -lt ~/skippy/work/project/

# Find the session
cd ~/skippy/work/project/20251106_141523_description/

# Review what changed
cat README.md
diff file_before.ext file_after.ext

# Restore if needed
cp file_before.ext /original/location/
```

---

## Examples

### Example 1: Database Update

**Operation:** Update WordPress database

**Safety Measures:**
```bash
# 1. Backup first
wp db export backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Make changes
wp db query "UPDATE..."

# 3. Verify changes
wp db query "SELECT..."

# 4. Test website
wp health check

# Result: Backup available for 30 days if rollback needed
```

### Example 2: Bulk File Delete

**Operation:** Delete old log files

**Safety Measures:**
```bash
# 1. Dry-run first
find /var/log -name "*.log" -mtime +90 -print
→ Shows 47 files

# 2. Ask confirmation
"This will delete 47 files older than 90 days. Proceed?"

# 3. Move to backup first (not permanent delete)
mkdir -p ~/skippy/work/maintenance/log_cleanup_20251106/
find /var/log -name "*.log" -mtime +90 -exec mv {} ~/skippy/work/maintenance/log_cleanup_20251106/ \;

# 4. Verify
ls ~/skippy/work/maintenance/log_cleanup_20251106/ | wc -l
→ 47 files (matches expected)

# Result: Files recoverable for 30 days from work directory
```

### Example 3: WordPress Content Update

**Operation:** Update policy page

**Safety Measures:**
```bash
# 1. Create work directory
SESSION_DIR="~/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_policy_update"
mkdir -p "$SESSION_DIR"

# 2. Save current content
wp post get 703 --field=post_content > "$SESSION_DIR/post_703_before.html"

# 3. Create new version
cat "$SESSION_DIR/post_703_before.html" | sed 's/old/new/g' > "$SESSION_DIR/post_703_v1.html"

# 4. Preview changes
diff "$SESSION_DIR/post_703_before.html" "$SESSION_DIR/post_703_v1.html"

# 5. Apply if approved
wp post update 703 --post_content="$(cat "$SESSION_DIR/post_703_v1.html")"

# 6. Verify
wp post get 703 --field=post_content > "$SESSION_DIR/post_703_after.html"
diff "$SESSION_DIR/post_703_v1.html" "$SESSION_DIR/post_703_after.html"
→ No diff = successful

# Result: Complete audit trail in work directory
```

---

## Trust the System

### You Can Trust:
✅ Work files are preserved (not in /tmp/)
✅ Before/After versions are saved
✅ Dangerous operations ask for confirmation
✅ Dry-run available for risky operations
✅ Recovery is possible for 30 days

### You Don't Need To:
❌ Manually create backups (Claude does it)
❌ Worry about /tmp/ usage (Claude uses work/)
❌ Ask for dry-run (Claude does it for risky ops)
❌ Manually verify (Claude does it automatically)

---

## Best Practices

### DO:
✅ Trust the automatic safety measures
✅ Review changes when prompted
✅ Keep work files for retention period
✅ Use undo/rollback when needed

### DON'T:
❌ Delete work directories prematurely
❌ Skip confirmation prompts for bulk operations
❌ Force operations without understanding risk
❌ Bypass safety measures

---

## Quick Reference

### Recovery Commands
```bash
# Find recent work
ls -lt ~/skippy/work/project/

# Restore file from backup
cp ~/skippy/work/.../file_before.ext /original/location/

# Undo with utilities database
python -c "from utilities.common.database import OperationDatabase; OperationDatabase().undo_last_operation()"

# Undo git commit (keep changes)
git reset --soft HEAD~1

# Restore database
wp db import backup_file.sql
```

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
