# Error Recovery Protocol

**Version:** 2.0.0
**Last Updated:** 2025-11-16
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

## Circuit Breaker Pattern (NEW in v2.0)

The circuit breaker prevents cascading failures by temporarily stopping operations that are likely to fail.

### Circuit States

```
[CLOSED] ─── failure threshold exceeded ───> [OPEN]
    ↑                                           │
    │                                           │
    └──── success ──── [HALF-OPEN] <── timeout expires
```

**CLOSED**: Normal operation, requests pass through
**OPEN**: Circuit tripped, all requests immediately fail
**HALF-OPEN**: Testing if service recovered, limited requests allowed

### Configuration

```python
circuit_breaker = {
    "failure_threshold": 3,        # Failures before opening
    "success_threshold": 2,        # Successes to close
    "timeout_seconds": 60,         # Time before half-open
    "half_open_max_calls": 1,      # Test calls in half-open
}
```

### Implementation

```bash
#!/bin/bash
# circuit_breaker.sh - Wraps commands with circuit breaker logic

CIRCUIT_STATE_FILE="/tmp/circuit_breaker_state"
FAILURE_COUNT_FILE="/tmp/circuit_breaker_failures"
LAST_FAILURE_FILE="/tmp/circuit_breaker_last_failure"

# Configuration
FAILURE_THRESHOLD=3
TIMEOUT_SECONDS=60

get_state() {
    if [ -f "$CIRCUIT_STATE_FILE" ]; then
        cat "$CIRCUIT_STATE_FILE"
    else
        echo "CLOSED"
    fi
}

get_failures() {
    if [ -f "$FAILURE_COUNT_FILE" ]; then
        cat "$FAILURE_COUNT_FILE"
    else
        echo "0"
    fi
}

check_timeout() {
    if [ -f "$LAST_FAILURE_FILE" ]; then
        LAST_FAILURE=$(cat "$LAST_FAILURE_FILE")
        CURRENT_TIME=$(date +%s)
        ELAPSED=$((CURRENT_TIME - LAST_FAILURE))
        if [ "$ELAPSED" -ge "$TIMEOUT_SECONDS" ]; then
            return 0  # Timeout expired
        fi
    fi
    return 1  # Still within timeout
}

execute_with_circuit_breaker() {
    COMMAND="$1"
    STATE=$(get_state)

    case $STATE in
        "OPEN")
            if check_timeout; then
                echo "HALF-OPEN" > "$CIRCUIT_STATE_FILE"
                echo "Circuit breaker: Testing recovery..."
            else
                echo "Circuit breaker OPEN: Service unavailable, skipping operation"
                return 1
            fi
            ;;
        "HALF-OPEN")
            echo "Circuit breaker: Testing recovery..."
            ;;
        "CLOSED")
            # Normal operation
            ;;
    esac

    # Execute command
    if eval "$COMMAND"; then
        # Success
        FAILURES=$(get_failures)
        if [ "$FAILURES" -gt 0 ]; then
            FAILURES=$((FAILURES - 1))
            echo "$FAILURES" > "$FAILURE_COUNT_FILE"
        fi

        if [ "$(get_state)" == "HALF-OPEN" ]; then
            echo "CLOSED" > "$CIRCUIT_STATE_FILE"
            echo "0" > "$FAILURE_COUNT_FILE"
            echo "Circuit breaker: Service recovered, circuit CLOSED"
        fi
        return 0
    else
        # Failure
        FAILURES=$(get_failures)
        FAILURES=$((FAILURES + 1))
        echo "$FAILURES" > "$FAILURE_COUNT_FILE"
        date +%s > "$LAST_FAILURE_FILE"

        if [ "$FAILURES" -ge "$FAILURE_THRESHOLD" ]; then
            echo "OPEN" > "$CIRCUIT_STATE_FILE"
            echo "Circuit breaker OPEN: Threshold exceeded ($FAILURES failures)"
        fi
        return 1
    fi
}

# Reset circuit breaker
reset_circuit_breaker() {
    rm -f "$CIRCUIT_STATE_FILE" "$FAILURE_COUNT_FILE" "$LAST_FAILURE_FILE"
    echo "Circuit breaker reset to CLOSED state"
}

# Usage example:
# execute_with_circuit_breaker "curl -s https://api.example.com/health"
```

### Use Cases

**API Calls**: Prevent hammering a down service
```bash
# Instead of:
curl https://api.service.com/data

# Use:
execute_with_circuit_breaker "curl https://api.service.com/data"
```

**Database Operations**: Avoid repeated connection attempts
```bash
execute_with_circuit_breaker "mysql -u root -p'pass' -e 'SELECT 1'"
```

**External Services**: Stop cascading failures
```bash
execute_with_circuit_breaker "gh api /user"
```

### Monitoring Circuit Breaker

```bash
# Check current state
cat /tmp/circuit_breaker_state

# Check failure count
cat /tmp/circuit_breaker_failures

# Reset after fixing issue
reset_circuit_breaker
```

### When to Use

- External API calls
- Database connections
- Network operations
- Third-party service integrations
- Any operation with repeated failures

### When NOT to Use

- One-time operations
- User-initiated retries
- Operations that must succeed
- Local file operations

---

## Exponential Backoff Strategy (NEW in v2.0)

Prevents thundering herd problem with exponential delays.

```bash
exponential_backoff() {
    local attempt=$1
    local base_delay=1
    local max_delay=60
    local jitter=$((RANDOM % 1000))

    # Calculate delay: base * 2^attempt + random jitter
    local delay=$(( base_delay * (2 ** attempt) ))

    # Cap at max delay
    if [ "$delay" -gt "$max_delay" ]; then
        delay=$max_delay
    fi

    # Add jitter (0-1 second)
    local jitter_seconds=$(echo "scale=3; $jitter/1000" | bc)
    local total_delay=$(echo "$delay + $jitter_seconds" | bc)

    echo "Waiting ${total_delay}s before retry (attempt $attempt)..."
    sleep "$total_delay"
}

# Usage:
# for attempt in 1 2 3 4 5; do
#     if operation_succeeds; then
#         break
#     fi
#     exponential_backoff $attempt
# done
```

### Backoff Schedule Example

| Attempt | Base Delay | With Jitter (example) |
|---------|-----------|------------------------|
| 1 | 2s | 2.347s |
| 2 | 4s | 4.821s |
| 3 | 8s | 8.156s |
| 4 | 16s | 16.492s |
| 5 | 32s | 32.089s |
| 6+ | 60s (capped) | 60.XXXs |

---

## Graceful Degradation (NEW in v2.0)

When primary approach fails, fall back to alternatives.

```bash
graceful_operation() {
    local operation=$1

    # Try primary approach
    if primary_method "$operation"; then
        return 0
    fi

    echo "Primary method failed, trying fallback..."

    # Try secondary approach
    if fallback_method "$operation"; then
        echo "Fallback succeeded"
        return 0
    fi

    echo "Fallback failed, using minimal mode..."

    # Minimal functionality
    if minimal_mode "$operation"; then
        echo "Operating in degraded mode"
        return 0
    fi

    echo "All methods failed"
    return 1
}
```

### Example: WordPress Database Query

```bash
# Primary: WP-CLI
if wp post list --allow-root 2>/dev/null; then
    echo "Used WP-CLI"

# Fallback: Direct MySQL
elif mysql -u root -p'root' local -e "SELECT ID FROM wp_posts LIMIT 1" 2>/dev/null; then
    echo "Used direct MySQL"

# Minimal: Check if site responds
elif curl -s "http://site.local/" | grep -q "WordPress"; then
    echo "Site is up, database queries unavailable"

else
    echo "Site completely unavailable"
fi
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
```
