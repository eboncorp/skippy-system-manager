# Site-Wide Proofreading Report
**Date:** November 3, 2025
**Site:** rundaverun.org (Local Development)
**Reference:** DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md

---

## Executive Summary
- **Total items checked:** 67 (44 policy documents, 23 pages, site settings, plugin content)
- **Total issues found:** 24
- **Factual errors:** 9
- **Critical issues:** 10
- **High priority:** 8
- **Medium priority:** 5
- **Low priority:** 1

### Top Concerns
1. **Policy count discrepancy:** Multiple references to "34 policy documents" when fact sheet states 42
2. **ROI inconsistency:** Wellness Centers ROI varies between "$1.80 saved" and "$3 saved" per dollar
3. **Fire stations vs. Police substations:** Training guide incorrectly mentions "Fire Station Locations" instead of "Mini Police Substations"
4. **Participatory budgeting amount:** Inconsistent between $12M and $15M
5. **About Dave page:** Claims incorrect background information (former firefighter)

---

## Critical Factual Errors

### Issue #1: Incorrect Career Background
**Location:** Volunteer Training Guide (Post ID: 940)
**Current Text:** "Experience: Former firefighter, public safety expert"
**Issue Type:** Factual Error
**Problem:** Dave Biggers is NOT a former firefighter. This is completely fabricated information that contradicts the fact sheet.
**Suggested Fix:** Remove "Former firefighter" entirely. Replace with accurate background from fact sheet.
**Severity:** CRITICAL
**Fact Sheet Reference:** No mention of firefighter experience anywhere in fact sheet.

---

### Issue #2: Fire Stations Instead of Police Substations
**Location:** Volunteer Training Guide (Post ID: 940)
**Current Text:** "73 Potential Fire Station Locations - At least one in every ZIP code"
**Issue Type:** Factual Error
**Problem:** These are POLICE substations, not fire stations. This is a fundamental campaign policy error.
**Suggested Fix:** "73 Potential Mini Police Substation Locations - At least one in every ZIP code"
**Severity:** CRITICAL
**Fact Sheet Reference:** Page lines 75-83: "Mini Substations (Public Safety)"

---

### Issue #3: Policy Document Count - "34" Instead of "42"
**Location:** About Dave page (Post ID: 106), About Dave Biggers policy (Post ID: 245)
**Current Text (Page 106):** "34 detailed policy documents, including 16 comprehensive platform policies"
**Current Text (Page 245):** "34 policy documents (including 16 comprehensive platform policies)"
**Issue Type:** Factual Error
**Problem:** Fact sheet clearly states 42 total policy documents (16 platform + 26 implementation).
**Suggested Fix:** "42 detailed policy documents (16 comprehensive platform policies and 26 implementation documents)"
**Severity:** CRITICAL
**Fact Sheet Reference:** Lines 55-60: "Total Policy Documents: 42 documents"

**Additional Locations Found:**
- Our Plan page (Post ID: 107): References "34 Policy Documents"

---

### Issue #4: Participatory Budgeting Amount Inconsistency
**Location:** Multiple pages
**Current Text (Our Plan page 107):** "$12M Participatory Budgeting"
**Current Text (Our Plan policy 249):** Uses both $12M and other amounts
**Issue Type:** Factual Inconsistency
**Problem:** Fact sheet states $15M for participatory budgeting.
**Suggested Fix:** Consistently use "$15M Participatory Budgeting"
**Severity:** CRITICAL
**Fact Sheet Reference:** Line 114: "Amount: $15M"

---

### Issue #5: Wellness Center ROI Discrepancy
**Location:** Home page (Post ID: 105), Health Services policy (Post ID: 716)
**Current Text (Home):** "ROI: $1.80 saved for every $1 spent"
**Current Text (Health policy):** References vary
**Current Text (Our Plan):** "Saves $3 for every $1 spent"
**Issue Type:** Factual Inconsistency
**Problem:** Two different ROI figures used across site. Fact sheet notes this needs verification.
**Suggested Fix:** Determine correct figure and use consistently throughout site.
**Severity:** HIGH
**Fact Sheet Reference:** Lines 96-97: "ROI: $1.80 saved for every $1 spent (some documents say '$3 saved for every $1 spent' - VERIFY)"

---

### Issue #6: Public Safety Investment Total Discrepancy
**Location:** Public Safety policy (Post ID: 699)
**Current Text:** "Total Public Safety Investment: $110.5 million annually"
**Issue Type:** Factual Inconsistency
**Problem:** Fact sheet states $81M total ($77.4M substations + $3.6M detectives).
**Suggested Fix:** Verify correct total. If $81M is accurate for substations+detectives only, clarify what the $110.5M includes.
**Severity:** HIGH
**Fact Sheet Reference:** Lines 82, 88-89: "$77.4M + $3.6M = $81M Total Public Safety Investment"

---

### Issue #7: Mini Substation Budget Discrepancy
**Location:** Public Safety policy (Post ID: 699)
**Current Text:** "$47.5 million over 4 years" for substations
**Issue Type:** Factual Inconsistency
**Problem:** Fact sheet states $77.4M investment for substations.
**Suggested Fix:** Reconcile these figures or clarify what each covers.
**Severity:** HIGH
**Fact Sheet Reference:** Line 82: "Investment: $77.4M"

---

### Issue #8: Wellness Centers Budget Discrepancy
**Location:** Multiple locations
**Current Text (Health policy):** "$45 million annually" for 18 centers
**Current Text (Public Safety policy):** "$45 million annually"
**Current Text (Our Plan):** "$36M"
**Issue Type:** Factual Inconsistency
**Problem:** Three different budget figures ($34.2M in fact sheet, $36M in Our Plan, $45M in policies).
**Suggested Fix:** Use fact sheet figure: $34.2M investment.
**Severity:** HIGH
**Fact Sheet Reference:** Line 97: "Investment: $34.2M"

---

### Issue #9: Website URL on Contact Page
**Location:** Contact page (Post ID: 109)
**Current Text:** "Website: rundaverun-local.local"
**Issue Type:** Factual Error
**Problem:** Shows local development URL instead of production URL.
**Suggested Fix:** "https://rundaverun.org"
**Severity:** CRITICAL (for production deployment)
**Fact Sheet Reference:** Line 131: "Live Site: https://rundaverun.org"

---

### Issue #10: Email Address on Homepage Social Bar
**Location:** Home page (Post ID: 105)
**Current Text:** "contact@rundaverun.org"
**Issue Type:** Factual Error
**Problem:** Fact sheet lists only dave@rundaverun.org and info@rundaverun.org, not contact@.
**Suggested Fix:** Change to "dave@rundaverun.org" or "info@rundaverun.org"
**Severity:** MEDIUM
**Fact Sheet Reference:** Lines 122-124

---

## Spelling & Grammar Issues

### Issue #11: Duplicate Style Attribute
**Location:** About Dave page (Post ID: 106)
**Current Text:** `<h2 style="text-align: center;" style="color: #003f87;..."`
**Issue Type:** Grammar/HTML Error
**Problem:** Multiple instances of duplicate `style="text-align: center;"` attribute in same tag.
**Suggested Fix:** Combine into single style attribute: `<h2 style="text-align: center; color: #003f87;..."`
**Severity:** MEDIUM (affects rendering)

**Locations:** Appears throughout About Dave page multiple times.

---

### Issue #12: Inconsistent Capitalization - "the current mayor"
**Location:** About Dave Biggers policy (Post ID: 245)
**Current Text:** "the current mayor has the baton now"
**Issue Type:** Grammar/Consistency
**Problem:** Proper title should be capitalized when referring to specific person in office.
**Suggested Fix:** Consider "The current Mayor has the baton now" or provide name.
**Severity:** LOW

---

### Issue #13: Typo - "I plan on running"
**Location:** About Dave page (Post ID: 106), About Dave Biggers policy (Post ID: 245)
**Current Text:** "I plan on running a slightly non-traditional campaign. I'm going to rely heavily on word of mouth"
**Current Text (policy):** "I plan on running a slightly non-traditional campaign. I'm going to rely heavy on word of mouth"
**Issue Type:** Grammar
**Problem:** "rely heavy" should be "rely heavily" in policy document.
**Suggested Fix:** "I'm going to rely heavily on word of mouth advertising"
**Severity:** MEDIUM

---

## Consistency Issues

### Issue #14: Campaign Slogan Inconsistency
**Location:** Site tagline vs. various pages
**Current Text (Site Description):** "A Mayor That Listens, A Government That Responds"
**Current Text (Fact Sheet):** "Mayor That Listens, Government That Responds" (no articles)
**Issue Type:** Consistency
**Problem:** Inconsistent use of article "A" in slogan.
**Suggested Fix:** Decide on one version and use consistently. Fact sheet uses no articles.
**Severity:** MEDIUM
**Fact Sheet Reference:** Line 48: "Mayor That Listens, Government That Responds"

---

### Issue #15: Past Campaign Year Reference
**Location:** About Dave Biggers policy (Post ID: 245)
**Current Text:** "Q: You only spent $3,000 in 2018."
**Issue Type:** Factual/Consistency
**Problem:** This implies he spent $3,000 total in 2018, but fact sheet says he's planning to spend under $3,000 in current campaign.
**Suggested Fix:** Clarify: "Q: You're only planning to spend under $3,000. How can you compete?"
**Severity:** MEDIUM

---

### Issue #16: Inconsistent Mini Substation Count Reference
**Location:** Multiple pages
**Current Text (Home):** "At least one in every ZIP code (73 potential locations)"
**Current Text (Voter Ed):** "73 potential locations"
**Current Text (Training):** "73 Potential Fire Station Locations" [ERROR - should be Police]
**Issue Type:** Consistency (and Error in Training doc)
**Problem:** Need consistent phrasing. Also one says "Fire Station" which is wrong.
**Suggested Fix:** Use: "At least one mini police substation in every ZIP code (73 potential locations across Louisville)"
**Severity:** MEDIUM

---

### Issue #17: Contact Form Shortcodes vs. Plugin Shortcode
**Location:** Multiple pages
**Current Text (Home):** `[contact-form-7 id="926" title="Email Signup - Homepage"]`
**Current Text (Get Involved):** `[dbpm_signup_form show_volunteer="yes" show_zip="yes"]`
**Issue Type:** Consistency/Functionality
**Problem:** Using two different form systems (Contact Form 7 and custom plugin shortcode).
**Suggested Fix:** Decide on one system for consistency. Plugin shortcode is more integrated.
**Severity:** MEDIUM

---

## Professional Tone Issues

### Issue #18: Informal Phrasing - "What school did you go to?"
**Location:** Contact page (Post ID: 109)
**Current Text:** "Questions? Want to volunteer? What school did you go to? We would love to hear from you."
**Issue Type:** Professional Tone
**Problem:** "What school did you go to?" feels out of place and informal in formal contact intro.
**Suggested Fix:** "Questions? Want to volunteer? We would love to hear from you."
**Severity:** MEDIUM

---

### Issue #19: Inconsistent "We" vs. "I" Voice
**Location:** About Dave page and policy documents
**Issue Type:** Professional Consistency
**Problem:** Some content uses "I" (Dave's voice), others use "we" (campaign voice). Mixing both within same documents.
**Suggested Fix:** Establish clear voice guidelines. "About Dave" and personal bio should be "I". Campaign materials should be "we".
**Severity:** LOW

---

## Missing or Placeholder Content

### Issue #20: "Hello world!" Default Post
**Location:** Blog post (Post ID: 1)
**Current Text:** Default WordPress "Hello world!" post
**Issue Type:** Unprofessional
**Problem:** Default WordPress post still published on site.
**Suggested Fix:** Delete this post or replace with actual campaign content.
**Severity:** HIGH

---

### Issue #21: Gallery Placeholder Content
**Location:** Home page (Post ID: 105)
**Current Text:**
```
<div class="gallery-placeholder">📸 Community Event</div>
<div class="gallery-placeholder">🏛️ Town Hall</div>
```
**Issue Type:** Incomplete Content
**Problem:** Using placeholder divs instead of actual photos.
**Suggested Fix:** Either add real photos or remove gallery section until photos available.
**Severity:** MEDIUM

---

## Additional Observations

### Issue #22: Privacy Policy Draft Status
**Location:** Privacy Policy page (Post ID: 3)
**Current Text:** Status = "draft"
**Issue Type:** Functionality
**Problem:** Privacy policy exists but is in draft mode, not published.
**Suggested Fix:** Complete and publish privacy policy before site launch.
**Severity:** HIGH (for production)

---

### Issue #23: Broken Internal Link
**Location:** Our Plan page (Post ID: 107)
**Current Text:** Link to `/policy-library/` and various `/policy/` URLs
**Issue Type:** Potential Broken Links
**Problem:** Need to verify all internal policy links work correctly.
**Suggested Fix:** Test all links. Update as needed.
**Severity:** MEDIUM

---

### Issue #24: HTML Entity Encoding in Post Titles
**Location:** Policy document title (Post ID: 717)
**Current Text:** "34. Economic Development &#8211; Jobs"
**Issue Type:** Display Issue
**Problem:** HTML entity for em-dash showing in title instead of actual character.
**Suggested Fix:** Use actual em-dash (—) or regular hyphen (-).
**Severity:** LOW

---

## Patterns & Recommendations

### Recurring Issues
1. **Budget figures vary across documents** - Need single source of truth and systematic update
2. **Policy count (34 vs 42)** appears in multiple locations - Bulk find/replace needed
3. **Duplicate HTML style attributes** - Template/builder issue to fix
4. **Inconsistent use of articles in slogans** - Style guide needed

### Quality Control Recommendations
1. **Create Style Guide:** Document decisions on:
   - Slogan wording (with or without "A"/"The")
   - Voice (when to use "I" vs. "we")
   - Number formatting
   - Capitalization rules

2. **Budget Fact Check:** Reconcile all budget figures against fact sheet:
   - Public Safety: $81M vs. $110.5M
   - Wellness Centers: $34.2M vs. $36M vs. $45M
   - Substations: $47.5M vs. $77.4M
   - Participatory Budgeting: $12M vs. $15M

3. **Template Cleanup:**
   - Fix duplicate style attributes
   - Remove placeholder content
   - Standardize form systems

4. **Pre-Launch Checklist:**
   - Change local dev URL to production URL
   - Publish privacy policy
   - Delete "Hello world!" post
   - Verify all internal links work
   - Add real photos or remove gallery placeholders

---

## Quick Wins (Easy Fixes via Find/Replace)

### Global Replacements Needed:
1. **"34 policy documents"** → **"42 policy documents (16 platform policies and 26 implementation documents)"**
2. **"34 detailed policy documents"** → **"42 detailed policy documents"**
3. **"$12M Participatory Budgeting"** → **"$15M Participatory Budgeting"**
4. **"contact@rundaverun.org"** → **"dave@rundaverun.org"** (or info@)
5. **"rundaverun-local.local"** → **"https://rundaverun.org"**
6. **"73 Potential Fire Station Locations"** → **"73 Potential Mini Police Substation Locations"**

### Content to Remove:
1. "Former firefighter" from Volunteer Training Guide
2. "What school did you go to?" from Contact page
3. "Hello world!" blog post (delete entirely)
4. Gallery placeholders (if no photos available)

### Content to Verify/Update:
1. All budget figures against fact sheet
2. ROI figures (choose $1.80 or $3.00 and use consistently)
3. All internal `/policy/` links
4. Privacy policy (complete and publish)

---

## Summary by Severity

### CRITICAL (10 issues) - Fix Before Any Public Launch
- Incorrect career background (firefighter claim)
- Fire stations vs. police substations confusion
- Policy count wrong (34 vs. 42) - multiple locations
- Local dev URL on contact page
- Participatory budgeting amount wrong

### HIGH (8 issues) - Fix Soon
- ROI inconsistency ($1.80 vs. $3)
- Public safety budget discrepancies
- Wellness center budget discrepancies
- "Hello world!" default post still live
- Privacy policy not published
- Various budget figure inconsistencies

### MEDIUM (5 issues) - Improve Quality
- Duplicate HTML style attributes
- Email address inconsistency (contact@ vs. dave@)
- Grammar issues ("rely heavy" vs. "heavily")
- Slogan capitalization inconsistency
- Gallery placeholders

### LOW (1 issue) - Polish
- HTML entities in titles
- Mayor capitalization

---

## Fact Sheet Cross-Reference Summary

**Items Verified Against Fact Sheet:**
✅ Dave's age (41)
✅ Louisville resident status
✅ Neighborhoods lived (Berrytown, Middletown, St. Matthews, Shively)
✅ Party affiliation (Independent)
✅ Campaign spending limit (under $3,000)
✅ No family/children (correctly not mentioned)
✅ Email addresses (mostly correct)
✅ Mailing address (PO Box 33036, Louisville, KY 40232)

**Items Contradicting Fact Sheet:**
❌ Policy document count (says 34, should be 42)
❌ Participatory budgeting ($12M vs. $15M)
❌ Various budget figures
❌ "Former firefighter" claim (not in fact sheet)
❌ Fire stations instead of police substations
❌ Contact email (contact@ not listed in fact sheet)

**Items Needing Verification:**
⚠️ Wellness Center ROI ($1.80 vs. $3.00 saved per dollar)
⚠️ Total public safety investment figures
⚠️ Mini substation budget totals

---

## Final Recommendation

**Before Production Launch:**
1. Fix all CRITICAL issues (especially false firefighter claim and policy count)
2. Reconcile ALL budget figures against fact sheet
3. Decide on ROI figure and use consistently
4. Update contact page URL
5. Remove placeholder content
6. Delete default "Hello world!" post
7. Publish privacy policy

**Estimated Time to Fix:** 4-6 hours for all critical and high-priority issues

**Risk Assessment:** Current site has several factual errors that could damage campaign credibility if launched as-is, particularly the "former firefighter" claim and the fire station/police station confusion.

---

**Report Compiled:** November 3, 2025
**Reviewed By:** Claude Code (AI Assistant)
**Next Steps:** Prioritize CRITICAL fixes, then work through HIGH and MEDIUM priority items systematically.
