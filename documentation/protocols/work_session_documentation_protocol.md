# Work Session Documentation Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

Every work session generates documentation automatically following established patterns. This protocol defines what gets documented, where, and when.

## Purpose

- Maintain comprehensive work history
- Enable session continuity across conversations
- Create searchable knowledge base
- Preserve before/after states for auditing
- Never lose work due to forgotten context

---

## Automatic Documentation (Claude Does This)

### 1. Conversation Summaries
**What:** High-level summary of session work
**Where:** `/home/dave/skippy/conversations/`
**When:** At end of significant work sessions
**Format:** `{topic}_{description}_YYYY-MM-DD.md`

**Contents:**
- What was requested
- What was done
- Files changed
- Commands executed
- Results achieved
- Next steps (if applicable)

### 2. Work Files (Edits)
**What:** Before/after versions of edited files
**Where:** `/home/dave/skippy/work/{project}/{subproject}/YYYYMMDD_HHMMSS_{description}/`
**When:** Every file edit operation
**Format:**
- `{resource}_{id}_before.{ext}`
- `{resource}_{id}_v1.{ext}` (iterations)
- `{resource}_{id}_final.{ext}`
- `{resource}_{id}_after.{ext}` (verification)

**Contents:**
- Original file state
- Intermediate versions
- Final version
- Applied changes
- README.md or session_notes.txt

### 3. Analysis Reports
**What:** Detailed technical analysis
**Where:** `/home/dave/skippy/conversations/`
**When:** After significant analysis or investigation
**Format:** `{topic}_analysis_YYYY-MM-DD.md`

**Contents:**
- Problem statement
- Investigation process
- Findings
- Recommendations
- Implementation details

### 4. Task Tracking (TodoWrite)
**What:** Real-time task progress
**Where:** In-memory during session, saved to conversation summary
**When:** Throughout work session
**Format:** TodoWrite tool updates

**Contents:**
- Task list with status (pending, in_progress, completed)
- Active form descriptions
- Progress indicators

---

## Documentation Standards

### File Naming Conventions

**Conversation Files:**
```
{project}_{topic}_{YYYY-MM-DD}.md
{topic}_analysis_{YYYY-MM-DD}.md
{project}_deployment_summary_{YYYY-MM-DD}.md
{topic}_complete_{YYYY-MM-DD}.md
```

**Examples:**
```
rundaverun_budget_update_2025-11-06.md
wordpress_optimization_analysis_2025-11-06.md
utilities_upgrade_analysis_2025-11-06.md
deployment_complete_2025-11-06.md
```

**Work Files:**
```
/home/dave/skippy/work/{project}/{subproject}/{YYYYMMDD_HHMMSS}_{description}/
```

**Examples:**
```
/home/dave/skippy/work/wordpress/rundaverun/20251106_141523_budget_page_update/
/home/dave/skippy/work/wordpress/rundaverun/20251106_153045_policy_fixes/
/home/dave/skippy/work/general/file_cleanup/20251106_160000_downloads_organize/
```

### Directory Structure

```
/home/dave/skippy/
├── conversations/              # All conversation summaries and analyses
│   ├── rundaverun_*.md
│   ├── utilities_*.md
│   ├── wordpress_*.md
│   └── general_*.md
│
├── work/                       # Work files (edits, iterations)
│   ├── wordpress/
│   │   └── rundaverun/
│   │       └── YYYYMMDD_HHMMSS_description/
│   ├── general/
│   │   ├── file_cleanup/
│   │   └── system_maintenance/
│   └── scripts/
│       └── development/
│
└── claude/
    └── uploads/                # Files prepared for Claude.ai upload
```

---

## What Gets Documented

### Always Document:
✅ File edits (before/after)
✅ Configuration changes
✅ Deployment activities
✅ Security-sensitive operations
✅ Database modifications
✅ Git commits and merges
✅ Analysis and investigations
✅ Problem resolutions

### Usually Document:
📝 Feature implementations
📝 Bug fixes
📝 Performance optimizations
📝 Script creations
📝 Protocol additions

### Don't Document:
❌ Simple read operations
❌ Status checks (git status, ls, etc.)
❌ Quick questions with immediate answers
❌ Trivial directory listings

---

## Procedure

### During Work Session

**Step 1: Session Start**
```
Claude automatically:
- Checks for related previous conversations
- Loads relevant context
- Initializes TodoWrite if complex task
```

**Step 2: During Work**
```
For each file edit:
1. Create session directory if doesn't exist
2. Save {file}_before.{ext}
3. Save iterations as needed
4. Save {file}_final.{ext}
5. Apply changes
6. Save {file}_after.{ext} for verification
```

**Step 3: Session End**
```
If significant work done:
1. Create conversation summary in skippy/conversations/
2. Update TodoWrite to show completion
3. Note next steps if work continues
```

### Documentation Template

**Conversation Summary Format:**
```markdown
# [Project] - [Topic] - [YYYY-MM-DD]

## Summary
[1-2 sentence overview]

## Work Completed
- [Major accomplishment 1]
- [Major accomplishment 2]
- [Major accomplishment 3]

## Files Changed
- /path/to/file1 - [what changed]
- /path/to/file2 - [what changed]

## Commands Executed
```bash
[key commands]
```

## Results
[What was achieved]

## Next Steps (if applicable)
- [ ] [Future task 1]
- [ ] [Future task 2]

---
**Generated:** [timestamp]
**Work Files:** /home/dave/skippy/work/[path]
**Related:** [links to related docs]
```

---

## Examples

### Example 1: Campaign Page Update

**User Request:**
```
Update the rundaverun budget page to fix transportation numbers
```

**Claude Creates:**

1. **Work Directory:**
```
/home/dave/skippy/work/wordpress/rundaverun/20251106_141523_budget_page_update/
├── post_145_before.html
├── post_145_v1.html
├── post_145_final.html
├── post_145_after.html
└── README.md
```

2. **Conversation Summary:**
```
/home/dave/skippy/conversations/rundaverun_budget_page_update_2025-11-06.md
```

**Contents:**
```markdown
# RunDaveRun - Budget Page Transportation Fix - 2025-11-06

## Summary
Updated transportation budget numbers on the campaign budget page to reflect accurate FY2026 allocations.

## Work Completed
- Read current budget page content (post ID 145)
- Updated transportation allocation: $500M → $525M
- Updated percentage: 15% → 16%
- Verified calculations accurate
- Ran pre-deployment validator
- Applied changes to production

## Files Changed
- Post ID 145 (Budget Page) - Updated transportation section

## Work Files
/home/dave/skippy/work/wordpress/rundaverun/20251106_141523_budget_page_update/
- post_145_before.html - Original content
- post_145_v1.html - With transportation updates
- post_145_final.html - Final version
- post_145_after.html - Verification from production

## Verification
✅ Pre-deployment validator passed
✅ No broken links
✅ Math calculations correct
✅ Content matches official budget documents

## Next Steps
None - work complete.

---
**Generated:** 2025-11-06 14:23:45
**Session Duration:** 8 minutes
```

### Example 2: Repository Update Analysis

**User Request:**
```
Check eboncorp repos for upgrades
```

**Claude Creates:**

**Conversation Summary:**
```
/home/dave/skippy/conversations/eboncorp_repos_update_summary_2025-11-06.md
```

**Contents:**
```markdown
# EbonCorp Repositories - Update Check - 2025-11-06

## Summary
Checked all 3 eboncorp repositories for available updates. Found and merged major upgrade to utilities repository.

## Repositories Checked
✅ skippy-system-manager - Up to date
✅ rundaverun-website - Up to date
🚀 utilities - Major upgrade available and merged

## Utilities Upgrade Details
- 34 files changed
- 5,131 lines added
- New features: CLI, web dashboard, database tracking, tests
- Merge type: Fast-forward (no conflicts)
- Status: Successfully merged and pushed

## Commands Executed
```bash
cd /home/dave/utilities
git fetch origin
git checkout claude/incomplete-description-011CUqiGwdhyzRxSQtFxyshh
git checkout master
git merge claude/incomplete-description-011CUqiGwdhyzRxSQtFxyshh --ff-only
git push origin master
```

## Results
All repositories now up to date with latest improvements.

## Related Documentation
- utilities_upgrade_analysis_2025-11-06.md (detailed analysis)

---
**Generated:** 2025-11-06
**Duration:** 25 minutes
```

### Example 3: Duplicate File Cleanup

**User Request:**
```
Find duplicates in Downloads folder
```

**Claude Creates:**

**Work Directory:**
```
/home/dave/skippy/work/general/file_cleanup/20251106_160000_downloads_duplicates/
├── duplicates_report.txt
├── duplicates_summary.json
└── README.md
```

**README.md:**
```markdown
# Downloads Duplicate Files Cleanup - 2025-11-06

## Summary
Scanned ~/Downloads for duplicate files using utilities package.

## Results
- Total files scanned: 1,247
- Duplicate groups found: 23
- Total wasted space: 2.3 GB
- Largest duplicate: video_file.mp4 (450 MB, 3 copies)

## Action Taken
- Generated report: duplicates_report.txt
- User review required before deletion

## Files
- duplicates_report.txt - Full list of duplicates
- duplicates_summary.json - Machine-readable summary

## Command Used
```bash
utilities find-duplicates ~/Downloads
```

## Next Steps
User to review duplicates_report.txt and decide which to delete.

---
**Generated:** 2025-11-06 16:05:23
```

---

## User Actions (Optional)

While Claude handles documentation automatically, you can:

### Request Additional Documentation
```
"Create a detailed report of what we did today"
"Document this for future reference"
"Create a summary I can share"
```

### Request Specific Format
```
"Create a markdown summary"
"Export this as a checklist"
"Create a quick reference guide"
```

### Request Upload Preparation
```
"Prepare this for Claude.ai upload"
→ Claude saves to /home/dave/skippy/claude/uploads/
```

---

## Documentation Search

### Finding Previous Work

**By Topic:**
```bash
grep -r "budget update" /home/dave/skippy/conversations/
grep -r "WordPress optimization" /home/dave/skippy/conversations/
```

**By Date:**
```bash
ls -lt /home/dave/skippy/conversations/ | grep "2025-11-06"
find /home/dave/skippy/conversations/ -name "*2025-11-06*"
```

**By Project:**
```bash
ls /home/dave/skippy/conversations/rundaverun_*
ls /home/dave/skippy/conversations/wordpress_*
ls /home/dave/skippy/conversations/utilities_*
```

**Work Files:**
```bash
find /home/dave/skippy/work/ -name "*budget*"
ls -lt /home/dave/skippy/work/wordpress/rundaverun/
```

---

## Retention Policy

**Conversation Files:**
- Keep indefinitely (they're small, plain text)
- Archive old files monthly (see Conversation Cleanup Protocol)

**Work Files:**
- Keep active files: 30 days
- Archive to compressed format: 90 days
- Delete after: 120 days total

**Automatic Cleanup:**
```bash
# Will be implemented in cleanup protocol
/home/dave/skippy/scripts/maintenance/cleanup_old_work_files.sh
```

---

## Integration with Other Protocols

**Related Protocols:**
- [Session Start Protocol](session_start_protocol.md) - How sessions begin
- [Context Preservation Protocol](context_preservation_protocol.md) - Multi-session work
- [Conversation Cleanup Protocol](conversation_cleanup_protocol.md) - Organization
- Work Files Preservation Protocol (in CLAUDE.md) - File handling

**Tools:**
- TodoWrite - Task tracking during sessions
- Conversation files - Session summaries
- Work directories - File versions
- Git - Version control integration

---

## Best Practices

### DO:
✅ Let Claude document automatically
✅ Trust the documentation system
✅ Reference previous work by filename
✅ Keep work files for the retention period
✅ Use conversation files to continue work

### DON'T:
❌ Delete work files prematurely
❌ Skip creating work directories for edits
❌ Use /tmp/ for work files (gets deleted on reboot)
❌ Manually create documentation (unless requested)
❌ Worry about over-documenting (storage is cheap)

---

## Quick Reference

### Find Previous Work
```bash
# By project
ls ~/skippy/conversations/rundaverun_*

# By date
ls ~/skippy/conversations/*2025-11-06*

# By topic
grep -l "budget" ~/skippy/conversations/*.md

# Recent work files
ls -lt ~/skippy/work/wordpress/rundaverun/
```

### Continue Previous Work
```
User: "Continue from [date] work on [topic]"
Claude: [Searches conversations, loads context, continues]
```

---

## Version History

**1.0.0 (2025-11-06)**
- Initial protocol creation
- Defined automatic documentation standards
- Integrated with existing work files protocol
- Added examples and templates

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
