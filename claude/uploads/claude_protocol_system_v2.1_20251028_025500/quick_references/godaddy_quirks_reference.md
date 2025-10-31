# GoDaddy Managed WordPress Quirks Reference

**Date Created**: 2025-10-28
**Purpose**: Document GoDaddy-specific quirks and workarounds
**Applies To**: rundaverun.org (GoDaddy Managed WordPress)
**Priority**: HIGH (prevents recurring issues)

## Overview

GoDaddy Managed WordPress has several quirks and limitations that differ from standard WordPress hosting. This document catalogs known issues and workarounds to prevent repeated troubleshooting.

---

## Database Quirks

### Custom Table Prefix ⚠️

**Issue**: GoDaddy uses custom table prefix instead of standard `wp_`

**Details**:
- Standard WordPress: `wp_`
- GoDaddy: `wp_7e1ce15f22_`
- This affects database queries and imports

**Impact**:
- Database imports from local must match prefix
- Direct SQL queries must use correct prefix
- Some plugins may not recognize tables

**Solution**:

```bash
# When importing database, check prefix in SQL file
head -20 backup.sql | grep "CREATE TABLE"
# Should show: CREATE TABLE `wp_7e1ce15f22_posts`

# If importing from local (has wp_ prefix):
# Option 1: Search-replace in SQL file before import
sed 's/wp_/wp_7e1ce15f22_/g' local_backup.sql > godaddy_backup.sql

# Option 2: Use WP-CLI search-replace after import
wp search-replace 'wp_' 'wp_7e1ce15f22_' --allow-root

# Verify prefix in wp-config.php
grep "table_prefix" wp-config.php
# Should show: $table_prefix = 'wp_7e1ce15f22_';
```

**Prevention**:
- Always check table prefix before database operations
- Use WP-CLI commands that handle prefix automatically
- Document prefix in deployment notes

---

## File Management Quirks

### File Manager vs FTP Uploads

**Issue**: Files uploaded via File Manager may have wrong permissions

**Details**:
- Files uploaded via File Manager: Often get 600 permissions
- Files uploaded via FTP: Usually get correct 644 permissions
- Files with 600 permissions = not accessible via web

**Symptoms**:
- Uploaded files return 403 Forbidden
- Images don't display
- CSS/JS files don't load

**Solution**:

```bash
# Via File Manager, select files and change permissions:
# Files should be: 644
# Directories should be: 755

# Or via SSH (if available):
find wp-content/uploads -type f -exec chmod 644 {} \;
find wp-content/uploads -type d -exec chmod 755 {} \;

# Check permissions:
ls -la wp-content/uploads/
```

**Prevention**:
- Always verify permissions after File Manager uploads
- Prefer FTP for file uploads when possible
- Include permission check in deployment checklist

---

### File Manager Backup Limitation

**Issue**: File Manager "Download Directory" only downloads files, NOT database

**Details**:
- File Manager download = files only
- Database must be backed up separately via phpMyAdmin
- No automatic combined backup option

**Solution**:

```bash
# File Backup:
# 1. File Manager → Select wp-content → Download
# 2. Extracts to ZIP file (files only)

# Database Backup:
# 1. phpMyAdmin → Export → Custom
# 2. Select all tables
# 3. Download SQL file

# Combined backup requires TWO separate operations
```

**Prevention**:
- Document backup procedure includes BOTH steps
- Create backup checklist
- Never assume "backup" includes database

---

## SSH/Command Line Quirks

### Limited SSH Access

**Issue**: GoDaddy Managed WordPress has restricted SSH access

**Details**:
- SSH may not be available by default
- SSH access may require account upgrade
- Some commands restricted for security
- WP-CLI may not be installed or may be restricted

**Workaround**:

```bash
# Check if SSH is available:
# Try connecting via SSH
ssh username@serveraddress

# If SSH unavailable, use alternatives:
# - File Manager (web interface)
# - FTP/SFTP clients (FileZilla, Cyberduck)
# - phpMyAdmin (database operations)
# - WordPress admin (plugin/theme management)

# For WP-CLI operations without SSH:
# - Use Local by Flywheel locally
# - Make changes locally, deploy via File Manager/FTP
```

**Prevention**:
- Don't assume SSH is available
- Have alternative methods ready
- Test operations locally before attempting on production

---

### Deployment File Upload Issues

**Issue**: GitHub Actions deployment may fail silently

**Details**:
- GitHub Actions uses SFTP to deploy
- Connection issues may not show clear error
- Files may partially upload
- Old files may not be removed

**Solution**:

```bash
# After deployment, verify files uploaded:
# 1. Check File Manager for new file timestamps
# 2. Check file sizes match local versions
# 3. Test affected pages in browser

# If deployment failed:
# 1. Check GitHub Actions logs
# 2. Verify SFTP credentials in GitHub Secrets
# 3. Manual upload via File Manager as backup
```

**Prevention**:
- Always verify deployment succeeded
- Include post-deployment verification in checklist
- Have manual upload procedure ready

---

## Cache Quirks

### Server-Side Caching

**Issue**: GoDaddy has multiple levels of caching that can show stale content

**Details**:
- WordPress cache (object cache, transients)
- GoDaddy server cache (varnish/nginx)
- CDN cache (if enabled)
- Browser cache

**Symptoms**:
- Changes not visible after deployment
- Old content shows after update
- Changes visible in admin but not frontend

**Solution**:

```bash
# 1. Clear WordPress cache
wp cache flush --allow-root

# 2. Clear GoDaddy cache
# Via GoDaddy dashboard:
# My Products → Managed WordPress → Settings → Clear Cache

# 3. Hard refresh browser
# Chrome/Firefox: Ctrl+Shift+R
# Safari: Cmd+Shift+R

# 4. Verify with curl (bypasses browser cache)
curl -I https://rundaverun.org
# Check Last-Modified header

# 5. Test in private/incognito window
```

**Prevention**:
- Always clear ALL cache levels after deployment
- Include cache clearing in deployment checklist
- Test in private/incognito window
- Document cache clearing procedure

---

## WordPress Admin Quirks

### Plugin/Theme Installation Restrictions

**Issue**: Some plugins/themes cannot be installed via WordPress admin

**Details**:
- Managed WordPress restricts certain plugins for security
- Cannot install plugins that conflict with managed environment
- Cannot install themes with known security issues

**Solution**:

```bash
# If plugin installation blocked:
# 1. Check GoDaddy's approved plugins list
# 2. Contact GoDaddy support for exceptions
# 3. Upload via File Manager (if plugin is safe):
#    - Upload to wp-content/plugins/
#    - Extract if zipped
#    - Activate in WordPress admin

# Alternative: Use approved alternatives
# Example: If security plugin blocked, use GoDaddy's built-in security
```

**Prevention**:
- Check plugin compatibility with Managed WordPress before purchasing
- Research if GoDaddy has native alternative
- Keep list of approved plugins

---

## Database Quirks

### phpMyAdmin Session Timeouts

**Issue**: phpMyAdmin sessions timeout quickly on GoDaddy

**Details**:
- phpMyAdmin may timeout during large imports
- Session expires after 15-30 minutes of inactivity
- Large database imports may fail mid-process

**Solution**:

```bash
# For large database imports:
# 1. Split large SQL files into smaller chunks
split -l 10000 large_backup.sql chunk_

# 2. Import chunks sequentially via phpMyAdmin

# 3. Or use WP-CLI (if SSH available)
wp db import backup.sql --allow-root

# 4. Monitor import progress
# phpMyAdmin shows progress bar during import
```

**Prevention**:
- Break large databases into manageable chunks
- Use WP-CLI when possible
- Keep active tab open during imports

---

### Database Size Limits

**Issue**: GoDaddy plans have database size limits

**Details**:
- Database size limits vary by plan
- Exceeding limit prevents new content
- No automatic cleanup

**Solution**:

```bash
# Check current database size:
# phpMyAdmin → Database → Size column

# Clean up database:
# 1. Delete spam/trash comments
wp comment delete $(wp comment list --status=spam --format=ids --allow-root) --force --allow-root

# 2. Delete post revisions
wp post delete $(wp post list --post_type=revision --format=ids --allow-root) --force --allow-root

# 3. Optimize database
wp db optimize --allow-root

# 4. Remove unused transients
wp transient delete --all --allow-root
```

**Prevention**:
- Monitor database size regularly
- Limit post revisions in wp-config.php:
  ```php
  define('WP_POST_REVISIONS', 3);
  ```
- Schedule regular cleanups

---

## Performance Quirks

### Resource Limits

**Issue**: GoDaddy Managed WordPress has resource limits per plan

**Details**:
- PHP memory limit (varies by plan)
- Max execution time (30-60 seconds)
- Upload file size limit
- Can't modify php.ini directly

**Solution**:

```php
// In wp-config.php (if limits too low):
define('WP_MEMORY_LIMIT', '256M');
define('WP_MAX_MEMORY_LIMIT', '512M');

// For specific operations, increase in plugin/theme code:
ini_set('memory_limit', '512M');
set_time_limit(300);

// For uploads, may need to contact GoDaddy support
```

**Prevention**:
- Optimize images before uploading
- Avoid memory-intensive plugins
- Monitor resource usage
- Upgrade plan if consistently hitting limits

---

## Email Quirks

### SMTP Configuration

**Issue**: wp_mail() may not work reliably on GoDaddy

**Details**:
- Shared hosting can have email delivery issues
- Emails may be marked as spam
- No guarantee of delivery

**Solution**:

```php
// Use SMTP plugin for reliable email:
// 1. Install "WP Mail SMTP" or similar
// 2. Configure with external SMTP:
//    - Gmail SMTP
//    - SendGrid
//    - Mailgun
//    - AWS SES

// Or use GoDaddy's email service (if part of plan)

// Test email sending:
wp eval "wp_mail('test@example.com', 'Test', 'Test message');" --allow-root
```

**Prevention**:
- Configure SMTP plugin on site setup
- Test email functionality after deployment
- Use transactional email service for critical emails

---

## SSL/Security Quirks

### SSL Certificate Management

**Issue**: SSL certificate auto-renews but may have brief gaps

**Details**:
- GoDaddy auto-renews SSL certificates
- May have 5-10 minute gap during renewal
- Renewal happens automatically (usually)

**Solution**:

```bash
# Check SSL certificate:
curl -I https://rundaverun.org
# Look for valid SSL in response

# If SSL error:
# 1. Wait 10-15 minutes (may be renewing)
# 2. Check GoDaddy dashboard for SSL status
# 3. Contact GoDaddy support if persists

# Force HTTPS in wp-config.php:
define('FORCE_SSL_ADMIN', true);
```

**Prevention**:
- Monitor SSL expiration dates
- Enable email alerts for SSL issues
- Have GoDaddy support contact ready

---

### Security Plugins Limitations

**Issue**: Some security plugins conflict with GoDaddy's built-in security

**Details**:
- GoDaddy has built-in malware scanning
- GoDaddy has built-in firewall
- Third-party security plugins may conflict
- Some security features redundant

**Solution**:

```bash
# Use GoDaddy's native security features:
# - Malware scanning (automatic)
# - SSL certificate (included)
# - Firewall (managed)
# - Backup (via control panel)

# If additional security needed:
# - Use approved security plugins
# - Focus on:
#   - Login security (2FA)
#   - Activity logging
#   - File integrity monitoring
```

**Prevention**:
- Check which security features GoDaddy provides
- Don't duplicate protection
- Test security plugins before full deployment

---

## Backup Quirks

### Automatic Backups

**Issue**: GoDaddy provides automatic backups but restoration process unclear

**Details**:
- Daily automatic backups (included in plan)
- Backups stored for 30 days
- Restoration requires support ticket (sometimes)
- No direct download of automatic backups

**Solution**:

```bash
# Create your own backups (don't rely solely on GoDaddy):

# 1. Database backup
wp db export backup_$(date +%Y%m%d).sql --allow-root

# 2. Files backup
# Download via File Manager or FTP

# 3. Store backups locally:
/home/dave/rundaverun/backups/

# 4. Schedule regular backups (weekly minimum)
```

**Prevention**:
- Maintain your own backup strategy
- Don't rely solely on GoDaddy backups
- Test restoration procedure
- Document backup locations

---

## Deployment Quirks

### File Upload Timing

**Issue**: Large files may timeout during upload

**Details**:
- File Manager has upload timeout
- Large themes/plugins may fail
- No resume feature for failed uploads

**Solution**:

```bash
# For large files:
# 1. Upload via FTP (more reliable than File Manager)
# 2. Upload ZIP, then extract on server
# 3. Split large files if possible

# Via File Manager:
# 1. Upload ZIP file
# 2. Right-click → Extract
# 3. Delete ZIP after extraction

# Via FTP:
# - Use FileZilla or similar
# - More reliable for large transfers
# - Can resume interrupted transfers
```

**Prevention**:
- Use FTP for large file uploads
- Compress files before uploading
- Upload during off-peak hours

---

### .htaccess Restrictions

**Issue**: Some .htaccess directives not allowed

**Details**:
- GoDaddy restricts certain Apache directives
- Some rewrite rules may not work
- Security-related directives may be blocked

**Solution**:

```apache
# Test .htaccess changes locally first

# If directive doesn't work:
# 1. Check GoDaddy documentation for allowed directives
# 2. Use alternative approach
# 3. Contact GoDaddy support for workaround

# Common safe directives:
# - RewriteEngine On
# - RewriteCond
# - RewriteRule
# - Redirect directives

# May not work:
# - Some security headers
# - Some caching directives
# - Server-level configurations
```

**Prevention**:
- Test .htaccess changes on staging first
- Keep backup of working .htaccess
- Document which directives work

---

## Debugging Quirks

### Error Logging

**Issue**: WordPress debug.log may not be accessible

**Details**:
- debug.log in wp-content/ may be disabled
- Error logs may be in different location
- May need to enable WP_DEBUG via wp-config.php

**Solution**:

```php
// Enable debugging in wp-config.php:
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);

// Log file location:
// /wp-content/debug.log

// View via File Manager:
// Navigate to wp-content/debug.log
// View or download

// Clear log:
// Delete debug.log file (will be recreated)
```

**Prevention**:
- Enable WP_DEBUG_LOG on site setup
- Check logs regularly
- Disable WP_DEBUG_DISPLAY on production (security)

---

### PHP Version Management

**Issue**: PHP version updates may break plugins

**Details**:
- GoDaddy periodically updates PHP versions
- May notify before update, may not
- Old plugins may not support newer PHP
- Can't control exact PHP version

**Solution**:

```bash
# Check current PHP version:
# Via WordPress: Site Health → Info → Server

# Via SSH (if available):
php -v

# If issues after PHP update:
# 1. Check plugin/theme compatibility
# 2. Update plugins/themes
# 3. Test on Local with same PHP version first
# 4. Contact GoDaddy to rollback PHP version (temporary)
```

**Prevention**:
- Monitor PHP compatibility of plugins
- Test with newer PHP versions locally
- Update plugins/themes regularly
- Maintain compatibility matrix

---

## Quick Reference: Common GoDaddy Issues

| Issue | Cause | Quick Fix |
|-------|-------|-----------|
| 403 Error on uploaded file | Permission 600 | Change to 644 |
| Changes not showing | Cache not cleared | Clear all cache levels |
| Database import fails | Wrong table prefix | Use `wp_7e1ce15f22_` |
| File upload fails | Timeout or size limit | Use FTP, smaller chunks |
| Email not sending | wp_mail() unreliable | Use SMTP plugin |
| SSL warning | Certificate renewing | Wait 10-15 minutes |
| Plugin won't install | Restricted by GoDaddy | Check approved list |
| Session timeout | phpMyAdmin limit | Split into smaller operations |

---

## Essential GoDaddy Information

### RunDaveRun Site Details

**Hosting**: GoDaddy Managed WordPress
**Site**: https://rundaverun.org
**Database Prefix**: `wp_7e1ce15f22_`
**WordPress Version**: 6.3.2
**PHP Version**: 8.1

### GoDaddy Control Panel Access

**Dashboard**: https://account.godaddy.com
**Managed WordPress**: My Products → Managed WordPress
**File Manager**: Managed WordPress → Settings → File Manager
**phpMyAdmin**: Managed WordPress → Settings → phpMyAdmin
**SSH/SFTP**: Managed WordPress → Settings → SSH/SFTP

### Support Resources

**GoDaddy Support**:
- Phone: (included in plan)
- Chat: Via dashboard
- Tickets: Via dashboard

**Documentation**:
- GoDaddy WordPress Help: https://www.godaddy.com/help/wordpress
- Managed WordPress Limits: Check plan documentation

---

## Integration with Other Protocols

### With WordPress Maintenance Protocol
Reference: `/home/dave/skippy/conversations/wordpress_maintenance_protocol.md`
- All GoDaddy-specific quirks noted
- Workarounds documented
- Alternative procedures provided

### With Deployment Checklist Protocol
Reference: `/home/dave/skippy/conversations/deployment_checklist_protocol.md`
- GoDaddy-specific verification steps
- Cache clearing procedures
- Permission checks

### With Debugging Workflow Protocol
Reference: `/home/dave/skippy/conversations/debugging_workflow_protocol.md`
- GoDaddy-specific debugging steps
- Log file locations
- Support escalation path

---

**This document is part of the persistent memory system.**
**Reference when working with GoDaddy Managed WordPress hosting.**
