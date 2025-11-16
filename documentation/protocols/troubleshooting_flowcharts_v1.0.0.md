# Troubleshooting Flowcharts v1.0.0

**Version:** 1.0.0
**Last Updated:** November 12, 2025
**Purpose:** Visual decision trees for common protocol issues

---

## Table of Contents

1. [Images Not Displaying (404 Errors)](#flowchart-1-images-not-displaying-404-errors)
2. [WordPress Database Connection Failed](#flowchart-2-wordpress-database-connection-failed)
3. [Content Update Not Reflecting](#flowchart-3-content-update-not-reflecting)
4. [WP-CLI Command Fails](#flowchart-4-wp-cli-command-fails)
5. [Verification Step Shows Differences](#flowchart-5-verification-step-shows-differences)
6. [Theme/Plugin Modification Breaks Site](#flowchart-6-themeplugin-modification-breaks-site)

---

## Flowchart 1: Images Not Displaying (404 Errors)

```
START: Images return HTTP 404 Not Found
│
├─> Are images in WordPress media library?
│   │
│   ├─ NO ──> Images not uploaded properly
│   │         │
│   │         └─> Re-upload using correct path:
│   │             wp --path="/home/dave/skippy/rundaverun_local_site/app/public" media import
│   │
│   └─ YES ──> Images uploaded but not accessible
│              │
│              ├─> Check filesystem path
│              │   │
│              │   ├─> Are files in correct uploads directory?
│              │   │   │
│              │   │   ├─ NO ──> Wrong upload path used
│              │   │   │         │
│              │   │   │         ├─> Step 0: Verify installation path
│              │   │   │         │   cat ~/.config/Local/sites.json | python3 -m json.tool | grep path
│              │   │   │         │
│              │   │   │         ├─> Copy files to correct location
│              │   │   │         │   cp -r /wrong/path/uploads/* /correct/path/uploads/
│              │   │   │         │
│              │   │   │         └─> Test HTTP accessibility
│              │   │   │             curl -I http://site.local/wp-content/uploads/image.jpg
│              │   │   │
│              │   │   └─ YES ──> Files in correct location
│              │   │              │
│              │   │              └─> Check file permissions
│              │   │                  │
│              │   │                  ├─ Incorrect ──> Fix permissions
│              │   │                  │                chmod 644 /path/to/uploads/*.jpg
│              │   │                  │
│              │   │                  └─ Correct ──> Check web server
│              │   │                                   │
│              │   │                                   └─> Restart web server
│              │   │                                       sudo systemctl restart nginx
│              │   │
│              │   └─> Check WordPress site URL setting
│              │       │
│              │       └─> wp option get siteurl
│              │           │
│              │           ├─ Wrong ──> Update site URL
│              │           │            wp option update siteurl "http://correct.url"
│              │           │
│              │           └─ Correct ──> Check featured image meta
│              │                         wp post meta get <ID> _thumbnail_id
│              │
│              └─> RESOLVED
│
└─> END
```

### Quick Commands:
```bash
# 1. Verify installation path
cat ~/.config/Local/sites.json | python3 -m json.tool | grep -A 5 "rundaverun"

# 2. Test image HTTP accessibility
SITE_URL=$(wp --path="/correct/path" option get siteurl)
curl -I "$SITE_URL/wp-content/uploads/2025/11/image.jpg"

# 3. Check file exists on filesystem
ls -la /home/dave/skippy/rundaverun_local_site/app/public/wp-content/uploads/2025/11/

# 4. If files in wrong location, copy
cp -r "/wrong/path/uploads/2025/11/*" "/correct/path/uploads/2025/11/"
```

---

## Flowchart 2: WordPress Database Connection Failed

```
START: Error establishing database connection
│
├─> Is Local by Flywheel site started?
│   │
│   ├─ NO ──> Start site in Local app
│   │         │
│   │         └─> Retry command
│   │
│   └─ YES ──> Site is running
│              │
│              ├─> Check MySQL process
│              │   ps aux | grep mysql
│              │   │
│              │   ├─ Not running ──> MySQL service down
│              │   │                   │
│              │   │                   └─> Start MySQL
│              │   │                       systemctl start mysql
│              │   │
│              │   └─ Running ──> MySQL is active
│              │                   │
│              │                   └─> Check socket path in wp-config.php
│              │                       │
│              │                       ├─> Socket path correct?
│              │                       │   │
│              │                       │   ├─ NO ──> Update wp-config.php
│              │                       │   │         │
│              │                       │   │         ├─> Find correct socket:
│              │                       │   │         │   ps aux | grep mysql | grep socket
│              │                       │   │         │
│              │                       │   │         └─> Update DB_HOST in wp-config.php:
│              │                       │   │             localhost:/path/to/correct/socket
│              │                       │   │
│              │                       │   └─ YES ──> Check database exists
│              │                       │              │
│              │                       │              └─> mysql -u root -p -e "SHOW DATABASES;"
│              │                       │                  │
│              │                       │                  ├─ DB missing ──> Import database
│              │                       │                  │                 wp db import backup.sql
│              │                       │                  │
│              │                       │                  └─ DB exists ──> Check credentials
│              │                       │                                   Verify DB_USER, DB_PASSWORD
│              │                       │
│              │                       └─> Test connection
│              │                           wp db check
│              │
│              └─> RESOLVED
│
└─> END
```

### Quick Commands:
```bash
# 1. Check MySQL is running
ps aux | grep mysql

# 2. Find correct socket path
ps aux | grep mysql | grep -o 'socket=[^[:space:]]*'

# 3. Test database connection
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" db check

# 4. Verify database exists
mysql -S /path/to/mysqld.sock -u root -p -e "SHOW DATABASES;" | grep local
```

---

## Flowchart 3: Content Update Not Reflecting

```
START: Updated content not showing on site
│
├─> Did verification step show differences?
│   │
│   ├─ YES ──> Update failed or was modified
│   │         │
│   │         ├─> Check WordPress hooks/filters
│   │         │   Plugins may be modifying content
│   │         │   │
│   │         │   └─> Temporarily disable plugins
│   │         │       wp plugin deactivate --all
│   │         │       Retry update
│   │         │
│   │         └─> Check for PHP errors
│   │             tail -f /path/to/error.log
│   │
│   └─ NO ──> Update succeeded in database
│             │
│             ├─> Clear cache
│             │   │
│             │   ├─> WordPress cache
│             │   │   wp cache flush
│             │   │
│             │   ├─> Browser cache
│             │   │   Hard refresh (Ctrl+Shift+R)
│             │   │
│             │   └─> CDN cache (if applicable)
│             │       Purge CDN cache
│             │
│             ├─> Check correct page/post ID
│             │   │
│             │   └─> Verify you're viewing the right resource
│             │       wp post get <ID> --field=post_title
│             │
│             └─> Check HTTP response
│                 │
│                 ├─> curl -s "http://site.local/?p=<ID>" | grep "expected text"
│                 │   │
│                 │   ├─ Found ──> Content is there, cache issue
│                 │   │            Clear browser cache
│                 │   │
│                 │   └─ Not found ──> Content not rendering
│                 │                    │
│                 │                    └─> Check theme template
│                 │                        Theme may not display content properly
│                 │
│                 └─> RESOLVED
│
└─> END
```

### Quick Commands:
```bash
# 1. Verify content in database
wp post get 105 --field=post_content | grep "search term"

# 2. Clear WordPress cache
wp cache flush

# 3. Test page renders
curl -s "http://rundaverun-local-complete-022655.local/?p=105" | grep "expected text"

# 4. Check for PHP errors
tail -50 /home/dave/.config/Local/run/EnByKrjFn/logs/php/php_errors.log
```

---

## Flowchart 4: WP-CLI Command Fails

```
START: WP-CLI command returns error
│
├─> Is --path parameter correct?
│   │
│   ├─ NO/UNSURE ──> Verify WordPress path
│   │               │
│   │               ├─> Step 0: Check installation path
│   │               │   wp --path="/path" db check
│   │               │
│   │               └─> If Local by Flywheel:
│   │                   cat ~/.config/Local/sites.json | python3 -m json.tool
│   │
│   └─ YES ──> Path is correct
│              │
│              ├─> Is wp-config.php accessible?
│              │   │
│              │   ├─ NO ──> Permission error
│              │   │         chmod 644 /path/to/wp-config.php
│              │   │
│              │   └─ YES ──> Check database connection
│              │              wp --path="/path" db check
│              │              │
│              │              ├─ FAIL ──> See "Database Connection Failed" flowchart
│              │              │
│              │              └─ OK ──> Database works
│              │                       │
│              │                       └─> Check command syntax
│              │                           │
│              │                           ├─> Review WP-CLI docs
│              │                           │   wp help <command>
│              │                           │
│              │                           └─> Check resource exists
│              │                               wp post get <ID>
│              │                               │
│              │                               ├─ Not found ──> Wrong ID
│              │                               │                List resources:
│              │                               │                wp post list
│              │                               │
│              │                               └─ Found ──> Check permissions
│              │                                             Current user has WP access?
│              │
│              └─> RESOLVED
│
└─> END
```

### Quick Commands:
```bash
# 1. Verify WP-CLI works
wp --version

# 2. Test database connection
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" db check

# 3. List available posts/pages
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" post list --post_type=page

# 4. Get command help
wp help post update
```

---

## Flowchart 5: Verification Step Shows Differences

```
START: diff shows differences between _final and _after
│
├─> Review the differences
│   diff /path/to/final.html /path/to/after.html
│   │
│   ├─> Differences are expected?
│   │   (e.g., WordPress added IDs, shortcodes expanded)
│   │   │
│   │   ├─ YES ──> Acceptable differences
│   │   │         │
│   │   │         └─> Document in README
│   │   │             "Minor WordPress auto-formatting applied"
│   │   │             ACCEPT and proceed
│   │   │
│   │   └─ NO ──> Unexpected differences
│   │             │
│   │             ├─> Content was modified by hooks/filters
│   │             │   │
│   │             │   └─> Investigate plugins
│   │             │       wp plugin list
│   │             │       │
│   │             │       └─> Disable suspect plugins
│   │             │           wp plugin deactivate <plugin-name>
│   │             │           Retry update
│   │             │
│   │             ├─> Update partially failed
│   │             │   │
│   │             │   └─> Check error logs
│   │             │       tail -f /path/to/error.log
│   │             │       │
│   │             │       └─> Fix errors and retry
│   │             │
│   │             └─> Wrong content applied
│   │                 │
│   │                 ├─> Verify _final.html content
│   │                 │   cat /path/to/final.html
│   │                 │   │
│   │                 │   ├─ Correct ──> Re-apply update
│   │                 │   │              wp post update <ID> --post_content="$(cat final.html)"
│   │                 │   │
│   │                 │   └─ Incorrect ──> Fix _final.html
│   │                 │                    Re-create from correct version
│   │                 │
│   │                 └─> Rollback and investigate
│   │                     wp post update <ID> --post_content="$(cat before.html)"
│   │
│   └─> RESOLVED or INVESTIGATE FURTHER
│
└─> END
```

### Quick Commands:
```bash
# 1. Compare files with context
diff -u /path/to/final.html /path/to/after.html | less

# 2. Check what plugins are active
wp --path="/path" plugin list --status=active

# 3. Rollback to original
wp post update 105 --post_content="$(cat /session/dir/page_105_before.html)"

# 4. Verify rollback
wp post get 105 --field=post_content > /session/dir/page_105_rolledback.html
diff /session/dir/page_105_before.html /session/dir/page_105_rolledback.html
```

---

## Flowchart 6: Theme/Plugin Modification Breaks Site

```
START: Site broken after theme/plugin modification
│
├─> What's the error?
│   │
│   ├─> White screen of death
│   │   │
│   │   └─> PHP fatal error
│   │       │
│   │       ├─> IMMEDIATE ROLLBACK
│   │       │   cp /session/dir/functions_before.php /path/to/theme/functions.php
│   │       │   │
│   │       │   └─> Verify site works
│   │       │       curl -I http://site.local
│   │       │       │
│   │       │       └─> Site restored ──> Review error
│   │       │                             │
│   │       │                             └─> Check PHP syntax
│   │       │                                 php -l /session/dir/functions_final.php
│   │       │                                 │
│   │       │                                 ├─ Syntax error ──> Fix syntax
│   │       │                                 │                   Missing semicolon, bracket, etc.
│   │       │                                 │
│   │       │                                 └─ Syntax OK ──> Logic error
│   │       │                                                   │
│   │       │                                                   └─> Review function logic
│   │       │                                                       Test in dev environment
│   │       │
│   │       └─> Check error log
│   │           tail -50 /path/to/php_errors.log
│   │
│   ├─> HTTP 500 error
│   │   │
│   │   └─> Server error
│   │       │
│   │       ├─> IMMEDIATE ROLLBACK (same as above)
│   │       │
│   │       └─> Check error log for details
│   │           │
│   │           ├─> Function name collision
│   │           │   Function already defined
│   │           │   │
│   │           │   └─> Rename function or add if(!function_exists())
│   │           │
│   │           └─> Missing dependency
│   │               Plugin/class not found
│   │               │
│   │               └─> Add required checks
│   │
│   └─> Site works but feature doesn't
│       │
│       └─> Logic error
│           │
│           ├─> Add debugging
│           │   error_log("Debug: " . print_r($variable, true));
│           │   │
│           │   └─> Test in dev environment first
│           │
│           └─> Review documentation
│               WordPress Codex, plugin docs
│
└─> RESOLVED or CONTINUE DEBUGGING
```

### Quick Commands:
```bash
# 1. IMMEDIATE ROLLBACK
SESSION_DIR="/path/to/session"
cp "$SESSION_DIR/functions_before.php" /path/to/theme/functions.php

# 2. Verify site accessible
curl -I http://rundaverun-local-complete-022655.local | grep "HTTP"

# 3. Check PHP syntax
php -l /path/to/theme/functions.php

# 4. View recent errors
tail -50 /home/dave/.config/Local/run/EnByKrjFn/logs/php/php_errors.log

# 5. Test in dev
wp eval "test_function();"
```

---

## Using These Flowcharts

### When to Reference:

1. **During Active Troubleshooting** - Follow the decision tree step by step
2. **Before Making Changes** - Review relevant flowchart to understand risks
3. **Training New Users** - Use as teaching tool for common issues
4. **Protocol Updates** - Reference when identifying new edge cases

### Integration with Protocols:

- **CLAUDE.md** - References these flowcharts in troubleshooting sections
- **Work Files Preservation Protocol v2.1** - Comprehensive troubleshooting section links here
- **Verification scripts** - Automated tools implement these decision paths

### Adding New Flowcharts:

When you encounter a new issue type:
1. Document the problem and solution
2. Create decision tree with all decision points
3. Add to this file
4. Update protocol references

---

## Quick Reference Summary

| Issue | First Step | Most Common Fix |
|-------|------------|-----------------|
| Images 404 | Verify installation path | Copy files to correct location |
| DB connection fail | Check MySQL running | Fix socket path in wp-config.php |
| Content not reflecting | Clear cache | wp cache flush + hard refresh |
| WP-CLI fails | Verify --path | Check ~/.config/Local/sites.json |
| Verification diff | Review differences | Check for plugin modifications |
| Site broken | IMMEDIATE ROLLBACK | Restore from _before file |

---

**Version:** 1.0.0
**Last Updated:** November 12, 2025
**Status:** Active
**Part of:** Protocol v2.1+ (100% Coverage)
