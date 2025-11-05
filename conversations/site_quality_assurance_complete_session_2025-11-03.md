# Site Quality Assurance & Production Preparation Session
**Date:** November 3, 2025  
**Session Duration:** Extended session (Phase 4 continuation + comprehensive QA)  
**Working Directory:** `/home/dave/Local Sites/rundaverun-local/app/public`  
**Site:** rundaverun.org (Dave Biggers for Mayor Campaign)

---

## Session Header

**Session Focus:** Complete site quality assurance, error correction, and production preparation  
**Primary Objectives:**
1. Fix all critical factual errors from proofreading report
2. Correct punctuation and formatting issues
3. Fix broken links and functional problems
4. Standardize budget figures across all documents
5. Prepare site for production launch

**Session Outcome:** Successfully fixed 22 critical/high priority issues and prepared site for production deployment

---

## Context

### Previous Work Referenced
This session is a continuation of Phase 4 implementation work. Prior to this session:
- Phase 3 was completed (email analytics, newsletter scheduling, A/B testing)
- Phase 4 features were implemented:
  - Volunteer activity tracking and gamification
  - Advanced faceted search
  - Email A/B testing system
- Initial proofreading agent was run, identifying 24 content issues

### Session Origin
The session began with a request to continue from a previous conversation that had run out of context. The conversation summary indicated:
- Phase 4 implementation was complete
- A proofreading agent had found 24 issues including critical factual errors
- User wanted to fix all issues except Issue #18 ("What school did you go to?" phrase to remain)

### Files Used as Reference
1. `/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md` - Authoritative source of campaign facts
2. `/home/dave/skippy/conversations/proofreading_report_20251103.md` - Initial content errors (24 issues)
3. `/home/dave/skippy/conversations/punctuation_errors_report_20251103.md` - Punctuation scan (20,060 issues)
4. `/home/dave/skippy/conversations/functional_testing_report_20251103.md` - Links and functional tests (87 issues)

---

## User Requests Timeline

### Request 1: "proceed with all fixes except issue #18"
**Intent:** Fix all critical proofreading issues but keep "What school did you go to?" on contact page
**Response:** Began systematic fixing of 5 critical content errors

### Request 2: "i seen at least two instances of extra '''"
**Intent:** User noticed triple apostrophes that needed fixing
**Response:** Launched punctuation-focused proofreading agent to find all similar errors

### Request 3: "not just ''' but anythin"
**Intent:** Expand search to ALL punctuation errors, not just triple apostrophes
**Response:** Ran comprehensive punctuation scan finding 20,060 formatting issues

### Request 4: "ok, now lets either edit the current or create a new to debug in the same fashion, test all links and functions, look for text wrapping badly, refer to conversations for context."
**Intent:** Run comprehensive functional testing for links, forms, UI issues
**Response:** Launched functional testing agent finding 87 issues (16 critical)

### Request 5: "i thought it was https?"
**Intent:** Verify correct production URL protocol
**Response:** Confirmed https://rundaverun.org is correct per fact sheet

### Request 6: "yes, and everything else"
**Intent:** Fix ALL remaining issues (duplicate HTML attributes, budget standardization, etc.)
**Response:** Systematically fixed all high-priority issues

### Request 7: "go ahead and push to the live site"
**Intent:** Deploy to production GoDaddy hosting
**Response:** Requested credentials/deployment configuration (user interrupted to request transcript instead)

---

## Investigation & Analysis Process

### Phase 1: Critical Content Errors (Proofreading Report)
**Files Investigated:**
- `/home/dave/skippy/conversations/proofreading_report_20251103.md`
- `/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md`

**Commands Executed:**
```bash
wp post get 940 --field=post_content  # Volunteer Training Guide
wp post get 106 --field=post_content  # About Dave page
wp post get 245 --field=post_content  # About Dave Biggers policy
wp post get 107 --field=post_content  # Our Plan page
wp post get 249 --field=post_content  # Our Plan policy
wp post get 109 --field=post_content  # Contact page
```

**Key Discoveries:**
1. False "former firefighter" claim in Volunteer Training Guide (Post 940)
2. "Fire Station Locations" should be "Mini Police Substation Locations"
3. Policy count wrong: "34" should be "42" in multiple locations
4. Participatory budgeting wrong: "$12M" should be "$15M"
5. Development URL exposed: "rundaverun-local.local" in contact page

### Phase 2: Punctuation Error Scanning
**Agent Launched:** `Task` agent with `general-purpose` type for comprehensive punctuation scanning

**Search Parameters:**
- Multiple consecutive apostrophes/quotes (''', "", etc.)
- Mismatched quotation marks
- Multiple consecutive periods/commas
- Spaces before punctuation
- Missing spaces after punctuation
- HTML entities needing conversion
- Mismatched parentheses/brackets

**Results:**
- Total errors: 20,060
- Most common: Multiple consecutive spaces (18,882 - 94%)
- Critical: Triple apostrophes in posts 716, 717
- High: Space before punctuation (130 instances)
- 1 mismatched parentheses (false positive - list markers A), B), C))

**Report Generated:** `/home/dave/skippy/conversations/punctuation_errors_report_20251103.md`

### Phase 3: Functional Testing
**Agent Launched:** `Task` agent for comprehensive functional and UI testing

**Testing Scope:**
1. Link validation (76 links tested)
2. Form functionality (email signup, volunteer forms)
3. UI/text wrapping issues
4. Shortcode validation
5. Image/media checks
6. Navigation/menu testing
7. Plugin functionality verification
8. Accessibility audit

**Key Findings:**
- 15 broken internal links (19.7% failure rate)
- PHP code exposed in volunteer dashboard (critical)
- Wrong email address (contact@ instead of dave@/info@)
- HTTP URLs instead of HTTPS
- Shortcode placeholders [NAME], [NUMBER] being interpreted
- Gallery placeholder content
- Privacy policy in draft status
- "Hello world!" default post still published

**Report Generated:** `/home/dave/skippy/conversations/functional_testing_report_20251103.md`

---

## Actions Taken - Detailed Log

### Critical Content Fixes (5 issues)

#### Fix #1: Remove False "Firefighter" Claim (Post 940)
**Location:** Volunteer Training Guide
**Original Text:** 
```html
<li><strong>Experience:</strong> Former firefighter, public safety expert</li>
```
**Fixed Text:**
```html
<li><strong>Experience:</strong> Public safety expert, policy developer</li>
```
**Command:**
```bash
wp post update 940 --post_content='<h1>Volunteer Training Guide</h1>...[updated content]...'
```
**Verification:** `wp post get 940 --field=post_content | grep -q "Former firefighter" || echo "FIXED"`
**Result:** ✓ Fixed - no longer contains false claim

#### Fix #2: Fire Stations → Mini Police Substations (Post 940)
**Location:** Volunteer Training Guide
**Original Text:**
```html
<li><strong>73 Potential Fire Station Locations</strong> - At least one in every ZIP code</li>
```
**Fixed Text:**
```html
<li><strong>73 Potential Mini Police Substation Locations</strong> - At least one in every ZIP code</li>
```
**Command:** Same update as Fix #1 (combined in single update)
**Verification:** `wp post get 940 --field=post_content | grep -q "Mini Police Substation" && echo "FIXED"`
**Result:** ✓ Fixed - correct terminology used

#### Fix #3: Policy Count 34→42 (Posts 106, 245, 107)
**Locations:** 
- Post 106 (About Dave page) - 2 instances
- Post 245 (About Dave Biggers policy) - 1 instance  
- Post 107 (Our Plan page) - 1 instance

**Search/Replace Pattern:**
```bash
sed 's/34 detailed policy documents, including 16 comprehensive platform policies/42 detailed policy documents (16 comprehensive platform policies and 26 implementation documents)/g'
sed 's/34 policy documents (including 16 comprehensive platform policies)/42 policy documents (16 comprehensive platform policies and 26 implementation documents)/g'
sed 's/34 Policy Documents/42 Policy Documents/g'
```

**Commands:**
```bash
wp post get 106 --field=post_content | sed [...] > /tmp/post106_fixed.html
wp post update 106 --post_content="$(cat /tmp/post106_fixed.html)"
wp post update 245 --post_content="$(cat /tmp/post245_fixed.html)"
wp post update 107 --post_content="$(cat /tmp/post107_fixed.html)"
```
**Result:** ✓ All 3 posts updated

#### Fix #4: Participatory Budgeting $12M→$15M (Post 249)
**Location:** Post 249 (Our Plan policy document)
**Instances:** 4 occurrences throughout document

**Search/Replace:**
```bash
sed 's/\$12M&nbsp;Participatory&nbsp;Budgeting/$15M Participatory Budgeting/g'
sed 's/<h2>4. YOUR VOICE: \$12M<\/h2>/<h2>4. YOUR VOICE: $15M<\/h2>/g'
sed 's/Participatory budgeting: +\$12M/Participatory budgeting: +$15M/g'
sed 's/Participatory Budgeting (6 Districts): \$12M/Participatory Budgeting (6 Districts): $15M/g'
```
**Command:**
```bash
wp post get 249 --field=post_content | sed [...] > /tmp/post249_fixed.html
wp post update 249 --post_content="$(cat /tmp/post249_fixed.html)"
```
**Result:** ✓ All instances updated to $15M

#### Fix #5: Development URL → Production URL (Post 109)
**Location:** Contact page
**Original:**
```html
<a href="http://rundaverun-local.local" style="color: #003f87">rundaverun.org</a>
```
**Fixed:**
```html
<a href="https://rundaverun.org" style="color: #003f87">rundaverun.org</a>
```
**Command:**
```bash
wp post get 109 --field=post_content | sed 's|http://rundaverun-local\.local|https://rundaverun.org|g' > /tmp/post109_fixed.html
wp post update 109 --post_content="$(cat /tmp/post109_fixed.html)"
```
**Result:** ✓ Production URL now used

### Punctuation Fixes (2 critical issues)

#### Fix #6: Triple Apostrophes (Posts 716, 717)
**Discovery:** Posts 716 and 717 had extensive use of `'''` instead of `'`

**Post 716 (Health & Human Services):**
- Issues found: Multiple instances in FAQ section
- Examples: "isn'''t", "don'''t", "can'''t"

**Post 717 (Economic Development & Jobs):**
- Issues found: Extensive throughout document (hundreds of instances)
- Examples: "we'''re", "workers'''", "don'''t"

**Fix Applied:**
```bash
wp post get 716 --field=post_content | sed "s/'''/'/g" > /tmp/post716_fixed.html
wp post update 716 --post_content="$(cat /tmp/post716_fixed.html)"

wp post get 717 --field=post_content | sed "s/'''/'/g" > /tmp/post717_fixed.html
wp post update 717 --post_content="$(cat /tmp/post717_fixed.html)"
```
**Verification:**
```bash
wp post get 716 --field=post_content | grep -c "'''"  # Result: 0
wp post get 717 --field=post_content | grep -c "'''"  # Result: 0
```
**Result:** ✓ All triple apostrophes converted to single apostrophes

#### Fix #7: Space Before Punctuation (Post 106)
**Issue:** Spaces before periods, commas, question marks
**Example:** `"word ."` instead of `"word."`

**Fix Applied:**
```bash
wp post get 106 --field=post_content | sed -E 's/ ([.?!,;:])/\1/g' > /tmp/post106_fixed.html
wp post update 106 --post_content="$(cat /tmp/post106_fixed.html)"
```
**Result:** ✓ Spaces removed before punctuation

### Functional & Link Fixes (6 critical issues)

#### Fix #8: PHP Code Exposed in Volunteer Dashboard (Post 934)
**Issue:** Raw PHP code visible in HTML instead of being executed
**Location:** Volunteer Dashboard logout link

**Original:**
```html
<a href="<?php echo wp_logout_url( home_url() ); ?>" style="color: #003f87; text-decoration: underline;">Log Out</a>
```
**Problem:** PHP code in page content won't execute, appears as text

**Fixed:**
```html
<a href="/wp-login.php?action=logout" style="color: #003f87; text-decoration: underline;">Log Out</a>
```
**Command:**
```bash
wp post get 934 --field=post_content | sed 's|<a href="<?php echo wp_logout_url( home_url() ); ?>"|<a href="/wp-login.php?action=logout"|g' > /tmp/post934_fixed.html
wp post update 934 --post_content="$(cat /tmp/post934_fixed.html)"
```
**Result:** ✓ Functional logout link

#### Fix #9: Broken Glossary Links (Posts 151, 328, 934)
**Issue:** Links pointing to `/glossary/` but actual page is `/voter-education-glossary/`
**Affected Posts:** 151, 328, 934

**Fix Applied:**
```bash
wp post get 151 --field=post_content | sed 's|href="/glossary/"|href="/voter-education-glossary/"|g' > /tmp/post151_fixed.html
wp post update 151 --post_content="$(cat /tmp/post151_fixed.html)"

wp post get 328 --field=post_content | sed 's|href="/glossary/"|href="/voter-education-glossary/"|g' > /tmp/post328_fixed.html
wp post update 328 --post_content="$(cat /tmp/post328_fixed.html)"

wp post get 934 --field=post_content | sed 's|href="/glossary/"|href="/voter-education-glossary/"|g' > /tmp/post934_fixed.html
wp post update 934 --post_content="$(cat /tmp/post934_fixed.html)"
```
**Result:** ✓ All glossary links corrected

#### Fix #10: Malformed Economic Development Slug (Post 717)
**Issue:** Post slug was `economic-development-jobspolicy-08-economic-development` (concatenated/malformed)
**Correct Slug:** `economic-development-jobs`

**Commands:**
```bash
# Fix the post slug itself
wp post update 717 --post_name="economic-development-jobs"

# Update homepage link to new slug
wp post get 105 --field=post_content | sed 's|/policy/economic-development-jobspolicy-08-economic-development/|/policy/economic-development-jobs/|g' > /tmp/post105_fixed.html
wp post update 105 --post_content="$(cat /tmp/post105_fixed.html)"
```
**Result:** ✓ Clean slug and working link

#### Fix #11: Wrong Email Address (Post 105)
**Location:** Homepage social bar
**Original:** `contact@rundaverun.org`
**Issue:** Email not listed in campaign fact sheet (only dave@ and info@)
**Fixed:** `dave@rundaverun.org`

**Command:**
```bash
wp post get 105 --field=post_content | sed 's|contact@rundaverun.org|dave@rundaverun.org|g' > /tmp/post105_email_fixed.html
wp post update 105 --post_content="$(cat /tmp/post105_email_fixed.html)"
```
**Result:** ✓ Correct email address used

#### Fix #12: HTTP → HTTPS URLs (Posts 699, 700)
**Issue:** Using insecure HTTP instead of HTTPS for internal links
**Locations:**
- Post 699 (Public Safety) - 3 instances
- Post 700 (Criminal Justice) - 1 instance

**Search Pattern:** `http://rundaverun.org`
**Replace:** `https://rundaverun.org`

**Commands:**
```bash
wp post get 699 --field=post_content | sed 's|http://rundaverun.org|https://rundaverun.org|g' > /tmp/post699_fixed.html
wp post update 699 --post_content="$(cat /tmp/post699_fixed.html)"

wp post get 700 --field=post_content | sed 's|http://rundaverun.org|https://rundaverun.org|g' > /tmp/post700_fixed.html
wp post update 700 --post_content="$(cat /tmp/post700_fixed.html)"
```
**Result:** ✓ All URLs now use HTTPS

#### Fix #13: Shortcode Placeholders (Posts 941, 942)
**Issue:** Placeholder text like `[NAME]`, `[YOUR NAME]`, `[CONTACT NAME]` being interpreted as WordPress shortcodes
**Affected Documents:**
- Post 941: Phone Banking Script
- Post 942: Canvassing Talking Points

**Problem:** WordPress processes square brackets as shortcodes, causing content to disappear

**Solution:** Escape square brackets using HTML entities
- `[` → `&#91;`
- `]` → `&#93;`

**Commands:**
```bash
wp post get 941 --field=post_content | sed 's/\[/&#91;/g' | sed 's/\]/&#93;/g' > /tmp/post941_fixed.html
wp post update 941 --post_content="$(cat /tmp/post941_fixed.html)"

wp post get 942 --field=post_content | sed 's/\[/&#91;/g' | sed 's/\]/&#93;/g' > /tmp/post942_fixed.html
wp post update 942 --post_content="$(cat /tmp/post942_fixed.html)"
```
**Result:** ✓ Placeholders now display correctly, not processed as shortcodes

### Budget Standardization (4 issues)

**Reference Source:** `/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md`

**Authoritative Figures:**
- Mini Substations: $77.4M
- Public Safety Total: $81M ($77.4M + $3.6M detectives)
- Wellness Centers: $34.2M investment
- Wellness Centers ROI: $1.80 saved per dollar (NOT $3.00)

#### Fix #14: Public Safety Budget (Post 699)
**Inconsistencies Found:**
- Total: "$110.5 million annually" (wrong - should be $81M)
- Substations: "$47.5 million over 4 years" (wrong - should be $77.4M)

**Fix Applied:**
```bash
wp post get 699 --field=post_content | \
  sed 's/\$110\.5 million annually/\$81 million total (\$77.4M substations + \$3.6M detectives)/g' | \
  sed 's/\$47\.5 million over 4 years/\$77.4 million investment/g' > /tmp/post699_budget_fixed.html
wp post update 699 --post_content="$(cat /tmp/post699_budget_fixed.html)"
```
**Result:** ✓ Standardized to fact sheet figures

#### Fix #15: Wellness Centers Budget & ROI (Posts 105, 107, 716)
**Inconsistencies:**
- Budget: $36M, $45M (wrong - should be $34.2M)
- ROI: "$3 saved per dollar" (wrong - should be $1.80)

**Post 716 (Health & Human Services):**
```bash
wp post get 716 --field=post_content | \
  sed 's/\$45 million annually/\$34.2 million investment/g' | \
  sed 's/\$3 saved for every \$1 spent/\$1.80 saved for every \$1 spent/g' | \
  sed 's/\$3\.00 saved/\$1.80 saved/g' > /tmp/post716_budget_fixed.html
wp post update 716 --post_content="$(cat /tmp/post716_budget_fixed.html)"
```

**Post 105 (Homepage):**
```bash
wp post get 105 --field=post_content | \
  sed 's/\$3 for every \$1 spent/\$1.80 saved for every \$1 spent/g' | \
  sed 's/Saves \$3 for/Saves \$1.80 for/g' > /tmp/post105_roi_fixed.html
wp post update 105 --post_content="$(cat /tmp/post105_roi_fixed.html)"
```

**Post 107 (Our Plan):**
```bash
wp post get 107 --field=post_content | sed 's/\$36M/\$34.2M/g' > /tmp/post107_budget_fixed.html
wp post update 107 --post_content="$(cat /tmp/post107_budget_fixed.html)"
```
**Result:** ✓ All documents now use consistent $34.2M budget and $1.80 ROI

### Quality Improvements (5 issues)

#### Fix #16: Duplicate HTML Style Attributes (Post 106)
**Issue:** Invalid HTML with multiple style attributes on single element
**Example:**
```html
<h2 style="text-align: center;" style="color: #003f87; font-size: 2.2em;">
```
**Problem:** HTML spec allows only ONE style attribute per element

**Fix Pattern:** Combine into single attribute
```bash
sed -E 's/(<[^>]+)style="([^"]*)" style="([^"]*)"([^>]*>)/\1style="\2; \3"\4/g'
```
**Command:**
```bash
wp post get 106 --field=post_content | sed -E 's/(<[^>]+)style="([^"]*)" style="([^"]*)"([^>]*>)/\1style="\2; \3"\4/g' > /tmp/post106_styles_fixed.html
wp post update 106 --post_content="$(cat /tmp/post106_styles_fixed.html)"
```
**Result:** ✓ Valid HTML with combined style attributes

#### Fix #17: Delete Default WordPress Post
**Issue:** "Hello world!" default post (ID: 1) still published
**Command:**
```bash
wp post delete 1 --force
```
**Result:** ✓ Default post deleted

#### Fix #18: Campaign Slogan Standardization
**Issue:** Site tagline used articles ("A Mayor That Listens, A Government That Responds")
**Fact Sheet Version:** "Mayor That Listens, Government That Responds" (no articles)

**Command:**
```bash
wp option get blogdescription  # Current: "A Mayor That Listens, A Government That Responds"
wp option update blogdescription "Mayor That Listens, Government That Responds"
```
**Result:** ✓ Tagline matches fact sheet

#### Fix #19: Gallery Placeholders
**Investigation:**
```bash
wp post get 105 --field=post_content | grep -i "placeholder"  # No results
```
**Result:** ✓ Already removed (no action needed)

#### Fix #20: Grammar Issues
**Investigation:**
```bash
wp post get 245 --field=post_content | grep "rely heavy"  # No results
```
**Result:** ✓ Already fixed (no action needed)

### Privacy Policy Creation (Fix #21)

**Issue:** Privacy Policy (Post ID: 3) was in draft status with default WordPress template

**Action:** Created comprehensive campaign-specific privacy policy

**Content Sections Created:**
1. Introduction
2. Information We Collect (opt-in, ZIP codes, volunteer data)
3. How We Use Your Information
4. Information Sharing (explicitly states: "We do not sell, rent, or trade your personal information")
5. Your Rights (unsubscribe, access, correct, delete)
6. Email Communications (double opt-in process)
7. Data Security (HTTPS, secure storage)
8. Children's Privacy (under 13 policy)
9. Third-Party Links
10. California Privacy Rights (CCPA compliance)
11. Changes to Policy
12. Contact Information
13. Political Campaign Notice (campaign finance compliance)

**Key Features:**
- Campaign-specific (not generic template)
- Mentions double opt-in email verification
- States explicitly: no selling of data
- Includes campaign contact info (PO Box, email)
- Addresses political campaign use

**Command:**
```bash
cat > /tmp/privacy_policy.html << 'EOF'
[Full privacy policy HTML content]
