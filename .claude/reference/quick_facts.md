# Quick Facts Reference

**Last Updated:** 2025-11-19
**Master Source:** QUICK_FACTS_SHEET.md

---

## Campaign Data (ALWAYS VERIFY BEFORE USE)

### Budget
- **Total Budget:** $81M (NOT $110.5M)
- **Public Safety Budget:** $77.4M
- **Campaign Budget:** $1.2B

### Wellness & Health
- **Wellness Center ROI:** $2-3 per $1 spent (NOT $1.80)

### Education (JCPS)
- **Reading Proficiency:** 34-35% (NOT 44%)
- **Math Proficiency:** 27-28% (NOT 41%)

### Policies
- **Total Policy Documents:** 42
- **Platform Policies:** 16
- **Implementation Policies:** 26

### Biographical
- **Full Name:** Dave Biggers
- **Age:** 41
- **Marital Status:** NOT married
- **Children:** NONE
- **City:** Louisville, KY
- **Office Sought:** Mayor

---

## Commonly Wrong Values (FLAG THESE)

| Topic | ❌ WRONG | ✅ CORRECT |
|-------|----------|-----------|
| Budget | $110.5M or $110M | $81M |
| Wellness ROI | $1.80 or $1.8 | $2-3 per $1 |
| JCPS Reading | 44% or 45% | 34-35% |
| JCPS Math | 41% or 40% | 27-28% |
| Marital Status | "married" or "wife" | NOT married |
| Children | Any mention | NO children |

---

## Fact-Check Protocol

**BEFORE using ANY number:**
1. Check QUICK_FACTS_SHEET.md
2. Run /fact-check command
3. Get approval if publishing
4. Document source in session README

**Master Source:**
```
/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/
1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/
QUICK_FACTS_SHEET.md
```

---

## Quick Verification Commands

```bash
# Set fact sheet path
FACT_SHEET="/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md"

# Check specific facts
grep -i "total.*budget" "$FACT_SHEET"
grep -i "wellness.*roi" "$FACT_SHEET"
grep -i "jcps.*reading" "$FACT_SHEET"
grep -i "jcps.*math" "$FACT_SHEET"
```

---

**CRITICAL:** Never copy numbers from existing WordPress pages. Always verify against QUICK_FACTS_SHEET.md.
