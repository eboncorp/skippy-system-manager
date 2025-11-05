# Content Publishing Protocol

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Owner:** Content Team
**Status:** Active

---

## Purpose

Ensure all published content is accurate, validated, and error-free before going live, preventing factual errors, broken links, and technical issues that could damage campaign credibility.

## Scope

This protocol applies to:
- Website pages and posts
- Policy documents
- Blog posts
- Press releases
- Email campaigns
- Social media (when posted via website)

---

## Pre-Publishing Checklist

### Content Review
- [ ] Factual accuracy verified against fact sheet
- [ ] Budget figures match approved numbers ($1.2B total, $15M wellness, etc.)
- [ ] No false biographical claims (firefighter, family status, etc.)
- [ ] Policy positions match campaign platform
- [ ] Dates and numbers double-checked
- [ ] Grammar and spelling checked
- [ ] Tone appropriate for campaign

### Technical Validation
- [ ] Run pre-deployment validator:
  ```bash
  cd /home/dave/Local\ Sites/rundaverun-local/app/public
  /home/dave/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh validate-all
  ```
- [ ] All critical errors resolved (zero tolerance)
- [ ] High-priority errors addressed
- [ ] Internal links tested
- [ ] No development URLs (localhost, .local, etc.)
- [ ] Images optimized and loading
- [ ] Mobile responsive check

### SEO Optimization
- [ ] Meta title set (50-60 characters)
- [ ] Meta description set (150-160 characters)
- [ ] Focus keyword identified
- [ ] Heading hierarchy correct (H1 → H2 → H3)
- [ ] Alt text on all images
- [ ] URL slug is clean and descriptive
- [ ] Internal linking to related content

### Legal & Compliance
- [ ] No copyright violations
- [ ] Proper attribution for quotes/sources
- [ ] Campaign finance disclosures if needed
- [ ] Privacy policy compliance
- [ ] Accessibility guidelines met (WCAG 2.1 AA)

---

## Validation Integration

### Using Pre-Deployment Validator

**Full Validation:**
```bash
/home/dave/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh validate-all
```

**Quick Fact Check:**
```bash
/home/dave/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh validate-facts
```

**Budget Validation:**
```bash
/home/dave/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh validate-budget
```

**Review Validation Report:**
- Location: `/home/dave/skippy/logs/wordpress/validation_report_*.md`
- Check for CRITICAL, HIGH, and MEDIUM errors
- Address all issues before publishing

---

## Approval Workflow

### Content Types & Required Approvals

**Major Policy Announcements:**
- Content author → Policy team → Campaign manager → Publish

**Standard Pages/Posts:**
- Content author → Editor → Publish

**Updates to Existing Content:**
- Content author → Quick review → Publish

**Emergency/Time-Sensitive:**
- Content author → Campaign manager (verbal OK) → Publish → Follow-up review

---

## Publishing Process

### 1. Staging Review
- [ ] Content created/updated in staging
- [ ] Validation run and passed
- [ ] Approvals obtained
- [ ] Final review completed

### 2. Backup Before Publishing
```bash
# Create backup before major content changes
/home/dave/skippy/scripts/disaster_recovery/dr_automation_v1.0.0.sh backup-wordpress
```

### 3. Publish to Production
- [ ] Content published
- [ ] Cache cleared if needed: `wp cache flush`
- [ ] Published URL tested
- [ ] Mobile view tested
- [ ] Social media preview checked

### 4. Post-Publishing Verification
- [ ] Page loads correctly
- [ ] All links work
- [ ] Images display
- [ ] Forms function (if applicable)
- [ ] No console errors
- [ ] Analytics tracking working

---

## Common Content Errors to Avoid

### Factual Errors (CRITICAL)
- ❌ Dave was a firefighter
- ❌ Wrong budget amounts ($3.00 ROI instead of $3.80)
- ❌ Fire stations instead of mini police substations
- ❌ Wrong family status claims
- ❌ Incorrect policy count

### Technical Errors
- ❌ Development URLs in production
- ❌ Broken internal links
- ❌ Missing images
- ❌ HTTP instead of HTTPS
- ❌ Unoptimized large images

### SEO Errors
- ❌ Missing meta descriptions
- ❌ Duplicate titles
- ❌ Poor URL slugs
- ❌ Missing alt text
- ❌ Keyword stuffing

---

## Emergency Content Updates

### When Emergency Publishing Needed
- Breaking news response
- Urgent campaign announcement
- Crisis communication
- Event cancellation/change

### Expedited Process
1. Create content with senior approval
2. Run quick validator: `validate-facts`
3. Get campaign manager verbal approval
4. Publish immediately
5. Full validation within 1 hour
6. Post-publish review within 24 hours

---

## Content Calendar Integration

**Planning:**
- Schedule content at least 1 week in advance
- Allow time for validation and approvals
- Build buffer for revisions

**Tracking:**
- Use content calendar (spreadsheet/tool)
- Track status: Draft → Review → Approved → Published
- Set reminders for validation checks

---

## Related Protocols
- Pre-Deployment Validator (tool)
- Deployment Checklist Protocol
- Incident Response Protocol (if content causes issues)

---

**Version History:**
- 1.0.0 (2025-11-04): Initial protocol creation
