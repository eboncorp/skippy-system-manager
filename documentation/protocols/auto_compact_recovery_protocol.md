# Auto-Compact Recovery Protocol
**Version:** 1.0.0
**Last Updated:** November 10, 2025
**Purpose:** Quick recovery and context restoration after Claude Code auto-compact

---

## Overview

When Claude Code performs an auto-compact (context window reset), this protocol helps quickly restore context and resume work efficiently.

## Symptoms of Auto-Compact

- Conversation suddenly resets mid-task
- Claude seems to have "forgotten" recent work
- Token count resets to near zero
- Previous conversation context unavailable

---

## Immediate Recovery Steps

### 1. Identify Current State (30 seconds)

**Check working directory:**
```bash
pwd
ls -la
git status --short 2>/dev/null
```

**Check recent activity:**
```bash
# Last 5 commands from history
history | tail -5

# Recent file modifications
ls -lt | head -10
```

### 2. Restore Context (1-2 minutes)

**A. Use Refresh Memory Command**
```bash
/refresh-memory
```
This reads the conversation index for quick context.

**B. Check Active Sessions**
```bash
# Find most recent work session
ls -ltd /home/dave/skippy/work/*/* | head -5

# Check for README in latest session
LATEST=$(ls -td /home/dave/skippy/work/*/* | head -1)
cat "$LATEST/README.md" 2>/dev/null
```

**C. Review Recent Conversations**
```bash
# Last 3 conversation logs
ls -lt /home/dave/skippy/conversations/*.md | head -3

# Quick scan of latest
head -50 $(ls -t /home/dave/skippy/conversations/*.md | head -1)
```

### 3. Assess Current Task (1 minute)

**Check git status across key repos:**
```bash
cd /home/dave/skippy
echo "=== Skippy ===" && git status --short
echo ""
cd app-to-deploy/NexusController
echo "=== NexusController ===" && git status --short
echo ""
cd /home/dave/skippy/rundaverun/campaign
echo "=== Campaign ===" && git status --short
```

**Check for uncommitted work:**
```bash
# Find files modified in last hour
find /home/dave/skippy -name "*.py" -o -name "*.md" -o -name "*.sh" | \
  xargs ls -lt | head -10
```

### 4. Resume Work (1-2 minutes)

**Use context clues to determine what you were doing:**

1. **Recent commits:**
   ```bash
   git log --oneline -5
   ```

2. **Open work sessions:**
   ```bash
   ls -lt /home/dave/skippy/work/*/* | head -3
   ```

3. **Modified but uncommitted files:**
   ```bash
   git status --short
   ```

4. **Running processes (if any):**
   ```bash
   ps aux | grep -E "python|node|docker" | grep -v grep
   ```

---

## Context Restoration Checklist

Use this checklist to quickly restore full context:

- [ ] Run `/refresh-memory` to load conversation index
- [ ] Check `pwd` - where am I?
- [ ] Check `git status` - what's uncommitted?
- [ ] Check latest work session - what was I working on?
- [ ] Check recent conversation logs - what was discussed?
- [ ] Check git log - what was last committed?
- [ ] Check for running processes
- [ ] Identify active branch
- [ ] Review any README.md in work session directory

---

## Quick Reference Cards

### Card 1: "Where Am I?"
```bash
pwd
ls -la
git branch --show-current
git status --short
```

### Card 2: "What Was I Doing?"
```bash
# Last work session
ls -ltd /home/dave/skippy/work/*/* | head -1

# Last conversation
ls -t /home/dave/skippy/conversations/*.md | head -1

# Last commits
git log --oneline -3
```

### Card 3: "What's Pending?"
```bash
# Uncommitted changes
git status --short

# Modified files (last hour)
find . -type f -name "*.py" -o -name "*.md" | xargs ls -lt | head -10

# Work session README
cat /home/dave/skippy/work/*/*/README.md 2>/dev/null | tail -50
```

---

## Recovery by Scenario

### Scenario 1: In Middle of Repository Update

**Quick Recovery:**
```bash
# 1. Check status
cd /home/dave/skippy
git status

# 2. Check recent conversation
ls -t conversations/*eboncorp*.md | head -1 | xargs head -100

# 3. Check what was pushed
git log origin/master..HEAD --oneline

# 4. Resume from checklist in conversation
```

### Scenario 2: In Middle of Code Restructure

**Quick Recovery:**
```bash
# 1. Find work session
LATEST_SESSION=$(ls -td /home/dave/skippy/work/*/* | head -1)
echo "Latest session: $LATEST_SESSION"

# 2. Review session README
cat "$LATEST_SESSION/README.md"

# 3. Check before/after files
ls -la "$LATEST_SESSION"

# 4. Resume based on session plan
```

### Scenario 3: In Middle of WordPress Update

**Quick Recovery:**
```bash
# 1. Check work session
ls -ltd /home/dave/skippy/work/wordpress/*/* | head -1

# 2. Check if update was applied
# (depends on what was being updated - check session README)

# 3. Review latest conversation about WordPress
ls -t conversations/*wordpress*.md | head -1 | xargs head -50
```

### Scenario 4: In Middle of Documentation/Protocol Work

**Quick Recovery:**
```bash
# 1. Check modified files
git status --short

# 2. Check latest conversation
ls -t conversations/*.md | head -1 | xargs tail -100

# 3. Check protocols directory
ls -lt documentation/protocols/*.md | head -5

# 4. Resume documentation task
```

---

## Communication Template

After auto-compact, provide user with this summary:

```markdown
## Auto-Compact Recovery

I've detected an auto-compact occurred. Here's what I found:

**Current Location:** [pwd output]

**Recent Activity:**
- Last work session: [path]
- Last conversation: [file]
- Last commit: [commit message]

**Pending Work:**
- Uncommitted changes: [list]
- Current branch: [branch name]

**Context Restored From:**
- Conversation index: ✅
- Work session README: ✅
- Git history: ✅

**Ready to Resume:**
[Brief summary of what we were working on]

Would you like me to:
1. Continue with [task]
2. Provide more detail on [aspect]
3. Start fresh with a new task
```

---

## Prevention Strategies

### 1. Regular Context Anchors

Every 30-60 minutes, create an anchor:
```bash
# Save current state
git add -A
git commit -m "WIP: [brief description]"

# Update work session README
cat >> "$SESSION_DIR/README.md" << EOF

## Progress at $(date)
- Completed: [list]
- In progress: [current task]
- Next: [next task]
EOF
```

### 2. Use Todo Lists

Keep active todo list updated:
```bash
# Claude automatically maintains todo list
# User can check: .claude/todos/
```

### 3. Commit Frequently

Even work-in-progress commits help with recovery:
```bash
git add -A
git commit -m "WIP: checkpoint before [next step]"
```

### 4. Document in Work Sessions

Always create and update work session README:
```bash
echo "## Current Status: [description]" >> "$SESSION_DIR/README.md"
```

---

## Tools Available

### Built-in Recovery Tools

1. **`/refresh-memory`** - Read conversation index
2. **`/refresh-memory --rebuild`** - Rebuild full index
3. **`git status`** - Check uncommitted work
4. **`git log`** - Review recent commits
5. **`history`** - Check recent commands

### Custom Recovery Scripts

```bash
# Create quick recovery script
cat > /home/dave/skippy/scripts/recovery/quick_context.sh << 'EOF'
#!/bin/bash
echo "=== QUICK CONTEXT RECOVERY ==="
echo ""
echo "Location: $(pwd)"
echo "Branch: $(git branch --show-current 2>/dev/null || echo 'Not a git repo')"
echo ""
echo "Recent commits:"
git log --oneline -5 2>/dev/null || echo "No git history"
echo ""
echo "Uncommitted changes:"
git status --short 2>/dev/null || echo "No git repo"
echo ""
echo "Latest work session:"
ls -ltd /home/dave/skippy/work/*/* | head -1
echo ""
echo "Latest conversation:"
ls -t /home/dave/skippy/conversations/*.md | head -1
EOF

chmod +x /home/dave/skippy/scripts/recovery/quick_context.sh
```

---

## Best Practices

### During Work Session

1. ✅ Create work session directory at start
2. ✅ Save before/after states
3. ✅ Write README with progress notes
4. ✅ Commit frequently (even WIP)
5. ✅ Use descriptive commit messages

### Documentation Habits

1. ✅ Update work session README every major milestone
2. ✅ Use conversation logs (auto-generated)
3. ✅ Create summary at end of major tasks
4. ✅ Tag important points in work

### Communication

1. ✅ Tell user about auto-compact when detected
2. ✅ Provide summary of recovered context
3. ✅ Confirm before resuming work
4. ✅ Ask if user wants more detail

---

## Recovery Time Estimates

| Scenario | Context Loss | Recovery Time | Success Rate |
|----------|--------------|---------------|--------------|
| Simple task (1 repo) | Low | 1-2 minutes | 95% |
| Multi-repo update | Medium | 3-5 minutes | 90% |
| Complex restructure | High | 5-10 minutes | 85% |
| Documentation work | Low | 1-2 minutes | 98% |

**Factors affecting recovery:**
- Quality of work session documentation
- Frequency of commits
- Completeness of conversation logs
- Complexity of task

---

## Troubleshooting

### Problem: Can't Find Recent Work

**Solution:**
```bash
# Search for recent modifications
find /home/dave/skippy -type f -mmin -60 -name "*.py" -o -name "*.md"

# Check all work sessions today
find /home/dave/skippy/work -type d -name "$(date +%Y%m%d)*"
```

### Problem: Git State Confusing

**Solution:**
```bash
# Reset to clean state if needed
git stash  # Save changes
git status  # Check clean

# Or see what would be lost
git stash show -p
```

### Problem: Don't Remember What User Asked For

**Solution:**
```bash
# Check latest conversation file
LATEST_CONV=$(ls -t /home/dave/skippy/conversations/*.md | head -1)
grep -A 5 "^user:" "$LATEST_CONV" | tail -20
```

---

## Success Criteria

Recovery is successful when:

- [ ] Current location identified
- [ ] Active task understood
- [ ] Uncommitted work accounted for
- [ ] Recent context restored
- [ ] Ready to resume without confusion
- [ ] User informed of status

---

## Related Protocols

- **session_start_protocol.md** - Starting new sessions properly
- **work_session_documentation_protocol.md** - Documenting work
- **context_preservation_protocol.md** - Maintaining context
- **conversation_cleanup_protocol.md** - Managing conversation history

---

## Version History

- **1.0.0** (2025-11-10) - Initial protocol creation
  - Core recovery steps
  - Scenario-specific guidance
  - Prevention strategies
  - Quick reference cards

---

## Notes

- Auto-compact is normal Claude Code behavior
- Good documentation practices minimize recovery time
- Regular commits are your best recovery tool
- Work session directories preserve context across compacts

**Remember:** The better your documentation habits during work, the faster your recovery after auto-compact!
