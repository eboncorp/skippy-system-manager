# Error Logging Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-10
**Owner:** Protocol Working Group
**Status:** Active


**Date Created**: 2025-10-28
**Purpose**: Standardized error logging and troubleshooting documentation
**Location**: `/home/dave/skippy/conversations/error_logs/`

## Overview

When errors occur during Claude sessions, proper logging helps with troubleshooting, learning from mistakes, and preventing future issues.

## Error Log Location

**All error logs save to**: `/home/dave/skippy/conversations/error_logs/`

### Directory Structure
```
/home/dave/skippy/conversations/error_logs/
├── YYYY-MM/                        - Monthly directories
│   ├── error_YYYY-MM-DD_HHMM.md   - Individual error logs
│   └── solutions_YYYY-MM-DD.md    - Solutions that worked
├── recurring/                      - Recurring issues tracker
├── resolved/                       - Permanently resolved issues
└── index.md                        - Error log index
```

## When to Create Error Logs

### Always Log
- ✅ Script failures with unclear cause
- ✅ Bash command errors that need investigation
- ✅ Permission denied errors
- ✅ Path not found errors (after reorganization)
- ✅ Package/dependency conflicts
- ✅ Git operation failures
- ✅ WordPress/database errors
- ✅ Network/connectivity issues
- ✅ Any error that blocks task completion

### Optional Logging
- Simple typos (unless recurring pattern)
- Expected validation failures
- User-requested cancellations

## Error Log Format

### Filename Convention
`error_YYYY-MM-DD_HHMM_brief_description.md`

**Examples**:
- `error_2025-10-28_1430_wordpress_database_connection.md`
- `error_2025-10-28_1445_script_permission_denied.md`
- `error_2025-10-28_1500_git_push_failed.md`

### Template

```markdown
# Error Log: [Brief Description]

**Date**: YYYY-MM-DD HH:MM
**Session**: [Session context if relevant]
**Task**: [What was being attempted]
**Severity**: [Critical/High/Medium/Low]
**Status**: [Investigating/Resolved/Workaround/Escalated]

## Error Details

### Error Message
```
[Exact error message from system]
```

### Context
- What was being done when error occurred
- Which directory/project
- Which files/scripts involved
- Any recent changes that might be related

### Command That Failed
```bash
[Exact command that produced error]
```

### Full Output
```
[Complete terminal output including error]
```

## Environment

- **OS**: Linux 6.8.0-65-generic
- **Working Directory**: /path/to/directory
- **User**: dave
- **Python Version**: [if relevant]
- **Node/npm Version**: [if relevant]
- **Other tools**: [versions if relevant]

## Investigation Steps

### What Was Tried
1. First attempt: [Description]
   - Result: [What happened]

2. Second attempt: [Description]
   - Result: [What happened]

3. Third attempt: [Description]
   - Result: [What happened]

### Diagnostic Commands Run
```bash
# List all diagnostic commands and their output
ls -la /path/to/check
cat /path/to/config
grep "pattern" /path/to/file
```

## Root Cause

### Analysis
[Detailed explanation of what caused the error]

### Contributing Factors
- Factor 1: [Description]
- Factor 2: [Description]
- Factor 3: [Description]

## Solution

### What Fixed It
[Detailed explanation of solution]

### Commands Used
```bash
# Exact commands that resolved the issue
command1
command2
command3
```

### Why It Worked
[Explanation of why this solution worked]

## Prevention

### How to Prevent This in Future
1. [Preventive measure 1]
2. [Preventive measure 2]
3. [Preventive measure 3]

### Checks to Add
- [ ] Check 1: [Description]
- [ ] Check 2: [Description]
- [ ] Check 3: [Description]

### Documentation Updates Needed
- Update file: [path/to/file]
- Add warning: [description]
- Create check: [description]

## Related Issues

### Similar Past Errors
- [Link to previous error log if similar]
- [Pattern recognition]

### Potentially Affected Areas
- Area 1: [Description]
- Area 2: [Description]

## Follow-Up Actions

- [ ] Test solution in different scenarios
- [ ] Update documentation
- [ ] Create preventive script/check
- [ ] Add to regular monitoring
- [ ] Notify user if recurring issue

## Tags

`category` `severity` `component` `status`

**Examples**:
- `wordpress` `high` `database` `resolved`
- `bash` `medium` `permissions` `resolved`
- `git` `low` `network` `workaround`

---

**Resolution Date**: YYYY-MM-DD HH:MM
**Time to Resolve**: [X hours/minutes]
**Resolved By**: [Claude/User/Collaboration]
```

## Quick Error Log Template

For faster logging:

```markdown
# Error: [Brief Title]

**Date**: YYYY-MM-DD HH:MM
**Task**: [What was attempted]

## Error
```
[Error message]
```

## Context
[What happened]

## Solution
[What fixed it]

## Prevention
[How to avoid it]

---
Tags: `category` `severity` `status`
```

## Error Index Maintenance

### Update Index File
Location: `/home/dave/skippy/conversations/error_logs/index.md`

**Format**:
```markdown
# Error Log Index

## 2025-10

### 2025-10-28
- **14:30** - [WordPress Database Connection](2025-10/error_2025-10-28_1430_wordpress_database_connection.md) - `RESOLVED`
- **14:45** - [Script Permission Denied](2025-10/error_2025-10-28_1445_script_permission_denied.md) - `RESOLVED`

## Statistics
- Total errors logged: X
- Resolved: X
- Recurring: X
- Critical: X
```

## Recurring Issues Tracking

### File Location
`/home/dave/skippy/conversations/error_logs/recurring/`

### When to Mark Recurring
If same error occurs 3+ times, create recurring issue doc:

```markdown
# Recurring Issue: [Description]

**First Occurrence**: YYYY-MM-DD
**Occurrences**: X times
**Last Seen**: YYYY-MM-DD

## Pattern
[Description of when/why it happens]

## Temporary Solutions
1. [Solution 1] - Works for X hours/days
2. [Solution 2] - Works but not ideal

## Root Cause Investigation
[Ongoing investigation notes]

## Permanent Solution Needed
[What would fix this permanently]

## Occurrences Log
- YYYY-MM-DD HH:MM - [Context] - [Solution used]
- YYYY-MM-DD HH:MM - [Context] - [Solution used]
```

## Critical Error Protocol

### Severity Levels

**Critical**: System down, data loss risk, security breach
- ✅ Log immediately
- ✅ Stop other tasks
- ✅ Focus on resolution
- ✅ Notify user
- ✅ Create detailed log

**High**: Task blocked, major functionality broken
- ✅ Log promptly
- ✅ Prioritize resolution
- ✅ Document thoroughly

**Medium**: Workaround available, minor impact
- ✅ Log for reference
- ✅ Resolve when convenient
- ✅ Note workaround

**Low**: Cosmetic, future improvement
- ⚠️ Optional logging
- Note in session summary

## Solutions Documentation

### Successful Solutions
Save to: `/home/dave/skippy/conversations/error_logs/YYYY-MM/solutions_YYYY-MM-DD.md`

**Format**:
```markdown
# Solutions Log - YYYY-MM-DD

## Solution 1: [Problem Description]
**Problem**: [What was wrong]
**Solution**: [What fixed it]
**Commands**:
```bash
[Commands used]
```
**Why it worked**: [Explanation]
**Reusable**: Yes/No

---

[Repeat for each solution]
```

## Automation Ideas

### Auto-Log Script (Future)
Create script to automatically capture:
- Error message
- Working directory
- Last commands run
- Timestamp
- Environment info

### Error Pattern Detection
- Track common error patterns
- Suggest solutions based on past logs
- Alert on recurring issues

## Best Practices

### During Error Investigation
1. ✅ Don't panic - errors are learning opportunities
2. ✅ Capture exact error message immediately
3. ✅ Note what you were doing when it occurred
4. ✅ Try to reproduce if possible
5. ✅ Document everything you try
6. ✅ Note what doesn't work (not just what works)

### Writing Error Logs
1. ✅ Be detailed - future you will thank you
2. ✅ Include context - why were you doing this?
3. ✅ Show exact commands - not paraphrased
4. ✅ Explain solution clearly
5. ✅ Add prevention steps
6. ✅ Use tags for searchability

### After Resolution
1. ✅ Update error log with solution
2. ✅ Add to index
3. ✅ Create prevention measures if needed
4. ✅ Update relevant documentation
5. ✅ Check for similar potential issues

## Integration with Other Protocols

### Script Creation
When script errors occur:
- Log to error_logs/
- Reference in script header if relevant
- Update script protocol if needed

### Git Workflow
When git errors occur:
- Log details
- Document resolution
- Update git protocol if needed

### WordPress Issues
When WordPress errors occur:
- Log with WordPress tag
- Include WP-CLI commands attempted
- Document database state if relevant

## Quick Commands

### Create Monthly Directory
```bash
mkdir -p /home/dave/skippy/conversations/error_logs/$(date +%Y-%m)
```

### Start New Error Log
```bash
cd /home/dave/skippy/conversations/error_logs/$(date +%Y-%m)
touch error_$(date +%Y-%m-%d_%H%M)_brief_description.md
```

### Search Error Logs
```bash
grep -r "search term" /home/dave/skippy/conversations/error_logs/
```

### List Recent Errors
```bash
ls -lt /home/dave/skippy/conversations/error_logs/$(date +%Y-%m)/ | head -10
```

## Examples

### Example 1: Permission Error
See: `/home/dave/skippy/conversations/error_logs/examples/permission_error_example.md`

### Example 2: Path Not Found After Reorganization
See: `/home/dave/skippy/conversations/error_logs/examples/path_error_example.md`

### Example 3: WordPress Database Connection
See: `/home/dave/skippy/conversations/error_logs/examples/wordpress_db_error_example.md`

---

**This protocol is part of the persistent memory system.**
**Reference this file when errors occur during sessions.**
```
