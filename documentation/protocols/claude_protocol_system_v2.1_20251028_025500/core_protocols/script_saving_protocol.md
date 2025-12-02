# Script Saving Protocol - Memory Reference

**Date Created**: 2025-10-28
**Purpose**: Standard protocol for saving scripts created during Claude sessions
**Location**: Always save to `/home/dave/skippy/scripts/`

## Protocol Rules

### 1. Save Location
**Always save scripts to**: `/home/dave/skippy/scripts/`

**Never save to**:
- `/home/dave/scripts/` (system-wide scripts only)
- `/home/dave/rundaverun/` (campaign-specific only)
- Other project directories (unless explicitly requested)

### 2. Versioning Requirements

**All scripts MUST include version numbers** using semantic versioning:
- Format: `script_name_v1.0.0.sh` or `script_name_v1.0.0.py`
- Increment rules:
  - **Major** (v2.0.0): Complete rewrites, breaking changes
  - **Minor** (v1.1.0): New features, significant improvements
  - **Patch** (v1.0.1): Bug fixes, small tweaks

**Version in file header**:
```bash
#!/bin/bash
# Script Name: descriptive_script_name
# Version: 1.0.0
# Date: 2025-10-28
# Purpose: Brief description of what this script does
```

### 3. Custom Naming Convention

**Use descriptive, specific names**:
- ✅ Good: `wordpress_backup_and_deploy_v1.0.0.sh`
- ✅ Good: `network_scanner_advanced_v2.1.0.py`
- ✅ Good: `budget_pdf_generator_v1.0.0.sh`
- ❌ Bad: `script1.sh`
- ❌ Bad: `test.py`
- ❌ Bad: `temp.sh`

**Naming pattern**: `{purpose}_{specific_task}_v{version}.{ext}`

### 4. When to Save

**Always save scripts when**:
- Creating new automation tools
- Writing data processing scripts
- Building utility functions
- Developing maintenance scripts
- Creating helper scripts for projects

**Ask user before saving**:
- Quick one-time debugging scripts
- Experimental/test code
- Scripts user says are temporary

### 5. Documentation Requirements

**Every saved script must include**:
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
```

### 6. Organization Within /skippy/scripts/

**Create subdirectories as needed**:
```
/home/dave/skippy/scripts/
├── automation/          - Automated tasks
├── backup/              - Backup scripts
├── data_processing/     - Data manipulation
├── deployment/          - Deployment scripts
├── maintenance/         - System maintenance
├── monitoring/          - Monitoring tools
├── network/             - Network utilities
├── utility/             - General utilities
├── web/                 - Web-related scripts
└── wordpress/           - WordPress-specific
```

### 7. Update Existing Scripts

**When improving existing scripts**:
1. Check if script exists in `/home/dave/skippy/scripts/`
2. Increment version number appropriately
3. Save with new version number
4. Keep previous version (don't overwrite)
5. Add changelog comment in header

Example:
```bash
# Changelog:
# v1.0.0 (2025-10-28): Initial release
# v1.1.0 (2025-10-28): Added error handling and logging
# v1.1.1 (2025-10-28): Fixed path bug
```

### 8. Executable Permissions

**After saving, always set executable**:
```bash
chmod +x /home/dave/skippy/scripts/subdirectory/script_name_v1.0.0.sh
```

### 9. Notification to User

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

### 10. Index Maintenance

**Keep track of scripts** in:
`/home/dave/skippy/scripts/index.md`

Update index with:
- Script name and version
- Purpose
- Last modified date
- Location

## Quick Reference

**Every script creation checklist**:
- [ ] Saved to `/home/dave/skippy/scripts/[category]/`
- [ ] Includes version number in filename (v1.0.0)
- [ ] Has complete header with metadata
- [ ] Uses descriptive, custom name
- [ ] Set executable permissions
- [ ] Notified user of save location
- [ ] Added to scripts index (if major script)

## Examples

### Good Script Names
- `campaign_glossary_merger_v1.0.0.py`
- `voter_education_package_builder_v2.1.0.sh`
- `wordpress_local_backup_v1.0.0.sh`
- `network_device_scanner_v3.0.0.py`
- `pdf_batch_converter_v1.2.1.sh`

### Directory Organization Examples
```bash
# Automation script
/home/dave/skippy/scripts/automation/daily_backup_v1.0.0.sh

# WordPress script
/home/dave/skippy/scripts/wordpress/plugin_updater_v1.0.0.sh

# Data processing
/home/dave/skippy/scripts/data_processing/csv_merger_v1.0.0.py

# Deployment
/home/dave/skippy/scripts/deployment/godaddy_deploy_v2.0.0.sh
```

## Priority Rules

1. **Always use versioning** - No exceptions
2. **Always use descriptive names** - No generic names
3. **Always save to /skippy/scripts/** - Unless explicitly told otherwise
4. **Always add documentation** - Header with metadata
5. **Always organize by category** - Use subdirectories

---

**This is a persistent memory reference for all future Claude sessions.**
**Read this file at the start of any session involving script creation.**
