# Session Start Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

Every Claude Code session should start with clear intent and context. This protocol ensures efficient session starts with proper context loading and tool awareness.

## Purpose

- Minimize time spent clarifying requirements
- Ensure Claude knows which tools/repos to use
- Load relevant context from previous sessions
- Set clear expectations for the work

---

## Guidelines

### User: Starting a New Session

**Be Specific:**
- State your goal clearly
- Mention the project/repository
- Provide relevant context

**Bad Examples:**
- ❌ "Can you help me with the website?"
- ❌ "I need to clean up some stuff"
- ❌ "Fix the thing we talked about"

**Good Examples:**
- ✅ "I need to update the campaign budget page to fix the transportation numbers"
- ✅ "Find all duplicate files in my Documents folder"
- ✅ "Deploy the rundaverun website to GoDaddy"
- ✅ "Continue from yesterday's work on WordPress optimization"

### Claude: Session Start Actions

**Automatically:**
1. Check for related conversation files in `/home/dave/skippy/conversations/`
2. Check if relevant scripts exist in skippy, skippy-tools, or utilities
3. Check for recent work files in `/home/dave/skippy/work/`
4. Propose using existing tools vs creating new ones
5. Clarify ambiguities before starting work

**Context Questions to Ask:**
- "Is this for rundaverun campaign, skippy system, or general use?"
- "Should I use existing scripts or write new code?"
- "Do you want me to review before pushing to GitHub?"

---

## Procedure

### Step 1: User States Goal
```
Format: "I need to [ACTION] [TARGET] for [PROJECT]"

Examples:
- "I need to update the About page for rundaverun campaign"
- "I need to find duplicate files in ~/Downloads"
- "I need to check for updates in all repos"
```

### Step 2: User Provides Context (Optional)
```
Additional context:
- "This is urgent for tomorrow's launch"
- "This is continuing from yesterday"
- "Use the existing deployment scripts"
- "Don't push to production yet"
```

### Step 3: Claude Confirms Understanding
```
Claude response format:
"I'll [ACTION] [TARGET] for [PROJECT] using [TOOLS/APPROACH].
[Any clarifications needed?]
[Starting work...]"
```

### Step 4: Claude Loads Context
```
Automatic checks:
- Search conversations for related work
- Check for existing scripts/tools
- Check work files from previous sessions
- Verify repository status if needed
```

---

## Session Start Templates

### Template 1: Campaign Website Work
```
User: "I need to [update/fix/add] [specific page/feature] on rundaverun website"

Claude checks:
- Recent campaign work in conversations/
- Deployment scripts in ~/rundaverun/campaign/skippy-scripts/
- Work files in ~/skippy/work/wordpress/rundaverun/
- Current website status
```

### Template 2: File Management
```
User: "I need to [organize/clean/find] files in [directory]"

Claude checks:
- utilities package: find-duplicates, organize
- skippy-tools: duplicate_cleaner, docker_cleanup
- Previous file operations in conversations/
```

### Template 3: System Maintenance
```
User: "Run [daily/weekly/monthly] maintenance"

Claude checks:
- Maintenance scripts in skippy/scripts/
- Health check scripts
- Previous maintenance logs
```

### Template 4: Repository Updates
```
User: "Check for updates in [repo/all repos]"

Claude checks:
- ~/skippy/ (skippy-system-manager)
- ~/rundaverun/ (rundaverun-website)
- ~/utilities/ (utilities)
- Git fetch and compare
```

### Template 5: Continue Previous Work
```
User: "Continue from yesterday/last session"

Claude checks:
- Most recent conversation files
- Most recent work directories
- Git status of relevant repos
- TodoWrite list from previous session
```

---

## Examples

### Example 1: Clear Start - Campaign Update

**User:**
```
I need to update the budget page on rundaverun website.
The public safety budget should be $125M, not $120M.
```

**Claude:**
```
I'll update the budget page for rundaverun campaign.

Plan:
1. Read current budget page content
2. Update public safety figure: $120M → $125M
3. Run pre-deployment validator
4. Show you changes for review
5. Deploy if approved

Starting work...
```

### Example 2: Clear Start - File Cleanup

**User:**
```
Find duplicate files in my Downloads folder and show me what's taking up space.
```

**Claude:**
```
I'll use the utilities package to find duplicates in ~/Downloads.

Using: utilities find-duplicates ~/Downloads

This will:
- Scan all files in Downloads
- Calculate SHA-256 hashes
- Show duplicate groups by size
- Let you choose which to delete

Starting scan...
```

### Example 3: Vague Start - Needs Clarification

**User:**
```
Can you help me with the website?
```

**Claude:**
```
I'd be happy to help! A few questions:

1. Which website? (rundaverun campaign, or another?)
2. What needs to be done? (update content, fix bug, deploy, check health?)
3. Is this urgent or routine maintenance?

This helps me use the right tools and approach.
```

### Example 4: Continue Previous Work

**User:**
```
Continue from yesterday's WordPress optimization work.
```

**Claude:**
```
I'll continue the WordPress optimization from yesterday.

Looking at recent work:
- Last session: WordPress performance improvements
- Work files: ~/skippy/work/wordpress/rundaverun/20251105_*
- Conversation: wordpress_optimization_2025-11-05.md

Picking up where we left off:
- Step 3: Implement caching strategy (completed)
- Step 4: Optimize database queries (in progress)
- Step 5: Test performance improvements (pending)

Continuing with Step 4...
```

---

## Session Start Checklist

**User Checklist:**
- [ ] Stated clear goal/objective
- [ ] Mentioned relevant project (rundaverun, skippy, general)
- [ ] Provided any special constraints (urgent, don't push, review first)
- [ ] Referenced previous work if continuing

**Claude Checklist:**
- [ ] Confirmed understanding of goal
- [ ] Checked for existing tools/scripts
- [ ] Loaded relevant context from previous sessions
- [ ] Identified which repository/project
- [ ] Clarified any ambiguities
- [ ] Proposed approach using existing tools when possible

---

## Common Session Start Patterns

### Pattern: Quick Task
```
User: "[Do simple task]"
Claude: "I'll [task] using [tool]. Starting now..."
[Executes immediately]
```

### Pattern: Complex Task
```
User: "[Do complex task]"
Claude: "I'll [task] with these steps:
1. [Step 1]
2. [Step 2]
3. [Step 3]
Is this approach correct?"
[Waits for confirmation]
```

### Pattern: Risky Task
```
User: "[Do risky task]"
Claude: "This will [describe risk]. I'll:
1. Create backup first
2. Use dry-run mode
3. Show you changes
4. Ask before applying
Proceeding..."
```

---

## Time Savings

**Good Session Start:**
- Clear goal → Claude starts immediately
- Proper context → Right tools used
- No back-and-forth → Work begins
- **Time to start work: ~30 seconds**

**Poor Session Start:**
- Vague goal → 3-5 clarification questions
- No context → Wrong tools chosen, restart
- Ambiguity → Multiple false starts
- **Time to start work: 5-10 minutes**

---

## Integration with Other Protocols

**Related Protocols:**
- [Tool Selection Protocol](tool_selection_protocol.md) - How to choose which tool
- [Context Preservation Protocol](context_preservation_protocol.md) - Multi-session work
- [Work Session Documentation Protocol](work_session_documentation_protocol.md) - What gets saved

**Tools Used:**
- Conversation files in `/home/dave/skippy/conversations/`
- Work files in `/home/dave/skippy/work/`
- TodoWrite for task tracking

---

## Quick Reference

### Starting Commands (Copy/Paste Ready)

**Campaign Work:**
```
I need to update [page] on rundaverun website
I need to deploy rundaverun to GoDaddy
I need to check rundaverun website health
```

**File Management:**
```
Find duplicates in ~/[directory]
Organize files in ~/[directory]
Clean up [directory]
```

**Repository Management:**
```
Check for updates in all repos
Update [repo name]
Show git status for all repos
```

**System Maintenance:**
```
Run daily health check
Run weekly maintenance
Clean up Docker
```

**Continue Work:**
```
Continue from yesterday
Continue the [project] work
Pick up where we left off on [topic]
```

---

## Best Practices

### DO:
✅ Be specific about what you want
✅ Mention the project/repository
✅ Provide relevant context upfront
✅ Reference previous work when continuing
✅ State constraints (don't push, review first, urgent)

### DON'T:
❌ Start with vague requests
❌ Assume Claude remembers everything
❌ Skip mentioning the project
❌ Forget to mention if it's continuing previous work
❌ Leave out critical context

---

## Version History

**1.0.0 (2025-11-06)**
- Initial protocol creation
- Defined session start patterns
- Added templates and examples
- Integration with existing work files protocol

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
