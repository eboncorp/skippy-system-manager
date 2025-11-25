# Secrets Rotation Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Owner:** Security Team
**Status:** Active

---

## Purpose

Establish regular rotation of passwords, API keys, and credentials to maintain security and reduce risk from compromised credentials.

## Scope

All credentials managed by secrets_manager_v1.0.0.sh and related systems including:
- Database passwords
- WordPress admin accounts
- API keys
- Service account credentials
- SSH keys
- Encryption keys

---

## Rotation Schedule

### High Risk (Every 30 Days)
- Database root password
- WordPress admin passwords
- Service account passwords with elevated privileges
- Any credential suspected of compromise

### Medium Risk (Every 90 Days)
- API keys
- Third-party service credentials
- SMTP passwords
- SSH keys for active users

### Low Risk (Every 180 Days)
- Read-only account passwords
- Internal service credentials
- Development/staging credentials

### Event-Triggered (Immediate)
- Suspected compromise
- Personnel departure
- Vendor contract termination
- Security incident
- Public exposure

---

## Rotation Process

### 1. Planning Phase
**Before Rotation:**
- [ ] Identify credential to rotate
- [ ] Check dependencies (what uses this?)
- [ ] Schedule maintenance window if needed
- [ ] Notify stakeholders
- [ ] Prepare rollback plan

### 2. Generate New Credential
```bash
# Generate strong password
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh generate-password

# Or for specific service
openssl rand -base64 32
```

### 3. Store New Credential
```bash
# Update in secrets manager
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh set credential_name
# Enter new credential when prompted
```

### 4. Update Services
**Update all services that use the credential:**
- Configuration files
- Environment variables
- Database connections
- API integrations
- Scripts and tools

### 5. Test New Credential
- [ ] Test service connectivity
- [ ] Verify authentication works
- [ ] Check all dependent systems
- [ ] Monitor logs for errors

### 6. Deactivate Old Credential
- [ ] Wait 24-48 hours (ensure no issues)
- [ ] Deactivate/delete old credential
- [ ] Verify nothing breaks
- [ ] Document rotation completion

### 7. Update Documentation
- [ ] Update runbooks
- [ ] Note rotation in changelog
- [ ] Update emergency contacts if needed

---

## Credential-Specific Procedures

### Database Password Rotation

```bash
# 1. Generate new password
NEW_PASS=$(openssl rand -base64 24)

# 2. Update database
mysql -u root -p <<EOF
ALTER USER 'wpuser'@'localhost' IDENTIFIED BY '${NEW_PASS}';
FLUSH PRIVILEGES;
EOF

# 3. Update wp-config.php
wp config set DB_PASSWORD "${NEW_PASS}"

# 4. Store in secrets manager
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh set db_password

# 5. Test
wp db check

# 6. Update backups with new credentials
```

**Downtime:** ~2 minutes
**Rollback:** Keep old password for 48 hours

### WordPress Admin Password

```bash
# 1. Generate new password
NEW_PASS=$(openssl rand -base64 24)

# 2. Update WordPress
wp user update admin --user_pass="${NEW_PASS}"

# 3. Store in secrets manager
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh set wordpress_admin

# 4. Test login
# Verify can log in with new password

# 5. Update shared password manager
# [Update team password manager]
```

**Downtime:** None
**Notify:** All admins before rotation

### API Key Rotation

```bash
# 1. Generate new API key in service
# [Visit service dashboard, generate new key]

# 2. Store new key
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh set service_api_key

# 3. Update configuration
# Update wp-config.php or plugin settings

# 4. Test API calls
# Verify service still works

# 5. Wait 48 hours, then revoke old key
```

**Best Practice:** Create new key before revoking old (zero downtime)

### SSH Key Rotation

```bash
# 1. Generate new key pair
ssh-keygen -t ed25519 -C "rundaverun-$(date +%Y%m)" -f ~/.ssh/id_ed25519_new

# 2. Add new public key to servers
ssh-copy-id -i ~/.ssh/id_ed25519_new.pub user@server

# 3. Test new key
ssh -i ~/.ssh/id_ed25519_new user@server

# 4. Update ~/.ssh/config to use new key
# Replace old key reference with new

# 5. Wait 1 week, then remove old public key from servers

# 6. Securely delete old private key
shred -vfz -n 3 ~/.ssh/id_ed25519_old
```

---

## Emergency Rotation

### When Suspected Compromise

**Immediate Actions (within 1 hour):**
1. Rotate compromised credential immediately
2. Check access logs for unauthorized use
3. Assess damage/exposure
4. Notify security team
5. Follow Incident Response Protocol

**Don't wait for:**
- Regular rotation schedule
- Maintenance windows
- Off-hours (do it immediately)

### Rotation Checklist for Compromise

- [ ] Identify all systems using credential
- [ ] Generate new credential
- [ ] Update all systems ASAP
- [ ] Deactivate old credential immediately
- [ ] Monitor for failed authentication attempts
- [ ] Review access logs for unauthorized activity
- [ ] Document incident
- [ ] Assess what attacker may have accessed
- [ ] Implement additional security measures

---

## Tracking Rotations

### Rotation Log

**Location:** `/home/dave/skippy/logs/security/rotation_log.csv`

**Format:**
```csv
Date,Credential,Rotated_By,Reason,Next_Rotation
2025-11-04,db_password,dave,scheduled,2025-12-04
2025-11-04,wp_admin,dave,scheduled,2026-02-04
```

### Rotation Reminder Script

```bash
#!/bin/bash
# Check for credentials needing rotation

LOG="/home/dave/skippy/logs/security/rotation_log.csv"
TODAY=$(date +%s)
WARN_DAYS=7

while IFS=, read -r date cred user reason next; do
    if [ "$date" = "Date" ]; then continue; fi

    next_ts=$(date -d "$next" +%s 2>/dev/null || continue)
    days_until=$(( (next_ts - TODAY) / 86400 ))

    if [ "$days_until" -le 0 ]; then
        echo "OVERDUE: $cred (due: $next)"
    elif [ "$days_until" -le "$WARN_DAYS" ]; then
        echo "UPCOMING: $cred (due in $days_until days)"
    fi
done < "$LOG"
```

---

## Integration with Secrets Manager

### Using Secrets Manager for Rotation

```bash
# List all secrets
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh list

# Update secret (rotation)
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh set secret_name

# Get secret (for service configuration)
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh get secret_name

# Delete old secret
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh delete old_secret_name
```

---

## Automation

### Automated Rotation Reminders

```bash
# Add to cron (check daily)
0 9 * * * /home/dave/skippy/scripts/security/rotation_reminder.sh | mail -s "Credential Rotation Reminders" admin@rundaverun.org
```

### Semi-Automated Rotation

**Some services support automated rotation:**
- AWS credentials (IAM credential rotation)
- Database passwords (automated via scripts)
- Service tokens with auto-renewal

**Cannot fully automate:**
- Third-party service API keys
- Manual login credentials
- Services without API for rotation

---

## Best Practices

### Password Requirements
- Minimum 24 characters for automated systems
- Minimum 16 characters for human use
- Use password generator, not manual creation
- Never reuse passwords
- Store only in secrets manager

### Key Generation
```bash
# Strong password
openssl rand -base64 32

# API key style
openssl rand -hex 32

# UUID style
uuidgen
```

### Documentation
- Document which services use which credentials
- Keep runbooks updated with rotation procedures
- Note any special considerations
- Track rotation history

---

## Monitoring

### Alert on:
- Failed authentication attempts (may indicate old credential in use)
- Credentials not rotated on schedule
- Unusual access patterns
- Secrets manager access

### Metrics to Track:
- Rotation compliance rate
- Overdue rotations
- Time to rotate after compromise
- Failed rotations (requiring rollback)

---

## Rollback Procedures

### If Rotation Causes Issues

**Immediate Rollback:**
1. Restore old credential from backup
2. Update services back to old credential
3. Verify services working
4. Document what went wrong
5. Fix issue before retry

**Rollback Example:**
```bash
# Restore old database password
mysql -u root -p <<EOF
ALTER USER 'wpuser'@'localhost' IDENTIFIED BY '${OLD_PASS}';
FLUSH PRIVILEGES;
EOF

# Update wp-config.php
wp config set DB_PASSWORD "${OLD_PASS}"

# Test
wp db check
```

---

## Related Protocols
- Authorization Protocol
- Access Control Protocol
- Incident Response Protocol
- Data Privacy Protocol

---

## Appendix: Rotation Checklist Template

### Pre-Rotation
- [ ] Identify credential to rotate
- [ ] Check dependencies
- [ ] Schedule if needed
- [ ] Prepare rollback plan
- [ ] Notify stakeholders

### During Rotation
- [ ] Generate new credential
- [ ] Store in secrets manager
- [ ] Update all services
- [ ] Test connectivity
- [ ] Monitor for errors

### Post-Rotation
- [ ] Wait 24-48 hours
- [ ] Deactivate old credential
- [ ] Verify no issues
- [ ] Update documentation
- [ ] Log rotation completion
- [ ] Schedule next rotation

---

**Version History:**
- 1.0.0 (2025-11-04): Initial protocol creation
