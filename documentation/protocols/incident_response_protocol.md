# Incident Response Protocol

**Version**: 1.0.0
**Last Updated**: 2025-11-16
**Owner**: System Administration

---

## Context

This protocol provides a structured approach to handling system incidents, from initial detection through resolution and post-mortem analysis. Proper incident response minimizes damage, reduces recovery time, and prevents recurrence.

## Purpose

- Define clear incident severity levels
- Establish rapid response procedures
- Minimize service disruption
- Enable root cause analysis
- Prevent incident recurrence

---

## Incident Severity Classification

### SEV-1: CRITICAL
**Impact**: Complete system outage or data loss
**Response Time**: Immediate (within 15 minutes)
**Examples**:
- Production site down
- Database corruption
- Security breach
- Data loss occurring
- Complete service failure

### SEV-2: HIGH
**Impact**: Major functionality impaired
**Response Time**: Within 1 hour
**Examples**:
- Key features broken
- Significant performance degradation
- Partial data access issues
- Authentication failures
- Payment processing down

### SEV-3: MEDIUM
**Impact**: Minor functionality affected
**Response Time**: Within 4 hours
**Examples**:
- Non-critical features broken
- Intermittent issues
- Slow but functional services
- Minor UI/UX problems
- Single user affected

### SEV-4: LOW
**Impact**: Minimal or cosmetic issues
**Response Time**: Within 24 hours
**Examples**:
- Typos in content
- Minor styling issues
- Enhancement requests
- Documentation updates
- Non-urgent maintenance

---

## Incident Response Phases

### Phase 1: Detection & Alert (0-5 minutes)

```bash
# Automated detection via health checks
# Manual detection via monitoring

# Create incident ticket
INCIDENT_ID="INC-$(date +%Y%m%d%H%M%S)"
INCIDENT_DIR="/home/dave/skippy/incidents/$INCIDENT_ID"
mkdir -p "$INCIDENT_DIR"

# Log initial detection
cat > "$INCIDENT_DIR/incident.md" <<EOF
# Incident: $INCIDENT_ID

**Status**: ACTIVE
**Severity**: [SEV-1|SEV-2|SEV-3|SEV-4]
**Detected**: $(date)
**Reporter**: [Name/System]

## Initial Symptoms
- [Describe what was observed]

## Affected Systems
- [ ] WordPress site
- [ ] Database
- [ ] Git repository
- [ ] MCP Server
- [ ] Network
- [ ] Other: ___

## Users Impacted
- [ ] Production users
- [ ] Development
- [ ] No users affected
EOF
```

### Phase 2: Triage & Assessment (5-15 minutes)

```bash
# Quick system assessment
echo "## Quick Assessment" >> "$INCIDENT_DIR/incident.md"

# Check service status
systemctl is-system-running >> "$INCIDENT_DIR/system_status.txt"
df -h >> "$INCIDENT_DIR/disk_status.txt"
free -h >> "$INCIDENT_DIR/memory_status.txt"

# Check logs for errors
journalctl --since "1 hour ago" | grep -E "ERROR|CRITICAL|FATAL" > "$INCIDENT_DIR/recent_errors.log"

# WordPress specific
curl -s -I "http://rundaverun-local-complete-022655.local/" > "$INCIDENT_DIR/wp_response.txt"

# Network connectivity
ping -c 3 8.8.8.8 >> "$INCIDENT_DIR/network_check.txt"
```

### Phase 3: Containment (15-30 minutes)

**Goal**: Stop the incident from getting worse

```bash
# SEV-1: Immediate containment actions
# - Stop affected services
# - Block malicious traffic
# - Isolate compromised systems
# - Enable maintenance mode

# WordPress: Enable maintenance mode
cat > /home/dave/skippy/rundaverun_local_site/app/public/.maintenance <<EOF
<?php
$upgrading = time();
EOF

# Database: Block connections if needed
# Backup: Ensure current backup exists
mysqldump -u root --password=root \
  --socket=/path/to/socket \
  local > "$INCIDENT_DIR/db_backup_$(date +%Y%m%d%H%M%S).sql"
```

### Phase 4: Investigation (30-60 minutes)

```bash
# Document investigation steps
echo "## Investigation Log" >> "$INCIDENT_DIR/incident.md"
echo "$(date): Starting investigation" >> "$INCIDENT_DIR/incident.md"

# Collect evidence
# - System logs
# - Application logs
# - Database logs
# - Network captures
# - User reports

# Timeline reconstruction
echo "## Timeline" >> "$INCIDENT_DIR/timeline.md"
echo "- [TIME]: Event description" >> "$INCIDENT_DIR/timeline.md"

# Root cause analysis
echo "## Root Cause Analysis" >> "$INCIDENT_DIR/incident.md"
echo "### Potential Causes:" >> "$INCIDENT_DIR/incident.md"
echo "1. " >> "$INCIDENT_DIR/incident.md"
echo "2. " >> "$INCIDENT_DIR/incident.md"
```

### Phase 5: Resolution (Time varies by severity)

```bash
# Apply fix
echo "$(date): Applying fix..." >> "$INCIDENT_DIR/incident.md"

# Document the fix
echo "## Resolution" >> "$INCIDENT_DIR/incident.md"
echo "- Action taken: " >> "$INCIDENT_DIR/incident.md"
echo "- Commands run: " >> "$INCIDENT_DIR/incident.md"

# Verify fix
echo "$(date): Verifying resolution..." >> "$INCIDENT_DIR/incident.md"

# Remove maintenance mode
rm -f /home/dave/skippy/rundaverun_local_site/app/public/.maintenance

# Test functionality
curl -s "http://rundaverun-local-complete-022655.local/" | grep -q "Dave Biggers" && echo "Site restored"
```

### Phase 6: Recovery & Monitoring (1-24 hours)

```bash
# Confirm full recovery
echo "## Recovery Verification" >> "$INCIDENT_DIR/incident.md"
echo "- [ ] All services restored" >> "$INCIDENT_DIR/incident.md"
echo "- [ ] Performance normal" >> "$INCIDENT_DIR/incident.md"
echo "- [ ] No data loss" >> "$INCIDENT_DIR/incident.md"
echo "- [ ] Monitoring in place" >> "$INCIDENT_DIR/incident.md"

# Enable enhanced monitoring
# Watch for recurrence for 24-48 hours

# Update incident status
sed -i 's/Status: ACTIVE/Status: RESOLVED/' "$INCIDENT_DIR/incident.md"
echo "**Resolved**: $(date)" >> "$INCIDENT_DIR/incident.md"
```

### Phase 7: Post-Mortem (Within 1 week)

```bash
# Create post-mortem document
cat > "$INCIDENT_DIR/postmortem.md" <<EOF
# Post-Mortem: $INCIDENT_ID

## Summary
- **Duration**: [X hours/minutes]
- **Impact**: [Description]
- **Root Cause**: [Brief summary]

## Timeline
[Detailed timeline from detection to resolution]

## Root Cause Analysis
[5 Whys or Fishbone analysis]

## What Went Well
-
-

## What Went Wrong
-
-

## Action Items
1. [ ] Prevent recurrence: [Specific action]
2. [ ] Improve detection: [Specific action]
3. [ ] Update runbooks: [Specific action]
4. [ ] Add monitoring: [Specific action]

## Lessons Learned
-

## Follow-up Date
$(date -d "+7 days" +%Y-%m-%d)
EOF
```

---

## Communication Templates

### Internal Alert (SEV-1/SEV-2)
```
INCIDENT ALERT: $INCIDENT_ID
Severity: SEV-1 CRITICAL
Status: ACTIVE
Impact: [Description]
Systems: [Affected systems]
ETA: [Estimated resolution time]
Updates: Every 30 minutes until resolved
```

### Status Update
```
INCIDENT UPDATE: $INCIDENT_ID
Time: $(date)
Status: [INVESTIGATING|IDENTIFIED|FIXING|MONITORING|RESOLVED]
Progress: [What's been done]
Next Steps: [What's planned]
ETA: [Updated estimate]
```

### Resolution Notice
```
INCIDENT RESOLVED: $INCIDENT_ID
Duration: [Total time]
Root Cause: [Brief explanation]
Resolution: [What fixed it]
Impact: [Final impact assessment]
Post-mortem: [Link/date scheduled]
```

---

## Common Incident Playbooks

### WordPress Site Down
```bash
1. Check nginx/apache: systemctl status nginx
2. Check PHP: php -v
3. Check database socket: ls -la /path/to/mysqld.sock
4. Check WordPress: wp core verify-checksums
5. Review error logs: tail -100 /var/log/nginx/error.log
6. Enable debugging: WP_DEBUG=true in wp-config.php
7. Restore from backup if needed
```

### Database Connection Failed
```bash
1. Check MySQL running: ps aux | grep mysql
2. Verify socket path in wp-config.php
3. Test manual connection: mysql -u root -p
4. Check disk space: df -h
5. Review MySQL logs: tail /var/log/mysql/error.log
6. Restart MySQL if needed
7. Repair tables if corrupted: mysqlcheck --repair --all-databases
```

### Git Repository Corrupted
```bash
1. Run git fsck: git fsck --full
2. Check .git/objects: find .git/objects -type f | wc -l
3. Try git reflog: git reflog
4. Recover from remote: git fetch origin; git reset --hard origin/master
5. Restore from backup if needed
6. Validate: git log --oneline -10
```

### High Memory Usage
```bash
1. Identify processes: top -o %MEM
2. Check for memory leaks: ps aux --sort=-%mem | head -20
3. Kill runaway processes: kill -9 [PID]
4. Clear caches: sync; echo 3 > /proc/sys/vm/drop_caches
5. Restart services: systemctl restart [service]
6. Monitor: watch -n 5 free -h
```

---

## Incident Metrics to Track

1. **MTTR** (Mean Time To Recovery)
2. **MTTD** (Mean Time To Detect)
3. **Incident frequency by severity
4. **Root cause categories**
5. **Repeat incidents**
6. **After-hours incidents**

---

## Quick Reference

```bash
# Start incident
INCIDENT_ID="INC-$(date +%Y%m%d%H%M%S)"
mkdir -p /home/dave/skippy/incidents/$INCIDENT_ID

# Quick status check
systemctl is-system-running && echo "System OK" || echo "System DEGRADED"

# Enable maintenance mode
touch /path/to/wp/.maintenance

# Emergency rollback
git checkout HEAD~1
# or restore database backup
mysql < backup.sql

# Close incident
echo "RESOLVED: $(date)" >> incident.md
```

---

## Integration with Other Protocols

- **Health Check Protocol**: Proactive detection prevents incidents
- **Error Recovery Protocol**: Automated handling of common errors
- **Emergency Rollback Protocol**: Quick restoration procedures
- **API Key Lifecycle**: Key compromise is security incident
- **Backup Protocol**: Recovery depends on good backups

---

**Generated**: 2025-11-16
**Status**: Active
**Next Review**: 2025-12-16
