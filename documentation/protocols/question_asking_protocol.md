# Question Asking Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

Balance between asking for clarification vs proceeding autonomously. This protocol defines when Claude should ask vs just do it.

## Purpose

- Minimize unnecessary questions
- Ask when genuinely ambiguous
- Don't block on trivial decisions
- Maintain appropriate autonomy level

---

## Ask When

### Multiple Valid Approaches
```
Example: "Should I use utilities or skippy-tools for this?"
→ Ask which approach user prefers
```

### Risk of Data Loss or Breaking Changes
```
Example: About to delete 1000 files
→ Ask for confirmation
```

### Unclear Requirements
```
Example: "Update the website" (which page? what change?)
→ Ask for specifics
```

### Permission Needed
```
Example: About to push to GitHub
→ Ask if ready to push (unless told "just do it")
```

### Architecture Decisions
```
Example: "Should this be a new plugin or modify existing?"
→ Ask for architectural preference
```

---

## Just Do It When

### Following Established Protocols
```
Example: Saving to skippy/conversations
→ Don't ask, just follow protocol
```

### Using Existing Scripts
```
Example: Running pre-deployment validator
→ Don't ask, just run it
```

### Clear Single Path Forward
```
Example: "Find duplicates in Downloads"
→ Don't ask, use utilities find-duplicates
```

### Safe Operations (Dry-Run, Read-Only)
```
Example: Running health check
→ Don't ask, just run it
```

### Obvious Fixes
```
Example: File not executable, needs chmod
→ Don't ask, just fix it
```

---

## Question Types

### Type 1: Clarifying Questions (Always Ask)
```
User: "Fix the website"
Claude: "Which website and what needs fixing?"

User: "Update that page"
Claude: "Which page specifically?"
```

### Type 2: Approach Questions (Ask if Ambiguous)
```
User: "Find duplicates"
Claude proceeds with utilities (established default)

User: "Organize my files"
Claude: "Which directory? Or search all of home directory?"
```

### Type 3: Permission Questions (Situational)
```
Context: First time deploying
Claude: "Ready to push to GitHub?"

Context: Routine deployment, user said "deploy"
Claude: [Just does it, user already gave permission]
```

### Type 4: Preference Questions (Avoid Unless Important)
```
Bad: "Should I use printf or echo?"
Good: [Just pick one, they're equivalent]

Good: "Should I create new database or modify existing?"
[This matters, ask]
```

---

## User Autonomy Settings

### More Cautious Mode
```
User: "Ask before pushing to GitHub"
User: "Check with me before major changes"
User: "Show me changes before applying"

Claude will ask more questions
```

### More Autonomous Mode
```
User: "Just do it, don't ask"
User: "Proceed with deployment"
User: "Handle it automatically"

Claude will ask fewer questions
```

### Default Mode
```
Balance:
- Ask for ambiguities
- Ask for risky operations
- Don't ask for routine operations
- Don't ask for trivial decisions
```

---

## Examples

### Example 1: Good - Ask (Ambiguous)

**User:** "Update the budget page"

**Claude:**
```
I'll update the budget page. A few clarifications:
1. Which numbers need updating?
2. Do you have the source document?
3. Should I run pre-deployment validator first?
```

**Why:** Multiple pieces of information needed

### Example 2: Good - Don't Ask (Clear)

**User:** "Find duplicates in Downloads"

**Claude:**
```
I'll use utilities to find duplicates in ~/Downloads.

utilities find-duplicates ~/Downloads

[Shows results]
```

**Why:** Clear request, obvious tool, safe operation

### Example 3: Good - Ask (Risky)

**User:** "Clean up old files"

**Claude:**
```
I can clean up old files. Before I start:
1. Which directory?
2. How old? (older than 30 days, 90 days, etc.)
3. Move to trash or permanently delete?
4. Any file types to preserve?
```

**Why:** Destructive operation, needs specifics

### Example 4: Bad - Asking Too Much

**User:** "Check git status"

**Bad Claude:**
```
Should I check git status for:
1. Current repository only?
2. All repositories?
3. Show branch info?
4. Show remotes?
```

**Good Claude:**
```
git status
[Shows output]
```

**Why:** Simple request, don't overthink it

### Example 5: Good - Confirm Risk

**User:** "Deploy to production"

**Claude:**
```
Ready to deploy to production. This will:
- Run pre-deployment validator
- Upload to GoDaddy
- Run post-deployment verification

Proceed? (yes/no)
```

**Why:** Production deployment is high-risk, confirm intent

---

## Question Format

### Good Questions (Specific)
```
✅ "Which page? (home, about, budget, contact)"
✅ "Delete permanently or move to trash?"
✅ "Should I push to GitHub now or wait for your review?"
```

### Bad Questions (Vague)
```
❌ "What should I do?"
❌ "Is this okay?"
❌ "How do you want to proceed?"
```

### Good Questions (With Context)
```
✅ "File X is 5MB. Include in git commit or add to .gitignore?"
✅ "Found 20 duplicates totaling 2GB. Show list now or save to file?"
```

---

## Exception Cases

### When User is Learning
```
If user is learning:
→ Explain more
→ Show what you're doing
→ Ask teaching questions

Example: "I'll use utilities for this because..."
```

### When Stakes Are High
```
Campaign website, production database:
→ Ask more questions
→ Verify intentions
→ Confirm before executing
```

### When User is Busy
```
If user said "handle it":
→ Ask fewer questions
→ Use best judgment
→ Document decisions
```

---

## Best Practices

### DO:
✅ Ask when genuinely ambiguous
✅ Provide context with questions
✅ Offer specific options
✅ Know when to just proceed

### DON'T:
❌ Ask trivial questions
❌ Ask for permission on routine operations
❌ Ask multiple rounds of questions (batch them)
❌ Ask when answer is obvious from context

---

## Quick Reference

**Ask:**
- Ambiguous requirements
- Risky operations
- Architecture decisions
- User preference matters

**Don't Ask:**
- Routine operations
- Following protocols
- Obvious fixes
- Safe/read-only operations

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
