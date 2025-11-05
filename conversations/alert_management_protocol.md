# Alert Management Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Owner:** Infrastructure Team
**Status:** Active

---

## Purpose

This protocol standardizes how alerts from monitoring tools are handled, prioritized, and resolved to ensure timely response while preventing alert fatigue.

## Scope

This protocol applies to all automated alerts from:
- critical_alerter_v1.0.0.sh
- system_dashboard_v1.0.0.sh
- log_aggregator_v1.0.0.sh
- performance_optimizer_v1.0.0.sh
- self_maintenance_v1.0.0.sh
- WordPress monitoring tools
- Infrastructure monitoring systems

---

## Alert Severity Levels

### P0 - Critical (Immediate Action Required)
**Response Time:** 15 minutes
**Examples:**
- Site completely down (HTTP 500/503)
- Database unavailable
- Security breach detected
- Data loss occurring
- Critical service failure

**Actions:**
- Immediately notify on-call person
- Create incident ticket
- Begin incident response protocol
- Update status page

### P1 - High (Urgent Action Required)
**Response Time:** 1 hour
**Examples:**
- Site performance severely degraded (>5s load time)
- Disk space >90% full
- Backup failures
- Security vulnerability detected
- Core functionality broken

**Actions:**
- Notify on-call person
- Create high-priority ticket
- Begin investigation
- Communicate to team

### P2 - Medium (Action Required Soon)
**Response Time:** 4 hours
**Examples:**
- Site performance degraded (3-5s load time)
- Disk space >80% full
- Warning-level errors in logs
- Plugin/theme updates available
- Non-critical service degradation

**Actions:**
- Create ticket
- Schedule investigation
- Monitor for escalation

### P3 - Low (Action Required This Week)
**Response Time:** 24 hours
**Examples:**
- Minor performance issues (2-3s load time)
- Disk space >70% full
- Info-level log entries
- Optimization opportunities
- Routine maintenance needed

**Actions:**
- Create ticket for backlog
- Address during normal work hours
- Include in weekly review

### P4 - Info (No Action Required)
**Response Time:** N/A
**Examples:**
- Successful operations
- System status updates
- Metric reports
- Scheduled task completions

**Actions:**
- Log for reference
- No ticket needed
- Review in weekly reports

---

## Alert Routing

### On-Call Rotation

**Primary On-Call:**
- Receives P0/P1 alerts immediately (phone/SMS)
- Receives P2 alerts via email
- Response time: 15 minutes for P0, 1 hour for P1

**Secondary On-Call (Backup):**
- Receives alerts if primary doesn't respond in 30 minutes
- Available for consultation
- Takes over if primary unavailable

**Team Distribution:**
- P3/P4 alerts: Email to team distribution list
- Weekly rotation schedule published in advance
- Swap/coverage process documented

### Alert Channels

**Critical (P0/P1):**
- Phone call (critical_alerter SMS/call)
- Slack/Teams urgent channel
- Email

**High/Medium (P2):**
- Slack/Teams alert channel
- Email

**Low/Info (P3/P4):**
- Email digest
- Weekly report

---

## Alert Response Workflow

### 1. Acknowledge Alert
**Within response time window:**
- Mark alert as "Acknowledged" in monitoring system
- Post acknowledgment in alert channel
- Create incident/ticket if needed

### 2. Initial Assessment
**Quick triage:**
- Verify alert is accurate (not false positive)
- Check scope/impact
- Determine if escalation needed
- Gather initial context

### 3. Investigation
**For P0/P1:**
- Follow incident response protocol
- Document steps taken
- Keep stakeholders updated

**For P2/P3:**
- Research issue
- Check logs, metrics, related systems
- Identify root cause
- Document findings

### 4. Resolution
**Actions:**
- Implement fix or mitigation
- Verify resolution
- Document solution
- Update alert rules if needed

### 5. Post-Resolution
**Follow-up:**
- Mark alert as "Resolved"
- Update ticket/incident
- Post resolution summary
- Schedule post-mortem if needed (P0/P1)

---

## Alert Tuning

### False Positive Handling

**When false positives occur:**
1. Document why it's a false positive
2. Adjust alert threshold or logic
3. Test new threshold
4. Update alert documentation
5. Communicate change to team

### Alert Fatigue Prevention

**Warning signs:**
- Same alert firing repeatedly
- Alerts ignored regularly
- Response times increasing
- Team complaints about noise

**Actions:**
1. Review alert frequency reports weekly
2. Consolidate related alerts
3. Adjust thresholds to reduce noise
4. Remove low-value alerts
5. Create alert effectiveness metrics

### Regular Review Schedule

**Weekly:**
- Review alert volume and response times
- Identify false positives
- Check for missing alerts
- Update thresholds as needed

**Monthly:**
- Analyze alert trends
- Review alert effectiveness
- Update alert documentation
- Team feedback session

---

## Alert Configuration

### Critical Alerter Integration

**Configuration:** `/home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh`

**Usage:**
```bash
# Send critical alert
/home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh "SITE_DOWN" "Website returning 503"

# Send high-priority alert
/home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh "BACKUP_FAILED" "Nightly backup did not complete"

# Send alert with custom severity
ALERT_SEVERITY="P2" /home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh "DISK_SPACE" "Disk space 85% full"
```

### System Dashboard Integration

**Configuration:** `/home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh`

**Health Score Alert Thresholds:**
- <50%: P0 alert
- 50-70%: P1 alert
- 70-85%: P2 alert
- 85-95%: P3 alert
- >95%: No alert (info only)

**Usage:**
```bash
# Get current health and alert if needed
HEALTH=$(/home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh status --format=json | jq -r '.health_score')

if [ "$HEALTH" -lt 50 ]; then
    /home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh "HEALTH_CRITICAL" "System health: ${HEALTH}%"
fi
```

### Log Aggregator Integration

**Configuration:** `/home/dave/skippy/scripts/monitoring/log_aggregator_v1.0.0.sh`

**Alert Rules:**
- >100 errors in 1 hour: P1 alert
- >50 errors in 1 hour: P2 alert
- >1000 warnings in 1 hour: P2 alert
- Error rate spike (2x normal): P1 alert

**Usage:**
```bash
# Analyze logs and alert on anomalies
/home/dave/skippy/scripts/monitoring/log_aggregator_v1.0.0.sh analyze --alert-on-errors
```

---

## Alert Documentation

### Alert Playbooks

Each common alert should have a playbook documenting:
- **Alert name and description**
- **What it means**
- **Potential causes**
- **Investigation steps**
- **Common resolutions**
- **Escalation path**

**Playbook Location:** `/home/dave/skippy/documentation/alert_playbooks/`

### Alert History

**Tracking:**
- All alerts logged to: `/home/dave/skippy/logs/alerts/`
- Alert database: `/home/dave/skippy/logs/alerts/alert_history.json`
- Response times tracked
- Resolution outcomes documented

### Metrics to Track

**Response Metrics:**
- Mean time to acknowledge (MTTA)
- Mean time to resolve (MTTR)
- Alert volume by severity
- False positive rate
- Alert response rate

**Monthly Report Should Include:**
- Total alerts by severity
- Average response times
- Top alert types
- False positive incidents
- Tuning actions taken

---

## Escalation Paths

### Internal Escalation

**Level 1: On-Call Engineer**
- Initial response and triage
- Resolves P2/P3/P4 issues
- Escalates P0/P1 as needed

**Level 2: Team Lead**
- Consulted for P0/P1 issues
- Makes architectural decisions
- Approves emergency changes
- Coordinates with stakeholders

**Level 3: Campaign Manager**
- Notified for P0 incidents
- Makes business decisions
- External communication approval
- Resource allocation

### External Escalation

**Vendor Support:**
- When to contact (e.g., hosting provider down)
- How to escalate (support ticket, phone, emergency line)
- Information to provide
- Tracking vendor response

**Emergency Contacts:**
- Maintain current contact list
- Include vendor support numbers
- Document escalation procedures
- Test contact methods quarterly

---

## Alert Suppression

### Scheduled Maintenance

**During planned maintenance:**
1. Announce maintenance window in advance
2. Suppress alerts for affected systems
3. Monitor maintenance progress
4. Resume alerts after completion
5. Verify system health post-maintenance

**Process:**
```bash
# Suppress alerts during maintenance
touch /home/dave/skippy/.maintenance_mode

# Perform maintenance
# ...

# Resume alerts
rm /home/dave/skippy/.maintenance_mode
```

### Known Issues

**For issues with known workarounds:**
- Document the issue and workaround
- Suppress repetitive alerts
- Schedule permanent fix
- Remove suppression after fix

---

## Communication Templates

### P0 Incident Notification

```
Subject: [P0] CRITICAL - [Brief Description]

Status: Investigating / Identified / Fixing / Resolved
Impact: [Describe user impact]
Started: [Time]
Current Actions: [What's being done]
Next Update: [Time]

[Additional details]
```

### Alert Resolution Summary

```
Alert: [Alert name]
Severity: [P0/P1/P2/P3]
Duration: [Time from alert to resolution]
Root Cause: [Brief explanation]
Resolution: [What was done]
Follow-up: [Any follow-up actions needed]
```

### Weekly Alert Report

```
Week of: [Date]
Total Alerts: [Number]
  P0: [Count]
  P1: [Count]
  P2: [Count]
  P3: [Count]
  P4: [Count]

Average Response Times:
  P0: [Time]
  P1: [Time]
  P2: [Time]

Top Alert Types:
1. [Alert] - [Count]
2. [Alert] - [Count]
3. [Alert] - [Count]

False Positives: [Count]
Tuning Actions: [List]
```

---

## Tool Integration Examples

### Self-Maintenance Integration

```bash
# In self_maintenance_v1.0.0.sh
if ! health_check > /dev/null 2>&1; then
    SEVERITY="P1"
    /home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh \
        "HEALTH_CHECK_FAILED" \
        "Self-maintenance health check found issues"
fi
```

### Performance Optimizer Integration

```bash
# In performance_optimizer_v1.0.0.sh
if [ "$LOAD_TIME" -gt 5000 ]; then
    SEVERITY="P1"
    /home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh \
        "PERFORMANCE_DEGRADED" \
        "Page load time: ${LOAD_TIME}ms (threshold: 5000ms)"
fi
```

### WordPress Validator Integration

```bash
# In pre_deployment_validator_v1.0.0.sh
if [ "$CRITICAL_ERRORS" -gt 0 ]; then
    SEVERITY="P0"
    /home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh \
        "VALIDATION_CRITICAL" \
        "Pre-deployment validation found ${CRITICAL_ERRORS} critical errors"
fi
```

---

## Training Requirements

### For On-Call Staff

**Must know:**
- Alert severity definitions
- Response time expectations
- How to acknowledge alerts
- Basic troubleshooting steps
- Escalation procedures
- Where to find playbooks

**Training Process:**
1. Review this protocol
2. Shadow current on-call person
3. Walk through common alerts
4. Practice with test alerts
5. First on-call shift with backup

### For All Team Members

**Should know:**
- Alert routing and channels
- How to report issues
- Basic alert interpretation
- Who to contact for help

---

## Continuous Improvement

### Regular Reviews

**Quarterly Alert Review:**
- Alert effectiveness analysis
- False positive rate review
- Response time trends
- Playbook updates needed
- Tool integration improvements

**Action Items:**
- Update alert thresholds
- Create new playbooks
- Retire outdated alerts
- Improve automation
- Team training needs

### Feedback Loop

**Encourage team to:**
- Report alert issues
- Suggest improvements
- Document new solutions
- Share learnings

**Process:**
- Weekly team feedback in standups
- Monthly feedback survey
- Quarterly improvement planning

---

## Success Metrics

### Key Performance Indicators

**Response Metrics:**
- MTTA (Mean Time to Acknowledge): Target <5 min for P0, <30 min for P1
- MTTR (Mean Time to Resolve): Target <1 hr for P0, <4 hrs for P1
- Alert response rate: Target 100% for P0/P1

**Quality Metrics:**
- False positive rate: Target <5%
- Alert tuning actions per month: Measure trend
- Repeat alerts: Target decreasing trend

**Operational Metrics:**
- System uptime: Target 99.9%
- Incident count: Measure and trend
- P0/P1 prevention rate: Measure proactive fixes

---

## Related Protocols

- **Incident Response Protocol** - Full incident management process
- **Health Check Protocol** - Regular monitoring procedures
- **Communication Protocol** - Team communication standards
- **Disaster Recovery Drill Protocol** - Testing recovery procedures

---

## Appendix A: Alert Checklist

### When Alert Fires

- [ ] Alert received and acknowledged within response time
- [ ] Alert severity assessed and confirmed
- [ ] Initial investigation started
- [ ] Stakeholders notified if P0/P1
- [ ] Ticket/incident created
- [ ] Investigation documented
- [ ] Resolution implemented
- [ ] Resolution verified
- [ ] Alert marked as resolved
- [ ] Post-resolution summary posted
- [ ] Follow-up actions scheduled if needed

### Weekly Alert Review

- [ ] Alert volume reviewed
- [ ] Response times analyzed
- [ ] False positives identified
- [ ] Alert tuning actions taken
- [ ] New playbooks created if needed
- [ ] Team feedback collected
- [ ] Improvement actions identified

---

## Appendix B: Common Alert Playbooks

### Site Down (HTTP 500/503)

**Investigation Steps:**
1. Check if site is truly down (curl http://rundaverun.org)
2. Check server status and resource usage
3. Check database connectivity
4. Check recent deployments
5. Review error logs

**Common Causes:**
- PHP fatal error
- Database connection failure
- Out of memory
- Plugin/theme conflict
- Server overload

**Common Resolutions:**
- Restart PHP-FPM
- Increase memory limits
- Disable problematic plugin
- Restore from backup if recent deployment
- Scale resources if load spike

### Disk Space Critical

**Investigation Steps:**
1. Check disk usage: `df -h`
2. Find large files: `du -sh /* | sort -rh | head -10`
3. Check log sizes
4. Check backup sizes
5. Check uploads/temp directories

**Common Causes:**
- Log files not rotating
- Backups accumulating
- Upload directory growth
- Temp files not cleaned
- Database backups not cleaned

**Common Resolutions:**
- Run log rotation
- Clean old backups (keep last 30 days)
- Clean temp files
- Compress old logs
- Run self_maintenance disk cleanup

---

## Appendix C: Alert Script Template

```bash
#!/bin/bash
# Alert Integration Template
# Use this template for custom alerts

ALERT_SCRIPT="/home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh"

# Define alert severity
SEVERITY="P2"  # P0, P1, P2, P3, P4

# Define alert event name (uppercase, underscores)
EVENT="CUSTOM_CHECK"

# Define alert message
MESSAGE="Description of what was detected"

# Send alert
if [ -x "$ALERT_SCRIPT" ]; then
    ALERT_SEVERITY="$SEVERITY" "$ALERT_SCRIPT" "$EVENT" "$MESSAGE"
fi
```

---

**Version History:**
- 1.0.0 (2025-11-04): Initial protocol creation
