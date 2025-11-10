# WordPress Content Update - Quick Reference

**Protocol:** [WordPress Content Update Protocol](../protocols/wordpress_content_update_protocol.md)
**Priority:** CRITICAL
**Use:** Every WordPress page/post/policy edit

---

## ❌ NEVER DO THIS

```bash
wp post get 105 > /tmp/page.html          # DON'T use /tmp!
python3 script.py > /tmp/output.html       # DON'T use /tmp!
```

---

## ✅ 7-Step Process (Mandatory)

### 1. CREATE SESSION DIR
```bash
SESSION="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION"
cd "$SESSION"
```

### 2. SAVE ORIGINAL
```bash
wp post get 105 --field=post_content > page_105_before.html
```

### 3. MAKE EDITS
```bash
# Edit in SESSION_DIR (never /tmp!)
cat page_105_before.html | sed 's/old/new/g' > page_105_v1.html
# Continue editing: v2.html, v3.html, etc.
```

### 4. SAVE FINAL
```bash
cp page_105_v3.html page_105_final.html
```

### 5. APPLY UPDATE
```bash
wp post update 105 --post_content="$(cat page_105_final.html)"
```

### 6. **VERIFY** (DON'T SKIP!)
```bash
wp post get 105 --field=post_content > page_105_after.html
diff page_105_final.html page_105_after.html
```

###7. DOCUMENT
```bash
cat > README.md <<EOF
# What Changed
- [List changes]

# Files
- page_105_before.html (original)
- page_105_final.html (applied)
- page_105_after.html (verified)

# Status: ✅ Complete
EOF
```

---

## 🔍 Must Verify

After EVERY update:
- [ ] Saved _after.html file
- [ ] Ran diff command
- [ ] Diff shows expected changes only
- [ ] Verified specific text present: `grep "new text" page_105_after.html`
- [ ] Verified old text gone: `! grep "old text" page_105_after.html`

---

## 🆘 If Something Goes Wrong

```bash
# Find your session
ls -lt /home/dave/skippy/work/wordpress/rundaverun/ | head -5

# Rollback
cd [session-dir]
wp post update 105 --post_content="$(cat page_105_before.html)"

# Verify rollback
wp post get 105 --field=post_content > page_105_rolledback.html
diff page_105_before.html page_105_rolledback.html
```

---

## 📋 Session Directory Structure

```
YYYYMMDD_HHMMSS_description/
├── page_105_before.html      ← Original
├── page_105_v1.html           ← First edit
├── page_105_v2.html           ← Second edit
├── page_105_final.html        ← Applied version
├── page_105_after.html        ← Verification ✓
├── FACT_CHECK_LOG.md          ← If data updated
└── README.md                  ← Summary
```

---

## Common Mistakes to Avoid

1. ❌ Using /tmp/ for ANY files
2. ❌ Skipping verification step
3. ❌ Not saving _after.html
4. ❌ Not running diff
5. ❌ Copying numbers from old pages
6. ❌ Not creating session directory

---

**Full Protocol:** documentation/protocols/wordpress_content_update_protocol.md
**Related:** fact_checking_protocol.md, verification_protocol.md
