# Data Privacy Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Owner:** Infrastructure & Legal Teams
**Status:** Active

---

## Purpose

Protect personal information of supporters, volunteers, and donors in compliance with privacy laws (GDPR, CCPA, state laws) and ethical campaign practices.

## Scope

All personally identifiable information (PII) collected, stored, or processed by the campaign including:
- Volunteer registration data
- Donor information
- Email subscribers
- Contact form submissions
- Website analytics
- Third-party integrations

---

## Data Classification

### High Sensitivity (Strict Protection Required)
- Social Security Numbers
- Financial information (credit cards, bank accounts)
- Background check results
- Health information
- Passwords and credentials

**Protection:** Encrypted at rest and in transit, access logs, minimal retention

### Medium Sensitivity (Standard Protection)
- Full names with contact info
- Email addresses
- Phone numbers
- Mailing addresses
- Volunteer preferences
- Donation history

**Protection:** Access controlled, encrypted in transit, secure storage

### Low Sensitivity (Basic Protection)
- First names only
- General preferences
- Public information
- Aggregated statistics

**Protection:** Standard security practices

---

## Collection Principles

### 1. Minimal Collection
- Only collect data necessary for stated purpose
- Don't collect "nice to have" data
- Regular review of forms to minimize fields

### 2. Informed Consent
- Clear privacy policy
- Opt-in for email/communications
- Explain how data will be used
- Easy opt-out mechanism

### 3. Purpose Limitation
- Use data only for stated purpose
- Don't repurpose without consent
- Delete when purpose complete

### 4. Transparency
- Privacy policy publicly available
- Contact method for privacy questions
- Annual privacy practices review

---

## Data Subject Rights

### Right to Access
**Request:** "What data do you have about me?"
**Response Time:** 30 days
**Process:**
1. Verify identity
2. Search all systems
3. Compile data report
4. Deliver in readable format

### Right to Deletion ("Right to be Forgotten")
**Request:** "Delete my data"
**Response Time:** 30 days
**Process:**
1. Verify identity
2. Check legal obligations (can't delete if required by law)
3. Delete from all systems
4. Log deletion
5. Confirm completion

**Deletion Script Template:**
```bash
#!/bin/bash
# Delete user data
EMAIL="$1"

# WordPress
wp user delete $(wp user list --field=ID --user_email="$EMAIL") --yes

# Database
wp db query "DELETE FROM wp_dbpm_subscribers WHERE email='$EMAIL'"

# Logs (anonymize)
sed -i "s/$EMAIL/[REDACTED]/g" /home/dave/skippy/logs/**/*.log

# Flamingo (contact forms)
wp post delete $(wp post list --post_type=flamingo_inbound --format=ids --meta_key=_field_email --meta_value="$EMAIL") --force

# Log deletion
echo "[$(date)] Deleted data for: $EMAIL" >> /home/dave/skippy/logs/privacy/deletions.log
```

### Right to Portability
**Request:** "Give me my data in machine-readable format"
**Response Time:** 30 days
**Format:** JSON or CSV

### Right to Rectification
**Request:** "Correct my data"
**Response Time:** 30 days
**Process:** Update in all systems, confirm

### Right to Restrict Processing
**Request:** "Stop using my data"
**Process:** Mark account as restricted, stop communications

---

## Data Storage & Security

### Encryption

**At Rest:**
- Database: Encrypted filesystem
- Backups: GPG encrypted
- Secrets: encrypted via secrets_manager

**In Transit:**
- HTTPS for all website traffic
- TLS for email
- Secure API connections

### Access Control

**Who Can Access PII:**
- Campaign manager (full access)
- Volunteer coordinator (volunteer data only)
- Finance team (donor data only)
- IT admin (technical access, logged)

**Access Logging:**
```bash
# Log all PII access
echo "[$(date)] $USER accessed PII: $RESOURCE" >> /home/dave/skippy/logs/security/pii_access.log
```

### Secure Deletion

**When Deleting Sensitive Data:**
```bash
# Secure deletion
shred -vfz -n 3 /path/to/sensitive/file

# Database deletion with logging
wp db query "DELETE FROM table WHERE condition"
echo "[$(date)] Deleted records: $condition" >> /home/dave/skippy/logs/privacy/deletions.log
```

---

## Retention Policy

**Active Supporters/Volunteers:**
- Retain while relationship is active
- Annual opt-in confirmation

**Inactive Contacts:**
- Email: 2 years of inactivity → delete
- Volunteers: 1 year of inactivity → archive, 3 years → delete
- Donors: Per legal requirements (typically 3-7 years)

**Legal/Compliance Data:**
- Campaign finance: Per federal/state law
- Tax records: 7 years
- Legal holds: Indefinite until released

---

## Third-Party Data Sharing

### Approved Vendors
- Email service (Mailchimp/similar)
- Payment processor (Stripe/ActBlue)
- Analytics (Google Analytics with IP anonymization)
- Hosting provider

**Requirements:**
- Data Processing Agreement (DPA)
- GDPR/CCPA compliant
- Security certification
- Limited to necessary data only

### Prohibited Sharing
- ❌ Selling email lists
- ❌ Sharing with unauthorized third parties
- ❌ Cross-campaign sharing without consent
- ❌ Public disclosure of donor info (except as legally required)

---

## Data Breach Response

### If Breach Detected

**Immediate (within 1 hour):**
1. Contain breach (isolate systems)
2. Assess scope (what data, how many people)
3. Preserve evidence
4. Follow Incident Response Protocol

**Within 24 hours:**
1. Notify campaign manager and legal team
2. Begin investigation
3. Document everything

**Within 72 hours (GDPR requirement):**
1. Notify supervisory authority if required
2. Assess notification requirements

**Notification to Affected Individuals:**
- If high risk to rights and freedoms
- Clear explanation of breach
- Steps being taken
- Recommendations for affected individuals

---

## Website & Forms

### Privacy Policy Requirements
- Clearly visible on all forms
- Link in footer of every page
- Updated within 30 days of changes
- Includes: what data, why, how long, rights, contact

### Form Best Practices
- Mark required fields clearly
- Minimize required fields
- Explain why data is needed
- Privacy policy link near submit
- Secure transmission (HTTPS)
- Confirmation message

### Cookies & Tracking
- Cookie banner/notice
- Opt-in for non-essential cookies
- Google Analytics: IP anonymization enabled
- Document what cookies are used

### Volunteer Registration
- Collect minimum necessary
- Explain data usage
- Option to opt-out of communications
- Secure storage
- Access controls

---

## Email Communications

### Requirements
- CAN-SPAM compliant
- Unsubscribe link in every email
- Process unsubscribes within 10 days
- Physical mailing address included
- Accurate "From" information

### List Management
- Separate lists for different purposes
- Honor unsubscribes immediately
- Permanent record of unsubscribes
- Don't re-add after unsubscribe
- Regular list cleanup

---

## Training Requirements

**All Team Members:**
- Privacy policy awareness
- How to handle PII
- Data breach reporting
- Social engineering awareness

**Staff with PII Access:**
- Full privacy protocol training
- Data handling procedures
- Access logging
- Annual refresher

---

## Compliance Checklist

### Monthly
- [ ] Review access logs for anomalies
- [ ] Process any data subject requests
- [ ] Update privacy documentation if needed
- [ ] Check vendor compliance

### Quarterly
- [ ] Audit PII access permissions
- [ ] Review data retention
- [ ] Clean inactive contacts
- [ ] Privacy policy review

### Annually
- [ ] Full privacy audit
- [ ] Vendor DPA renewal
- [ ] Team training refresh
- [ ] Update privacy policy if needed
- [ ] Review incident response procedures

---

## Integration with Existing Tools

### Secrets Manager
```bash
# Store credentials securely
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh set db_password

# Never store PII in secrets manager
```

### Backup & Encryption
```bash
# Encrypted backups
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh backup-wordpress
# Backups are automatically encrypted
```

---

## Contact for Privacy Issues

**Data Protection Contact:** [Name/Email]
**Privacy Requests:** privacy@rundaverun.org
**Breach Reporting:** security@rundaverun.org

---

## Related Protocols
- Data Retention Protocol
- Incident Response Protocol
- Access Control Protocol
- Secrets Rotation Protocol

---

**Version History:**
- 1.0.0 (2025-11-04): Initial protocol creation
