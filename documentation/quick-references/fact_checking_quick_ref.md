# Fact-Checking - Quick Reference

**Protocol:** [Fact-Checking Protocol](../protocols/fact_checking_protocol.md)
**Priority:** CRITICAL
**Use:** Before publishing ANY number or statistic

---

## 🎯 Master Source of Truth

```
/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/
1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/
assets/markdown-files/QUICK_FACTS_SHEET.md
```

**ALWAYS check here FIRST** before using any number.

---

## Known Correct Data (As of Nov 2025)

### Budget Numbers
- **Total City Budget:** $81M (NOT $80M, NOT $82M)
- **Public Safety Budget:** $77.4M
- **Remaining for Everything Else:** $3.6M

### Education (JCPS)
- **Reading Proficiency:** 34-35% (NOT 44%)
- **Math Proficiency:** 27-28% (NOT 41%)
- **Source:** State assessment data

### Health/Wellness
- **ROI:** $2-3 for every $1 invested
- **Source:** CDC Workplace Health Programs

### Crime Stats
- **Always verify** - changes frequently
- **Source:** LMPD crime statistics

---

## ✅ Fact-Checking Process

### Before Using ANY Number:

```bash
# 1. Search master source
cd /path/to/QUICK_FACTS_SHEET.md
grep -i "search term" QUICK_FACTS_SHEET.md

# 2. If not found, STOP and verify elsewhere
# 3. If found, copy EXACTLY as written
# 4. Document source in FACT_CHECK_LOG.md
```

### Document Your Check:

```markdown
## Fact Check Log - [Date]

### Number: $77.4M (Public Safety Budget)
- **Source:** QUICK_FACTS_SHEET.md line 45
- **Verified:** [Date]
- **Used In:** Policy page, Budget page
- **Status:** ✅ Verified
```

---

## ❌ Common Errors to Avoid

1. **Copying from old WordPress pages**
   - Old pages may have outdated numbers
   - ALWAYS verify against master source

2. **Using rounded numbers**
   - Use exact numbers from source
   - Don't round $77.4M to $77M

3. **Assuming similar pages have same data**
   - Each page may have been updated at different times
   - Verify every instance

4. **Using data from external sources without verification**
   - External sources may be outdated
   - Cross-reference with master source

---

## 🔍 Quick Verification

### Budget Claims
```bash
grep -i "budget" QUICK_FACTS_SHEET.md | grep -i "million"
```

### Education Stats
```bash
grep -i "proficiency\|JCPS\|reading\|math" QUICK_FACTS_SHEET.md
```

### Public Safety
```bash
grep -i "public safety\|police\|fire" QUICK_FACTS_SHEET.md
```

---

## 📝 When Adding New Data

1. Verify with authoritative source
2. Add to QUICK_FACTS_SHEET.md
3. Document source and date
4. Update related pages
5. Note in changelog

---

## 🚨 Red Flags

These should trigger immediate fact-check:
- Numbers that seem too round (exactly 80, 100, etc.)
- Percentages over 50% for education stats
- Budget numbers not in millions
- Claims without sources
- Data older than 6 months

---

## Emergency Fact-Check

If you're unsure and need to publish:

1. **Mark as preliminary**: "[Approximately X]" or "[Estimated]"
2. **Add note**: "Pending verification"
3. **Create task**: Verify before next update
4. **Document**: Note in FACT_CHECK_LOG.md

---

**Full Protocol:** documentation/protocols/fact_checking_protocol.md
**Master Source:** QUICK_FACTS_SHEET.md
**Related:** wordpress_content_update_protocol.md
