# Error Recovery Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

Errors happen during work sessions. This protocol defines how to handle errors gracefully, recover quickly, and learn from failures.

## Purpose

- Minimize downtime when errors occur
- Provide clear error information
- Attempt automatic recovery
- Know when to escalate vs continue
- Document error patterns for prevention

---

## Error Categories

### Category 1: Transient Errors (Auto-Retry)
**Examples:**
- Network timeouts
- Temporary file locks
- Rate limiting
- Connection refused (service starting)

**Action:** Retry 2-3 times with backoff

### Category 2: Permission Errors (Fixable)
**Examples:**
- File not executable
- Directory not writable
- User not in docker group

**Action:** Fix permissions, retry

### Category 3: Configuration Errors (User Input Needed)
**Examples:**
- Missing .env file
- Invalid configuration
- Missing credentials

**Action:** Explain what's needed, wait for user

### Category 4: Code Errors (Debug Required)
**Examples:**
- Syntax errors in scripts
- Logic errors
- Unexpected behavior

**Action:** Debug, fix, or suggest workaround

### Category 5: External Dependency Errors (May Block)
**Examples:**
- Service is down
- External API unavailable
- Database offline

**Action:** Verify status, suggest alternatives or waiting

---

## Recovery Procedure

### Step 1: Error Detection
```
Claude automatically:
- Captures full error message
- Identifies error type/category
- Determines severity
```

### Step 2: Initial Response
```
For transient errors:
→ Retry automatically (up to 3 times)

For fixable errors:
→ Attempt automatic fix
→ Retry operation

For configuration errors:
→ Explain what's missing
→ Wait for user input

For serious errors:
→ Stop operation
→ Explain problem clearly
→ Suggest alternatives
```

### Step 3: Communication
```
Claude tells user:
- What went wrong (clear explanation)
- What was attempted (retry, fix, etc.)
- What's needed (user action, if any)
- Alternative approaches (if available)
```

### Step 4: Alternative Solutions
```
If primary approach fails:
- Suggest backup approach
- Use different tool
- Manual steps as fallback
- Document workaround
```

---

## Examples

### Example 1: Network Timeout (Transient)

**Error:**
```
curl: (28) Connection timed out after 30000 milliseconds
```

**Claude Response:**
```
Network timeout occurred while fetching data. Retrying...

Attempt 1: Failed (timeout)
Attempt 2: Failed (timeout)
Attempt 3: Success ✓

Continuing with operation...
```

### Example 2: Permission Denied (Fixable)

**Error:**
```
bash: ./deploy.sh: Permission denied
```

**Claude Response:**
```
Script is not executable. Fixing permissions...

chmod +x ./deploy.sh
✓ Permissions fixed

Retrying deployment...
bash ./deploy.sh
✓ Deployment started successfully
```

### Example 3: Missing Configuration (User Input Needed)

**Error:**
```
Error: .env file not found
```

**Claude Response:**
```
The .env file is missing. This file contains required configuration.

I can create a template .env file with placeholders.
Would you like me to:

1. Create .env.example showing required variables
2. Create .env with default values (you'll need to edit)
3. Wait while you create .env manually

Which approach would you prefer?
```

### Example 4: WordPress Health Check Failure (Informational)

**Error:**
```
wp: Error establishing database connection
```

**Claude Response:**
```
WordPress can't connect to the database.

Possible causes:
1. Database service is not running
2. Credentials in wp-config.php are incorrect
3. Database server is down

Quick checks:
- Is this the production or local site? (matters for troubleshooting)
- Was the database working recently?
- Any recent configuration changes?

I can help diagnose further if you'd like.
```

### Example 5: Git Push Failure (Action Required)

**Error:**
```
! [rejected] master -> master (fetch first)
error: failed to push some refs
```

**Claude Response:**
```
Git push rejected - remote has changes we don't have locally.

This typically means someone else pushed changes.

Safe approach:
1. Fetch remote changes: git fetch origin
2. Review differences: git log HEAD..origin/master
3. Merge or rebase (your choice)
4. Push again

Would you like me to:
- Show what changed on remote
- Pull and merge automatically
- Let you handle it manually
```

---

## Retry Strategy

### Automatic Retry Conditions
```python
retry_errors = [
    "Connection timed out",
    "Connection refused",
    "Temporary failure",
    "Resource temporarily unavailable",
    "Too many requests"  # Rate limiting
]

retry_attempts = 3
backoff_seconds = [1, 5, 10]  # 1s, 5s, 10s delays
```

### No Retry Conditions
```python
no_retry_errors = [
    "Permission denied",
    "No such file or directory",
    "Invalid syntax",
    "Authentication failed",
    "Not found (404)"
]
```

---

## When to Stop vs Continue

### Continue (Errors Expected)
✅ Testing new code
✅ Network operations with retry
✅ Non-critical operations
✅ User explicitly says "keep going"

### Stop (Errors Serious)
🛑 Data loss risk
🛑 Security credential exposure
🛑 Production system impact
🛑 Repeated failures (3+ times)
🛑 Unclear how to proceed

---

## Error Documentation

### For Recurring Errors
```markdown
Document in conversation summary:

## Error Encountered
[Error message]

## Cause
[Root cause analysis]

## Solution Applied
[What fixed it]

## Prevention
[How to avoid in future]
```

### Example Documentation
```markdown
## Error: WordPress Database Connection Failed

**Cause:** Local database service not running after system reboot

**Solution:** sudo systemctl start mysql

**Prevention:** Enable mysql to start on boot:
sudo systemctl enable mysql

**Related:** This happens after system updates that restart services.
```

---

## User Guidance Options

### When Error Occurs, User Can Say:

**"Keep trying"**
→ Claude continues despite errors

**"Try a different approach"**
→ Claude suggests alternatives

**"Stop and explain"**
→ Claude stops, gives detailed error analysis

**"Show me the full error"**
→ Claude displays complete error output

**"That's expected, continue"**
→ Claude proceeds, ignoring the error

**"Let me fix it"**
→ Claude pauses, waits for user action

---

## Best Practices

### DO:
✅ Explain errors clearly in plain language
✅ Attempt automatic recovery when safe
✅ Provide alternatives when blocked
✅ Document solutions for recurring errors
✅ Know when to stop vs retry

### DON'T:
❌ Retry indefinitely
❌ Hide errors from user
❌ Give up immediately on first error
❌ Proceed with risky operations after errors
❌ Use technical jargon without explanation

---

## Quick Reference

### Error Response Pattern
```
1. What happened (plain language)
2. What I tried (auto-fix attempts)
3. Current status (working/blocked/need input)
4. Next steps (options for user)
```

### Example Template
```
❌ Error: [Plain language description]

What I tried:
- [Attempt 1]: [Result]
- [Attempt 2]: [Result]

Status: [Blocked/Waiting/Alternative Available]

Options:
1. [Option 1]
2. [Option 2]
3. [Option 3]

What would you like to do?
```

---

## Integration

**Related Protocols:**
- [Verification Protocol](verification_protocol.md) - Confirm operations succeeded
- [Safety and Backup Protocol](safety_backup_protocol.md) - Prevent errors
- [Work Session Documentation Protocol](work_session_documentation_protocol.md) - Document errors

---

## Version History

**1.0.0 (2025-11-06)**
- Initial protocol creation
- Defined error categories
- Established retry strategy
- Added examples

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
