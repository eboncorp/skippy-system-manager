# Transcript Management Protocol

**Version:** 2.0.0
**Created:** 2025-11-05 (Consolidated from auto_transcript v1.0.0 + session_transcript v1.0.0)
**Purpose:** Complete transcript lifecycle - automatic creation, manual creation, and session documentation
**Priority:** HIGH - Prevents loss of session details and ensures knowledge retention

---

## Overview

This protocol covers both automatic and manual transcript creation:

1. **Automatic Transcripts** - Triggered by token thresholds before context compacting
2. **Manual Transcripts** - User-requested session documentation via `/transcript` command
3. **Standardized Format** - Consistent structure for all transcripts
4. **Knowledge Retention** - Preserves technical details, decisions, and troubleshooting

**Key Principles:**
- Save conversations before compression or summarization occurs
- Use consistent format for both auto and manual transcripts
- Preserve all technical details, commands, and decision-making
- Enable future reference and troubleshooting

---

## Context Window Monitoring

### Token Budget Tracking

**Total Context Window:** 200,000 tokens
**Recommended Trigger Points:**

| Token Usage | Status | Action |
|-------------|--------|--------|
| 0-100,000 | Safe | Continue normally |
| 100,001-140,000 | Monitor | Watch for natural breakpoints |
| 140,001-160,000 | Warning | **Create transcript at next logical pause** |
| 160,001-180,000 | Critical | **Create transcript immediately** |
| 180,001+ | Urgent | **Force transcript creation NOW** |

**Current token usage is shown in system warnings:**
```
<system_warning>Token usage: 117594/200000; 82406 remaining</system_warning>
```

### Calculation Guide

**Monitor remaining tokens:**
- **Safe:** 80,000+ tokens remaining
- **Warning:** 40,000-80,000 tokens remaining (≈70-80% used)
- **Critical:** 20,000-40,000 tokens remaining (≈80-90% used)
- **Urgent:** <20,000 tokens remaining (≈90%+ used)

---

## Auto-Trigger Conditions

### Condition 1: Token Threshold Reached (Primary Trigger)

**When to trigger:**
```
If (tokens_used > 140,000) OR (tokens_remaining < 60,000):
    Trigger auto-transcript at next natural pause
```

**Natural pause points:**
- Task completion
- User confirmation/approval
- Before starting new major task
- After successful deployment/push
- After error resolution

### Condition 2: Complex Session Indicators

**Trigger transcript if session includes:**
- ✅ Multiple major tasks completed (3+)
- ✅ Complex troubleshooting/debugging
- ✅ Database modifications
- ✅ Git commits/pushes
- ✅ File reorganization (10+ files)
- ✅ Protocol creation/modification
- ✅ System-wide changes
- ✅ Multi-step workflows

**Example complex sessions:**
- Script reorganization (226 scripts moved)
- WordPress deployment with debugging
- Database schema changes
- Multi-protocol implementation

### Condition 3: Session Duration

**Long-running sessions that should be transcribed:**
- Session exceeds 1.5 hours of active work
- More than 50 user messages
- More than 100 tool uses
- Spans multiple related tasks

### Condition 4: User Request

**Always honor explicit requests:**
- User types `/transcript`
- User asks to "save the session"
- User says "document what we did"
- User requests "summary of changes"

---

## Auto-Transcript Workflow

### Step 1: Detect Trigger Condition

**Monitor for triggers:**
1. Check token usage every 10-15 interactions
2. Watch for complexity indicators
3. Track session duration
4. Listen for user cues

**Detection pattern:**
```
IF tokens_used > 140,000:
    SET flag: auto_transcript_needed = TRUE
    WAIT FOR: natural_pause_point
    EXECUTE: create_auto_transcript()
```

### Step 2: Choose Optimal Moment

**Don't interrupt mid-task!**

**Good moments to create transcript:**
- ✅ Just completed a major task
- ✅ User says "ok" or confirms completion
- ✅ After successful git push
- ✅ After verification steps complete
- ✅ Before starting entirely new topic
- ✅ After resolving complex error

**Bad moments to create transcript:**
- ❌ Mid-debugging session
- ❌ During file editing
- ❌ In middle of git operations
- ❌ While user is asking questions
- ❌ During active problem-solving

### Step 3: Inform User

**Notification message:**
```
"I'm at ~70% of my context window (140,000 tokens used). I'm going to create
a comprehensive transcript of our session now to preserve all details before
any conversation compacting occurs. This will take about 30 seconds."
```

**If urgent (180,000+ tokens):**
```
"I'm at ~90% of my context window and need to create a transcript immediately
to preserve session details before conversation compacting begins."
```

### Step 4: Create Transcript

**Execute transcript creation:**
```bash
# Use same format as manual /transcript command
# Save to /home/dave/skippy/conversations/
# Filename: [topic]_session_YYYY-MM-DD.md
```

**Include all standard sections:**
1. Session Header
2. Context
3. User Requests
4. Investigation/Analysis
5. Actions Taken
6. Technical Details
7. Results
8. Deliverables
9. User Interaction
10. Session Summary

### Step 5: Confirm Completion

**After transcript created:**
```
"✅ Session transcript saved to:
/home/dave/skippy/conversations/[topic]_session_2025-10-31.md

The transcript preserves:
- All commands executed
- Every file modified
- Complete decision-making process
- Technical details and verification steps

We can continue our conversation - the full session is safely documented!"
```

---

## Transcript Naming Convention

### Auto-Generated Filename Format

**Pattern:** `[topic]_auto_transcript_YYYY-MM-DD_HHMMSS.md`

**Examples:**
- `wordpress_debugging_auto_transcript_2025-10-31_143022.md`
- `script_organization_auto_transcript_2025-10-31_165533.md`
- `database_migration_auto_transcript_2025-11-01_092145.md`

**Note:** The `_auto_transcript` marker indicates it was automatically generated rather than manually requested.

### Topic Detection

**Determine topic from session content:**

1. **Analyze user's primary requests:**
   - First major task mentioned
   - Most time spent on what activity
   - What was the main deliverable

2. **Common topic patterns:**
   - `wordpress_[specific_task]`
   - `script_[action]`
   - `database_[operation]`
   - `deployment_[target]`
   - `debugging_[system]`
   - `protocol_[name]`

3. **Multi-topic sessions:**
   - Use most significant topic
   - Or combine: `wordpress_and_database_updates`
   - Or use generic: `system_maintenance_session`

---

## Implementation Checklist

### Before Auto-Transcript

**Pre-checks:**
```
1. ✅ Token usage > 140,000 OR remaining < 60,000?
2. ✅ At natural pause point?
3. ✅ Current task completed?
4. ✅ No active operations (git, database, file edits)?
5. ✅ User available for brief notification?
```

**If all YES → Proceed with auto-transcript**

### During Auto-Transcript Creation

**Process:**
1. Notify user of transcript creation
2. Review entire conversation context
3. Extract all key information
4. Format according to transcript template
5. Save to conversations directory
6. Verify file created successfully
7. Confirm to user with file path

**Time estimate:** 30-60 seconds for comprehensive transcript

### After Auto-Transcript

**Post-creation steps:**
1. ✅ Verify file exists and is readable
2. ✅ Confirm file size is reasonable (not truncated)
3. ✅ Notify user with file path
4. ✅ Continue conversation normally
5. ✅ Reset mental count of "transcript needed" flag

---

## Transcript Content Requirements

### Mandatory Sections (Auto-Transcript)

**Must include:**
1. **Session Header** - Date, time, topic, working directory
2. **Token Usage Stats** - Current usage that triggered auto-transcript
3. **Complete Command History** - Every bash command executed
4. **File Operations** - All files created, modified, deleted
5. **User Requests** - Verbatim user messages and requests
6. **Technical Details** - Paths, configurations, git operations
7. **Results** - What was accomplished
8. **Session Summary** - Before/after state

### Optional Enhancements

**Include if available:**
- Screenshots or output samples
- Error messages and resolutions
- Decision-making rationale
- Alternative approaches considered
- Future recommendations
- Related sessions/references

### Compression Guidelines

**For very long sessions (180,000+ tokens):**
- Summarize repetitive operations (e.g., "moved 226 scripts" instead of listing each)
- Focus on unique/critical commands
- Keep all user interactions verbatim
- Preserve all file paths and technical details
- Compress verbose output, keep key results

---

## Token Usage Best Practices

### Proactive Token Management

**Throughout session:**
1. **Monitor regularly** - Check token warnings every 10-15 messages
2. **Compress early** - Summarize repetitive operations in your responses
3. **Reference efficiently** - Use file paths instead of full content when possible
4. **Plan ahead** - If complex task ahead, trigger transcript before starting

### Token-Saving Techniques

**During conversation:**
- ✅ Use `head -20` instead of reading entire large files
- ✅ Use `--short` for git status
- ✅ Reference protocols by name/path, don't repeat full content
- ✅ Summarize repetitive operations
- ✅ Use grep/find efficiently, limit results

**Avoid token waste:**
- ❌ Reading same file multiple times
- ❌ Verbose command output when summary suffices
- ❌ Repeating large code blocks
- ❌ Unnecessary file listings

---

## Integration with Other Protocols

### Works With

**This protocol integrates with:**

1. **Session Transcript Protocol** - Uses same format/structure
2. **Git Workflow Protocol** - Captures all git operations
3. **Error Logging Protocol** - Preserves error resolution steps
4. **Documentation Standards** - Follows same documentation guidelines

### Workflow Integration

```
User Request
     │
     ▼
Execute Tasks
     │
     ▼
Monitor Tokens ◄─── AUTO-TRANSCRIPT PROTOCOL ACTIVE
     │
     ├─ < 140k tokens → Continue
     │
     └─ > 140k tokens → Natural Pause?
              │
              ├─ YES → Create Auto-Transcript
              │        Continue Session
              │
              └─ NO  → Complete Current Task
                       Create Auto-Transcript
                       Continue Session
```

---

## Example Scenarios

### Scenario 1: Script Organization Session

**Token usage progression:**
- Start: 0 tokens
- After /refresh-memory: 20,000 tokens
- After finding scripts: 40,000 tokens
- After moving scripts: 80,000 tokens
- After protocol creation: 120,000 tokens
- **Trigger point reached!** → 140,000 tokens
- After git operations: 150,000 tokens

**Auto-transcript triggered at 140k:**
```
User just confirmed: "ok"
Task completed: Protocol created
Natural pause: Yes
Action: Create auto-transcript
Continue: GitHub push operations
```

### Scenario 2: WordPress Debugging Session

**Token usage progression:**
- Start: 0 tokens
- Read conversation history: 15,000 tokens
- Debug glossary issue: 45,000 tokens
- Fix policy restrictions: 75,000 tokens
- Update bibliography: 105,000 tokens
- Test mobile display: 135,000 tokens
- **Trigger point reached!** → 145,000 tokens

**Auto-transcript triggered at 145k:**
```
Task completed: All WordPress issues resolved
User verified: Local site working
Natural pause: Yes
Action: Create auto-transcript
Continue: Production deployment discussion
```

### Scenario 3: Complex Multi-Task Session

**Token usage progression:**
- Database schema changes: 60,000 tokens
- API endpoint updates: 95,000 tokens
- Frontend modifications: 130,000 tokens
- **Trigger point reached!** → 142,000 tokens

**Auto-transcript triggered at 142k:**
```
Current task: Frontend modifications 90% complete
Action: Finish current task (adds ~8k tokens)
Then: Create auto-transcript at 150k
Continue: Testing and verification
```

---

## Emergency Procedures

### Critical Threshold (180,000+ tokens)

**When >90% context used:**

1. **Immediate notification:**
   ```
   "⚠️ CRITICAL: Context window at 92% (184,000/200,000 tokens).
   Creating emergency transcript NOW to preserve session details."
   ```

2. **Skip waiting for natural pause** - Create immediately

3. **Streamlined transcript:**
   - Focus on key actions and results
   - Compress verbose output
   - Preserve all file paths and commands
   - Quick summary format acceptable

4. **After emergency transcript:**
   - Offer to continue in new session
   - Or suggest wrapping up current session
   - User chooses next step

### Context Compacting Detected

**If conversation already being compacted:**

1. **Create transcript with what's available**
2. **Note in transcript:** "Emergency transcript - some context may be compressed"
3. **Save immediately**
4. **Inform user:** "Transcript created from available context. Some early session details may be summarized."

---

## Monitoring Indicators

### Visual Cues to Watch

**System warnings show token usage:**
```xml
<system_warning>Token usage: 140567/200000; 59433 remaining</system_warning>
```

**Parse the numbers:**
- `140567` = tokens used (70% - WARNING threshold)
- `59433` = tokens remaining

**Action based on remaining tokens:**
- 80,000+ remaining = Safe, continue
- 60,000-80,000 = Monitor closely
- 40,000-60,000 = Prepare for transcript
- 20,000-40,000 = Create transcript soon
- <20,000 = Create transcript NOW

### Session Complexity Indicators

**High-complexity markers:**
- Multiple git operations
- Extensive file operations (20+ files)
- Database modifications
- System-wide searches
- Multiple protocol modifications
- Complex debugging sessions
- Multi-step deployments

**If 2+ complexity markers + >120k tokens:**
→ Plan for transcript at next pause

---

## Best Practices

### Do's

✅ **Monitor token usage** every 10-15 interactions
✅ **Choose natural pause points** for transcript creation
✅ **Inform user** before creating transcript
✅ **Preserve all technical details** in transcript
✅ **Continue session** after transcript created
✅ **Name files descriptively** with topic and timestamp
✅ **Verify file created** successfully
✅ **Use consistent format** matching manual transcripts

### Don'ts

❌ **Don't wait until critical threshold** (>180k tokens)
❌ **Don't interrupt mid-task** to create transcript
❌ **Don't skip technical details** to save space
❌ **Don't forget to notify user** of transcript creation
❌ **Don't create multiple transcripts** for same session
❌ **Don't truncate important information** even if tokens are high
❌ **Don't ignore token warnings** in system messages

---

## Success Metrics

### This Protocol is Working When:

✅ **Transcripts created before conversation compacting**
- No loss of session details
- Full command history preserved
- All technical decisions documented

✅ **Optimal timing**
- Created at natural pause points
- Not interrupting active work
- User minimally disrupted

✅ **Complete documentation**
- All files created/modified listed
- Every command captured
- User interactions preserved

✅ **Continuation possible**
- Session continues after transcript
- No context loss affects ongoing work
- User can continue seamlessly

### Key Metrics

**Target Performance:**
- 95%+ transcripts created before 160,000 tokens
- 100% created before 180,000 tokens
- <1 minute delay for transcript creation
- Zero interrupted tasks
- 100% session details preserved

---

## Quick Reference

### Token Thresholds (Quick Lookup)

| Tokens Used | % Full | Remaining | Action |
|-------------|--------|-----------|--------|
| 100,000 | 50% | 100,000 | Continue normally |
| 120,000 | 60% | 80,000 | Monitor closely |
| 140,000 | 70% | 60,000 | **TRIGGER: Plan transcript** |
| 160,000 | 80% | 40,000 | **CRITICAL: Create transcript** |
| 180,000 | 90% | 20,000 | **EMERGENCY: Transcript NOW** |

### Decision Tree (Quick Reference)

```
Tokens > 140k?
├─ NO  → Continue session
└─ YES → At natural pause?
         ├─ YES → Create auto-transcript
         │        ├─ Notify user
         │        ├─ Create transcript
         │        ├─ Verify saved
         │        └─ Continue session
         │
         └─ NO  → Complete current task
                  Then create auto-transcript
```

### Notification Templates

**Warning (140k-160k tokens):**
```
"I'm at ~70% of my context window. I'll create a comprehensive transcript
at the next natural pause to preserve all session details."
```

**Critical (160k-180k tokens):**
```
"I'm at ~80% of my context window. Creating transcript now to preserve
full session details before conversation compacting occurs."
```

**Emergency (180k+ tokens):**
```
"⚠️ Context window at ~90%. Creating emergency transcript NOW to preserve
session details."
```

---

## Protocol Maintenance

### Monthly Review

**Check these metrics:**
1. How many auto-transcripts created?
2. Average token usage at creation?
3. Any transcripts created after compacting?
4. User feedback on timing?
5. Any interrupted tasks?

### Update Triggers

**Adjust thresholds if:**
- Consistently creating too early (wasted effort)
- Consistently creating too late (context loss)
- User preferences change
- Claude model context window changes

### Version History

**v1.0.0 - 2025-10-31**
- Initial protocol creation
- 140k token trigger threshold
- Natural pause point detection
- Standard transcript format

---

## Part 2: Manual Transcript Creation

### When to Create Manual Transcripts

#### Always Create Transcript For

**Major Work Sessions**:
- ✅ Multi-hour sessions with significant accomplishments
- ✅ Complex problem-solving sessions
- ✅ System configuration or setup
- ✅ Major deployments
- ✅ Large feature implementations
- ✅ Troubleshooting complex issues

**Milestone Sessions**:
- ✅ Completing major features
- ✅ Fixing critical bugs
- ✅ System architecture changes
- ✅ Protocol implementations
- ✅ Infrastructure setup

**Learning/Documentation Sessions**:
- ✅ First-time setup of new tools
- ✅ Learning new workflows
- ✅ Exploring unfamiliar systems
- ✅ Creating documentation

#### Consider Creating Transcript For

- Sessions with valuable troubleshooting steps
- Sessions solving unusual problems
- Sessions establishing new procedures
- Sessions with important discoveries

#### Skip Transcript For

- Simple file edits
- Quick fixes (< 15 minutes)
- Routine tasks
- Questions only (no implementation)

---

### Manual Transcript Structure

#### Required Sections

**1. Session Header**
```markdown
# [Topic] Session

**Date**: YYYY-MM-DD
**Time**: HH:MM - HH:MM UTC
**Session Duration**: X hours, Y minutes
**Session Topic**: Brief description
**Working Directory**: /path/to/working/directory
**Transcript Type**: Auto-Generated / Manual / User-Requested
```

**2. Session Overview**
```markdown
### Session Overview
Brief summary of what was accomplished

### Session Status
✅ COMPLETE / ⚠️ PARTIAL / ❌ BLOCKED

### Key Metrics
- Files created/modified: X
- Commands executed: Y
- Time spent: Z hours
- Token usage (if auto): XXX,XXX / 200,000
```

**3. Context**
```markdown
## Context

### What Led to This Session
- Previous work that led here
- Related sessions
- User's initial state

### Problem Statement
- What problem needed solving
- Why it was important
- Expected outcome
```

**4. User Requests**
```markdown
## User Requests (Chronological)

### Request 1: [Title]
**User**: "exact quote of user request"
**Context**: Why user made this request
**Objectives**: What user wanted to achieve
```

**5. Investigation/Analysis**
```markdown
## Investigation/Analysis Process

### Phase 1: [Understanding the Problem]
**Files Reviewed**: List of files examined
**Commands Executed**: Diagnostic commands
**Key Discoveries**: What was learned

### Phase 2: [Planning the Solution]
**Approach Decided**: What approach was chosen
**Alternatives Considered**: Other options and why rejected
```

**6. Actions Taken**
```markdown
## Actions Taken

### Action 1: [Description]
**Objective**: What this action was meant to accomplish
**Steps**:
1. Step 1
2. Step 2
**Commands Executed**:
```bash
command here
```
**Files Modified**: List of changed files
**Result**: What happened
```

**7. Technical Details**
```markdown
## Technical Details

### File Paths
- Created: /path/to/file
- Modified: /path/to/file
- Deleted: /path/to/file

### Commands Executed
```bash
# All significant commands with context
command1
command2
```

### Configuration Changes
- What was changed
- Old value → New value
- Why changed
```

**8. Results**
```markdown
## Results

### What Was Accomplished
- Achievement 1
- Achievement 2

### Verification Steps
- How success was verified
- Tests performed
- Validation done

### Final Status
✅ Objective 1
✅ Objective 2
❌ Objective 3 (if any failed)
```

**9. Deliverables**
```markdown
## Deliverables

### Files Created
1. /path/to/file1 - Description
2. /path/to/file2 - Description

### URLs/Links
- https://example.com

### Documentation
- Where to find related docs
```

**10. Session Summary**
```markdown
## Session Summary

### Start State
- What existed before session

### End State
- What exists after session

### Success Metrics
- How success is measured
- What was achieved
```

---

### Manual Naming Convention

#### Format for Manual Transcripts
```
[topic]_session_YYYY-MM-DD.md
```

#### Topic Guidelines

**Use clear, descriptive topics**:
- ✅ `wordpress_database_migration_session_2025-10-28.md`
- ✅ `mobile_menu_fix_session_2025-10-28.md`
- ✅ `protocol_system_implementation_session_2025-10-28.md`
- ❌ `session_2025-10-28.md` (too generic)
- ❌ `work_session.md` (no date, not descriptive)

**Topic Naming Patterns**:
- Feature implementation: `[feature]_implementation_session_`
- Bug fixes: `[bug]_fix_session_` or `[area]_troubleshooting_session_`
- Setup/configuration: `[tool]_setup_session_`
- Optimization: `[area]_optimization_session_`
- Deployment: `[what]_deployment_session_`
- Review/analysis: `[area]_review_session_`

---

### Using /transcript Command

#### Command Format
```bash
/transcript
```

**What the command does**:
- Creates comprehensive session transcript
- Follows this protocol automatically
- Saves to `/home/dave/skippy/conversations/`
- Uses appropriate naming convention

#### When to Use
- At end of significant sessions
- After completing major work
- When switching contexts (preserve current work)
- Before context cutoff (though auto-transcript should trigger first)

---

### File Location

**Primary Location:**
```
/home/dave/skippy/conversations/
```

**All session transcripts save here** for centralized access.

**Organization:**
- All transcripts in one directory
- Use descriptive filenames for organization
- Use `ls -lt` to see recent sessions
- Use `grep` to search across sessions

**Rationale:**
- Easy to find all sessions
- Easy to search across sessions
- Chronological by date in filename
- No need to remember subdirectory structure

---

### Transcript Template

**Quick Start Template:**

```markdown
# [Topic] Session

**Date**: YYYY-MM-DD
**Time**: HH:MM - HH:MM UTC
**Session Duration**: X hours
**Session Topic**: Brief description
**Working Directory**: /path/to/directory
**Transcript Type**: Auto-Generated / Manual / User-Requested

---

## Session Header

### Session Overview
What was accomplished in brief

### Session Status
✅ COMPLETE

### Key Metrics
- Metric 1
- Metric 2

---

## Context

### What Led to This Session
Background and previous work

### Problem Statement
What needed to be solved

---

## User Requests

### Request 1: [Title]
**User**: "quote"
**Objectives**: What was wanted

---

## Investigation/Analysis Process

### Phase 1: [Name]
What was investigated and discovered

---

## Actions Taken

### Action 1: [Description]
**Steps**:
1. Step 1
2. Step 2

**Commands**:
```bash
commands here
```

**Result**: What happened

---

## Technical Details

### File Paths
- Created: /path/to/file

### Commands Executed
```bash
all commands
```

---

## Results

### What Was Accomplished
- List of achievements

### Verification Steps
- How verified

### Final Status
✅ Objective 1
✅ Objective 2

---

## Deliverables

### Files Created
1. File 1
2. File 2

---

## Session Summary

### Start State
What existed before

### End State
What exists after

### Success Metrics
How success measured
```

---

## Part 3: Session History Management

### Reviewing Past Sessions

**Find recent sessions**:
```bash
ls -lt /home/dave/skippy/conversations/*session*.md | head -10
ls -lt /home/dave/skippy/conversations/*transcript*.md | head -10
```

**Find sessions by topic**:
```bash
ls /home/dave/skippy/conversations/*wordpress*session*.md
ls /home/dave/skippy/conversations/*mobile*session*.md
ls /home/dave/skippy/conversations/*deployment*session*.md
```

**Find sessions by date**:
```bash
ls /home/dave/skippy/conversations/*2025-10*session*.md
ls /home/dave/skippy/conversations/*2025-10-28*session*.md
```

**Search session contents**:
```bash
grep -r "specific term" /home/dave/skippy/conversations/*session*.md
```

---

### Retention Policy

#### Keep Indefinitely

**High-Value Sessions**:
- Major feature implementations
- Complex problem solutions
- System architecture decisions
- Protocol implementations
- First-time setups
- Unique troubleshooting

#### Review Periodically

**Standard Sessions**:
- Review quarterly
- Archive if no longer relevant
- Consolidate similar sessions
- Extract patterns into protocols

#### Archive Location

**Archived Sessions**:
```
/home/dave/skippy/conversations/archive/YYYY/
```

**Archive after**:
- 1 year for routine sessions
- Never for high-value sessions
- When superseded by newer work
- When knowledge captured in protocols

---

## Part 4: Best Practices

### During Session

1. **Take Notes as You Go**
   - Note significant commands
   - Note discoveries
   - Note decisions and why

2. **Document Problems and Solutions**
   - What went wrong
   - How it was fixed
   - Why it happened

3. **Capture Context**
   - Why this work was needed
   - What led to this session
   - Related work

### Creating Transcript

1. **Be Comprehensive**
   - Include all significant steps
   - Include all commands
   - Include all decisions

2. **Be Specific**
   - Exact commands used
   - Exact file paths
   - Exact error messages

3. **Be Useful**
   - Make it easy to recreate work
   - Make it easy to understand
   - Make it searchable

### After Creating Transcript

1. **Verify Completeness**
   - All files listed
   - All commands included
   - All results documented

2. **Make Discoverable**
   - Use clear filename
   - Cross-reference in protocols if needed
   - Document patterns discovered

3. **Extract Learnings**
   - Update protocols if needed
   - Add to error logs if needed
   - Document patterns discovered

---

## Part 5: Common Session Types

### WordPress Database Session

**Typical Contents**:
- Database export/import commands
- Search-replace operations
- Verification steps
- Issues encountered and solutions
- GoDaddy-specific notes

**Key Information to Capture**:
- Table prefix used
- URLs replaced
- Backup locations
- Import success verification

---

### Deployment Session

**Typical Contents**:
- Pre-deployment checklist completion
- Files uploaded
- Database changes
- Cache clearing
- Post-deployment verification
- Issues and fixes

**Key Information to Capture**:
- What was deployed
- Where it was deployed
- Verification results
- Rollback plan (if needed)

---

### Troubleshooting Session

**Typical Contents**:
- Problem description
- Investigation steps
- Hypotheses tested
- Solution found
- Prevention measures

**Key Information to Capture**:
- Error messages (exact)
- Diagnostic commands used
- What worked, what didn't
- Root cause
- How to prevent

---

### Setup/Configuration Session

**Typical Contents**:
- What was set up
- Configuration steps
- Configuration files modified
- Verification of setup
- Next steps

**Key Information to Capture**:
- Installation commands
- Configuration settings
- File locations
- How to verify it's working

---

### Feature Implementation Session

**Typical Contents**:
- Feature requirements
- Implementation approach
- Code written
- Tests performed
- Documentation created

**Key Information to Capture**:
- Files created/modified
- How feature works
- How to use feature
- Testing results

---

## Part 6: Transcript Quality Checklist

Before considering transcript complete:

- [ ] Session header complete (date, time, topic, type)
- [ ] Context explained (what led to session)
- [ ] User requests documented (verbatim when manual)
- [ ] Investigation process documented
- [ ] All actions documented
- [ ] All commands included
- [ ] All files listed (created/modified)
- [ ] Results documented
- [ ] Deliverables listed
- [ ] Start state vs end state clear
- [ ] Success metrics documented
- [ ] Filename follows convention (auto vs manual naming)
- [ ] Saved to correct location

---

## Consolidation Notes

**This protocol consolidates:**
- `auto_transcript_protocol.md` (v1.0.0) - Token monitoring and automatic triggers
- `session_transcript_protocol.md` (v1.0.0) - Manual transcript structure and format

**Eliminated duplication:**
- Transcript structure (was in both)
- Naming conventions (was duplicated)
- File location rules (was repeated)
- Documentation requirements (was in both)

**Unique content preserved:**
- **From auto_transcript**: Token monitoring, automatic triggers, timing logic
- **From session_transcript**: Comprehensive structure, session types, template details

**Net result:**
- Complete lifecycle management (auto + manual)
- Single source of truth for transcript format
- Better organization with Part 1 (auto) and Part 2 (manual)
- Easier to maintain

---

**Status:** ✅ ACTIVE
**Priority:** HIGH
**Version:** 2.0.0
**Last Updated:** 2025-11-05
**Supersedes:** auto_transcript_protocol.md v1.0.0, session_transcript_protocol.md v1.0.0
**Integration:** Auto-loads with conversation protocols
**Trigger:** Automatic at 140,000 tokens OR 60,000 remaining, OR manual `/transcript`

**This protocol ensures session details are preserved through automatic monitoring and enables comprehensive manual documentation.**

---
