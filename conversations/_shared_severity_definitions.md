# Shared Severity Definitions

**Version:** 1.0.0
**Created:** 2025-11-05
**Purpose:** Centralized severity level definitions used by alert_management and incident_response protocols
**Status:** Reference Document

---

## Severity Levels

### P0 - Critical
**Response Time:** 15 minutes
**Impact:** Complete failure, active data loss, or security breach

**Examples:**
- Website completely down (HTTP 500/503)
- Database unavailable or corrupted
- Active security breach in progress
- Data loss occurring
- Payment/donation system down during critical period

**Escalation:**
- Immediate notification to all on-call personnel
- Create incident ticket automatically
- Begin incident response protocol
- Update status page (if applicable)

---

### P1 - High
**Response Time:** 1 hour
**Impact:** Major functionality unavailable, significant degradation

**Examples:**
- Core features broken (forms, registration, critical pages)
- Severe performance degradation (>5-10s load times)
- Backup failures
- Security vulnerability actively exploited
- Critical service unavailable

**Escalation:**
- Notify on-call person
- Create high-priority ticket
- Begin investigation immediately
- Communicate to key stakeholders

---

### P2 - Medium
**Response Time:** 4 hours (business hours)
**Impact:** Minor functionality issues, degraded experience

**Examples:**
- Single feature not working
- Performance degraded (3-5s load times)
- Disk space >80% full
- Warning-level errors in logs
- Non-critical service disruption
- Plugin/theme updates available

**Escalation:**
- Create ticket
- Schedule investigation
- Monitor for escalation to P1

---

### P3 - Low
**Response Time:** 24 hours / Next business day
**Impact:** Minimal user impact, minor issues

**Examples:**
- Cosmetic issues
- Minor performance degradation (2-3s load time)
- Disk space >70% full
- Info-level log entries
- Optimization opportunities
- Routine maintenance needed

**Escalation:**
- Create ticket for backlog
- Address during normal work hours
- Include in weekly review

---

### P4 - Info
**Response Time:** N/A
**Impact:** No user impact, informational only

**Examples:**
- Successful operations
- System status updates
- Metric reports
- Scheduled task completions
- Routine system events

**Escalation:**
- Log for reference
- No ticket needed
- Review in weekly reports

---

## Escalation Paths

### Automatic Escalation Triggers

**P0 Escalation (from P1):**
- Issue persists >2 hours without resolution
- Impact expands to affect more systems
- Data integrity concerns emerge
- Security implications discovered

**P1 Escalation (from P2):**
- Issue persists >8 hours
- User complaints increase significantly
- Performance continues degrading
- Workaround not possible

**P2 Escalation (from P3):**
- Issue persists >24 hours
- Minor issue becomes recurring
- Multiple related issues detected

### Manual Escalation

**When to Manually Escalate:**
- New information changes impact assessment
- Stakeholder requests escalation
- On-call engineer determines higher severity appropriate
- Pattern of issues indicates larger problem

**How to Escalate:**
1. Update ticket severity
2. Notify next level on-call
3. Document reason for escalation
4. Update communication plan
5. Follow new severity response procedures

---

## De-escalation

**When to De-escalate:**
- Immediate threat resolved
- Impact reduced significantly
- Workaround in place
- Root cause identified and contained

**Process:**
1. Verify reduced impact
2. Update ticket severity
3. Adjust communication frequency
4. Document reason for de-escalation
5. Continue resolution at new severity level

---

**Status:** ✅ ACTIVE
**Referenced By:**
- alert_management_protocol.md
- incident_response_protocol.md

**This is a shared reference document - do not duplicate this content in other protocols.**

---
