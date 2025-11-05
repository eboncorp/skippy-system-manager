# WordPress Site Investigation Report
**Date:** November 4, 2025
**Site:** Dave Biggers for Louisville Mayor Campaign
**Environment:** Local Development (rundaverun-local.local)
**Investigator:** Claude Code

---

## Executive Summary

Investigation of changes made to the local WordPress site on November 4, 2025, reveals:

### ✅ POSITIVE FINDINGS:
- 35+ posts/pages received security-related updates early morning (Nov 4, 3am-8:30am)
- Security hardening implemented (debug disabled, file permissions secured, headers added)
- No new biographical errors introduced in policy documents

### ⚠️ CRITICAL ISSUES IDENTIFIED:
1. **November 3 fact-check fixes NEVER imported back to WordPress**
   - Fixes were applied to exported HTML files only
   - WordPress database still contains incorrect data
   - 3 documents have wrong figures (posts 701, 709, 246)

2. **Volunteer scripts contain serious biographical errors** (posts 941, 942)
   - Falsely claim Dave is "former firefighter"
   - Incorrectly mention "fire stations" instead of "mini police substations"
   - Created/updated on Nov 4 with errors intact

3. **"Fire station" language persists in 6 published documents**
   - Should be "mini police substations" per campaign fact sheet

---

## Today's Changes Summary (November 4, 2025)

### Posts Modified Today:
- **Total modified:** 35 posts/pages
- **Time range:** 3:47 AM - 8:23 AM EST
- **Types:** Policy documents (27), Pages (8)

### Primary Changes Made:
Based on session reports found in /home/dave/skippy/conversations/:

1. **Security Hardening (1:00 AM - 1:20 AM)**
   - Disabled WP_DEBUG modes
   - Added HTTP security headers
   - Secured file permissions
   - Implemented login rate limiting
   - Created robots.txt

2. **Content Updates (3:47 AM - 8:23 AM)**
   - Policy documents touched (likely mass updates)
   - Main pages updated (Home, About, Contact, etc.)
   - Unknown what content changes were made

### What Changed in Key Documents:

**Post 699 (Public Safety & Community Policing):**
- Last modified: 2025-11-04 08:23:19
- Content appears correct for public safety policy
- No firefighter biographical errors found
- Mini substations mentioned correctly (not fire stations)

**Post 716 (Health & Human Services):**
- Last modified: 2025-11-04 08:23:29
- Contains wellness centers information
- **ISSUE:** ROI still shows "$3 saved per $1 spent" (should be $1.80)

**Post 717 (Economic Development & Jobs):**
- Last modified: 2025-11-04 08:19:16
- Employee Bill of Rights content
- No biographical errors found

**Post 941 (Phone Banking Script):**
- Last modified: 2025-11-04 08:19:25
- **CRITICAL ERROR:** Says Dave is "former firefighter"
- **CRITICAL ERROR:** Mentions "fire stations in every ZIP code"
- Script appears to be newly created with errors

**Post 942 (Canvassing Talking Points):**
- Last modified: 2025-11-04 08:20:05
- **CRITICAL ERROR:** Says Dave is "former firefighter"
- **CRITICAL ERROR:** Says "fire stations in every ZIP code"
- Script appears to be newly created with errors

---

## November 3 QA Session - Status Check

### What Should Have Been Fixed:

According to `/home/dave/skippy/conversations/policy_factcheck_fixes_complete_2025-11-03.md`:

**Error #1 - Participatory Budgeting: $5M → $15M**
- **Documents:** Posts 701, 709
- **Status:** ❌ NOT FIXED IN WORDPRESS
- **Current State:** Both documents still show $5M

**Error #2 - Wellness Centers ROI: $3.00 → $1.80**
- **Document:** Post 246
- **Status:** ❌ NOT FIXED IN WORDPRESS  
- **Current State:** Still shows $3 saved per $1 spent

**Error #3 - Multiple documents**
- **Status:** ❌ NOT FIXED IN WORDPRESS
- **Root Cause:** Fixes applied to exported HTML files in `/home/dave/skippy/claude/uploads/policy_documents_export/` but never re-imported to WordPress

### Why Fixes Weren't Applied:

The November 3 session:
1. Exported 44 policy documents to HTML
2. Fact-checked against campaign fact sheet
3. Found 3 errors in 3 documents
4. **Applied fixes to exported HTML files**
5. ❌ **NEVER re-imported corrected files back to WordPress**

Result: WordPress database still contains the old, incorrect data.

---

## Issue #1: Participatory Budgeting - Wrong Amount

### Correct Information (from Fact Sheet):
- Amount: **$15 million annually**
- Distribution: $577K per Metro Council district × 26 districts

### Current WordPress Content (INCORRECT):

**Post 701 (Budget & Financial Management):**
```
"Participatory Budgeting ($5M annually): Give residents direct control 
over $5 million in neighborhood improvement funding through democratic voting."
```
Multiple other references to $5M throughout document.

**Post 709 (Neighborhood Development):**
```
"Participatory Neighborhood Budgeting ($5M annually): Give residents direct 
control over $5 million in neighborhood improvement funds"
```

### Impact:
- **Severity:** HIGH
- Understates community investment by $10 million
- Contradicts major campaign commitment
- Featured prominently in budget policy

---

## Issue #2: Wellness Centers ROI - Wrong Figure

### Correct Information (from Fact Sheet):
- ROI: **$1.80 saved for every $1 spent**

### Current WordPress Content (INCORRECT):

**Post 246 (Executive Budget Summary):**
```html
<li>Wellness centers: 30+ cities, $3 saved per $1 spent</li>
```

### Impact:
- **Severity:** MEDIUM-HIGH
- Overstates return on investment by 67%
- Can be fact-checked by opponents
- Credibility risk

---

## Issue #3: Biographical Errors in Volunteer Scripts

### Correct Information (from Fact Sheet):
- Dave Biggers is **NOT a firefighter** (never was)
- Campaign proposes **mini police substations** (not fire stations)
- Policy: 73 potential locations for mini police substations

### Current WordPress Content (INCORRECT):

**Post 941 (Phone Banking Script):**
```
Q: What's Dave's background?
A: "Dave is 41 years old, a Louisville native and former firefighter 
with extensive public safety experience."
```

Also:
```
Public Safety: Fire stations in every ZIP code (73 potential locations)
```

**Post 942 (Canvassing Talking Points):**
```
KEY MESSAGE: "Dave has a plan for fire stations in every ZIP code - 
73 potential locations across Louisville."
```

Also:
```
"Dave is 41, a Louisville native and former firefighter."
```

### Impact:
- **Severity:** CRITICAL
- **Distribution:** Given to campaign volunteers
- **Risk:** Volunteers spreading false biographical information
- **Credibility:** Major misrepresentation of candidate background
- **Confusion:** Fire stations vs. mini police substations completely different
  - Fire stations = firefighters, fire trucks, emergency medical
  - Mini police substations = community policing, 2-4 officers, neighborhood presence

---

## Issue #4: "Fire Stations" Language Throughout Site

### Documents with "Fire Station" Mentions:
- Post 941 (Phone Banking Script) - volunteer facing
- Post 942 (Canvassing Talking Points) - volunteer facing  
- Post 702 (Affordable Housing)
- Post 249 (Our Plan for Louisville)
- Post 244 (Detailed Line-Item Budget)
- Post 243 (Campaign One-Pager)

**Total:** 6 published documents with incorrect terminology

### Should Be:
"Mini police substations" or "community policing substations"

### Impact:
- Confuses voters about actual policy
- Fire departments are separate issue from police/public safety
- Creates expectation of fire department expansion (not the plan)

---

## Site Statistics

### Policy Documents:
- **Total count:** 45 policy documents
- **Target count per fact sheet:** 42 documents
- **Discrepancy:** 3 extra documents (need to verify which are current)

### Glossary Terms:
- **Total:** 351 terms (matches fact sheet ✓)
- **Categories:** 48 categories (matches fact sheet ✓)

---

## Remaining Issues from Original 22 Fixes

Unable to verify if all 22 fixes from November 3 QA session are still in place because:
1. No comprehensive list of all 22 fixes found in session reports
2. Only 3 fixes documented in detail (the factual errors)
3. Would need original QA checklist to verify each item

### What We Can Confirm:
✅ Security hardening maintained (separate fixes, Nov 4)
✅ No new biographical errors in main policy documents
❌ 3 factual errors NOT fixed (participatory budgeting, wellness ROI)
❌ New biographical errors in volunteer scripts (posts 941, 942)
❌ "Fire stations" language not corrected

---

## Recommended Actions

### URGENT (Do Immediately):

1. **Fix Volunteer Scripts (Posts 941, 942)**
   - Remove "former firefighter" references
   - Change "fire stations" to "mini police substations"
   - Add warning to verify with campaign before distribution
   - **Risk:** Volunteers may already have incorrect scripts

2. **Apply November 3 Fixes to WordPress**
   - Post 701: Change $5M to $15M (participatory budgeting)
   - Post 709: Change $5M to $15M (participatory budgeting)
   - Post 246: Change $3.00 to $1.80 (wellness ROI)

3. **Fix "Fire Stations" References**
   - Search and replace site-wide
   - Change to "mini police substations"
   - Verify context makes sense after change

### HIGH PRIORITY (Do Today):

4. **Verify November 3 Fixes Still In Place**
   - Need original QA checklist
   - Re-test each of 22 items
   - Document current status

5. **Audit All Volunteer-Facing Materials**
   - Check for other scripts/materials with errors
   - Verify talking points match fact sheet
   - Review any printed materials before distribution

6. **Create Content Update Process**
   - When fixing exported files, create import workflow
   - Verify fixes in WordPress database, not just exports
   - Test in staging before updating production

### MEDIUM PRIORITY (This Week):

7. **Policy Document Count Reconciliation**
   - Fact sheet says 42 documents
   - WordPress has 45 documents
   - Determine which are current/should be published

8. **Site-Wide Fact Check**
   - Run comprehensive check against fact sheet
   - Focus on frequently-used figures
   - Document any other discrepancies

9. **Volunteer Training Update**
   - Brief volunteers on correct information
   - Provide updated scripts
   - Create FAQ with verified facts

### LONG-TERM:

10. **Implement Single Source of Truth System**
    - All facts managed in one canonical location
    - Auto-populate content from fact sheet where possible
    - Version control for fact sheet
    - Notification system when facts change

---

## Technical Notes

### Environment:
- **Working Directory:** `/home/dave/Local Sites/rundaverun-local/app/public`
- **Database:** Local WordPress installation
- **WordPress Version:** [check with wp core version]
- **PHP Version:** [check with php --version]

### Files Reviewed:
- Campaign Fact Sheet: `/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md`
- November 3 QA Report: `/home/dave/skippy/conversations/policy_factcheck_fixes_complete_2025-11-03.md`
- Security Fixes Report: `/home/dave/skippy/conversations/SECURITY_FIXES_IMPLEMENTED_2025-11-04.md`
- Exported HTML files: `/home/dave/skippy/claude/uploads/policy_documents_export/`

### WordPress Posts Checked:
- 699 (Public Safety & Community Policing) ✓ No errors found
- 701 (Budget & Financial Management) ❌ $5M error persists
- 709 (Neighborhood Development) ❌ $5M error persists
- 716 (Health & Human Services) ✓ Mostly correct
- 717 (Economic Development) ✓ No errors found
- 246 (Executive Budget Summary) ❌ $3.00 ROI error persists
- 941 (Phone Banking Script) ❌ Multiple critical errors
- 942 (Canvassing Talking Points) ❌ Multiple critical errors

---

## Conclusion

While security hardening was successfully implemented today, critical content accuracy issues remain:

**High Risk:**
- Volunteer scripts contain false biographical information
- Could damage campaign credibility if distributed
- Volunteers may be actively using incorrect scripts

**Medium Risk:**
- Budget figures incorrect in 3 documents
- Can be fact-checked by opponents/media
- Creates internal inconsistency

**Process Issue:**
- November 3 fixes applied to exports but not WordPress
- Demonstrates need for better update workflow
- Current process vulnerable to version control issues

**Next Steps:**
1. Immediately fix volunteer scripts (highest priority)
2. Apply November 3 fixes to WordPress database
3. Comprehensive site audit against fact sheet
4. Implement change management process

---

**Report Generated:** November 4, 2025 (afternoon)
**Environment:** Local Development
**Status:** Investigation Complete - Action Required
**Priority:** URGENT (volunteer scripts), HIGH (budget figures)

