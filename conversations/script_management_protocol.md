# Script Management Protocol

**Version:** 2.0.0
**Created:** 2025-11-05 (Consolidated from script_creation v1.0.0 + script_saving v1.0.0)
**Purpose:** Complete lifecycle management for scripts - search, create, save, and version
**Priority:** CRITICAL - MUST follow before creating ANY script

---

## Overview

This protocol covers the complete lifecycle of script management in the skippy system:
1. **Search existing scripts first** (avoid duplication)
2. **Create new scripts** (when necessary)
3. **Save properly** (correct location and naming)
4. **Version correctly** (semantic versioning)
5. **Organize logically** (category structure)

**Key Principles:**
- Don't reinvent the wheel - reuse and improve existing scripts
- Always use semantic versioning
- Maintain organized category structure
- Document everything

---

## Part 1: Pre-Creation Search (MANDATORY)

### Step 1: Search Existing Scripts (REQUIRED)

Before writing ANY new script, you MUST:

1. **Search by purpose/keyword** in the script library
2. **Check relevant category directories**
3. **Review similar scripts** that might be adapted

**Commands to Run:**

```bash
# Search all scripts for keywords related to the task
grep -r "KEYWORD" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py"

# List scripts in relevant category
ls -lh /home/dave/skippy/scripts/[CATEGORY]/

# Search by filename pattern
find /home/dave/skippy/scripts -name "*PATTERN*"
```

**Example:**
```bash
# User asks: "Create a script to backup files"
# FIRST, search for existing backup scripts:
grep -r "backup" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py"
ls -lh /home/dave/skippy/scripts/backup/
```

### Step 2: Review Found Scripts

If similar scripts exist:

1. **Read the script** to understand its functionality
2. **Assess if it can be modified** to meet the new requirement
3. **Check version numbers** to use the latest version
4. **Consider if enhancement is better than new creation**

### Step 3: Decision Tree

```
┌─────────────────────────────────────┐
│ Need to create/modify a script?    │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ Step 1: Search existing scripts    │
│ - grep for keywords                 │
│ - check relevant category           │
│ - list similar scripts              │
└───────────────┬─────────────────────┘
                │
                ▼
        ┌───────┴────────┐
        │                │
   Found?              Not Found?
        │                │
        ▼                ▼
┌──────────────┐   ┌──────────────┐
│ Similar      │   │ No similar   │
│ exists       │   │ scripts      │
└──────┬───────┘   └──────┬───────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│ Can modify?  │   │ Create new   │
│              │   │ script       │
└──────┬───────┘   └──────────────┘
       │
   ┌───┴───┐
   │       │
  Yes     No
   │       │
   ▼       ▼
┌────┐  ┌────────┐
│Use │  │Create  │
│and │  │new but │
│mod-│  │document│
│ify │  │why     │
└────┘  └────────┘
```

### Step 4: Inform User

**ALWAYS tell the user:**
- "I found X existing scripts that might work"
- "Script Y at path Z does something similar"
- "Would you like me to modify [existing script] or create a new one?"

---

## Part 2: Script Library Organization

### Current Categories (226+ scripts total)

| Category | Count | Purpose |
|----------|-------|---------|
| **automation/** | 29+ | Document scanning, music organization, drive scanning |
| **backup/** | 6+ | Google Photos, cloud sync, full backups |
| **Blockchain/** | 3+ | Ethereum, Chainlink setup |
| **data_processing/** | 17+ | Glossary generation, data conversion |
| **deployment/** | 19+ | Server setup, app installation |
| **maintenance/** | 17+ | System updates, fixes, optimizers |
| **monitoring/** | 19+ | EbonHawk, Nexus, media monitoring |
| **network/** | 5+ | WiFi debugging, SSL testing |
| **utility/** | 35+ | General utilities, helpers, launchers |
| **web/** | 0 | Reserved for web scripts |
| **wordpress/** | 9+ | Deployment, GoDaddy, REST API |

### Category Selection Guide

Choose the most appropriate category:
- **automation** - Automated tasks, document processing, scanning
- **backup** - Backup and synchronization scripts
- **data_processing** - Data conversion, transformation, generation
- **deployment** - Installation, setup, configuration
- **maintenance** - System updates, fixes, cleanups
- **monitoring** - Status checks, watchers, alerts
- **network** - Network diagnostics, testing, optimization
- **utility** - General-purpose tools, helpers
- **wordpress** - WordPress-specific operations
- **web** - Web-related scripts (general)

---

## Part 3: When to Modify vs Create New

### Modify Existing Script When:

✅ Script does 80%+ of what you need
✅ Changes are minor enhancements
✅ Adding features that benefit the original purpose
✅ Fixing bugs or improving existing functionality
✅ Script is well-structured and documented

**Action:** Create new version (bump version number)

### Create New Script When:

✅ No existing script does anything similar
✅ Purpose is fundamentally different
✅ Would require complete rewrite (>70% changes)
✅ Existing script is too specialized to generalize
✅ User explicitly requests a new script

**Action:** Create new script with v1.0.0

### Quick Decision Matrix

| Situation | Action |
|-----------|--------|
| Exact match found | Use as-is or suggest minor updates |
| 80%+ match found | Modify existing, bump version |
| 50-79% match found | Offer choice: modify or create new |
| <50% match found | Create new, document why |
| No match found | Create new script |
| User wants new despite match | Create but inform about existing |

---

## Part 4: Modification Workflow

When modifying an existing script:

### 1. Read Current Script
```bash
cat /home/dave/skippy/scripts/[category]/script_name_v1.0.0.sh
```

### 2. Determine Version Bump

- **Patch (v1.0.X):** Bug fixes, minor improvements, no breaking changes
- **Minor (v1.X.0):** New features, enhanced functionality, backward compatible
- **Major (vX.0.0):** Breaking changes, complete rewrites, incompatible changes

### 3. Inform User

"I found an existing script at `/home/dave/skippy/scripts/[category]/[script]` that does [description]. I can enhance it to [new functionality] by [changes needed]. This would be version [new_version]. Proceed?"

### 4. Create Modified Version

- Copy to new version number
- Make modifications
- Update header with changes
- Test if possible
- Keep old version intact

### 5. Document Changes

Update the script header:
```bash
# Version History:
# v1.0.0 - 2025-10-15 - Initial version
# v1.1.0 - 2025-10-31 - Added [feature], enhanced [functionality]
```

---

## Part 5: Script Creation & Saving

### Save Location Rules

**Always save scripts to**: `/home/dave/skippy/scripts/[category]/`

**Never save to**:
- `/home/dave/scripts/` (system-wide scripts only)
- `/home/dave/rundaverun/` (campaign-specific only)
- Other project directories (unless explicitly requested)

### Versioning Requirements

**All scripts MUST include version numbers** using semantic versioning:
- Format: `script_name_v1.0.0.sh` or `script_name_v1.0.0.py`
- Increment rules:
  - **Major** (v2.0.0): Complete rewrites, breaking changes
  - **Minor** (v1.1.0): New features, significant improvements
  - **Patch** (v1.0.1): Bug fixes, small tweaks

### Naming Convention

**Use descriptive, specific names**:
- ✅ Good: `wordpress_backup_and_deploy_v1.0.0.sh`
- ✅ Good: `network_scanner_advanced_v2.1.0.py`
- ✅ Good: `budget_pdf_generator_v1.0.0.sh`
- ❌ Bad: `script1.sh`
- ❌ Bad: `test.py`
- ❌ Bad: `temp.sh`

**Naming pattern**: `{purpose}_{specific_task}_v{version}.{ext}`
**Use lowercase_with_underscores** for all script names

### Documentation Requirements

**Every saved script must include complete header**:
```bash
#!/bin/bash
# Script Name: [descriptive_name]
# Version: [semantic_version]
# Date: [YYYY-MM-DD]
# Author: Claude Code
# Purpose: [What this script does]
# Usage: [How to run it]
# Dependencies: [Required tools/packages]
# Notes: [Any important information]
#
# Version History:
# v1.0.0 - [date] - Initial release
```

### Executable Permissions

**After saving, always set executable**:
```bash
chmod +x /home/dave/skippy/scripts/[category]/script_name_v1.0.0.sh
```

### User Notification

**After saving, inform user**:
- Full path where script was saved
- Version number
- Brief description of what it does
- How to run it

Example message:
```
✅ Script saved: /home/dave/skippy/scripts/automation/wordpress_backup_v1.0.0.sh
Version: 1.0.0
Purpose: Automated WordPress backup with compression
Usage: bash /home/dave/skippy/scripts/automation/wordpress_backup_v1.0.0.sh
```

---

## Part 6: Search Strategies

### By Functionality

```bash
# Backup-related
ls /home/dave/skippy/scripts/backup/

# WordPress/web
ls /home/dave/skippy/scripts/wordpress/
ls /home/dave/skippy/scripts/web/

# System maintenance
ls /home/dave/skippy/scripts/maintenance/

# Monitoring
ls /home/dave/skippy/scripts/monitoring/

# Automation
ls /home/dave/skippy/scripts/automation/
```

### By Keyword

```bash
# Search all scripts for specific functionality
grep -r "google" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l
grep -r "backup" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l
grep -r "wordpress" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l
grep -r "database" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l
grep -r "scan" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l
```

### By Technology

```bash
# Find Python scripts
find /home/dave/skippy/scripts -name "*.py" | grep -i "KEYWORD"

# Find shell scripts
find /home/dave/skippy/scripts -name "*.sh" | grep -i "KEYWORD"

# Find by version (get latest)
ls /home/dave/skippy/scripts/*/SCRIPTNAME_v*.sh | sort -V | tail -1
```

---

## Part 7: Examples

### Example 1: User Requests Backup Script

❌ **WRONG Approach:**
```
User: "Create a script to backup my home directory"
Assistant: *immediately writes new backup script*
```

✅ **CORRECT Approach:**
```
User: "Create a script to backup my home directory"
Assistant: *searches first*
$ ls /home/dave/skippy/scripts/backup/

I found several existing backup scripts:
- full_home_backup_v1.0.0.sh (backs up entire home directory)
- gdrive_backup_v1.0.0.sh (backs up to Google Drive)
- backup_google_photos_v1.0.0.sh (Google Photos backup)

The 'full_home_backup_v1.0.0.sh' already handles home directory backups.
Would you like me to:
1. Use the existing script as-is
2. Modify it to add specific features you need
3. Create a new specialized version

What specific features do you need?
```

### Example 2: User Requests Document Scanner

❌ **WRONG Approach:**
```
User: "I need a script to organize scanned documents"
Assistant: *creates new document organizer script*
```

✅ **CORRECT Approach:**
```
User: "I need a script to organize scanned documents"
Assistant: *searches first*
$ ls /home/dave/skippy/scripts/automation/ | grep -i scan

I found 12 existing document scanning scripts:
- scan_organizer_v1.0.0.py (interactive GUI organizer)
- simple_scan_organizer_v1.0.0.py (simpler version)
- business_document_organizer_v1.0.0.py (business docs)
- automated_document_scanner_v1.0.0.sh (automated scanning)
- epson_scan_process_gui_v1.0.0.sh (Epson scanner)

The 'scan_organizer_v1.0.0.py' provides an interactive GUI for organizing
scanned documents into personal/business categories.

Would this work for your needs, or do you need specific customizations?
```

### Example 3: Modifying Existing Script

✅ **CORRECT Approach:**
```
User: "Add email notification to the backup script"
Assistant: *reads existing script*
$ cat /home/dave/skippy/scripts/backup/full_home_backup_v1.0.0.sh

I found the existing backup script. I can add email notification functionality.
This would be a minor version update (v1.1.0) since we're adding a new feature.

Changes:
- Add email notification on completion
- Add error email on failure
- Require 'mailutils' dependency

Shall I create v1.1.0 with these enhancements?
```

---

## Part 8: Quick Reference Commands

### Pre-Creation Search Commands

```bash
# Search all scripts for keyword
grep -r "KEYWORD" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l

# List category contents
ls -lh /home/dave/skippy/scripts/[CATEGORY]/

# Search filenames
find /home/dave/skippy/scripts -name "*PATTERN*" -type f

# Get latest version of a script
ls /home/dave/skippy/scripts/*/SCRIPTNAME_v*.sh | sort -V | tail -1

# Count scripts per category
for dir in /home/dave/skippy/scripts/*/; do echo -n "$(basename $dir): "; find $dir -maxdepth 1 -type f | wc -l; done
```

### Common Search Patterns

```bash
# Backup-related
grep -r "backup\|sync\|archive" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l

# WordPress-related
grep -r "wordpress\|wp-cli\|godaddy" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l

# Network-related
grep -r "network\|wifi\|dns\|ssl" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l

# Document processing
grep -r "scan\|document\|pdf\|organize" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l

# System maintenance
grep -r "update\|upgrade\|clean\|maintain" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l

# Monitoring
grep -r "monitor\|watch\|alert\|status" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l
```

---

## Part 9: Script Creation Checklist

**Every script creation checklist**:
- [ ] Searched existing scripts first (grep + ls)
- [ ] Informed user of existing options (if found)
- [ ] Determined if modify or create new
- [ ] Saved to `/home/dave/skippy/scripts/[category]/`
- [ ] Includes version number in filename (v1.0.0)
- [ ] Has complete header with metadata
- [ ] Uses descriptive, custom name (lowercase_with_underscores)
- [ ] Set executable permissions (chmod +x)
- [ ] Notified user of save location and usage
- [ ] Added version history section for future updates

---

## Part 10: Special Cases

### Case 1: User Explicitly Wants New Script

If user says "create a NEW script" or "don't use existing":
- Still inform them of existing options
- Note: "Creating new script as requested, though [existing_script] could have been modified"
- Proceed with creation

### Case 2: Existing Script is Legacy/Deprecated

If found script is old or poorly maintained:
- Inform user of its limitations
- Recommend creating new version with modern best practices
- Archive old version or mark as deprecated

### Case 3: Multiple Similar Scripts Found

If 3+ similar scripts exist:
- List all options
- Recommend the most appropriate one
- Suggest consolidation if they're nearly identical

### Case 4: Update Existing Scripts

**When improving existing scripts**:
1. Check if script exists in `/home/dave/skippy/scripts/`
2. Increment version number appropriately
3. Save with new version number
4. Keep previous version (don't overwrite)
5. Add changelog comment in header

---

## Part 11: Common Mistakes to Avoid

❌ **Don't:**
- Create new scripts without searching first
- Assume no script exists for common tasks
- Only search one category
- Ignore similar scripts that could be adapted
- Use generic names (script1.sh, test.py)
- Save to wrong directories
- Forget version numbers
- Skip documentation headers

✅ **Do:**
- Always search before creating
- Check multiple categories if relevant
- Read existing scripts to understand capabilities
- Offer modification as first option
- Document why new script is needed if creating
- Use semantic versioning
- Organize by category
- Set executable permissions
- Notify user with full details

---

## Part 12: Integration with Other Protocols

This protocol works with:

1. **error_logging_protocol.md** - Logging errors in scripts
2. **git_workflow_protocol.md** - Version control for scripts
3. **documentation_standards_protocol.md** - Documenting scripts
4. **deployment_checklist_protocol.md** - Deploying scripts to production
5. **testing_qa_protocol.md** - Testing scripts before use

### Workflow Integration

```
User Request
     │
     ▼
┌─────────────────────────────┐
│ Script Management Protocol  │ ◄── YOU ARE HERE
│ 1. Search existing first    │
│ 2. Modify or create?        │
│ 3. Save with versioning     │
│ 4. Organize by category     │
│ 5. Document completely      │
└─────────────────────────────┘
```

---

## Part 13: Success Metrics

This protocol is working when:

✅ Zero duplicate scripts are created
✅ Existing scripts are enhanced instead of replaced
✅ User is informed of existing options before creation
✅ Script library stays organized and consolidated
✅ Version numbers increment logically
✅ No abandoned orphan scripts scattered around
✅ All scripts have proper documentation
✅ Scripts are categorized correctly
✅ Executable permissions are set

---

## Part 14: When to Reference This Protocol

**ALWAYS reference before:**
- Creating any script (.sh, .py, .pl, .rb)
- User requests automation
- User asks for tool/utility
- Starting any script-related task
- Modifying existing scripts

**Example trigger phrases:**
- "Create a script to..."
- "I need a script for..."
- "Can you write a script that..."
- "Make a tool to..."
- "Automate..."
- "Update the script..."
- "Modify the script..."

---

## Part 15: Protocol Maintenance

**Monthly Review:**
- Check for duplicate scripts created despite protocol
- Identify common search patterns not covered
- Update examples with real usage
- Refine search commands
- Verify category organization is still logical

**After Creating 10+ Scripts:**
- Review if any could have used existing scripts
- Update protocol with lessons learned
- Add new categories if patterns emerge
- Update script counts

**Quarterly:**
- Full protocol review for effectiveness
- Update version if significant changes
- Archive obsolete sections
- Add new best practices learned

---

## Consolidation Notes

**This protocol consolidates:**
- `script_creation_protocol.md` (v1.0.0) - Search and decision logic
- `script_saving_protocol.md` (v1.0.0) - Save location and versioning

**Eliminated duplication:**
- Script header template (was in both)
- Versioning guidelines (was duplicated)
- File naming conventions (was repeated)
- Storage location rules (was in both)
- Organization structure (was duplicated)

**Net result:**
- ~650 lines vs 800 lines combined (19% reduction)
- Single source of truth
- Better flow from search → create → save
- Easier to maintain and reference

---

**Status:** ✅ ACTIVE
**Version:** 2.0.0
**Last Updated:** 2025-11-05
**Supersedes:** script_creation_protocol.md v1.0.0, script_saving_protocol.md v1.0.0
**Integration:** Works with error_logging, git_workflow, documentation_standards

**This protocol MUST be followed before creating or modifying ANY script.**

---
