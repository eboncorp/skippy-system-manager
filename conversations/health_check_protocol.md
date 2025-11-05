# Health Check Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Owner:** Infrastructure Team
**Status:** Active

---

## Purpose

Establish regular health monitoring procedures to proactively identify issues, maintain system reliability, and improve health scores from 75% to 90%+.

## Scope

All infrastructure components monitored by system_dashboard_v1.0.0.sh and related tools.

---

## Health Check Schedule

### Daily (Automated via Cron)
**Time:** 6:00 AM
**Tool:** `system_dashboard_v1.0.0.sh status`
**Alert if:** Health score <85%

```bash
# Cron entry
0 6 * * * /home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh status --alert-threshold=85
```

### Weekly (Manual Review)
**Time:** Monday 9:00 AM
**Tool:** `system_dashboard_v1.0.0.sh report`
**Review:** Trends, recurring issues, optimization opportunities

### Pre-Deployment (Required)
**When:** Before any production deployment
**Tool:** Full validation suite
**Requirement:** Health >90%, zero critical errors

### Post-Incident (Required)
**When:** After resolving P0/P1 incident
**Tool:** `system_dashboard_v1.0.0.sh snapshot`
**Verify:** System returned to healthy state

---

## Health Score Interpretation

### 95-100% (A+) - Excellent
**Status:** System operating optimally
**Action:** Maintain current practices

### 90-94% (A) - Very Good
**Status:** Minor improvements possible
**Action:** Monitor, address low-priority items

### 85-89% (B+) - Good
**Status:** Some attention needed
**Action:** Review warnings, plan improvements

### 80-84% (B) - Acceptable
**Status:** Issues present but manageable
**Action:** Address issues this week

### 70-79% (C) - Poor
**Status:** Significant issues
**Action:** Immediate attention required, create tickets

### <70% (D/F) - Critical
**Status:** System at risk
**Action:** Emergency response, follow Incident Response Protocol

---

## Health Check Components

### 1. System Health
**Check:**
```bash
# CPU, memory, disk usage
df -h
free -h
top -bn1 | head -5
```

**Thresholds:**
- Disk >90%: -10 points (critical)
- Disk >80%: -5 points (warning)
- Memory >90%: -5 points
- CPU avg >80%: -5 points

### 2. WordPress Health
**Check:**
```bash
cd /home/dave/Local\ Sites/rundaverun-local/app/public
wp core verify-checksums
wp plugin list --status=active
wp theme list
wp db check
```

**Issues:**
- Core file modified: -15 points
- Plugin needs update: -5 points per plugin
- Database errors: -20 points

### 3. Security Health
**Check:**
```bash
# Review security logs
tail -100 /home/dave/skippy/logs/security/audit_trail.log

# Check recent alerts
tail -50 /home/dave/skippy/logs/alerts/critical_events.log
```

**Issues:**
- Security alerts: -15 points each
- Failed login attempts >10: -5 points
- Outdated secrets: -10 points

### 4. Backup Health
**Check:**
```bash
# Check latest backup
ls -lht /home/dave/skippy/backups/ | head -5
```

**Issues:**
- No backup in 24h: -15 points (critical)
- No backup in 7 days: -25 points (critical)
- Backup failures: -10 points

### 5. Performance Health
**Check:**
```bash
# Page load times
curl -o /dev/null -s -w '%{time_total}\n' http://rundaverun.org

# Database queries
wp db query "SHOW PROCESSLIST" | wc -l
```

**Thresholds:**
- Load time >5s: -10 points
- Load time >3s: -5 points
- Slow queries >10: -5 points

---

## Action Thresholds

### Automatic Actions

**Health <90%:**
- Alert on-call engineer
- Create ticket
- Include health report

**Health <80%:**
- Alert team lead
- Urgent ticket
- Begin investigation

**Health <70%:**
- Declare P2 incident
- Immediate investigation
- Hourly status updates

**Health <60%:**
- Declare P1 incident
- All hands response
- Follow Incident Response Protocol

---

## Weekly Health Review Process

### 1. Generate Report
```bash
/home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh report --output=/home/dave/skippy/conversations/health_report_$(date +%Y%m%d).md
```

### 2. Review Trends
- Health score trend (improving/declining?)
- Recurring issues
- Component-specific problems
- Performance trends

### 3. Identify Actions
- Issues to address this week
- Optimization opportunities
- Preventive maintenance needed
- Documentation updates required

### 4. Track Progress
- Create tickets for actions
- Assign owners
- Set deadlines
- Follow up in next review

---

## Health Improvement Actions

### Quick Wins (Score +5-10)
- Update outdated plugins
- Clear caches: `wp cache flush`
- Rotate logs
- Run database optimization: `wp db optimize`

### Medium Impact (Score +10-15)
- Create first backup (if missing)
- Fix file permissions
- Address security warnings
- Optimize images

### High Impact (Score +15-25)
- Implement regular backups
- Fix critical security issues
- Resolve database problems
- Performance optimization

---

## Integration with Tools

### System Dashboard
```bash
# Quick status
/home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh status

# Detailed report
/home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh report

# JSON for automation
/home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh status --format=json
```

### Self-Maintenance
```bash
# Run health check and auto-heal
/home/dave/skippy/scripts/automation/self_maintenance_v1.0.0.sh check
/home/dave/skippy/scripts/automation/self_maintenance_v1.0.0.sh auto-heal
```

### Performance Optimizer
```bash
# Performance analysis
/home/dave/skippy/scripts/optimization/performance_optimizer_v1.0.0.sh analyze

# Optimize if needed
/home/dave/skippy/scripts/optimization/performance_optimizer_v1.0.0.sh optimize-wordpress
```

---

## Monitoring Automation

### Automated Daily Health Check Script

```bash
#!/bin/bash
# Daily health check automation

HEALTH_SCRIPT="/home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh"
ALERT_SCRIPT="/home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh"
THRESHOLD=85

# Get current health score
HEALTH=$($HEALTH_SCRIPT status --format=json | jq -r '.health_score')

echo "[$(date)] Health check: ${HEALTH}%"

# Alert if below threshold
if [ "$HEALTH" -lt "$THRESHOLD" ]; then
    $ALERT_SCRIPT "HEALTH_LOW" "System health at ${HEALTH}% (threshold: ${THRESHOLD}%)"

    # Auto-heal if possible
    if [ "$HEALTH" -lt 80 ]; then
        /home/dave/skippy/scripts/automation/self_maintenance_v1.0.0.sh auto-heal
    fi
fi
```

---

## Metrics Tracking

**Track Monthly:**
- Average health score
- Minimum health score
- Days below 90%
- Number of auto-heal actions
- Improvement rate

**Goal:** Maintain >90% health score 95% of the time

---

## Related Protocols
- Alert Management Protocol
- Incident Response Protocol
- Data Retention Protocol
- Self-Maintenance (tool)

---

**Version History:**
- 1.0.0 (2025-11-04): Initial protocol creation
