# Secrets Inventory & Management Protocol

**Version:** 1.0.0
**Created:** 2025-11-05
**Owner:** Security Team
**Status:** Active
**Priority:** CRITICAL (Security)

---

## Purpose

Maintain a complete, centralized inventory of all secrets (passwords, API keys, tokens, certificates) to ensure proper rotation, access control, and incident response capability.

**Focus:** Centralized tracking and inventory management
**Complements:** secrets_rotation_protocol (rotation schedules), access_control_protocol (who has access)

---

## Scope

This protocol covers all secrets including:
- API keys and tokens
- Database credentials
- Server/hosting passwords
- SSH keys and certificates
- Service account credentials
- Encryption keys
- Third-party service credentials
- OAuth tokens and refresh tokens
- Webhook secrets
- 2FA backup codes

---

## Secrets Inventory Location

### Primary Inventory
**Location:** `/home/dave/skippy/security/secrets_inventory.csv`
**Format:** CSV spreadsheet (can be opened in Excel, LibreOffice, or text editor)
**Access:** Restricted to authorized personnel only
**Backup:** Encrypted backup in secure location

### Inventory Structure

**Required Fields:**
1. **Secret ID** - Unique identifier (e.g., SEC-001)
2. **Secret Name** - Descriptive name (e.g., "WordPress Admin Password")
3. **Secret Type** - Password, API Key, Token, Certificate, SSH Key
4. **Service/System** - Where it's used (e.g., "WordPress Production")
5. **Owner** - Person responsible for this secret
6. **Location Stored** - Where the actual secret is stored (password manager, env file, etc.)
7. **Last Rotated** - Date last changed
8. **Next Rotation Due** - Based on rotation schedule
9. **Rotation Frequency** - 30/90/180/365 days
10. **Who Has Access** - List of people/systems with access
11. **Criticality** - Critical/High/Medium/Low
12. **Notes** - Additional context

---

## Secrets Inventory Template

```csv
Secret_ID,Secret_Name,Secret_Type,Service_System,Owner,Location_Stored,Last_Rotated,Next_Rotation_Due,Rotation_Frequency,Who_Has_Access,Criticality,Notes
SEC-001,WordPress Admin Password,Password,WordPress Production,Dave,1Password,2025-10-15,2025-11-15,30 days,"Dave, Emergency Admin",Critical,Main admin account
SEC-002,GoDaddy API Key,API Key,GoDaddy Hosting,Dave,1Password,2025-09-01,2025-12-01,90 days,"Dave, Deployment Scripts",High,Used for automated deployments
SEC-003,Database Root Password,Password,MySQL Production,Dave,1Password,2025-08-15,2026-02-15,180 days,"Dave, Backup Scripts",Critical,Production DB root access
SEC-004,GitHub Deploy Token,Token,GitHub Deployments,Dave,GitHub Secrets,2025-10-01,2026-10-01,365 days,"Dave, CI/CD Pipeline",High,Read-only deploy token
SEC-005,SSH Private Key (Production),SSH Key,Production Server,Dave,~/.ssh/,2025-07-01,2026-07-01,365 days,Dave,Critical,Server access key
```

---

## Secret Categories

### Critical Secrets (30-day rotation)
**Definition:** Compromise would cause immediate, severe impact
**Examples:**
- Production database root passwords
- Server root/admin SSH keys
- Payment processor API keys
- Domain registrar credentials
- Cloud provider root credentials

**Requirements:**
- Rotate every 30 days
- Multi-factor authentication required
- Access logged and monitored
- Emergency access procedure documented

---

### High Secrets (90-day rotation)
**Definition:** Compromise would cause significant impact
**Examples:**
- WordPress admin passwords
- Hosting panel credentials
- API keys for critical services
- Service account credentials
- Application database passwords

**Requirements:**
- Rotate every 90 days
- MFA recommended
- Access reviewed quarterly
- Backup codes stored securely

---

### Medium Secrets (180-day rotation)
**Definition:** Compromise would cause moderate impact
**Examples:**
- Read-only API keys
- Development database passwords
- Third-party integration tokens
- Monitoring service credentials
- Backup service credentials

**Requirements:**
- Rotate every 180 days
- Access reviewed semi-annually
- Can be shared with team if needed

---

### Low Secrets (365-day rotation)
**Definition:** Compromise would cause minimal impact
**Examples:**
- Non-sensitive service credentials
- Test environment passwords
- Public API read-only tokens
- Analytics read-only tokens

**Requirements:**
- Rotate annually
- Access reviewed annually
- Can be documented in team wiki

---

## Inventory Management Procedures

### Adding New Secret to Inventory

**When adding a new secret:**
1. Assign next sequential Secret ID
2. Fill in all required fields
3. Store actual secret in password manager
4. Set rotation reminder
5. Document who has access
6. Update inventory spreadsheet
7. Commit inventory update (if in git)

**Example:**
```bash
# Add new secret entry
echo 'SEC-006,Mailgun API Key,API Key,Email Service,Dave,1Password,2025-11-05,2026-02-05,90 days,Dave,Medium,Used for campaign emails' >> /home/dave/skippy/security/secrets_inventory.csv
```

---

### Rotating a Secret

**When rotating a secret:**
1. Generate new secret value
2. Update in all locations where used
3. Test to verify new secret works
4. Update "Last_Rotated" date in inventory
5. Calculate and update "Next_Rotation_Due"
6. Document rotation in change log
7. Revoke old secret after verification period

**Documentation:**
```bash
# Update rotation dates
# Before: SEC-002,GoDaddy API Key,API Key,GoDaddy Hosting,Dave,1Password,2025-09-01,2025-12-01,90 days
# After:  SEC-002,GoDaddy API Key,API Key,GoDaddy Hosting,Dave,1Password,2025-11-05,2026-02-05,90 days
```

---

### Removing Secret from Inventory

**When removing a secret (service discontinued):**
1. Verify secret is no longer in use
2. Revoke/delete secret from service
3. Remove from password manager
4. Mark as "DELETED" in inventory (don't delete row)
5. Move to "Deleted Secrets" section
6. Document date deleted and reason

**Example:**
```csv
# Mark as deleted but keep record
SEC-999,Old Service API,API Key,DELETED,Dave,DELETED,2025-11-05,N/A,N/A,NONE,N/A,Deleted 2025-11-05 - Service discontinued
```

---

## Access Management

### Who Should Have Access to Inventory

**Full Access (Read/Write):**
- Security team lead
- System administrator
- Designated backup person

**Read-Only Access:**
- Team leads (for their domain)
- Incident response team (during incidents)
- Auditors (during security audits)

**No Access:**
- General team members (request specific secrets as needed)
- Contractors (unless specifically authorized)
- Automated systems (use specific credentials, not inventory access)

---

### Emergency Access Procedure

**If primary secret owner unavailable:**

1. **Locate Emergency Access Document:**
   - Stored in: `/home/dave/skippy/security/emergency_access.md`
   - Contains: Instructions for accessing critical secrets

2. **Follow Break-Glass Procedure:**
   - Contact secondary owner
   - Document emergency access in log
   - Reset secret after emergency resolved
   - Update inventory with new rotation date

3. **Post-Emergency Actions:**
   - Review why emergency access was needed
   - Update emergency contact information
   - Rotate any secrets accessed during emergency
   - Document lessons learned

---

## Audit Procedures

### Monthly Audit (Quick Check)

**Check these items:**
- [ ] Any secrets past rotation date?
- [ ] Any new secrets added but not in inventory?
- [ ] Any deleted services still have secrets listed?
- [ ] Inventory file backed up?
- [ ] Access log reviewed?

**Time:** 15 minutes
**Owner:** Security team lead

---

### Quarterly Audit (Comprehensive)

**Check these items:**
- [ ] All secrets accounted for
- [ ] All rotation schedules appropriate
- [ ] All owners still current
- [ ] All locations still accurate
- [ ] Test random sample of secrets (still work?)
- [ ] Review access permissions
- [ ] Update emergency access procedures
- [ ] Archive old rotation logs

**Time:** 2 hours
**Owner:** Security team
**Output:** Audit report saved to `/home/dave/skippy/security/audits/`

---

### Annual Audit (Full Review)

**Check these items:**
- [ ] Complete inventory verification
- [ ] Re-evaluate all criticality ratings
- [ ] Review and update all rotation frequencies
- [ ] Test all emergency access procedures
- [ ] Review all access permissions
- [ ] Update documentation
- [ ] Conduct penetration test of secret storage
- [ ] Review incident reports for secret-related issues

**Time:** 1 day
**Owner:** Security team + External auditor (if available)
**Output:** Comprehensive audit report

---

## Integration with Other Protocols

### With secrets_rotation_protocol
- Inventory provides list of what to rotate
- Rotation protocol defines how to rotate
- Inventory tracks when rotation occurred

### With access_control_protocol
- Inventory documents who has access
- Access control defines how to grant/revoke
- Both must stay synchronized

### With incident_response_protocol
- Inventory enables quick secret identification during incident
- Incident response may trigger emergency rotation
- Post-incident review updates inventory

---

## Secret Discovery Process

**How to find secrets not yet in inventory:**

### 1. Code Repository Scan
```bash
# Search for potential secrets in code
grep -r "api_key\|password\|secret\|token" /home/dave/skippy/ --include="*.sh" --include="*.py" --include="*.php" --include="*.env"
```

### 2. Configuration File Review
```bash
# Check common config file locations
find /home/dave/skippy -name "*.conf" -o -name "*.config" -o -name ".env*" -o -name "wp-config.php"
```

### 3. Password Manager Review
- Export list of all entries from password manager
- Compare against inventory
- Add missing entries

### 4. Service Account Review
- List all third-party services used
- Check each for API keys/tokens
- Add to inventory if missing

### 5. Team Interview
- Ask each team member what secrets they use
- Document undiscovered secrets
- Add to inventory

---

## Quick Reference Commands

### View Inventory
```bash
# View entire inventory
cat /home/dave/skippy/security/secrets_inventory.csv

# View secrets due for rotation soon
awk -F',' 'NR>1 && $8 < "'$(date -d '+7 days' +%Y-%m-%d)'" {print $1,$2,$8}' /home/dave/skippy/security/secrets_inventory.csv

# Count secrets by type
awk -F',' 'NR>1 {print $3}' /home/dave/skippy/security/secrets_inventory.csv | sort | uniq -c

# List critical secrets
awk -F',' 'NR>1 && $11=="Critical" {print $1,$2}' /home/dave/skippy/security/secrets_inventory.csv
```

### Add New Secret
```bash
# Template for adding
echo 'SEC-XXX,Name,Type,Service,Owner,Location,Date,NextDate,Frequency,Access,Criticality,Notes' >> /home/dave/skippy/security/secrets_inventory.csv
```

### Backup Inventory
```bash
# Create encrypted backup
cp /home/dave/skippy/security/secrets_inventory.csv /home/dave/skippy/security/backups/secrets_inventory_$(date +%Y%m%d).csv
```

---

## Getting Started Checklist

**To implement this protocol:**

- [ ] Create `/home/dave/skippy/security/` directory
- [ ] Create `secrets_inventory.csv` file with headers
- [ ] Conduct initial secret discovery
- [ ] Document all known secrets in inventory
- [ ] Set up monthly audit reminder
- [ ] Document emergency access procedure
- [ ] Train team on inventory usage
- [ ] Schedule first quarterly audit
- [ ] Integrate with rotation protocol
- [ ] Set up automated backup of inventory

---

## Metrics & KPIs

### Track These Metrics:

**Coverage:**
- % of secrets in inventory (target: 100%)
- Time to add new secret to inventory (target: <24 hours)

**Rotation Compliance:**
- % of secrets rotated on schedule (target: >95%)
- Average days overdue for rotation (target: <7 days)

**Access Control:**
- % of secrets with documented access (target: 100%)
- Average number of people with access per secret (target: <3)

**Audit Compliance:**
- Monthly audits completed on time (target: 100%)
- Critical findings from audits (target: 0)

---

## Common Scenarios

### Scenario 1: New Team Member Joins

**Steps:**
1. Review inventory for secrets they need access to
2. Grant access through proper channels (password manager, service admin panel)
3. Update "Who_Has_Access" field for each secret granted
4. Document access grant date in log
5. Schedule access review in 90 days

---

### Scenario 2: Secret Potentially Compromised

**Steps:**
1. Immediately locate secret in inventory (by name or service)
2. Identify all places secret is used (from inventory notes)
3. Generate new secret value
4. Update in all locations
5. Test to verify functionality
6. Revoke old secret
7. Update inventory with new rotation date
8. Document incident in security log
9. Review how compromise occurred
10. Update procedures to prevent recurrence

---

### Scenario 3: Service Being Decommissioned

**Steps:**
1. Identify all secrets for that service (search inventory by Service_System)
2. Revoke all secrets at service level
3. Remove from password manager
4. Mark secrets as DELETED in inventory (keep record)
5. Remove access for all users
6. Archive related documentation
7. Document decommissioning date and reason

---

## Best Practices

✅ **Do:**
- Keep inventory up to date (within 24 hours of changes)
- Use strong, unique passwords for all secrets
- Store actual secrets in password manager, not inventory
- Regular audits (monthly minimum)
- Document everything
- Encrypt inventory file
- Backup inventory regularly

❌ **Don't:**
- Store actual secret values in inventory CSV
- Share inventory file unencrypted
- Skip rotation schedules
- Grant access without documentation
- Delete inventory entries (mark as deleted instead)
- Ignore overdue rotations
- Share secrets via insecure channels (email, Slack, etc.)

---

**Status:** ✅ ACTIVE
**Version:** 1.0.0
**Last Updated:** 2025-11-05
**Integrates With:** secrets_rotation_protocol, access_control_protocol, incident_response_protocol

**This protocol is critical for security. Non-compliance may result in security incidents.**

---
