# Protocol Quick Reference Card

**Version:** 1.0.0
**Last Updated:** 2025-11-08
**Purpose:** One-page cheat sheet for critical protocols

---

## 🚨 NEVER DO THIS

```bash
❌ python3 script.py > /tmp/output.html
❌ wp post get 105 > /tmp/page.html
❌ echo "data" > /tmp/temp.txt
❌ Copy numbers from existing WordPress pages
❌ Skip verification step after updates
❌ Make production changes without testing locally first
```

---

## ✅ WordPress Update (7 Steps)

```bash
# 1. CREATE SESSION
SESSION_DIR="/home/dave/skippy/work/wordpress/{site}/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION_DIR"

# 2. SAVE ORIGINAL
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_before.html"

# 3. CREATE EDITS
cat "$SESSION_DIR/page_105_before.html" | sed 's/old/new/g' > "$SESSION_DIR/page_105_v1.html"

# 4. SAVE FINAL
cp "$SESSION_DIR/page_105_v1.html" "$SESSION_DIR/page_105_final.html"

# 5. APPLY UPDATE
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_final.html")"

# 6. VERIFY (CRITICAL!)
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_after.html"
diff "$SESSION_DIR/page_105_final.html" "$SESSION_DIR/page_105_after.html"

# 7. DOCUMENT
cat > "$SESSION_DIR/README.md" <<EOF
# What Changed
...
EOF
```

---

## 📊 Fact-Checking (CRITICAL)

**Master Source of Truth:**
```
/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md
```

**Always check BEFORE using any number:**
```bash
grep -i "search term" QUICK_FACTS_SHEET.md
```

**Known Data (as of Nov 2025):**
- Total Budget: $81M
- Public Safety: $77.4M
- Wellness ROI: $2-3 per $1
- JCPS Reading: 34-35% (NOT 44%)
- JCPS Math: 27-28% (NOT 41%)

---

## ✓ Verification Checklist

After EVERY WordPress update:
- [ ] Saved `_after.html` file
- [ ] Ran `diff final.html after.html`
- [ ] Verified specific text present: `grep "text" after.html`
- [ ] Checked old text removed
- [ ] No errors in output

---

## 🔄 Local vs Production

**ALWAYS test on LOCAL first:**
```
rundaverun-local (Local Sites/rundaverun-local/app/public/)
```

**ONLY deploy to PRODUCTION after:**
- ✅ Tested locally
- ✅ Verified works
- ✅ Fact-checked all data
- ✅ Created backup

---

## 📝 Report Generation

**Location:** `/home/dave/skippy/conversations/`
**Naming:** `{topic}_{YYYY-MM-DD}.md`

**Required Sections:**
1. Summary (2-4 sentences)
2. What Was Changed
3. Files Modified
4. Status (✅⚠️❌)
5. Next Steps (if applicable)

---

## 🆘 Emergency Rollback

```bash
# Find session directory
ls -lt /home/dave/skippy/work/wordpress/{site}/ | head -5

# Rollback to original
SESSION_DIR="[found directory]"
wp post update 105 --post_content="$(cat "$SESSION_DIR/page_105_before.html")"

# Verify rollback
wp post get 105 --field=post_content > "$SESSION_DIR/page_105_rolledback.html"
diff "$SESSION_DIR/page_105_before.html" "$SESSION_DIR/page_105_rolledback.html"
```

---

## 🔍 Quick Diagnostic

```bash
# Run full diagnostic
bash /home/dave/skippy/scripts/wordpress/wordpress_comprehensive_diagnostic_v1.3.0.sh

# Check for errors
grep -E "ERROR|WARNING|FAIL" diagnostic_output.txt

# Check specific page
wp post get 105 --field=post_content | wc -c  # Should be > 100
```

---

## 📂 Session Directory Structure

```
/home/dave/skippy/work/wordpress/{site}/YYYYMMDD_HHMMSS_description/
├── resource_id_before.html      ← Original state
├── resource_id_v1.html           ← First edit
├── resource_id_v2.html           ← Second edit (if needed)
├── resource_id_final.html        ← Final version to apply
├── resource_id_after.html        ← Actual state after update ✓
├── FACT_CHECK_LOG.md             ← If numbers updated
└── README.md                     ← What changed
```

---

## 🎯 Pre-Flight Checklist

Before completing ANY file edit:
- [ ] Created SESSION_DIR
- [ ] Saved _before file
- [ ] Saved iterations (v1, v2, etc.)
- [ ] Saved _final file
- [ ] Applied changes
- [ ] **Saved _after file** ← DON'T SKIP
- [ ] **Ran diff** ← DON'T SKIP
- [ ] Created README.md
- [ ] **NO /tmp/ usage**

---

## 📞 Protocol Locations

- **Full CLAUDE.md:** `/home/dave/.claude/CLAUDE.md`
- **All Protocols:** `/home/dave/skippy/documentation/protocols/`
- **WordPress Update:** `protocols/wordpress_content_update_protocol.md`
- **Fact-Checking:** `protocols/fact_checking_protocol.md`
- **Verification:** `protocols/verification_protocol.md`
- **This Card:** `/home/dave/skippy/documentation/PROTOCOL_QUICK_REFERENCE.md`

---

**Print this card and keep nearby!**
**Or bookmark this file for quick access.**
