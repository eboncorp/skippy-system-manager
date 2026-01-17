# Deployment Workflow

**Version:** 1.0.0
**Last Updated:** 2026-01-17

---

## Overview

Standard workflow for deploying changes to production WordPress site (rundaverun.org).

---

## Pre-Deployment Checklist

- [ ] All changes tested locally
- [ ] Database backup created
- [ ] Files backup created
- [ ] No broken links
- [ ] Campaign facts verified
- [ ] Security scan passed

---

## Step 1: Create Deployment Session

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_deploy"
mkdir -p "$SESSION_DIR"
```

---

## Step 2: Pre-Deployment Backup

### Local Backup
```bash
wp db export "$SESSION_DIR/local_db_before.sql" --allow-root
```

### Production Backup (via SSH)
```bash
SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun \
  git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com \
  'cd html && wp db export /tmp/prod_backup_$(date +%Y%m%d).sql --allow-root'
```

---

## Step 3: Run Pre-Deployment Validator

```bash
# Check for common issues
bash ~/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh
```

---

## Step 4: Deploy Changes

### Content Update (Single Page)
```bash
# Get local content
wp post get {ID} --field=post_content > "$SESSION_DIR/content_to_deploy.html"

# Copy to production
SSH_AUTH_SOCK="" scp -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun \
  "$SESSION_DIR/content_to_deploy.html" \
  git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com:/tmp/

# Apply on production
SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun \
  git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com \
  'cd html && wp post update {ID} --post_content="$(cat /tmp/content_to_deploy.html)" --allow-root'
```

### Plugin/Theme Update
```bash
SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun \
  git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com \
  'cd html && wp plugin update {plugin-name} --allow-root'
```

---

## Step 5: Flush Caches

**ALWAYS run after deployment:**
```bash
SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun \
  git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com \
  'cd html && wp cache flush --allow-root && wp transient delete --all --allow-root && wp rewrite flush --allow-root'
```

May also need manual CDN purge from GoDaddy hosting panel.

---

## Step 6: Verify Deployment

### HTTP Status Check
```bash
curl -I https://rundaverun.org | grep "200 OK"
```

### Content Verification
```bash
# Fetch deployed content
curl -s https://rundaverun.org/page-slug/ > "$SESSION_DIR/deployed_content.html"

# Check for expected text
grep "expected text" "$SESSION_DIR/deployed_content.html"
```

### Health Check
```bash
SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun \
  git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com \
  'cd html && wp health-check --allow-root'
```

---

## Step 7: Document Deployment

```bash
cat > "$SESSION_DIR/README.md" <<EOF
# Deployment: $(date +%Y-%m-%d)

**Status:** ✅ Completed

## Changes Deployed
- [List changes]

## Verification
- HTTP 200: ✅
- Content verified: ✅
- Health check: ✅

## Rollback
\`\`\`bash
# Restore from backup
wp db import $SESSION_DIR/prod_backup_*.sql --allow-root
\`\`\`
EOF
```

---

## Rollback Procedure

If issues detected after deployment:

```bash
# 1. Restore database
SSH_AUTH_SOCK="" ssh ... \
  'cd html && wp db import /tmp/prod_backup_*.sql --allow-root'

# 2. Flush caches
SSH_AUTH_SOCK="" ssh ... \
  'cd html && wp cache flush --allow-root'

# 3. Verify rollback
curl -I https://rundaverun.org | grep "200 OK"
```

---

## Related

- Backup Workflow
- Emergency Recovery Workflow
- WordPress Update Workflow
