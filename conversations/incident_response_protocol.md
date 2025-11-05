# Incident Response Protocol

**Version:** 2.0.0
**Last Updated:** 2025-11-05
**Owner:** Infrastructure Team
**Status:** Active

---

## Purpose

This protocol defines how to **respond to and resolve incidents** affecting the campaign infrastructure, ensuring rapid resolution, clear communication, post-mortems, and continuous improvement.

**Focus:** Incident workflow, investigation, resolution, and post-mortem process
**Complement:** Works with alert_management_protocol for alert routing and tuning

## Scope

This protocol applies to all incidents including:
- Site outages or degradation
- Security incidents
- Data loss or corruption
- Service disruptions
- Performance issues
- Failed deployments
- User-reported issues
- Detected anomalies

**Note:** Incidents can originate from automated alerts (see alert_management_protocol) or manual detection.

---

## Incident Severity Levels

**For complete severity definitions, escalation paths, and examples, see:**
`/home/dave/skippy/conversations/_shared_severity_definitions.md`

**Quick Reference:**
- **P0 - Critical:** 15 min response, complete failure/active breach
- **P1 - High:** 1 hour response, major functionality broken
- **P2 - Medium:** 4 hours response, degraded experience
- **P3 - Low:** 24 hours response, minor issues

**Severity determines:**
- Response time requirements
- Communication frequency
- Escalation paths
- Post-incident review requirements (P0/P1 require full post-mortem)

---

## Incident Response Phases

### 1. Detection & Alert

**How Incidents Are Detected:**
- Automated monitoring alerts
- User reports
- Team member observation
- Third-party notifications

**Initial Actions:**
- Alert acknowledged within response time
- Initial severity assessment
- Create incident ticket
- Notify on-call engineer

### 2. Triage & Assessment

**Quick Assessment (5-10 minutes):**
- Verify incident is real (not false positive)
- Assess scope and impact
- Confirm severity level
- Identify affected systems
- Determine if escalation needed

**Document:**
- Time incident detected
- Initial symptoms
- Affected systems
- User impact
- Initial severity assessment

### 3. Communication

**Immediate Notifications (within 15 min for P0, 1 hr for P1):**
- On-call team
- Team lead
- Campaign manager (for P0)
- Affected users (via status page if applicable)

**Ongoing Updates:**
- P0: Every 30-60 minutes
- P1: Every 2-4 hours
- P2: Daily
- Include: status, progress, ETA

**Communication Channels:**
- Internal: Slack/Teams incident channel
- External: Email, status page, social media (if needed)

### 4. Investigation

**Gather Information:**
- Check recent changes (deployments, config changes)
- Review logs (/home/dave/skippy/logs/)
- Check monitoring dashboards
- Test affected functionality
- Interview witnesses if applicable

**Investigation Commands:**
```bash
# Check system health
/home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh status

# Review recent logs
/home/dave/skippy/scripts/monitoring/log_aggregator_v1.0.0.sh errors --since today

# Check recent deployments
git log -10 --oneline
wp plugin list --status=active

# Database status
wp db check

# Performance check
/home/dave/skippy/scripts/optimization/performance_optimizer_v1.0.0.sh analyze
```

**Document Findings:**
- Symptoms observed
- Error messages
- Log entries
- Timeline of events
- Hypotheses about cause

### 5. Mitigation/Resolution

**Immediate Mitigation:**
- Stop ongoing damage
- Restore service (even if temporary)
- Isolate affected systems if needed
- Roll back recent changes if cause identified

**Permanent Fix:**
- Implement root cause fix
- Verify fix works
- Monitor for recurrence
- Update systems/code as needed

**Resolution Options:**
1. **Rollback:** Revert to last known good state
2. **Fix Forward:** Implement fix in production
3. **Failover:** Switch to backup system
4. **Workaround:** Temporary solution while fixing root cause

**Decision Tree:**
```
Is there a recent deployment?
  YES -> Rollback
  NO  -> Can we quickly fix?
          YES -> Fix forward
          NO  -> Workaround + schedule fix
```

### 6. Verification

**Confirm Resolution:**
- Test affected functionality
- Check monitoring metrics
- Verify user reports resolved
- Monitor for 30-60 minutes
- Get user confirmation if possible

**Verification Checklist:**
- [ ] Functionality restored
- [ ] Monitoring shows healthy
- [ ] Users can access system
- [ ] No new errors in logs
- [ ] Performance acceptable
- [ ] No side effects observed

### 7. Post-Incident Activities

**Immediate (same day):**
- Update all stakeholders
- Close incident ticket
- Thank responders
- Document resolution in ticket

**Within 24 hours (P0/P1):**
- Initial incident report
- Share key learnings
- Identify immediate action items

**Within 1 week (P0/P1):**
- Full post-incident review meeting
- Comprehensive incident report
- Preventive action plan
- Update documentation/runbooks

---

## Incident Response Roles

### Incident Commander (IC)

**Responsibilities:**
- Overall incident coordination
- Decision-making authority
- Communication to stakeholders
- Resource allocation
- Declaring incident over

**Activities:**
- Assess severity
- Coordinate response
- Make critical decisions
- Communicate status
- Lead post-incident review

### Technical Lead

**Responsibilities:**
- Technical investigation
- Implement fixes
- Coordinate technical team
- Technical decision-making

**Activities:**
- Root cause analysis
- Testing fixes
- Coordinating changes
- Technical documentation

### Communications Lead

**Responsibilities:**
- Internal communications
- External communications
- Status page updates
- Social media updates (if needed)

**Activities:**
- Draft updates
- Post status updates
- Respond to inquiries
- Coordinate messaging

### Scribe

**Responsibilities:**
- Document timeline
- Record decisions
- Track action items
- Capture key information

**Activities:**
- Maintain incident timeline
- Document in incident ticket
- Track who's working on what
- Note key decisions and why

---

## Communication Templates

### P0 Initial Notification

```
Subject: [P0 INCIDENT] - Site Down

SEVERITY: P0 - Critical
STATUS: Investigating
IMPACT: Website completely unavailable
STARTED: [Time]
IC: [Name]

We are currently experiencing a complete site outage. The team is
investigating and working on restoration.

Next update: [Time]
```

### Status Update

```
Subject: [P0 INCIDENT] - UPDATE - Site Down

SEVERITY: P0 - Critical
STATUS: [Investigating/Identified/Fixing/Monitoring]
DURATION: [Time since start]

UPDATE:
[What we've learned, what we're doing]

IMPACT:
[Current user impact]

NEXT STEPS:
[What happens next]

ETA: [If known]
Next update: [Time]
```

### Resolution Notification

```
Subject: [RESOLVED] P0 Incident - Site Down

SEVERITY: P0 - Critical
STATUS: Resolved
DURATION: [Total time]
RESOLVED: [Time]

The incident has been resolved. The site is now accessible and
functioning normally.

ROOT CAUSE:
[Brief explanation]

RESOLUTION:
[What was done]

PREVENTION:
[Steps being taken to prevent recurrence]

Full incident report will be available within 24 hours.
```

---

## Incident War Room

### Physical/Virtual War Room

**For P0/P1 Incidents:**
- Dedicated communication channel (Slack/Teams)
- Video call for coordination
- Shared document for real-time updates
- Screen sharing for collaboration

**Setup:**
```
# Create incident channel
#incident-YYYYMMDD-brief-description

# Pin important info:
- Incident ticket link
- Relevant dashboard links
- Key contact info
- Current status document
```

### Incident Timeline Document

**Maintain shared document:**
```markdown
# Incident: [Brief Description]

**Severity:** P0
**Started:** [Time]
**IC:** [Name]
**Tech Lead:** [Name]

## Timeline
- HH:MM - Incident detected via [source]
- HH:MM - IC assigned, investigation started
- HH:MM - Root cause hypothesis: [description]
- HH:MM - Mitigation attempted: [action]
- HH:MM - Status update sent
- HH:MM - Resolution implemented
- HH:MM - Verification complete
- HH:MM - Incident closed

## Current Status
[Keep this section updated]

## Actions Taken
- Action 1
- Action 2

## Key Decisions
- Decision 1: [Why]
- Decision 2: [Why]
```

---

## Escalation Procedures

### Internal Escalation

**Level 1: On-Call Engineer**
- Initial response
- Resolves P2/P3
- Escalates P0/P1 as needed

**Level 2: Team Lead**
- Automatically notified for P0/P1
- Acts as IC for major incidents
- Makes architectural decisions
- Coordinates resources

**Level 3: Campaign Manager**
- Notified for all P0
- Makes business decisions
- External communication approval
- Resource allocation

### External Escalation

**Hosting Provider:**
- Contact if infrastructure issue
- Have account info ready
- Use emergency support line for P0

**Vendor Support:**
- Contact for vendor-specific issues
- Reference support ticket system
- Escalate within vendor if needed

**Emergency Contacts:**
- Maintain current contact list
- Include after-hours contacts
- Test contact methods quarterly

---

## Runbooks for Common Incidents

### Site Down (HTTP 500/503)

**Investigation:**
```bash
# Check if site is responding
curl -I http://rundaverun.org

# Check WordPress
wp core verify-checksums

# Check database
wp db check

# Check error logs
tail -100 /path/to/wordpress/wp-content/debug.log

# Check system resources
df -h
free -h
top -bn1 | head -20
```

**Common Fixes:**
1. Restart web server
2. Clear cache: `wp cache flush`
3. Disable problematic plugin: `wp plugin deactivate plugin-name`
4. Restore from backup if recent deployment
5. Increase memory limit in wp-config.php

### Database Connection Failure

**Investigation:**
```bash
# Test database connectivity
wp db check

# Check database service
systemctl status mysql
# or
systemctl status mariadb

# Check database logs
tail -100 /var/log/mysql/error.log
```

**Common Fixes:**
1. Restart database service
2. Check wp-config.php database credentials
3. Check database server disk space
4. Repair database: `wp db repair`
5. Restore database from backup if corrupted

### Performance Degradation

**Investigation:**
```bash
# Run performance analysis
/home/dave/skippy/scripts/optimization/performance_optimizer_v1.0.0.sh analyze

# Check system resources
top -bn1 | head -20
df -h

# Check slow queries
wp db query "SHOW FULL PROCESSLIST;"

# Check plugin performance
wp plugin list --status=active
```

**Common Fixes:**
1. Clear caches: `wp cache flush`
2. Optimize database: `wp db optimize`
3. Disable slow plugins temporarily
4. Scale resources if traffic spike
5. Enable caching if not already

### Failed Deployment

**Investigation:**
```bash
# Check what was deployed
git log -5 --oneline

# Check for errors
/home/dave/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh validate-all

# Check WordPress status
wp core verify-checksums
wp plugin list
```

**Common Fixes:**
1. Rollback to previous version: `git revert` or restore from backup
2. Fix errors and redeploy
3. Check file permissions
4. Clear caches
5. Run database migrations if needed

### Security Incident

**Immediate Actions:**
1. **Contain:** Isolate affected systems
2. **Assess:** Determine scope of breach
3. **Preserve:** Save logs and evidence
4. **Eradicate:** Remove attacker access
5. **Recover:** Restore to secure state

**Investigation:**
```bash
# Check security logs
tail -100 /home/dave/skippy/logs/security/audit_trail.log

# Check for unauthorized changes
git status
git diff

# Check for suspicious files
find /path/to/wordpress -type f -mtime -1

# Check user accounts
wp user list

# Run security scan
/home/dave/skippy/scripts/security/vulnerability_scanner_v1.0.0.sh
```

**Response:**
1. Change all passwords immediately
2. Review access logs
3. Check for backdoors/malware
4. Restore from clean backup if needed
5. Report to authorities if required
6. Follow Data Privacy Protocol for any data breach

---

## Post-Incident Review (PIR)

### When Required

**Must conduct PIR for:**
- All P0 incidents
- All P1 incidents
- Any security incident
- Repeated P2 incidents (same root cause)

### PIR Meeting

**Timing:** Within 1 week of resolution
**Duration:** 1 hour
**Attendees:** All responders + stakeholders

**Agenda:**
1. Review timeline (15 min)
2. Discuss what went well (15 min)
3. Discuss what needs improvement (15 min)
4. Identify action items (10 min)
5. Assign owners and deadlines (5 min)

**Ground Rules:**
- Blameless environment
- Focus on systems, not individuals
- Seek to understand, not judge
- Look for improvements

### PIR Report Template

```markdown
# Post-Incident Review: [Incident Title]

**Date:** [Incident Date]
**Severity:** [P0/P1/P2]
**Duration:** [Duration]
**PIR Date:** [PIR Meeting Date]
**Attendees:** [Names]

## Incident Summary
Brief description of what happened

## Timeline
Detailed timeline of events

## Impact
- Users affected: [Number/description]
- Duration: [Time]
- Systems affected: [List]
- Business impact: [Description]

## Root Cause
What actually caused the incident

## What Went Well
- Good thing 1
- Good thing 2

## What Needs Improvement
- Issue 1
- Issue 2

## Action Items
- [ ] Action 1 (Owner: Name, Due: Date)
- [ ] Action 2 (Owner: Name, Due: Date)

## Prevention
How we'll prevent this from happening again

## Lessons Learned
- Learning 1
- Learning 2
```

### Action Items Tracking

**After PIR:**
- Create tickets for all action items
- Assign owners
- Set deadlines
- Track completion
- Follow up in next team meeting

---

## Integration with Existing Tools

### Critical Alerter

```bash
# Send incident notification
/home/dave/skippy/scripts/monitoring/critical_alerter_v1.0.0.sh \
  "INCIDENT_P0" \
  "Site down - beginning incident response"
```

### System Dashboard

```bash
# Quick health check during incident
/home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh status

# Get metrics for incident report
/home/dave/skippy/scripts/monitoring/system_dashboard_v1.0.0.sh snapshot
```

### DR Automation

```bash
# Restore from backup if needed
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh restore-wordpress
```

### Log Aggregator

```bash
# Analyze logs during incident
/home/dave/skippy/scripts/monitoring/log_aggregator_v1.0.0.sh analyze

# Search for specific errors
/home/dave/skippy/scripts/monitoring/log_aggregator_v1.0.0.sh search "error message"
```

---

## Training and Drills

### Incident Response Training

**All Team Members Should Know:**
- How to report an incident
- Incident severity levels
- Basic troubleshooting
- When to escalate

**On-Call Engineers Must Know:**
- Full incident response process
- All runbooks
- Escalation procedures
- Communication protocols

### Incident Simulations

**Quarterly Drill:**
- Simulate incident scenario
- Test response procedures
- Practice coordination
- Identify gaps

**Scenarios to Practice:**
- Site down
- Database failure
- Security breach
- Failed deployment
- Performance crisis

---

## Success Metrics

### Response Metrics

**Track:**
- Mean time to detect (MTTD)
- Mean time to acknowledge (MTTA)
- Mean time to resolve (MTTR)
- Incident count by severity
- Repeat incidents (same root cause)

**Targets:**
- P0 MTTA: <15 minutes
- P0 MTTR: <1 hour
- P1 MTTA: <1 hour
- P1 MTTR: <4 hours

### Process Metrics

**Track:**
- PIR completion rate (target: 100% for P0/P1)
- Action item completion rate
- Time to PIR (target: <1 week)
- Prevention effectiveness (incident recurrence)

---

## Related Protocols

- **Alert Management Protocol** - Alert handling and routing
- **Health Check Protocol** - Regular monitoring
- **Disaster Recovery Drill Protocol** - DR testing
- **Communication Protocol** - Team communication
- **Deployment Checklist Protocol** - Prevent deployment issues

---

## Appendix: Incident Response Checklist

### During Incident

- [ ] Incident detected and acknowledged
- [ ] Severity assessed
- [ ] Incident ticket created
- [ ] IC assigned
- [ ] Initial notification sent
- [ ] War room established (if P0/P1)
- [ ] Timeline document started
- [ ] Investigation begun
- [ ] Status updates sent regularly
- [ ] Resolution implemented
- [ ] Verification complete
- [ ] Resolution notification sent
- [ ] Incident closed

### After Incident (P0/P1)

- [ ] Initial incident report (24 hours)
- [ ] PIR meeting scheduled (within 1 week)
- [ ] PIR conducted
- [ ] PIR report published
- [ ] Action items created and assigned
- [ ] Documentation updated
- [ ] Runbooks updated
- [ ] Monitoring/alerts adjusted
- [ ] Team learnings shared
- [ ] Prevention measures implemented

---

**Version History:**
- 1.0.0 (2025-11-04): Initial protocol creation
