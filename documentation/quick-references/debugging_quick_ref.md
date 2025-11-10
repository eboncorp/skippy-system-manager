# Debugging & Troubleshooting - Quick Reference

**Protocol:** [Diagnostic & Debugging Protocol](../protocols/diagnostic_debugging_protocol.md)
**Priority:** HIGH
**Use:** When things aren't working as expected

---

## 🎯 Systematic Approach

### 1. Define the Problem (1 minute)
- What's not working?
- What should it do?
- When did it start?
- What changed recently?

### 2. Gather Information (2-3 minutes)
```bash
# Check logs
tail -100 /var/log/[relevant-log]
wp log list  # WordPress errors

# Check recent changes
git log --oneline -10
ls -lt ~/skippy/work/ | head -10

# Check system status
systemctl status [service]
wp cli check-update
```

### 3. Form Hypothesis (1 minute)
- Most likely cause?
- Quick test to verify?

### 4. Test & Iterate
- Test hypothesis
- Observe results
- Refine or try next hypothesis

---

## 🔍 Common Issues & Solutions

### WordPress Site Issues

**Site won't load:**
```bash
# Check if WP-CLI works
wp cli version

# Check site URL
wp option get siteurl
wp option get home

# Check for fatal errors
tail -100 wp-content/debug.log
```

**Content not updating:**
```bash
# Check cache
wp cache flush
wp transient delete --all

# Verify content saved
wp post get [ID] --field=post_content | head -20

# Check for plugin conflicts
wp plugin deactivate --all
wp plugin activate --all  # One by one
```

**500 Server Error:**
```bash
# Check error logs
tail -100 /var/log/apache2/error.log
tail -100 /var/log/nginx/error.log

# Check .htaccess
cat .htaccess

# Check file permissions
ls -la wp-content/
```

---

### Git/Deployment Issues

**Push rejected:**
```bash
# Check remote
git remote -v

# Check branch
git branch -vv

# Pull first
git pull --rebase origin main
git push origin branch-name
```

**Merge conflicts:**
```bash
# See conflicts
git status
git diff

# Resolve
# Edit conflicted files
git add .
git rebase --continue
```

**Lost changes:**
```bash
# Check reflog
git reflog

# Restore from reflog
git reset --hard HEAD@{2}

# Or check session directory
ls -lt ~/skippy/work/wordpress/rundaverun/
```

---

### Script/Command Failures

**Script not found:**
```bash
# Find script
find scripts -name "*keyword*"
bash scripts/utility/search_protocols_v2.0.0.sh [keyword]

# Check permissions
ls -la scripts/[script].sh
chmod +x scripts/[script].sh
```

**Permission denied:**
```bash
# Check file permissions
ls -la [file]

# Fix if needed (be careful!)
chmod +x [file]  # For scripts
chmod 644 [file]  # For regular files
```

**Command not found:**
```bash
# Check if installed
which [command]
dpkg -l | grep [package]

# Check PATH
echo $PATH

# Install if missing
sudo apt install [package]
```

---

## 🛠️ Debugging Tools

### WordPress Diagnostic
```bash
# Comprehensive diagnostic
bash scripts/wordpress/wordpress_comprehensive_diagnostic_v1.3.0.sh

# Check plugin status
wp plugin list --status=active

# Check theme
wp theme list --status=active

# Database check
wp db check
wp db repair  # If issues found
```

### Protocol Validation
```bash
# Check protocol health
bash scripts/utility/validate_protocols_v2.0.0.sh

# Find protocol
bash scripts/utility/search_protocols_v2.0.0.sh [keyword]
```

### System Logs
```bash
# WordPress debug log
tail -f wp-content/debug.log

# System logs
journalctl -xe
dmesg | tail -50

# Apache/Nginx
tail -f /var/log/apache2/error.log
tail -f /var/log/nginx/error.log
```

---

## 🚨 Emergency Checklist

When site is down:

- [ ] Can access server via SSH?
- [ ] WP-CLI responding? `wp cli version`
- [ ] Database accessible? `wp db check`
- [ ] Recent changes? `git log -5`
- [ ] Disk space? `df -h`
- [ ] Memory? `free -h`
- [ ] Recent errors? `tail -50 wp-content/debug.log`

---

## 📊 Data Collection

Before asking for help, collect:

```bash
# System info
uname -a
php -v
wp cli info

# Recent activity
git log --oneline -10
ls -lt ~/skippy/work/ | head -5

# Error logs
tail -50 wp-content/debug.log > debug.txt
tail -50 /var/log/apache2/error.log > apache.txt

# Current state
wp plugin list > plugins.txt
wp theme list > themes.txt
git status > git-status.txt
```

---

## 🔄 Rollback Quick Steps

If debugging takes too long:

```bash
# 1. Find recent session
ls -lt ~/skippy/work/wordpress/rundaverun/ | head -3

# 2. Rollback content
cd [session-dir]
wp post update [ID] --post_content="$(cat page_[ID]_before.html)"

# 3. Verify
wp post get [ID] --field=post_content | head -20

# 4. Or restore database
wp db import ~/backups/backup_latest.sql
```

**Full procedure:** `emergency_rollback_quick_ref.md`

---

## 💡 Pro Tips

### Enable Debug Mode (Temporarily)
```php
// In wp-config.php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);

// Don't forget to disable after debugging!
```

### Test in Isolation
```bash
# Test on local first
# Use rundaverun-local

# Deactivate plugins one by one
wp plugin deactivate [plugin-name]

# Test with default theme
wp theme activate twentytwentyfour
```

### Document Your Findings
```bash
# Create debug log in session directory
cd ~/skippy/work/[project]/[session]
cat > DEBUG_LOG.md <<EOF
# Debug Session

## Problem
[Describe issue]

## Tests Performed
1. [Test 1] - Result
2. [Test 2] - Result

## Solution
[What fixed it]

## Prevention
[How to avoid in future]
EOF
```

---

## 🎓 Debugging Mindset

**Do:**
- ✅ Change one thing at a time
- ✅ Document what you try
- ✅ Test hypothesis before making changes
- ✅ Save current state before changes
- ✅ Take breaks if stuck (fresh perspective helps)

**Don't:**
- ❌ Make multiple changes at once
- ❌ Skip basic checks (logs, recent changes)
- ❌ Forget to save before state
- ❌ Give up too soon (systematic approach works)

---

## 📞 When to Escalate

Escalate if:
- Issue persists after 30 minutes of debugging
- Affecting production with no obvious cause
- Data loss or corruption suspected
- Security incident suspected
- Outside your expertise area

**Before escalating:**
- Collect data (logs, error messages, recent changes)
- Document what you've tried
- Have rollback plan ready

---

**Full Protocol:** documentation/protocols/diagnostic_debugging_protocol.md
**Related:** emergency_rollback_quick_ref.md, deployment_checklist_quick_ref.md
