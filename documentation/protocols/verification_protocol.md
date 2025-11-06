# Verification Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
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
✓ Verify content updated
✓ Check for errors in logs
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
- [ ] No broken links introduced
- [ ] Images display correctly
- [ ] Formatting preserved
- [ ] Pre-deployment validator passes

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
