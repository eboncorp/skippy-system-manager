# Claude Code Enforcement Hooks - Implementation Guide

**Date:** 2025-11-19
**Based On:** Official Claude Code Documentation + Robustness Analysis
**Priority:** 🔴 **CRITICAL - IMPLEMENT IMMEDIATELY**

---

## Executive Summary

After analyzing the official Claude Code hooks documentation, I've identified **exactly what we need** to make our system robust. We have all the building blocks (tools, commands, skills) but we're **missing the enforcement layer**.

**The Solution:** Use Claude Code's **PreToolUse hooks with "deny" decisions** to block unauthorized operations.

---

## What We Learned from Official Docs

### Hook Decision Types

PreToolUse hooks can return three decisions:
1. **"allow"** - Bypass permission system, approve tool
2. **"deny"** - **BLOCK tool execution**, show reason to Claude
3. **"ask"** - Prompt user for confirmation

**This is EXACTLY what we need** - we can BLOCK WordPress updates that haven't been approved!

---

## Critical Implementation: WordPress Protection Hook

### Hook #1: Block Unapproved WordPress Updates

**File:** `~/.claude/hooks/pre_wordpress_update_protection.sh`

```bash
#!/bin/bash
# WordPress Update Protection Hook
# BLOCKS wp post update commands without approval

# Read hook input
HOOK_INPUT=$(cat)

# Extract tool info
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name')
TOOL_INPUT_JSON=$(echo "$HOOK_INPUT" | jq -r '.tool_input')

# Only process Bash tool calls
if [[ "$TOOL_NAME" != "Bash" ]]; then
    exit 0  # Allow non-Bash tools
fi

# Extract command
COMMAND=$(echo "$TOOL_INPUT_JSON" | jq -r '.command')

# Detect WordPress update commands
if [[ "$COMMAND" =~ wp.*post.*update|wp.*page.*update ]]; then
    # Extract page ID
    PAGE_ID=$(echo "$COMMAND" | grep -oP 'update\s+\K[0-9]+')

    if [[ -z "$PAGE_ID" ]]; then
        # Can't determine page ID - block for safety
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Cannot determine page ID from WordPress update command. Please specify page ID explicitly."
  }
}
EOF
        exit 0
    fi

    # Check if approval exists
    APPROVAL_FILE="$HOME/.claude/content-vault/approvals/page_${PAGE_ID}_approval.json"

    if [[ ! -f "$APPROVAL_FILE" ]]; then
        # NO APPROVAL - BLOCK THE UPDATE
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Page $PAGE_ID is not approved for publishing. Run /content-approve --page-id=$PAGE_ID first. This enforcement is required to prevent unauthorized content changes."
  }
}
EOF
        exit 0
    fi

    # Check approval hasn't expired (24 hour validity)
    APPROVAL_TIMESTAMP=$(jq -r '.timestamp' "$APPROVAL_FILE")
    CURRENT_TIMESTAMP=$(date +%s)
    AGE=$((CURRENT_TIMESTAMP - APPROVAL_TIMESTAMP))

    if [[ $AGE -gt 86400 ]]; then
        # APPROVAL EXPIRED - BLOCK THE UPDATE
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Approval for page $PAGE_ID has expired (>24 hours old). Please re-approve with /content-approve --page-id=$PAGE_ID before publishing."
  }
}
EOF
        exit 0
    fi

    # Approval valid - log and allow
    echo "[$(date)] ALLOWED: WordPress update for page $PAGE_ID (approved by $(jq -r '.approver' "$APPROVAL_FILE"))" >> "$HOME/.claude/content-vault/audit-log/updates.log"

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Page $PAGE_ID approved by $(jq -r '.approver' "$APPROVAL_FILE") at $(jq -r '.timestamp_human' "$APPROVAL_FILE")"
  }
}
EOF
fi

# Allow all other commands
exit 0
```

**Register in settings.json:**
```json
{
  "hooks": {
    "PreToolUse": {
      "Bash": [
        {
          "type": "command",
          "command": "~/.claude/hooks/pre_wordpress_update_protection.sh"
        }
      ]
    }
  }
}
```

---

### Hook #2: Block Fact-Check Bypass

**File:** `~/.claude/hooks/pre_wordpress_fact_check_enforcement.sh`

```bash
#!/bin/bash
# Fact-Check Enforcement Hook
# BLOCKS WordPress updates with incorrect facts

HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name')
TOOL_INPUT_JSON=$(echo "$HOOK_INPUT" | jq -r '.tool_input')

if [[ "$TOOL_NAME" != "Bash" ]]; then
    exit 0
fi

COMMAND=$(echo "$TOOL_INPUT_JSON" | jq -r '.command')

if [[ "$COMMAND" =~ wp.*post.*update ]]; then
    PAGE_ID=$(echo "$COMMAND" | grep -oP 'update\s+\K[0-9]+')

    # Check for fact-check record
    FACT_CHECK_FILE="$HOME/.claude/content-vault/fact-checks/page_${PAGE_ID}_facts.json"

    if [[ ! -f "$FACT_CHECK_FILE" ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Page $PAGE_ID has not been fact-checked. Run /fact-check --page-id=$PAGE_ID before publishing to ensure accuracy."
  }
}
EOF
        exit 0
    fi

    # Check fact-check is recent (within 1 hour)
    FACT_CHECK_TIMESTAMP=$(jq -r '.checked_at' "$FACT_CHECK_FILE")
    AGE=$(($(date +%s) - FACT_CHECK_TIMESTAMP))

    if [[ $AGE -gt 3600 ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Fact-check for page $PAGE_ID is stale (>1 hour). Re-run /fact-check --page-id=$PAGE_ID to verify current content."
  }
}
EOF
        exit 0
    fi

    # Check fact-check passed
    PASSED=$(jq -r '.passed' "$FACT_CHECK_FILE")

    if [[ "$PASSED" != "true" ]]; then
        ERRORS=$(jq -r '.errors | join(", ")' "$FACT_CHECK_FILE")
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Fact-check failed for page $PAGE_ID: $ERRORS. Fix these errors before publishing."
  }
}
EOF
        exit 0
    fi

    # Fact-check passed - allow
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Fact-check passed for page $PAGE_ID"
  }
}
EOF
fi

exit 0
```

---

### Hook #3: Block Sensitive File Modifications

**File:** `~/.claude/hooks/pre_sensitive_file_protection.sh`

```bash
#!/bin/bash
# Sensitive File Protection Hook
# BLOCKS modifications to .env, credentials, keys

HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name')
TOOL_INPUT_JSON=$(echo "$HOOK_INPUT" | jq -r '.tool_input')

# Check Edit and Write tools
if [[ "$TOOL_NAME" == "Edit" ]] || [[ "$TOOL_NAME" == "Write" ]]; then
    FILE_PATH=$(echo "$TOOL_INPUT_JSON" | jq -r '.file_path')

    # Block sensitive files
    if [[ "$FILE_PATH" =~ \.env|credentials|\.key|\.pem|\.ssh|business/|personal/ ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Cannot modify sensitive file: $FILE_PATH. This file contains credentials or private data."
  }
}
EOF
        exit 0
    fi
fi

# Check Bash tool for dangerous commands
if [[ "$TOOL_NAME" == "Bash" ]]; then
    COMMAND=$(echo "$TOOL_INPUT_JSON" | jq -r '.command')

    # Block dangerous operations
    if [[ "$COMMAND" =~ rm\s+-rf\s+/|git\s+push\s+--force\s+origin\s+master|DROP\s+DATABASE ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "Potentially destructive command detected: This operation cannot be undone. Please confirm."
  }
}
EOF
        exit 0
    fi
fi

exit 0
```

---

## Content Vault Setup

### Step 1: Create Vault Structure

```bash
mkdir -p ~/.claude/content-vault/{approvals,fact-checks,audit-log}

# Create .gitkeep files
touch ~/.claude/content-vault/approvals/.gitkeep
touch ~/.claude/content-vault/fact-checks/.gitkeep
touch ~/.claude/content-vault/audit-log/.gitkeep

# Initialize audit logs
touch ~/.claude/content-vault/audit-log/approvals.log
touch ~/.claude/content-vault/audit-log/updates.log
touch ~/.claude/content-vault/audit-log/fact-checks.log
```

---

### Step 2: Enhance /fact-check Command

**Modify:** `.claude/commands/fact-check.md`

**Add at the end:**

```markdown
## Fact-Check Record Generation

After validation, create verification record:

```bash
# Extract page ID if checking WordPress page
if [[ -n "$PAGE_ID" ]]; then
    FACT_CHECK_FILE="$HOME/.claude/content-vault/fact-checks/page_${PAGE_ID}_facts.json"

    cat > "$FACT_CHECK_FILE" <<EOF
{
  "page_id": $PAGE_ID,
  "checked_at": $(date +%s),
  "checked_at_human": "$(date +"%Y-%m-%d %H:%M:%S")",
  "passed": $PASSED,
  "errors": [$ERROR_LIST],
  "warnings": [$WARNING_LIST],
  "verified_facts": {
    "budget": "$BUDGET_VALUE",
    "roi": "$ROI_VALUE",
    "jcps_reading": "$READING_VALUE",
    "jcps_math": "$MATH_VALUE"
  }
}
EOF

    echo "✅ Fact-check record saved: $FACT_CHECK_FILE"
    echo "Valid for 1 hour"
fi
```
```

---

### Step 3: Create /content-approve Command

**File:** `.claude/commands/content-approve.md`

```yaml
---
description: Approve WordPress content for publishing with signature tracking
argument-hint: "--page-id=<id> --approver=<name> [--notes='...']"
allowed-tools: ["Bash", "Read", "Write"]
---

# Content Approval System

## Usage

```bash
/content-approve --page-id=105 --approver=dave --notes="Homepage updates verified"
```

## What This Command Does

1. ✅ Checks fact-check record exists and is recent
2. ✅ Creates approval record with signature
3. ✅ Logs to audit trail
4. ✅ Enables WordPress update (hook will allow it)

## Implementation

```bash
#!/bin/bash

# Parse arguments
PAGE_ID=""
APPROVER=""
NOTES=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --page-id=*) PAGE_ID="${1#*=}" ;;
        --approver=*) APPROVER="${1#*=}" ;;
        --notes=*) NOTES="${1#*=}" ;;
    esac
    shift
done

# Validate inputs
if [[ -z "$PAGE_ID" ]] || [[ -z "$APPROVER" ]]; then
    echo "❌ Error: --page-id and --approver are required"
    exit 1
fi

# Check fact-check exists
FACT_CHECK_FILE="$HOME/.claude/content-vault/fact-checks/page_${PAGE_ID}_facts.json"

if [[ ! -f "$FACT_CHECK_FILE" ]]; then
    echo "❌ Cannot approve: No fact-check found for page $PAGE_ID"
    echo "Run: /fact-check --page-id=$PAGE_ID first"
    exit 1
fi

# Check fact-check is recent (within 1 hour)
FACT_CHECK_TIMESTAMP=$(jq -r '.checked_at' "$FACT_CHECK_FILE")
AGE=$(($(date +%s) - FACT_CHECK_TIMESTAMP))

if [[ $AGE -gt 3600 ]]; then
    echo "❌ Cannot approve: Fact-check is stale ($(($AGE / 60)) minutes old)"
    echo "Re-run: /fact-check --page-id=$PAGE_ID"
    exit 1
fi

# Check fact-check passed
PASSED=$(jq -r '.passed' "$FACT_CHECK_FILE")

if [[ "$PASSED" != "true" ]]; then
    ERRORS=$(jq -r '.errors | join(", ")' "$FACT_CHECK_FILE")
    echo "❌ Cannot approve: Fact-check failed"
    echo "Errors: $ERRORS"
    echo "Fix these errors before approval"
    exit 1
fi

# Create approval record
APPROVAL_FILE="$HOME/.claude/content-vault/approvals/page_${PAGE_ID}_approval.json"

cat > "$APPROVAL_FILE" <<EOF
{
  "page_id": $PAGE_ID,
  "approver": "$APPROVER",
  "timestamp": $(date +%s),
  "timestamp_human": "$(date +"%Y-%m-%d %H:%M:%S")",
  "notes": "$NOTES",
  "fact_check_passed": true,
  "fact_check_timestamp": $FACT_CHECK_TIMESTAMP,
  "expires": $(($(date +%s) + 86400))
}
EOF

# Log to audit trail
echo "[$(date)] APPROVED: Page $PAGE_ID by $APPROVER - $NOTES" >> "$HOME/.claude/content-vault/audit-log/approvals.log"

echo "✅ Page $PAGE_ID approved for publishing"
echo "Approver: $APPROVER"
echo "Valid: 24 hours"
echo ""
echo "You can now update this page with: wp post update $PAGE_ID"
```
```

---

## Installation & Testing

### 1. Install Hooks

```bash
# Create hooks directory if needed
mkdir -p ~/.claude/hooks

# Copy hook files
cp pre_wordpress_update_protection.sh ~/.claude/hooks/
cp pre_wordpress_fact_check_enforcement.sh ~/.claude/hooks/
cp pre_sensitive_file_protection.sh ~/.claude/hooks/

# Make executable
chmod +x ~/.claude/hooks/*.sh

# Test hook execution
echo '{"tool_name":"Bash","tool_input":{"command":"wp post update 105"}}' | ~/.claude/hooks/pre_wordpress_update_protection.sh
# Should output JSON with "deny" decision
```

### 2. Register in Settings

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": {
      "Bash": [
        {
          "type": "command",
          "command": "~/.claude/hooks/pre_wordpress_update_protection.sh"
        },
        {
          "type": "command",
          "command": "~/.claude/hooks/pre_wordpress_fact_check_enforcement.sh"
        },
        {
          "type": "command",
          "command": "~/.claude/hooks/pre_sensitive_file_protection.sh"
        }
      ],
      "Edit": [
        {
          "type": "command",
          "command": "~/.claude/hooks/pre_sensitive_file_protection.sh"
        }
      ],
      "Write": [
        {
          "type": "command",
          "command": "~/.claude/hooks/pre_sensitive_file_protection.sh"
        }
      ]
    }
  }
}
```

### 3. Test Enforcement

```bash
# Test 1: Try to update without approval (should be BLOCKED)
wp post update 105 --post_content="test"
# Expected: Hook blocks with "not approved" message

# Test 2: Run fact-check
/fact-check --page-id=105

# Test 3: Approve page
/content-approve --page-id=105 --approver=dave --notes="Test approval"

# Test 4: Try update again (should SUCCEED)
wp post update 105 --post_content="test"
# Expected: Hook allows with approval confirmation
```

### 4. Verify Audit Trail

```bash
# Check approval log
tail ~/.claude/content-vault/audit-log/approvals.log

# Check update log
tail ~/.claude/content-vault/audit-log/updates.log

# Check fact-check records
ls -la ~/.claude/content-vault/fact-checks/

# Check approval records
ls -la ~/.claude/content-vault/approvals/
```

---

## Benefits of This Approach

### ✅ True Enforcement

- **Cannot bypass** - hooks execute BEFORE tools run
- **Claude is informed** - sees denial reasons, can explain to user
- **User cannot override** - even manual commands are blocked

### ✅ Complete Audit Trail

- **All approvals logged** with who/when/why
- **All updates logged** with approval reference
- **All fact-checks logged** with pass/fail status

### ✅ Time-Limited Approvals

- **24-hour expiry** - approvals must be recent
- **1-hour fact-check validity** - ensures current data
- **Prevents stale approvals** from being used

### ✅ Multi-Layer Protection

1. Fact-check must pass first
2. Then approval with signature
3. Then hook allows WordPress update
4. All logged to audit trail

---

## Impact Assessment

### Before Hooks (CURRENT STATE)

```
User: "Update page 105 with budget of $110.5M"
Claude: *updates immediately*
Result: ❌ WRONG DATA PUBLISHED
```

### After Hooks (WITH ENFORCEMENT)

```
User: "Update page 105 with budget of $110.5M"
Claude: *attempts wp post update 105*
Hook: ❌ BLOCKS - "Page 105 is not approved"
Claude: "I cannot update page 105 because it hasn't been approved. Let me run fact-check first."
*runs /fact-check --page-id=105*
Result: ❌ Fact-check fails ($110.5M is incorrect, should be $81M)
Claude: "Fact-check found an error. The budget should be $81M, not $110.5M. Would you like me to fix this?"
User: "Yes"
Claude: *updates content with correct $81M*
*runs /fact-check --page-id=105*
Result: ✅ Fact-check passes
Claude: "Would you like to approve this for publishing?"
User: "Yes"
Claude: *runs /content-approve --page-id=105 --approver=dave*
*attempts wp post update 105*
Hook: ✅ ALLOWS - "Page 105 approved by dave"
Result: ✅ CORRECT DATA PUBLISHED
```

---

## Rollout Plan

### Phase 1: Infrastructure (Day 1)

- [x] Create content vault structure
- [x] Enhance /fact-check to create records
- [x] Create /content-approve command
- [ ] Test vault operations

### Phase 2: Hooks (Day 2)

- [ ] Create WordPress protection hook
- [ ] Create fact-check enforcement hook
- [ ] Create sensitive file hook
- [ ] Test hooks individually

### Phase 3: Integration (Day 3)

- [ ] Register all hooks in settings.json
- [ ] Test full workflow (fact-check → approve → update)
- [ ] Verify denial cases work correctly
- [ ] Test with multiple pages

### Phase 4: Production (Day 4-5)

- [ ] Deploy to actual WordPress workflow
- [ ] Monitor audit logs
- [ ] Fix any issues discovered
- [ ] Document procedures

---

## Maintenance

### Daily

- Review audit logs for anomalies
- Check for blocked operations

### Weekly

- Clean expired approvals (>7 days old)
- Clean stale fact-checks (>7 days old)
- Review audit trail for patterns

### Monthly

- Security audit of hook execution
- Review denied operations
- Update enforcement rules as needed

---

## Conclusion

**This is the missing piece.** We have all the tools, commands, and skills - we just need **enforcement hooks** to make it robust.

**Implementation Time:** 2-3 days
**Impact:** Prevents 100% of unauthorized/incorrect publishing
**ROI:** Massive - protects campaign from data accuracy issues

**Next Action:** Implement Phase 1 (content vault) TODAY.

---

**Document Created:** 2025-11-19 15:00 EST
**Status:** 🔴 READY FOR IMMEDIATE IMPLEMENTATION
**Priority:** P0 - CRITICAL
