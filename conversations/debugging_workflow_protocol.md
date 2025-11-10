# Debugging Workflow Protocol

**Date Created**: 2025-10-28
**Purpose**: Systematic debugging methodology and troubleshooting procedures
**Applies To**: All debugging tasks (WordPress, scripts, system issues)
**Priority**: HIGH (occurs 2-3 times per week)

## Overview

This protocol provides a systematic approach to debugging issues rather than trial-and-error. Following this workflow reduces debugging time and ensures problems are properly documented for future reference.

## Core Debugging Principles

### 1. Systematic Approach
✅ **DO**: Work methodically through diagnosis steps
✅ **DO**: Document each attempt and result
✅ **DO**: Test one variable at a time
❌ **DON'T**: Try random fixes hoping something works
❌ **DON'T**: Skip documentation
❌ **DON'T**: Change multiple things simultaneously

### 2. Understand Before Fixing
✅ **DO**: Identify root cause before applying fixes
✅ **DO**: Reproduce the issue consistently
✅ **DO**: Understand what changed to cause the issue
❌ **DON'T**: Apply fixes without understanding why they work
❌ **DON'T**: Implement workarounds without investigating cause

### 3. Documentation
✅ **DO**: Log all errors encountered
✅ **DO**: Document solutions that work
✅ **DO**: Update protocols with prevention measures
❌ **DON'T**: Forget to document once problem is solved

---

## Debugging Workflow (5-Step Process)

### Step 1: Problem Identification

#### Gather Information
```bash
# Ask these questions:
1. What is the expected behavior?
2. What is the actual behavior?
3. When did it start failing?
4. What changed recently?
5. Can you reproduce it consistently?
6. Does it fail for everyone or specific users/conditions?
```

#### Document Initial State
- [ ] Error message captured (exact text)
- [ ] Screenshots taken (if UI issue)
- [ ] Reproduction steps documented
- [ ] Environment details noted (local/production, OS, browser, etc.)
- [ ] Recent changes identified

#### Create Error Log
Reference: `/home/dave/skippy/conversations/error_logging_protocol.md`

```bash
# Create error log immediately
ERROR_DATE=$(date +%Y-%m-%d_%H%M)
ERROR_FILE="/home/dave/skippy/conversations/error_logs/2025-10/error_${ERROR_DATE}_[brief_description].md"

# Document:
# - What you were trying to do
# - What went wrong
# - Error messages
# - Environment details
```

---

### Step 2: Information Gathering

#### Check Logs
```bash
# WordPress error logs
tail -100 /home/dave/Local\ Sites/rundaverun-local/app/public/wp-content/debug.log

# System logs
journalctl -xe --since "10 minutes ago"

# Apache/nginx logs (if applicable)
tail -100 /var/log/apache2/error.log

# Application logs (if applicable)
tail -100 /path/to/app/logs/error.log
```

#### Check System State
```bash
# Disk space
df -h

# Memory usage
free -h

# Process status
ps aux | grep [relevant_process]

# Service status
systemctl status [service_name]
```

#### Browser DevTools (For Web Issues)
- [ ] Console errors checked (F12 → Console)
- [ ] Network tab checked (failed requests, 404s, 500s)
- [ ] Response codes noted
- [ ] Request/response headers examined
- [ ] JavaScript errors identified

#### WordPress-Specific Checks
```bash
cd "/home/dave/Local Sites/rundaverun-local/app/public"

# Check WordPress status
wp core verify-checksums --allow-root
wp plugin list --allow-root
wp theme list --allow-root

# Check database connection
wp db check --allow-root

# Check for errors in database
wp db query "SELECT * FROM wp_7e1ce15f22_options WHERE option_name = 'siteurl'" --allow-root
```

---

### Step 3: Hypothesis Formation

#### Identify Possible Causes
Based on information gathered, list potential causes in priority order:

**1. Most Likely Cause**: [Based on error message and recent changes]
**2. Second Most Likely**: [Based on similar past issues]
**3. Third Most Likely**: [Based on environmental factors]

#### Create Test Plan
For each hypothesis, define:
- What to test
- How to test it
- Expected result if hypothesis is correct
- How to verify fix worked

**Example**:
```markdown
**Hypothesis 1**: File permissions preventing WordPress from writing
**Test**: Check permissions on wp-content/uploads/
**Expected**: Directory should be 755, files should be 644
**Verification**: Upload test image through WordPress admin
```

---

### Step 4: Testing & Validation

#### Test One Variable at a Time

**❌ WRONG APPROACH**:
```bash
# Changing multiple things at once
chmod -R 777 wp-content/
wp cache flush --allow-root
wp plugin deactivate --all --allow-root
# Now you don't know what fixed it!
```

**✅ CORRECT APPROACH**:
```bash
# Test 1: Check current permissions
ls -la wp-content/uploads/

# Test 2: Fix permissions if needed
chmod 755 wp-content/uploads/

# Test 3: Verify fix
# Try upload again

# If still failing, move to next hypothesis
```

#### Document Each Attempt
```markdown
**Attempt 1**: Changed wp-content/uploads/ permissions to 755
**Result**: Still failing
**Error**: Same error message
**Next Step**: Check if uploads directory exists
```

#### Verification Checklist
- [ ] Issue is resolved
- [ ] No new issues introduced
- [ ] Solution works consistently (test 3+ times)
- [ ] Solution works in all affected environments
- [ ] Root cause identified and understood

---

### Step 5: Documentation & Prevention

#### Update Error Log
```markdown
## Solution
Changed file permissions on wp-content/uploads/ from 600 to 755.

## Root Cause
GoDaddy file upload through cPanel set incorrect permissions (600 instead of 644).

## Prevention
- Always check permissions after cPanel file uploads
- Use deployment script that sets correct permissions
- Add permission check to deployment checklist
```

#### Update Relevant Protocols
If this issue reveals a gap in existing protocols:
- Update deployment checklist
- Add to common errors guide
- Create prevention measure
- Update quick reference docs

#### Create Prevention Measures
```bash
# Example: Add permission check to deployment script
echo "Checking file permissions..."
find wp-content -type f -not -perm 644 -exec chmod 644 {} \;
find wp-content -type d -not -perm 755 -exec chmod 755 {} \;
echo "✅ Permissions fixed"
```

---

## Problem Category Decision Trees

### Category 1: WordPress Database Issues

```
Issue: WordPress database error
├─ Can't connect to database?
│  ├─ YES → Check wp-config.php credentials
│  │       Check database service running
│  │       Check database host (localhost vs 127.0.0.1)
│  └─ NO → Continue
│
├─ Wrong table prefix?
│  ├─ YES → Check wp-config.php $table_prefix
│  │       Local uses: wp_
│  │       Production uses: wp_7e1ce15f22_
│  └─ NO → Continue
│
├─ Database corruption?
│  ├─ YES → wp db check --allow-root
│  │       wp db repair --allow-root
│  └─ NO → Continue
│
└─ Wrong URLs in database?
   └─ YES → wp search-replace 'old-url' 'new-url' --all-tables --allow-root
```

### Category 2: File Permission Issues

```
Issue: File permission error (typically "Permission denied")
├─ WordPress can't write files?
│  ├─ YES → Check wp-content/uploads/ permissions
│  │       Should be: directories 755, files 644
│  │       Fix: chmod 755 [dir] && chmod 644 [files]
│  └─ NO → Continue
│
├─ Files uploaded but not accessible (403)?
│  ├─ YES → Permissions too restrictive (600)
│  │       Change to 644 for files, 755 for directories
│  └─ NO → Continue
│
└─ Script not executable?
   └─ YES → chmod +x [script_name]
```

### Category 3: WordPress Plugin/Theme Issues

```
Issue: WordPress site broken or white screen
├─ Recent plugin/theme activation?
│  ├─ YES → Deactivate via WP-CLI:
│  │       wp plugin deactivate [plugin-name] --allow-root
│  │       OR rename plugin directory via File Manager
│  └─ NO → Continue
│
├─ PHP errors in debug.log?
│  ├─ YES → Check wp-content/debug.log
│  │       Look for fatal errors
│  │       Identify failing plugin/theme
│  └─ NO → Continue
│
└─ Memory limit exceeded?
   └─ YES → Increase memory_limit in wp-config.php:
           define('WP_MEMORY_LIMIT', '256M');
```

### Category 4: Deployment Issues

```
Issue: Deployment failed or site broken after deployment
├─ Files not uploaded?
│  ├─ YES → Check FTP/File Manager connection
│  │       Verify upload completed (file sizes match)
│  └─ NO → Continue
│
├─ Database not imported?
│  ├─ YES → Check database import success
│  │       Verify table count matches
│  │       Check for SQL errors
│  └─ NO → Continue
│
├─ Cache causing old content?
│  ├─ YES → Clear all caches:
│  │       wp cache flush --allow-root
│  │       Clear server cache (GoDaddy hosting panel)
│  │       Hard refresh browser (Ctrl+Shift+R)
│  └─ NO → Continue
│
└─ URLs pointing to local?
   └─ YES → Run search-replace:
           wp search-replace 'http://rundaverun-local.local' 'https://rundaverun.org' --all-tables --allow-root
```

### Category 5: Mobile Issues

```
Issue: Mobile layout broken or features not working
├─ Mobile menu not working?
│  ├─ YES → Check JavaScript console for errors
│  │       Verify mobile-menu-injector.php is active
│  │       Check z-index conflicts
│  └─ NO → Continue
│
├─ Layout broken on mobile?
│  ├─ YES → Check CSS media queries
│  │       Verify viewport meta tag exists
│  │       Test in DevTools mobile view
│  └─ NO → Continue
│
└─ Touch interactions not working?
   └─ YES → Check touch event handlers
           Verify no hover-only interactions
           Test on actual device (not just DevTools)
```

---

## Tool Selection Guide

### When to Use Each Tool

#### WP-CLI (WordPress Command Line)
**Use For**:
- Database operations (export, import, search-replace)
- Plugin/theme management
- Post/page management
- Cache clearing
- Verification commands

**Example Commands**:
```bash
# Most used
wp db export backup.sql --allow-root
wp search-replace 'old' 'new' --all-tables --allow-root
wp plugin list --allow-root
wp cache flush --allow-root
wp post list --allow-root
```

#### Browser DevTools (F12)
**Use For**:
- JavaScript errors
- Network request failures (404, 500)
- CSS issues
- AJAX debugging
- Performance profiling

**Key Tabs**:
- **Console**: JavaScript errors
- **Network**: HTTP requests/responses
- **Elements**: HTML/CSS inspection
- **Application**: Cookies, localStorage

#### curl (HTTP Testing)
**Use For**:
- Testing API endpoints
- Checking HTTP response codes
- Testing redirects
- Header inspection
- Authentication testing

**Example Commands**:
```bash
# Check if URL is accessible
curl -I https://rundaverun.org

# Test API endpoint
curl -X POST https://rundaverun.org/wp-json/wp/v2/posts \
  -u username:application_password \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","status":"draft"}'

# Follow redirects
curl -L https://rundaverun.org/old-page

# Check response time
curl -w "@curl-format.txt" -o /dev/null -s https://rundaverun.org
```

#### grep/ripgrep (Code Search)
**Use For**:
- Finding where function/variable is used
- Searching error messages in logs
- Finding configuration settings
- Locating TODO comments

**Example Commands**:
```bash
# Find function usage
grep -r "function_name" /path/to/code/

# Search logs for errors
grep -i "error" /var/log/apache2/error.log

# Find WordPress shortcode usage
grep -r "\[glossary_link\]" wp-content/
```

#### Git (Version Control Investigation)
**Use For**:
- Finding when bug was introduced
- Seeing what changed recently
- Comparing working vs broken versions
- Reverting problematic commits

**Example Commands**:
```bash
# See recent changes
git log --oneline -10

# See what changed in specific file
git log -p -- path/to/file.php

# Find when string was added/removed
git log -S "search_string"

# Compare current vs previous
git diff HEAD~1 HEAD
```

#### System Tools
**Use For**:
- Process debugging (ps, top, htop)
- Network debugging (ping, curl, dig, netstat)
- File debugging (ls, find, stat)
- Permission issues (chmod, chown)

---

## Common Problem Patterns

### Pattern 1: "It worked locally but not in production"

**Likely Causes**:
1. Database URLs not updated (local URLs in production)
2. File permissions different (600 in production vs 644 local)
3. Plugin/theme files not uploaded
4. Cache showing old version
5. PHP version differences

**Investigation Steps**:
```bash
# 1. Check URLs in database
wp db query "SELECT option_value FROM wp_7e1ce15f22_options WHERE option_name IN ('siteurl', 'home')" --allow-root

# 2. Check file permissions
ls -la wp-content/themes/[theme-name]/

# 3. Verify files exist
ls -la wp-content/uploads/[new-files]

# 4. Clear all caches
wp cache flush --allow-root

# 5. Check PHP version
php -v
```

### Pattern 2: "It worked yesterday but broke today"

**Investigation Steps**:
```bash
# 1. What changed? Check git
git log --since="yesterday" --oneline

# 2. Were plugins/themes updated?
wp plugin list --allow-root
# Check for recent update timestamps

# 3. Check error logs for new errors
tail -50 wp-content/debug.log

# 4. Check if hosting made changes
# Review GoDaddy notifications/emails

# 5. Check if SSL certificate expired
curl -I https://rundaverun.org
```

### Pattern 3: "Works in Chrome but not Firefox/Safari"

**Investigation Steps**:
1. Open DevTools in failing browser (F12)
2. Check Console for JavaScript errors
3. Check Network tab for failed requests
4. Check CSS compatibility (prefixes, newer features)
5. Test in private/incognito mode (cache issue?)

**Common Causes**:
- Browser-specific CSS issues
- JavaScript features not supported
- Cookie/localStorage differences
- Cache showing old version

### Pattern 4: "Mobile menu not working"

**Investigation Steps**:
```bash
# 1. Check if injector file exists
ls -la wp-content/mu-plugins/mobile-menu-injector.php

# 2. Check file permissions
ls -la wp-content/mu-plugins/mobile-menu-injector.php
# Should be 644

# 3. Test JavaScript
# Open mobile DevTools (F12 → Toggle device toolbar)
# Check Console for errors

# 4. Check z-index conflicts
# Inspect menu element
# Verify z-index is high enough (e.g., 9999)

# 5. Test on actual mobile device
# Not just DevTools simulation
```

### Pattern 5: "Database import failed"

**Investigation Steps**:
```bash
# 1. Check database file exists and is not empty
ls -lh backup.sql

# 2. Check for SQL syntax errors
head -20 backup.sql
# Look for proper SQL syntax

# 3. Try importing with error output
wp db import backup.sql --allow-root 2>&1 | tee import_errors.log

# 4. Check database connection
wp db check --allow-root

# 5. Verify table prefix matches
# In backup.sql, tables should start with: wp_7e1ce15f22_
# Check wp-config.php: $table_prefix = 'wp_7e1ce15f22_';
```

---

## Quick Fixes Reference

### WordPress Quick Fixes

#### Reset Permalinks
```bash
wp rewrite flush --allow-root
```

#### Clear All Caches
```bash
wp cache flush --allow-root
# Also clear server cache (GoDaddy panel)
# Hard refresh browser: Ctrl+Shift+R
```

#### Deactivate All Plugins
```bash
wp plugin deactivate --all --allow-root
```

#### Switch to Default Theme
```bash
wp theme activate twentytwentythree --allow-root
```

#### Regenerate wp-config.php Salts
```bash
wp config shuffle-salts --allow-root
```

#### Verify Core Files
```bash
wp core verify-checksums --allow-root
```

### File Permission Quick Fixes

#### Fix WordPress Permissions
```bash
# Files: 644
# Directories: 755
cd "/home/dave/Local Sites/rundaverun-local/app/public"
find wp-content -type d -exec chmod 755 {} \;
find wp-content -type f -exec chmod 644 {} \;
```

#### Fix Script Permissions
```bash
chmod +x /home/dave/skippy/scripts/[category]/script_name.sh
```

### Git Quick Fixes

#### Undo Last Commit (Keep Changes)
```bash
git reset --soft HEAD~1
```

#### Discard Local Changes
```bash
git checkout -- [file_name]
```

#### View File from Previous Commit
```bash
git show HEAD~1:path/to/file.php
```

### Database Quick Fixes

#### Fix Wrong URLs
```bash
wp search-replace 'http://rundaverun-local.local' 'https://rundaverun.org' --all-tables --allow-root
```

#### Repair Database
```bash
wp db repair --allow-root
```

#### Optimize Database
```bash
wp db optimize --allow-root
```

---

## Prevention Checklist

After resolving any issue, ask:

### Was This Preventable?
- [ ] Could pre-deployment testing have caught this?
- [ ] Should this be added to deployment checklist?
- [ ] Does this reveal a gap in our protocols?
- [ ] Should we create automated check for this?

### Documentation Updates Needed?
- [ ] Add to common errors guide
- [ ] Update relevant protocol file
- [ ] Create quick reference card
- [ ] Update deployment checklist

### Process Improvements?
- [ ] Should we create a script to prevent this?
- [ ] Should we add this to automated testing?
- [ ] Should we monitor for this condition?
- [ ] Should we create an alert for this?

### Knowledge Sharing
- [ ] Document in error log
- [ ] Update troubleshooting guide
- [ ] Add to protocol references
- [ ] Create example for future reference

---

## Debugging Templates

### Error Log Template
```markdown
# Error Log: [Brief Description]

**Date**: 2025-10-28 14:30
**Task**: [What you were trying to do]
**Severity**: [Critical/High/Medium/Low]

## Error Details

### Error Message
```
[Exact error message]
```

### Environment
- **Location**: Local / Production
- **OS**: Linux/Windows/Mac
- **Browser**: Chrome 118 / Firefox 119 / etc.
- **WordPress Version**: 6.3.2
- **PHP Version**: 8.1

### Reproduction Steps
1. Step 1
2. Step 2
3. Step 3
4. Error occurs

## Investigation

### Hypothesis 1: [Most Likely Cause]
**Test**: [What was tested]
**Result**: [Pass/Fail]
**Conclusion**: [What this tells us]

### Hypothesis 2: [Second Most Likely]
**Test**: [What was tested]
**Result**: [Pass/Fail]
**Conclusion**: [What this tells us]

## Solution

### What Fixed It
[Detailed explanation of solution]

### Root Cause
[Why the problem occurred]

### Prevention
[How to prevent this in the future]

## References
- Protocol: `/home/dave/skippy/conversations/[relevant_protocol].md`
- Similar Issue: `error_logs/2025-09/error_2025-09-15_1200_similar.md`
```

### Investigation Checklist Template
```markdown
## Investigation Checklist: [Issue Description]

### Information Gathering
- [ ] Error message captured
- [ ] Screenshots taken
- [ ] Reproduction steps documented
- [ ] Environment details noted
- [ ] Recent changes identified

### Log Review
- [ ] Application logs checked
- [ ] System logs checked
- [ ] Browser console checked
- [ ] Network requests checked
- [ ] Database logs checked (if applicable)

### System State
- [ ] Disk space checked
- [ ] Memory usage checked
- [ ] Service status checked
- [ ] File permissions checked
- [ ] Network connectivity checked

### Testing
- [ ] Issue reproduced consistently
- [ ] Test in different environment
- [ ] Test with minimal configuration
- [ ] Test with different user/browser
- [ ] Root cause identified

### Solution
- [ ] Fix implemented
- [ ] Fix tested and verified
- [ ] No new issues introduced
- [ ] Works in all environments
- [ ] Documentation updated
```

---

## Integration with Other Protocols

### With Error Logging Protocol
Reference: `/home/dave/skippy/conversations/error_logging_protocol.md`
- Create error log for every debugging session
- Document solutions for future reference
- Update recurring issues list
- Track patterns across time

### With WordPress Maintenance Protocol
Reference: `/home/dave/skippy/conversations/wordpress_maintenance_protocol.md`
- Use WordPress-specific troubleshooting procedures
- Reference GoDaddy quirks section
- Follow database operation safety rules
- Use WP-CLI command reference

### With Deployment Checklist Protocol
Reference: `/home/dave/skippy/conversations/deployment_checklist_protocol.md`
- Many issues occur during/after deployment
- Use post-deployment verification checklist
- Follow rollback procedure if needed
- Update checklist with lessons learned

### With Backup Strategy Protocol
Reference: `/home/dave/skippy/conversations/backup_strategy_protocol.md`
- Create backup before attempting fixes
- Document backup location
- Use backup to compare working vs broken state
- Restore from backup if fix makes things worse

---

## Advanced Debugging Techniques

### Binary Search Debugging

When you have many potential causes, use binary search to narrow down:

```bash
# Example: Which plugin is causing the issue?
# Instead of testing plugins one by one (linear search),
# divide and conquer:

# 1. Deactivate all plugins
wp plugin deactivate --all --allow-root

# 2. Activate half of them
wp plugin activate plugin1 plugin2 plugin3 --allow-root

# 3. Test - does issue occur?
#    - YES: Issue is in first half, deactivate all, test other half
#    - NO: Issue is in second half, activate second half

# 4. Repeat until you find the problematic plugin
```

### Diff Debugging

Compare working vs broken:

```bash
# Compare local (working) vs production (broken)
# Export both databases
wp db export local_working.sql --allow-root
# Download production database

# Compare specific tables
diff <(grep "option_name" local_working.sql) \
     <(grep "option_name" production_broken.sql)

# Compare file contents
diff -r /local/wp-content/themes/campaign/ \
        /production/wp-content/themes/campaign/
```

### Logging Debugging

Add temporary logging to narrow down issue:

```php
// In WordPress theme/plugin file
error_log("DEBUG: Reached line 123");
error_log("DEBUG: Variable value: " . print_r($variable, true));

// Then check debug.log
// tail -f wp-content/debug.log
```

### Network Debugging

Use browser DevTools Network tab:

```
1. Open DevTools (F12)
2. Go to Network tab
3. Reproduce issue
4. Look for:
   - Failed requests (red)
   - 404 errors (missing files)
   - 500 errors (server errors)
   - Slow requests (performance issues)
5. Click on failed request to see details:
   - Request headers
   - Response headers
   - Response body (error message)
```

---

## Debugging Mindset

### Stay Calm and Methodical
- Debugging is problem-solving, not guesswork
- Follow the process even when frustrated
- Take breaks if stuck for 30+ minutes
- Ask for help after exhausting systematic approaches

### Document Everything
- Future you will thank present you
- Others can learn from your investigation
- Patterns become visible over time
- Prevention measures come from good documentation

### Learn from Every Issue
- Every bug teaches something
- Update protocols after solving issues
- Share solutions with team/community
- Build your mental model of the system

### When to Ask for Help
- After exhausting systematic debugging steps
- When issue is outside your expertise
- When time-critical and stuck
- When you need fresh perspective

**Before asking for help, document**:
- What you've tried
- What you've ruled out
- Current hypothesis
- Relevant error messages/logs

---

## Quick Reference

### Debugging Process (Summary)
1. **Identify**: Gather info, document error, create error log
2. **Investigate**: Check logs, system state, browser DevTools
3. **Hypothesize**: List possible causes, create test plan
4. **Test**: Test one variable at a time, document attempts
5. **Document**: Update error log, update protocols, create prevention

### Most Common Issues (Top 10)
1. File permissions (600 vs 644)
2. Database URLs (local vs production)
3. Cache not cleared
4. Files not uploaded during deployment
5. GoDaddy custom table prefix
6. Mobile menu z-index conflicts
7. Plugin conflicts
8. PHP memory limit
9. JavaScript errors (browser-specific)
10. SSL certificate issues

### Essential Commands
```bash
# WordPress
wp db check --allow-root
wp cache flush --allow-root
wp plugin list --allow-root

# File permissions
ls -la [path]
chmod 644 [file]
chmod 755 [directory]

# Logs
tail -50 wp-content/debug.log
journalctl -xe --since "10 minutes ago"

# Network
curl -I [url]
ping [domain]
```

### Essential Tools
- **WP-CLI**: WordPress operations
- **Browser DevTools**: JavaScript, network, CSS
- **curl**: HTTP testing
- **grep/ripgrep**: Code search
- **Git**: Version comparison
- **ls/find**: File investigation

---

## Quick Reference Card

### 5-Step Debugging Process
```
1. IDENTIFY → What's broken? When? What changed?
2. ISOLATE → Which component? Reproduce consistently
3. DIAGNOSE → Root cause? Logs? Tests?
4. FIX → Minimal change, test thoroughly
5. VERIFY → Works? Document? Prevent?
```

### First 3 Questions to Ask
1. **What changed recently?** (deployments, updates, config)
2. **Can I reproduce it?** (consistently, specific conditions)
3. **What do the logs say?** (error messages, stack traces)

### Essential Debug Commands

**WordPress Issues:**
```bash
# Enable debug mode
wp config set WP_DEBUG true --type=constant
wp config set WP_DEBUG_LOG true --type=constant

# Check database
wp db check

# Check plugins
wp plugin list --status=active

# Check logs
tail -50 wp-content/debug.log

# Clear cache
wp cache flush
```

**System Issues:**
```bash
# Check processes
ps aux | grep php
systemctl status apache2  # or nginx

# Check disk space
df -h

# Check permissions
ls -la /path/to/problem

# Check logs
tail -50 /var/log/apache2/error.log
journalctl -xe --since "10 minutes ago"
```

**Network Issues:**
```bash
# Test HTTP
curl -I https://yourdomain.com

# Check DNS
nslookup yourdomain.com

# Check connectivity
ping yourdomain.com

# Check SSL
openssl s_client -connect yourdomain.com:443
```

### Common Fixes Checklist
- [ ] Clear all caches (browser, server, CDN)
- [ ] Check recent changes (rollback if needed)
- [ ] Verify file permissions (644 files, 755 directories)
- [ ] Check disk space (df -h)
- [ ] Restart services if needed
- [ ] Check error logs
- [ ] Test in different browser/incognito
- [ ] Disable plugins one by one

### When to Escalate
- Issue persists >2 hours without progress
- Data loss risk identified
- Security implications discovered
- Beyond current skill level
- Requires vendor support

### Debug Documentation Template
```markdown
## Issue: [Brief description]
**Date:** YYYY-MM-DD
**Status:** Investigating / Resolved

## Purpose

This protocol defines the procedures and standards for debugging workflow  within the Skippy System Manager.


**Symptoms:**
- What's broken

**What I Tried:**
1. Tried X → Result: Failed because Y
2. Tried Z → Result: Worked!

**Root Cause:**
[Why it happened]

**Solution:**
[What fixed it]

**Prevention:**
[How to avoid in future]
```

---

**This protocol is part of the persistent memory system.**
**Reference when debugging any issue to work systematically.**
**Version:** 1.1.0 (Added quick reference 2025-11-05)
```
