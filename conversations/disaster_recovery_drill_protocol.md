# Disaster Recovery Drill Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Owner:** Infrastructure Team
**Status:** Active

---

## Purpose

Regularly test disaster recovery procedures to ensure they work when needed, identify gaps, and maintain team readiness for actual disasters.

## Scope

All disaster recovery procedures including:
- Full system restoration
- WordPress restoration
- Database restoration
- Failover procedures
- Backup verification
- Recovery time objectives (RTO)

---

## Drill Schedule

### Monthly (Lightweight)
- Backup verification only
- Restore to test environment
- Time: ~30 minutes
- Impact: None (test environment)

### Quarterly (Medium)
- Full WordPress restore drill
- Database restore drill
- Backup integrity verification
- Time: 2-3 hours
- Impact: Minimal (use staging)

### Annually (Full Scale)
- Complete disaster simulation
- Full system restore
- Failover testing
- Communication testing
- All hands drill
- Time: Half day
- Impact: Requires planning

### Ad-Hoc (After Major Changes)
- New backup system
- Infrastructure changes
- Major migrations
- Tool updates

---

## Monthly Backup Verification

### Objectives
- Verify backups are being created
- Confirm backups are not corrupted
- Test restore to non-production

### Procedure

**1. List Recent Backups:**
```bash
ls -lht /home/dave/skippy/backups/wordpress/ | head -5
ls -lht /home/dave/skippy/backups/database/ | head -5
ls -lht /home/dave/skippy/backups/full/ | head -5
```

**2. Select Most Recent Backup:**
```bash
LATEST_WP=$(ls -t /home/dave/skippy/backups/wordpress/wordpress_*.tar.gz | head -1)
LATEST_DB=$(ls -t /home/dave/skippy/backups/database/*.sql.gz | head -1)
```

**3. Verify Integrity:**
```bash
# Check if files are readable
tar -tzf "$LATEST_WP" > /dev/null
gunzip -t "$LATEST_DB"

# Check if encrypted backups can be decrypted
gpg --decrypt test.gpg > /dev/null 2>&1
```

**4. Test Restore (Test Environment):**
```bash
# Restore to /tmp/restore-test/
mkdir -p /tmp/restore-test
cd /tmp/restore-test

tar -xzf "$LATEST_WP"
gunzip < "$LATEST_DB" | head -100

# Verify key files present
ls -la
```

**5. Document Results:**
```markdown
## Monthly Backup Verification - [Date]

**Backups Checked:**
- WordPress: [filename] - [size]
- Database: [filename] - [size]

**Tests Performed:**
- ✓ Backup file integrity
- ✓ Extraction test
- ✓ Decryption test (if applicable)

**Results:** PASS / FAIL
**Issues Found:** [None / List issues]
**Time Taken:** [X minutes]
**Next Drill:** [Date]
```

---

## Quarterly WordPress Restore Drill

### Objectives
- Full WordPress restore capability
- Measure recovery time
- Verify data integrity
- Team practice

### Preparation (1 week before)

**1. Schedule Drill:**
- Pick date/time (avoid busy periods)
- Notify team
- Reserve test environment
- Prepare checklist

**2. Identify Baseline:**
```bash
# Document current state
wp post list --format=count
wp plugin list --format=count
wp theme list
wp db size
```

### Drill Execution

**1. Backup Current State:**
```bash
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh backup-wordpress
```

**2. Simulate Disaster:**
```bash
# (In test environment only!)
# Delete WordPress files
rm -rf /test/wordpress/wp-content/

# Corrupt database
# (Don't actually do this in production!)
```

**3. Execute Recovery:**
```bash
# Start timer
START_TIME=$(date +%s)

# Restore WordPress
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh restore-wordpress

# End timer
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "Recovery time: ${DURATION} seconds"
```

**4. Verify Recovery:**
```bash
# Check WordPress
wp core verify-checksums
wp db check

# Compare counts
wp post list --format=count
wp plugin list --format=count

# Test site functionality
curl -I http://test-site.local
wp user list

# Check critical pages
curl http://test-site.local/ | grep "Dave Biggers"
```

**5. Document Results:**
```markdown
## Quarterly DR Drill - [Date]

**Type:** WordPress Restore
**Environment:** Test/Staging
**Participants:** [Names]

**Scenario:** WordPress files deleted

**Recovery Steps:**
1. Identified disaster: [Time]
2. Located backup: [Time]
3. Began restore: [Time]
4. Completed restore: [Time]
5. Verified recovery: [Time]

**Total Recovery Time:** [X minutes]
**RTO Target:** 1 hour
**RTO Met:** YES / NO

**Verification Results:**
- ✓ Core files restored
- ✓ Plugins restored
- ✓ Themes restored
- ✓ Database intact
- ✓ Content present
- ✓ Site functional

**Issues Found:** [None / List]
**Improvements Needed:** [List]
**Action Items:** [List with owners]
```

---

## Annual Full Disaster Drill

### Objectives
- Complete system failure scenario
- Multi-system recovery
- Team coordination
- Communication testing
- Process validation

### Drill Scenario Examples

**Scenario 1: Complete Data Center Failure**
- All servers down
- No access to production
- Must restore from backups
- Build new infrastructure

**Scenario 2: Ransomware Attack**
- All systems encrypted
- Backups partially compromised
- Must identify clean backup
- Restore and verify integrity

**Scenario 3: Database Corruption**
- Database unrecoverable
- Must restore from backup
- Data loss acceptable
- Minimize downtime

### Full Drill Procedure

**Phase 1: Preparation (2 weeks before)**
- [ ] Schedule drill (half day)
- [ ] Notify all participants
- [ ] Prepare test environment
- [ ] Create drill scenario document
- [ ] Assign roles (IC, Tech Lead, Scribe)
- [ ] Review procedures
- [ ] Pre-position resources

**Phase 2: Kickoff (9:00 AM)**
- [ ] Brief all participants
- [ ] Distribute scenario
- [ ] Start timer
- [ ] Declare "disaster" started
- [ ] Begin documentation

**Phase 3: Assessment (15 min)**
- [ ] Assess situation
- [ ] Determine scope
- [ ] Identify what needs restoration
- [ ] Locate backups
- [ ] Make recovery plan

**Phase 4: Recovery (2-3 hours)**
- [ ] Execute recovery plan
- [ ] Document all steps
- [ ] Track time for each phase
- [ ] Communicate status updates
- [ ] Handle discovered issues

**Phase 5: Verification (30 min)**
- [ ] Test all critical functionality
- [ ] Verify data integrity
- [ ] Check all integrations
- [ ] User acceptance testing
- [ ] Performance testing

**Phase 6: Debrief (1 hour)**
- [ ] Review timeline
- [ ] Discuss what went well
- [ ] Identify problems
- [ ] Create action items
- [ ] Assign owners
- [ ] Schedule follow-ups

### Roles During Drill

**Disaster Coordinator (DC):**
- Presents scenario
- Tracks time
- Adds complications (optional)
- Evaluates response
- Leads debrief

**Incident Commander (IC):**
- Leads recovery effort
- Makes decisions
- Coordinates team
- Communicates status

**Technical Lead:**
- Executes recovery
- Troubleshoots issues
- Validates restoration

**Scribe:**
- Documents timeline
- Records decisions
- Tracks action items
- Takes notes

**Observers:**
- Watch and learn
- Ask questions after
- Provide feedback

---

## Recovery Time Objectives (RTO)

### Target RTOs

**Critical Systems (P0):**
- WordPress site: 1 hour
- Database: 30 minutes
- Email: 4 hours

**Important Systems (P1):**
- Volunteer registration: 4 hours
- Analytics: 8 hours
- Monitoring: 4 hours

**Standard Systems (P2):**
- Development: 24 hours
- Documentation: 48 hours

### Measuring RTO

**Track During Drills:**
- Detection time (how long to notice)
- Decision time (decide what to do)
- Preparation time (gather resources)
- Execution time (actual restore)
- Verification time (confirm working)

**Calculate:**
```
Total RTO = Detection + Decision + Preparation + Execution + Verification
```

**Example:**
```
Detection: 5 min (alert fired)
Decision: 10 min (assessed situation)
Preparation: 15 min (found backup, staged restore)
Execution: 25 min (ran restore script)
Verification: 10 min (tested functionality)
Total: 65 minutes (within 1 hour RTO)
```

---

## Recovery Point Objectives (RPO)

### Target RPOs

**Critical Data:**
- Database: 24 hours (daily backup)
- WordPress content: 24 hours
- User data: 24 hours

**Important Data:**
- Configurations: 1 week
- Logs: 1 day
- Reports: 1 week

### Testing RPO

**During Drill:**
- Note timestamp of backup used
- Compare to "disaster" time
- Calculate data loss
- Verify acceptable

**Example:**
```
Disaster occurred: 2025-11-04 14:00
Backup used: 2025-11-04 06:00 (8 hours old)
RPO target: 24 hours
RPO met: YES (8 < 24)
Data lost: 8 hours of changes
```

---

## Drill Evaluation Criteria

### Success Criteria

**✓ Drill Passes If:**
- RTO target met
- RPO target met
- All critical systems restored
- Data integrity verified
- No data loss beyond RPO
- Team followed procedures
- Documentation complete

**✗ Drill Fails If:**
- RTO exceeded significantly (>50%)
- Unable to restore from backup
- Critical functionality missing
- Major procedural gaps
- Poor team coordination

### Scoring

**Excellent (90-100%):**
- All success criteria met
- Exceeded RTO targets
- Smooth execution
- Minor improvements only

**Good (75-89%):**
- Most criteria met
- RTO targets met
- Some minor issues
- Improvements identified

**Needs Improvement (60-74%):**
- Some criteria missed
- RTO targets barely met
- Several issues
- Significant improvements needed

**Failed (<60%):**
- Major criteria missed
- RTO not met
- Critical issues
- Major rework required

---

## Common Drill Issues

### Issues Found in Drills

**Documentation Issues:**
- Outdated procedures
- Missing steps
- Incorrect paths
- Tool versions changed

**Technical Issues:**
- Backup corrupted
- Permissions wrong
- Dependencies missing
- Configuration drift

**Process Issues:**
- Unclear roles
- Poor communication
- Decision delays
- Coordination problems

### Addressing Issues

**During Drill:**
- Document all issues
- Work around if possible
- Note for improvement

**After Drill:**
- Prioritize issues
- Assign owners
- Set deadlines
- Track completion
- Test fixes in next drill

---

## Integration with DR Automation

### Using DR Automation Tool

**Full Backup:**
```bash
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh backup-full
```

**WordPress Backup:**
```bash
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh backup-wordpress
```

**Full Restore:**
```bash
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh restore-full
```

**WordPress Restore:**
```bash
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh restore-wordpress
```

**Test Recovery:**
```bash
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh test-recovery
```

**Create Snapshot:**
```bash
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh create-snapshot
```

---

## Drill Documentation

### Drill Report Template

```markdown
# Disaster Recovery Drill Report

**Date:** [Date]
**Type:** [Monthly/Quarterly/Annual]
**Scenario:** [Description]
**Participants:** [Names and roles]

## Executive Summary
[Brief overview of drill results]

## Drill Details
- **Start Time:** [Time]
- **End Time:** [Time]
- **Duration:** [X hours/minutes]
- **Environment:** [Test/Staging/Production]

## Scenario
[Describe the disaster scenario]

## Recovery Timeline
| Phase | Start | End | Duration |
|-------|-------|-----|----------|
| Detection | XX:XX | XX:XX | X min |
| Assessment | XX:XX | XX:XX | X min |
| Preparation | XX:XX | XX:XX | X min |
| Execution | XX:XX | XX:XX | X min |
| Verification | XX:XX | XX:XX | X min |
| **Total** | | | **XX min** |

## RTO/RPO Results
- **RTO Target:** [X hours]
- **RTO Actual:** [X hours]
- **RTO Met:** YES / NO
- **RPO Target:** [X hours]
- **RPO Actual:** [X hours]
- **RPO Met:** YES / NO

## What Went Well
- [Item 1]
- [Item 2]

## Issues Encountered
- [Issue 1]
- [Issue 2]

## Improvements Needed
- [Improvement 1]
- [Improvement 2]

## Action Items
- [ ] [Action 1] (Owner: [Name], Due: [Date])
- [ ] [Action 2] (Owner: [Name], Due: [Date])

## Overall Assessment
**Score:** [X/100]
**Status:** PASS / FAIL
**Recommendation:** [Continue/Improve procedures]

## Next Drill
**Scheduled:** [Date]
**Type:** [Monthly/Quarterly/Annual]
```

---

## Continuous Improvement

### After Each Drill

**Immediate (same day):**
- Complete drill report
- Share with team
- Create action items

**Within 1 week:**
- Update procedures
- Fix identified issues
- Update documentation
- Schedule training if needed

**Before Next Drill:**
- Verify fixes implemented
- Test improvements
- Review lessons learned

---

## Related Protocols
- Incident Response Protocol
- Data Retention Protocol
- Backup Strategy Protocol

---

**Version History:**
- 1.0.0 (2025-11-04): Initial protocol creation
