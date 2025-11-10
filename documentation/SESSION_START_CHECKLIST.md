# Session Start Checklist

**Purpose:** Run this checklist at the start of EVERY Claude Code session
**Location:** `/home/dave/skippy/documentation/SESSION_START_CHECKLIST.md`

---

## 📋 Pre-Session Checklist

### 1. Understand the Task
- [ ] User stated clear goal
- [ ] I understand what needs to be done
- [ ] I know which project (rundaverun, skippy, general)
- [ ] I know the scope (quick task vs multi-step project)

### 2. Identify Environment
- [ ] Know which WordPress site (if applicable):
  - [ ] **Local:** rundaverun-local (for testing)
  - [ ] **Production:** rundaverun (for approved changes only)
- [ ] Verified site with: `wp option get siteurl`

### 3. Check for Existing Resources
- [ ] Searched for existing scripts (if creating scripts):
  ```bash
  find /home/dave/skippy/scripts -name "*keyword*"
  ```
- [ ] Checked recent conversation files (if continuing work):
  ```bash
  ls -lt /home/dave/skippy/conversations/ | head -10
  ```
- [ ] Reviewed related protocols:
  - [ ] WordPress update? → `wordpress_content_update_protocol.md`
  - [ ] Numbers/claims? → `fact_checking_protocol.md`
  - [ ] Debugging? → `diagnostic_debugging_protocol.md`

### 4. Plan Session Structure
- [ ] Will this task take 30+ minutes? (If yes, use TodoWrite)
- [ ] Will I be modifying files? (If yes, create session directory)
- [ ] Will I be updating WordPress content? (If yes, follow 7-step process)
- [ ] Will I need to generate a report? (If yes, plan report content)

### 5. Prepare Session Directory (If Modifying Files)
- [ ] Determined session description
- [ ] Created session directory:
  ```bash
  SESSION_DIR="/home/dave/skippy/work/{project}/{subproject}/$(date +%Y%m%d_%H%M%S)_description"
  mkdir -p "$SESSION_DIR"
  ```
- [ ] Reported session directory to user

---

## 🎯 Task-Specific Checklists

### If WordPress Content Update:
- [ ] Reviewed WordPress Content Update Protocol
- [ ] Checked QUICK_FACTS_SHEET.md location (if updating numbers)
- [ ] Decided local vs production
- [ ] Created session directory
- [ ] Ready to follow 7-step process

### If Fact-Checking Required:
- [ ] Located QUICK_FACTS_SHEET.md
- [ ] Identified numbers to verify
- [ ] Ready to create FACT_CHECK_LOG.md

### If Debugging/Diagnostic:
- [ ] Reviewed Diagnostic & Debugging Protocol
- [ ] Know which diagnostic script to run
- [ ] Created debug session directory
- [ ] Ready to document issue description

### If Creating Script:
- [ ] Searched existing 179 scripts first
- [ ] Determined no existing script meets need
- [ ] Planned script name (lowercase_with_underscores_v1.0.0.sh)
- [ ] Know which category directory

---

## ⚠️ Critical Reminders

### ALWAYS:
- ✅ Use `/home/dave/skippy/work/` for ALL intermediate files
- ✅ Save `_before` state before any changes
- ✅ Save `_after` state to verify updates
- ✅ Run `diff` to verify updates succeeded
- ✅ Create README.md documenting changes
- ✅ Check QUICK_FACTS_SHEET.md for any numbers

### NEVER:
- ❌ Use `/tmp/` for work files
- ❌ Skip verification step (Step 6)
- ❌ Copy numbers from existing WordPress pages
- ❌ Make production changes without local testing first
- ❌ Assume updates succeeded without verification

---

## 📝 Quick Start Commands

```bash
# Check which WordPress site
wp option get siteurl

# Create WordPress session directory (local)
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"
echo "Session: $SESSION_DIR"

# Create WordPress session directory (production)
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"
echo "Session: $SESSION_DIR"

# Search for existing scripts
find /home/dave/skippy/scripts -name "*keyword*" -type f

# Check recent work
ls -lt /home/dave/skippy/work/wordpress/rundaverun-local/ | head -5
ls -lt /home/dave/skippy/conversations/ | head -10

# View fact sheet
cat /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md
```

---

## 🔄 Session End Checklist

Before ending session:
- [ ] All changes verified
- [ ] README.md created in session directory
- [ ] Report generated (if applicable)
- [ ] Session directory path reported to user
- [ ] No files left in /tmp/
- [ ] All todos completed or documented

---

## 📚 Protocol References

- **CLAUDE.md:** `/home/dave/.claude/CLAUDE.md`
- **Quick Reference:** `/home/dave/skippy/documentation/PROTOCOL_QUICK_REFERENCE.md`
- **All Protocols:** `/home/dave/skippy/documentation/protocols/`
- **This Checklist:** `/home/dave/skippy/documentation/SESSION_START_CHECKLIST.md`

---

**Use this checklist EVERY session to ensure protocol compliance!**
