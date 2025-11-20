# File & Script Naming Standards

**Version:** 1.0.0
**Enforcement:** Pre-commit hooks, code review

---

## Universal Standards

**All files and directories:**
- Lowercase letters only
- Underscores for word separation (no hyphens, no spaces)
- No capital letters anywhere
- Semantic versioning required for scripts

---

## File Naming Convention

```
{purpose}_{specific_task}_v{version}.{ext}
```

### Examples

✅ **GOOD:**
- `budget_update_v1.0.0.sh`
- `homepage_content_v2.1.0.html`
- `wordpress_backup_v1.0.0.py`
- `session_summary_20251119.md`

❌ **BAD:**
- `Budget-Update.sh` (capitals, hyphens)
- `Homepage Content.html` (capitals, spaces)
- `WordPressBackup.py` (capitals, no version)
- `Session-Summary.md` (hyphens)

---

## Semantic Versioning

**Format:** `vMAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes

**Examples:**
- `v1.0.0` - Initial release
- `v1.1.0` - Added new feature
- `v1.1.1` - Fixed bug
- `v2.0.0` - Breaking change

---

## WordPress Work Files

### Pages
```
page_{id}_{stage}.html
```
Examples:
- `page_105_before.html`
- `page_105_v1.html`
- `page_105_v2.html`
- `page_105_final.html`
- `page_105_after.html`

### Posts
```
post_{id}_{stage}.html
```
Examples:
- `post_941_before.html`
- `post_941_v1.html`
- `post_941_final.html`

### Policies
```
policy_{id}_{stage}.html
```
Examples:
- `policy_699_before.html`
- `policy_699_final.html`

---

## Scripts

### Script Naming
```
{category}_{specific_task}_v{version}.{ext}
```

Examples:
- `wordpress_backup_v1.0.0.sh`
- `fact_check_validator_v2.1.0.py`
- `session_cleanup_v1.0.0.sh`

### Script Categories
- `automation_` - Automated tasks
- `backup_` - Backup operations
- `deployment_` - Deployment tasks
- `monitoring_` - Monitoring scripts
- `security_` - Security tools
- `utility_` - General utilities
- `wordpress_` - WordPress operations

---

## Session Directories

### Format
```
/home/dave/skippy/work/{project}/{YYYYMMDD_HHMMSS}_{description}
```

### Examples
✅ **GOOD:**
- `20251119_143000_homepage_budget_fix`
- `20251119_150000_policy_batch_update`
- `20251119_160000_content_approval_workflow`

❌ **BAD:**
- `20251119_Homepage-Update` (capitals, hyphens)
- `homepage_fixes` (no timestamp)
- `20251119-14-30-00-update` (wrong timestamp format)

---

## Documentation Files

### Session Documentation
```
{session_dir}/README.md
```

Always includes:
- Session purpose
- Changes made
- Files modified
- Verification results
- Status

### Protocol Documentation
```
{protocol_name}_protocol_v{version}.md
```

Examples:
- `wordpress_update_protocol_v2.0.0.md`
- `fact_check_protocol_v1.0.0.md`
- `emergency_rollback_protocol_v1.0.0.md`

---

## Temporary/Working Files

### Format
```
{descriptive_name}_{stage}.{ext}
```

Examples:
- `converted_content_v1.html`
- `processed_data_v2.json`
- `validation_results_20251119.txt`

**CRITICAL:** NEVER use `/tmp/` - always use session directory

❌ **NEVER:**
```bash
echo "data" > /tmp/temp.txt
python3 script.py > /tmp/output.html
```

✅ **ALWAYS:**
```bash
echo "data" > "$SESSION_DIR/temp_data.txt"
python3 script.py > "$SESSION_DIR/output_converted.html"
```

---

## Stages

Standard stage suffixes:
- `_before` - Original state
- `_v1`, `_v2`, `_v3` - Iterations
- `_final` - Final version before apply
- `_after` - Verified state after apply
- `_backup` - Backup copy
- `_rolledback` - After rollback

---

## Validation

### Pre-Commit Hook

Automatically checks:
- Lowercase only
- No spaces
- Underscores for separation
- Version numbers present (for scripts)
- Proper stage suffixes

### Manual Check

```bash
# Check file naming
find . -name "*[A-Z]*" -o -name "* *" -o -name "*-*"

# Should return nothing if compliant
```

---

## Exceptions

**Only these files may use capitals:**
- `README.md` (standard)
- `LICENSE` (standard)
- `CHANGELOG.md` (standard)
- `CONTRIBUTING.md` (standard)

All other files must follow lowercase_underscore convention.

---

**Enforcement:** Automated via pre-commit hooks
**Violations:** Build fails, requires rename before commit
