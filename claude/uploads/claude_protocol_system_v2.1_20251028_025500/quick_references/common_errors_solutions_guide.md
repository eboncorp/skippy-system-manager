# Common Errors & Solutions Guide

**Date Created**: 2025-10-28
**Purpose**: Quick reference for frequently encountered errors and solutions
**Applies To**: All projects (WordPress, scripts, system)
**Priority**: HIGH (saves troubleshooting time)

## How to Use This Guide

1. Find your error message or symptom
2. Try the quick fix first
3. If quick fix doesn't work, follow detailed solution
4. Document any new errors encountered

---

## WordPress Errors

### Error: "Error establishing a database connection"

**Symptom**: White screen with error message
**Common Causes**: Wrong database credentials, database server down, corrupted database

**Quick Fix**:
```bash
# Check wp-config.php database settings
cd "/home/dave/Local Sites/rundaverun-local/app/public"
grep "DB_NAME\|DB_USER\|DB_PASSWORD\|DB_HOST" wp-config.php

# Test database connection
wp db check --allow-root
```

**Detailed Solution**:
```bash
# 1. Verify database credentials in wp-config.php
# DB_NAME: Should match database name
# DB_USER: Should match database user
# DB_PASSWORD: Should match password
# DB_HOST: Usually 'localhost' or '127.0.0.1'

# 2. Check if MySQL/MariaDB is running
sudo systemctl status mysql
# Or
sudo systemctl status mariadb

# 3. Restart database if needed
sudo systemctl restart mysql

# 4. Test connection manually
mysql -u DB_USER -p -h localhost

# 5. Repair database if corrupted
wp db repair --allow-root
```

---

### Error: "This site is experiencing technical difficulties"

**Symptom**: WordPress admin shows generic error message
**Common Causes**: Plugin conflict, theme error, PHP error

**Quick Fix**:
```bash
# Check debug.log for actual error
tail -50 wp-content/debug.log

# Deactivate all plugins
wp plugin deactivate --all --allow-root
```

**Detailed Solution**:
```bash
# 1. Enable debugging to see actual error
# Edit wp-config.php:
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);

# 2. Check debug.log
tail -100 wp-content/debug.log

# 3. If plugin issue, deactivate all and reactivate one by one
wp plugin deactivate --all --allow-root
# Test site - if working now, plugin is the issue
wp plugin activate plugin-name --allow-root
# Test again, repeat until you find culprit

# 4. If theme issue, switch to default
wp theme activate twentytwentythree --allow-root

# 5. Fix the problematic plugin/theme or find alternative
```

---

### Error: "The uploaded file exceeds the upload_max_filesize directive in php.ini"

**Symptom**: Cannot upload files larger than X MB
**Common Causes**: PHP upload limits too low

**Quick Fix**:
```php
// Add to wp-config.php:
@ini_set('upload_max_size', '64M');
@ini_set('post_max_size', '64M');
@ini_set('max_execution_time', '300');
```

**Detailed Solution**:
```bash
# 1. Check current limits
wp eval "echo ini_get('upload_max_filesize');" --allow-root
wp eval "echo ini_get('post_max_size');" --allow-root

# 2. For Local by Flywheel, edit PHP settings:
# Local → Site → Show Folder → conf → php → php.ini.hbs

# 3. Increase limits:
upload_max_filesize = 64M
post_max_size = 64M
max_execution_time = 300

# 4. Restart site
# Local → Stop Site → Start Site

# 5. Verify new limits
wp eval "echo ini_get('upload_max_filesize');" --allow-root
```

---

### Error: "Sorry, you are not allowed to access this page"

**Symptom**: Cannot access WordPress admin pages
**Common Causes**: Incorrect user capabilities, plugin conflict

**Quick Fix**:
```bash
# Update user role
wp user set-role USERNAME administrator --allow-root

# Or deactivate security plugins
wp plugin deactivate wordfence --allow-root
```

**Detailed Solution**:
```bash
# 1. Check user role
wp user list --allow-root

# 2. Ensure user is administrator
wp user set-role USERNAME administrator --allow-root

# 3. If still failing, reset user capabilities
wp eval "require_once ABSPATH . 'wp-admin/includes/schema.php'; wp_install_defaults();" --allow-root

# 4. Check if security plugin is blocking
# Deactivate security plugins temporarily
wp plugin deactivate wordfence all-in-one-wp-security --allow-root

# 5. Clear any session/cache issues
wp cache flush --allow-root
# Delete browser cookies
```

---

### Error: "Fatal error: Maximum execution time of 30 seconds exceeded"

**Symptom**: Script times out during long operation
**Common Causes**: PHP time limit too low, slow operation

**Quick Fix**:
```php
// Add to top of problematic script:
set_time_limit(300); // 5 minutes
```

**Detailed Solution**:
```php
// 1. In wp-config.php (site-wide):
@ini_set('max_execution_time', '300');

// 2. In specific PHP file:
set_time_limit(300);

// 3. For WP-CLI operations, use --no-timeout:
wp command --allow-root --no-timeout

// 4. Optimize the operation:
// - Process in smaller batches
// - Use cron for long operations
// - Optimize database queries

// 5. For Local by Flywheel, edit php.ini.hbs:
max_execution_time = 300
```

---

### Error: "Call to undefined function wp_..." or Fatal Error in WordPress

**Symptom**: PHP fatal error about missing WordPress function
**Common Causes**: WordPress not properly loaded, corrupted core files

**Quick Fix**:
```bash
# Verify WordPress core files
wp core verify-checksums --allow-root

# Reinstall core (keeps database and plugins)
wp core download --force --allow-root
```

**Detailed Solution**:
```bash
# 1. Check if WordPress is loaded in your script
# Make sure script includes:
require_once '/path/to/wp-load.php';

# 2. Verify core files
wp core verify-checksums --allow-root

# 3. If core files corrupted, reinstall
wp core download --force --allow-root
# This downloads WordPress files without affecting database

# 4. Check file permissions
ls -la wp-includes/
# Should be readable (644 for files, 755 for directories)

# 5. If specific plugin causing issue:
# Rename plugin directory to deactivate
mv wp-content/plugins/problematic-plugin wp-content/plugins/problematic-plugin.disabled
```

---

## WP-CLI Errors

### Error: "YIKES! It looks like you're running this as root"

**Symptom**: WP-CLI refuses to run
**Common Causes**: Running as root on Local by Flywheel

**Quick Fix**:
```bash
# Add --allow-root flag
wp command --allow-root
```

**Detailed Solution**:
```bash
# On Local by Flywheel, ALWAYS use --allow-root:
wp plugin list --allow-root
wp db export backup.sql --allow-root

# Why: Local by Flywheel runs as root user
# Production usually doesn't need this flag

# To avoid typing every time, create alias:
echo "alias wp='wp --allow-root'" >> ~/.bashrc
source ~/.bashrc
# Now just type: wp plugin list
```

---

### Error: "This does not seem to be a WordPress installation"

**Symptom**: WP-CLI can't find WordPress
**Common Causes**: Running from wrong directory

**Quick Fix**:
```bash
# Change to WordPress directory
cd "/home/dave/Local Sites/rundaverun-local/app/public"
wp command --allow-root
```

**Detailed Solution**:
```bash
# 1. Verify you're in WordPress root directory
pwd
ls wp-config.php wp-includes/ wp-content/
# These should all exist

# 2. Change to correct directory
cd "/home/dave/Local Sites/rundaverun-local/app/public"

# 3. Or use --path flag
wp --path="/home/dave/Local Sites/rundaverun-local/app/public" plugin list --allow-root

# 4. Check wp-config.php exists and is readable
ls -la wp-config.php
```

---

### Error: "Error: The search-replace command could not be found"

**Symptom**: search-replace command doesn't work
**Common Causes**: Old WP-CLI version

**Quick Fix**:
```bash
# Use search-replace as sub-command:
wp search-replace 'old' 'new' --allow-root
```

**Detailed Solution**:
```bash
# 1. Update WP-CLI
wp cli update

# 2. Verify version
wp cli version

# 3. Use correct syntax:
# OLD: wp search 'old' 'new'
# NEW: wp search-replace 'old' 'new' --all-tables --allow-root

# 4. If still not working, reinstall WP-CLI
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
sudo mv wp-cli.phar /usr/local/bin/wp
```

---

## File Permission Errors

### Error: "403 Forbidden" on uploaded file

**Symptom**: Cannot access uploaded file via browser
**Common Causes**: File permissions too restrictive (600 instead of 644)

**Quick Fix**:
```bash
# Fix file permissions
chmod 644 path/to/file

# For directory of files
find path/to/directory -type f -exec chmod 644 {} \;
find path/to/directory -type d -exec chmod 755 {} \;
```

**Detailed Solution**:
```bash
# 1. Check current permissions
ls -la path/to/file
# Should show: -rw-r--r-- (644)
# If shows: -rw------- (600) = TOO RESTRICTIVE

# 2. Fix file permissions
chmod 644 file.php

# 3. Fix directory permissions
chmod 755 directory/

# 4. Fix entire wp-content (if needed)
find wp-content -type f -exec chmod 644 {} \;
find wp-content -type d -exec chmod 755 {} \;

# 5. GoDaddy: Always check after File Manager uploads
# File Manager often sets 600 permissions
```

---

### Error: "Permission denied" when running script

**Symptom**: Script won't execute
**Common Causes**: Script not executable

**Quick Fix**:
```bash
# Make script executable
chmod +x script.sh
```

**Detailed Solution**:
```bash
# 1. Check current permissions
ls -la script.sh
# Should show: -rwxr-xr-x (755 or 700)

# 2. Make executable
chmod +x script.sh
# Or more specifically:
chmod 755 script.sh

# 3. Run script
./script.sh

# 4. If still "Permission denied":
# Check if correct interpreter
head -1 script.sh
# Should show: #!/bin/bash or #!/usr/bin/env python3

# 5. Run directly with interpreter
bash script.sh
# or
python3 script.py
```

---

## Database Errors

### Error: "Error importing database: Unknown table prefix"

**Symptom**: Database import fails with table prefix error
**Common Causes**: Table prefix mismatch (local wp_ vs production wp_7e1ce15f22_)

**Quick Fix**:
```bash
# Search-replace prefix in SQL file before import
sed 's/wp_/wp_7e1ce15f22_/g' backup.sql > backup_godaddy.sql
wp db import backup_godaddy.sql --allow-root
```

**Detailed Solution**:
```bash
# 1. Check table prefix in wp-config.php
grep "table_prefix" wp-config.php
# Local shows: $table_prefix = 'wp_';
# GoDaddy shows: $table_prefix = 'wp_7e1ce15f22_';

# 2. Check prefix in SQL file
head -50 backup.sql | grep "CREATE TABLE"
# Should match wp-config.php prefix

# 3. If mismatch, search-replace in SQL:
sed 's/wp_/wp_7e1ce15f22_/g' local_backup.sql > godaddy_backup.sql

# 4. Import fixed SQL
wp db import godaddy_backup.sql --allow-root

# 5. Verify import
wp db check --allow-root
wp option get siteurl --allow-root
```

---

### Error: "Database connection timed out"

**Symptom**: Database operations fail with timeout
**Common Causes**: Database server slow, large operation

**Quick Fix**:
```bash
# Increase timeout
wp db import large_file.sql --allow-root --no-timeout
```

**Detailed Solution**:
```bash
# 1. Check database server status
sudo systemctl status mysql

# 2. For large imports, split file
split -l 10000 large_backup.sql chunk_

# Import each chunk:
for file in chunk_*; do
    echo "Importing $file..."
    wp db import "$file" --allow-root
done

# 3. Optimize database after import
wp db optimize --allow-root

# 4. Check slow query log (if available)
tail -100 /var/log/mysql/slow-query.log

# 5. For GoDaddy: Use phpMyAdmin with smaller chunks
```

---

## Git Errors

### Error: "fatal: Not a git repository"

**Symptom**: Git commands fail
**Common Causes**: Not in git repository directory

**Quick Fix**:
```bash
# Change to git repository directory
cd /home/dave/rundaverun/campaign

# Or initialize git if new repository
git init
```

**Detailed Solution**:
```bash
# 1. Check if in git repository
git status
# If error "Not a git repository", not in repo

# 2. Find git repository
find /home/dave -name ".git" -type d 2>/dev/null

# 3. Change to correct directory
cd /path/to/git/repo

# 4. Or initialize new repository
git init
git add .
git commit -m "Initial commit"

# 5. Add remote if needed
git remote add origin https://github.com/username/repo.git
```

---

### Error: "Your local changes would be overwritten by merge"

**Symptom**: Can't pull changes from remote
**Common Causes**: Local uncommitted changes conflict with remote

**Quick Fix**:
```bash
# Stash local changes temporarily
git stash
git pull
git stash pop
```

**Detailed Solution**:
```bash
# 1. See what changes you have
git status
git diff

# 2. Option A: Keep local changes
git stash
git pull
git stash pop
# Resolve any conflicts

# 3. Option B: Discard local changes
git checkout -- filename
# Or discard all changes:
git reset --hard HEAD

# 4. Option C: Commit local changes first
git add .
git commit -m "Local changes before pull"
git pull

# 5. After pull, resolve any conflicts
git status
# Edit conflicting files
git add .
git commit -m "Resolved merge conflicts"
```

---

## SSH/Connection Errors

### Error: "Connection refused" or "Connection timed out"

**Symptom**: Cannot connect to server
**Common Causes**: Wrong host, firewall, SSH not running

**Quick Fix**:
```bash
# Test connection
ping example.com

# Test SSH port
nc -zv example.com 22
```

**Detailed Solution**:
```bash
# 1. Verify hostname
ping rundaverun.org
# Should get response

# 2. Check if SSH port open
nc -zv rundaverun.org 22
# Should say "Connection to rundaverun.org 22 port [tcp/ssh] succeeded!"

# 3. Check SSH service running (if local server)
sudo systemctl status ssh
sudo systemctl start ssh

# 4. Check firewall
sudo ufw status
# Ensure port 22 allowed

# 5. Verify SSH credentials
ssh -v user@host
# -v shows verbose output for debugging

# 6. For GoDaddy: SSH may not be available
# Use File Manager, FTP, or phpMyAdmin instead
```

---

## Mobile/Browser Errors

### Error: "Mobile menu not opening" or "Menu button not working"

**Symptom**: Mobile menu doesn't work on phones/tablets
**Common Causes**: JavaScript error, z-index conflict, injector not active

**Quick Fix**:
```bash
# Check if mobile-menu-injector.php exists
ls -la wp-content/mu-plugins/mobile-menu-injector.php

# Verify JavaScript console for errors (F12)
```

**Detailed Solution**:
```bash
# 1. Verify injector file exists and has correct permissions
ls -la wp-content/mu-plugins/mobile-menu-injector.php
# Should be: -rw-r--r-- (644)
chmod 644 wp-content/mu-plugins/mobile-menu-injector.php

# 2. Open browser DevTools (F12) → Console
# Look for JavaScript errors

# 3. Check z-index in browser DevTools
# Inspect menu element → Computed styles
# z-index should be high (9999)

# 4. Test on actual mobile device
# DevTools mobile view may not match real device

# 5. Clear all caches
wp cache flush --allow-root
# Clear browser cache: Ctrl+Shift+R

# 6. Check if JavaScript file loaded
# DevTools → Network tab → Filter: JS
# Should show mobile-menu script loading
```

---

### Error: "Layout broken on mobile" or "Elements overlapping"

**Symptom**: Website looks broken on mobile devices
**Common Causes**: CSS media queries not working, viewport meta tag missing

**Quick Fix**:
```html
<!-- Verify viewport meta tag in <head>: -->
<meta name="viewport" content="width=device-width, initial-scale=1">
```

**Detailed Solution**:
```bash
# 1. Check viewport meta tag in header.php
grep "viewport" wp-content/themes/campaign/header.php

# 2. Test in browser DevTools mobile view
# F12 → Toggle device toolbar

# 3. Check CSS media queries
# DevTools → Sources → Open CSS file
# Look for @media queries

# 4. Common media query issues:
# - Wrong breakpoints
# - Missing !important where needed
# - Specificity issues

# 5. Test on actual device
# Don't rely only on DevTools

# 6. Check for horizontal scrolling
# Should never scroll horizontally on mobile
# In CSS: overflow-x: hidden on body (if necessary)
```

---

## Cache Errors

### Error: "Changes not showing after deployment"

**Symptom**: Updated files but old content still displays
**Common Causes**: Multiple cache layers not cleared

**Quick Fix**:
```bash
# Clear WordPress cache
wp cache flush --allow-root

# Clear browser cache
# Ctrl+Shift+R (Chrome/Firefox)

# Test in private/incognito window
```

**Detailed Solution**:
```bash
# 1. Clear WordPress cache
wp cache flush --allow-root
wp rewrite flush --allow-root

# 2. Clear GoDaddy server cache (for production)
# Login to GoDaddy dashboard
# My Products → Managed WordPress → Settings → Clear Cache

# 3. Clear browser cache
# Chrome/Firefox: Ctrl+Shift+R
# Safari: Cmd+Shift+R

# 4. Test with curl (bypasses all browser cache)
curl -I https://rundaverun.org
# Check Last-Modified header

# 5. Test in private/incognito window

# 6. Clear CDN cache (if using CDN)

# 7. Verify files actually uploaded
# Check File Manager timestamp on production

# 8. Check if old file cached on your browser
# View source (Ctrl+U) and check timestamps in code
```

---

## Quick Diagnostic Commands

### WordPress Health Check
```bash
cd "/home/dave/Local Sites/rundaverun-local/app/public"

# Database
wp db check --allow-root

# Core files
wp core verify-checksums --allow-root

# Plugins
wp plugin list --allow-root

# Theme
wp theme list --status=active --allow-root

# Site URLs
wp option get siteurl --allow-root
wp option get home --allow-root

# WordPress version
wp core version --allow-root

# PHP version
wp eval "echo PHP_VERSION;" --allow-root
```

### File Permission Check
```bash
# Check WordPress directory permissions
ls -la wp-content/

# Files should be: 644 (-rw-r--r--)
# Directories should be: 755 (drwxr-xr-x)

# Find files with wrong permissions
find wp-content -type f ! -perm 644
find wp-content -type d ! -perm 755
```

### Error Log Check
```bash
# WordPress debug log
tail -50 wp-content/debug.log

# System error log
sudo tail -50 /var/log/syslog

# Apache error log (if applicable)
sudo tail -50 /var/log/apache2/error.log

# MySQL error log (if applicable)
sudo tail -50 /var/log/mysql/error.log
```

---

## Emergency Procedures

### Site Completely Broken

**Quick Recovery**:
```bash
# 1. Enable maintenance mode
echo '<?php $upgrading = time(); ?>' > .maintenance

# 2. Deactivate all plugins
wp plugin deactivate --all --allow-root

# 3. Switch to default theme
wp theme activate twentytwentythree --allow-root

# 4. Test site - if working now, plugin/theme was issue

# 5. Restore from backup if still broken
wp db import /path/to/backup.sql --allow-root

# 6. Disable maintenance mode
rm .maintenance
```

### Database Completely Corrupted

**Quick Recovery**:
```bash
# 1. Stop making changes!

# 2. Try repair
wp db repair --allow-root

# 3. If repair fails, restore from backup
wp db reset --yes --allow-root
wp db import /home/dave/rundaverun/backups/latest_backup.sql --allow-root

# 4. Verify restore
wp db check --allow-root
wp option get siteurl --allow-root

# 5. Clear all caches
wp cache flush --allow-root
```

---

## Prevention Checklist

To avoid common errors:

- [ ] **Before any changes**: Create backup
- [ ] **Before database operations**: Export database
- [ ] **Before plugin activation**: Check compatibility
- [ ] **After file uploads**: Verify permissions (644/755)
- [ ] **After deployment**: Clear all cache levels
- [ ] **After database import**: Verify table prefix
- [ ] **Before git operations**: Check current branch
- [ ] **Regular maintenance**: Update plugins/themes
- [ ] **Monitor logs**: Check debug.log regularly
- [ ] **Test locally first**: Never change production directly

---

## When to Get Help

**Seek help if**:
- Data loss has occurred
- Security breach suspected
- Multiple solutions attempted without success
- Issue affects production site and causes downtime
- Issue involves hosting provider (GoDaddy support)

**Before asking for help, document**:
- What you were trying to do
- What happened instead
- What you've already tried
- Error messages (exact text)
- Environment details (local/production, versions)

---

**This guide is part of the persistent memory system.**
**Add new errors and solutions as they're encountered.**
**Update solutions if better approaches are found.**
