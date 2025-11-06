# Conversation Cleanup Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

184+ conversation files in skippy/conversations/ need organization. This protocol defines cleanup and archival procedures.

## Purpose

- Maintain findable conversation history
- Prevent clutter
- Enable quick searches
- Preserve important work

---

## Directory Structure

```
skippy/conversations/
├── active/                    # Current work (< 30 days)
├── archived/                  # Completed projects
│   ├── 2025-10/
│   ├── 2025-11/
│   └── INDEX.md              # Archive index
├── rundaverun/               # Campaign-specific (permanent)
├── utilities/                # Utilities project (permanent)
├── wordpress/                # WordPress work (permanent)
└── INDEX.md                  # Master index
```

---

## Retention Policy

**Active (< 30 days):**
- Keep in root conversations/ or active/
- Immediately accessible

**Archived (30-365 days):**
- Move to archived/YYYY-MM/
- Compressed monthly
- Searchable via index

**Permanent:**
- Project-specific subdirectories
- Never delete
- Keep indefinitely

---

## Monthly Cleanup Procedure

### Step 1: Identify Old Files
```bash
find ~/skippy/conversations -name "*.md" -mtime +30 -not -path "*/archived/*"
```

### Step 2: Review for Importance
```bash
# Keep if:
- Major project work
- Reference documentation
- Protocol definitions
- Deployment records

# Archive if:
- Routine maintenance logs
- Temporary investigations
- Completed one-off tasks
```

### Step 3: Move to Archives
```bash
MONTH=$(date -d "30 days ago" +%Y-%m)
mkdir -p ~/skippy/conversations/archived/$MONTH
mv [old-files] ~/skippy/conversations/archived/$MONTH/
```

### Step 4: Update Index
Create INDEX.md in archive directory listing all files with brief descriptions.

---

## Search Strategy

**Find Recent Work:**
```bash
ls -lt ~/skippy/conversations/ | head -20
```

**Find by Topic:**
```bash
grep -l "wordpress" ~/skippy/conversations/*.md
grep -l "budget" ~/skippy/conversations/rundaverun_*.md
```

**Find by Date:**
```bash
ls ~/skippy/conversations/*2025-11-06*
find ~/skippy/conversations/archived/2025-10/ -name "*.md"
```

---

## Best Practices

### DO:
✅ Archive monthly
✅ Create index files
✅ Use descriptive filenames
✅ Keep permanent project files separate

### DON'T:
❌ Delete without review
❌ Archive active projects
❌ Skip creating indexes
❌ Let files accumulate over 90 days

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
