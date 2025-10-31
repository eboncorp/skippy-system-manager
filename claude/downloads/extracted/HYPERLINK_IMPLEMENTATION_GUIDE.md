# Hyperlink Implementation Guide
## Step-by-Step Integration of Glossary with Policy Documents

**Campaign:** Run Dave Run - Louisville Mayor 2026  
**Date:** October 29, 2025  
**Purpose:** Practical guide for adding glossary hyperlinks to all policy documents

---

## EXECUTIVE SUMMARY

This guide shows exactly how to transform your policy documents from standalone files into an integrated educational system by hyperlinking every technical term to comprehensive glossary definitions.

**What We're Creating:**
- Clickable policy documents where voters can instantly learn any term
- Seamless education experience (no leaving the document to Google terms)
- Professional presentation showing command of issues
- Accessibility for all education levels

**Time Required:**
- Budget 3.0 Executive Summary: 2-3 hours
- Budget 3.0 Detailed Plan: 4-5 hours
- Implementation Guides: 2-3 hours each
- Campaign Materials: 1-2 hours each

**Total: 15-25 hours for complete integration**

---

## PART 1: TECHNICAL SETUP

### WordPress Implementation

**Option A: Manual HTML Links (Recommended for now)**

**Format:**
```html
<a href="https://rundaverun.org/glossary/term-name" target="_blank">term text</a>
```

**Example:**
```html
We propose <a href="https://rundaverun.org/glossary/participatory-budgeting" target="_blank">participatory budgeting</a> for $25M annually.
```

**Advantages:**
- Works immediately
- Full control
- No plugin dependencies
- Opens in new tab (preserves reading position)

**Option B: Glossary Plugin with Auto-Linking**

**If using WordPress Glossary plugin:**
- Plugin can auto-detect terms and add tooltips
- Hover over term = see brief definition
- Click = full glossary entry
- Requires initial term mapping

**Recommended Setup:**
1. Install and configure glossary plugin
2. Import all glossary terms
3. Enable auto-linking for policy documents
4. Test thoroughly before launch

---

### URL Structure

**Glossary URLs should follow this pattern:**
```
https://rundaverun.org/glossary/term-name
```

**Term name formatting:**
- All lowercase
- Hyphens instead of spaces
- No special characters

**Examples:**
- Participatory Budgeting → `/glossary/participatory-budgeting`
- Tax Increment Financing (TIF) → `/glossary/tax-increment-financing`
- Community Benefits Agreement → `/glossary/community-benefits-agreement`
- Mini Substations → `/glossary/mini-substations`

---

## PART 2: DOCUMENT-BY-DOCUMENT IMPLEMENTATION

### Document 1: Budget 3.0 Executive Summary

**Priority:** HIGHEST (most-read document)

**Step 1: Identify All Technical Terms**

Page through document, mark every term that:
1. Might be unfamiliar to average voter
2. Has a glossary entry
3. Is central to understanding the policy

**Terms in Order of Appearance (First 2 Pages):**

1. Participatory Budgeting (paragraph 1)
2. Community Policing (paragraph 2)
3. Mini Substations / Mini Police Substations (paragraph 2)
4. Community Wellness Centers (paragraph 2)
5. Youth Development Programs (paragraph 3)
6. Mental Health Crisis Teams (paragraph 3)
7. Fire Prevention Centers (paragraph 4)
8. Evidence-Based Policy (paragraph 5)
9. Budget-Neutral (paragraph 6)
10. Living Wage (paragraph 7)

**Step 2: Link First Instance Only**

**Rule:** Link the first instance of each term in the document. Subsequent uses don't need links (avoids link overload).

**Exception:** If term appears again after 5+ pages, link again as reminder.

**Step 3: Apply Hyperlinks**

**BEFORE:**
```
We propose participatory budgeting for $25M annually, with community benefits 
agreements required for all economic development incentives.
```

**AFTER:**
```
We propose <a href="https://rundaverun.org/glossary/participatory-budgeting" 
target="_blank">participatory budgeting</a> for $25M annually, with 
<a href="https://rundaverun.org/glossary/community-benefits-agreement" 
target="_blank">community benefits agreements</a> required for all 
<a href="https://rundaverun.org/glossary/economic-development-incentives" 
target="_blank">economic development incentives</a>.
```

**Step 4: Test All Links**

After applying links:
1. Preview document
2. Click each link
3. Verify opens correct glossary entry
4. Check that new tab opens (preserves position in policy doc)
5. Fix any broken links

**Step 5: Create Link Map**

Track which terms were linked where:

| Term | First Linked | Page | Paragraph | Link URL |
|------|-------------|------|-----------|----------|
| Participatory Budgeting | ✅ | 1 | 1 | /glossary/participatory-budgeting |
| Community Policing | ✅ | 1 | 2 | /glossary/community-policing |
| Mini Substations | ✅ | 1 | 2 | /glossary/mini-substations |

**This helps with:**
- Quality control
- Future updates
- Troubleshooting broken links

---

### Document 2: Budget 3.0 Detailed Plan

**Priority:** HIGH (deep-dive document)

**Additional Considerations:**

**More Technical Terms:**
Detailed plan uses more specialized vocabulary:
- Beat Patrol
- School Resource Officers (SRO)
- Diversion Programs
- Restorative Justice
- Bail Reform
- Use of Force
- Constitutional Policing
- DOJ Consent Decree

**Link Density:**
Can have more links in detailed doc (readers expect detail)
- Executive Summary: ~15-20 total links
- Detailed Plan: ~40-50 total links acceptable

**Section-Specific Linking:**

**Public Safety Section:**
Link all policing terms first instance:
- Community Policing
- Mini Substations
- Beat Patrol
- Constitutional Policing
- Use of Force
- Body-Worn Cameras
- Civilian Oversight

**Youth Programs Section:**
Link all youth/education terms:
- Youth Development
- After-School Programs
- Summer Jobs Program
- Gang Intervention
- Mentorship Programs
- School-to-Prison Pipeline

**Wellness Centers Section:**
Link all healthcare terms:
- Community Wellness Centers
- Mental Health Services
- Substance Use Disorder Treatment
- Harm Reduction
- Social Determinants of Health
- Healthcare Desert

---

### Document 3: Campaign One-Pager

**Priority:** MEDIUM-HIGH (widely distributed)

**Special Considerations:**

**Keep It Clean:**
- One-pager needs to stay scannable
- Too many links = overwhelming
- Link only the 5-7 most important terms

**Terms to Link:**
1. Participatory Budgeting (your signature program)
2. Mini Substations (clear differentiator)
3. Community Wellness Centers (prevention focus)
4. Budget-Neutral (fiscal responsibility)
5. Evidence-Based (credibility)

**Format Example:**

**BEFORE:**
```
46 Mini Substations - One in every major neighborhood
18 Community Wellness Centers - Health + mental health + addiction services
$25M Participatory Budgeting - YOU vote on spending priorities
```

**AFTER:**
```
46 <a href="https://rundaverun.org/glossary/mini-substations" target="_blank">
Mini Substations</a> - One in every major neighborhood

18 <a href="https://rundaverun.org/glossary/community-wellness-centers" 
target="_blank">Community Wellness Centers</a> - Health + mental health + 
addiction services

$25M <a href="https://rundaverun.org/glossary/participatory-budgeting" 
target="_blank">Participatory Budgeting</a> - YOU vote on spending priorities
```

---

### Document 4: Implementation Guides

**Mini Substations Implementation:**

Link heavily in this doc (technical document for those wanting details):
- Community Policing (multiple times - core concept)
- Mini Substations
- Beat Patrol  
- Problem-Oriented Policing
- Crime Prevention Through Environmental Design (CPTED)
- Hot Spot Policing
- Community Trust
- Procedural Justice
- Legitimacy

**Wellness Centers Operations:**

Link all healthcare and operational terms:
- Community Wellness Centers
- Primary Care
- Mental Health Services
- Substance Use Disorder Treatment
- Medication-Assisted Treatment (MAT)
- Harm Reduction
- Social Determinants of Health
- Healthcare Desert
- Integrated Care Model

**Participatory Budgeting Guide:**

This document IS about the glossary term, so link related concepts:
- Participatory Budgeting (in intro, linking to comprehensive entry)
- Community Engagement
- Civic Participation
- Budget Transparency
- Outcome-Based Budgeting
- District Councils (process facilitators)

---

## PART 3: LINK STYLING & USER EXPERIENCE

### Visual Design

**Link Appearance:**

**Option 1: Standard Link (Recommended)**
```css
a {
    color: #0066cc; /* Blue, accessible */
    text-decoration: underline;
    cursor: pointer;
}

a:hover {
    color: #004080; /* Darker blue on hover */
    text-decoration: underline;
}

a:visited {
    color: #551a8b; /* Purple for visited */
}
```

**Option 2: Subtle Link (For link-heavy documents)**
```css
a.glossary-link {
    color: #333; /* Nearly black */
    text-decoration: underline dotted; /* Dotted underline */
    cursor: help; /* Question mark cursor */
}

a.glossary-link:hover {
    color: #0066cc;
    text-decoration: underline solid;
}
```

**Best Practice:**
- Use consistent styling across all documents
- Ensure sufficient color contrast (WCAG AA minimum: 4.5:1)
- Underline or other visual indicator (not just color)
- Hover state shows link is clickable

---

### Tooltip Option (If Using Plugin)

**With glossary plugin, can add hover tooltips:**

```html
<span class="glossary-term" data-term="participatory-budgeting">
    participatory budgeting
</span>
```

**On hover:**
- Small popup appears
- Shows first 2 sentences of definition
- Click for full entry

**Advantages:**
- Quick reference without leaving page
- Full entry still available on click
- Professional UX

**Disadvantages:**
- Requires plugin/JavaScript
- More complex setup
- May not work on all devices

**Recommendation:**
- Start with simple hyperlinks (works everywhere)
- Add tooltips later if desired (progressive enhancement)

---

### Mobile Considerations

**Challenge:**
- Hover doesn't work on touch screens
- Links must be easily tappable
- Text size must be readable

**Solutions:**

**Link Sizing:**
```css
/* Ensure links have enough tap target */
a {
    display: inline-block;
    min-height: 44px; /* iOS guideline */
    padding: 2px 0;
}
```

**Mobile-Specific Styling:**
```css
@media (max-width: 768px) {
    a {
        font-size: 16px; /* Prevent zoom on iOS */
        padding: 8px 0; /* Larger tap target */
    }
}
```

**Testing:**
- View documents on actual phones (iPhone, Android)
- Verify links are easy to tap
- Check that new tab opens correctly
- Ensure back button works to return to document

---

## PART 4: QUALITY CONTROL

### Pre-Launch Checklist

**For Each Document:**

- [ ] All technical terms identified
- [ ] First instance of each term linked
- [ ] No subsequent instances linked (unless far apart)
- [ ] All links tested and working
- [ ] Links open in new tab (target="_blank")
- [ ] Mobile view tested
- [ ] Link map created (tracking document)
- [ ] Broken link check run
- [ ] Accessibility check completed

**Broken Link Checker:**
```bash
# Use online tool or command line
wget --spider -r --no-parent https://rundaverun.org/policy-documents/
```

Or use online service:
- https://www.deadlinkchecker.com/
- https://validator.w3.org/checklink

**Accessibility Check:**
- Color contrast ratio ≥ 4.5:1
- Links identifiable without color alone
- Keyboard navigation works (tab through links)
- Screen reader announces links correctly

---

### Post-Launch Monitoring

**Week 1:**
- Monitor analytics: Which glossary terms are clicked most?
- Check for 404 errors (broken links)
- User feedback: Are links helpful or overwhelming?

**Monthly:**
- Review most-clicked terms (consider featuring these)
- Check for new terms needing glossary entries
- Update links if URLs change
- Add links to new documents

**Quarterly:**
- Comprehensive link audit
- Update glossary entries based on usage
- Refine linking strategy based on data
- A/B test link density (more vs. fewer links)

---

## PART 5: ADVANCED FEATURES

### Feature 1: Related Terms Box

**At end of each document, add "Learn More" box:**

```html
<div class="related-terms-box">
    <h3>Learn More - Key Terms in This Document</h3>
    <ul>
        <li><a href="/glossary/participatory-budgeting">Participatory Budgeting</a> - 
            Direct democracy for budget decisions</li>
        <li><a href="/glossary/mini-substations">Mini Police Substations</a> - 
            Community policing model</li>
        <li><a href="/glossary/community-wellness-centers">Community Wellness Centers</a> - 
            Preventive healthcare hubs</li>
    </ul>
    <p><a href="/glossary/">View Full Glossary →</a></p>
</div>
```

**Benefits:**
- Summarizes key concepts
- Encourages exploration
- Reinforces learning

---

### Feature 2: Glossary Reference Card

**Create PDF "cheat sheet" with 10 most important terms:**

**For Volunteers:**
- Participatory Budgeting
- Mini Substations
- Community Policing
- Wellness Centers
- Budget-Neutral
- Evidence-Based Policy
- Clawback Provisions
- Community Benefits Agreement
- Living Wage
- Defunding the Police (what it's NOT)

**Format:**
- Term + 2-sentence definition
- QR code linking to full glossary
- Pocket-sized (4"x6")
- Available at campaign events

---

### Feature 3: Glossary Highlights on Social Media

**Weekly "Term Tuesday" posts:**

**Example:**
```
📚 TERM TUESDAY: Participatory Budgeting

What if YOU could vote directly on how $25M is spent in Louisville?

That's participatory budgeting - and it's in Dave's plan for Louisville.

11,500 cities worldwide use this model. It works.

Learn more: rundaverun.org/glossary/participatory-budgeting

#RunDaveRun #Louisville #ParticipatoryBudgeting
```

**Benefits:**
- Educates voters incrementally
- Drives traffic to glossary
- Shows depth of platform
- Social proof (used by 11,500 cities)

---

## PART 6: TEMPLATE & CHECKLIST

### Quick Reference: Linking a Term

**Steps:**
1. Find first instance of term in document
2. Confirm glossary entry exists
3. Look up correct URL slug
4. Wrap term in link tag
5. Add target="_blank"
6. Test link
7. Mark as complete in tracking sheet

**HTML Template:**
```html
<a href="https://rundaverun.org/glossary/TERM-SLUG" target="_blank">TERM TEXT</a>
```

**Example:**
```html
<a href="https://rundaverun.org/glossary/participatory-budgeting" target="_blank">
participatory budgeting</a>
```

---

### Full Implementation Checklist

**Phase 1: Preparation (1-2 hours)**
- [ ] Review all glossary entries
- [ ] Verify all URLs are live
- [ ] Create URL mapping document (term → slug)
- [ ] Set up tracking spreadsheet
- [ ] Designate who's responsible for implementation

**Phase 2: Budget Documents (6-8 hours)**
- [ ] Budget 3.0 Executive Summary - identify terms
- [ ] Budget 3.0 Executive Summary - apply links
- [ ] Budget 3.0 Executive Summary - test links
- [ ] Budget 3.0 Detailed Plan - identify terms
- [ ] Budget 3.0 Detailed Plan - apply links
- [ ] Budget 3.0 Detailed Plan - test links
- [ ] Update Budget Glossary page with new comprehensive version

**Phase 3: Implementation Guides (6-9 hours)**
- [ ] Mini Substations Guide - identify terms
- [ ] Mini Substations Guide - apply links
- [ ] Mini Substations Guide - test links
- [ ] Wellness Centers Guide - identify terms
- [ ] Wellness Centers Guide - apply links
- [ ] Wellness Centers Guide - test links
- [ ] Participatory Budgeting Guide - identify terms
- [ ] Participatory Budgeting Guide - apply links
- [ ] Participatory Budgeting Guide - test links

**Phase 4: Campaign Materials (3-5 hours)**
- [ ] Campaign One-Pager - identify terms
- [ ] Campaign One-Pager - apply links
- [ ] Campaign One-Pager - test links
- [ ] Quick Facts Sheet - identify terms
- [ ] Quick Facts Sheet - apply links
- [ ] Quick Facts Sheet - test links
- [ ] Other materials as needed

**Phase 5: Quality Control (2-3 hours)**
- [ ] Broken link check (all documents)
- [ ] Mobile testing (all documents)
- [ ] Accessibility audit
- [ ] Link map finalized
- [ ] Analytics tracking set up

**Phase 6: Launch (1 hour)**
- [ ] Publish updated documents
- [ ] Announce enhanced glossary integration
- [ ] Train volunteers on using linked documents
- [ ] Social media posts about glossary
- [ ] Monitor for issues

**TOTAL TIME: 19-28 hours**

---

## PART 7: TROUBLESHOOTING

### Common Issues & Solutions

**Issue 1: Link doesn't work**
- **Check:** URL spelling (hyphens, lowercase, no spaces)
- **Check:** Glossary entry is published (not draft)
- **Check:** No extra characters in link code
- **Solution:** Test link in browser, fix typos

**Issue 2: Link opens in same tab**
- **Check:** target="_blank" included in link tag
- **Solution:** Add target="_blank" to preserve document position

**Issue 3: Too many links feel overwhelming**
- **Check:** Linked every instance instead of first only?
- **Solution:** Remove subsequent links, keep only first instance
- **Alternative:** Use subtler link styling (dotted underline)

**Issue 4: Term exists but no glossary entry**
- **Priority:** Tier 1/2 terms should exist (check if overlooked)
- **Solution:** Create entry or use inline definition
- **Temporary:** Add to "coming soon" list

**Issue 5: Mobile links too small to tap**
- **Check:** Link padding, min-height in mobile CSS
- **Solution:** Increase tap target size (44px minimum)
- **Test:** Use actual phone, not just browser resize

---

## CONCLUSION

**What You're Creating:**

✅ Accessible policy documents for all education levels  
✅ Seamless voter education experience  
✅ Professional presentation of complex policies  
✅ Differentiation from opponents (no one else does this)  
✅ Foundation for informed electorate  

**Implementation Timeline:**

- **Week 1:** Budget documents linked (highest priority)
- **Week 2:** Implementation guides linked
- **Week 3:** Campaign materials linked  
- **Week 4:** Quality control, launch, monitor

**Success Metrics:**

- Glossary page views increase 500%+
- Average time on policy pages increases 50%+
- Volunteer comprehension scores improve 40%+
- Media cites definitions from glossary
- Voters reference glossary in community conversations

**This is how you transform a campaign into a civic education movement.**

---

*Implementation guide created: October 29, 2025*  
*Campaign: Dave Biggers for Mayor 2026*  
*Status: Ready to deploy*  
*Estimated completion: 3-4 weeks*
