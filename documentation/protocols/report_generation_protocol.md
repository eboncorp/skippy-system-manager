# Report Generation Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-08
**Owner:** Claude Code / Dave

---

## Context

Every significant work session should generate a report documenting what was done, what changed, and results. Reports provide continuity across sessions and serve as project history.

## Purpose

- Document work performed
- Enable work continuation in future sessions
- Provide project history and audit trail
- Share progress with stakeholders

---

## When to Generate Reports

### ALWAYS Generate for:
- ✅ Multi-step tasks (30+ minutes of work)
- ✅ WordPress content updates
- ✅ Deployments to production
- ✅ Bug fixes and troubleshooting
- ✅ New feature implementations
- ✅ Work that will continue in future sessions

### NOT Needed for:
- ❌ Quick 5-minute tasks
- ❌ Simple file reads/searches
- ❌ Research-only sessions with no changes

---

## Standard Report Location

**ALL reports MUST be saved to:**
```
/home/dave/skippy/conversations/
```

## Naming Convention

```
{topic}_{YYYY-MM-DD}.md
```

**Examples:**
- `wordpress_diagnostic_fixes_2025-11-08.md`
- `voter_registration_implementation_2025-11-08.md`
- `budget_corrections_2025-11-02.md`

**Guidelines:**
- Use lowercase with underscores
- Be descriptive (3-5 words)
- Include full date
- Use `.md` extension

---

## Required Report Sections

### 1. Summary (Required)
- 2-4 sentences
- What was accomplished
- Key outcomes

### 2. What Was Changed (Required)
- Bullet list of changes
- Be specific (page IDs, file names, etc.)
- Include quantities (5 pages, 132 links, etc.)

### 3. Files Modified (Required)
- List of files/resources changed
- Include paths
- Note new vs modified

### 4. Status (Required)
- ✅ Completed successfully
- ⚠️ Completed with notes
- ❌ Failed (with reason)
- 🔄 In progress

### 5. Next Steps (If applicable)
- Follow-up tasks
- Future work needed
- Unresolved issues

---

## Report Templates

### Template 1: WordPress Content Update

```markdown
# [Title] - YYYY-MM-DD

**Site:** [rundaverun / rundaverun-local]
**Session:** [session directory path]
**Status:** [✅⚠️❌]

---

## Summary

[2-4 sentences describing what was done]

## Changes Made

- Change 1: [description]
- Change 2: [description]
- Change 3: [description]

## Resources Modified

| ID | Type | Title | Changes |
|----|------|-------|---------|
| 105 | Page | Homepage | [what changed] |
| 699 | Policy | Budget | [what changed] |

## Files Modified

- `/path/to/file1` - [what changed]
- `/path/to/file2` - [what changed]

## Verification

```bash
[verification commands run]
[verification results]
```

## Session Files

**Location:** `/home/dave/skippy/work/wordpress/{site}/{session}/`

**Files:**
- resource_id_before.html
- resource_id_v1.html
- resource_id_final.html
- resource_id_after.html
- README.md

## Next Steps

- [Future task 1]
- [Future task 2]

---

**Completed:** YYYY-MM-DD HH:MM
```

### Template 2: Diagnostic/Debugging Session

```markdown
# [Issue] Diagnostic Report - YYYY-MM-DD

**Issue:** [Brief description]
**Severity:** [Critical/High/Medium/Low]
**Status:** [✅ Resolved / ⚠️ Partial / ❌ Unresolved]

---

## Summary

[What was wrong, how it was diagnosed, how it was fixed]

## Issue Description

**Symptoms:**
- [Symptom 1]
- [Symptom 2]

**Impact:**
- [What was affected]

## Diagnostic Process

1. [Step 1]: [What was checked]
   - Result: [Finding]

2. [Step 2]: [What was tested]
   - Result: [Finding]

## Root Cause

[What caused the issue]

## Resolution

[How it was fixed]

**Commands Run:**
```bash
[commands used]
```

## Verification

[How fix was verified]

## Prevention

[How to prevent recurrence]

---

**Completed:** YYYY-MM-DD HH:MM
```

### Template 3: Feature Implementation

```markdown
# [Feature Name] Implementation - YYYY-MM-DD

**Status:** [✅ Complete / 🔄 In Progress]
**Scope:** [Brief description]

---

## Summary

[What was implemented and why]

## Implementation Details

### Components Added

- Component 1: [description]
- Component 2: [description]

### Files Created/Modified

- `file1.php` - [purpose]
- `file2.js` - [purpose]

### Configuration Changes

- Setting 1: `old` → `new`
- Setting 2: `old` → `new`

## Testing

- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual testing complete

## Documentation

- [x] Code comments added
- [x] README updated
- [x] Protocol updated (if applicable)

## Next Steps

- [Remaining task 1]
- [Remaining task 2]

---

**Completed:** YYYY-MM-DD HH:MM
```

---

## Quick Report Generation

For standard WordPress updates:

```bash
cat > "/home/dave/skippy/conversations/{topic}_$(date +%Y-%m-%d).md" <<EOF
# [Title] - $(date +%Y-%m-%d)

**Status:** ✅ Completed successfully

## Summary

[2-4 sentences]

## Changes Made

- [List changes]

## Files Modified

- [List files]

## Verification

All changes verified successfully.

---

**Completed:** $(date +%Y-%m-%d\ %H:%M)
EOF
```

---

## Report Quality Checklist

Before saving report:
- [ ] Filename follows naming convention
- [ ] Saved to /home/dave/skippy/conversations/
- [ ] Summary is clear and concise
- [ ] Changes are specific and detailed
- [ ] Status is clearly indicated
- [ ] Session directory path included (if applicable)
- [ ] Verification results documented
- [ ] Next steps noted (if incomplete)

---

## Best Practices

### DO:
✅ Be specific (use IDs, filenames, quantities)
✅ Include verification results
✅ Document both successes and failures
✅ Link to session directories
✅ Use clear status indicators (✅⚠️❌)

### DON'T:
❌ Use vague descriptions ("updated stuff")
❌ Skip file listings
❌ Omit verification steps
❌ Forget to document failures
❌ Use inconsistent naming

---

## Related Protocols

- [Work Session Documentation Protocol](work_session_documentation_protocol.md)
- [WordPress Content Update Protocol](wordpress_content_update_protocol.md)
- [Verification Protocol](verification_protocol.md)

---

**Generated:** 2025-11-08
**Status:** Active
**Next Review:** 2025-12-08
```
