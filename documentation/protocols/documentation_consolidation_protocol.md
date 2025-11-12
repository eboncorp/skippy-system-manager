# Documentation Consolidation Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

Multiple README files, quick start guides, and documentation files cause confusion. This protocol establishes "one source of truth" principle.

## Purpose

- Eliminate duplicate documentation
- Create clear documentation hierarchy
- Make information findable
- Reduce maintenance burden

---

## One Source of Truth Principle

### For Each Project: Maximum of 3 Core Docs

**1. README.md (Primary)**
- Purpose: Project overview
- Audience: First-time users
- Length: 2-5 minutes to read
- Content: What, why, quick start

**2. QUICK_START.md**
- Purpose: Get running in < 5 minutes
- Audience: Users who want to start immediately
- Length: 10-20 commands max
- Content: Essential steps only

**3. docs/COMPREHENSIVE_GUIDE.md**
- Purpose: Complete documentation
- Audience: Advanced users, reference
- Length: As long as needed
- Content: Everything

### Everything Else Goes in docs/ Subdirectory
```
project/
├── README.md                    # Primary (one only)
├── QUICK_START.md              # Optional (if complex setup)
├── docs/                        # All other documentation
│   ├── COMPREHENSIVE_GUIDE.md
│   ├── API_REFERENCE.md
│   ├── TROUBLESHOOTING.md
│   ├── CONTRIBUTING.md
│   └── CHANGELOG.md
└── [project files]
```

---

## Documentation Audit Process

### Step 1: Inventory All Docs
```bash
find /home/dave/rundaverun/campaign -name "*.md" -type f
# Found: 150+ markdown files
```

### Step 2: Categorize
```
Primary Information:
- README.md (keep ONE)
- QUICK_START.md (consolidate to ONE)

Reference Information:
- Policy documents (keep, organize in docs/policies/)
- Implementation guides (keep, organize in docs/guides/)
- Deployment checklists (keep, organize in docs/deployment/)

Historical/Duplicate:
- Multiple "start here" docs (merge or delete)
- Old status reports (archive)
- Superseded versions (delete or archive)
```

### Step 3: Consolidate Duplicates
```
Found 5 "getting started" guides:
- 00_readme_start_here.md
- start_here_dave.md
- quick_start_guide.md
- start_here.md
- executive_summary_start_here.md

Action: Merge into ONE README.md
```

### Step 4: Create Directory Structure
```bash
mkdir -p docs/{policies,guides,deployment,archived}
```

### Step 5: Move Files
```bash
mv POLICY_*.md docs/policies/
mv *_guide.md docs/guides/
mv POST_DEPLOYMENT_CHECKLIST.md docs/deployment/
mv *_complete.md docs/archived/
```

### Step 6: Create Master Index
```markdown
# docs/INDEX.md

## Documentation Index

### Core Documentation
- README.md - Project overview (../README.md)
- QUICK_START.md - 5-minute setup (../QUICK_START.md)

### Policies
- Policy 01: Public Safety (policies/POLICY_01_PUBLIC_SAFETY_COMMUNITY_POLICING.md)
- Policy 02: Criminal Justice Reform (policies/POLICY_02_CRIMINAL_JUSTICE_REFORM.md)
[...]

### Deployment
- Post-Deployment Checklist (deployment/POST_DEPLOYMENT_CHECKLIST.md)
- Deployment Verification (deployment/deployment_verification.md)

### Guides
- Budget Implementation (guides/budget_implementation_roadmap.md)
- Volunteer Mobilization (guides/volunteer_mobilization_guide.md)
```

---

## Documentation Standards

### README.md Template
```markdown
# Project Name

One-sentence description.

## Quick Start

```bash
# 3-5 commands to get started
```

## What It Does

Brief explanation (2-3 paragraphs max)

## Documentation

- Quick Start - Get running in 5 minutes (QUICK_START.md)
- Full Documentation - Complete reference (docs/COMPREHENSIVE_GUIDE.md)
- API Reference - API docs (docs/API_REFERENCE.md)

## Support

How to get help.
```

### QUICK_START.md Template
```markdown
# Quick Start

Get [Project] running in 5 minutes.

## Prerequisites

- Requirement 1
- Requirement 2

## Installation

```bash
command 1
command 2
command 3
```

## Verification

```bash
test command
```

## Next Steps

- Full Documentation (docs/COMPREHENSIVE_GUIDE.md)
```

---

## Cleanup Checklist

- [ ] Inventory all .md files
- [ ] Identify duplicates
- [ ] Merge similar content
- [ ] Create docs/ structure
- [ ] Move files to appropriate locations
- [ ] Create INDEX.md
- [ ] Update all internal links
- [ ] Delete true duplicates
- [ ] Archive historical versions
- [ ] Test all links work

---

## Maintenance

**Monthly Review:**
- Check for new duplicate docs
- Update INDEX.md
- Archive old versions
- Verify links

**When Adding New Docs:**
- Check if content already exists
- Add to appropriate docs/ subdirectory
- Update INDEX.md
- Link from README if primary

---

## Best Practices

### DO:
✅ Keep ONE README.md
✅ Use docs/ for everything else
✅ Create master index
✅ Update links when moving files
✅ Delete true duplicates

### DON'T:
❌ Create multiple "start here" docs
❌ Duplicate information across files
❌ Keep outdated versions
❌ Skip updating links
❌ Create docs without checking for duplicates

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
