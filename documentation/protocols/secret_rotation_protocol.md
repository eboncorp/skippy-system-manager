# Secret Rotation Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

Security keys, passwords, and API tokens must be rotated regularly to maintain security.

## Purpose

- Reduce risk of compromised credentials
- Meet security best practices
- Maintain system security
- Track rotation history

---

## Rotation Schedule

**WordPress Security Keys: Every 90 Days**
- AUTH_KEY, SECURE_AUTH_KEY, LOGGED_IN_KEY, NONCE_KEY
- AUTH_SALT, SECURE_AUTH_SALT, LOGGED_IN_SALT, NONCE_SALT

**Database Passwords: Every 180 Days**
- WordPress database user password
- Root database password (if applicable)

**API Keys: Immediately if Compromised**
- Google Analytics
- Email service APIs
- External service integrations

**SSH Keys: Every 365 Days**
- GoDaddy SSH key
- GitHub deploy keys

---

## WordPress Security Key Rotation

### Procedure

**Step 1: Generate New Keys**
```bash
curl https://api.wordpress.org/secret-key/1.1/salt/
```

**Step 2: Update .env File**
```bash
cd ~/rundaverun/campaign
nano .env  # Update the 8 keys
```

**Step 3: Deploy to Production**
```bash
scp .env godaddy:~/html/.env
```

**Step 4: Verify Authentication Still Works**
```bash
# Test WordPress login
# Test user sessions
# Verify no users logged out unexpectedly
```

**Step 5: Document Rotation**
```bash
echo "$(date): WordPress keys rotated" >> ~/skippy/logs/secret_rotation.log
```

---

## Database Password Rotation

### Procedure

**Step 1: Create Backup**
```bash
wp db export backup_pre_password_change.sql
```

**Step 2: Generate New Password**
```bash
NEW_PASS=$(openssl rand -base64 32)
```

**Step 3: Update Database User**
```bash
wp db query "ALTER USER 'dbuser'@'localhost' IDENTIFIED BY '$NEW_PASS';"
```

**Step 4: Update Configuration**
```bash
# Update .env file with new password
nano ~/rundaverun/campaign/.env
```

**Step 5: Test Connection**
```bash
wp db check
```

---

## Automation

### Quarterly Reminder (Cron)
```bash
# Add to crontab
# Every 90 days on 1st of quarter at 9 AM
0 9 1 */3 * echo "Reminder: Rotate WordPress security keys" | mail -s "Security Key Rotation Due" dave@example.com
```

### Rotation Script
```bash
#!/bin/bash
# rotate_wordpress_keys_v1.0.0.sh

# Generate new keys
NEW_KEYS=$(curl -s https://api.wordpress.org/secret-key/1.1/salt/)

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d)

# Update .env with new keys
# (Manual step - requires careful editing)

echo "New keys generated. Update .env file manually."
echo "Backup saved: .env.backup.$(date +%Y%m%d)"
```

---

## Tracking

### Rotation Log
```
/home/dave/skippy/logs/secret_rotation.log

Format:
YYYY-MM-DD HH:MM:SS | Resource | Action | Status
2025-11-06 14:30:00 | WordPress Keys | Rotated | Success
2025-11-06 14:35:00 | Database Password | Rotated | Success
```

### Next Rotation Dates
```
WordPress Keys: 2026-02-04 (90 days from 2025-11-06)
Database Password: 2026-05-05 (180 days from 2025-11-06)
SSH Keys: 2026-11-06 (365 days from 2025-11-06)
```

---

## Best Practices

### DO:
✅ Rotate on schedule
✅ Test after rotation
✅ Document rotation dates
✅ Keep backups before rotation
✅ Use strong generated passwords

### DON'T:
❌ Skip rotations
❌ Use predictable passwords
❌ Forget to update all instances
❌ Rotate without testing
❌ Lose backup of old credentials (until verified)

---

## Emergency Rotation

**If Credentials Compromised:**

1. **Immediately** generate new credentials
2. Update all systems simultaneously
3. Audit for unauthorized access
4. Document incident
5. Review security procedures
6. Consider additional security measures

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2026-02-04
