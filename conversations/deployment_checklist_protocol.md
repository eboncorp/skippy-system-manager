# Deployment Checklist Protocol

**Date Created**: 2025-10-28
**Purpose**: Step-by-step deployment procedures with verification
**Applies To**: All deployments (WordPress, scripts, packages)
**Priority**: HIGH (prevents deployment failures)

## Purpose

This protocol provides:
- Comprehensive pre-deployment checklists
- Deployment verification procedures
- Post-deployment testing workflows
- Rollback procedures for failed deployments
- Type-specific checklists for WordPress, scripts, and packages

---

## Overview

This protocol provides comprehensive checklists for deploying changes from local/development to staging/production environments. Following these steps prevents common deployment issues and ensures rollback capability.

## Deployment Types

### 1. WordPress Site Deployment
### 2. Script Deployment
### 3. Package/Release Deployment
### 4. Configuration Changes
### 5. Emergency/Hotfix Deployment

---

## WordPress Site Deployment Checklist

### PRE-DEPLOYMENT (Local Environment)

#### Development Complete
- [ ] All changes completed locally
- [ ] Code reviewed and tested
- [ ] No debug code left in (console.log, var_dump, etc.)
- [ ] No hardcoded credentials
- [ ] No commented-out code blocks (clean up)

#### Local Testing
- [ ] Homepage loads correctly
- [ ] All new/modified pages accessible
- [ ] Forms submit correctly
- [ ] Images display properly
- [ ] Links work (no 404s)
- [ ] Menu navigation works
- [ ] Search functionality works (if applicable)
- [ ] User registration/login works (if applicable)

#### Browser Testing (Local)
- [ ] Chrome Desktop - Pass
- [ ] Firefox Desktop - Pass
- [ ] Safari Desktop - Pass (if available)
- [ ] Chrome Mobile (DevTools) - Pass
- [ ] Actual mobile device - Pass (if possible)

#### Mobile Specific
- [ ] Mobile menu opens/closes
- [ ] Touch targets adequate (44x44px min)
- [ ] Text readable (16px min)
- [ ] No horizontal scrolling
- [ ] Images scale properly
- [ ] Forms usable on mobile

#### Performance Check
- [ ] Page load time < 3 seconds
- [ ] No slow database queries
- [ ] Images optimized
- [ ] No JavaScript errors in console
- [ ] No excessive HTTP requests

#### Backup Creation
```bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/dave/rundaverun/backups/pre_deploy_$DATE"

# Local backup
mkdir -p "$BACKUP_DIR/local"
wp db export "$BACKUP_DIR/local/database.sql" --allow-root
cp -r "/home/dave/Local Sites/rundaverun-local/app/public/wp-content" "$BACKUP_DIR/local/"

# Production backup (download first if not done)
mkdir -p "$BACKUP_DIR/production"
# Download via phpMyAdmin or WP-CLI
# Download files via FTP/File Manager
```
- [ ] Local database backed up
- [ ] Local files backed up
- [ ] Production database backed up
- [ ] Production files backed up
- [ ] Backup verification (files not empty)
- [ ] Backup location documented: `/home/dave/rundaverun/backups/pre_deploy_YYYYMMDD_HHMMSS`

#### Git Preparation
- [ ] All changes committed to git
- [ ] Commit message descriptive and follows format
- [ ] Branch up to date with main (if using branches)
- [ ] No merge conflicts
- [ ] Git push completed successfully
- [ ] GitHub Actions passing (if configured)

---

### DEPLOYMENT (Production Environment)

#### Maintenance Mode
```bash
# Enable maintenance mode (if WP-CLI available)
wp maintenance-mode activate --allow-root

# Or create .maintenance file manually
echo '<?php $upgrading = time(); ?>' > .maintenance
```
- [ ] Maintenance mode enabled
- [ ] Maintenance page displays correctly
- [ ] Timestamp recorded: `_____________`

#### Deployment Method Selection
Choose one:
- [ ] **Method A**: GitHub Actions (automated)
- [ ] **Method B**: Manual FTP/File Manager upload
- [ ] **Method C**: WP-CLI (if SSH available)
- [ ] **Method D**: GoDaddy Hosting Panel

#### Method A: GitHub Actions (Automated)
- [ ] Code pushed to GitHub
- [ ] GitHub Actions workflow triggered
- [ ] Workflow running (check Actions tab)
- [ ] Workflow completed successfully
- [ ] No error messages in logs
- [ ] Files deployed to production

#### Method B: Manual Upload (FTP/File Manager)
- [ ] Connect to production server
- [ ] Navigate to correct directory
- [ ] Upload modified files only (not entire site)
- [ ] Verify file upload completion
- [ ] Set correct permissions (644 files, 755 directories)
```bash
# Files to upload typically:
# - Theme files: wp-content/themes/
# - Plugin files: wp-content/plugins/
# - Uploads: wp-content/uploads/ (if new media)
# - Custom files: wp-content/uploads/glossary_v4.html, etc.
```

#### Database Changes (if applicable)
```bash
# If database changes needed:
# 1. Enable maintenance mode
# 2. Backup production database
# 3. Import new database OR run UPDATE queries
# 4. Update URLs if needed
wp search-replace 'http://rundaverun-local.local' 'https://rundaverun.org' --all-tables --allow-root

# 5. Verify database
wp db check --allow-root
```
- [ ] Production database backed up (pre-import)
- [ ] Database import completed (if full import)
- [ ] OR SQL queries executed (if incremental)
- [ ] URLs updated (local → production)
- [ ] Database check passed
- [ ] No SQL errors

#### File Permissions Check
```bash
# Verify permissions on production
# Files: 644
# Directories: 755
```
- [ ] Uploaded files have correct permissions (644)
- [ ] Directories have correct permissions (755)
- [ ] No files with 600 permissions (blocks web access)

#### Clear Caches
```bash
# WordPress cache
wp cache flush --allow-root

# Server cache (if available)
# GoDaddy: Use hosting panel to clear cache

# Browser cache
# Hard refresh: Ctrl+Shift+R
```
- [ ] WordPress cache cleared
- [ ] Server cache cleared (if applicable)
- [ ] CDN cache purged (if using CDN)

---

### POST-DEPLOYMENT (Verification)

#### Critical Path Testing
- [ ] Homepage loads (https://rundaverun.org)
- [ ] No 500/404 errors
- [ ] Database connection working
- [ ] Admin panel accessible (/wp-admin)

#### Content Verification
- [ ] New/modified pages display correctly
- [ ] Policy documents accessible
- [ ] Glossary loads and works
- [ ] Voter Education hub accessible
- [ ] About page content correct
- [ ] Contact form works
- [ ] Images display properly
- [ ] All menus work

#### Functionality Testing
- [ ] Forms submit correctly
- [ ] User login works (if applicable)
- [ ] Search works (if applicable)
- [ ] Comments work (if enabled)
- [ ] Share buttons work (if applicable)

#### Mobile Testing (Production)
- [ ] Mobile menu works
- [ ] Mobile layout correct
- [ ] Touch interactions work
- [ ] No horizontal scrolling
- [ ] Images scale properly

#### Browser Testing (Production)
- [ ] Chrome Desktop - Pass
- [ ] Firefox Desktop - Pass
- [ ] Safari Desktop - Pass (if available)
- [ ] Chrome Mobile - Pass
- [ ] Actual mobile device - Pass

#### Performance Check (Production)
- [ ] Page load time acceptable (< 3 sec)
- [ ] No JavaScript errors (check console)
- [ ] No broken links (check network tab)
- [ ] Images loading correctly
- [ ] CSS loading correctly

#### SEO/Analytics Check
- [ ] Meta tags correct
- [ ] Title tags correct
- [ ] Analytics tracking working (if configured)
- [ ] Sitemap accessible (if configured)
- [ ] Robots.txt correct (if configured)

#### Security Check
- [ ] HTTPS working (SSL certificate valid)
- [ ] No mixed content warnings
- [ ] Admin panel secured
- [ ] File permissions correct
- [ ] No debug output visible

#### Disable Maintenance Mode
```bash
wp maintenance-mode deactivate --allow-root

# Or delete .maintenance file
rm .maintenance
```
- [ ] Maintenance mode disabled
- [ ] Site accessible to public
- [ ] No maintenance message showing

---

### POST-DEPLOYMENT (Monitoring)

#### Immediate Monitoring (First 30 minutes)
- [ ] Monitor error logs for new errors
- [ ] Check analytics for traffic (if configured)
- [ ] Monitor form submissions
- [ ] Check for user-reported issues
- [ ] Test critical user paths

#### 24-Hour Monitoring
- [ ] Check error logs daily
- [ ] Monitor page load times
- [ ] Monitor uptime
- [ ] Check for 404 errors
- [ ] Review user feedback/issues

#### Documentation
- [ ] Deployment timestamp: `_____________`
- [ ] Deployed by: `_____________`
- [ ] Changes deployed: `_____________`
- [ ] Issues encountered: `_____________`
- [ ] Solutions applied: `_____________`
- [ ] Backup location: `_____________`

---

## ROLLBACK PROCEDURE

### When to Rollback
- Critical errors preventing site function
- Data loss or corruption
- Security vulnerability introduced
- Performance severely degraded
- User-facing errors affecting all visitors

### Rollback Steps

#### 1. Enable Maintenance Mode
```bash
wp maintenance-mode activate --allow-root
# Or create .maintenance file
```
- [ ] Maintenance mode enabled

#### 2. Restore Database
```bash
# Import backup database
wp db reset --yes --allow-root
wp db import /path/to/backup/production/database.sql --allow-root
wp db check --allow-root
```
- [ ] Production database reset
- [ ] Backup database imported
- [ ] Database check passed
- [ ] No import errors

#### 3. Restore Files
```bash
# Restore from backup
# Via FTP/File Manager: Upload backup files
# Or via command line if available:
cp -r /backup/path/wp-content/* /production/path/wp-content/
```
- [ ] Files restored from backup
- [ ] Permissions verified (644/755)
- [ ] Critical files present

#### 4. Clear Caches
- [ ] WordPress cache cleared
- [ ] Server cache cleared
- [ ] CDN cache purged

#### 5. Verify Rollback
- [ ] Site loads correctly
- [ ] Database connection working
- [ ] No errors in logs
- [ ] Critical functionality working

#### 6. Disable Maintenance Mode
- [ ] Maintenance mode disabled
- [ ] Site accessible

#### 7. Document Rollback
- [ ] Rollback timestamp: `_____________`
- [ ] Reason for rollback: `_____________`
- [ ] What failed: `_____________`
- [ ] Backup restored from: `_____________`
- [ ] Site verified working: Yes / No

---

## Script Deployment Checklist

### Pre-Deployment
- [ ] Script tested locally
- [ ] Version number incremented
- [ ] Documentation header complete
- [ ] Error handling included
- [ ] Backup of previous version created
- [ ] Git commit created

### Deployment
- [ ] Script copied to `/home/dave/skippy/scripts/[category]/`
- [ ] Executable permissions set (chmod +x)
- [ ] Previous version backed up (if updating)
- [ ] Script location documented

### Post-Deployment
- [ ] Test run successful
- [ ] No errors in execution
- [ ] Output as expected
- [ ] Dependencies available

---

## Package/Release Deployment Checklist

### Pre-Deployment
- [ ] All files included
- [ ] Documentation complete (README, guides)
- [ ] Version number correct
- [ ] Archive created (.zip or .tar.gz)
- [ ] Checksums generated (if needed)
- [ ] Testing completed

### Deployment
- [ ] Uploaded to distribution location
- [ ] Permissions correct
- [ ] Download link works
- [ ] Archive extracts correctly

### Post-Deployment
- [ ] Documentation accessible
- [ ] No corrupted files
- [ ] Version tagged in git (if applicable)
- [ ] Release notes published

---

## Emergency/Hotfix Deployment

### When to Use Emergency Deployment
- Critical security vulnerability
- Site completely down
- Data loss in progress
- Legal/compliance issue

### Emergency Procedure

**SPEED + SAFETY BALANCE**

#### Minimal Checklist (5 minutes)
- [ ] Backup production (quick snapshot)
- [ ] Fix implemented locally
- [ ] Fix tested (basic test only)
- [ ] Deploy fix
- [ ] Verify site working
- [ ] Monitor for 10 minutes

#### Full Checklist Later
- [ ] Complete testing when site stable
- [ ] Proper backup created
- [ ] Documentation updated
- [ ] Incident report created
- [ ] Post-mortem scheduled

---

## Integration with Other Protocols

### With WordPress Protocol
Reference: `/home/dave/skippy/conversations/wordpress_maintenance_protocol.md`
- Use WordPress-specific procedures
- Follow WP-CLI commands
- Check GoDaddy quirks

### With Backup Protocol
Reference: `/home/dave/skippy/conversations/backup_strategy_protocol.md`
- Create backups before deployment
- Verify backup integrity
- Document backup locations

### With Git Protocol
Reference: `/home/dave/skippy/conversations/git_workflow_protocol.md`
- Follow commit message standards
- Create deployment tag
- Document in commit

### With Error Logging
Reference: `/home/dave/skippy/conversations/error_logging_protocol.md`
- Log deployment issues
- Document solutions
- Track rollbacks

---

## Quick Reference

### Pre-Deployment Summary
1. ✅ Development complete & tested locally
2. ✅ Backups created (local + production)
3. ✅ Git committed & pushed
4. ✅ Browser/mobile testing complete
5. ✅ Performance acceptable

### Deployment Summary
1. ✅ Maintenance mode ON
2. ✅ Deploy files/database
3. ✅ Verify permissions
4. ✅ Clear caches
5. ✅ Maintenance mode OFF

### Post-Deployment Summary
1. ✅ Critical paths working
2. ✅ Browser/mobile testing
3. ✅ Performance check
4. ✅ Monitor for issues
5. ✅ Document deployment

### Rollback Summary
1. ✅ Maintenance mode ON
2. ✅ Restore database
3. ✅ Restore files
4. ✅ Clear caches
5. ✅ Verify working
6. ✅ Maintenance mode OFF
7. ✅ Document rollback

---

## Quick Reference Card

### Pre-Flight Checklist (5 minutes)
```
☐ Backup created and verified
☐ Maintenance mode ON
☐ Changes tested locally
☐ No debug code present
☐ Rollback plan ready
```

### Deployment Commands (WordPress)
```bash
# 1. Backup
wp db export backup_$(date +%Y%m%d_%H%M%S).sql
tar -czf files_backup_$(date +%Y%m%d_%H%M%S).tar.gz wp-content/

# 2. Maintenance mode
wp maintenance-mode activate

# 3. Deploy changes
# (upload files via FTP/SFTP or use deployment script)

# 4. Clear caches
wp cache flush
wp rewrite flush

# 5. Verify
wp post list --post_type=page --fields=post_title,post_status
wp plugin list --status=active

# 6. Disable maintenance
wp maintenance-mode deactivate
```

### Critical Paths to Test
1. Homepage - `https://yourdomain.com/`
2. Forms - Test all submission forms
3. Key landing pages - Policy pages, volunteer registration
4. Admin - Can login and access admin panel
5. Mobile - Responsive layout works

### Emergency Rollback (2 minutes)
```bash
# If deployment fails:
wp maintenance-mode activate
wp db import backup_[timestamp].sql
# Restore files from backup
tar -xzf files_backup_[timestamp].tar.gz
wp cache flush
wp maintenance-mode deactivate
```

### Support Contacts
- **Hosting:** GoDaddy Support
- **DNS:** Domain registrar
- **Backup:** Check `/home/dave/skippy/backups/`
- **Logs:** `/home/dave/skippy/logs/`

---

**This protocol is part of the persistent memory system.**
**Reference before any deployment operation.**
**Version:** 1.1.0 (Added quick reference 2025-11-05)
