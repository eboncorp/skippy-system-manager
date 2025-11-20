# WordPress Update Workflow

**Version:** 2.0.0 (Enhanced with Enforcement Hooks)
**Last Updated:** 2025-11-19

Complete step-by-step workflow for WordPress content updates with approval and fact-checking enforcement.

---

## Pre-Flight Checklist

Before ANY WordPress update:
- [ ] WordPress installation path verified
- [ ] Session directory created
- [ ] Original content backed up
- [ ] Content fact-checked (< 1 hour ago)
- [ ] Approval obtained (< 24 hours ago)

---

## Step 0: Verify WordPress Installation Path

**ALWAYS verify correct WordPress installation path BEFORE starting:**

```bash
# 1. Check WordPress database connection
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" db check

# 2. Verify site URL matches expectation
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" option get siteurl
# Expected: http://rundaverun-local-complete-022655.local

# 3. For Local by Flywheel, verify active installation path
cat ~/.config/Local/sites.json | python3 -m json.tool | grep -A 5 "rundaverun"

# 4. Test HTTP accessibility
curl -I "http://rundaverun-local-complete-022655.local" | grep "HTTP/1.1 200"
```

---

## Step 1: Create Session Directory

```bash
# WordPress work (local development)
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"
echo "Created session: $SESSION_DIR"
```

**Description naming:**
- Use underscores: `homepage_fixes` not `homepage-fixes`
- Be specific: `page_105_wellness_roi_update` not `updates`
- 2-5 words max

---

## Step 2: Save Original State

```bash
# WordPress pages
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# WordPress posts
wp post get 941 --field=post_content > "$SESSION_DIR/post_941_before.html"

# Policy documents
wp post get 699 --field=post_content > "$SESSION_DIR/policy_699_before.html"
```

---

## Step 3: Make Changes (Save Iterations)

```bash
# First edit
cat "$SESSION_DIR/page_105_before.html" | sed 's/old/new/g' > "$SESSION_DIR/page_105_v1.html"

# Second edit
cat "$SESSION_DIR/page_105_v1.html" | sed 's/foo/bar/g' > "$SESSION_DIR/page_105_v2.html"

# Python conversion (MUST use SESSION_DIR)
python3 << PYEOF > "$SESSION_DIR/page_331_converted.html"
import markdown
with open("$SESSION_DIR/source.md") as f:
    print(markdown.markdown(f.read()))
PYEOF
```

---

## Step 4: Fact-Check Content (REQUIRED)

**This step is CRITICAL - WordPress updates will be BLOCKED without recent fact-check**

```bash
# Run fact-check command
/fact-check "Total budget is $81M and wellness ROI is $2-3 per $1"

# Creates record: ~/.claude/content-vault/fact-checks/{page_id}_{timestamp}.fact-checked
# Valid for: 1 hour
```

**Verification record enables approval and updates**

---

## Step 5: Get Approval (REQUIRED)

**WordPress updates will be BLOCKED without valid approval**

```bash
# Approve single page
/content-approve --page-id=105 --approver=dave --notes="Homepage wellness ROI update"

# Approve multiple pages
/content-approve --page-id=105,106,107 --approver=dave --notes="Budget corrections"

# Creates record: ~/.claude/content-vault/approvals/{page_id}_{timestamp}.approved
# Valid for: 24 hours
```

**Approval requires recent fact-check (< 1 hour)**

---

## Step 6: Save Final Version

```bash
# This is the version you're about to apply
cp "$SESSION_DIR/page_105_v2.html" "$SESSION_DIR/page_105_final.html"
```

---

## Step 7: Apply Changes

```bash
# WordPress update (enforcement hooks will verify approval + fact-check)
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# If approved and fact-checked: ✅ Update succeeds
# If not approved: ⛔ BLOCKED - run /content-approve
# If fact-check expired: ⛔ BLOCKED - run /fact-check
```

---

## Step 8: Verify Update (CRITICAL)

**THIS STEP IS CRITICAL - DO NOT SKIP**

```bash
# A. Database Verification
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"

# Compare to verify update worked
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"
# If diff shows differences, INVESTIGATE before proceeding

# B. HTTP Verification (for media/public resources)
SITE_URL=$(wp option get siteurl)
curl -I "$SITE_URL/?p=105" | grep "HTTP" >> "$SESSION_DIR/http_verification.log"

# C. Functional Verification
curl -s "$SITE_URL/?p=105" | grep "expected content" && echo "✅ Page renders correctly"
```

---

## Step 9: Document Changes (MANDATORY)

```bash
cat > "$SESSION_DIR/README.md" <<EOF
# Session: Homepage Wellness ROI Update

**Date:** $(date)
**Resources Modified:** Page 105 (Homepage)
**Changes Made:**
- Updated wellness center ROI from \$1.80 to \$2-3
- Fixed budget figure from \$110.5M to \$81M

**Approval:**
- Approver: dave
- Fact-check: ✅ Verified
- Timestamp: $(date -Iseconds)

**Status:** ✅ Completed successfully

**Files:**
- page_105_before.html - Original state
- page_105_v1.html - First edit (ROI fix)
- page_105_v2.html - Second edit (budget fix)
- page_105_final.html - Final version for update
- page_105_after.html - Verified actual state after update

**Verification:**
\`\`\`
diff page_105_final.html page_105_after.html
# (no differences - update successful)
\`\`\`
EOF
```

---

## Complete Example: Homepage Update

```bash
# 1. CREATE SESSION
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_homepage_wellness_roi_fix"
mkdir -p "$SESSION_DIR"
echo "Created session: $SESSION_DIR"

# 2. SAVE ORIGINAL
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# 3. CREATE EDITS
cat "$SESSION_DIR/page_105_before.html" | \
  sed 's/\$1\.80/\$2-3/g' > "$SESSION_DIR/page_105_v1.html"

cat "$SESSION_DIR/page_105_v1.html" | \
  sed 's/\$110\.5M/\$81M/g' > "$SESSION_DIR/page_105_v2.html"

# 4. FACT-CHECK (REQUIRED)
/fact-check "Updated ROI to $2-3 per $1 and budget to $81M per QUICK_FACTS"

# 5. GET APPROVAL (REQUIRED)
/content-approve --page-id=105 --approver=dave --notes="Homepage budget corrections"

# 6. SAVE FINAL
cp "$SESSION_DIR/page_105_v2.html" "$SESSION_DIR/page_105_final.html"

# 7. APPLY UPDATE
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# 8. VERIFY
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# 9. DOCUMENT
cat > "$SESSION_DIR/README.md" <<EOF
# Homepage Budget Corrections
Completed: $(date)
Status: ✅ Verified successful
EOF

# Report to user
echo "✅ Session complete: $SESSION_DIR"
```

---

## Emergency Rollback

**When to use:** Update failed, wrong content published, site broken

```bash
# 1. Find most recent session
ls -lt /home/dave/skippy/work/wordpress/rundaverun-local/ | head -5

# 2. Set session directory
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/[directory_name]"

# 3. Rollback to original state
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_before.html")"

# 4. Verify rollback
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_rolledback.html"
diff "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_rolledback.html"

# 5. If diff shows no output, rollback successful ✅
```

---

## Enforcement Hook Behavior

### WordPress Update Protection Hook

**Blocks updates when:**
- No valid approval (< 24 hours)
- No recent fact-check (< 1 hour)
- Page ID cannot be determined

**Allows updates when:**
- Valid approval exists
- Recent fact-check exists
- Both verified and logged to audit trail

### Error Messages

**No Approval:**
```
⛔ WordPress Update BLOCKED: No valid approval found
Page 105 requires approval before updating. Use /content-approve command first.
Remediation: Run: /content-approve --page-id=105 --approver=dave --notes="..."
```

**No Fact-Check:**
```
⛔ WordPress Update BLOCKED: No recent fact-check found
Page 105 requires fact-checking within the last hour.
Remediation: Run: /fact-check <content to verify>
```

**Success:**
```
✅ WordPress Update APPROVED
Page 105 approved by dave at 2025-11-19T10:30:00Z. Fact-check verified.
```

---

## Best Practices

1. **Always create session directory FIRST**
2. **Always save original state BEFORE changes**
3. **Always fact-check content BEFORE approval**
4. **Always get approval BEFORE update**
5. **Always verify update succeeded**
6. **Never skip documentation**
7. **Never use /tmp/ for work files**

---

**Status:** ✅ Active
**Dependencies:** Content Vault, /fact-check, /content-approve
