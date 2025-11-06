# Tool Selection Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

With 328 scripts in skippy, tools in skippy-tools, utilities package with CLI, and the ability to write new code, choosing the right tool for each task is critical for efficiency.

## Purpose

- Use existing, tested tools when available
- Avoid reinventing the wheel
- Maintain consistency across operations
- Know when to write new code vs use existing
- Optimize for speed and reliability

---

## Decision Tree

### Step 1: Is this a common task?
```
YES → Check existing tools (Step 2)
NO  → Consider writing new code (Step 5)
```

### Step 2: Which category?
```
WordPress/Campaign → Check rundaverun skippy-scripts
File Management    → Check utilities or skippy-tools
System Admin       → Check skippy scripts
Security          → Check skippy-tools security scans
Git Operations    → Check skippy-tools git utilities
Docker            → Check skippy-tools docker cleanup
```

### Step 3: Does a tool exist?
```
YES → Use it (Step 4)
NO  → Write new code (Step 5)
```

### Step 4: Is tool appropriate?
```
Exact match  → Use it
Close enough → Adapt/extend it
Not quite    → Write new code
```

### Step 5: Write new code
```
One-off task     → Write inline script
Reusable feature → Create new script
Complex feature  → Use utilities API or create new tool
```

---

## Tool Inventory

### WordPress/Campaign Tools
**Location:** `/home/dave/rundaverun/campaign/skippy-scripts/wordpress/`

**Use for:**
- WordPress deployment validation
- Post-deployment verification
- WordPress health checks

**Tools:**
```bash
pre_deployment_validator_v1.0.0.sh
deployment_verification_v1.0.0.sh
wordpress_health_check_v1.0.0.sh
```

### Skippy-Tools (Everyday Utilities)
**Location:** `/home/dave/skippy-tools/`

**Use for:**
- Finding duplicates (quick scans)
- Security scanning (git commits)
- Docker cleanup
- Safe git pushes

**Tools:**
```bash
# Automation
duplicate_cleaner_v1.0.0.py
quick_duplicate_finder_v1.0.0.py
find_duplicates_v1.0.0.sh

# Utility
pre_commit_security_scan_v1.0.0.sh
push_to_github_v1.0.0.sh
docker_cleanup_v1.0.0.sh
generate_script_index_v1.0.0.sh
```

### Utilities Package (Document Organization)
**Location:** `/home/dave/utilities/`

**Use for:**
- Document organization
- Duplicate detection (comprehensive)
- PDF/document processing
- File categorization
- Web dashboard for monitoring

**CLI:**
```bash
utilities organize <directory>
utilities find-duplicates <directory>
utilities categorize <file>
utilities web
utilities config-show
utilities categories-list
```

**API:**
```python
from utilities.organizers import BaseOrganizer
from utilities.common import calculate_file_hash, CategoryMatcher
```

### Skippy Scripts (328 scripts)
**Location:** `/home/dave/skippy/scripts/`

**Categories:**
```
automation/      - Automation tasks
backup/          - Backup operations
data_processing/ - Data manipulation
deployment/      - Deployment tools
maintenance/     - System maintenance
monitoring/      - System monitoring
network/         - Network utilities
security/        - Security tools
testing/         - Testing frameworks
utility/         - General utilities
wordpress/       - WordPress specific
```

**Use for:** Check before writing new scripts

### Skippy CLI
**Location:** `/home/dave/bin/skippy`

**Use for:**
- System status checks
- Health monitoring
- Performance metrics
- Log management
- Script management
- WordPress operations
- Backup operations

**Commands:**
```bash
skippy status
skippy health
skippy metrics show
skippy logs tail
skippy scripts list
skippy wordpress health
skippy backup create
```

---

## Selection Guidelines

### Priority Order

**1st: Use Existing Integrated Tools**
```
For WordPress deployment → use skippy-scripts
For git security → use pre_commit_security_scan
For Docker cleanup → use docker_cleanup
```

**2nd: Use Skippy-Tools or Utilities**
```
For file organization → use utilities
For duplicates → use utilities or skippy-tools
For system health → use skippy CLI
```

**3rd: Check Skippy Scripts (328 scripts)**
```
Search: ls /home/dave/skippy/scripts/*/ | grep [keyword]
Might exist already in one of the categories
```

**4th: Write New Code**
```
One-off tasks → bash commands
Reusable tasks → create new script
Complex tasks → use utilities API as base
```

---

## Examples

### Example 1: Find Duplicate Files

**Request:** "Find duplicates in Downloads"

**Decision Process:**
```
1. Common task? YES
2. Category? File Management
3. Tool exists? YES
   - utilities find-duplicates
   - skippy-tools duplicate_cleaner
4. Which to use?
   - utilities: More features, web dashboard, database tracking
   - skippy-tools: Simpler, GUI interface
5. Choice: utilities (more comprehensive)
```

**Selected:**
```bash
utilities find-duplicates ~/Downloads
```

### Example 2: WordPress Deployment

**Request:** "Deploy rundaverun website"

**Decision Process:**
```
1. Common task? YES
2. Category? WordPress/Campaign
3. Tool exists? YES
   - pre_deployment_validator_v1.0.0.sh
4. Appropriate? EXACT MATCH
5. Choice: Use WordPress deployment scripts
```

**Selected:**
```bash
cd /home/dave/rundaverun/campaign
bash skippy-scripts/wordpress/pre_deployment_validator_v1.0.0.sh
bash deploy-to-godaddy.sh
ssh godaddy 'cd ~/html && bash post-deployment-setup.sh'
bash skippy-scripts/wordpress/deployment_verification_v1.0.0.sh
```

### Example 3: Security Scan Before Commit

**Request:** "Make sure no secrets in code before committing"

**Decision Process:**
```
1. Common task? YES
2. Category? Security
3. Tool exists? YES
   - pre_commit_security_scan_v1.0.0.sh
4. Appropriate? EXACT MATCH
5. Choice: Use security scan
```

**Selected:**
```bash
bash ~/skippy-tools/utility/pre_commit_security_scan_v1.0.0.sh
```

### Example 4: Custom Campaign Analysis

**Request:** "Analyze campaign budget vs actual city budget and create comparison report"

**Decision Process:**
```
1. Common task? NO (campaign-specific analysis)
2. Category? Custom analysis
3. Tool exists? NO
4. Appropriate to create? YES (one-off)
5. Choice: Write new code
```

**Selected:**
```python
# Write custom Python script to:
# 1. Read campaign budget
# 2. Fetch city budget data
# 3. Compare line items
# 4. Generate markdown report
```

### Example 5: Organize Scanned Documents

**Request:** "Organize my scanned documents into categories"

**Decision Process:**
```
1. Common task? YES
2. Category? File Management/Document Organization
3. Tool exists? YES
   - utilities organize
   - utilities scan-organizer (migrated)
4. Appropriate? EXACT MATCH
5. Choice: utilities organize
```

**Selected:**
```bash
# Test first
utilities organize ~/Scans/Incoming --dry-run

# Then run for real
utilities organize ~/Scans/Incoming --verbose
```

### Example 6: Check All Repos for Updates

**Request:** "Check eboncorp repos for upgrades"

**Decision Process:**
```
1. Common task? YES
2. Category? Git/Repository Management
3. Tool exists? PARTIAL
   - Can use git commands
   - No dedicated script for multi-repo check
4. Appropriate to write? YES (will reuse)
5. Choice: Write reusable script
```

**Selected:**
```bash
# Write and save for future use
for repo in ~/skippy ~/rundaverun ~/utilities; do
    cd $repo
    echo "=== $(basename $repo) ==="
    git fetch
    git log HEAD..origin/master --oneline
done
```

---

## When to Write New Code

### Write Inline Commands For:
✅ One-off tasks
✅ Quick file operations
✅ Status checks
✅ Simple searches

**Example:**
```bash
find ~/Documents -name "*.pdf" -mtime -7
grep -r "TODO" ~/skippy/scripts/
```

### Write New Scripts For:
✅ Reusable workflows
✅ Complex multi-step processes
✅ Tasks that will be repeated
✅ Integration between tools

**Example:**
```bash
# Create: ~/skippy/scripts/maintenance/weekly_maintenance.sh
# Combines: Docker cleanup, duplicate scan, update checks, health checks
```

### Use Utilities API For:
✅ Document processing tasks
✅ File organization workflows
✅ Custom categorization logic
✅ Building on existing framework

**Example:**
```python
from utilities.organizers import BaseOrganizer

class CampaignDocOrganizer(BaseOrganizer):
    def get_category(self, file_path):
        # Custom logic for campaign documents
        pass
```

---

## Tool Comparison

### Duplicate File Detection

**Option 1: utilities find-duplicates**
- Pros: Comprehensive, database tracking, web dashboard, undo support
- Cons: Requires Python package install
- Use when: Need full features, audit trail, web interface

**Option 2: skippy-tools duplicate_cleaner.py**
- Pros: Standalone, GUI interface, simple
- Cons: No database, no undo
- Use when: Quick cleanup, prefer GUI

**Option 3: skippy-tools quick_duplicate_finder.py**
- Pros: Fast (size-based pre-filter), simple output
- Cons: Less comprehensive
- Use when: Quick scan for obvious duplicates

### WordPress Health Check

**Option 1: wordpress_health_check_v1.0.0.sh**
- Pros: Comprehensive, campaign-specific checks
- Cons: WordPress-specific only
- Use when: Checking rundaverun website

**Option 2: skippy wordpress health**
- Pros: Quick status, integration with skippy
- Cons: Less detailed
- Use when: Quick health check

### File Organization

**Option 1: utilities organize**
- Pros: Modern, tested, configurable, dry-run mode, database tracking
- Cons: Requires utilities package
- Use when: Ongoing document management

**Option 2: Legacy scripts (scan_organizer.py, etc.)**
- Pros: Standalone, simple
- Cons: Older code, less features, code duplication
- Use when: Utilities not available (shouldn't happen)

---

## User Override Options

You can always override tool selection:

**"Use existing tools only"**
```
Claude will search harder for existing solutions
Won't write new code
Will adapt existing tools if needed
```

**"Write new code"**
```
Claude will write fresh code
Won't use existing scripts
Useful for learning or custom requirements
```

**"Use utilities package"**
```
Claude will use utilities API
Even if simpler tools exist
Good for consistency
```

**"Just use bash commands"**
```
Claude will use simple bash
No scripts or packages
Quick and dirty approach
```

---

## Search Strategy

### Before Writing New Code

**Step 1: Search skippy scripts**
```bash
find /home/dave/skippy/scripts -name "*duplicate*"
find /home/dave/skippy/scripts -name "*organize*"
grep -r "function_name" /home/dave/skippy/scripts/
```

**Step 2: Check skippy-tools**
```bash
ls /home/dave/skippy-tools/automation/
ls /home/dave/skippy-tools/utility/
```

**Step 3: Check utilities**
```bash
utilities --help
utilities scripts list
```

**Step 4: Check skippy CLI**
```bash
skippy --help
skippy scripts search [keyword]
```

---

## Integration Workflow

### Combining Multiple Tools

**Example: Complete Deployment Workflow**
```bash
# 1. Pre-deployment validation (WordPress script)
bash ~/rundaverun/campaign/skippy-scripts/wordpress/pre_deployment_validator_v1.0.0.sh

# 2. Security scan (skippy-tools)
bash ~/skippy-tools/utility/pre_commit_security_scan_v1.0.0.sh

# 3. Deploy (custom script)
bash ~/rundaverun/campaign/deploy-to-godaddy.sh

# 4. Post-deployment verification (WordPress script)
bash ~/rundaverun/campaign/skippy-scripts/wordpress/deployment_verification_v1.0.0.sh

# 5. Health check (skippy CLI)
skippy wordpress health
```

**Example: File Organization + Cleanup**
```bash
# 1. Find duplicates (utilities)
utilities find-duplicates ~/Documents > ~/duplicates_report.txt

# 2. Organize remaining files (utilities)
utilities organize ~/Documents --dry-run
utilities organize ~/Documents  # after review

# 3. Docker cleanup (skippy-tools)
bash ~/skippy-tools/utility/docker_cleanup_v1.0.0.sh
```

---

## Best Practices

### DO:
✅ Check for existing tools first
✅ Use specialized tools when available
✅ Prefer tested, versioned scripts
✅ Combine tools for workflows
✅ Document new tools for future use

### DON'T:
❌ Reinvent existing tools
❌ Write new code without searching first
❌ Use deprecated tools when modern versions exist
❌ Skip testing existing tools
❌ Forget to version new scripts

---

## Quick Reference

### Tool Selection Cheat Sheet

| Task | First Choice | Alternative | Write New |
|------|-------------|-------------|-----------|
| WordPress deploy | skippy-scripts | skippy CLI | Rarely |
| Find duplicates | utilities | skippy-tools | Never |
| Git security | pre_commit_security_scan | Manual grep | Never |
| Docker cleanup | docker_cleanup.sh | Docker commands | Never |
| Organize docs | utilities organize | Legacy scripts | Rarely |
| Health check | skippy health | Custom checks | Sometimes |
| Custom analysis | - | - | Always |
| One-off task | Bash commands | - | As needed |

---

## Version History

**1.0.0 (2025-11-06)**
- Initial protocol creation
- Defined decision tree
- Documented all tool categories
- Added examples and comparison tables

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
