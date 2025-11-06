# Campaign Content Approval Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Owner:** Claude Code / Dave

---

## Context

Campaign content (policies, budget, claims) requires fact-checking and approval before publication.

## Purpose

- Ensure accuracy of published content
- Prevent false or misleading claims
- Maintain credibility
- Provide approval workflow

---

## Content Categories

### High Risk (Requires Fact-Checking)
- Budget numbers and financial data
- Policy implementation timelines
- Statistical claims
- Quotes from documents
- Legal interpretations

### Medium Risk (Requires Review)
- Policy descriptions
- Program details
- Contact information
- Event information

### Low Risk (Standard Review)
- General campaign messaging
- Biography
- Endorsements (with written permission)
- Event announcements

---

## Approval Workflow

### For Policy Documents

**Step 1: Draft Creation**
```
- Create in staging/draft
- Include source citations
- Note any assumptions
```

**Step 2: Fact-Checking**
```
- Verify all numerical claims
- Cross-reference with source documents
- Check implementation feasibility
- Verify legal accuracy (if applicable)
```

**Step 3: Source Documentation**
```
- Add "Source:" citations on page
- Include links to official documents
- Document methodology for calculations
```

**Step 4: Dave Approval**
```
- Review draft
- Verify accuracy
- Approve or request changes
- Sign off explicitly
```

**Step 5: Pre-Publication Validation**
```bash
bash ~/rundaverun/campaign/skippy-scripts/wordpress/pre_deployment_validator_v1.0.0.sh
```

**Step 6: Publication**
```
- Deploy to production
- Verify published correctly
- Monitor for issues
```

---

## Budget Information Protocol

### Requirements
1. **Must match official city budget documents**
2. **Must include source URL/citation**
3. **Must be current fiscal year**
4. **Must explain methodology if calculated**

### Verification Steps
```bash
# 1. Get source document
curl -O [official-budget-url]

# 2. Extract relevant numbers
grep "Public Safety" official_budget.pdf

# 3. Compare with draft
# 4. Document any differences
# 5. Get Dave approval if numbers differ
```

### Example Citation
```
Source: FY2026 City Budget, Public Safety Department
URL: https://city.gov/budget/fy2026/public-safety
Retrieved: 2025-11-06
```

---

## Prohibited Without Verification

**Never publish without source verification:**
- ❌ Budget numbers
- ❌ Crime statistics
- ❌ Demographic data
- ❌ Economic projections
- ❌ Program costs
- ❌ Implementation timelines (if specific)

**Can publish with general approval:**
- ✅ Campaign goals
- ✅ General policy positions
- ✅ Event information
- ✅ Contact information
- ✅ Volunteer opportunities

---

## Fact-Checking Checklist

**For Each Claim:**
- [ ] Source document identified
- [ ] Source URL documented
- [ ] Numbers match source
- [ ] Context accurate
- [ ] No misleading framing
- [ ] Current/up-to-date
- [ ] Dave reviewed and approved

---

## Red Flags (Require Extra Scrutiny)

- Round numbers (might be estimates)
- "Approximately" or "about"
- Projections or forecasts
- Comparisons to other cities
- Historical data (verify year)
- Percentages (verify calculation)

---

## Approval Documentation

### Track in Conversation File
```markdown
## Content Approval Log

**Page:** Budget Overview
**Date:** 2025-11-06
**Changes:** Updated FY2026 public safety allocation
**Sources:** 
  - FY2026 Budget Document (https://...)
  - Department breakdown spreadsheet
**Verified By:** Dave
**Status:** Approved for publication
```

---

## Emergency Content Updates

**If Error Found After Publication:**

1. **Immediately** mark page for review
2. Add correction notice if visible to public
3. Prepare corrected version
4. Fact-check correction
5. Get expedited approval
6. Deploy correction
7. Document in changelog

---

## Best Practices

### DO:
✅ Cite sources on page
✅ Use official documents
✅ Get Dave approval for claims
✅ Document methodology
✅ Keep sources accessible

### DON'T:
❌ Publish unverified numbers
❌ Make assumptions about data
❌ Skip fact-checking "small" changes
❌ Use outdated information
❌ Publish without approval

---

**Generated:** 2025-11-06
**Status:** Active
**Next Review:** 2025-12-06
