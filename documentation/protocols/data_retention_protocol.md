# Data Retention Protocol

**Version**: 1.0.0
**Last Updated**: 2025-11-16
**Owner**: Data Management

---

## Context

This protocol defines how long different types of data should be retained, when to archive or purge, and ensures compliance with privacy regulations. Proper data retention balances storage costs, legal requirements, and operational needs.

## Purpose

- Define retention periods for all data types
- Ensure regulatory compliance (GDPR, privacy laws)
- Manage storage efficiently
- Protect sensitive information
- Enable data recovery when needed

---

## Data Classification

### Category 1: User/Personal Data (Sensitive)
- Email addresses
- User names
- IP addresses
- Form submissions
- Newsletter signups

**Retention**: Based on user consent + legal requirements

### Category 2: Operational Data (Critical)
- Configuration files
- Database backups
- System logs
- Git repositories
- Application code

**Retention**: Long-term (1-5 years)

### Category 3: Session Data (Temporary)
- Work files (`/home/dave/skippy/work/`)
- Debug reports
- Temporary conversions
- Cache files

**Retention**: Short-term (30-90 days)

### Category 4: Archived Data (Historical)
- Old conversation summaries
- Deprecated protocols
- Historical reports
- Completed project files

**Retention**: Medium-term (1-2 years)

---

## Retention Schedule

| Data Type | Location | Active Period | Archive Period | Total Retention | Deletion |
|-----------|----------|---------------|----------------|-----------------|----------|
| Work Sessions | `/work/wordpress/` | 30 days | 90 days | 120 days | Auto |
| Conversations | `/conversations/` | 90 days | 1 year | 15 months | Manual |
| Database Backups | `/backups/` | 7 days | 30 days | 37 days | Auto |
| System Logs | `/var/log/` | 30 days | - | 30 days | Logrotate |
| Git History | `.git/` | Permanent | - | Permanent | Never |
| User Data | Database | Per consent | Per law | Varies | On request |
| API Keys | `.credentials/` | 90 days | Rotate | - | On rotation |

---

## Automated Cleanup Script

```bash
#!/bin/bash
# data_retention_cleanup_v1.0.0.sh
# Run: Weekly via cron

LOG_FILE="/home/dave/skippy/logs/retention_cleanup_$(date +%Y%m%d).log"

echo "Data Retention Cleanup - $(date)" > "$LOG_FILE"

# 1. Clean old work sessions (>120 days)
echo "Cleaning old work sessions..." >> "$LOG_FILE"
OLD_SESSIONS=$(find /home/dave/skippy/work -type d -mtime +120 2>/dev/null)
if [ -n "$OLD_SESSIONS" ]; then
    echo "Sessions to delete:" >> "$LOG_FILE"
    echo "$OLD_SESSIONS" >> "$LOG_FILE"
    find /home/dave/skippy/work -type d -mtime +120 -exec rm -rf {} \; 2>/dev/null
fi

# 2. Archive conversations older than 90 days
echo "Archiving old conversations..." >> "$LOG_FILE"
ARCHIVE_DIR="/home/dave/skippy/conversations/archive/$(date +%Y)"
mkdir -p "$ARCHIVE_DIR"

find /home/dave/skippy/conversations -maxdepth 1 -type f -name "*.md" -mtime +90 \
    -exec mv {} "$ARCHIVE_DIR/" \; 2>/dev/null

# 3. Clean old database backups (>37 days)
echo "Cleaning old database backups..." >> "$LOG_FILE"
find /home/dave/skippy/backups -type f -name "*.sql" -mtime +37 -delete 2>/dev/null

# 4. Clean temporary files older than 7 days
echo "Cleaning temporary files..." >> "$LOG_FILE"
find /tmp -user dave -type f -mtime +7 -delete 2>/dev/null

# 5. Clean old log files (>30 days)
echo "Cleaning old logs..." >> "$LOG_FILE"
find /home/dave/skippy/logs -type f -mtime +30 -delete 2>/dev/null

# Summary
echo "Cleanup complete" >> "$LOG_FILE"
df -h /home | tail -1 >> "$LOG_FILE"

echo "Log saved: $LOG_FILE"
```

---

## User Data Handling (GDPR Compliance)

### Collection Consent

When collecting user data (email signups, form submissions):

1. **Explicit consent** required
2. **Purpose stated** clearly
3. **Retention period** disclosed
4. **Rights explained** (access, deletion, portability)

### Data Subject Rights

**Right to Access**: Provide all data within 30 days
```bash
# Export user data
mysql -e "SELECT * FROM wp_subscribers WHERE email='user@example.com'" > user_data_export.csv
```

**Right to Deletion**: Remove on request
```bash
# Delete user data
mysql -e "DELETE FROM wp_subscribers WHERE email='user@example.com'"
echo "$(date): Deleted data for user@example.com" >> deletion_log.txt
```

**Right to Portability**: Export in machine-readable format
```bash
# Export as JSON
mysql -e "SELECT * FROM wp_subscribers WHERE email='user@example.com'" -B | python3 -c "import json,sys,csv; print(json.dumps(list(csv.DictReader(sys.stdin, delimiter='\t'))))"
```

### Anonymization

When retention period expires but data needed for analytics:

```bash
# Anonymize email addresses
mysql -e "UPDATE wp_submissions SET email=MD5(email), ip_address='0.0.0.0' WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR)"
```

---

## Backup Retention

### Database Backups

- **Daily**: Keep 7 days
- **Weekly**: Keep 4 weeks
- **Monthly**: Keep 12 months
- **Yearly**: Keep 5 years (archived)

```bash
# Automated backup rotation
# Daily backups
for i in {8..365}; do
    find /home/dave/skippy/backups/daily -name "*_$(date -d "$i days ago" +%Y%m%d)*" -delete
done

# Keep weekly (every Sunday)
# Keep monthly (first of month)
```

### Configuration Backups

- WordPress: Before each plugin update
- System: Before major changes
- Application: On every significant change

---

## Archive Structure

```
/home/dave/skippy/conversations/archive/
├── 2024/
│   ├── Q1/
│   ├── Q2/
│   ├── Q3/
│   └── Q4/
└── 2025/
    ├── Q1/
    ├── Q2/
    ├── Q3/
    └── Q4/

/home/dave/skippy/backups/archive/
├── databases/
│   └── monthly/
└── configurations/
    └── system/
```

---

## Data Purge Procedures

### Secure Deletion

```bash
# For sensitive data, use secure delete
shred -vfz -n 3 sensitive_file.txt

# For directories
find /path/to/sensitive -type f -exec shred -vfz {} \;
rm -rf /path/to/sensitive
```

### Verification

```bash
# Verify data is truly deleted
ls -la /path/to/deleted/file  # Should return "No such file"

# Check database
mysql -e "SELECT COUNT(*) FROM table WHERE condition"  # Should return 0
```

### Documentation

```bash
# Log all deletions
echo "$(date): Deleted [description] - Reason: [retention policy/user request]" >> /home/dave/skippy/logs/deletion_audit.log
```

---

## Storage Monitoring

### Disk Usage Alerts

```bash
# Check storage consumption by category
echo "Work files: $(du -sh /home/dave/skippy/work | cut -f1)"
echo "Conversations: $(du -sh /home/dave/skippy/conversations | cut -f1)"
echo "Backups: $(du -sh /home/dave/skippy/backups | cut -f1)"
echo "Total skippy: $(du -sh /home/dave/skippy | cut -f1)"
```

### Growth Trends

```bash
# Track growth over time
DATE=$(date +%Y%m%d)
SIZE=$(du -s /home/dave/skippy | cut -f1)
echo "$DATE,$SIZE" >> /home/dave/skippy/logs/storage_growth.csv
```

---

## Legal Hold

When data must be preserved for legal reasons:

```bash
# Mark data as "legal hold" - DO NOT DELETE
touch /home/dave/skippy/work/session_dir/.legal_hold

# Exclude from cleanup
find /home/dave/skippy/work -name ".legal_hold" -exec dirname {} \;
# These directories are exempt from automated cleanup
```

---

## Exception Handling

### Extend Retention

```bash
# If data needs to be kept longer
touch /home/dave/skippy/work/session_dir/.extend_retention_YYYYMMDD

# Modify cleanup script to check for this marker
```

### Early Deletion

```bash
# If data needs immediate removal
rm -rf /path/to/data
echo "$(date): Early deletion - Reason: [reason]" >> deletion_audit.log
```

---

## Audit Trail

### What to Log

- Date/time of deletion
- What was deleted
- Why (policy, user request, legal requirement)
- Who initiated (automated vs manual)
- Verification of completion

### Sample Audit Entry

```
2025-11-16 03:30:00 | AUTO | DELETED | /work/wordpress/20250801_session | 120-day retention expired | Verified: file removed
2025-11-16 04:15:00 | MANUAL | DELETED | user@example.com | GDPR deletion request | Verified: database record removed
```

---

## Quick Reference

```bash
# Check retention status
find /home/dave/skippy/work -type d -mtime +30  # Sessions over 30 days
find /home/dave/skippy/conversations -type f -mtime +90  # Conversations over 90 days

# Cleanup now
bash /home/dave/skippy/scripts/system/data_retention_cleanup_v1.0.0.sh

# Archive old files
mv /home/dave/skippy/conversations/old_*.md /home/dave/skippy/conversations/archive/2025/

# Check storage
df -h /home
du -sh /home/dave/skippy/*
```

---

## Integration with Other Protocols

- **Privacy Protocol**: User data handling
- **Backup Protocol**: Backup retention schedules
- **Incident Response**: Legal hold procedures
- **Compliance Protocol**: Regulatory requirements

---

**Generated**: 2025-11-16
**Status**: Active
**Next Review**: 2025-12-16
