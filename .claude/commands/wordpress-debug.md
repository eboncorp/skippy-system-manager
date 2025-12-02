---
description: Automated WordPress diagnostic - identifies issues in 15 layers
argument-hint: "[optional: specific issue like 'mobile' or '500 error']"
allowed-tools: ["Bash", "Read", "Grep", "WebFetch"]
---

# WordPress Debug Command

Comprehensive 15-layer diagnostic for WordPress issues. Reduces 2-3 hour debug sessions to 15-30 minutes.

## Quick Start

Run all diagnostics:
```bash
WP_PATH="/home/dave/skippy/rundaverun_local_site/app/public"
SITE_URL="http://rundaverun-local-complete-022655.local"
```

## 15-Layer Diagnostic Framework

### Layer 1: WordPress Core Health
```bash
echo "=== Layer 1: WordPress Core Health ==="
wp --path="$WP_PATH" core verify-checksums 2>&1 || echo "Core files modified"
wp --path="$WP_PATH" core version
wp --path="$WP_PATH" db check 2>&1 | tail -5
```

### Layer 2: Theme Status
```bash
echo "=== Layer 2: Theme Status ==="
wp --path="$WP_PATH" theme list --status=active --format=table
wp --path="$WP_PATH" theme status astra-child 2>&1
ls -la "$WP_PATH/wp-content/themes/astra-child/"
```

### Layer 3: Plugin Status
```bash
echo "=== Layer 3: Plugin Status ==="
wp --path="$WP_PATH" plugin list --format=table
wp --path="$WP_PATH" plugin list --status=active --field=name
```

### Layer 4: PHP Errors
```bash
echo "=== Layer 4: PHP Errors ==="
if [ -f "$WP_PATH/wp-content/debug.log" ]; then
  tail -50 "$WP_PATH/wp-content/debug.log" | grep -E "Fatal|Error|Warning" | tail -20
else
  echo "Debug log not found - check WP_DEBUG settings"
fi
```

### Layer 5: Database Connection
```bash
echo "=== Layer 5: Database Connection ==="
wp --path="$WP_PATH" db query "SELECT 1" 2>&1 && echo "DB connection OK"
wp --path="$WP_PATH" db size --tables --format=table | head -15
```

### Layer 6: URL/Rewrite Issues
```bash
echo "=== Layer 6: URL/Rewrite Status ==="
wp --path="$WP_PATH" option get siteurl
wp --path="$WP_PATH" option get home
wp --path="$WP_PATH" rewrite list --format=table | head -10
```

### Layer 7: HTTP Response Check
```bash
echo "=== Layer 7: HTTP Response Check ==="
for path in "/" "/about/" "/contact/" "/neighborhoods/"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL$path" 2>/dev/null)
  echo "$path: HTTP $STATUS"
done
```

### Layer 8: CSS/JS Loading
```bash
echo "=== Layer 8: CSS/JS Assets ==="
curl -s "$SITE_URL/" | grep -oE 'href="[^"]+\.css[^"]*"' | head -10
curl -s "$SITE_URL/" | grep -oE 'src="[^"]+\.js[^"]*"' | head -10
```

### Layer 9: Cache Status
```bash
echo "=== Layer 9: Cache Status ==="
wp --path="$WP_PATH" cache flush 2>&1
ls -la "$WP_PATH/wp-content/cache/" 2>/dev/null || echo "No cache directory"
```

### Layer 10: File Permissions
```bash
echo "=== Layer 10: File Permissions ==="
stat -c "%a %U:%G %n" "$WP_PATH/wp-config.php"
stat -c "%a %U:%G %n" "$WP_PATH/wp-content/"
stat -c "%a %U:%G %n" "$WP_PATH/wp-content/uploads/"
```

### Layer 11: wp-config.php Settings
```bash
echo "=== Layer 11: wp-config Settings ==="
grep -E "WP_DEBUG|SCRIPT_DEBUG|WP_DEBUG_LOG|WP_DEBUG_DISPLAY" "$WP_PATH/wp-config.php"
grep -E "define.*DISALLOW|define.*FS_METHOD" "$WP_PATH/wp-config.php"
```

### Layer 12: .htaccess Status
```bash
echo "=== Layer 12: .htaccess Status ==="
if [ -f "$WP_PATH/.htaccess" ]; then
  cat "$WP_PATH/.htaccess"
else
  echo "No .htaccess found"
fi
```

### Layer 13: Memory Limits
```bash
echo "=== Layer 13: Memory Limits ==="
grep -E "memory_limit|max_execution|upload_max" "$WP_PATH/wp-config.php" 2>/dev/null
wp --path="$WP_PATH" eval "echo 'PHP memory_limit: ' . ini_get('memory_limit');" 2>/dev/null
```

### Layer 14: mu-plugins Check
```bash
echo "=== Layer 14: Must-Use Plugins ==="
ls -la "$WP_PATH/wp-content/mu-plugins/" 2>/dev/null || echo "No mu-plugins directory"
```

### Layer 15: Recent Changes
```bash
echo "=== Layer 15: Recent Changes ==="
find "$WP_PATH/wp-content/themes/astra-child" -mtime -1 -type f 2>/dev/null | head -10
find "$WP_PATH/wp-content/plugins" -mtime -1 -type f 2>/dev/null | head -10
```

## Issue-Specific Diagnostics

### Mobile Issues
```bash
echo "=== Mobile-Specific Checks ==="
grep -r "max-width: 768px\|@media.*mobile" "$WP_PATH/wp-content/themes/astra-child/style.css" | head -20
curl -A "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)" -s "$SITE_URL/" | grep -E "viewport|mobile" | head -5
```

### 500 Error
```bash
echo "=== 500 Error Investigation ==="
tail -100 "$WP_PATH/wp-content/debug.log" 2>/dev/null | grep -E "Fatal|Error" | tail -20
wp --path="$WP_PATH" plugin deactivate --all --skip-plugins 2>&1
wp --path="$WP_PATH" theme activate twentytwentyfour --skip-themes 2>&1
```

### White Screen of Death
```bash
echo "=== WSOD Investigation ==="
wp --path="$WP_PATH" eval "echo 'PHP OK';" 2>&1
wp --path="$WP_PATH" config set WP_DEBUG true --raw 2>&1
wp --path="$WP_PATH" config set WP_DEBUG_LOG true --raw 2>&1
```

### CSS Not Loading
```bash
echo "=== CSS Investigation ==="
wp --path="$WP_PATH" option get stylesheet
ls -la "$WP_PATH/wp-content/themes/astra-child/style.css"
grep "Version:" "$WP_PATH/wp-content/themes/astra-child/style.css"
curl -sI "$SITE_URL/wp-content/themes/astra-child/style.css" | head -10
```

## Production Diagnostics

For production site (rundaverun.org):
```bash
PROD_CMD='SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i ~/.ssh/godaddy_rundaverun git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com'

# Run any wp command on production
$PROD_CMD "cd html && wp core version"
$PROD_CMD "cd html && wp plugin list --status=active"
$PROD_CMD "cd html && tail -50 wp-content/debug.log 2>/dev/null"
```

## Quick Fix Commands

### Flush Everything
```bash
wp --path="$WP_PATH" cache flush
wp --path="$WP_PATH" rewrite flush
wp --path="$WP_PATH" transient delete --all
```

### Reset Permissions
```bash
find "$WP_PATH" -type d -exec chmod 755 {} \;
find "$WP_PATH" -type f -exec chmod 644 {} \;
chmod 600 "$WP_PATH/wp-config.php"
```

### Enable Debug Mode
```bash
wp --path="$WP_PATH" config set WP_DEBUG true --raw
wp --path="$WP_PATH" config set WP_DEBUG_LOG true --raw
wp --path="$WP_PATH" config set WP_DEBUG_DISPLAY false --raw
```

## Output

After running diagnostics, provide:
1. **Summary** - What layers passed/failed
2. **Root Cause** - Most likely issue
3. **Fix** - Specific commands to resolve
4. **Prevention** - How to avoid in future

## Session Directory

Always save diagnostic output:
```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_debug"
mkdir -p "$SESSION_DIR"
# Run diagnostics and save to $SESSION_DIR/diagnostic_report.md
```
