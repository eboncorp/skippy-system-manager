# Update and Maintenance Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

Keep systems, repositories, and dependencies up to date. This protocol defines regular maintenance schedules and procedures.

## Purpose

- Keep software current and secure
- Prevent dependency drift
- Catch issues early
- Maintain system health

---

## Update Schedule

### Daily (As Needed)
```
- Check rundaverun website health
- Review error logs
- Check disk space
- Monitor performance
```

### Weekly (Sundays)
```
- Check all repos for updates
- Run health checks
- Clean Docker
- Find duplicate files (report only)
- Review WordPress plugins for updates
```

### Monthly (1st of Month)
```
- Check Python package updates
- Check npm package updates
- Review and archive old conversation files
- Clean up work directories (>30 days)
- Verify backups
```

### Quarterly (Every 90 Days)
```
- Rotate WordPress security keys
- Review and update protocols
- Audit script inventory
- Database optimization
```

---

## Repository Updates

### Check for Updates
```bash
# User can request:
"Check for updates"
"Check all repos for updates"
"Update check"

# Claude will:
cd ~/skippy && git fetch && git status
cd ~/rundaverun && git fetch && git status
cd ~/utilities && git fetch && git status

# Report what's available
```

### Apply Updates
```bash
# For each repo with updates:
cd /repo
git pull origin master

# Or if feature branch available:
git fetch origin
git checkout feature-branch
# Review, then merge if appropriate
```

---

## WordPress Updates

### Plugin Updates
```bash
# Check for updates
wp plugin list --update=available

# Update specific plugin
wp plugin update plugin-name

# Update all (after testing in staging)
wp plugin update --all
```

### WordPress Core Updates
```bash
# Check current version
wp core version

# Check for updates
wp core check-update

# Update (after backup)
wp db export backup_pre_update.sql
wp core update
wp core update-db
```

### Theme Updates
```bash
# Check theme updates
wp theme list --update=available

# Update theme
wp theme update theme-name
```

---

## Dependency Updates

### Python Packages
```bash
# Check outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update utilities package
cd ~/utilities
pip install -e ".[web]" --upgrade
```

### System Packages
```bash
# Check for updates
sudo apt update
sudo apt list --upgradable

# Apply updates (security first)
sudo apt upgrade

# Clean up
sudo apt autoremove
sudo apt autoclean
```

---

## Maintenance Tasks

### Docker Cleanup
```bash
# Weekly or when space low
bash ~/skippy-tools/utility/docker_cleanup_v1.0.0.sh

# Expected: 1-10GB freed
```

### Duplicate File Scan
```bash
# Monthly - report only
utilities find-duplicates ~ --dry-run > ~/logs/duplicates_$(date +%Y%m%d).log

# Review report, delete manually if needed
```

### Log Rotation
```bash
# Check log sizes
du -sh ~/skippy/logs/*
du -sh ~/.local/share/utilities/logs/*

# Archive old logs
tar -czf logs_$(date +%Y%m).tar.gz ~/skippy/logs/*.log
mv logs_*.tar.gz ~/skippy/archives/
rm ~/skippy/logs/*.log
```

### Work Directory Cleanup
```bash
# Monthly - archive files > 30 days old
find ~/skippy/work -type d -mtime +30 -print
# Move to archives or delete
```

---

## Health Checks

### System Health
```bash
skippy health
skippy metrics show
```

### WordPress Health
```bash
bash ~/rundaverun/campaign/skippy-scripts/wordpress/wordpress_health_check_v1.0.0.sh
```

### Disk Space
```bash
df -h
du -sh ~/* | sort -h
```

### Service Status
```bash
systemctl status mysql
systemctl status nginx
docker ps
```

---

## Automated Maintenance

### Cron Jobs

**Weekly Maintenance (Sunday 2 AM):**
```bash
# Add to crontab:
0 2 * * 0 /home/dave/skippy/scripts/maintenance/weekly_maintenance.sh >> /home/dave/logs/weekly_maintenance.log 2>&1
```

**Monthly Cleanup (1st of Month, 3 AM):**
```bash
0 3 1 * * /home/dave/skippy/scripts/maintenance/monthly_cleanup.sh >> /home/dave/logs/monthly_cleanup.log 2>&1
```

**Daily Health Check (6 AM):**
```bash
0 6 * * * /home/dave/bin/skippy health >> /home/dave/logs/daily_health.log 2>&1
```

---

## Update Procedures

### WordPress Plugin Update Procedure
```
1. Check current state
   wp plugin list

2. Create backup
   wp db export backup_pre_plugin_update.sql

3. Update in staging first (if available)

4. Update production
   wp plugin update plugin-name

5. Test functionality
   Visit website, test features

6. Monitor for errors
   tail -f error.log

7. Rollback if issues
   wp plugin install plugin-name --version=X.X.X --force
   wp db import backup_pre_plugin_update.sql
```

### Repository Update Procedure
```
1. Check for updates
   cd /repo && git fetch

2. Review changes
   git log HEAD..origin/master

3. Check for conflicts
   git merge-base master origin/master

4. Pull/merge
   git pull origin master
   # or git merge if on feature branch

5. Test
   Run relevant tests

6. Verify
   Check functionality

7. Document
   Note what was updated
```

---

## Notification of Updates

### When Claude Finds Updates
```
User: "Check for updates"

Claude response:
"Checked all repositories:
✅ skippy-system-manager: Up to date
✅ rundaverun-website: Up to date
🔄 utilities: Update available
   - 15 commits ahead
   - New features: X, Y, Z
   - Recommendation: Review and merge

Would you like me to show details or apply updates?"
```

---

## Best Practices

### DO:
✅ Check for updates regularly
✅ Create backups before major updates
✅ Test updates in staging first (when possible)
✅ Read changelogs before updating
✅ Keep dependencies current

### DON'T:
❌ Update production without testing
❌ Skip backups before updates
❌ Ignore security updates
❌ Let dependencies get too far behind
❌ Update everything at once without testing

---

## Quick Reference

### Update Commands
```bash
# Check all repos
for repo in ~/skippy ~/rundaverun ~/utilities; do cd $repo && echo "=== $repo ===" && git fetch && git status; done

# WordPress updates
wp plugin list --update=available
wp core check-update

# Python packages
pip list --outdated

# System packages
sudo apt update && sudo apt list --upgradable

# Docker cleanup
bash ~/skippy-tools/utility/docker_cleanup_v1.0.0.sh

# Health checks
skippy health
bash ~/rundaverun/campaign/skippy-scripts/wordpress/wordpress_health_check_v1.0.0.sh
```

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
