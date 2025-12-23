Refresh context from conversation index.

**Index Location:** `/home/dave/skippy/conversations/INDEX.md`

---

## Execution Steps

### Step 1: Read Index and Check Staleness
```bash
# Read the index
cat /home/dave/skippy/conversations/INDEX.md

# Check index date vs today
INDEX_DATE=$(grep "Last Updated:" /home/dave/skippy/conversations/INDEX.md | sed 's/.*: //')
```

**Staleness Check:**
- Extract "Last Updated:" date from INDEX.md
- Compare to today's date
- If >7 days old: **WARN USER** that index is stale and suggest `--rebuild`
- Count conversations added since last index: `find /home/dave/skippy/conversations -name "*.md" -newer INDEX.md | wc -l`

### Step 2: Structured Output (REQUIRED FORMAT)

Always present results in this structure:

```
## Context Refreshed from Conversation Index

**Index Status:** [Fresh/Stale (X days old)]
**New Conversations Since Index:** [count]
**Total Indexed:** [count]

### Recent Activity (Last 14 Days)
[List recent sessions with dates and tags]

### Active Projects
| Project | Status | Last Activity |
|---------|--------|---------------|
[Table of active projects]

### Critical Reference Files
[List authoritative/important files]

### Pending/Incomplete Work
[Any sessions marked incomplete or with next steps]
```

---

## Modes

### Quick Mode (Default)
1. Read INDEX.md
2. Check staleness (warn if >7 days)
3. Count new conversations since last index
4. Output structured summary per format above

### Full Rebuild (--rebuild)
1. Create backup: `cp INDEX.md INDEX.md.backup.$(date +%Y%m%d)`
2. Scan all conversations: `ls -lt /home/dave/skippy/conversations/*.md`
3. For each file, extract:
   - Filename and date
   - Tags (look for `Tags:` line or `#tags` in content)
   - Summary (first paragraph or `Summary:` line)
   - Status (completed/pending/in-progress)
4. Group by month, then by project
5. Regenerate INDEX.md with:
   - Updated "Last Updated:" timestamp
   - Accurate file count
   - Fresh summaries
6. Report: "Rebuilt index with X conversations"

### Incremental Update (--update)
1. Find files newer than INDEX.md: `find ... -newer INDEX.md`
2. Extract metadata from only new files
3. Append to appropriate sections in INDEX.md
4. Update "Last Updated:" and file count
5. Report: "Added X new conversations to index"

### Search Mode (--search TERM)
1. Search conversations: `grep -l "TERM" /home/dave/skippy/conversations/*.md`
2. For each match, show:
   - Filename
   - Date
   - Context snippet (2-3 lines around match)
3. Report: "Found X conversations matching 'TERM'"

### Recent Only (--recent [DAYS])
1. Default DAYS=30 if not specified
2. Find files modified in last N days: `find ... -mtime -N`
3. Show only those in structured output
4. Report: "Showing X conversations from last N days"

### Statistics (--stats)
Show:
- Total conversations
- Conversations by month
- Most common tags
- Largest files
- Projects breakdown

---

## Usage Examples

```
/refresh-memory              # Quick scan with staleness check
/refresh-memory --rebuild    # Full index regeneration
/refresh-memory --update     # Add only new conversations
/refresh-memory --search wordpress  # Find WordPress-related sessions
/refresh-memory --recent 14  # Last 2 weeks only
/refresh-memory --stats      # Show statistics
```

---

## Important Notes

- Always warn if index is stale (>7 days)
- Always show count of new conversations since last index
- Backup index before rebuild
- Use structured output format for consistency
