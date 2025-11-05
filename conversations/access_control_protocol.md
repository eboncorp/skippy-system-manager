# Access Control Protocol

**Version:** 1.1.0
**Last Updated:** 2025-11-05
**Owner:** Security Team
**Status:** Active

---

## Purpose

Define who can access what systems, how access is granted/revoked, and how access is monitored to maintain security while enabling team productivity.

**Focus:** System access (accounts, passwords, SSH keys, database credentials)
**Complement:** See authorization_protocol for action-level permissions (destructive operations)

## Scope

All systems and resources including:
- WordPress admin access
- Database access
- Server/hosting access
- Code repositories
- Secrets manager
- Monitoring tools
- Third-party services

---

## Access Levels

### Level 1: View Only
**Permissions:** Read-only access, no modifications
**Examples:**
- View WordPress pages
- Read documentation
- View monitoring dashboards
- Read code repositories

**Who:** Volunteers, content reviewers, observers

### Level 2: Standard User
**Permissions:** Create/edit assigned content, use approved tools
**Examples:**
- Create/edit blog posts
- Update assigned pages
- Run approved scripts
- Submit code changes

**Who:** Content creators, developers, standard staff

### Level 3: Editor/Manager
**Permissions:** Publish content, manage users in their domain
**Examples:**
- Publish/unpublish content
- Manage content team
- Approve changes
- Configure plugins (limited)

**Who:** Content manager, team leads

### Level 4: Administrator
**Permissions:** Full system access, can grant access to others
**Examples:**
- WordPress admin
- Database admin
- Server access
- Secrets manager
- Deploy code

**Who:** Technical lead, campaign manager, IT admin

### Level 5: Root/Super Admin
**Permissions:** Unrestricted access, can break things
**Examples:**
- Root server access
- Production database direct access
- Delete operations
- Security configuration

**Who:** Very limited (1-2 people)

---

## Access Request Process

### 1. Request Submission
**Requester provides:**
- What access is needed
- Why it's needed
- How long it's needed
- Justification for access level

**Request Methods:**
- Email to: access-requests@rundaverun.org
- Ticket system
- Direct request to manager

### 2. Approval
**Approval Requirements:**
| Access Level | Approver Required |
|--------------|-------------------|
| View Only | Team Lead |
| Standard User | Team Lead |
| Editor/Manager | Campaign Manager |
| Administrator | Campaign Manager + IT Lead |
| Root/Super Admin | Campaign Manager Only |

**Approval Timeline:** 24-48 hours for normal requests, same-day for urgent

### 3. Provisioning
**IT Admin:**
- Create accounts
- Assign permissions
- Document access in register
- Send credentials via secure method
- Provide onboarding documentation

**Timeline:** Within 24 hours of approval

### 4. Verification
**New User:**
- Confirm access works
- Acknowledge responsibilities
- Complete required training
- Sign acceptable use policy

---

## Access Granting Procedures

### WordPress Access
```bash
# Create new user
wp user create username email@example.com --role=editor --user_pass="$(openssl rand -base64 16)"

# Roles:
# - subscriber (view only)
# - contributor (can write, can't publish)
# - author (can publish own posts)
# - editor (can publish all posts, manage content)
# - administrator (full WordPress access)

# Send credentials via secure channel
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh set wordpress_user_username
```

### Database Access
```bash
# Create read-only user
mysql -u root -p <<EOF
CREATE USER 'readonly'@'localhost' IDENTIFIED BY '${PASSWORD}';
GRANT SELECT ON wordpress_db.* TO 'readonly'@'localhost';
FLUSH PRIVILEGES;
EOF

# Create standard user (read/write, no structure changes)
mysql -u root -p <<EOF
CREATE USER 'wpuser'@'localhost' IDENTIFIED BY '${PASSWORD}';
GRANT SELECT, INSERT, UPDATE, DELETE ON wordpress_db.* TO 'wpuser'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### SSH Access
```bash
# Add user to server
sudo adduser username

# Add SSH public key
sudo mkdir -p /home/username/.ssh
sudo bash -c 'echo "ssh-ed25519 AAAA..." >> /home/username/.ssh/authorized_keys'
sudo chown -R username:username /home/username/.ssh
sudo chmod 700 /home/username/.ssh
sudo chmod 600 /home/username/.ssh/authorized_keys

# Grant sudo if admin level
sudo usermod -aG sudo username
```

### Git Repository Access
```bash
# Add collaborator to GitHub repo
# Via GitHub web interface or gh CLI:
gh repo add-collaborator owner/repo username --permission=push

# Permissions:
# - pull (read only)
# - push (read/write)
# - admin (full access)
```

---

## Access Revocation

### When to Revoke

**Immediate Revocation:**
- Employee/volunteer departure
- Security incident involving user
- Policy violation
- Role change (reduce access)
- Contractor contract end

**Scheduled Revocation:**
- Temporary access expiration
- Quarterly access review cleanup
- Unused accounts (90 days inactive)

### Revocation Process

**Within 1 hour of departure/incident:**
- [ ] Disable all accounts
- [ ] Change shared passwords they knew
- [ ] Revoke SSH keys
- [ ] Remove from GitHub/repos
- [ ] Remove from email lists
- [ ] Collect equipment/credentials

**Within 24 hours:**
- [ ] Audit what they had access to
- [ ] Check for suspicious activity before departure
- [ ] Document revocation
- [ ] Update access register

### Revocation Commands

**WordPress:**
```bash
# Delete user (reassign content)
wp user delete username --reassign=admin_id

# Or just disable (keep content)
wp user update username --role=subscriber
# Then manually disable login
```

**Database:**
```bash
mysql -u root -p <<EOF
DROP USER 'username'@'localhost';
FLUSH PRIVILEGES;
EOF
```

**SSH:**
```bash
# Remove user
sudo userdel -r username

# Or just disable
sudo usermod --expiredate 1 username
```

**GitHub:**
```bash
gh repo remove-collaborator owner/repo username
```

---

## Access Register

### Maintain Access Log

**Location:** `/home/dave/skippy/logs/security/access_register.csv`

**Format:**
```csv
Username,System,Access_Level,Granted_Date,Granted_By,Expires,Status
jdoe,WordPress,Editor,2025-11-04,admin,2026-11-04,active
jsmith,Database,ReadOnly,2025-11-04,admin,2025-12-04,active
```

### Register Updates

**Update when:**
- Access granted
- Access revoked
- Access level changed
- Temporary access expires
- User role changes

### Quarterly Review

**Every 90 days:**
- Review all active access
- Verify access still needed
- Check for unused accounts
- Remove expired access
- Update documentation

**Review Checklist:**
- [ ] Export current access register
- [ ] Review each entry
- [ ] Confirm with managers access still needed
- [ ] Revoke unnecessary access
- [ ] Document review completion
- [ ] Update access register

---

## Shared Credentials

### When Shared Credentials Necessary

**Acceptable:**
- Service accounts (monitoring, backups)
- Emergency admin access (documented, limited)
- System accounts (web server, database)

**Not Acceptable:**
- Personal account sharing
- Password sharing between people
- Forwarding credentials via email

### Shared Credential Management

**Requirements:**
- Store in secrets manager only
- Change immediately if person leaves who knew it
- Audit log all access
- Rotate regularly (per Secrets Rotation Protocol)
- Limit who knows them (document who)

**Tracking:**
```markdown
## Shared Credential: WordPress Emergency Admin

**Purpose:** Emergency WordPress access when individual accounts don't work
**Stored:** secrets_manager (key: wordpress_emergency)
**Who Knows:**
- Campaign Manager
- IT Lead
- On-call engineer (current)

**Usage:** Only in emergency, access logged
**Last Rotated:** 2025-11-04
**Next Rotation:** 2026-02-04
```

---

## Principle of Least Privilege

### Implementation

**Always:**
- Grant minimum access needed
- Use most restrictive role possible
- Time-limit temporary access
- Require re-approval for renewals
- Escalate privileges only when needed

**Examples:**

**Good:**
- Content creator gets "Author" role (can publish own posts)
- Developer gets read-only database access for troubleshooting
- Volunteer gets "Subscriber" role to view content

**Bad:**
- Content creator gets "Administrator" because it's easier
- Everyone gets database admin access
- All staff get root access "just in case"

---

## Monitoring Access

### Access Logging

**What to Log:**
- Login attempts (success/failure)
- Administrative actions
- Permission changes
- File modifications
- Database queries (if sensitive)

**Logs Location:**
- WordPress: `/home/dave/skippy/logs/security/wordpress_access.log`
- SSH: `/var/log/auth.log`
- Database: MySQL general log (if enabled)
- Application: `/home/dave/skippy/logs/security/audit_trail.log`

### Automated Monitoring

```bash
# Monitor failed logins
grep "Failed" /var/log/auth.log | tail -20

# Monitor WordPress admin actions
wp user list --role=administrator

# Check who accessed secrets
grep "Retrieved secret" /home/dave/skippy/logs/security/audit_trail.log
```

### Alerts

**Alert on:**
- Multiple failed login attempts (>5 in 10 min)
- New admin account created
- Permission changes
- Access from unusual location/time
- Shared credential usage

---

## Emergency Access

### Break-Glass Access

**Purpose:** Emergency access when normal access unavailable

**Procedure:**
1. Verify true emergency
2. Get verbal approval from campaign manager
3. Use emergency credentials from secrets manager
4. Document usage immediately
5. Complete post-incident review
6. Rotate emergency credentials

**Emergency Access Log:**
```csv
Date,User,Reason,Approved_By,Actions_Taken,Duration
2025-11-04,jdoe,Site_Down_Prod_Admin_Unavailable,Campaign_Mgr,Restored_Site,30min
```

---

## Service Accounts

### Creating Service Accounts

**Purpose:** Automated tasks (backups, monitoring, deployments)

**Naming Convention:** `svc-[purpose]` (e.g., `svc-backup`, `svc-monitor`)

**Requirements:**
- Strong random password (32+ characters)
- Stored in secrets manager
- Limited permissions (only what's needed)
- No interactive login
- Regular rotation

**Example:**
```bash
# Create monitoring service account
wp user create svc-monitor monitor@rundaverun.local \
    --role=subscriber \
    --user_pass="$(openssl rand -base64 32)"

# Grant only needed capabilities
# [Configure specific permissions]
```

---

## Third-Party Access

### Vendor/Consultant Access

**Requirements:**
- Signed NDA
- Time-limited access
- Specific scope documented
- Activity monitored
- Access revoked when contract ends

**Process:**
1. Contract signed with access terms
2. Create temporary account
3. Set expiration date
4. Monitor activity
5. Require status updates
6. Revoke on completion
7. Audit their activities

---

## Training Requirements

**All Users Must:**
- Complete security awareness training
- Sign acceptable use policy
- Understand their access level
- Know how to report security issues

**Admins Must Also:**
- Complete advanced security training
- Understand access control principles
- Know revocation procedures
- Practice least privilege

---

## Integration with Existing Protocols

- **Authorization Protocol:** General authorization procedures
- **Secrets Rotation Protocol:** Managing credentials
- **Data Privacy Protocol:** PII access controls
- **Incident Response Protocol:** Security incidents

---

## Related Tools

- secrets_manager_v1.0.0.sh - Credential storage
- Authorization checks in scripts
- Audit logging throughout system

---

**Version History:**
- 1.0.0 (2025-11-04): Initial protocol creation
