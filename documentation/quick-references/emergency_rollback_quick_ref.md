# Emergency Rollback - Quick Reference

**Protocol:** [Emergency Rollback Protocol](../protocols/emergency_rollback_protocol.md)
**Priority:** HIGH
**Use:** When deployment goes wrong

---

## 🚨 EMERGENCY - Act Fast!

### Immediate Assessment (30 seconds)

**Is the site down completely?**
- YES → Go to [Site Down](#site-down-critical)
- NO → Continue assessment

**What changed?**
- Content → [Content Rollback](#content-rollback)
- Plugin → [Plugin Rollback](#plugin-rollback)
- Theme → [Theme Rollback](#theme-rollback)
- Database → [Database Rollback](#database-rollback)

---

## 🔥 Site Down (CRITICAL)

### Immediate Actions (Do in order):

**1. Check if WordPress is accessible:**
```bash
curl -I https://davebiggers.com
wp cli version  # Can we reach WP-CLI?
```

**2. If WP-CLI works - Deactivate recent changes:**
```bash
# Deactivate last plugin
wp plugin deactivate [plugin-name]

# Revert to default theme temporarily
wp theme activate twentytwentyfour
```

**3. If WP-CLI doesn't work - Database restore:**
```bash
# Find latest backup
ls -lt ~/backups/*.sql | head -1

# Restore
wp db import ~/backups/backup_YYYYMMDD_HHMMSS.sql
```

**4. Verify site is back:**
```bash
curl -I https://davebiggers.com
# Should return 200 OK
```

---

## 📄 Content Rollback

### Find your session directory:
```bash
ls -lt /home/dave/skippy/work/wordpress/rundaverun/ | head -5
cd [most-recent-session]
```

### Revert content:
```bash
# For single page/post
wp post update [ID] --post_content="$(cat page_[ID]_before.html)"

# Verify
wp post get [ID] --field=post_content > page_[ID]_reverted.html
diff page_[ID]_before.html page_[ID]_reverted.html
```

### If session directory not found:
```bash
# Use WordPress revisions
wp post list --post_type=revision --post_parent=[ID]
wp post get [revision-ID]
# Manually restore from revision
```

---

## 🔌 Plugin Rollback

### Deactivate problematic plugin:
```bash
# Deactivate
wp plugin deactivate [plugin-name]

# Verify site works
curl -I https://davebiggers.com
```

### If that fixes it:
```bash
# Uninstall if needed
wp plugin uninstall [plugin-name]

# Or rollback to previous version
wp plugin install [plugin-name] --version=[old-version] --force
```

### If site still broken:
```bash
# Deactivate ALL plugins
wp plugin deactivate --all

# Test site
# Reactivate one by one to find culprit
wp plugin activate [plugin-name]
```

---

## 🎨 Theme Rollback

### Switch to safe theme:
```bash
# Activate default WordPress theme
wp theme activate twentytwentyfour

# Verify site works
curl -I https://davebiggers.com
```

### Restore previous theme:
```bash
# If you have backup
cp -r ~/backups/themes/[theme-name]/* wp-content/themes/[theme-name]/

# Or reinstall
wp theme install [theme-name] --version=[old-version] --force
```

---

## 🗄️ Database Rollback

### Critical warnings:
- ⚠️ Recent content since backup will be lost
- ⚠️ Only use if no other option works
- ⚠️ Document what will be lost

### Find latest backup:
```bash
ls -lth ~/backups/*.sql | head -5
```

### Create safety backup first:
```bash
wp db export safety_backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore:
```bash
wp db import ~/backups/backup_YYYYMMDD_HHMMSS.sql
```

### Verify:
```bash
wp db check
wp option get siteurl
curl -I https://davebiggers.com
```

---

## 🔍 Verification After Rollback

### Immediate Checks:
- [ ] Site loads (https://davebiggers.com)
- [ ] Homepage displays correctly
- [ ] No fatal errors
- [ ] Admin accessible
- [ ] Core functionality works

### Detailed Checks:
- [ ] All pages load
- [ ] Forms work
- [ ] Navigation works
- [ ] Mobile responsive
- [ ] Search functions

---

## 📝 Post-Rollback Documentation

### Create incident report:
```bash
cat > ~/skippy/conversations/reports/rollback_$(date +%Y%m%d_%H%M%S).md <<EOF
# Emergency Rollback Report

**Date:** $(date)
**Time:** $(date +%H:%M:%S)

## What Happened
[Describe the issue]

## What Was Rolled Back
- [ ] Content changes
- [ ] Plugin: [name]
- [ ] Theme: [name]
- [ ] Database

## Rollback Method Used
[Describe what you did]

## Verification
- Site status: [up/down]
- Functionality: [working/partial/broken]
- Data loss: [none/some/significant]

## Root Cause
[What caused the problem]

## Prevention
[How to prevent this in future]

## Follow-up Actions
- [ ] [Action 1]
- [ ] [Action 2]
EOF
```

---

## 🛡️ Prevention for Next Time

### Before ANY deployment:
1. ✅ **Create backup**
   ```bash
   wp db export backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. ✅ **Test on local**
   ```bash
   # Use rundaverun-local first
   ```

3. ✅ **Document session**
   ```bash
   # Always use session directories
   # Never use /tmp/
   ```

4. ✅ **Have rollback plan ready**
   - Know where backups are
   - Know rollback commands
   - Test rollback procedure

---

## 📞 Escalation

### If rollback doesn't work:

1. **Check hosting status**
   - GoDaddy control panel
   - Server status

2. **Check recent changes**
   ```bash
   git log -10 --oneline
   ls -lt ~/backups/ | head -10
   ```

3. **Contact support**
   - Document what you tried
   - Provide error messages
   - Share recent changes

---

## 🔬 Debugging After Partial Rollback

### Site partially working:

**Check error log:**
```bash
wp log list
tail -100 wp-content/debug.log
```

**Check database:**
```bash
wp db check
wp db repair  # If issues found
```

**Check file permissions:**
```bash
find wp-content -type f -not -perm 644
find wp-content -type d -not -perm 755
```

**Check .htaccess:**
```bash
cat .htaccess
# Verify it's not corrupted
```

---

## 📊 Rollback Decision Matrix

| Symptom | Likely Cause | First Action |
|---------|--------------|--------------|
| White screen | Fatal error | Check error logs |
| 500 error | Server/PHP error | Deactivate plugins |
| Content missing | Bad update | Content rollback |
| Broken layout | Theme issue | Switch theme |
| Database error | DB corruption | DB rollback |
| Can't login | Auth issue | Reset from CLI |

---

## 🚀 Getting Back on Track

### After successful rollback:

1. **Identify root cause**
   - What went wrong?
   - Why wasn't it caught?

2. **Fix the issue**
   - Test fix locally
   - Verify thoroughly

3. **Try deployment again**
   - Follow checklist
   - Have monitoring ready

4. **Document lessons learned**
   - Update protocols if needed
   - Add to knowledge base

---

**Full Protocol:** documentation/protocols/emergency_rollback_protocol.md
**Related:** deployment_checklist_protocol.md, wordpress_backup_protocol.md
**Emergency Contact:** [Add contact info]
