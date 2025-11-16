# Work Files Preservation - Quick Reference Card

**Print this single page for rapid reference during sessions**

---

## MANDATORY: Start Every Session With This

```bash
# 1. CREATE SESSION DIRECTORY
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# 2. SAVE ORIGINAL STATE BEFORE ANY CHANGES
wp post get [ID] --field=post_content > "$SESSION_DIR/page_[ID]_before.html"
```

---

## The 7-Step Process

| Step | Action | Command Example |
|------|--------|-----------------|
| **1** | Create session dir | `mkdir -p "$SESSION_DIR"` |
| **2** | Save original | `*_before.html` |
| **3** | Save iterations | `*_v1.html`, `*_v2.html` |
| **4** | Save final | `*_final.html` |
| **5** | Apply changes | `wp post update [ID] --post_content="$(cat ...)"` |
| **6** | **VERIFY** | `*_after.html` + `diff` |
| **7** | Document | `README.md` |

---

## File Naming Convention

```
page_[ID]_[stage].html

Stages: before → v1 → v2 → v3 → final → after
```

**Examples:**
- `page_105_before.html` - Original
- `page_105_v1.html` - First edit
- `page_105_final.html` - Ready to apply
- `page_105_after.html` - Verification

---

## CRITICAL: Never Use /tmp/

```bash
# ❌ WRONG - Lost on reboot
python3 script.py > /tmp/output.html

# ✅ CORRECT - Preserved
python3 script.py > "$SESSION_DIR/output.html"
```

---

## Quick Verification

```bash
# After applying update
wp post get [ID] --field=post_content > "$SESSION_DIR/page_[ID]_after.html"
diff "$SESSION_DIR/page_[ID]_final.html" "$SESSION_DIR/page_[ID]_after.html"

# No output = Success ✅
# Output = Something changed ⚠️
```

---

## Emergency Rollback

```bash
# Find latest session
ls -lt /home/dave/skippy/work/wordpress/rundaverun-local/ | head -5

# Restore original
wp post update [ID] --post_content="$(cat "$SESSION_DIR/page_[ID]_before.html")"
```

---

## Session README Template

```markdown
# Session: Brief Description
**Date:** $(date)
**Resources:** Page 105, 106
**Changes:** What was changed
**Status:** ✅ Completed / ⚠️ Partial / ❌ Failed
```

---

## Key Directories

| Purpose | Path |
|---------|------|
| WordPress Local | `/home/dave/skippy/work/wordpress/rundaverun-local/` |
| WordPress Prod | `/home/dave/skippy/work/wordpress/rundaverun/` |
| Scripts | `/home/dave/skippy/work/scripts/` |
| Reports | `/home/dave/skippy/conversations/` |

---

## Pre-Flight Checklist

Before closing session, verify:

- [ ] Session directory created with timestamp
- [ ] All `_before` files saved
- [ ] All iterations saved (`_v1`, `_v2`, etc.)
- [ ] Final version saved (`_final`)
- [ ] Changes applied to system
- [ ] **After state verified (`_after` + diff)**
- [ ] README.md documenting changes
- [ ] **NO files in /tmp/**

---

## Fact-Checking Reminder

```bash
# ALWAYS check before using numbers
grep -i "budget" /home/dave/rundaverun/campaign/.../QUICK_FACTS_SHEET.md
```

**Key Values (Nov 2025):**
- Budget: **$81M** (not $110.5M)
- Wellness ROI: **$2-3** (not $1.80)
- JCPS Reading: **34-35%** (not 44%)

---

**Full Protocol:** `/home/dave/skippy/documentation/protocols/work_files_preservation_protocol_v2.1.md`

**Generated:** 2025-11-16 | **Version:** 1.0.0
