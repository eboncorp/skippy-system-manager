# Context Preservation Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

Work often spans multiple sessions. This protocol ensures context is preserved between sessions and long tasks are trackable.

## Purpose

- Enable multi-session work continuity
- Preserve progress on long tasks
- Allow sessions to pick up where previous left off
- Maintain work history

---

## For Long Tasks

### During Work
```
Claude automatically:
- Uses TodoWrite to track progress
- Saves intermediate results to files
- Creates timestamped work directories
- Documents each major step
```

### At Session End
```
Claude creates:
- Continuation summary in conversations/
- Final TodoWrite status
- Work files in skippy/work/
- Clear next steps
```

### Next Session
```
User says: "Continue from last session on [topic]"
Claude:
- Searches for related conversation files
- Reads the summary
- Loads TodoWrite state
- Picks up where left off
```

---

## For Multi-Day Projects

### Directory Structure
```
/home/dave/skippy/work/project/YYYYMMDD_HHMMSS_description/
- Dated directories preserve chronological work
- Each session gets own directory
- README.md documents session's work
```

### Referencing Previous Work
```
User: "Like we did on Nov 5th"
Claude: [Searches for 20251105_* directories and conversations]

User: "Continue the WordPress optimization"
Claude: [Searches conversations for "wordpress_optimization_*"]
```

---

## Examples

### Example 1: Multi-Session WordPress Optimization

**Session 1 (Monday):**
```
Work: Optimized database queries
Saved to: skippy/work/wordpress/rundaverun/20251104_140000_db_optimization/
Conversation: wordpress_optimization_2025-11-04.md
TodoWrite:
  ✅ Analyze slow queries
  ✅ Add indexes
  ⏳ Implement caching (in progress)
  ⏸️ Test performance (pending)
```

**Session 2 (Tuesday):**
```
User: "Continue the WordPress optimization from yesterday"

Claude:
- Found: wordpress_optimization_2025-11-04.md
- Last status: Caching in progress, testing pending
- Continuing: Implement caching strategy...
```

### Example 2: Long File Organization Task

**During Session:**
```
Processing 10,000 files...

Progress tracking:
- Scanned: 2,500 / 10,000 (25%)
- Organized: 2,000 / 10,000 (20%)
- Errors: 12

Saved to: skippy/work/general/file_org/20251106_*/progress.txt
```

**If Session Interrupted:**
```
Next session:
User: "Continue organizing files"
Claude: [Reads progress.txt, resumes from file 2,501]
```

---

## Conversation File Search

### Finding Previous Work
```bash
# By date
ls ~/skippy/conversations/*2025-11-05*

# By topic
grep -l "wordpress optimization" ~/skippy/conversations/*.md

# Recent work
ls -lt ~/skippy/conversations/ | head -10

# By project
ls ~/skippy/conversations/rundaverun_*
```

---

## TodoWrite for Context

### Long Task Example
```json
[
  {"content": "Research database optimization", "status": "completed"},
  {"content": "Add indexes to slow queries", "status": "completed"},
  {"content": "Implement query caching", "status": "in_progress"},
  {"content": "Test performance improvements", "status": "pending"},
  {"content": "Document changes", "status": "pending"}
]
```

Next session picks up at "Implement query caching"

---

## Best Practices

### DO:
✅ Use dated work directories
✅ Create continuation summaries
✅ Save intermediate progress
✅ Use TodoWrite for multi-step tasks
✅ Document "next steps" clearly

### DON'T:
❌ Rely on Claude remembering context
❌ Skip creating summaries
❌ Use /tmp/ for multi-session work
❌ Forget to document current progress

---

## Quick Reference

**Starting Continuation:**
```
"Continue from yesterday"
"Continue the [topic] work"
"Pick up where we left off on [project]"
"What were we working on last session?"
```

**Claude Will:**
- Search conversation files
- Read last session summary
- Check work directories
- Load TodoWrite state
- Resume work

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
