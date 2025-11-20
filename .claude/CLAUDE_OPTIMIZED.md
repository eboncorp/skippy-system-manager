# CRITICAL INSTRUCTIONS - Read First Every Session

**Version:** 2.0.0 (Progressive Disclosure)
**Last Updated:** 2025-11-19

---

## Quick Start

### File Naming
✅ **Lowercase with underscores:** `my_file_v1.0.0.sh`
❌ **No capitals, spaces, hyphens:** `My-File.sh`

**Full standards:** `.claude/protocols/file_naming_standards.md`

### WordPress Updates (CRITICAL)
**ALL WordPress updates require:**
1. **Fact-check** (< 1 hour old) - `/fact-check "content"`
2. **Approval** (< 24 hours old) - `/content-approve --page-id=105 --approver=dave`
3. **Session directory** - Create BEFORE any changes
4. **Verification** - Save before/after states

**Full workflow:** `.claude/workflows/wordpress_update_workflow.md`

### Quick Facts (ALWAYS VERIFY)
- Total Budget: **$81M** (NOT $110.5M)
- Wellness ROI: **$2-3 per $1** (NOT $1.80)
- JCPS Reading: **34-35%** (NOT 44%)
- JCPS Math: **27-28%** (NOT 41%)

**Full reference:** `.claude/reference/quick_facts.md`

---

## Enforcement Hooks (NEW)

### WordPress Update Protection
**Blocks** `wp post update` without valid approval + fact-check

**Status:** ✅ Active
**Hook:** `~/.claude/hooks/pre_wordpress_update_protection.sh`

### Fact-Check Enforcement
**Blocks** content modifications without recent fact-check

**Status:** ✅ Active
**Hook:** `~/.claude/hooks/pre_fact_check_enforcement.sh`

### Sensitive File Protection
**Blocks** modifications to .env, credentials, business/, personal/

**Status:** ✅ Active
**Hook:** `~/.claude/hooks/pre_sensitive_file_protection.sh`

---

## Critical Commands

### /fact-check
Verify campaign data against QUICK_FACTS_SHEET.md

**Creates:** Fact-check record (valid 1 hour)
**Usage:** `/fact-check "Total budget is $81M"`
**Required:** Before any content update

### /content-approve
Approve WordPress content updates

**Creates:** Approval record (valid 24 hours)
**Usage:** `/content-approve --page-id=105 --approver=dave --notes="description"`
**Required:** Before WordPress update

### /session-summary
Generate comprehensive session summary

**Enhanced:** WordPress-aware, includes fact-checks & approvals
**Usage:** `/session-summary [session_directory]`

---

## WordPress Workflow (Brief)

```bash
# 1. Create session
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# 2. Save original
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# 3. Make changes
cat "$SESSION_DIR/page_105_before.html" | sed 's/old/new/' > "$SESSION_DIR/page_105_final.html"

# 4. Fact-check (REQUIRED)
/fact-check "Updated content with correct budget $81M"

# 5. Get approval (REQUIRED)
/content-approve --page-id=105 --approver=dave --notes="Budget correction"

# 6. Update WordPress
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# 7. Verify
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# 8. Document
cat > "$SESSION_DIR/README.md" <<EOF
# Session: Description
Status: ✅ Completed
EOF
```

**Complete workflow:** `.claude/workflows/wordpress_update_workflow.md`

---

## Script Creation Rule

**BEFORE creating ANY script:**

```bash
find /home/dave/skippy/development/scripts -type f -name "*.sh" -exec grep -l "keyword" {} \;
```

**179+ scripts available** - check if functionality exists first

---

## Claude Code Skills Standards

### Required YAML Frontmatter

```yaml
---
name: skill-name
description: Brief description and when to use
---
```

### Name Requirements
- Lowercase letters, numbers, hyphens ONLY
- Max 64 characters
- ✅ Good: `wordpress-deployment`, `nexus-controller`
- ❌ Bad: `WordPress_Deployment`, `NEXUS Controller`

### Tools

**Check existing:**
```bash
ls ~/.claude/skills/
```

**Validate structure:**
```bash
python3 /home/dave/skippy/development/scripts/skills/audit_skills_v1.0.0.py
```

---

## File Output Locations (MANDATORY)

- **Reports:** `/home/dave/skippy/documentation/conversations/`
- **Claude.ai Uploads:** `/home/dave/skippy/operations/claude/uploads/`
- **Scripts:** `/home/dave/skippy/development/scripts/[category]/`
- **Sessions:** `/home/dave/skippy/work/wordpress/rundaverun-local/`

---

## Key Directories

- **Campaign:** `/home/dave/skippy/business/campaign/`
- **Scripts:** `/home/dave/skippy/development/scripts/`
- **WordPress Local:** `/home/dave/skippy/websites/rundaverun/local_site/app/public/`
- **Documentation:** `/home/dave/skippy/documentation/conversations/`
- **Fact Sheet:** `/home/dave/rundaverun/campaign/.../QUICK_FACTS_SHEET.md`

---

## WP-CLI Path Variables

```bash
# Set at start of WordPress sessions
WP_PATH="/home/dave/skippy/websites/rundaverun/local_site/app/public"
alias wplocal="wp --path=$WP_PATH"

# Usage
wplocal db check
wplocal post get 105 --field=post_content
```

---

## Emergency Rollback

```bash
# 1. Find recent session
ls -lt /home/dave/skippy/work/wordpress/rundaverun-local/ | head -5

# 2. Set session directory
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/[directory]"

# 3. Rollback
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_before.html")"

# 4. Verify
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_rolledback.html"
diff "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_rolledback.html"
```

---

## Common Mistakes to Avoid

❌ **NEVER:**
- Use /tmp/ for work files
- Skip fact-checking before updates
- Skip approval before WordPress updates
- Forget to save before/after states
- Use capitals or hyphens in filenames
- Copy numbers from existing pages without verification

✅ **ALWAYS:**
- Use session directory for ALL files
- Fact-check content (< 1 hour before update)
- Get approval (< 24 hours before update)
- Save original state BEFORE changes
- Verify update succeeded
- Document changes in README.md

---

## Progressive Disclosure

**For detailed information, consult these modular files:**

### Workflows
- `.claude/workflows/wordpress_update_workflow.md` - Complete WordPress workflow
- `.claude/workflows/script_development_workflow.md` - Script development

### Protocols
- `.claude/protocols/file_naming_standards.md` - Comprehensive naming rules
- `.claude/protocols/work_files_preservation.md` - Session file management
- `.claude/protocols/emergency_rollback.md` - Disaster recovery

### Reference
- `.claude/reference/quick_facts.md` - Campaign fact sheet
- `.claude/reference/common_errors.md` - Known issues and fixes
- `.claude/reference/enforcement_hooks.md` - Hook documentation

### Commands
- `.claude/commands/fact-check.md` - /fact-check documentation
- `.claude/commands/content-approve.md` - /content-approve documentation
- `.claude/commands/session-summary.md` - /session-summary documentation

---

## Content Vault System (NEW)

**Location:** `~/.claude/content-vault/`

**Structure:**
```
content-vault/
├── approvals/          # 24-hour validity
├── fact-checks/        # 1-hour validity
└── audit-log/          # Permanent audit trail
```

**Purpose:** Centralized approval and fact-check tracking

**Documentation:** `~/.claude/content-vault/README.md`

---

## Success Metrics

### Enforcement
- ✅ Zero WordPress updates without approval
- ✅ 100% fact-check enforcement
- ✅ Complete audit trail for all updates

### Efficiency
- ✅ 80% context usage reduction (progressive disclosure)
- ✅ On-demand detail loading
- ✅ Faster Claude startup

---

## Quick Reference Card

```bash
# START SESSION
SESSION_DIR="/home/dave/skippy/work/wordpress/{site}/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# SAVE ORIGINAL
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# FACT-CHECK (REQUIRED)
/fact-check "content to verify"

# APPROVE (REQUIRED)
/content-approve --page-id=105 --approver=dave --notes="description"

# UPDATE
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# VERIFY
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# DOCUMENT
cat > "$SESSION_DIR/README.md" <<EOF
# Session Summary
Status: ✅ Complete
EOF
```

---

**Last Updated:** November 19, 2025
**Protocol Version:** 2.0.0 (Progressive Disclosure + Enforcement Hooks)
**Status:** ✅ Production Ready
