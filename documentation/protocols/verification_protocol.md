# Verification Protocol

**Version:** 1.1.0
**Last Updated:** 2025-11-08
**Owner:** Claude Code / Dave

---

## Context

After making changes, verify they worked correctly. This protocol defines what to verify and when.

## Purpose

- Ensure operations completed successfully
- Catch errors before they cause problems
- Provide confidence in changes
- Create audit trail

---

## Automatic Verification (Claude Does This)

### After File Edits
```bash
✓ Verify file exists
✓ Verify file size changed (if expected)
✓ Compare before/after
✓ Check syntax (for code files)
```

### After Git Operations
```bash
✓ Verify commit created
✓ Verify push succeeded
✓ Check remote status
```

### After WordPress Operations
```bash
✓ Run wordpress_health_check
✓ Verify content updated (wp post get)
✓ Compare final vs actual (diff)
✓ Check for errors in logs
✓ Verify specific changes applied
```

### After Deployments
```bash
✓ Run deployment_verification script
✓ Check website accessible
✓ Verify no broken links
✓ Test critical features
```

### After File Operations
```bash
✓ Verify files moved/copied
✓ Check permissions
✓ Verify count matches expected
```

---

## Verification Checklist by Operation Type

### WordPress Content Updates
- [ ] Content matches intended changes
- [ ] Saved "_after" file from actual WordPress state
- [ ] Ran diff between "_final" and "_after" files
- [ ] Verified specific text/numbers present in "_after" file
- [ ] No broken links introduced
- [ ] Images display correctly
- [ ] Formatting preserved
- [ ] Pre-deployment validator passes (if deploying)

### Deployments
- [ ] All files uploaded successfully
- [ ] Plugins activated
- [ ] No PHP errors
- [ ] Health check passes
- [ ] Analytics tracking works

### Script Creation/Modification
- [ ] Syntax valid (shellcheck, python -m py_compile)
- [ ] Executable permissions set
- [ ] Script runs without errors
- [ ] Produces expected output

### Git Operations
- [ ] Commit includes all intended files
- [ ] Commit message follows format
- [ ] Push successful
- [ ] Remote matches local

### File Organization
- [ ] Expected number of files processed
- [ ] No files lost
- [ ] Permissions preserved
- [ ] Duplicates identified correctly

---

## WordPress Content Verification (Detailed)

### CRITICAL: After EVERY wp post update

**This is the most important verification step - DO NOT SKIP**

#### Step 1: Save Actual State from WordPress

```bash
# Get actual content from WordPress after update
wp post get {ID} --field=post_content > "$SESSION_DIR/{resource}_{id}_after.html"

# Example:
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
```

**Why this matters:**
- Verifies update actually applied
- Catches WordPress HTML sanitization
- Detects plugin content filters
- Proves update succeeded

#### Step 2: Compare Final vs Actual

```bash
# Compare what you intended vs what actually got saved
diff "$SESSION_DIR/{resource}_{id}_final.html" "$SESSION_DIR/{resource}_{id}_after.html"

# Example:
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"
```

**Interpreting diff results:**

**✅ No output (files identical):**
```bash
$ diff page_105_final.html page_105_after.html
$ # (no output = success)
```
- Update applied exactly as intended
- No WordPress modifications
- Perfect success

**⚠️ Minor differences (WordPress formatting):**
```bash
$ diff page_105_final.html page_105_after.html
< <p>Text</p>
> <p>Text</p>
```
- WordPress may have added/removed whitespace
- May have formatted HTML differently
- Usually harmless
- **Verify content substance unchanged**

**❌ Major differences (INVESTIGATE):**
```bash
$ diff page_105_final.html page_105_after.html
< $81M
> $110.5M
```
- Update may have failed
- Content may have been reverted
- Plugin may have filtered content
- **DO NOT PROCEED - Investigate issue**

#### Step 3: Verify Specific Changes

```bash
# Verify expected text is present
grep "expected text" "$SESSION_DIR/{resource}_{id}_after.html"

# Example - verify new budget number
grep "\$81M" "$SESSION_DIR/page_105_after.html" && echo "✅ Budget updated" || echo "❌ Budget not found"

# Verify old text is gone
if grep -q "old text" "$SESSION_DIR/{resource}_{id}_after.html"; then
  echo "❌ Old text still present - update may have failed"
else
  echo "✅ Old text removed successfully"
fi

# Example - verify old budget removed
if grep -q "\$110.5M" "$SESSION_DIR/page_105_after.html"; then
  echo "❌ Old budget still present"
else
  echo "✅ Old budget removed"
fi
```

#### Step 4: Verify Content Length

```bash
# Check content length (catches empty updates)
BEFORE_LENGTH=$(wc -c < "$SESSION_DIR/{resource}_{id}_before.html")
AFTER_LENGTH=$(wc -c < "$SESSION_DIR/{resource}_{id}_after.html")

echo "Before: $BEFORE_LENGTH characters"
echo "After: $AFTER_LENGTH characters"
echo "Change: $((AFTER_LENGTH - BEFORE_LENGTH)) characters"

# If after is significantly smaller, investigate
if [ $AFTER_LENGTH -lt $((BEFORE_LENGTH / 2)) ]; then
  echo "⚠️ WARNING: Content significantly smaller - verify update"
fi
```

#### Step 5: Check for Common Issues

```bash
# Check for broken HTML
if grep -q '<[^>]*$' "$SESSION_DIR/{resource}_{id}_after.html"; then
  echo "⚠️ Possible broken HTML tag"
fi

# Check for broken links
grep -oE 'href="[^"]*"' "$SESSION_DIR/{resource}_{id}_after.html" | \
  grep -E '(href="/$|href="//$)' && \
  echo "⚠️ Possible broken links found"

# Check for encoding issues
if grep -q '�' "$SESSION_DIR/{resource}_{id}_after.html"; then
  echo "⚠️ Encoding issues detected"
fi
```

### WordPress Verification Example (Complete)

```bash
# After running: wp post update 105 --post_content="$(cat $SESSION_DIR/page_105_final.html)"

echo "=== Verifying WordPress Update ==="

# 1. Get actual state
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
echo "✓ Retrieved actual content from WordPress"

# 2. Compare final vs actual
echo ""
echo "Comparing final vs actual..."
if diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html" > "$SESSION_DIR/diff_output.txt"; then
  echo "✅ Files identical - update applied exactly"
else
  echo "⚠️ Differences found - reviewing..."
  cat "$SESSION_DIR/diff_output.txt"
fi

# 3. Verify specific changes
echo ""
echo "Verifying specific changes..."
grep "\$81M" "$SESSION_DIR/page_105_after.html" > /dev/null && echo "✅ New budget (\$81M) present" || echo "❌ New budget NOT found"
grep "\$2-3" "$SESSION_DIR/page_105_after.html" > /dev/null && echo "✅ New ROI (\$2-3) present" || echo "❌ New ROI NOT found"

# Check old values removed
if grep "\$110.5M" "$SESSION_DIR/page_105_after.html" > /dev/null; then
  echo "❌ Old budget (\$110.5M) still present - UPDATE FAILED"
else
  echo "✅ Old budget removed"
fi

# 4. Content length check
BEFORE=$(wc -c < "$SESSION_DIR/page_105_before.html")
AFTER=$(wc -c < "$SESSION_DIR/page_105_after.html")
echo ""
echo "Content length: $BEFORE → $AFTER ($((AFTER - BEFORE)) change)"

# 5. Final status
echo ""
echo "=== Verification Complete ==="
```

### WordPress Verification for Multiple Items

```bash
# After bulk updates
echo "=== Verifying Bulk WordPress Updates ==="

for ID in 699 716 717; do
  echo ""
  echo "Verifying resource $ID..."

  # Get actual state
  wp post get $ID --field=post_content > "$SESSION_DIR/policy_${ID}_after.html"

  # Compare
  if diff "$SESSION_DIR/policy_${ID}_final.html" "$SESSION_DIR/policy_${ID}_after.html" > /dev/null; then
    echo "✅ Policy $ID: Update verified"
  else
    echo "❌ Policy $ID: Differences detected"
    diff "$SESSION_DIR/policy_${ID}_final.html" "$SESSION_DIR/policy_${ID}_after.html" | head -20
  fi
done

echo ""
echo "=== All Verifications Complete ==="
```

### When Verification Fails

**If diff shows major differences:**

1. **Review the differences:**
   ```bash
   diff -u "$SESSION_DIR/final.html" "$SESSION_DIR/after.html" | less
   ```

2. **Check WordPress logs:**
   ```bash
   wp eval 'error_log("Test");' # Verify error logging works
   # Check PHP error logs for issues
   ```

3. **Try update again:**
   ```bash
   # Sometimes first update fails
   wp post update {ID} --post_content="$(cat "$SESSION_DIR/final.html")"
   wp post get {ID} --field=post_content > "$SESSION_DIR/after_retry.html"
   diff "$SESSION_DIR/final.html" "$SESSION_DIR/after_retry.html"
   ```

4. **Check for plugin conflicts:**
   ```bash
   # Try without plugins
   wp post update {ID} --post_content="$(cat "$SESSION_DIR/final.html")" --skip-plugins
   ```

5. **Rollback and investigate:**
   ```bash
   # Restore original content
   wp post update {ID} --post_content="$(cat "$SESSION_DIR/before.html")"
   # Investigate why update failed
   ```

---

## Examples

### Example 1: WordPress Page Update

**Operation:** Update budget page

**Automatic Verification:**
```bash
# Verify update applied
wp post get 145 --field=post_content | grep "$NEW_VALUE"
✓ Content updated

# Run health check
bash wordpress_health_check_v1.0.0.sh
✓ No errors detected

# Check for broken links
# (pre-deployment validator does this)
✓ No broken links

Status: ✅ Verified successfully
```

### Example 2: Git Commit and Push

**Operation:** Commit and push changes

**Automatic Verification:**
```bash
# Verify commit created
git log -1 --oneline
✓ 5ee5bd4 Your commit message

# Verify push succeeded
git push origin master
To github.com:user/repo.git
   abc123..5ee5bd4  master -> master
✓ Push successful

# Verify remote matches local
git log HEAD..origin/master
(no output = in sync)
✓ Remote up to date

Status: ✅ Verified successfully
```

### Example 3: File Organization

**Operation:** Organize 100 documents

**Automatic Verification:**
```bash
# Count files before
BEFORE_COUNT=100

# Run organization
utilities organize ~/Documents

# Verify count (should match)
AFTER_COUNT=$(find ~/Documents/Organized -type f | wc -l)
✓ 100 files organized (none lost)

# Check log for errors
grep "ERROR" organization.log
(no output = no errors)
✓ No errors during organization

Status: ✅ Verified successfully
```

---

## Manual Verification (User Should Check)

### Campaign Content Accuracy
❗ Claude cannot fact-check
❗ User must verify numbers match source documents
❗ User must verify claims are accurate

### Visual Appearance
❗ Claude cannot see rendered pages
❗ User must verify design looks correct
❗ User must verify images display properly

### User Experience
❗ Claude cannot test as real user
❗ User must test forms submission
❗ User must test navigation
❗ User must verify mobile responsiveness

---

## Verification Commands

### Quick Verification Commands
```bash
# Verify WordPress health
bash ~/rundaverun/campaign/skippy-scripts/wordpress/wordpress_health_check_v1.0.0.sh

# Verify git status
git status
git log -1

# Verify file exists and size
ls -lh /path/to/file

# Verify script syntax
bash -n script.sh
python -m py_compile script.py

# Verify service running
systemctl status service_name
docker ps

# Verify port open
curl -I http://localhost:8000
```

---

## When Verification Fails

### If Verification Fails:
1. Stop further operations
2. Show user what failed
3. Explain expected vs actual
4. Suggest fix or rollback
5. Don't proceed until verified

### Example:
```
❌ Verification Failed

Expected: 100 files organized
Actual: 95 files found

5 files appear to be missing. This is unexpected.

Options:
1. Check organization log for errors
2. Search for missing files
3. Rollback operation
4. Investigate before proceeding

What would you like to do?
```

---

## Best Practices

### DO:
✅ Verify every critical operation
✅ Show verification results
✅ Stop if verification fails
✅ Document what was verified

### DON'T:
❌ Skip verification for "quick" operations
❌ Assume operations succeeded
❌ Continue after failed verification
❌ Verify only at the end (verify progressively)

---

## Quick Reference

```bash
# After WordPress updates
bash wordpress_health_check_v1.0.0.sh

# After git operations
git status && git log -1

# After file operations
ls -l target/directory/

# After deployments
bash deployment_verification_v1.0.0.sh

# After script creation
bash -n script.sh && ./script.sh --help
```

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
