# Change Management Protocol

**Version:** 1.0.0
**Created:** 2025-11-05
**Owner:** Infrastructure Team
**Status:** Active
**Priority:** MEDIUM-HIGH

---

## Purpose

Establish formal procedures for requesting, reviewing, approving, and implementing changes to systems, ensuring controlled modifications while maintaining system stability and enabling quick rollback when needed.

**Focus:** Change request process, impact assessment, approval workflows, scheduling
**Integrates With:** deployment_checklist_protocol, authorization_protocol, incident_response_protocol

---

## Scope

This protocol applies to all changes including:
- Production system modifications
- Configuration changes
- Code deployments
- Database schema changes
- Infrastructure changes
- Third-party service changes
- Security updates
- Emergency hotfixes

---

## Change Categories

### Category 1: Standard Changes (Pre-Approved)
**Definition:** Routine, low-risk changes with established procedures
**Examples:**
- Content updates (blog posts, page edits)
- Plugin/theme updates (tested versions)
- Scheduled backups
- Log rotation
- Certificate renewals

**Process:**
- No formal approval needed
- Follow standard procedures
- Document in change log
- Notify team (FYI)

**Timeline:** Can be executed immediately

---

### Category 2: Minor Changes
**Definition:** Small, low-risk changes to existing functionality
**Examples:**
- CSS/styling tweaks
- Copy/text changes
- Minor bug fixes
- Configuration adjustments
- Non-critical plugin updates

**Process:**
- Submit change request
- Technical lead approval
- Test in staging (if applicable)
- Schedule deployment
- Document and deploy

**Timeline:** 1-3 days approval to deployment

---

### Category 3: Normal Changes
**Definition:** Moderate-risk changes requiring coordination
**Examples:**
- New features
- Database changes
- API integrations
- Major plugin updates
- Performance optimizations
- Access control changes

**Process:**
- Submit detailed change request
- Impact assessment required
- Manager approval required
- Test thoroughly in staging
- Schedule maintenance window
- Deployment with rollback plan
- Post-change verification

**Timeline:** 3-7 days approval to deployment

---

### Category 4: Major Changes
**Definition:** High-risk changes with significant impact
**Examples:**
- Architecture changes
- Major version upgrades
- Database migrations
- Server migrations
- Security overhauls
- Complete redesigns

**Process:**
- Submit comprehensive change proposal
- Multiple stakeholder approvals
- Detailed impact assessment
- Extensive testing period
- Scheduled maintenance window
- Full backup and rollback plan
- Staged rollout if possible
- Post-change review required

**Timeline:** 1-4 weeks approval to deployment

---

### Category 5: Emergency Changes
**Definition:** Urgent changes required to resolve critical issues
**Examples:**
- Security patches (critical vulnerabilities)
- System down/restoration
- Data corruption fixes
- Critical bug hotfixes

**Process:**
- Verbal approval from manager
- Document intent immediately
- Implement fix
- Verify resolution
- Formal documentation within 24 hours
- Post-incident review

**Timeline:** Immediate (approval within 15 minutes)

---

## Change Request Process

### Step 1: Submit Change Request

**Required Information:**
1. **Change ID** - Unique identifier (CHG-YYYY-MMDD-NNN)
2. **Requestor** - Who is requesting the change
3. **Category** - Standard/Minor/Normal/Major/Emergency
4. **Summary** - Brief description (1-2 sentences)
5. **Detailed Description** - What will change and why
6. **Business Justification** - Why this change is needed
7. **Systems Affected** - List all impacted systems
8. **Implementation Plan** - Step-by-step procedure
9. **Rollback Plan** - How to undo if it fails
10. **Testing Plan** - How it will be tested
11. **Proposed Schedule** - When to implement
12. **Risk Assessment** - Potential risks and mitigations

**Change Request Template:**
```markdown
# Change Request: CHG-2025-1105-001

## Summary
[Brief description]

## Category
☐ Standard  ☐ Minor  ☐ Normal  ☐ Major  ☐ Emergency

## Details
**Requested By:** [Name]
**Date Requested:** [YYYY-MM-DD]
**Desired Implementation Date:** [YYYY-MM-DD]

**Description:**
[Detailed description of what will change]

**Business Justification:**
[Why this change is needed]

**Systems Affected:**
- System 1
- System 2

**Implementation Plan:**
1. Step 1
2. Step 2
3. Step 3

**Rollback Plan:**
1. Step 1
2. Step 2

**Testing Plan:**
- Test 1
- Test 2

**Risk Assessment:**
- Risk 1: [Mitigation]
- Risk 2: [Mitigation]

## Approvals
- [ ] Technical Lead: __________ Date: ______
- [ ] Manager: __________ Date: ______
- [ ] Security (if applicable): __________ Date: ______

## Implementation
**Implemented By:** [Name]
**Implementation Date:** [YYYY-MM-DD]
**Implementation Time:** [HH:MM]
**Status:** ☐ Success  ☐ Failed  ☐ Rolled Back

## Verification
**Verified By:** [Name]
**Verification Date:** [YYYY-MM-DD]
**Result:** [Pass/Fail]

## Notes
[Any additional notes, issues encountered, lessons learned]
```

---

### Step 2: Impact Assessment

**Assess these factors:**

**Technical Impact:**
- Which systems are affected?
- What dependencies exist?
- What integrations might break?
- Database schema changes required?
- API changes required?

**User Impact:**
- How many users affected?
- Duration of service disruption?
- Critical functionality unavailable?
- Alternative workarounds available?

**Business Impact:**
- Revenue impact?
- Reputation impact?
- Legal/compliance impact?
- Deadline/time-sensitive impact?

**Risk Level:**
- Low: Minimal impact, easy rollback
- Medium: Some impact, rollback available
- High: Significant impact, complex rollback
- Critical: Severe impact, difficult rollback

---

### Step 3: Approval Workflow

#### Standard Changes
✅ **No approval needed** - Pre-approved procedures

#### Minor Changes
✅ **Technical Lead** approval required

#### Normal Changes
✅ **Technical Lead** + **Manager** approval required

#### Major Changes
✅ **Technical Lead** + **Manager** + **Stakeholders** approval required
✅ Security review if security-related

#### Emergency Changes
✅ **Manager** verbal approval (document within 24 hours)

**Approval Criteria:**
- Clear business justification
- Acceptable risk level
- Adequate testing plan
- Viable rollback plan
- Appropriate scheduling

---

### Step 4: Scheduling

**Maintenance Windows:**

**Preferred Windows (Lowest Traffic):**
- Sundays 2:00 AM - 6:00 AM
- Late nights (11:00 PM - 5:00 AM)

**Avoid:**
- Peak hours (Mon-Fri 9 AM - 5 PM)
- Major events or deadlines
- Holidays
- End of month/quarter (if fundraising deadline)

**Scheduling Rules:**
- **Minor:** Anytime with 24-hour notice
- **Normal:** Off-peak hours with 3-day notice
- **Major:** Maintenance window with 1-week notice
- **Emergency:** Immediate (no notice)

**Communication:**
- Notify team 72 hours in advance (normal changes)
- Notify team 1 week in advance (major changes)
- Status page update for user-facing changes
- Email supporters if significant impact

---

### Step 5: Implementation

**Pre-Implementation Checklist:**
- [ ] Change request approved
- [ ] Backup completed and verified
- [ ] Rollback plan documented and ready
- [ ] Testing completed in staging
- [ ] Team notified
- [ ] Maintenance mode ready (if needed)
- [ ] Monitoring dashboards open

**During Implementation:**
1. Execute change request following implementation plan
2. Document any deviations or issues
3. Monitor system health
4. Test critical paths
5. Verify expected behavior

**Post-Implementation:**
- [ ] Change completed successfully
- [ ] Critical paths verified
- [ ] System health normal
- [ ] Rollback NOT needed
- [ ] Maintenance mode disabled
- [ ] Team notified of completion
- [ ] Change request updated

---

### Step 6: Verification

**Verify these items:**
- Intended functionality works
- No unintended side effects
- Performance acceptable
- No errors in logs
- All systems operational
- User experience acceptable

**Verification Methods:**
- Automated tests
- Manual testing
- User acceptance testing
- Performance monitoring
- Error log review

---

### Step 7: Documentation

**Document these details:**
- What was changed
- When it was changed
- Who implemented it
- Verification results
- Any issues encountered
- Lessons learned

**Update these locations:**
- Change request ticket
- Change log file
- System documentation
- Team wiki (if applicable)

---

## Rollback Procedures

### When to Rollback

**Rollback immediately if:**
- Critical functionality broken
- Major errors occurring
- Performance severely degraded
- Security vulnerability introduced
- Data integrity compromised
- Cannot be fixed forward quickly

**Consider rollback if:**
- Minor errors occurring
- Performance degraded
- User complaints significant
- Fix-forward estimate > 30 minutes

---

### Rollback Process

**1. Initiate Rollback:**
- Notify team immediately
- Enable maintenance mode
- Document reason for rollback

**2. Execute Rollback:**
- Follow rollback plan from change request
- Restore from backup if needed
- Revert configuration changes
- Clear caches

**3. Verify Rollback:**
- Test critical paths
- Verify system stability
- Check error logs
- Monitor performance

**4. Document Rollback:**
- Update change request (status: Rolled Back)
- Document what failed and why
- Lessons learned
- Plan for re-attempt (if applicable)

---

## Change Log Maintenance

### Change Log Location
**File:** `/home/dave/skippy/logs/change_log.md`

### Change Log Format
```markdown
## 2025-11-05

### CHG-2025-1105-001: WordPress Plugin Update
**Category:** Minor
**Implemented By:** Dave
**Time:** 14:30
**Status:** Success
**Impact:** None
**Notes:** Updated Contact Form 7 to v5.8.5
```

---

## Change Freeze Periods

### When Changes Are Restricted

**Complete Freeze (Emergency only):**
- Major fundraising deadlines
- Critical campaign events
- During active incidents

**Partial Freeze (Normal+ changes restricted):**
- Week before major deadline
- Holiday periods
- Low-staffing periods

**Advance Notice:**
- Freeze periods announced 2 weeks in advance
- Emergency contact designated
- Exception process documented

---

## Metrics & KPIs

### Track These Metrics:

**Success Rate:**
- % of changes successful (target: >95%)
- % requiring rollback (target: <5%)

**Timing:**
- Average approval time by category
- Average implementation time by category

**Quality:**
- Changes causing incidents (target: <2%)
- Changes requiring emergency fixes (target: <1%)

**Process:**
- % of changes properly documented (target: 100%)
- % following approval process (target: 100%)

---

## Integration with Other Protocols

### With deployment_checklist_protocol:
- Change request approved before deployment
- Deployment checklist executed during implementation
- Both must be completed and documented

### With authorization_protocol:
- Changes requiring authorization noted in request
- Authorization obtained before implementation
- Document authorization in change request

### With incident_response_protocol:
- Failed changes may trigger incidents
- Emergency changes follow incident response
- Post-incident changes reviewed carefully

---

## Quick Reference

### Change Request Approval Matrix

| Category | Approver | Timeline | Notice |
|----------|----------|----------|--------|
| Standard | None (pre-approved) | Immediate | None |
| Minor | Technical Lead | 1-3 days | 24 hours |
| Normal | Lead + Manager | 3-7 days | 3 days |
| Major | Lead + Manager + Stakeholders | 1-4 weeks | 1 week |
| Emergency | Manager (verbal) | Immediate | None |

### Quick Commands

**Create change request:**
```bash
cp /home/dave/skippy/templates/change_request_template.md /home/dave/skippy/changes/CHG-$(date +%Y-%m%d)-001.md
```

**Log completed change:**
```bash
echo "### CHG-$(date +%Y-%m%d)-001: [Description]" >> /home/dave/skippy/logs/change_log.md
echo "**Status:** Success" >> /home/dave/skippy/logs/change_log.md
echo "" >> /home/dave/skippy/logs/change_log.md
```

**Review recent changes:**
```bash
tail -50 /home/dave/skippy/logs/change_log.md
```

---

## Common Scenarios

### Scenario 1: Plugin Update (Minor Change)

**Process:**
1. Submit change request (CHG-2025-MMDD-NNN)
2. Test plugin update in staging
3. Get technical lead approval
4. Schedule during low-traffic period
5. Create backup
6. Update plugin
7. Test critical paths
8. Document in change log

**Timeline:** 1-2 days

---

### Scenario 2: New Feature (Normal Change)

**Process:**
1. Submit detailed change request
2. Impact assessment
3. Get manager approval
4. Develop and test in staging
5. Schedule deployment window
6. Execute deployment checklist
7. Monitor closely post-deployment
8. Post-change review meeting

**Timeline:** 5-7 days

---

### Scenario 3: Security Patch (Emergency Change)

**Process:**
1. Security vulnerability identified
2. Verbal approval from manager
3. Document emergency change request
4. Test patch quickly in staging
5. Deploy immediately to production
6. Monitor for issues
7. Full documentation within 24 hours
8. Post-incident review

**Timeline:** 1-2 hours

---

## Best Practices

✅ **Do:**
- Always document changes
- Test before production
- Have rollback plan ready
- Communicate with team
- Schedule during low-traffic
- Monitor after changes
- Learn from failures

❌ **Don't:**
- Make undocumented changes
- Skip testing
- Deploy during peak hours
- Make changes without approval
- Forget to backup first
- Stack multiple changes
- Ignore rollback procedures

---

## Getting Started Checklist

**To implement this protocol:**

- [ ] Create `/home/dave/skippy/changes/` directory
- [ ] Create `/home/dave/skippy/templates/change_request_template.md`
- [ ] Create `/home/dave/skippy/logs/change_log.md`
- [ ] Document current maintenance windows
- [ ] Identify change freeze periods
- [ ] Train team on change process
- [ ] Set up change tracking system
- [ ] Schedule first quarterly review

---

**Status:** ✅ ACTIVE
**Version:** 1.0.0
**Last Updated:** 2025-11-05
**Integrates With:** deployment_checklist_protocol, authorization_protocol, incident_response_protocol

**All production changes must follow this protocol. Exceptions require manager approval.**

---
