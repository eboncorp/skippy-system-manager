# Security Checklist - Quick Reference

**Protocols:** [Authorization Protocol](../../conversations/authorization_protocol.md), [Pre-commit Sanitization](../../conversations/pre_commit_sanitization_protocol.md)
**Priority:** CRITICAL
**Use:** Before ANY deployment, commit, or sensitive operation

---

## 🔒 Pre-Commit Security Scan

### Automatic (Always Runs)
```bash
# Pre-commit hook automatically checks:
# - Credentials in code
# - API keys
# - Passwords
# - Private keys
# - Tokens

# If scan fails:
# 1. Remove sensitive data
# 2. Commit will proceed automatically
```

### Manual Check (Before Committing)
```bash
# Search for common patterns
grep -r "password\|api_key\|secret\|token" [files]
grep -r "BEGIN.*PRIVATE KEY" [files]
grep -r "@.*\.com.*password" [files]

# Check git diff before commit
git diff
git diff --staged
```

---

## 🚨 Never Commit These

### ❌ Credentials
```
# BAD - Never commit:
API_KEY=sk_live_abc123
DB_PASSWORD=mypassword
AWS_SECRET=AKIAIOSFODNN7EXAMPLE

# GOOD - Use environment variables:
API_KEY=${API_KEY}
DB_PASSWORD=${DB_PASSWORD}
AWS_SECRET=${AWS_SECRET}
```

### ❌ Private Keys
```
# Never commit:
- id_rsa (SSH private key)
- *.pem files
- *.key files
- certificate private keys
```

### ❌ Configuration Files with Secrets
```
# Never commit:
- .env (if contains real values)
- credentials.json
- config.production.json (with real data)

# OK to commit:
- .env.example (with placeholder values)
- credentials.example.json
- config.template.json
```

---

## ✅ Authorization Required

### When to Ask for Authorization

**Before these operations:**
```bash
# Destructive operations
rm -rf [directory]
git push --force
DROP TABLE [table]

# Mass changes
UPDATE [table] SET [field]  # Without WHERE
DELETE FROM [table]  # Without WHERE
git rebase -i  # Interactive rebase

# Production deployments
# - Database migrations
# - Plugin activations
# - Theme changes
# - Configuration updates
```

**How to request:**
```bash
# Run authorization script
/home/dave/scripts/system/authorize_claude

# Or ask user directly:
# "This operation [description] is destructive. May I proceed?"
```

**Authorization window:** 4 hours

---

## 🔐 WordPress Security

### Before Deployment
- [ ] No credentials in code
- [ ] No debug mode enabled in production
- [ ] Security plugins active
- [ ] SSL certificate valid
- [ ] File permissions correct (644 files, 755 dirs)
- [ ] .htaccess secured
- [ ] wp-config.php permissions set (400 or 440)

### Check Security Settings
```bash
# Check debug mode (should be false in production)
wp config get WP_DEBUG
wp config get WP_DEBUG_LOG
wp config get WP_DEBUG_DISPLAY

# Check file permissions
find wp-content -type f -not -perm 644
find wp-content -type d -not -perm 755

# Check security plugins
wp plugin list | grep security

# Check user roles
wp user list --role=administrator
```

### Secure wp-config.php
```bash
# Restrictive permissions
chmod 400 wp-config.php

# Or if needed by web server
chmod 440 wp-config.php

# Verify
ls -la wp-config.php
```

---

## 🔍 Secret Scanning

### Before Commit
```bash
# Use pre-commit security scan
bash scripts/utility/pre_commit_security_scan_v1.0.0.sh

# Patterns to search:
# - password, passwd, pwd
# - api_key, apikey, api-key
# - secret, token, auth
# - private_key, privatekey
# - credentials, creds
```

### After Accidental Commit
```bash
# If you committed secrets:

# 1. Remove from latest commit
git reset --soft HEAD~1
# Remove secret
git add .
git commit -m "Remove secrets"

# 2. If already pushed - ROTATE IMMEDIATELY
# - Change password/key
# - Revoke API token
# - Generate new credentials

# 3. Clean git history (advanced)
# Contact security team for help
```

---

## 📋 Deployment Security Checklist

### Pre-Deployment
- [ ] Code reviewed by at least one other person
- [ ] Security scan passed
- [ ] No TODO comments with security implications
- [ ] No hardcoded secrets
- [ ] Environment variables configured
- [ ] Backup created
- [ ] Rollback plan ready

### Post-Deployment
- [ ] Site loads correctly
- [ ] HTTPS working (green lock icon)
- [ ] No console errors
- [ ] Security headers present
- [ ] Login still works
- [ ] Admin panel accessible

---

## 🛡️ Access Control

### Principle of Least Privilege

**Give minimum necessary access:**
```bash
# WordPress roles (most to least privileged)
# - Super Admin (multisite only)
# - Administrator
# - Editor
# - Author
# - Contributor
# - Subscriber

# Check user permissions
wp user list --role=administrator

# Audit user capabilities
wp user get [username]
```

### SSH Key Security
```bash
# Proper permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
chmod 644 ~/.ssh/authorized_keys

# Check permissions
ls -la ~/.ssh/
```

---

## 🚨 Incident Response

### If Security Issue Suspected

**Immediate actions:**
1. **Isolate** - Stop further damage
2. **Assess** - What's affected?
3. **Contain** - Limit access
4. **Document** - Record everything
5. **Notify** - Contact appropriate people

**Steps:**
```bash
# 1. Check for unauthorized access
wp user list --role=administrator
last | head -20  # Recent logins

# 2. Check recent changes
git log --all --since="24 hours ago"
wp post list --post_type=any --orderby=modified --order=DESC

# 3. Check for malware
find wp-content -name "*.php" -mtime -7  # Modified in last 7 days
grep -r "eval(base64_decode" wp-content/

# 4. Rotate credentials
# - Database passwords
# - API keys
# - WordPress salts
# - SSH keys

# 5. Create incident report
cat > ~/skippy/conversations/reports/security_incident_$(date +%Y%m%d).md
```

---

## 🔑 Password & Secret Management

### Best Practices
- ✅ Use unique passwords for each service
- ✅ Use password manager
- ✅ Enable 2FA where available
- ✅ Rotate secrets quarterly
- ✅ Never share credentials in plain text
- ✅ Use SSH keys instead of passwords

### WordPress Security Keys
```bash
# Rotate WordPress salts (forces all users to re-login)
wp config shuffle-salts

# Or get new salts
curl https://api.wordpress.org/secret-key/1.1/salt/
```

---

## 📊 Security Audit

### Monthly Check (15 minutes)
```bash
# 1. User audit
wp user list --role=administrator

# 2. Plugin audit
wp plugin list | grep -v "active"  # Check inactive plugins
wp plugin list --field=update  # Check for updates

# 3. File integrity
find wp-content -name "*.php" -mtime -30 | head -20

# 4. Log review
grep "failed login" /var/log/auth.log | tail -20

# 5. Backup verification
ls -lh ~/backups/*.sql | tail -5
```

---

## 🎯 Quick Security Commands

### Check for Common Issues
```bash
# Permissions audit
find . -type f -perm 777  # Should return nothing
find . -type d -perm 777  # Should be minimal

# Search for eval/base64 (potential malware)
grep -r "eval(base64_decode" wp-content/ 2>/dev/null

# Check for recently modified files
find . -type f -mtime -7 -name "*.php"

# Check for suspicious users
wp user list --role=administrator
```

### Quick Hardening
```bash
# Disable file editing in WP admin
wp config set DISALLOW_FILE_EDIT true

# Limit login attempts (if plugin installed)
wp plugin activate limit-login-attempts

# Force HTTPS
wp config set FORCE_SSL_ADMIN true
```

---

## 📞 Security Contacts

**If you find a security issue:**
1. Document the issue (don't share publicly)
2. Contact protocol owner
3. Follow incident response protocol
4. Don't deploy until resolved

**For authorization:**
- Run: `/home/dave/scripts/system/authorize_claude`
- Valid for: 4 hours
- Required for: Destructive operations

---

## 💡 Remember

**Security is everyone's responsibility!**

- 🔒 Never commit secrets
- ✅ Always run security scan
- 🔑 Rotate credentials regularly
- 📋 Follow checklists
- 🚨 Report incidents immediately

**When in doubt, ask before proceeding!**

---

**Full Protocols:**
- conversations/authorization_protocol.md
- conversations/pre_commit_sanitization_protocol.md
- conversations/secrets_inventory_protocol.md
**Related:** git_workflow_quick_ref.md
