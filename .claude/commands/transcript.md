---
description: Create comprehensive session transcript and save to Skippy conversations
---

Create a comprehensive transcript of our conversation session and save it to /home/dave/skippy/conversations/

The transcript should include:

## Structure:
1. **Session Header**
   - Date and time
   - Session topic/focus
   - Working directory
   - Token usage (if available from budget info)

2. **Context**
   - What led to this session
   - Previous work referenced
   - User's initial state/problem

3. **User Request**
   - Original request verbatim
   - Task objectives
   - Expected deliverables

4. **Investigation/Analysis Process**
   - Steps taken to understand the problem
   - Files searched/read
   - Commands executed
   - Discoveries made

5. **Actions Taken**
   - Each action with details
   - Technical commands executed
   - Database changes (if applicable)
   - Files created/modified

6. **Technical Details**
   - Database operations
   - File paths
   - Command syntax
   - Configuration changes

7. **Results**
   - What was accomplished
   - Verification steps
   - Final status

8. **Deliverables**
   - Files created
   - URLs/links
   - Documentation

9. **User Interaction**
   - Questions asked
   - Clarifications received
   - Follow-up requests

10. **Session Summary**
    - Start state
    - End state
    - Success metrics

## Auto-Compact Recovery Section (CRITICAL)

**Include this section to enable seamless continuation after auto-compacting:**

11. **Continuation Context** (for resuming after auto-compact)
    - **Primary Request:** [What the user originally asked for]
    - **Current Progress:** [What has been completed]
    - **Pending Tasks:** [What still needs to be done - check todo list]
    - **Critical Files:**
      - Files modified: [list with full paths]
      - Files read: [important ones for context]
      - Session directories: [any SESSION_DIR paths created]
    - **Key Technical Context:**
      - Important variables/values discovered
      - Configuration state
      - Any errors encountered and their resolution
    - **Next Steps:** [Explicit list of what to do next]
    - **User Preferences Observed:** [Any specific ways the user likes things done]

## Filename Format:
`[topic]_session_YYYY-MM-DD_HHMMSS.md`

Examples:
- `budget_publishing_session_2025-10-13_143022.md`
- `design_implementation_session_2025-10-13_091545.md`
- `database_fix_session_2025-10-13_162301.md`
- `auto_compact_recovery_session_2025-11-17_131500.md`

## Save Location:
`/home/dave/skippy/conversations/`

## Auto-Update Index (REQUIRED)

After saving the transcript, **automatically update INDEX.md**:

1. Add new entry at top of "### December 2025" (or current month) section
2. Format:
```markdown
- **{filename}** [{Mon DD}] ⭐ NEW
  - Tags: `{tag1}`, `{tag2}`, `{tag3}`
  - Summary: {one-line summary of session}
  - Status: {Completed/In Progress/Pending}
```
3. Increment "Total Conversations" count in header
4. Update "Last Updated" date to today
5. Bump "Index Version" minor number (e.g., 1.7 → 1.8)

**Example entry:**
```markdown
- **wordpress_fixes_session_2025-12-25_143000.md** [Dec 25] ⭐ NEW
  - Tags: `wordpress`, `bugfix`, `production`
  - Summary: Fixed homepage ROI figure and removed broken social icons
  - Status: Completed
```

## Additional Instructions:

1. **For Auto-Compact Preparation:**
   - If context budget is running low (check the budget info), proactively create transcript
   - Emphasize the "Continuation Context" section
   - Make it detailed enough that a new session can pick up exactly where this left off

2. **Check for Recent Compactions:**
   ```bash
   ls -lt /home/dave/skippy/work/compactions/ | head -5
   ```
   If recent compaction saves exist, reference them in the transcript.

3. **Include Todo List State:**
   If a todo list was active, document all items and their status.

4. **Cross-Reference Skills:**
   List which Agent Skills were relevant to this session (from ~/.claude/skills/)

Make the transcript comprehensive, technical, and useful for both future reference AND seamless continuation after auto-compacting.
