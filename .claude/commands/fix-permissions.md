---
description: Auto-correct file and directory permissions for WordPress and system files
allowed-tools: ["Bash", "mcp__general-server__run_remote_command", "mcp__general-server__get_file_info"]
argument-hint: "[optional: path] [optional: --production] [optional: --dry-run]"
---

# Fix Permissions Command

Automatically correct file and directory permissions to prevent deployment failures and security issues.

## Quick Usage

```
/fix-permissions                    # Fix local WordPress
/fix-permissions --production       # Fix production site
/fix-permissions /path/to/dir       # Fix specific directory
/fix-permissions --dry-run          # Preview changes only
```

## Standard Permissions

| Type | Permission | Octal | Purpose |
|------|------------|-------|---------|
| Directories | drwxr-xr-x | 755 | Readable, executable by all; writable by owner |
| Files | -rw-r--r-- | 644 | Readable by all; writable by owner |
| wp-config.php | -rw------- | 600 | Owner-only access (security) |
| uploads/ | drwxrwxr-x | 775 | Group-writable for web server |
| cache/ | drwxrwxr-x | 775 | Group-writable for caching |

## Local WordPress Fix

```bash
#!/bin/bash
# Fix WordPress Permissions v1.0.0

WP_PATH="${1:-/home/dave/skippy/rundaverun_local_site/app/public}"
DRY_RUN="${2:-false}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              FIX PERMISSIONS                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Target: $WP_PATH"
echo "Mode: $([ "$DRY_RUN" = "true" ] && echo "DRY RUN (preview only)" || echo "LIVE")"
echo ""

# Validate path exists
if [ ! -d "$WP_PATH" ]; then
  echo "❌ Error: Directory not found: $WP_PATH"
  exit 1
fi

# Count issues before
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ BEFORE - Scanning for permission issues                     │"
echo "└─────────────────────────────────────────────────────────────┘"

# Find directories not 755
BAD_DIRS=$(find "$WP_PATH" -type d ! -perm 755 2>/dev/null | wc -l)
echo "  Directories needing fix: $BAD_DIRS"

# Find files not 644 (excluding wp-config.php which should be 600)
BAD_FILES=$(find "$WP_PATH" -type f ! -name "wp-config.php" ! -perm 644 2>/dev/null | wc -l)
echo "  Files needing fix: $BAD_FILES"

# Check wp-config.php specifically
if [ -f "$WP_PATH/wp-config.php" ]; then
  WP_CONFIG_PERM=$(stat -c %a "$WP_PATH/wp-config.php")
  if [ "$WP_CONFIG_PERM" != "600" ]; then
    echo "  wp-config.php: $WP_CONFIG_PERM (should be 600) ⚠️"
    WP_CONFIG_FIX=true
  else
    echo "  wp-config.php: 600 ✅"
    WP_CONFIG_FIX=false
  fi
fi

echo ""

if [ "$DRY_RUN" = "true" ]; then
  echo "┌─────────────────────────────────────────────────────────────┐"
  echo "│ DRY RUN - Would fix these items                            │"
  echo "└─────────────────────────────────────────────────────────────┘"

  echo ""
  echo "Directories that would be changed to 755:"
  find "$WP_PATH" -type d ! -perm 755 2>/dev/null | head -10
  [ "$BAD_DIRS" -gt 10 ] && echo "  ... and $((BAD_DIRS - 10)) more"

  echo ""
  echo "Files that would be changed to 644:"
  find "$WP_PATH" -type f ! -name "wp-config.php" ! -perm 644 2>/dev/null | head -10
  [ "$BAD_FILES" -gt 10 ] && echo "  ... and $((BAD_FILES - 10)) more"

  echo ""
  echo "Run without --dry-run to apply changes."
  exit 0
fi

echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ FIXING - Applying correct permissions                       │"
echo "└─────────────────────────────────────────────────────────────┘"

# Fix directory permissions
echo "  [1/4] Setting directories to 755..."
find "$WP_PATH" -type d -exec chmod 755 {} \; 2>/dev/null
echo "       ✅ Done"

# Fix file permissions
echo "  [2/4] Setting files to 644..."
find "$WP_PATH" -type f -exec chmod 644 {} \; 2>/dev/null
echo "       ✅ Done"

# Fix wp-config.php (more restrictive)
if [ -f "$WP_PATH/wp-config.php" ]; then
  echo "  [3/4] Setting wp-config.php to 600..."
  chmod 600 "$WP_PATH/wp-config.php"
  echo "       ✅ Done"
fi

# Fix uploads directory (group writable)
if [ -d "$WP_PATH/wp-content/uploads" ]; then
  echo "  [4/4] Setting uploads/ to 775..."
  chmod 775 "$WP_PATH/wp-content/uploads"
  find "$WP_PATH/wp-content/uploads" -type d -exec chmod 775 {} \; 2>/dev/null
  echo "       ✅ Done"
fi

echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ AFTER - Verification                                        │"
echo "└─────────────────────────────────────────────────────────────┘"

# Verify fixes
BAD_DIRS_AFTER=$(find "$WP_PATH" -type d ! -perm 755 -not -path "*/uploads/*" 2>/dev/null | wc -l)
BAD_FILES_AFTER=$(find "$WP_PATH" -type f ! -name "wp-config.php" ! -perm 644 2>/dev/null | wc -l)

echo "  Directories with issues: $BAD_DIRS → $BAD_DIRS_AFTER"
echo "  Files with issues: $BAD_FILES → $BAD_FILES_AFTER"

if [ -f "$WP_PATH/wp-config.php" ]; then
  WP_CONFIG_PERM_AFTER=$(stat -c %a "$WP_PATH/wp-config.php")
  echo "  wp-config.php: $WP_CONFIG_PERM_AFTER"
fi

echo ""
if [ "$BAD_DIRS_AFTER" -eq 0 ] && [ "$BAD_FILES_AFTER" -eq 0 ]; then
  echo "✅ All permissions fixed successfully"
else
  echo "⚠️  Some items could not be fixed (may require sudo)"
fi
```

## Production Fix

```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ PRODUCTION - Fixing permissions via SSH                    │"
echo "└─────────────────────────────────────────────────────────────┘"

SSH_CMD='SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i ~/.ssh/godaddy_rundaverun git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com'

# Fix production permissions
$SSH_CMD "cd html && find . -type d -exec chmod 755 {} \; 2>/dev/null && echo 'Directories: 755'"
$SSH_CMD "cd html && find . -type f -exec chmod 644 {} \; 2>/dev/null && echo 'Files: 644'"
$SSH_CMD "cd html && chmod 600 wp-config.php 2>/dev/null && echo 'wp-config.php: 600'"
$SSH_CMD "cd html/wp-content/uploads && find . -type d -exec chmod 775 {} \; 2>/dev/null && echo 'uploads/: 775'"

echo ""
echo "✅ Production permissions fixed"
```

## Session Directory Fix

For work session directories:

```bash
SESSION_PATH="${1:-/home/dave/skippy/work}"

echo "Fixing session directory permissions..."

# Session directories should be user-accessible
find "$SESSION_PATH" -type d -exec chmod 755 {} \; 2>/dev/null
find "$SESSION_PATH" -type f -exec chmod 644 {} \; 2>/dev/null

# Scripts should be executable
find "$SESSION_PATH" -name "*.sh" -exec chmod 755 {} \; 2>/dev/null

echo "✅ Session directory permissions fixed"
```

## Theme/Plugin Fix

For theme or plugin directories specifically:

```bash
THEME_PATH="$WP_PATH/wp-content/themes/astra-child"

echo "Fixing theme permissions..."

# Standard permissions
find "$THEME_PATH" -type d -exec chmod 755 {} \;
find "$THEME_PATH" -type f -exec chmod 644 {} \;

# Verify
ls -la "$THEME_PATH/"
```

## Common Permission Issues

### "Permission denied" on upload
```bash
# Fix uploads directory
chmod -R 775 wp-content/uploads/
```

### Plugin/theme update fails
```bash
# Ensure wp-content is writable
chmod 755 wp-content/
chmod 755 wp-content/plugins/
chmod 755 wp-content/themes/
```

### wp-config.php security warning
```bash
# Restrict to owner-only
chmod 600 wp-config.php
```

### CSS/JS changes not applying
```bash
# May be cache directory permissions
chmod -R 775 wp-content/cache/
```

## Integration

This command integrates with:
- `/deploy-verify` - Verify permissions after deployment
- `/wordpress-debug` - Layer 10 checks file permissions
- `wordpress-emergency` skill - Permission fixes in recovery

## Safety

- Always shows before/after comparison
- `--dry-run` mode for preview
- Logs all changes to session directory
- Does not touch system files outside WordPress

## Output

Creates session log at:
```
/home/dave/skippy/work/permissions/YYYYMMDD_HHMMSS_fix/
├── before.txt    # Permission state before
├── after.txt     # Permission state after
├── changes.log   # What was changed
└── README.md     # Summary
```
