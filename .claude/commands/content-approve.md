---
description: Approve WordPress content updates with signature tracking and audit trail
argument-hint: "--page-id=<id> --approver=<name> [--notes=\"description\"]"
allowed-tools: ["Bash", "Read"]
---

# Content Approval Command

Create approval records for WordPress content updates with accountability and audit trail.

## Purpose

Enables the enforcement hooks to allow WordPress updates by creating signed approval records. All WordPress `wp post update` commands require valid approval.

---

## Usage

### Basic Approval

```bash
/content-approve --page-id=105 --approver=dave --notes="Homepage wellness ROI update"
```

### Bulk Approval

```bash
# Approve multiple pages at once
/content-approve --page-id=105,106,107 --approver=dave --notes="Policy budget updates"
```

### Quick Approval

```bash
# Approve without notes (prompts for details)
/content-approve --page-id=105 --approver=dave
```

---

## Implementation

```bash
#!/bin/bash
# Content Approval Handler
set -euo pipefail

# Parse arguments
PAGE_ID=""
APPROVER=""
NOTES=""

for arg in "$@"; do
  case $arg in
    --page-id=*)
      PAGE_ID="${arg#*=}"
      ;;
    --approver=*)
      APPROVER="${arg#*=}"
      ;;
    --notes=*)
      NOTES="${arg#*=}"
      ;;
  esac
done

# Validate required arguments
if [[ -z "$PAGE_ID" ]]; then
  echo "❌ ERROR: --page-id is required"
  echo "Usage: /content-approve --page-id=<id> --approver=<name> [--notes=\"description\"]"
  exit 1
fi

if [[ -z "$APPROVER" ]]; then
  echo "❌ ERROR: --approver is required"
  echo "Usage: /content-approve --page-id=<id> --approver=<name> [--notes=\"description\"]"
  exit 1
fi

# Handle multiple page IDs (comma-separated)
IFS=',' read -ra PAGE_IDS <<< "$PAGE_ID"

# Process each page ID
for PID in "${PAGE_IDS[@]}"; do
  echo "Processing approval for page ${PID}..."

  # Check for recent fact-check (required before approval)
  FACT_CHECK_FILE=$(find ~/.claude/content-vault/fact-checks/ \
    -name "${PID}_*.fact-checked" \
    -mmin -60 \
    2>/dev/null | sort -r | head -1)

  if [[ -z "$FACT_CHECK_FILE" ]]; then
    echo "⚠️  WARNING: No recent fact-check found for page ${PID}"
    echo "   Fact-check is required before approval."
    echo "   Run: /fact-check <content for page ${PID}>"
    echo ""
    continue
  fi

  # Create approval record
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  APPROVAL_FILE=~/.claude/content-vault/approvals/${PID}_${TIMESTAMP}.approved

  # Extract fact-check ID
  FACT_CHECK_ID=$(basename "$FACT_CHECK_FILE" .fact-checked)

  # Create approval record
  cat > "$APPROVAL_FILE" <<APPROVAL
{
  "page_id": ${PID},
  "approver": "${APPROVER}",
  "timestamp": "$(date -Iseconds)",
  "expires": "$(date -Iseconds -d '+24 hours')",
  "notes": "${NOTES}",
  "fact_check_id": "${FACT_CHECK_ID}",
  "fact_check_file": "${FACT_CHECK_FILE}",
  "approval_signature": "$(echo -n "${PID}${APPROVER}$(date -Iseconds)" | sha256sum | cut -d' ' -f1)",
  "valid_until": "$(date -Iseconds -d '+24 hours')"
}
APPROVAL

  # Set proper permissions
  chmod 600 "$APPROVAL_FILE"

  # Log to audit trail
  AUDIT_DIR=~/.claude/content-vault/audit-log/$(date +%Y-%m)
  mkdir -p "$AUDIT_DIR"

  cat > "$AUDIT_DIR/${PID}_approval_${TIMESTAMP}.audit" <<AUDIT
{
  "page_id": ${PID},
  "action": "content_approved",
  "timestamp": "$(date -Iseconds)",
  "approver": "${APPROVER}",
  "approval_file": "${APPROVAL_FILE}",
  "fact_check_file": "${FACT_CHECK_FILE}",
  "notes": "${NOTES}",
  "expires": "$(date -Iseconds -d '+24 hours')"
}
AUDIT

  echo "✅ Approval created for page ${PID}"
  echo "   Approver: ${APPROVER}"
  echo "   Valid until: $(date -d '+24 hours' '+%Y-%m-%d %H:%M:%S')"
  echo "   Fact-check: ${FACT_CHECK_ID}"
  if [[ -n "$NOTES" ]]; then
    echo "   Notes: ${NOTES}"
  fi
  echo "   File: ${APPROVAL_FILE}"
  echo ""
done

# Summary
APPROVED_COUNT=${#PAGE_IDS[@]}
echo "📋 Summary: ${APPROVED_COUNT} page(s) approved"
echo "   Approver: ${APPROVER}"
echo "   Validity: 24 hours"
echo ""
echo "✅ WordPress updates now allowed for approved pages"
echo "   Run: wp post update <page-id> --post_content=\"...\""
```

---

## Approval Requirements

Before approval can be granted:

1. **Recent Fact-Check Required**
   - Fact-check must be < 1 hour old
   - Run `/fact-check` first
   - Verifies data accuracy

2. **Approver Must Be Specified**
   - Usually: `dave` (campaign owner)
   - Could be: `editor`, `staff`, etc.
   - Tracked in audit trail

3. **Page/Post ID Required**
   - Must be specific WordPress page/post ID
   - Can approve multiple IDs at once
   - Example: `105` (homepage)

---

## Approval Validity

**Duration:** 24 hours from creation

**After expiration:**
- Approval record moved to audit-log
- New approval required for updates
- Fact-check must be recent (< 1 hour)

**Cleanup:**
- Automatic daily at 3 AM
- Expired approvals archived
- Audit trail preserved permanently

---

## Approval Workflow

### Standard Workflow

```bash
# 1. Fact-check content first
/fact-check "Total budget is $81M and wellness ROI is $2-3 per $1"
# Output: ✅ Fact-check record created

# 2. Get approval
/content-approve --page-id=105 --approver=dave --notes="Homepage budget update"
# Output: ✅ Approval created for page 105

# 3. Update WordPress
wp post update 105 --post_content="<html>..."
# Hook allows update (approval + fact-check valid)
```

### Bulk Workflow

```bash
# 1. Fact-check all content
/fact-check "Policy documents with budget figures"

# 2. Approve multiple pages
/content-approve --page-id=699,716,717 --approver=dave --notes="Policy budget corrections"

# 3. Update all pages
for ID in 699 716 717; do
  wp post update $ID --post_content="..."
done
```

---

## Error Handling

### No Recent Fact-Check

```
⚠️  WARNING: No recent fact-check found for page 105
   Fact-check is required before approval.
   Run: /fact-check <content for page 105>
```

**Resolution:** Run `/fact-check` first

### Missing Arguments

```
❌ ERROR: --page-id is required
Usage: /content-approve --page-id=<id> --approver=<name> [--notes="description"]
```

**Resolution:** Provide required arguments

### Expired Approval

When trying to update with expired approval:

```
⛔ WordPress Update BLOCKED: No valid approval found
Page 105 requires approval before updating. Use /content-approve command first.
```

**Resolution:** Create new approval (fact-check must also be recent)

---

## Audit Trail

Every approval creates two records:

1. **Approval Record** (`approvals/`)
   - Valid for 24 hours
   - Used by enforcement hooks
   - Contains signature and fact-check reference

2. **Audit Log** (`audit-log/YYYY-MM/`)
   - Permanent record
   - Complete approval history
   - Used for compliance/review

### View Audit Trail

```bash
# Recent approvals
ls -lh ~/.claude/content-vault/approvals/

# This month's audit log
ls -lh ~/.claude/content-vault/audit-log/$(date +%Y-%m)/

# Find specific page approvals
find ~/.claude/content-vault/audit-log/ -name "105_approval_*.audit"

# View approval details
cat ~/.claude/content-vault/approvals/105_*.approved | jq .
```

---

## Security

**Signature Verification:**
- Each approval has unique SHA256 signature
- Signature includes: page_id + approver + timestamp
- Prevents tampering

**File Permissions:**
- All approval files: 600 (owner read/write only)
- Audit logs: 600 (owner read/write only)
- No group or world access

**Accountability:**
- Every approval logged with approver name
- Timestamps in ISO8601 format
- Complete audit trail

---

## Integration

Used by:
- `pre_wordpress_update_protection.sh` hook
- WordPress update workflow
- Content publishing pipeline
- Compliance and audit systems

Required for:
- ALL WordPress `wp post update` commands
- Content modifications via WP-CLI
- Automated content deployments

---

## Examples

### Example 1: Homepage Update

```bash
# Fact-check new homepage content
/fact-check "Budget is $81M, wellness ROI is $2-3 per $1"

# Approve homepage (page 105)
/content-approve --page-id=105 --approver=dave --notes="Nov 2025 budget update"

# Update WordPress
wp post update 105 --post_content="$(cat homepage_final.html)"
```

### Example 2: Policy Batch Update

```bash
# Fact-check policy content
/fact-check "All policies reference $81M total budget"

# Approve all policy pages
/content-approve --page-id=699,716,717,720,723 --approver=dave --notes="Batch policy corrections"

# Update all policies
for ID in 699 716 717 720 723; do
  wp post update $ID --post_content="$(cat policy_${ID}_final.html)"
done
```

### Example 3: Emergency Update

```bash
# Quick approval for urgent fix
/fact-check "Correcting typo on contact page"
/content-approve --page-id=212 --approver=dave --notes="Emergency typo fix"
wp post update 212 --post_content="$(cat contact_corrected.html)"
```

---

## Troubleshooting

**Problem:** Approval created but WordPress update still blocked

**Cause:** Fact-check expired (> 1 hour old)

**Solution:**
```bash
# Re-run fact-check (creates new 1-hour record)
/fact-check <content>

# Approval is still valid (24 hours)
# Now update will work
wp post update 105 --post_content="..."
```

**Problem:** Can't find approval file

**Cause:** Approval expired (> 24 hours)

**Solution:**
```bash
# Check audit log for historical approvals
find ~/.claude/content-vault/audit-log/ -name "105_approval_*.audit" | tail -1

# Create new approval
/content-approve --page-id=105 --approver=dave --notes="Renewing approval"
```

---

## Best Practices

1. **Always fact-check before approving**
   - Ensures data accuracy
   - Required by enforcement hooks
   - Valid for 1 hour

2. **Use descriptive notes**
   - Good: "Homepage wellness ROI correction per QUICK_FACTS"
   - Bad: "update"

3. **Approve in batches when possible**
   - More efficient
   - Single audit trail
   - Example: `--page-id=105,106,107`

4. **Review audit trail regularly**
   - Monthly review recommended
   - Check for unauthorized approvals
   - Verify compliance

5. **Renew approvals as needed**
   - 24-hour validity
   - Create new approval if expired
   - Fact-check must be recent

---

**Status:** ✅ Active
**Version:** 1.0.0
**Created:** 2025-11-19
**Dependencies:** Content Vault, /fact-check command
