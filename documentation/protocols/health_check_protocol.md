# Health Check Protocol

**Version**: 1.0.0
**Last Updated**: 2025-11-16
**Owner**: System Administration

---

## Context

This protocol defines systematic health monitoring for the Skippy system, ensuring proactive identification of issues before they become critical failures.

## Purpose

- Detect system degradation early
- Prevent data loss from disk space issues
- Ensure service availability
- Maintain database integrity
- Monitor resource utilization

---

## Health Check Categories

### 1. System Resources
- Disk space usage (alert at 80%, critical at 90%)
- Memory utilization
- CPU load average
- Swap usage

### 2. Service Health
- WordPress site accessibility
- Database connectivity
- Local by Flywheel status
- Git repository integrity

### 3. Data Integrity
- Backup freshness (not older than 24 hours)
- Database consistency
- File permission correctness
- Log file rotation

### 4. Security Health
- Failed login attempts
- Firewall status
- SSL certificate expiration
- Unauthorized file changes

---

## Automated Health Check Script

```bash
#!/bin/bash
# health_check_v1.0.0.sh
# Run: Daily via cron or manually

ALERT_THRESHOLD=80
CRITICAL_THRESHOLD=90
REPORT_FILE="/home/dave/skippy/conversations/health_check_$(date +%Y%m%d_%H%M%S).md"

echo "# System Health Check Report" > "$REPORT_FILE"
echo "**Date:** $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 1. Disk Space Check
echo "## Disk Space" >> "$REPORT_FILE"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -ge "$CRITICAL_THRESHOLD" ]; then
    echo "- **CRITICAL**: Root filesystem at ${DISK_USAGE}% (>90%)" >> "$REPORT_FILE"
elif [ "$DISK_USAGE" -ge "$ALERT_THRESHOLD" ]; then
    echo "- **WARNING**: Root filesystem at ${DISK_USAGE}% (>80%)" >> "$REPORT_FILE"
else
    echo "- OK: Root filesystem at ${DISK_USAGE}%" >> "$REPORT_FILE"
fi

# Check skippy directory specifically
SKIPPY_SIZE=$(du -sh /home/dave/skippy 2>/dev/null | cut -f1)
echo "- Skippy directory size: $SKIPPY_SIZE" >> "$REPORT_FILE"

# 2. Memory Check
echo "" >> "$REPORT_FILE"
echo "## Memory Usage" >> "$REPORT_FILE"
MEM_PERCENT=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
SWAP_PERCENT=$(free | awk '/Swap:/ {if($2>0) printf "%.0f", $3/$2 * 100; else print "0"}')
echo "- Memory: ${MEM_PERCENT}% used" >> "$REPORT_FILE"
echo "- Swap: ${SWAP_PERCENT}% used" >> "$REPORT_FILE"

# 3. Service Checks
echo "" >> "$REPORT_FILE"
echo "## Service Status" >> "$REPORT_FILE"

# WordPress Local Site
if curl -s -I "http://rundaverun-local-complete-022655.local/" 2>/dev/null | grep -q "HTTP/1.1 200"; then
    echo "- WordPress Local: ONLINE" >> "$REPORT_FILE"
else
    echo "- **WARNING**: WordPress Local: OFFLINE or UNREACHABLE" >> "$REPORT_FILE"
fi

# MySQL (Local by Flywheel)
if [ -S "/home/dave/.config/Local/run/EnByKrjFn/mysql/mysqld.sock" ]; then
    echo "- MySQL Socket: EXISTS" >> "$REPORT_FILE"
else
    echo "- **WARNING**: MySQL Socket: NOT FOUND" >> "$REPORT_FILE"
fi

# Git Repository Health
echo "" >> "$REPORT_FILE"
echo "## Git Repository Health" >> "$REPORT_FILE"
cd /home/dave/skippy
if git fsck --quiet 2>/dev/null; then
    echo "- Git integrity: OK" >> "$REPORT_FILE"
else
    echo "- **WARNING**: Git integrity check failed" >> "$REPORT_FILE"
fi

UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l)
echo "- Uncommitted changes: $UNCOMMITTED files" >> "$REPORT_FILE"

# 4. Backup Freshness
echo "" >> "$REPORT_FILE"
echo "## Backup Status" >> "$REPORT_FILE"
LATEST_BACKUP=$(ls -t /home/dave/skippy/work/wordpress/rundaverun-local/ 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    echo "- Latest WordPress backup: $LATEST_BACKUP" >> "$REPORT_FILE"
else
    echo "- **WARNING**: No WordPress backups found" >> "$REPORT_FILE"
fi

# 5. Security Checks
echo "" >> "$REPORT_FILE"
echo "## Security Status" >> "$REPORT_FILE"

# UFW Status
if sudo ufw status 2>/dev/null | grep -q "Status: active"; then
    echo "- Firewall: ACTIVE" >> "$REPORT_FILE"
else
    echo "- **WARNING**: Firewall: INACTIVE" >> "$REPORT_FILE"
fi

# Failed SSH attempts (last 24 hours)
FAILED_SSH=$(journalctl -u sshd --since "24 hours ago" 2>/dev/null | grep -c "Failed password" || echo "0")
if [ "$FAILED_SSH" -gt 10 ]; then
    echo "- **WARNING**: $FAILED_SSH failed SSH attempts in 24h" >> "$REPORT_FILE"
else
    echo "- Failed SSH attempts (24h): $FAILED_SSH" >> "$REPORT_FILE"
fi

# 6. Log Analysis
echo "" >> "$REPORT_FILE"
echo "## Log Analysis" >> "$REPORT_FILE"
ERROR_COUNT=$(grep -c "ERROR\|CRITICAL\|FATAL" /var/log/syslog 2>/dev/null || echo "0")
echo "- System log errors: $ERROR_COUNT" >> "$REPORT_FILE"

# Summary
echo "" >> "$REPORT_FILE"
echo "## Summary" >> "$REPORT_FILE"
if grep -q "CRITICAL\|WARNING" "$REPORT_FILE"; then
    echo "**STATUS: NEEDS ATTENTION**" >> "$REPORT_FILE"
else
    echo "**STATUS: HEALTHY**" >> "$REPORT_FILE"
fi

echo "Report saved to: $REPORT_FILE"
```

---

## Scheduled Health Checks

### Daily (Automated)
- Disk space monitoring
- Service availability
- Backup verification
- Security log review

### Weekly (Manual Review)
- Database optimization check
- Performance metrics analysis
- Dependency vulnerability scan
- Git repository cleanup

### Monthly (Comprehensive)
- Full system audit
- Protocol compliance review
- Documentation currency check
- Security policy review

---

## Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Disk Space | 80% | 90% | Clean old files |
| Memory | 85% | 95% | Restart services |
| CPU Load | 70% (5min avg) | 90% | Investigate processes |
| Swap Usage | 50% | 80% | Add RAM or optimize |
| Failed SSH | 10/day | 50/day | Block IPs |
| DB Size | 500MB | 1GB | Optimize/archive |

---

## Response Actions

### Disk Space Critical (>90%)
```bash
# 1. Find large files
find /home/dave/skippy -type f -size +100M -exec ls -lh {} \;

# 2. Clean old work sessions (>30 days)
find /home/dave/skippy/work -type d -mtime +30 -exec rm -rf {} \;

# 3. Remove old conversation files (>90 days)
find /home/dave/skippy/conversations -type f -mtime +90 -delete

# 4. Clean package caches
sudo apt clean
pip cache purge
```

### Service Offline
```bash
# 1. Check Local by Flywheel app
ps aux | grep Local

# 2. Restart WordPress site
# Open Local app and restart site

# 3. Test connectivity
curl -I http://rundaverun-local-complete-022655.local/
```

### Database Issues
```bash
# 1. Check MySQL process
ps aux | grep mysql

# 2. Verify socket
ls -la /home/dave/.config/Local/run/*/mysql/mysqld.sock

# 3. Test connection
mysql -u root --password=root --socket=/path/to/socket local -e "SELECT 1;"
```

---

## Health Check Cron Setup

```bash
# Add to crontab (crontab -e)
# Daily health check at 6 AM
0 6 * * * /home/dave/skippy/scripts/system/health_check_v1.0.0.sh

# Weekly comprehensive check on Sunday at 3 AM
0 3 * * 0 /home/dave/skippy/scripts/system/weekly_audit_v1.0.0.sh
```

---

## Quick Health Check (Manual)

```bash
# One-liner health snapshot
echo "Disk: $(df -h / | awk 'NR==2 {print $5}') | Mem: $(free | awk '/Mem:/ {printf "%.0f%%", $3/$2*100}') | Load: $(uptime | awk -F'average:' '{print $2}' | cut -d',' -f1) | Services: $(systemctl is-system-running)"
```

---

## Integration with Other Protocols

- **Error Recovery Protocol**: Trigger health check after errors
- **Incident Response Protocol**: Health check part of incident triage
- **Backup Protocol**: Verify backup health weekly
- **Update Protocol**: Health check before and after updates

---

## Best Practices

### DO:
- Run health checks before major operations
- Keep 7 days of health reports
- Investigate any warning immediately
- Document recurring issues

### DON'T:
- Ignore warning thresholds
- Skip scheduled checks
- Delete health reports without review
- Assume services are running

---

## Quick Reference

```bash
# Manual health check
bash /home/dave/skippy/scripts/system/health_check_v1.0.0.sh

# View latest report
cat /home/dave/skippy/conversations/health_check_*.md | tail -100

# Quick disk check
df -h / /home

# Service status
systemctl is-system-running
```

---

**Generated**: 2025-11-16
**Status**: Active
**Next Review**: 2025-12-16
