# Script Usage vs Creation Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

With 328 existing scripts plus tools in skippy-tools and utilities, deciding when to use existing vs create new is critical.

## Purpose

- Maximize use of existing, tested scripts
- Avoid code duplication
- Know when new scripts are warranted
- Maintain script quality standards

---

## Decision Flow

```
Task requested
    ↓
Is there an exact match script?
    YES → Use it
    NO  ↓
Is there a close match that can be adapted?
    YES → Extend/adapt it
    NO  ↓
Is this a one-off task?
    YES → Write inline commands
    NO  ↓
Is this reusable?
    YES → Create new script
    NO  → Write inline commands
```

---

## Use Existing Scripts For

### WordPress Deployment
```bash
# Use skippy-scripts
pre_deployment_validator_v1.0.0.sh
deployment_verification_v1.0.0.sh
wordpress_health_check_v1.0.0.sh
```

### File Management
```bash
# Use utilities or skippy-tools
utilities find-duplicates
utilities organize
duplicate_cleaner_v1.0.0.py
```

### Security
```bash
# Use skippy-tools
pre_commit_security_scan_v1.0.0.sh
```

### System Maintenance
```bash
# Use skippy-tools
docker_cleanup_v1.0.0.sh
```

### Health Checks
```bash
# Use skippy CLI
skippy health
skippy wordpress health
```

---

## Write Inline Commands For

### One-Off File Operations
```bash
# Don't create script
find ~/Documents -name "*.old" -delete
```

### Quick Searches
```bash
# Don't create script
grep -r "TODO" ~/project/
```

### Status Checks
```bash
# Don't create script
git status
docker ps
systemctl status nginx
```

### Simple Data Extraction
```bash
# Don't create script
cat file.csv | cut -d',' -f2 | sort | uniq
```

---

## Create New Scripts For

### Reusable Workflows
```bash
# Example: Weekly maintenance combining multiple tools
#!/bin/bash
# weekly_maintenance_v1.0.0.sh
docker_cleanup_v1.0.0.sh
utilities find-duplicates ~ --dry-run > ~/logs/duplicates.log
skippy health
```

### Complex Multi-Step Processes
```bash
# Example: Complete deployment pipeline
#!/bin/bash
# deploy_pipeline_v1.0.0.sh
pre_deployment_validator_v1.0.0.sh
deploy-to-godaddy.sh
post-deployment-setup.sh  (on remote)
deployment_verification_v1.0.0.sh
```

### Project-Specific Automation
```bash
# Example: Campaign-specific checks
#!/bin/bash
# campaign_content_validator_v1.0.0.sh
# Validates campaign claims against source documents
```

### Integration Between Tools
```bash
# Example: Export utilities database to spreadsheet
#!/usr/bin/python3
# export_file_operations_v1.0.0.py
from utilities.common.database import OperationDatabase
import csv
# ...export to CSV
```

---

## Script Creation Standards

### Naming Convention
```
{purpose}_{version}.{ext}

Examples:
backup_verification_test_v1.0.0.sh
duplicate_cleaner_v1.0.0.py
wordpress_health_check_v1.0.0.sh
```

### Header Template
```bash
#!/bin/bash
# Script Name
# Purpose: [One line description]
# Version: 1.0.0
# Author: Dave / Claude
# Created: YYYY-MM-DD
#
# Usage: script_name.sh [options]
#
# Dependencies:
#   - bash >= 4.0
#   - wp-cli (for WordPress scripts)
#
# Examples:
#   ./script_name.sh --dry-run
```

### Required Elements
- Shebang line
- Purpose/description
- Version number
- Usage examples
- Error handling
- Exit codes
- Help text (--help)

---

## Examples

### Example 1: Use Existing (Exact Match)

**Request:** "Find duplicates in Downloads"

**Decision:** Use existing

**Rationale:**
- utilities find-duplicates exists
- Exact match for request
- Well-tested, feature-rich

**Action:**
```bash
utilities find-duplicates ~/Downloads
```

### Example 2: Inline Commands (One-Off)

**Request:** "Show me all PDF files modified this week"

**Decision:** Inline commands

**Rationale:**
- Simple one-off query
- Not reusable
- Two commands sufficient

**Action:**
```bash
find ~/Documents -name "*.pdf" -mtime -7 -ls
```

### Example 3: Create New (Reusable Workflow)

**Request:** "Create a script that runs all pre-deployment checks"

**Decision:** Create new script

**Rationale:**
- Combines multiple existing scripts
- Will be run repeatedly
- Deployment workflow integration

**Action:**
```bash
# Create: ~/skippy/scripts/deployment/complete_pre_deployment_check_v1.0.0.sh
#!/bin/bash
# Complete Pre-Deployment Check
# Runs all validation before deployment

set -e

echo "=== Running Security Scan ==="
bash ~/skippy-tools/utility/pre_commit_security_scan_v1.0.0.sh

echo "=== Running WordPress Validator ==="
bash ~/rundaverun/campaign/skippy-scripts/wordpress/pre_deployment_validator_v1.0.0.sh

echo "=== Running Health Check ==="
skippy health

echo "=== All Pre-Deployment Checks Passed ✓ ==="
```

### Example 4: Extend Existing (Close Match)

**Request:** "Organize documents but also generate report"

**Decision:** Extend utilities

**Rationale:**
- utilities organize exists (close match)
- Need additional reporting
- Use utilities API

**Action:**
```python
#!/usr/bin/env python3
# organize_with_report_v1.0.0.py

from utilities.organizers import BaseOrganizer
from utilities.common import Config
import json

class ReportingOrganizer(BaseOrganizer):
    def organize(self):
        results = super().organize()
        # Add custom reporting
        with open('organization_report.json', 'w') as f:
            json.dump(results, f, indent=2)
        return results

# Use it
organizer = ReportingOrganizer()
organizer.organize()
```

---

## When NOT to Create Scripts

### Don't Create For:
❌ Simple one-line commands
❌ One-time data migrations
❌ Quick status checks
❌ Exploratory analysis
❌ Tasks with existing scripts

### Create Instead For:
✅ Repeated workflows
✅ Complex multi-step processes
✅ Integration between systems
✅ Production automation
✅ Audit-trail required tasks

---

## Script Maintenance

### Version Numbering
```
v1.0.0 → v1.0.1 (bug fix)
v1.0.1 → v1.1.0 (new feature)
v1.1.0 → v2.0.0 (breaking change)
```

### Keep Old Versions
```
backup_script_v1.0.0.sh (original)
backup_script_v1.1.0.sh (improved)
backup_script_v2.0.0.sh (major rewrite)

Allows rollback if new version has issues
```

### Documentation
```
Update when creating scripts:
- Add to SCRIPT_INDEX.md
- Document in README if major tool
- Add usage examples
- Note dependencies
```

---

## Best Practices

### DO:
✅ Search for existing scripts first
✅ Use established tools when available
✅ Create reusable scripts for repeated tasks
✅ Follow naming conventions
✅ Version scripts properly

### DON'T:
❌ Create scripts for one-off tasks
❌ Duplicate existing functionality
❌ Create scripts without headers
❌ Skip versioning
❌ Forget to make executable (chmod +x)

---

## Quick Reference

```
Task Type                    → Action
═══════════════════════════════════════════════════
WordPress deployment         → Use skippy-scripts
Find duplicates             → Use utilities/skippy-tools
Security scan               → Use pre_commit_security_scan
One-off file operation      → Inline bash commands
Repeated workflow           → Create new script
Complex integration         → Create new script
Status check                → Inline commands
Custom analysis             → Write custom code
```

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
