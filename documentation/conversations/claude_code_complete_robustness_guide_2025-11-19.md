# Claude Code Complete Robustness Guide

**Date:** 2025-11-19
**Session:** Comprehensive Claude Code Best Practices Analysis
**Sources:** Official Claude Code Documentation + Best Practices + Community Resources
**Status:** 🎯 **COMPLETE IMPLEMENTATION ROADMAP**

---

## Executive Summary

After analyzing the official Claude Code documentation, Anthropic's best practices, and comparing against our current implementation, I've identified **comprehensive improvements** across ALL Claude Code extension points:

1. **Hooks** (enforcement mechanisms)
2. **Skills** (model-invoked capabilities)
3. **Slash Commands** (user-invoked workflows)
4. **MCP Servers** (external integrations)
5. **CLAUDE.md** (project context)
6. **Permissions** (security configuration)
7. **Workflows** (development patterns)

**Current Status:** We have 60% of the infrastructure but are missing critical enforcement and optimization.

---

## Part 1: CLAUDE.md Optimization

### What We Have

`.claude/CLAUDE.md` (3000+ lines) with:
- Work files preservation protocol
- Fact-checking requirements
- WordPress workflows
- File naming standards
- Script creation rules

### What We're Missing

**Best Practice:** Progressive disclosure, concise human-readable format, focus on frequently-used patterns.

**Problem:** Our CLAUDE.md is MASSIVE - Claude has to load 3000+ lines every session.

**Solution:** Split into multiple files with on-demand loading.

---

### Optimized Structure

**Root:** `.claude/CLAUDE.md` (keep <500 lines, essentials only)

```markdown
# Essential Instructions

## File & Script Naming
- Lowercase with underscores: `file_name_v1.0.0.ext`
- Semantic versioning required
- Format: `{purpose}_{task}_v{version}.{ext}`

## Before Creating Scripts
**CRITICAL:** Check existing 179 scripts first:
```bash
find /home/dave/skippy/development/scripts -name "*.sh" -exec grep -l "keyword" {} \;
```

## Fact-Checking Rule
**Master Source:** `/home/dave/rundaverun/campaign/.../QUICK_FACTS_SHEET.md`

**ALWAYS VERIFY BEFORE USING:**
- Total Budget: $81M (NOT $110.5M)
- Wellness ROI: $2-3 per $1 (NOT $1.80)
- JCPS Reading: 34-35% (NOT 44%)

## WordPress Work Sessions
**MANDATORY:** Create session directory FIRST, save before/after states.

See: `.claude/workflows/wordpress.md` for complete process.

## MCP Tools Available
52 tools across 6 categories - use /mcp-status to check.

## Quick Commands
- `/fact-check` - Verify campaign numbers
- `/content-approve` - Approve for publishing
- `/session-summary` - Document session
- `/screenshot` - Recent screenshots
```

**Supporting Files:**

`.claude/workflows/wordpress.md` - Complete WordPress workflow (Step 0-7)
`.claude/workflows/script-development.md` - Script creation workflow
`.claude/protocols/fact-checking.md` - Detailed fact-check process
`.claude/protocols/work-files-preservation.md` - Full preservation protocol
`.claude/reference/quick-facts.md` - Key campaign facts
`.claude/reference/directory-structure.md` - Project organization

**Benefits:**
- ✅ 80% less context usage
- ✅ Faster Claude startup
- ✅ On-demand detail loading
- ✅ Easier to maintain

---

## Part 2: Enforcement Hooks (CRITICAL)

### Hook #1: WordPress Update Protection

**File:** `~/.claude/hooks/pre_wordpress_update_protection.sh`

```bash
#!/bin/bash
# WordPress Update Protection Hook
# BLOCKS wp post update without approval

HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name')
TOOL_INPUT_JSON=$(echo "$HOOK_INPUT" | jq -r '.tool_input')

if [[ "$TOOL_NAME" != "Bash" ]]; then
    exit 0
fi

COMMAND=$(echo "$TOOL_INPUT_JSON" | jq -r '.command')

if [[ "$COMMAND" =~ wp.*post.*update ]]; then
    PAGE_ID=$(echo "$COMMAND" | grep -oP 'update\s+\K[0-9]+')

    if [[ -z "$PAGE_ID" ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Cannot determine page ID. Specify explicitly."
  }
}
EOF
        exit 0
    fi

    APPROVAL_FILE="$HOME/.claude/content-vault/approvals/page_${PAGE_ID}_approval.json"

    if [[ ! -f "$APPROVAL_FILE" ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Page $PAGE_ID not approved. Run: /content-approve --page-id=$PAGE_ID"
  }
}
EOF
        exit 0
    fi

    # Check expiry (24 hours)
    APPROVAL_TS=$(jq -r '.timestamp' "$APPROVAL_FILE")
    AGE=$(($(date +%s) - APPROVAL_TS))

    if [[ $AGE -gt 86400 ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Approval expired (>24h). Re-approve first."
  }
}
EOF
        exit 0
    fi

    # Log and allow
    echo "[$(date)] ALLOWED: Page $PAGE_ID by $(jq -r '.approver' "$APPROVAL_FILE")" >> "$HOME/.claude/content-vault/audit-log/updates.log"

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Approved by $(jq -r '.approver' "$APPROVAL_FILE")"
  }
}
EOF
fi

exit 0
```

---

### Hook #2: Fact-Check Enforcement

**File:** `~/.claude/hooks/pre_fact_check_enforcement.sh`

```bash
#!/bin/bash
# Blocks WordPress updates without recent fact-check

HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name')
TOOL_INPUT_JSON=$(echo "$HOOK_INPUT" | jq -r '.tool_input')

if [[ "$TOOL_NAME" != "Bash" ]]; then
    exit 0
fi

COMMAND=$(echo "$TOOL_INPUT_JSON" | jq -r '.command')

if [[ "$COMMAND" =~ wp.*post.*update ]]; then
    PAGE_ID=$(echo "$COMMAND" | grep -oP 'update\s+\K[0-9]+')
    FACT_CHECK_FILE="$HOME/.claude/content-vault/fact-checks/page_${PAGE_ID}_facts.json"

    if [[ ! -f "$FACT_CHECK_FILE" ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "No fact-check found. Run: /fact-check --page-id=$PAGE_ID"
  }
}
EOF
        exit 0
    fi

    # Check freshness (1 hour)
    FACT_CHECK_TS=$(jq -r '.checked_at' "$FACT_CHECK_FILE")
    AGE=$(($(date +%s) - FACT_CHECK_TS))

    if [[ $AGE -gt 3600 ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Fact-check stale ($(($AGE/60))min). Re-run /fact-check"
  }
}
EOF
        exit 0
    fi

    # Check passed
    PASSED=$(jq -r '.passed' "$FACT_CHECK_FILE")
    if [[ "$PASSED" != "true" ]]; then
        ERRORS=$(jq -r '.errors | join(", ")' "$FACT_CHECK_FILE")
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Fact-check failed: $ERRORS"
  }
}
EOF
        exit 0
    fi

    # Allow - fact-check passed
    exit 0
fi

exit 0
```

---

### Hook #3: Sensitive File Protection

**File:** `~/.claude/hooks/pre_sensitive_file_protection.sh`

```bash
#!/bin/bash
# Blocks modifications to .env, credentials, business/personal

HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name')
TOOL_INPUT_JSON=$(echo "$HOOK_INPUT" | jq -r '.tool_input')

# Check Edit/Write tools
if [[ "$TOOL_NAME" == "Edit" ]] || [[ "$TOOL_NAME" == "Write" ]]; then
    FILE_PATH=$(echo "$TOOL_INPUT_JSON" | jq -r '.file_path')

    if [[ "$FILE_PATH" =~ \.env|credentials|\.key|\.pem|\.ssh|business/|personal/ ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Cannot modify sensitive file: $FILE_PATH"
  }
}
EOF
        exit 0
    fi
fi

# Check Bash for dangerous commands
if [[ "$TOOL_NAME" == "Bash" ]]; then
    COMMAND=$(echo "$TOOL_INPUT_JSON" | jq -r '.command')

    if [[ "$COMMAND" =~ rm\s+-rf\s+/|git\s+push\s+--force\s+origin\s+master|DROP\s+DATABASE ]]; then
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "Destructive operation - confirm before proceeding"
  }
}
EOF
        exit 0
    fi
fi

exit 0
```

---

### Hook #4: Session Start Context Loader

**File:** `~/.claude/hooks/session_start_context.sh`

```bash
#!/bin/bash
# Loads environment-specific context at session start

HOOK_INPUT=$(cat)
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd')

# Detect project type
if [[ "$CWD" =~ wordpress ]]; then
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "WordPress development session detected. Remember:\n- Use work file preservation protocol\n- Fact-check all numbers against QUICK_FACTS_SHEET.md\n- Approve content before publishing\nActive tools: /fact-check, /content-approve, /wp-deploy"
  }
}
EOF
elif [[ "$CWD" =~ scripts ]]; then
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Script development session. Remember:\n- Check for existing scripts before creating new ones (179 available)\n- Use naming convention: purpose_task_v1.0.0.ext\n- Test with profile-script before deploying"
  }
}
EOF
fi

exit 0
```

---

## Part 3: Skills Optimization

### Current Skills: 50+

All have proper YAML frontmatter ✅

### Missing: Security-Constrained Skills

**Problem:** Skills have full tool access by default.

**Solution:** Use `allowed-tools` for read-only/restricted skills.

---

### Security-Constrained Skill Example

**Create:** `~/.claude/skills/code-reviewer-readonly/SKILL.md`

```yaml
---
name: code-reviewer-readonly
description: Perform code review with read-only access. Reviews code quality, security, best practices. Auto-invoke when user asks to review code. Cannot modify files.
allowed-tools: Read, Grep, Glob
---

# Code Reviewer (Read-Only)

This skill performs comprehensive code review WITHOUT modifying files.

## What I Check

1. **Security Issues**
   - SQL injection vulnerabilities
   - XSS risks
   - Hardcoded credentials
   - Unsafe file operations

2. **Code Quality**
   - Naming conventions
   - Code duplication
   - Error handling
   - Documentation

3. **Best Practices**
   - PHP/JavaScript standards
   - WordPress coding standards
   - Security best practices

## Process

1. Read requested files
2. Analyze for issues
3. Provide detailed report with:
   - Issue location (file:line)
   - Severity (critical/high/medium/low)
   - Recommendation
   - Example fix (without modifying)

## Restrictions

This skill CANNOT:
- Modify any files
- Execute bash commands
- Write new files

For automated fixes, ask user to approve first, then create separate skill invocation.
```

**Benefits:**
- ✅ Can review without risk of modification
- ✅ Perfect for pre-commit reviews
- ✅ Security-focused

---

### Fact-Check Skill Enhancement

**Enhance:** `~/.claude/skills/campaign-facts/SKILL.md`

**Add section:**

```markdown
## Enforcement Integration

When fact-checking WordPress content, this skill:

1. Validates content against QUICK_FACTS_SHEET.md
2. Creates fact-check record in `~/.claude/content-vault/fact-checks/`
3. Enables approval workflow via /content-approve

**Fact-Check Record Schema:**
```json
{
  "page_id": 105,
  "checked_at": 1700443200,
  "passed": true,
  "errors": [],
  "verified_facts": {
    "budget": "$81M",
    "roi": "$2-3 per $1"
  }
}
```

This record is REQUIRED before approval and publishing.
```

---

## Part 4: Slash Commands Enhancement

### Current Commands: 25

All with proper YAML frontmatter ✅

### Missing: Approval Workflow Command

**Create:** `.claude/commands/content-approve.md`

```yaml
---
description: Approve WordPress content for publishing with signature tracking
argument-hint: "--page-id=<id> --approver=<name> [--notes='...']"
allowed-tools: Bash, Read, Write
---

# Content Approval System

Approve WordPress pages for publishing with:
- Fact-check validation
- Signature tracking
- 24-hour validity
- Audit trail logging

## Usage

```bash
/content-approve --page-id=105 --approver=dave --notes="Homepage verified"
```

## Process

1. Checks fact-check record exists (<1 hour old)
2. Verifies fact-check passed
3. Creates approval record
4. Logs to audit trail
5. Enables WordPress update (hook allows it)

## Implementation

```bash
#!/bin/bash

# Parse args
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

# Validate
if [[ -z "$PAGE_ID" ]] || [[ -z "$APPROVER" ]]; then
    echo "❌ Error: --page-id and --approver required"
    exit 1
fi

# Check fact-check
FACT_CHECK_FILE="$HOME/.claude/content-vault/fact-checks/page_${PAGE_ID}_facts.json"

if [[ ! -f "$FACT_CHECK_FILE" ]]; then
    echo "❌ No fact-check found. Run: /fact-check --page-id=$PAGE_ID"
    exit 1
fi

# Check freshness
FACT_CHECK_TS=$(jq -r '.checked_at' "$FACT_CHECK_FILE")
AGE=$(($(date +%s) - FACT_CHECK_TS))

if [[ $AGE -gt 3600 ]]; then
    echo "❌ Fact-check stale. Re-run /fact-check"
    exit 1
fi

# Check passed
PASSED=$(jq -r '.passed' "$FACT_CHECK_FILE")
if [[ "$PASSED" != "true" ]]; then
    ERRORS=$(jq -r '.errors | join(", ")' "$FACT_CHECK_FILE")
    echo "❌ Cannot approve - fact-check failed: $ERRORS"
    exit 1
fi

# Create approval
APPROVAL_FILE="$HOME/.claude/content-vault/approvals/page_${PAGE_ID}_approval.json"

cat > "$APPROVAL_FILE" <<EOF
{
  "page_id": $PAGE_ID,
  "approver": "$APPROVER",
  "timestamp": $(date +%s),
  "timestamp_human": "$(date +"%Y-%m-%d %H:%M:%S")",
  "notes": "$NOTES",
  "fact_check_passed": true,
  "expires": $(($(date +%s) + 86400))
}
EOF

# Log
echo "[$(date)] APPROVED: Page $PAGE_ID by $APPROVER - $NOTES" >> "$HOME/.claude/content-vault/audit-log/approvals.log"

echo "✅ Page $PAGE_ID approved (valid 24h)"
echo "Approver: $APPROVER"
echo ""
echo "You can now update with: wp post update $PAGE_ID"
```
```

---

### Enhanced Fact-Check Command

**Modify:** `.claude/commands/fact-check.md`

**Add at end:**

```markdown
## Create Fact-Check Record

After validation, save record for approval workflow:

```bash
if [[ -n "$PAGE_ID" ]]; then
    mkdir -p "$HOME/.claude/content-vault/fact-checks"
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
    "budget": "$BUDGET_CHECK",
    "roi": "$ROI_CHECK",
    "jcps_reading": "$READING_CHECK",
    "jcps_math": "$MATH_CHECK"
  }
}
EOF

    echo "✅ Fact-check record created (valid 1 hour)"
    echo "Next: /content-approve --page-id=$PAGE_ID --approver=<name>"
fi
```
```

---

## Part 5: MCP Server Enhancements

### Current: 52 MCP Tools

From `general-server` including Google Drive, Pexels, file ops, monitoring, remote commands, WordPress

### Missing: WordPress Content Validator

**Create:** `development/mcp_servers/mcp-servers/general-server/tools/wordpress_content_validator.py`

```python
#!/usr/bin/env python3
"""
WordPress Content Validator MCP Tool
Comprehensive multi-level validation
"""

import json
import re
import subprocess
from typing import Dict, List, Optional

def wordpress_content_validator(
    post_id: Optional[int] = None,
    content: Optional[str] = None,
    validation_level: str = "standard"  # standard|strict|publish-ready
) -> Dict:
    """
    Validates WordPress content against multiple criteria.

    Args:
        post_id: WordPress post ID to validate
        content: Raw HTML content to validate
        validation_level: Depth of validation

    Returns:
        {
            "passed": bool,
            "validation_results": {
                "facts": {"passed": bool, "errors": [...]},
                "links": {"passed": bool, "broken_links": [...]},
                "seo": {"passed": bool, "warnings": [...]},
                "accessibility": {"passed": bool, "violations": [...]},
                "html": {"passed": bool, "errors": [...]}
            },
            "recommendations": ["Fix...", "Update..."],
            "severity": "critical|high|medium|low"
        }
    """

    results = {
        "passed": True,
        "validation_results": {},
        "recommendations": [],
        "severity": "low"
    }

    # Get content if post_id provided
    if post_id and not content:
        wp_path = "/home/dave/skippy/websites/rundaverun/local_site/app/public"
        cmd = f"wp --path={wp_path} post get {post_id} --field=post_content"
        content = subprocess.check_output(cmd, shell=True, text=True)

    # 1. Fact validation
    fact_results = validate_facts(content)
    results["validation_results"]["facts"] = fact_results

    if not fact_results["passed"]:
        results["passed"] = False
        results["severity"] = "critical"

    # 2. Link validation (if strict or publish-ready)
    if validation_level in ["strict", "publish-ready"]:
        link_results = validate_links(content)
        results["validation_results"]["links"] = link_results

        if not link_results["passed"]:
            results["passed"] = False
            if results["severity"] == "low":
                results["severity"] = "high"

    # 3. SEO validation (publish-ready only)
    if validation_level == "publish-ready":
        seo_results = validate_seo(content, post_id)
        results["validation_results"]["seo"] = seo_results

        # SEO warnings don't fail validation, but add recommendations
        if seo_results.get("warnings"):
            results["recommendations"].extend(seo_results["warnings"])

    # 4. Accessibility validation (publish-ready only)
    if validation_level == "publish-ready":
        a11y_results = validate_accessibility(content)
        results["validation_results"]["accessibility"] = a11y_results

        if not a11y_results["passed"]:
            results["passed"] = False
            if results["severity"] not in ["critical", "high"]:
                results["severity"] = "medium"

    # 5. HTML validation
    html_results = validate_html(content)
    results["validation_results"]["html"] = html_results

    if not html_results["passed"]:
        results["passed"] = False

    return results


def validate_facts(content: str) -> Dict:
    """Validate facts against QUICK_FACTS_SHEET.md"""
    errors = []

    # Check for common incorrect values
    if "$110" in content or "$110.5M" in content:
        errors.append("Budget error: Should be $81M, not $110.5M")

    if "$1.80" in content or "$1.8" in content:
        errors.append("ROI error: Should be $2-3 per $1, not $1.80")

    if re.search(r"44%.*reading|reading.*44%", content, re.IGNORECASE):
        errors.append("JCPS Reading error: Should be 34-35%, not 44%")

    if re.search(r"41%.*math|math.*41%", content, re.IGNORECASE):
        errors.append("JCPS Math error: Should be 27-28%, not 41%")

    return {
        "passed": len(errors) == 0,
        "errors": errors
    }


def validate_links(content: str) -> Dict:
    """Check for broken links"""
    import requests

    broken_links = []
    links = re.findall(r'href=["\'](https?://[^"\']+)["\']', content)

    for link in links:
        try:
            response = requests.head(link, timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                broken_links.append(f"{link} (HTTP {response.status_code})")
        except requests.RequestException as e:
            broken_links.append(f"{link} (Error: {str(e)})")

    return {
        "passed": len(broken_links) == 0,
        "broken_links": broken_links
    }


def validate_seo(content: str, post_id: Optional[int]) -> Dict:
    """Check SEO requirements"""
    warnings = []

    # Check for meta description (would need to query WordPress)
    # Check for alt tags on images
    images_without_alt = re.findall(r'<img(?![^>]*alt=)[^>]*>', content)
    if images_without_alt:
        warnings.append(f"{len(images_without_alt)} images missing alt tags")

    # Check for heading structure
    if not re.search(r'<h1[^>]*>', content):
        warnings.append("No H1 heading found")

    return {
        "passed": True,  # SEO warnings don't fail validation
        "warnings": warnings
    }


def validate_accessibility(content: str) -> Dict:
    """Check WCAG 2.1 compliance"""
    violations = []

    # Check for proper heading hierarchy
    headings = re.findall(r'<h([1-6])', content)
    if headings:
        prev = 0
        for level in [int(h) for h in headings]:
            if level > prev + 1:
                violations.append(f"Heading hierarchy skip: H{prev} to H{level}")
            prev = level

    # Check for tables without headers
    tables = re.findall(r'<table[^>]*>(.*?)</table>', content, re.DOTALL)
    for table in tables:
        if not re.search(r'<th[^>]*>', table):
            violations.append("Table missing header row (<th>)")

    return {
        "passed": len(violations) == 0,
        "violations": violations
    }


def validate_html(content: str) -> Dict:
    """Validate HTML structure"""
    errors = []

    # Check for unclosed tags
    open_tags = re.findall(r'<([a-z]+)(?:\s[^>]*)?>(?!.*</\1>)', content)
    if open_tags:
        errors.append(f"Unclosed tags: {', '.join(set(open_tags))}")

    # Check for duplicate IDs
    ids = re.findall(r'id=["\'"]([^"\']+)["\']', content)
    duplicates = [id for id in ids if ids.count(id) > 1]
    if duplicates:
        errors.append(f"Duplicate IDs: {', '.join(set(duplicates))}")

    return {
        "passed": len(errors) == 0,
        "errors": errors
    }


if __name__ == "__main__":
    # CLI interface
    import sys
    post_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    level = sys.argv[2] if len(sys.argv) > 2 else "standard"

    result = wordpress_content_validator(post_id=post_id, validation_level=level)
    print(json.dumps(result, indent=2))
```

**Register in MCP server** (add to tool registry)

---

## Part 6: Permission Optimization

### Current Permissions: 28 auto-approve patterns

Good coverage ✅

### Optimization: Context-Aware Permissions

**Best Practice:** Different permission sets for different project types.

**Create:** `.claude/profiles/wordpress-permissive.json`

```json
{
  "permissionsFilters": {
    "Bash": [
      "wp --path=* post get *",
      "wp --path=* post update *",
      "wp --path=* db check",
      "wp --path=* option get *",
      "git status*",
      "git diff*",
      "git log*",
      "curl -I http://*"
    ],
    "Read": [
      "/home/dave/skippy/**",
      "/home/dave/.claude/**"
    ],
    "Write": [
      "/home/dave/skippy/work/**",
      "/home/dave/.claude/content-vault/**"
    ]
  }
}
```

**Create:** `.claude/profiles/script-dev-restrictive.json`

```json
{
  "permissionsFilters": {
    "Bash": [
      "shellcheck *",
      "chmod +x *",
      "find *",
      "grep -l *"
    ],
    "Read": [
      "/home/dave/skippy/development/scripts/**"
    ],
    "Write": [
      "/home/dave/skippy/development/scripts/**"
    ]
  }
}
```

**Usage:**

```bash
# WordPress session
claude --permissions-profile wordpress-permissive

# Script development
claude --permissions-profile script-dev-restrictive
```

---

## Part 7: Workflow Patterns

### Pattern #1: Explore-Plan-Code-Commit (WordPress)

```bash
# 1. EXPLORE
User: "I need to update the homepage wellness ROI"
Claude: *reads page 105, QUICK_FACTS_SHEET.md, previous sessions*

# 2. PLAN
Claude: "Here's my plan:
1. Create session directory
2. Save original page content
3. Run fact-check to verify current ROI value
4. Update $1.80 → $2-3 per $1
5. Verify with diff
6. Get approval
7. Publish"
User: "Approved"

# 3. CODE
Claude: *executes plan step by step*
Hook: ❌ BLOCKS wp post update - "Not approved"
Claude: "Cannot publish without approval. Running fact-check..."
*runs /fact-check --page-id=105*
Result: ✅ Passed
Claude: "Fact-check passed. Request approval?"
User: "Yes"
*runs /content-approve --page-id=105 --approver=dave*
*retries wp post update 105*
Hook: ✅ ALLOWS - "Approved by dave"

# 4. COMMIT
*git add, git commit with detailed message, git push*
*pre-commit hooks validate*
*GitHub Actions run tests*
```

---

### Pattern #2: TDD with Claude

```bash
# 1. REQUEST TESTS
User: "Create tests for the approval workflow"
Claude: *creates test_approval_workflow.sh*

# 2. CONFIRM FAIL
bash development/tests/run_tests.sh
Result: ❌ All tests fail (expected - no implementation)

# 3. IMPLEMENT
Claude: *creates /content-approve command*

# 4. ITERATIVE FIX
bash development/tests/run_tests.sh
Result: ✅ 3/5 passed
Claude: "Tests 4 and 5 failing due to expiry logic. Fixing..."
*fixes expiry check*
bash development/tests/run_tests.sh
Result: ✅ 5/5 passed

# 5. COMMIT
git commit -m "feat: Add content approval workflow with tests"
```

---

### Pattern #3: Multi-Claude Verification

```bash
# Terminal 1: Implementation Claude
claude1> "Implement WordPress content validator"
*writes validator code*

# Terminal 2: Review Claude (separate context)
claude2> "Review the WordPress content validator for security issues"
*reads code with fresh perspective*
"Found 3 potential issues:
1. SQL injection risk in post_id parameter
2. Missing timeout on HTTP requests
3. No input sanitization on content parameter"

# Terminal 1: Fix issues
claude1> "Address the security issues from review"
*fixes all 3 issues*

# Terminal 2: Re-review
claude2> "Review again"
"✅ All security issues resolved. Code ready for production."
```

---

## Part 8: Complete Implementation Checklist

### Phase 1: Infrastructure (Week 1)

**Day 1-2: CLAUDE.md Optimization**
- [ ] Split into multiple files
- [ ] Create workflows/ directory
- [ ] Create protocols/ directory
- [ ] Create reference/ directory
- [ ] Update root CLAUDE.md to <500 lines
- [ ] Test context loading

**Day 3-4: Content Vault**
- [ ] Create vault structure (~/.claude/content-vault/)
- [ ] Create approval directory
- [ ] Create fact-checks directory
- [ ] Create audit-log directory
- [ ] Initialize log files
- [ ] Test vault operations

**Day 5: Enhanced Commands**
- [ ] Enhance /fact-check to create records
- [ ] Create /content-approve command
- [ ] Test workflow: fact-check → approve
- [ ] Verify record creation

---

### Phase 2: Enforcement (Week 2)

**Day 6-7: WordPress Protection Hooks**
- [ ] Create pre_wordpress_update_protection.sh
- [ ] Create pre_fact_check_enforcement.sh
- [ ] Test hooks individually
- [ ] Register in settings.json

**Day 8-9: Security Hooks**
- [ ] Create pre_sensitive_file_protection.sh
- [ ] Create session_start_context.sh
- [ ] Test all hooks together
- [ ] Verify blocking works

**Day 10: Integration Testing**
- [ ] Test full workflow with hooks active
- [ ] Test approval expiry
- [ ] Test fact-check expiry
- [ ] Test denied operations
- [ ] Test allowed operations with approval

---

### Phase 3: Skills & MCP (Week 3)

**Day 11-12: Security-Constrained Skills**
- [ ] Create code-reviewer-readonly skill
- [ ] Test with allowed-tools restriction
- [ ] Enhance campaign-facts skill
- [ ] Add enforcement integration

**Day 13-14: MCP Content Validator**
- [ ] Implement wordpress_content_validator.py
- [ ] Add to MCP server registry
- [ ] Test validation levels
- [ ] Test all validation types

**Day 15: Permission Optimization**
- [ ] Create wordpress-permissive profile
- [ ] Create script-dev-restrictive profile
- [ ] Test profile switching
- [ ] Document usage

---

### Phase 4: Production Deployment (Week 4)

**Day 16-17: Testing**
- [ ] Create comprehensive test suite
- [ ] Test all hooks in production scenarios
- [ ] Test approval workflow end-to-end
- [ ] Test fact-check enforcement
- [ ] Verify audit trail completeness

**Day 18-19: Documentation**
- [ ] Document all new workflows
- [ ] Create runbooks with generate-runbook
- [ ] Update CONTRIBUTING.md
- [ ] Create training materials

**Day 20: Rollout**
- [ ] Deploy to production
- [ ] Monitor first 24 hours
- [ ] Collect feedback
- [ ] Fix any issues discovered

---

## Success Metrics

### Immediate (Week 1-2)
- [ ] Zero WordPress updates without approval
- [ ] 100% fact-check enforcement
- [ ] Complete audit trail
- [ ] Context usage reduced 80%

### Short-term (Month 1)
- [ ] 50% reduction in deployment errors
- [ ] 100% content validation coverage
- [ ] Multi-level validation operational
- [ ] Team fully onboarded

### Long-term (Quarter 1)
- [ ] Zero unauthorized publishing
- [ ] Zero factually incorrect content published
- [ ] 70% reduction in manual compliance work
- [ ] Complete approval audit capability

---

## Conclusion

**Current State:** Strong foundation (15 tools, 50 skills, 25 commands, 52 MCP tools)

**Missing:** Enforcement mechanisms, optimization, security constraints

**Solution:** 4-week implementation across ALL Claude Code extension points:
1. Hooks for enforcement
2. Optimized CLAUDE.md for efficiency
3. Security-constrained skills
4. Enhanced MCP validators
5. Permission profiles
6. Workflow patterns

**Impact:** Transform from "can be bypassed" to "robust, enforced, production-ready"

**ROI:** Massive - prevents all unauthorized/incorrect publishing while improving efficiency

---

**Guide Completed:** 2025-11-19 16:00 EST
**Total Recommendations:** 30+ across 7 extension points
**Implementation Time:** 4 weeks
**Status:** 🎯 READY FOR IMMEDIATE IMPLEMENTATION
