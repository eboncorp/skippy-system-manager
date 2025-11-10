# WordPress Maintenance Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-10
**Owner:** Protocol Working Group
**Status:** Active


**Date Created**: 2025-10-28
**Purpose**: Complete WordPress development, deployment, and troubleshooting procedures
**Applies To**: All WordPress sites, especially rundaverun.org campaign site
**Priority**: CRITICAL (40% of recent work)

## Purpose

This protocol covers comprehensive WordPress operations:
- Local development setup (Local by Flywheel)
- Production environment management (GoDaddy)
- Database operations (export, import, search-replace)
- WP-CLI commands and troubleshooting
- GoDaddy-specific quirks and workarounds
- Deployment workflows and verification

---

## Overview

This protocol covers all WordPress operations from local development through production deployment, focusing on the rundaverun.org campaign site but applicable to any WordPress installation.

## Core Principles

### WordPress Safety Rules
1. ✅ **ALWAYS** test locally before production changes
2. ✅ **ALWAYS** backup database before major operations
3. ✅ **ALWAYS** use `--allow-root` flag with WP-CLI on Local by Flywheel
4. ✅ **ALWAYS** verify file permissions (644 for files, 755 for directories)
5. ✅ **NEVER** edit production database directly
6. ✅ **NEVER** skip testing on mobile devices
7. ✅ **NEVER** deploy without verification checklist

## Environment Setup

### Local Development (Local by Flywheel)

**Site Details**:
- **Site Name**: rundaverun-local
- **Local URL**: `http://rundaverun-local.local`
- **Site Path**: `/home/dave/Local Sites/rundaverun-local/app/public/`
- **Database**: Local MySQL (managed by Local app)
- **PHP Version**: Check with `wp cli info --allow-root`

**Access**:
```bash
cd "/home/dave/Local Sites/rundaverun-local/app/public"
```

**Common Local Commands**:
```bash
# Check WordPress version
wp core version --allow-root

# Check site URL
wp option get siteurl --allow-root
wp option get home --allow-root

# List users
wp user list --allow-root

# Check database prefix
wp db prefix --allow-root
```

### Production Environment (GoDaddy Managed WordPress)

**Site Details**:
- **Production URL**: `https://rundaverun.org`
- **Hosting**: GoDaddy Managed WordPress
- **SSH Access**: Limited (git_deployer user)
- **Database Prefix**: `wp_7e1ce15f22_` (CUSTOM - not standard wp_)
- **PHP Version**: Check via hosting panel

**GoDaddy-Specific Quirks** ⚠️:
1. **Custom Table Prefix**: Uses `wp_7e1ce15f22_` instead of standard `wp_`
2. **Backup Downloads**: File Manager only downloads files, NOT database
3. **Database Access**: Must download separately or use phpMyAdmin
4. **REST API**: Requires application passwords (not regular passwords)
5. **File Permissions**: May reset after updates
6. **Caching**: Aggressive server-side caching
7. **SSH**: Limited to git_deployer user, restricted commands

### CI/CD Integration (GitHub Actions)

**Repository**: Connected to GitHub with automated deployment
**Workflow**: Local → Git → GitHub → GoDaddy (via SSH)
**Note**: CI/CD setup incomplete as of Oct 2025 (SSH access issues)

## Database Operations

### Database Export (Backup)

**Local Database Export**:
```bash
cd "/home/dave/Local Sites/rundaverun-local/app/public"

# Export with timestamp
wp db export /home/dave/rundaverun/backups/local_db_$(date +%Y%m%d_%H%M%S).sql --allow-root

# Verify export
ls -lh /home/dave/rundaverun/backups/local_db_*.sql | tail -1
```

**Production Database Export** (via phpMyAdmin or WP-CLI if available):
```bash
# If WP-CLI access available
wp db export /path/to/backup/prod_db_$(date +%Y%m%d_%H%M%S).sql

# Otherwise download via phpMyAdmin:
# 1. Log into GoDaddy hosting panel
# 2. Open phpMyAdmin
# 3. Select database
# 4. Export → SQL format → Go
# 5. Save to /home/dave/rundaverun/backups/
```

**Important**: Always verify export file is not empty!
```bash
# Check file size (should be > 1MB for rundaverun site)
du -h backup_file.sql

# Check first few lines
head -20 backup_file.sql

# Should see SQL statements, not errors
```

### Database Import

**Import to Local**:
```bash
cd "/home/dave/Local Sites/rundaverun-local/app/public"

# ALWAYS backup current database first
wp db export /home/dave/rundaverun/backups/pre_import_$(date +%Y%m%d_%H%M%S).sql --allow-root

# Reset database (WARNING: Deletes all data)
wp db reset --yes --allow-root

# Import backup
wp db import /path/to/backup.sql --allow-root

# Verify import
wp db check --allow-root
```

**Common Import Issues**:

**Issue 1: Table Prefix Mismatch**
```bash
# Production uses: wp_7e1ce15f22_
# Local uses: wp_

# BEFORE import, update wp-config.php:
# $table_prefix = 'wp_7e1ce15f22_';

# OR after import, search-replace in SQL file:
sed 's/wp_7e1ce15f22_/wp_/g' production_backup.sql > local_backup.sql
```

**Issue 2: Import Errors**
```bash
# Check error log
tail -50 /home/dave/Local\ Sites/rundaverun-local/logs/php/error.log

# Common causes:
# - File too large (increase max_upload_size)
# - SQL syntax errors (check MySQL version compatibility)
# - Permissions (ensure wp user has access)
```

### URL Search-Replace

**Production → Local**:
```bash
cd "/home/dave/Local Sites/rundaverun-local/app/public"

# Replace all production URLs with local URLs
wp search-replace 'https://rundaverun.org' 'http://rundaverun-local.local' \
  --all-tables --allow-root

# Or with www subdomain
wp search-replace 'https://www.rundaverun.org' 'http://rundaverun-local.local' \
  --all-tables --allow-root

# Verify replacement
wp search-replace 'https://rundaverun.org' 'http://rundaverun-local.local' \
  --all-tables --allow-root --dry-run

# Clear cache
wp cache flush --allow-root
```

**Local → Production** (when deploying):
```bash
# On production (if WP-CLI available)
wp search-replace 'http://rundaverun-local.local' 'https://rundaverun.org' \
  --all-tables --allow-root

# IMPORTANT: Use HTTPS for production, HTTP for local
```

**Common URL Variations to Check**:
- `http://rundaverun.org` (no SSL)
- `https://rundaverun.org` (SSL)
- `http://www.rundaverun.org` (www subdomain)
- `https://www.rundaverun.org` (www + SSL)
- `rundaverun.org` (no protocol)

### Database Optimization

**Check Database Size**:
```bash
wp db size --allow-root

# Check individual table sizes
wp db query "SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)' FROM information_schema.TABLES WHERE table_schema = DATABASE() ORDER BY (data_length + index_length) DESC;" --allow-root
```

**Optimize Tables**:
```bash
wp db optimize --allow-root

# Verify optimization
wp db check --allow-root
```

**Clean Up Transients**:
```bash
# Delete expired transients
wp transient delete --expired --allow-root

# Delete all transients (if needed)
wp transient delete --all --allow-root
```

**Clean Up Revisions**:
```bash
# List post revisions
wp post list --post_type=revision --allow-root | wc -l

# Delete old revisions (keep last 5)
wp post delete $(wp post list --post_type=revision --format=ids --allow-root) --force --allow-root
```

## Content Management

### Pages & Posts

**List All Pages**:
```bash
wp page list --allow-root

# With specific fields
wp page list --fields=ID,post_title,post_status,post_date --allow-root

# Filter by status
wp page list --post_status=publish --allow-root
```

**Create New Page**:
```bash
wp post create --post_type=page \
  --post_title="Page Title" \
  --post_status=publish \
  --post_content="$(cat /path/to/content.md)" \
  --allow-root

# Returns page ID, save it
PAGE_ID=$(wp post create --post_type=page --post_title="Title" --post_status=publish --allow-root --porcelain)
```

**Update Existing Page**:
```bash
# Update content from file
wp post update <PAGE_ID> \
  --post_content="$(cat /path/to/new_content.md)" \
  --allow-root

# Update title
wp post update <PAGE_ID> \
  --post_title="New Title" \
  --allow-root

# Update multiple fields
wp post update <PAGE_ID> \
  --post_title="New Title" \
  --post_content="New content" \
  --post_status=publish \
  --allow-root
```

**Delete Page**:
```bash
# Move to trash
wp post delete <PAGE_ID> --allow-root

# Permanently delete
wp post delete <PAGE_ID> --force --allow-root
```

**Get Page Content**:
```bash
# View page details
wp post get <PAGE_ID> --allow-root

# Get just the content
wp post get <PAGE_ID> --field=post_content --allow-root
```

### Policy Documents (Custom Post Type)

**RunDaveRun Campaign Specific**:

**List Policy Documents**:
```bash
wp post list --post_type=policy_document --allow-root

# Check if custom post type exists
wp post-type list --allow-root | grep policy
```

**Create Policy Document**:
```bash
wp post create --post_type=policy_document \
  --post_title="Policy Title" \
  --post_status=publish \
  --post_content="$(cat /path/to/policy.md)" \
  --allow-root
```

### Menus

**List Menus**:
```bash
wp menu list --allow-root
```

**List Menu Items**:
```bash
wp menu item list <MENU_ID> --allow-root

# Example for main menu (usually ID 2 or 3)
wp menu item list 2 --allow-root
```

**Add Page to Menu**:
```bash
wp menu item add-post <MENU_ID> <PAGE_ID> --allow-root

# With custom title
wp menu item add-post <MENU_ID> <PAGE_ID> \
  --title="Custom Menu Title" \
  --allow-root
```

### Media Library

**List Media**:
```bash
wp media list --allow-root

# Filter by type
wp media list --post_mime_type=image/jpeg --allow-root
```

**Import Media**:
```bash
wp media import /path/to/image.jpg \
  --title="Image Title" \
  --allow-root
```

**Regenerate Thumbnails**:
```bash
# Install plugin first if not present
wp plugin install regenerate-thumbnails --activate --allow-root

# Regenerate
wp regenerate-thumbnails --yes --allow-root
```

## File Management

### Upload Files to WordPress

**Via WP-CLI (if available)**:
```bash
# Upload to uploads directory
wp media import /path/to/local/file.pdf \
  --title="Document Title" \
  --allow-root
```

**Via File Manager (GoDaddy)**:
```bash
# Manual upload via hosting panel:
# 1. Go to File Manager in hosting panel
# 2. Navigate to /wp-content/uploads/
# 3. Create subdirectory if needed
# 4. Upload files
# 5. IMPORTANT: Set permissions to 644
```

**Correct Permissions**:
```bash
# Files should be 644
chmod 644 /path/to/file.pdf

# Directories should be 755
chmod 755 /path/to/directory

# Recursively fix permissions
find /home/dave/Local\ Sites/rundaverun-local/app/public/wp-content/uploads/ \
  -type f -exec chmod 644 {} \;

find /home/dave/Local\ Sites/rundaverun-local/app/public/wp-content/uploads/ \
  -type d -exec chmod 755 {} \;
```

### Glossary Files (RunDaveRun Specific)

**Current Setup**:
- **Location**: `/wp-content/uploads/glossary_v4.html` and `.json`
- **Page**: ID 328 - "Complete Voter Education Glossary"
- **Version**: v4.0 - 499 terms across 48 categories
- **Display**: Iframe embedding the HTML file

**Update Glossary**:
```bash
# 1. Upload new glossary files
cp /path/to/new/glossary_v4.1.html \
  "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/uploads/"

cp /path/to/new/glossary_v4.1.json \
  "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/uploads/"

# 2. Set permissions
chmod 644 "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/uploads/glossary_v4.1.*"

# 3. Update page 328 iframe src if filename changed
wp post update 328 \
  --post_content="<iframe src='/wp-content/uploads/glossary_v4.1.html' width='100%' height='1200px'></iframe>" \
  --allow-root

# 4. Clear cache
wp cache flush --allow-root

# 5. Test in browser
```

**Glossary Integration on Policy Pages**:
All policy pages should have this banner at top:
```html
<div class="glossary-notice" style="background: #e6f2ff; border-left: 4px solid #003f87; padding: 15px 20px;">
    <p><strong>💡 New to government terms?</strong> Visit our <a href="/voter-education-glossary/">Voter Education Glossary</a> to understand key concepts. <em>499 terms explained with Louisville-specific context.</em></p>
</div>
```

## Theme & Plugin Management

### Themes

**List Themes**:
```bash
wp theme list --allow-root
```

**Activate Theme**:
```bash
wp theme activate theme-name --allow-root
```

**Check Active Theme**:
```bash
wp theme list --status=active --allow-root
```

### Plugins

**List Plugins**:
```bash
wp plugin list --allow-root

# Check for updates
wp plugin list --update=available --allow-root
```

**Install Plugin**:
```bash
wp plugin install plugin-name --activate --allow-root

# From ZIP file
wp plugin install /path/to/plugin.zip --activate --allow-root
```

**Update Plugins**:
```bash
# Update all
wp plugin update --all --allow-root

# Update specific plugin
wp plugin update plugin-name --allow-root
```

**Deactivate/Delete Plugin**:
```bash
# Deactivate
wp plugin deactivate plugin-name --allow-root

# Delete
wp plugin delete plugin-name --allow-root
```

## Troubleshooting

### Common Issues & Solutions

#### Issue 1: Page Loads Blank

**Symptoms**: White screen, no content
**Diagnosis**:
```bash
# 1. Check PHP error log
tail -50 "/home/dave/Local Sites/rundaverun-local/logs/php/error.log"

# 2. Enable WordPress debug mode
wp config set WP_DEBUG true --allow-root
wp config set WP_DEBUG_LOG true --allow-root
wp config set WP_DEBUG_DISPLAY false --allow-root

# 3. Check for fatal errors
tail -50 "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/debug.log"

# 4. Check database connection
wp db check --allow-root
```

**Common Causes**:
- PHP fatal error (check error log)
- Database connection issue (check wp-config.php)
- Plugin conflict (deactivate all, test)
- Theme issue (switch to default theme)
- Memory limit (increase in wp-config.php)

**Solutions**:
```bash
# Increase memory limit
wp config set WP_MEMORY_LIMIT 256M --allow-root

# Deactivate all plugins
wp plugin deactivate --all --allow-root

# Switch to default theme
wp theme activate twentytwentyfour --allow-root
```

#### Issue 2: Images/Files Not Loading

**Symptoms**: Broken images, 404 errors for uploads
**Diagnosis**:
```bash
# 1. Check if file exists
ls -la "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/uploads/path/to/file.jpg"

# 2. Check permissions
# Files should be 644, directories 755

# 3. Test direct access
curl -I http://rundaverun-local.local/wp-content/uploads/path/to/file.jpg

# 4. Check URL in database
wp db query "SELECT * FROM wp_posts WHERE guid LIKE '%filename%'" --allow-root
```

**Common Causes**:
- Wrong permissions (600 instead of 644)
- Wrong path (absolute vs relative)
- URL still points to production
- File doesn't exist

**Solutions**:
```bash
# Fix permissions
chmod 644 /path/to/file.jpg
chmod 755 /path/to/directory/

# Search-replace URLs if needed
wp search-replace 'https://rundaverun.org' 'http://rundaverun-local.local' \
  --all-tables --allow-root

# Verify file is readable by web server
curl -s http://rundaverun-local.local/wp-content/uploads/file.jpg | head
```

#### Issue 3: Database Import Fails

**Symptoms**: Error during import, corrupted database
**Diagnosis**:
```bash
# 1. Check SQL file integrity
head -20 /path/to/backup.sql
tail -20 /path/to/backup.sql

# 2. Check file size
du -h /path/to/backup.sql

# 3. Check for SQL errors
grep -i "error" /path/to/backup.sql | head -10

# 4. Check MySQL version compatibility
wp db query "SELECT VERSION();" --allow-root
```

**Common Causes**:
- File corrupted during download
- SQL syntax incompatibility
- Character encoding issues
- File too large
- Table prefix mismatch

**Solutions**:
```bash
# Re-download backup (if from production)

# Convert line endings if needed
dos2unix /path/to/backup.sql

# Import in smaller chunks
split -l 10000 backup.sql backup_chunk_
for chunk in backup_chunk_*; do
    wp db query < "$chunk" --allow-root
done

# Check table prefix and update wp-config.php
```

#### Issue 4: Mobile Menu Not Working

**Symptoms**: Menu not visible/clickable on mobile
**Diagnosis**:
```bash
# 1. Check browser console (mobile device or DevTools)
# Look for JavaScript errors

# 2. Check menu exists
wp menu list --allow-root

# 3. Check menu items
wp menu item list <MENU_ID> --allow-root

# 4. Check theme mobile CSS
# Inspect mobile breakpoints in theme
```

**Common Causes**:
- JavaScript not loading
- CSS z-index issues
- Touch event conflicts
- Theme not responsive
- Plugin conflict

**Solutions**:
- Clear cache (browser + WordPress)
- Disable conflicting plugins
- Check mobile-specific CSS
- Test on actual mobile device
- Check theme mobile menu settings

#### Issue 5: CSS Changes Not Showing

**Symptoms**: CSS updates not visible
**Diagnosis**:
```bash
# 1. Check if CSS file updated
ls -la /path/to/style.css

# 2. Check cache status
wp cache flush --allow-root

# 3. Test direct CSS file access
curl -I http://rundaverun-local.local/wp-content/themes/theme-name/style.css

# 4. Check browser DevTools Network tab
# Look for cached CSS (304 status)
```

**Common Causes**:
- Browser cache
- WordPress cache
- Server-side cache (GoDaddy)
- CDN cache
- CSS not actually updated
- CSS specificity issues

**Solutions**:
```bash
# Clear WordPress cache
wp cache flush --allow-root

# Version CSS file (force reload)
# In theme functions.php:
# wp_enqueue_style('style', get_stylesheet_uri(), array(), '1.0.1');

# Hard refresh browser
# Ctrl+Shift+R (Windows/Linux)
# Cmd+Shift+R (Mac)

# Disable caching temporarily for testing
```

#### Issue 6: "No Terms Found" in Glossary

**Symptoms**: Glossary loads but shows no terms
**Diagnosis**:
```bash
# 1. Check if JSON file exists
ls -la "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/uploads/glossary_v4.json"

# 2. Check JSON file contents
head -50 "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/uploads/glossary_v4.json"

# 3. Validate JSON syntax
python3 -m json.tool /path/to/glossary_v4.json > /dev/null

# 4. Check file permissions
ls -la /path/to/glossary_v4.json
# Should be 644

# 5. Check browser console for JavaScript errors

# 6. Test direct file access
curl -s http://rundaverun-local.local/wp-content/uploads/glossary_v4.json | head
```

**Common Causes**:
- JSON file doesn't exist
- Wrong file path in HTML
- JSON syntax error
- Permissions issue (600 instead of 644)
- JavaScript error loading terms
- CORS issue

**Solutions**:
```bash
# Fix permissions
chmod 644 /path/to/glossary_v4.json

# Verify JSON is valid
python3 -m json.tool /path/to/glossary_v4.json

# Check path in glossary HTML file
# Should be relative: /wp-content/uploads/glossary_v4.json
# NOT absolute: http://domain.com/wp-content/uploads/...

# Test in browser DevTools Network tab
# Should see successful load of JSON file
```

## Testing Procedures

### Pre-Deployment Testing Checklist

**Local Testing** (before deployment):
- [ ] Homepage loads correctly
- [ ] All policy pages accessible
- [ ] Glossary search works
- [ ] Menu navigation works
- [ ] Forms submit correctly
- [ ] Images display properly
- [ ] Links are not broken
- [ ] Contact form works
- [ ] Mobile menu works
- [ ] Mobile layout correct
- [ ] Desktop layout correct
- [ ] No JavaScript errors (check console)
- [ ] No 404 errors (check network tab)
- [ ] Performance acceptable (< 3 second load)

**Browser Testing**:
- [ ] Chrome (desktop)
- [ ] Firefox (desktop)
- [ ] Safari (desktop if available)
- [ ] Chrome (mobile/responsive mode)
- [ ] Actual mobile device (if possible)

**Content Verification**:
- [ ] All policy documents display correctly
- [ ] Glossary has all 499 terms
- [ ] Voter Education hub links work
- [ ] About page content correct
- [ ] Contact information accurate

### Mobile Testing

**Device Testing**:
```bash
# Use browser DevTools responsive mode
# Test these breakpoints:
# - 320px (small phone)
# - 375px (iPhone)
# - 768px (tablet)
# - 1024px (desktop)
```

**Mobile Checklist**:
- [ ] Menu accessible (hamburger icon visible)
- [ ] Menu opens/closes correctly
- [ ] Touch targets large enough (44x44px minimum)
- [ ] Text readable (16px minimum)
- [ ] No horizontal scrolling
- [ ] Images scale properly
- [ ] Forms usable (inputs large enough)
- [ ] Buttons work on touch
- [ ] No text wrapping issues
- [ ] Footer displays correctly

## Performance Optimization

### Database Optimization

**Clean Up**:
```bash
# Delete spam comments
wp comment delete $(wp comment list --status=spam --format=ids --allow-root) --force --allow-root

# Delete trash posts
wp post delete $(wp post list --post_status=trash --format=ids --allow-root) --force --allow-root

# Optimize tables
wp db optimize --allow-root
```

### Caching

**WordPress Cache**:
```bash
# Flush all caches
wp cache flush --allow-root

# If using cache plugin (e.g., WP Super Cache)
wp cache flush --allow-root
```

**Browser Cache Headers**:
Check .htaccess or server config for:
```apache
# Browser caching
<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType image/jpg "access plus 1 year"
ExpiresByType image/jpeg "access plus 1 year"
ExpiresByType image/png "access plus 1 year"
ExpiresByType text/css "access plus 1 month"
ExpiresByType application/javascript "access plus 1 month"
</IfModule>
```

### Image Optimization

**Compress Images**:
```bash
# Install optimization plugin
wp plugin install ewww-image-optimizer --activate --allow-root

# Or use external tools before upload
# - TinyPNG
# - ImageOptim
# - squoosh.app
```

**Lazy Loading**:
```bash
# WordPress 5.5+ has native lazy loading
# Verify it's enabled in theme
```

## Backup Procedures

### Before Major Changes

**Always backup**:
1. Database
2. wp-content directory
3. .htaccess file
4. wp-config.php file

```bash
# Full backup script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/dave/rundaverun/backups/pre_change_$DATE"
SITE_PATH="/home/dave/Local Sites/rundaverun-local/app/public"

mkdir -p "$BACKUP_DIR"

# Database
wp db export "$BACKUP_DIR/database.sql" --allow-root

# wp-content
cp -r "$SITE_PATH/wp-content" "$BACKUP_DIR/"

# Config files
cp "$SITE_PATH/wp-config.php" "$BACKUP_DIR/"
cp "$SITE_PATH/.htaccess" "$BACKUP_DIR/" 2>/dev/null

echo "Backup complete: $BACKUP_DIR"
```

### Backup Schedule

**Recommended**:
- **Before deployment**: Always
- **After major changes**: Always
- **Weekly**: Automated (if possible)
- **Before updates**: Always (core, plugins, themes)

## Integration with Other Protocols

### With Backup Protocol
- Reference: `/home/dave/skippy/conversations/backup_strategy_protocol.md`
- Use backup procedures before risky operations

### With Git Workflow
- Reference: `/home/dave/skippy/conversations/git_workflow_protocol.md`
- Commit WordPress changes following git standards
- Include database exports in version control (or .gitignore them)

### With Deployment Checklist
- Reference: `/home/dave/skippy/conversations/deployment_checklist_protocol.md`
- Follow deployment checklist for production pushes

### With Error Logging
- Reference: `/home/dave/skippy/conversations/error_logging_protocol.md`
- Log WordPress errors following error protocol

## Quick Reference Commands

### Most Used WP-CLI Commands

```bash
# Database
wp db export backup.sql --allow-root
wp db import backup.sql --allow-root
wp db reset --yes --allow-root
wp search-replace 'old' 'new' --all-tables --allow-root

# Pages
wp page list --allow-root
wp post get <ID> --allow-root
wp post update <ID> --post_content="content" --allow-root
wp post create --post_type=page --post_title="Title" --allow-root

# Plugins
wp plugin list --allow-root
wp plugin activate plugin-name --allow-root
wp plugin deactivate plugin-name --allow-root

# Cache
wp cache flush --allow-root

# Users
wp user list --allow-root
wp user create username email@example.com --role=administrator --allow-root

# Site info
wp core version --allow-root
wp option get siteurl --allow-root
wp db check --allow-root
```

### Emergency Commands

```bash
# Reset admin password
wp user update admin --user_pass=newpassword --allow-root

# Deactivate all plugins (if site broken)
wp plugin deactivate --all --allow-root

# Switch to default theme (if theme broken)
wp theme activate twentytwentyfour --allow-root

# Repair database
wp db repair --allow-root

# Check for corrupted tables
wp db check --allow-root
```

## Best Practices

### Development Workflow
1. ✅ Always work locally first
2. ✅ Test thoroughly on local
3. ✅ Backup production before deployment
4. ✅ Deploy during low-traffic hours
5. ✅ Monitor after deployment
6. ✅ Have rollback plan ready

### Security
1. ✅ Keep WordPress core updated
2. ✅ Keep plugins updated
3. ✅ Keep themes updated
4. ✅ Use strong passwords
5. ✅ Limit login attempts
6. ✅ Regular security scans
7. ✅ Backup regularly
8. ✅ Use SSL (HTTPS)

### Performance
1. ✅ Optimize images before upload
2. ✅ Use caching plugin
3. ✅ Minimize plugins (only what's needed)
4. ✅ Regular database optimization
5. ✅ Monitor page load times
6. ✅ Use CDN if high traffic

---

**This protocol is part of the persistent memory system.**
**Reference when performing any WordPress operations.**
```
