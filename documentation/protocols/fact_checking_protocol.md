# Fact-Checking Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-08
**Owner:** Claude Code / Dave
**Priority:** CRITICAL - Campaign Accuracy

---

## Context

Campaign content must be factually accurate. All numbers, statistics, claims, and data points must be verified against authoritative sources before publication. This protocol ensures data accuracy and maintains campaign credibility.

## Purpose

- Ensure all published numbers are accurate
- Prevent publication of outdated or incorrect data
- Maintain single source of truth for campaign facts
- Enable quick verification during content updates
- Protect campaign credibility

---

## Core Principle

**NEVER copy numbers from existing WordPress content.**

WordPress content may contain outdated, incorrect, or unverified information. Always verify against authoritative sources.

---

## Authoritative Sources (Priority Order)

### 1. QUICK_FACTS_SHEET.md (PRIMARY SOURCE)

**Location:** `/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md`

**This is the master source of truth for:**
- Budget numbers (total budget, department breakdowns)
- Program costs and savings
- Return on investment (ROI) figures
- Timeline information
- Key statistics

**Before using ANY number, check this file first.**

### 2. Policy Documents (SECONDARY SOURCE)

**Location:** `/home/dave/rundaverun/campaign/downloads/policy_documents/*.md`

**Use for:**
- Policy-specific details
- Implementation plans
- Technical specifications
- Program descriptions

**Note:** If numbers conflict between policy docs and QUICK_FACTS_SHEET.md, QUICK_FACTS_SHEET.md takes precedence.

### 3. Original Research/Data (TERTIARY SOURCE)

**For new data not in existing docs:**
- Louisville Open Data Portal: https://data.louisvilleky.gov
- Census Data: https://censusreporter.org
- LMPD Crime Statistics
- Metro Louisville Budget documents

**Always document source when adding new data.**

---

## When to Fact-Check

### MANDATORY Fact-Checking:

✅ **Before EVERY number/statistic publication:**
- Budget figures
- Cost estimates
- ROI calculations
- Population statistics
- Crime statistics
- Timeline dates
- Program participant counts

✅ **When updating existing content:**
- Review ALL numbers, not just the ones changing
- Verify current numbers are still accurate
- Check for newer data

✅ **When creating new content:**
- Verify every claim against sources
- Document source for each fact
- Double-check calculations

### NOT Needed:

❌ **For non-factual content:**
- Personal biographical information (Dave's experience)
- Qualitative descriptions
- Opinion statements
- Vision/values statements

---

## Fact-Checking Workflow

### Step 1: Identify Facts to Verify

```bash
# Extract all numbers from content
grep -oE '\$[0-9]+(\.[0-9]+)?[KMB]?' content.html

# Common patterns to check:
# - Dollar amounts: $81M, $2.5M, $1,200
# - Percentages: 34%, 2-3x
# - Counts: 42 policies, 14 mini substations
# - Dates: December 31, 2025
```

### Step 2: Check QUICK_FACTS_SHEET.md

```bash
# View fact sheet
cat /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md

# Search for specific fact
grep -i "wellness" /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md

# Save reference copy to session directory
cp /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md "$SESSION_DIR/FACT_SHEET_reference.md"
```

### Step 3: Verify Each Fact

**For each number/claim:**

1. **Find in QUICK_FACTS_SHEET.md**
   - Search for the topic/program
   - Locate exact figure
   - Note any caveats or context

2. **If not in QUICK_FACTS_SHEET.md:**
   - Check policy documents
   - Search campaign downloads folder
   - Verify with original source (Louisville data, census, etc.)
   - **Document source in session notes**

3. **If conflicting information found:**
   - QUICK_FACTS_SHEET.md takes precedence
   - If QUICK_FACTS_SHEET.md appears outdated, **ASK USER** before proceeding
   - Document conflict in session notes

### Step 4: Document Sources

```bash
cat > "$SESSION_DIR/FACT_CHECK_LOG.md" <<EOF
# Fact-Checking Log

**Date:** $(date)
**Content:** [Page/Policy being updated]

## Facts Verified

| Fact | Value | Source | Status |
|------|-------|--------|--------|
| Total Budget | \$81M | QUICK_FACTS_SHEET.md | ✅ Verified |
| Wellness ROI | \$2-3 per \$1 | QUICK_FACTS_SHEET.md (updated Oct 2025) | ✅ Verified |
| Mini Substations Count | 14 | Policy document MINI_SUBSTATIONS.md | ✅ Verified |
| [Fact] | [Value] | [Source] | [Status] |

## Conflicts Resolved

- **Old value:** \$1.80 ROI (outdated)
- **New value:** \$2-3 ROI
- **Source:** QUICK_FACTS_SHEET.md updated October 2025
- **Resolution:** Updated to current figure

## New Data Added

- [Any new facts not previously in fact sheet]
- Source: [Where it came from]
- Verification: [How verified]

EOF
```

---

## Common Fact-Checking Scenarios

### Scenario 1: Updating Budget Numbers

```bash
# WRONG WAY (DON'T DO THIS)
# Copying from existing WordPress page
wp post get 699 --field=post_content | grep -oE '\$[0-9]+M'

# RIGHT WAY
# Check fact sheet first
grep -i "budget" /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md

# Example output:
# Total Budget: $81M
# Public Safety: $29.9M
# Community Wellness: $13.4M
# etc.
```

### Scenario 2: ROI Claims

```bash
# Check fact sheet for ROI data
grep -i "roi\|return" /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md

# Verify calculation if needed
# Example: Wellness Centers ROI
# - Cost per participant: ~$2,000
# - Healthcare savings: $4,000-6,000
# - ROI: $2-3 per $1 invested ✓
```

### Scenario 3: Program Costs

```bash
# Check fact sheet for program costs
grep -i "mini substation\|wellness center\|youth" /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md

# Cross-reference with policy documents
cat /home/dave/rundaverun/campaign/downloads/policy_documents/MINI_SUBSTATIONS_IMPLEMENTATION_GUIDE.md | grep -i cost
```

### Scenario 4: Timeline/Dates

```bash
# Verify election dates
grep -i "election\|deadline\|date" /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md

# For official election dates, verify with:
# - Kentucky Secretary of State website
# - Jefferson County Clerk website
```

---

## Red Flags: When to Stop and Verify

**STOP and verify if you encounter:**

🚩 **Numbers that seem outdated:**
- Last updated date is old
- Numbers have been "corrected" multiple times
- Conflicting numbers across pages

🚩 **Numbers without sources:**
- Can't find in QUICK_FACTS_SHEET.md
- No source documented
- "Approximately" or "around" numbers

🚩 **Conflicting information:**
- Different pages show different numbers
- Policy doc conflicts with fact sheet
- Recent corrections contradict older content

🚩 **Suspiciously round numbers:**
- Exact thousands (e.g., $50,000 vs. $47,832)
- May be estimates, not actual figures
- Verify precision required

**When in doubt, ASK USER before proceeding.**

---

## Known Data Points (Quick Reference)

**As of November 2025:**

### Budget
- **Total Budget:** $81M
- **Public Safety (Mini Substations):** $77.4M (not $29.9M or $47.5M)
- **Community Wellness Centers:** $13.4M
- **Youth Programs:** Included in wellness budget

### ROI
- **Wellness Centers:** $2-3 per $1 invested (updated from $1.80)
- **Mini Substations:** Reduced response times, improved safety

### Programs
- **Mini Substations:** 14 locations
- **Wellness Centers:** 7 locations
- **Youth Programs:** $1,200 value per participant

### Education (Louisville)
- **JCPS Reading Proficiency:** 34-35% (NOT 44%)
- **JCPS Math Proficiency:** 27-28% (NOT 41%)

**NOTE:** These figures are subject to update. Always verify against QUICK_FACTS_SHEET.md.

---

## Common Mistakes to Avoid

### ❌ DON'T:

1. **Copy numbers from existing WordPress pages**
   - Pages may have outdated data
   - Previous updates may have been incorrect

2. **Trust old conversation reports**
   - Reports reflect data at time of creation
   - May not include latest corrections

3. **Use approximate numbers without verification**
   - "$about 50M" is not precise
   - Verify exact figure

4. **Skip verification for "small" updates**
   - Even typo fixes should verify numbers
   - All numbers must be accurate

5. **Assume calculations are correct**
   - Verify math independently
   - ROI, percentages, totals

### ✅ DO:

1. **Check QUICK_FACTS_SHEET.md first**
   - Every single time
   - No exceptions

2. **Document source for every fact**
   - In session notes
   - In fact-check log

3. **Verify calculations**
   - Double-check math
   - Verify formulas

4. **Copy reference files to session directory**
   - Keep snapshot of sources used
   - Enables future verification

5. **Ask when unsure**
   - Better to ask than publish incorrect data
   - User has final authority on facts

---

## Integration with WordPress Content Update

**Fact-checking should happen during Phase 2 (Content Modification) of WordPress updates:**

```bash
# After creating session directory and backing up content:

# STEP: Fact-Check Before Making Changes
echo "Fact-checking content..."
cp /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md "$SESSION_DIR/FACT_SHEET_reference.md"

# Identify all numbers in content
grep -oE '\$[0-9,]+(\.[0-9]+)?[KMB]?|[0-9]+%' "$SESSION_DIR/page_105_before.html" > "$SESSION_DIR/numbers_to_verify.txt"

# Verify each against fact sheet
while read number; do
  grep -q "$number" "$SESSION_DIR/FACT_SHEET_reference.md" && echo "✓ $number" || echo "⚠ $number - needs verification"
done < "$SESSION_DIR/numbers_to_verify.txt"

# Then proceed with content modification
```

---

## Fact-Checking Checklist

Before publishing content:
- [ ] Identified all facts/numbers in content
- [ ] Checked QUICK_FACTS_SHEET.md for each fact
- [ ] Verified facts not in fact sheet against secondary sources
- [ ] Documented sources in fact-check log
- [ ] Resolved any conflicts (fact sheet takes precedence)
- [ ] Double-checked calculations and math
- [ ] Copied reference materials to session directory
- [ ] No outdated data from previous WordPress content

---

## Updating QUICK_FACTS_SHEET.md

**ONLY USER CAN UPDATE FACT SHEET**

If you find data that should be added to QUICK_FACTS_SHEET.md:

1. **Document in session notes:**
   ```markdown
   ## Suggested Fact Sheet Update

   **New Data Found:**
   - [Fact]: [Value]
   - Source: [Where it came from]
   - Verification: [How verified]

   **Recommendation:** Add to QUICK_FACTS_SHEET.md
   ```

2. **Ask user:**
   "I found [data] from [source]. Should this be added to QUICK_FACTS_SHEET.md?"

3. **Never update fact sheet without explicit user approval**

---

## Quality Assurance

### After Fact-Checking:

**High confidence indicators:**
- ✅ Found in QUICK_FACTS_SHEET.md
- ✅ Cross-referenced with policy docs (consistent)
- ✅ Recently updated/verified
- ✅ Source documented

**Medium confidence indicators:**
- ⚠️ Found in policy docs but not fact sheet
- ⚠️ Calculation derived from fact sheet data
- ⚠️ From external source (needs user verification)

**Low confidence indicators:**
- 🚩 Only found in existing WordPress content
- 🚩 Conflicting sources
- 🚩 No source found
- 🚩 Approximate/rounded numbers

**If confidence is medium or low, ASK USER before publishing.**

---

## Related Protocols

- [WordPress Content Update Protocol](wordpress_content_update_protocol.md) - When to fact-check during updates
- [Campaign Content Approval Protocol](campaign_content_approval_protocol.md) - Approval workflow
- [Verification Protocol](verification_protocol.md) - General verification procedures

---

## Quick Reference

### Fact-Checking Command Flow:

```bash
# 1. Save fact sheet reference
cp /home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md "$SESSION_DIR/FACT_SHEET_reference.md"

# 2. Extract numbers to verify
grep -oE '\$[0-9,]+(\.[0-9]+)?[KMB]?|[0-9]+%' content.html

# 3. Search fact sheet
grep -i "search term" "$SESSION_DIR/FACT_SHEET_reference.md"

# 4. Document in fact-check log
cat > "$SESSION_DIR/FACT_CHECK_LOG.md" <<EOF
[See template above]
EOF
```

---

**Generated:** 2025-11-08
**Status:** Active - CRITICAL
**Next Review:** Before every content update
