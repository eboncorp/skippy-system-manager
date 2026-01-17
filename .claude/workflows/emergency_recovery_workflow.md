# Emergency Recovery Workflow

**Version:** 1.0.0
**Last Updated:** 2026-01-17

---

## Overview

Emergency procedures for recovering from critical failures affecting the WordPress site or Skippy system.

---

## Quick Decision Tree

```
Is the site loading?
├─ YES → Content issue
│   └─ Go to: Content Recovery
└─ NO → Site broken
    ├─ PHP errors → Go to: PHP Recovery
    ├─ Database errors → Go to: Database Recovery
    └─ Server unreachable → Go to: Server Recovery
```

---

## Scenario 1: Content Recovery

**Symptoms:** Site loads but content is wrong/missing

### Step 1: Find Session Backup
```bash
# List recent sessions with backups
ls -lt /home/dave/skippy/work/wordpress/*/ | head -10

# Find specific page backup
find /home/dave/skippy/work/wordpress/ -name "page_*_before.html" | sort -r | head -5
```

### Step 2: Restore Content
```bash
# From local WP
wp post update {ID} --post_content="$(cat "$SESSION_DIR/page_{ID}_before.html")" --allow-root

# From production (via SSH)
SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes \
  -i ~/.ssh/godaddy_rundaverun \
  git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com \
  'cd html && wp post update {ID} --post_content="$(cat /tmp/restored_content.html)" --allow-root'
```

### Step 3: Verify
```bash
wp post get {ID} --field=post_content > "$SESSION_DIR/page_{ID}_after_recovery.html"
diff "$SESSION_DIR/page_{ID}_before.html" "$SESSION_DIR/page_{ID}_after_recovery.html"
```

---

## Scenario 2: PHP Recovery

**Symptoms:** White screen, PHP errors, 500 errors

### Step 1: Check Error Logs
```bash
# Local
tail -50 ~/html/wp-content/debug.log

# Production
SSH_AUTH_SOCK="" ssh ... 'tail -50 html/wp-content/debug.log'
```

### Step 2: Deactivate Plugins
```bash
# Deactivate all
wp plugin deactivate --all --allow-root

# Or specific plugin
wp plugin deactivate {suspect-plugin} --allow-root
```

### Step 3: Restore Plugin
```bash
# Reactivate one by one
wp plugin activate {plugin-name} --allow-root

# If plugin file corrupted, reinstall
wp plugin install {plugin-name} --force --allow-root
```

### Step 4: Clear Caches
```bash
wp cache flush --allow-root
wp rewrite flush --allow-root
```

---

## Scenario 3: Database Recovery

**Symptoms:** Database connection errors, corrupted data

### Step 1: Emergency Backup Current State
```bash
wp db export "/home/dave/skippy/emergency_$(date +%Y%m%d_%H%M%S).sql" --allow-root 2>/dev/null || echo "DB export failed"
```

### Step 2: Find Recent Backup
```bash
find /home/dave/skippy/work/wordpress/ -name "db_backup*.sql.gz" | sort -r | head -5
```

### Step 3: Restore Database
```bash
# Decompress if needed
gunzip -k backup.sql.gz

# Import
wp db import backup.sql --allow-root

# Flush caches
wp cache flush --allow-root
wp transient delete --all --allow-root
wp rewrite flush --allow-root
```

### Step 4: Verify
```bash
wp db check --allow-root
wp post list --post_type=page --allow-root
```

---

## Scenario 4: Server Recovery

**Symptoms:** Cannot reach server, SSH timeout

### For Ebon Server
```bash
# Check if server is responding
ping -c 3 10.0.0.29

# Check SSH
timeout 15 ssh -o ConnectTimeout=5 ebon@10.0.0.29 "echo 'Server responding'"

# Check Docker containers
timeout 15 ssh ebon@10.0.0.29 "docker ps"
```

### For GoDaddy Production
```bash
# Check if site is up from external
curl -I https://rundaverun.org

# Try SSH connection
SSH_AUTH_SOCK="" ssh -o ConnectTimeout=10 ... 'echo "Connected"'
```

If server completely unreachable:
1. Check hosting provider status page
2. Contact hosting support
3. Wait for infrastructure team if internal server

---

## Post-Recovery Checklist

- [ ] Root cause identified
- [ ] Recovery steps documented
- [ ] Backup verified current
- [ ] Monitoring alerts checked
- [ ] Team notified if production impact

---

## Emergency Contacts

| Issue | Contact |
|-------|---------|
| GoDaddy hosting | GoDaddy support |
| Internal server | Check #infrastructure |
| Database | Check backups first |

---

## Prevention

1. **Always backup before changes**
2. **Use session directories**
3. **Test locally first**
4. **Keep multiple backup generations**
5. **Document all changes**

---

## Related

- Backup Workflow
- Deployment Workflow
- WordPress Update Workflow
