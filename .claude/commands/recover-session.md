---
description: Recover context after auto-compacting from saved state
---

Check for recent auto-compaction events and help recover session context.

## Automatic Recovery Process:

1. **Check for recent compactions:**
   ```bash
   ls -lt /home/dave/skippy/work/compactions/ | head -10
   ```

2. **Read the most recent recovery information:**
   If compaction saves exist, read:
   - `RESUME_INSTRUCTIONS.md` - How to continue
   - `session_summary.md` - What was happening
   - `session_state.json` - Raw session data (if needed)

3. **Restore context:**
   - Identify what work was in progress
   - Check any pending tasks or todos
   - Review critical file paths and technical details
   - Understand the user's original request

4. **Report findings:**
   Provide a clear summary:
   - When the last compaction occurred
   - What was being worked on
   - What tasks were pending
   - Recommended next steps

5. **Resume work:**
   Ask the user if the recovered context is correct before proceeding.

## If No Recent Compactions Found:

Check alternative sources:
- Recent conversation transcripts: `ls -lt /home/dave/skippy/conversations/*.md | head -10`
- Recent work directories: `ls -lt /home/dave/skippy/work/ | head -10`
- Git history: `git log --oneline -10`

## Output Format:

```markdown
# Session Recovery Report

**Last Compaction:** [timestamp or "None found"]
**Recovery Files:** [list of available files]

## Previous Session Context
- **Original Task:** [what was being done]
- **Progress:** [what was completed]
- **Pending:** [what still needs to be done]

## Recommended Actions
1. [Next step]
2. [Following step]
...

## Verification
Please confirm this matches your recollection before I continue.
```
