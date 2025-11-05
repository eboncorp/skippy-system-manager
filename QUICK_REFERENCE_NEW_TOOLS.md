# Quick Reference: New Tools

**Created:** November 4, 2025
**Total New Tools:** 3 production-ready scripts

---

## 1. WordPress Pre-Deployment Validator ⭐ HIGHEST PRIORITY

**Purpose:** Catch errors BEFORE they go live
**Location:** `/home/dave/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh`
**When to Run:** Before EVERY deployment

### Quick Start
```bash
cd "/home/dave/Local Sites/rundaverun-local/app/public"
/home/dave/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh
```

### What It Checks (12 validations)
- ✓ Factual content (no false firefighter claims)
- ✓ Budget consistency ($77.4M, $34.2M, $1.80 ROI, $15M)
- ✓ Broken links (zero tolerance)
- ✓ Email addresses (authorized only)
- ✓ URLs (HTTPS, no dev URLs)
- ✓ Punctuation (no triple apostrophes)
- ✓ PHP code exposure
- ✓ Shortcode placeholders
- ✓ Policy count (42)
- ✓ Privacy policy published
- ✓ No default WordPress content

### Deployment Decision
- 🔴 **BLOCKED** = Critical errors, DO NOT DEPLOY
- 🟡 **NOT RECOMMENDED** = High errors, fix first
- 🟢 **APPROVED** = Safe to deploy

### ROI
- Saves: 2-3 hours per deployment
- Prevents: Campaign-ending errors
- Payback: 2-3 uses (1 month)

---

## 2. Security Vulnerability Scanner

**Purpose:** Weekly security health check
**Location:** `/home/dave/skippy/scripts/security/vulnerability_scanner_v1.0.0.sh`
**When to Run:** Weekly (automate with cron)

### Quick Start
```bash
/home/dave/skippy/scripts/security/vulnerability_scanner_v1.0.0.sh
```

### What It Scans (8 checks)
- Python package vulnerabilities
- npm package vulnerabilities
- System security updates
- Git history for secrets
- File permissions
- Hardcoded credentials
- SSL certificates
- Docker security

### Reports
```bash
# View latest report
ls -lht /home/dave/skippy/conversations/security_reports/ | head -1
```

### Automate It
```bash
# Add to crontab
0 2 * * 0 /home/dave/skippy/scripts/security/vulnerability_scanner_v1.0.0.sh
```

---

## 3. Backup Verification Test

**Purpose:** Ensure backups actually work
**Location:** `/home/dave/skippy/scripts/backup/backup_verification_test_v1.0.0.sh`
**When to Run:** Monthly (automate with cron)

### Quick Start
```bash
/home/dave/skippy/scripts/backup/backup_verification_test_v1.0.0.sh
```

### What It Tests (7 checks)
- Latest backup exists
- File integrity
- Extraction works
- Critical files present
- Backup age acceptable
- Backup size reasonable
- Multiple backups exist

### Reports
```bash
# View latest report
ls -lht /home/dave/skippy/conversations/backup_reports/ | head -1
```

### Automate It
```bash
# Add to crontab
0 4 1 * * /home/dave/skippy/scripts/backup/backup_verification_test_v1.0.0.sh
```

---

## Critical Workflow: Pre-Deployment

```bash
# 1. Make your changes in WordPress
# ... edit content ...

# 2. Run the validator
cd "/home/dave/Local Sites/rundaverun-local/app/public"
/home/dave/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh

# 3. Check the result
# - 🔴 BLOCKED? Fix critical errors and re-run
# - 🟡 NOT RECOMMENDED? Fix high errors
# - 🟢 APPROVED? Safe to deploy!

# 4. Review the report
ls -lht /home/dave/skippy/conversations/deployment_validation_reports/ | head -1

# 5. Deploy only if APPROVED
# ... your deployment process ...

# 6. Verify deployment
# ... check live site ...
```

---

## All Cron Jobs

```bash
# Edit crontab
crontab -e

# Add these lines:
# Work files cleanup - 3:30 AM daily
30 3 * * * /home/dave/skippy/scripts/cleanup_work_files.sh

# Security scan - 2 AM Sundays
0 2 * * 0 /home/dave/skippy/scripts/security/vulnerability_scanner_v1.0.0.sh

# Backup verification - 4 AM on 1st of month
0 4 1 * * /home/dave/skippy/scripts/backup/backup_verification_test_v1.0.0.sh
```

---

## What These Tools Prevent

| Problem | Cost | Tool That Prevents It |
|---------|------|----------------------|
| False firefighter claim | Campaign ending | WordPress Validator |
| Budget inconsistencies | Credibility loss | WordPress Validator |
| Broken links | User frustration | WordPress Validator |
| Security breach | Catastrophic | Security Scanner |
| Backup failure | Data loss | Backup Verifier |
| Dev URLs in production | Embarrassment | WordPress Validator |
| Triple apostrophes | Unprofessional | WordPress Validator |

---

## Reports Location

All reports saved to: `/home/dave/skippy/conversations/`

```bash
# Security reports
ls -lh /home/dave/skippy/conversations/security_reports/

# Backup reports
ls -lh /home/dave/skippy/conversations/backup_reports/

# Deployment validation reports
ls -lh /home/dave/skippy/conversations/deployment_validation_reports/

# All reports
ls -lht /home/dave/skippy/conversations/*_reports/
```

---

## Getting Help

### Documentation
- Full session summary: `/home/dave/skippy/conversations/SESSION_SUMMARY_ENHANCEMENT_PROJECT_2025-11-04.md`
- Problem analysis: `/home/dave/skippy/conversations/PROBLEM_ANALYSIS_AND_PREVENTION_2025-11-04.md`
- Enhancement roadmap: `/home/dave/skippy/conversations/SKIPPY_IMPROVEMENT_RECOMMENDATIONS_2025-11-04.md`

### Logs
```bash
# Security scanner log
tail -f /home/dave/skippy/logs/security/scanner.log

# Backup verification log
tail -f /home/dave/skippy/logs/backup_verification/verification.log

# WordPress validator log
tail -f /home/dave/skippy/logs/deployment_validation/validator.log
```

---

**Next Steps:**
1. Test WordPress validator before next deployment
2. Review security scan results when complete
3. Run backup verification test
4. Schedule cron jobs for automation
