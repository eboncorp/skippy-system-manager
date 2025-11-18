# CRITICAL INSTRUCTIONS - Read First Every Session

## File & Script Naming Standards

**All files and directories:** lowercase with underscores (no capitals, no spaces)
- ✅ Good: `budget_update_v1.0.0.sh`
- ❌ Bad: `Budget-Update.sh`

**File naming convention:** `{purpose}_{specific_task}_v{version}.{ext}`

**Semantic versioning:** Always use (v1.0.0, v1.1.0, etc.)

## Script Creation Rule
**BEFORE creating ANY script:**
```bash
find /home/dave/skippy/development/scripts -type f -name "*.sh" -exec grep -l "keyword" {} \;
```
**Available scripts:** 179 scripts in `/home/dave/skippy/development/scripts/`

Check if similar functionality already exists.

## Claude Code Skills Creation Standards

**CRITICAL:** All skills MUST have proper YAML frontmatter.

### Required Structure

Every SKILL.md must start with YAML frontmatter:

```yaml
---
name: skill-name
description: Brief description of what this skill does and when Claude should use it
---
```

### Field Requirements

**name:**
- Lowercase letters, numbers, and hyphens ONLY
- Max 64 characters
- No spaces, underscores, or capitals
- ✅ Good: `wordpress-deployment`, `nexus-controller`
- ❌ Bad: `WordPress_Deployment`, `NEXUS Controller`

**description:**
- Clear explanation of what the skill does AND when to use it
- Max 1024 characters
- Should include trigger keywords
- ✅ Good: `Manages WordPress deployment and content updates. Use when user mentions updating WordPress pages, posts, or site content.`
- ❌ Bad: `WordPress stuff`

### Skill Creation Tools

**Check existing skills:**
```bash
ls ~/.claude/skills/
```

**Validate skill structure:**
```bash
python3 /home/dave/skippy/development/scripts/skills/audit_skills_v1.0.0.py
```

**Convert script to skill:**
```bash
python3 /home/dave/skippy/development/scripts/skills/convert_script_to_skill_v1.0.0.py /path/to/script.py
```

### Skill Template

```markdown
---
name: my-skill-name
description: What this skill does and when to invoke it
---

# My Skill Name

## When to Use This Skill

Auto-invoke when:
- User mentions [trigger keywords]
- Working with [specific tasks]
- Need to [primary function]

## Quick Start

[Basic usage instructions]

## Examples

[Concrete examples]

## Troubleshooting

[Common issues and solutions]
```

### Best Practices

1. **Name matching:** Skill directory name must match YAML `name:` field
2. **Rich descriptions:** Include trigger keywords so Claude knows when to use it
3. **Progressive disclosure:** Put essentials in SKILL.md, details in separate files
4. **Include examples:** Concrete usage examples help Claude understand
5. **Validate after creation:** Run audit tool to verify structure

## File Output Locations (MANDATORY)
- **Reports & Analyses:** `/home/dave/skippy/documentation/conversations/`
- **Claude.ai Upload Files:** `/home/dave/skippy/operations/claude/uploads/`
- **Upload Protocol:** `/home/dave/skippy/operations/claude/UPLOAD_PROTOCOL.md`
- **Scripts:** `/home/dave/skippy/development/scripts/[category]/`

## Key Directories (REORGANIZED 2025-11-18)
- **Campaign:** `/home/dave/skippy/business/campaign/`
- **Scripts:** `/home/dave/skippy/development/scripts/`
- **WordPress Local (ACTIVE):** `/home/dave/skippy/websites/rundaverun/local_site/app/public/`
- **Documentation:** `/home/dave/skippy/documentation/conversations/`
- **Protocols:** `/home/dave/skippy/documentation/protocols/`

**⚠️ CRITICAL:** Always verify WordPress installation path before WP-CLI operations!
- Local by Flywheel sites use `/home/dave/skippy/websites/rundaverun/local_site/`
- Check `~/.config/Local/sites.json` for actual path if unsure

---

## WP-CLI Path Variables

Set these at start of WordPress sessions to simplify commands and prevent path errors:

```bash
# WordPress Local (active site)
WP_PATH="/home/dave/skippy/websites/rundaverun/local_site/app/public"
alias wplocal="wp --path=$WP_PATH"

# Then use throughout session
wplocal db check
wplocal option get siteurl
wplocal post get 105 --field=post_content
wplocal media import image.jpg
```

---

## Fact-Checking (CRITICAL)

**Master Source of Truth:**
```
/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md
```

**ALWAYS verify numbers BEFORE using:**
```bash
# Search for specific data
grep -i "budget" QUICK_FACTS_SHEET.md
grep -i "wellness" QUICK_FACTS_SHEET.md
grep -i "JCPS" QUICK_FACTS_SHEET.md
```

**Known Key Data (as of November 2025):**
- **Total Budget:** $81M (NOT $110.5M)
- **Public Safety Budget:** $77.4M
- **Wellness Center ROI:** $2-3 per $1 spent (NOT $1.80)
- **JCPS Reading Proficiency:** 34-35% (NOT 44%)
- **JCPS Math Proficiency:** 27-28% (NOT 41%)

**❌ NEVER:**
- Copy numbers from existing WordPress pages
- Use numbers from memory
- Assume numbers are current

**✅ ALWAYS:**
- Check QUICK_FACTS_SHEET.md first
- Document source in session README
- Create FACT_CHECK_LOG.md if updating numbers

---

## Emergency Rollback

**When to use:** Update failed, wrong content published, site broken

```bash
# 1. Find most recent session
ls -lt /home/dave/skippy/work/wordpress/rundaverun-local/ | head -5

# 2. Set session directory
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/[directory_name]"

# 3. Rollback to original state
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_before.html")"

# 4. Verify rollback succeeded
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_rolledback.html"
diff "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_rolledback.html"

# 5. If diff shows no output, rollback successful ✅
```

**For multiple pages:**
```bash
# Rollback several pages at once
for ID in 105 106 107; do
  wp post update $ID --post_content="$(cat "$SESSION_DIR/page_${ID}_before.html")"
  echo "Rolled back page $ID"
done
```

**For database changes:**
```bash
# Restore from database backup
wp db import "$SESSION_DIR/db_full_backup.sql"

# Verify restore
wp db check
```

---

## ⚠️ CRITICAL: Work Files Preservation Protocol

### WHY THIS MATTERS
- `/tmp/` is **CLEARED ON REBOOT** = PERMANENT DATA LOSS
- **EVERY intermediate file** must be in work directory
- **NO EXCEPTIONS** - includes Python temp files, conversion files, diagnostic output

### WHEN TO USE (Always!)
**MANDATORY for:**
- ✅ Every WordPress post/page edit
- ✅ Every file modification
- ✅ Every script development session
- ✅ Every diagnostic/debug session
- ✅ ANY command that creates intermediate files
- ✅ Python conversions, sed/awk operations, ANY temp files

---

## MANDATORY Process: Step 0 Through Step 7

### Step 0: Verify Installation Path (WordPress Work Only)

**ALWAYS verify correct WordPress installation path BEFORE starting:**

```bash
# 1. Check WordPress database connection
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" db check

# 2. Verify site URL matches expectation
wp --path="/home/dave/skippy/rundaverun_local_site/app/public" option get siteurl
# Expected: http://rundaverun-local-complete-022655.local

# 3. For Local by Flywheel, verify active installation path
cat ~/.config/Local/sites.json | python3 -m json.tool | grep -A 5 "rundaverun"
# Look for "path" field - this is the ACTUAL installation location

# 4. Test HTTP accessibility (if site is running)
curl -I "http://rundaverun-local-complete-022655.local" | grep "HTTP/1.1 200"
```

**If verification fails:**
- Check Local by Flywheel app is running and site is started
- Verify correct installation path in Local config
- Check wp-config.php database socket path matches running MySQL

**Document verified path in session README.**

---

### Step 1: Create Session Directory FIRST (Before ANY work)

```bash
# WordPress work (production site)
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# WordPress work (local development)
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# Script development
SESSION_DIR="/home/dave/skippy/work/scripts/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"
```

**Description naming:**
- Use underscores: `homepage_fixes` not `homepage-fixes`
- Be specific: `page_105_wellness_roi_update` not `updates`
- 2-5 words max

### Step 2: Save Original State BEFORE Any Changes

```bash
# WordPress pages
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# WordPress posts
wp post get 941 --field=post_content > "$SESSION_DIR/post_941_before.html"

# Policy documents
wp post get 699 --field=post_content > "$SESSION_DIR/policy_699_before.html"

# Any file
cp /path/to/file "$SESSION_DIR/filename_before.ext"
```

### Step 3: Save Each Iteration

```bash
# First edit
cat "$SESSION_DIR/page_105_before.html" | sed 's/old/new/g' > "$SESSION_DIR/page_105_v1.html"

# Second edit
cat "$SESSION_DIR/page_105_v1.html" | sed 's/foo/bar/g' > "$SESSION_DIR/page_105_v2.html"

# Python conversion (MUST use SESSION_DIR, NOT /tmp/)
python3 << PYEOF > "$SESSION_DIR/page_331_converted.html"
import markdown
with open("$SESSION_DIR/source.md") as f:
    print(markdown.markdown(f.read()))
PYEOF

# ANY intermediate file
echo "temp data" > "$SESSION_DIR/temp_data.txt"  # NOT /tmp/temp_data.txt
```

### Step 4: Save Final Version BEFORE Applying

```bash
# This is the version you're about to apply
cp "$SESSION_DIR/page_105_v2.html" "$SESSION_DIR/page_105_final.html"
```

### Step 5: Apply Changes to Actual System

```bash
# WordPress update
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# File update
cp "$SESSION_DIR/script_final.sh" /actual/location/script.sh

# Database update
wp db query < "$SESSION_DIR/query_final.sql"
```

### Step 6: VERIFY - Save Actual State AFTER Applying

**THIS STEP IS CRITICAL - DO NOT SKIP**

```bash
# A. Database Verification (WordPress content)
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"

# Compare to verify update worked
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# If diff shows differences, INVESTIGATE before proceeding

# B. HTTP Verification (for media uploads, public resources)
# Test that uploaded images are accessible via web server
if [[ -n "$SITE_URL" ]]; then
    # Test a sample image or resource
    curl -I "$SITE_URL/wp-content/uploads/2025/11/sample_image.jpg" | grep "HTTP" >> "$SESSION_DIR/http_verification.log"

    # Should return "HTTP/1.1 200 OK" not "404 Not Found"
    echo "HTTP verification logged to http_verification.log"
fi

# C. Functional Verification (page renders correctly)
# Test that page actually displays correctly
curl -s "$SITE_URL/?p=105" | grep "expected content string" && echo "✅ Page renders correctly" || echo "⚠️  Page render check failed"
```

**Why this matters:**
- **Database verification** catches failed updates and hook/filter modifications
- **HTTP verification** confirms uploaded files are accessible via web server
- **Functional verification** ensures changes actually work as intended
- Provides proof update succeeded at all levels

### Step 7: Document Changes (MANDATORY)

```bash
cat > "$SESSION_DIR/README.md" <<EOF
# Session: {Brief Description}

**Date:** $(date)
**Resources Modified:** Page 105 (Homepage)
**Changes Made:**
- Updated wellness center ROI from \$1.80 to \$2-3
- Fixed budget figure from \$110.5M to \$81M

**Status:** ✅ Completed successfully

**Files:**
- page_105_before.html - Original state
- page_105_v1.html - First edit (ROI fix)
- page_105_v2.html - Second edit (budget fix)
- page_105_final.html - Final version for update
- page_105_after.html - Verified actual state after update

**Verification:**
\`\`\`
diff page_105_final.html page_105_after.html
# (no differences - update successful)
\`\`\`
EOF
```

---

## Complete WordPress Example

```bash
# 1. CREATE SESSION
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_homepage_wellness_roi_fix"
mkdir -p "$SESSION_DIR"
echo "Created session: $SESSION_DIR"

# 2. SAVE ORIGINAL
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# 3. CREATE EDITS
# First fix: Update ROI
cat "$SESSION_DIR/page_105_before.html" | \
  sed 's/\$1\.80/\$2-3/g' > "$SESSION_DIR/page_105_v1.html"

# Second fix: Update budget
cat "$SESSION_DIR/page_105_v1.html" | \
  sed 's/\$110\.5M/\$81M/g' > "$SESSION_DIR/page_105_v2.html"

# 4. SAVE FINAL
cp "$SESSION_DIR/page_105_v2.html" "$SESSION_DIR/page_105_final.html"

# 5. APPLY UPDATE
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# 6. VERIFY (CRITICAL!)
# A. Database verification
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# B. HTTP verification (if applicable)
SITE_URL=$(wp --path="/home/dave/skippy/rundaverun_local_site/app/public" option get siteurl)
curl -I "$SITE_URL" | grep "HTTP" >> "$SESSION_DIR/http_verification.log"

# 7. DOCUMENT
cat > "$SESSION_DIR/README.md" <<EOF
# Homepage Wellness ROI & Budget Fixes
Date: $(date)
Resources: Page 105
Changes: Updated ROI and budget figures
Status: ✅ Verified successful
EOF

# Report to user
echo "✅ Session complete: $SESSION_DIR"
```

---

## Multiple Items Example

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_policy_budget_updates"
mkdir -p "$SESSION_DIR"

# Process each item
for ID in 699 716 717; do
  # Save before
  wp post get $ID --field=post_content > "$SESSION_DIR/policy_${ID}_before.html"

  # Edit
  cat "$SESSION_DIR/policy_${ID}_before.html" | \
    sed 's/old/new/g' > "$SESSION_DIR/policy_${ID}_v1.html"

  # Save final
  cp "$SESSION_DIR/policy_${ID}_v1.html" "$SESSION_DIR/policy_${ID}_final.html"

  # Apply
  wp post update $ID --post_content="$(cat "$SESSION_DIR/policy_${ID}_final.html")"

  # Verify
  wp post get $ID --field=post_content > "$SESSION_DIR/policy_${ID}_after.html"
  diff "$SESSION_DIR/policy_${ID}_final.html" "$SESSION_DIR/policy_${ID}_after.html"
done

# Document
cat > "$SESSION_DIR/README.md" <<EOF
# Policy Budget Updates
Date: $(date)
Policies Modified: 699, 716, 717
Changes: Updated budget figures across all policies
Status: ✅ All verified
EOF
```

---

## Python Conversion Example

```bash
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_markdown_to_html_conversion"
mkdir -p "$SESSION_DIR"

# Copy source markdown
cp /source/policy.md "$SESSION_DIR/policy_source.md"

# Convert (MUST output to SESSION_DIR, NOT /tmp/)
python3 <<PYEOF > "$SESSION_DIR/policy_converted.html"
import markdown
with open("$SESSION_DIR/policy_source.md") as f:
    content = f.read()
html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
print(html)
PYEOF

# Review conversion
cat "$SESSION_DIR/policy_converted.html"

# Apply to WordPress
wp post update 331 --post_content="$(cat "$SESSION_DIR/policy_converted.html")"

# Verify
wp post get 331 --field=post_content > "$SESSION_DIR/policy_331_after.html"

# Document
cat > "$SESSION_DIR/README.md" <<EOF
# Markdown to HTML Conversion
Converted policy.md to HTML for post 331
Status: ✅ Verified
EOF
```

---

## Pre-Flight Checklist (Check EVERY Session)

Before completing ANY file edit task:
- [ ] Created `SESSION_DIR` with timestamp
- [ ] Saved ALL original files with `_before` suffix
- [ ] Saved ALL iterations (`_v1`, `_v2`, etc.)
- [ ] Saved final version with `_final` suffix
- [ ] Applied changes to actual system
- [ ] **Saved `_after` file to VERIFY update**
- [ ] **Ran `diff` to confirm update succeeded**
- [ ] Created `README.md` documenting what changed
- [ ] Reported session directory path to user
- [ ] **NO FILES created in `/tmp/`**

---

## Common Mistakes to Avoid

❌ **NEVER DO THIS:**
```bash
python3 script.py > /tmp/output.html                    # WRONG - uses /tmp/
wp post get 105 --field=post_content > /tmp/page.html   # WRONG - uses /tmp/
wp post update 105 < /tmp/edited.html                   # WRONG - source in /tmp/
echo "data" > /tmp/temp.txt                             # WRONG - uses /tmp/
```

✅ **ALWAYS DO THIS:**
```bash
python3 script.py > "$SESSION_DIR/output.html"          # CORRECT
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"  # CORRECT
wp post update 105 < "$SESSION_DIR/page_105_final.html"  # CORRECT
echo "data" > "$SESSION_DIR/temp_data.txt"              # CORRECT
```

---

## File Naming Standards

| Type | Format | Example |
|------|--------|---------|
| **Pages** | `page_{id}_{stage}.html` | `page_105_before.html` |
| **Posts** | `post_{id}_{stage}.html` | `post_941_v1.html` |
| **Policies** | `policy_{id}_{stage}.html` | `policy_699_final.html` |
| **Scripts** | `script_name_{stage}.sh` | `backup_script_v2.sh` |
| **Temp/Working** | `descriptive_name.ext` | `converted_content.html` |
| **Diagnostic** | `diagnostic_{timestamp}.txt` | `diagnostic_20251108.txt` |

**Stages:** `before`, `v1`, `v2`, `v3`..., `final`, `after`

---

## Retention Policy
- **Active:** 30 days in `/home/dave/skippy/work/`
- **Archive:** 90 additional days (120 days total)
- **Cleanup:** Automatic via cron (3 AM daily)
- **Full Protocol:** `/home/dave/skippy/documentation/WORK_FILES_PRESERVATION_PROTOCOL.md`

---

## Quick Reference Card

```bash
# START EVERY SESSION WITH:
SESSION_DIR="/home/dave/skippy/work/wordpress/{site}/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# SAVE EVERYTHING TO:
"$SESSION_DIR/filename_stage.ext"

# NEVER USE:
/tmp/anything

# END EVERY SESSION WITH:
cat > "$SESSION_DIR/README.md" <<EOF
# What Changed
...
EOF
```

---

**Last Updated:** November 12, 2025
**Protocol Version:** 2.1 (Multi-Installation & Verification Enhanced)
