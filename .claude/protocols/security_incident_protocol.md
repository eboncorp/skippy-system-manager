# Security Incident Protocol

**Version:** 1.0.0
**Last Updated:** 2026-01-17

---

## Overview

Standard procedures for detecting, responding to, and recovering from security incidents.

---

## Incident Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **Critical** | Active breach, data exfiltration | Immediate |
| **High** | Compromised credentials, malware detected | < 1 hour |
| **Medium** | Suspicious activity, failed login attempts | < 4 hours |
| **Low** | Vulnerability discovered, policy violation | < 24 hours |

---

## Immediate Response (Critical/High)

### Step 1: Isolate

```bash
# Disable compromised service
sudo systemctl stop {service-name}

# Block suspicious IP
sudo iptables -A INPUT -s {IP} -j DROP

# Revoke compromised credentials
# (Change passwords, rotate keys)
```

### Step 2: Document

```bash
SESSION_DIR="/home/dave/skippy/work/security/$(date +%Y%m%d_%H%M%S)_incident"
mkdir -p "$SESSION_DIR"

# Capture current state
date > "$SESSION_DIR/timestamp.txt"
ps aux > "$SESSION_DIR/processes.txt"
netstat -tulpn > "$SESSION_DIR/network.txt"
last -100 > "$SESSION_DIR/logins.txt"
```

### Step 3: Preserve Evidence

```bash
# Copy logs before rotation
cp /var/log/auth.log "$SESSION_DIR/"
cp /var/log/syslog "$SESSION_DIR/"
cp ~/html/wp-content/debug.log "$SESSION_DIR/" 2>/dev/null
```

---

## Credential Compromise Response

### If API Key/Token Exposed

```bash
# 1. Rotate immediately
# Generate new key from provider

# 2. Update in secure storage
# Update .env file or secrets manager

# 3. Search for exposure
grep -r "OLD_KEY_PREFIX" /home/dave/

# 4. Audit usage
# Check provider logs for unauthorized access
```

### If SSH Key Compromised

```bash
# 1. Remove from authorized_keys on all servers
ssh server "grep -v 'compromised-key-fingerprint' ~/.ssh/authorized_keys > temp && mv temp ~/.ssh/authorized_keys"

# 2. Generate new key
ssh-keygen -t ed25519 -C "new-key-$(date +%Y%m%d)"

# 3. Distribute new key
ssh-copy-id -i ~/.ssh/new_key.pub user@server

# 4. Update documentation
```

### If WordPress Admin Compromised

```bash
# 1. Change password immediately
wp user update admin --user_pass="$(openssl rand -base64 32)" --allow-root

# 2. Force logout all sessions
wp user meta delete admin session_tokens --allow-root

# 3. Rotate security keys
curl https://api.wordpress.org/secret-key/1.1/salt/
# Update wp-config.php or .env

# 4. Check for backdoors
grep -r "eval(" wp-content/
grep -r "base64_decode" wp-content/
```

---

## Malware Detection

### Scan Commands

```bash
# Check for suspicious files
find wp-content/ -name "*.php" -mtime -7 -exec ls -la {} \;

# Look for obfuscated code
grep -r "eval(base64_decode" wp-content/
grep -r "preg_replace.*e" wp-content/
grep -r "create_function" wp-content/

# Check file permissions
find wp-content/ -type f -perm /o+w

# Compare core files
wp core verify-checksums --allow-root
wp plugin verify-checksums --all --allow-root
```

### If Malware Found

```bash
# 1. Quarantine
mv suspicious_file.php "$SESSION_DIR/quarantine/"

# 2. Restore from clean backup
wp core download --force --allow-root
wp plugin install {plugin} --force --allow-root

# 3. Update all software
wp core update --allow-root
wp plugin update --all --allow-root
wp theme update --all --allow-root
```

---

## Suspicious Login Activity

### Detection

```bash
# Check failed logins
grep "Failed password" /var/log/auth.log | tail -20

# WordPress login attempts
wp db query "SELECT * FROM wp_usermeta WHERE meta_key = 'wp_user_level';" --allow-root
```

### Response

```bash
# Block IP
sudo iptables -A INPUT -s {IP} -j DROP

# Enable login limiting (if not already)
wp plugin install login-lockdown --activate --allow-root

# Force password reset for affected accounts
wp user reset-password admin --allow-root
```

---

## Post-Incident Actions

### Recovery Checklist

- [ ] Incident contained
- [ ] Root cause identified
- [ ] All compromised credentials rotated
- [ ] Systems restored from clean backup
- [ ] Security patches applied
- [ ] Monitoring enhanced
- [ ] Documentation complete

### Incident Report Template

```markdown
# Security Incident Report

**Date:**
**Severity:**
**Status:** Resolved / Ongoing

## Summary
Brief description of what happened.

## Timeline
- HH:MM - Initial detection
- HH:MM - Response began
- HH:MM - Incident contained
- HH:MM - Recovery complete

## Impact
- Systems affected
- Data exposed (if any)
- Duration

## Root Cause
What allowed this to happen.

## Response Actions
1. Step taken
2. Step taken

## Prevention Measures
How to prevent recurrence.

## Lessons Learned
What we learned from this incident.
```

---

## Prevention Checklist

### Daily
- [ ] Review authentication logs
- [ ] Check error logs

### Weekly
- [ ] Update software packages
- [ ] Review access permissions
- [ ] Verify backups

### Monthly
- [ ] Rotate API keys (if policy requires)
- [ ] Audit user accounts
- [ ] Run security scan

### Quarterly
- [ ] Rotate WordPress security keys
- [ ] Review firewall rules
- [ ] Penetration testing (if applicable)

---

## Emergency Contacts

Document relevant contacts here:
- Hosting provider support
- Security team
- System administrator

---

## Related

- Secret Rotation (in rules)
- Emergency Recovery Workflow
- Backup Workflow
