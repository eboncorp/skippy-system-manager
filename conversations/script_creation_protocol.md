# Script Creation Protocol

**Version:** 1.0.0
**Created:** 2025-10-31
**Purpose:** Ensure we check for existing scripts before creating new ones
**Priority:** HIGH - MUST follow before creating ANY script

---

## Purpose

This protocol defines:
- Mandatory search procedures before creating new scripts
- Decision matrix for modifying existing vs creating new
- Script library organization (226+ scripts across 12 categories)
- Search strategies by functionality, keyword, and technology
- Integration with script_saving and version control protocols

---

## Overview

Before creating any new script, ALWAYS search the existing script library first. There are 226+ scripts already organized in `/home/dave/skippy/scripts/` that may already solve the problem or can be easily modified.

**Key Principle:** Don't reinvent the wheel - reuse and improve existing scripts.

---

## Mandatory Pre-Creation Checklist

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

## Script Library Organization

### Current Categories (226 scripts total)

| Category | Count | Purpose |
|----------|-------|---------|
| **automation/** | 29 | Document scanning, music organization, drive scanning |
| **backup/** | 6 | Google Photos, cloud sync, full backups |
| **Blockchain/** | 3 | Ethereum, Chainlink setup |
| **data_processing/** | 17 | Glossary generation, data conversion |
| **deployment/** | 19 | Server setup, app installation |
| **legacy_system_managers/** | 54 | System managers, NexusController |
| **maintenance/** | 17 | System updates, fixes, optimizers |
| **monitoring/** | 19 | EbonHawk, Nexus, media monitoring |
| **network/** | 5 | WiFi debugging, SSL testing |
| **utility/** | 35 | Google Drive, TidyTux, launchers |
| **Utility/** | 19 | Legacy utilities (to consolidate) |
| **web/** | 0 | Reserved for web scripts |
| **wordpress/** | 9 | Deployment, GoDaddy, REST API |

### Common Script Types Available

**Backup Scripts:**
- `backup_google_photos_v1.0.0.sh`
- `sync_clouds_to_gdrive_v1.0.0.sh`
- `full_home_backup_v1.0.0.sh`
- `gdrive_backup_v1.0.0.sh`

**Document Automation:**
- `scan_organizer_v1.0.0.py`
- `duplicate_cleaner_v1.0.0.py`
- `business_document_organizer_v1.0.0.py`
- `automated_document_scanner_v1.0.0.sh`

**System Management:**
- `system_update_v1.0.0.sh`
- `system_cleanup_v1.0.0.sh`
- `system_audit_comprehensive_v1.0.0.sh`

**Monitoring:**
- `nexus_status_v1.0.0.sh`
- `downloads_watcher_v1.0.0.py`
- `screenshot_cleanup_v1.0.0.py`

**WordPress:**
- `deploy_to_production_v1.0.0.sh`
- `wordpress_health_check_v1.0.0.sh`
- `import_markdown_to_wordpress_v1.0.0.py`

**Network:**
- `wifi_debug_v1.0.0.sh`
- `test_network_ssl_v1.0.0.sh`
- `network_performance_enhancer_v1.0.0.sh`

---

## Search Strategies

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

## When to Modify vs Create New

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

---

## Modification Workflow

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

## Creation Workflow (When No Existing Script)

Only when no suitable script exists:

### 1. Confirm No Match

"I searched the script library and found no existing scripts that handle [task]. Creating new script: [name]"

### 2. Follow Script Saving Protocol

Reference: `/home/dave/skippy/conversations/script_saving_protocol.md`

- Save to `/home/dave/skippy/scripts/[appropriate-category]/`
- Use semantic versioning: `script_name_v1.0.0.sh`
- Use lowercase_with_underscores naming
- Include complete header documentation
- Make executable (chmod +x)
- Update category if creating new type

### 3. Categorize Correctly

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

## Examples

### Example 1: User Requests Backup Script

❌ **WRONG Approach:**
```
User: "Create a script to backup my home directory"
Assistant: *immediately writes new backup script*
```

✅ **CORRECT Approach:**
```
User: "Create a script to backup my home directory"Assistant: *searches first*
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

### Example 3: User Requests Network Tool

✅ **CORRECT Approach:**
```
User: "Create a script to test WiFi connection"
Assistant: *searches first*
$ ls /home/dave/skippy/scripts/network/
$ grep -r "wifi\|wireless\|connection" /home/dave/skippy/scripts/network/ -l

I found:
- wifi_debug_v1.0.0.sh (comprehensive WiFi diagnostic tool)
- test_network_ssl_v1.0.0.sh (SSL certificate testing)
- network_performance_enhancer_v1.0.0.sh (optimize network)

The 'wifi_debug_v1.0.0.sh' already provides WiFi connection testing and
diagnostics. It checks connection status, DNS, gateway, and SSL certificates.

Shall I use this script or do you need additional specific tests?
```

---

## Quick Reference Commands

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

## Integration with Other Protocols

This protocol works with:

1. **script_saving_protocol.md** - Where/how to save scripts
2. **error_logging_protocol.md** - Logging errors in scripts
3. **git_workflow_protocol.md** - Version control for scripts
4. **documentation_standards_protocol.md** - Documenting scripts

### Workflow Integration

```
User Request
     │
     ▼
┌─────────────────────────┐
│ Script Creation Protocol│ ◄── YOU ARE HERE
│ (Search existing first) │
└────────────┬────────────┘
             │
        ┌────┴────┐
        │         │
   Found?     Not Found?
        │         │
   Modify?    Create New
        │         │
        ▼         ▼
┌────────────────────────┐
│ Script Saving Protocol │
│ (Where/how to save)    │
└────────────────────────┘
```

---

## Success Metrics

This protocol is working when:

✅ Zero duplicate scripts are created
✅ Existing scripts are enhanced instead of replaced
✅ User is informed of existing options before creation
✅ Script library stays organized and consolidated
✅ Version numbers increment logically
✅ No abandoned orphan scripts scattered around

---

## Special Cases

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

---

## Common Mistakes to Avoid

❌ **Don't:**
- Create new scripts without searching first
- Assume no script exists for common tasks
- Only search one category
- Ignore similar scripts that could be adapted

✅ **Do:**
- Always search before creating
- Check multiple categories if relevant
- Read existing scripts to understand capabilities
- Offer modification as first option
- Document why new script is needed if creating

---

## Quick Decision Matrix

| Situation | Action |
|-----------|--------|
| Exact match found | Use as-is or suggest minor updates |
| 80%+ match found | Modify existing, bump version |
| 50-79% match found | Offer choice: modify or create new |
| <50% match found | Create new, document why |
| No match found | Create new script |
| User wants new despite match | Create but inform about existing |

---

## When to Reference This Protocol

**ALWAYS reference before:**
- Creating any script (.sh, .py, .pl, .rb)
- User requests automation
- User asks for tool/utility
- Starting any script-related task

**Example trigger phrases:**
- "Create a script to..."
- "I need a script for..."
- "Can you write a script that..."
- "Make a tool to..."
- "Automate..."

---

## Protocol Maintenance

**Monthly Review:**
- Check for duplicate scripts created despite protocol
- Identify common search patterns not covered
- Update examples with real usage
- Refine search commands

**After Creating 10+ Scripts:**
- Review if any could have used existing scripts
- Update protocol with lessons learned
- Add new categories if patterns emerge

---

**Status:** ✅ ACTIVE
**Version:** 1.0.0
**Last Updated:** 2025-10-31
**Integration:** Works with script_saving_protocol.md

**This protocol MUST be followed before creating ANY script.**

---
