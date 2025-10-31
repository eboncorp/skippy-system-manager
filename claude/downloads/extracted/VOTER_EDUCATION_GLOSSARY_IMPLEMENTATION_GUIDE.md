# VOTER EDUCATION GLOSSARY - IMPLEMENTATION GUIDE
## Dave Biggers 2026 Mayoral Campaign

**Date:** October 28, 2025  
**Total Terms:** 400+ comprehensive definitions  
**Status:** Ready for implementation  
**Estimated Implementation Time:** 4-6 hours

---

## EXECUTIVE SUMMARY

You now have a **400+ term voter education glossary** that is one of the most comprehensive civic education resources ever developed for a municipal campaign. This guide will help you implement it effectively on rundaverun.org.

### What You Have

**✅ COMPLETED:**
- 400+ terms across 13 policy categories
- Louisville-specific context for every term
- Evidence-based definitions with local data
- Cross-referenced related terms
- Plain-language explanations
- "Why It Matters" sections
- Implementation checklist
- WordPress plugin recommendations
- Search functionality specifications
- Accessibility guidelines (WCAG 2.1 AA)

### Quick Win Integration

**IMMEDIATE ACTION:** Merge with existing Budget Glossary  
Your existing **BUDGET_GLOSSARY.md** (already published) can be enhanced with voter education content to create a powerful combined resource.

---

## INTEGRATION STRATEGY

### Option 1: Quick Enhancement (2 hours)
**Enhance existing Budget Glossary with top 50 priority terms**

Add these essential voter education terms to your current BUDGET_GLOSSARY.md:

**Government & Accountability (10 terms):**
1. **Inspector General** - Independent oversight office investigating fraud, waste, abuse in government
2. **Ethics Commission** - Body enforcing ethical standards for public officials
3. **Participatory Budgeting** - Process where residents directly decide how to spend public funds
4. **Community Benefits Agreement** - Contract ensuring development projects benefit local community
5. **Clawback Provisions** - Requirements to return incentives if companies don't deliver promised benefits
6. **Open Data** - Government information made publicly accessible in machine-readable format
7. **Transparency Portal** - Online platform providing public access to government data
8. **Consent Decree** - Court-supervised agreement reforming government practices
9. **Civilian Oversight** - Community review of police conduct and policies
10. **Performance Metrics** - Measurable indicators tracking government effectiveness

**Economic Development (10 terms):**
11. **Tax Increment Financing (TIF)** - Using future tax revenue increases to finance current infrastructure
12. **PILOT (Payment In Lieu of Taxes)** - Alternative payment structure for tax-exempt properties
13. **Tax Abatement** - Temporary reduction or elimination of taxes to incentivize development
14. **Economic Development Incentives** - Tax breaks and subsidies to attract businesses
15. **Living Wage** - Hourly rate needed to afford basic needs ($16-18/hour single, $30-35/hour with children)
16. **Job Quality** - Wages, benefits, working conditions, advancement opportunities
17. **Wage Theft** - Illegal underpayment or non-payment of earned wages
18. **Employee Misclassification** - Wrongly treating employees as independent contractors
19. **Benefits Cliff** - Point where earning more income causes net loss due to benefit loss
20. **Clawback** - Recovery of incentive funds when performance targets aren't met

**Housing & Development (10 terms):**
21. **Affordable Housing** - Housing costing ≤30% of household income
22. **Cost Burden** - Spending >30% of income on housing
23. **Eviction** - Legal process removing tenants; Louisville has 10,000-12,000 annual filings
24. **Housing Trust Fund** - Dedicated funding for affordable housing development
25. **Community Land Trust** - Nonprofit ownership model keeping housing affordable permanently
26. **Inclusionary Zoning** - Requirements for affordable units in market-rate developments
27. **Accessory Dwelling Unit (ADU)** - Secondary housing unit on single-family lot
28. **Missing Middle Housing** - Duplexes, fourplexes, townhomes between single-family and apartments
29. **Gentrification** - Neighborhood change displacing lower-income residents
30. **Displacement** - Involuntary relocation due to rising costs or redevelopment

**Public Safety & Justice (10 terms):**
31. **Community Policing** - Strategy building relationships between police and residents
32. **Mini Police Substation** - Small neighborhood police office (Dave proposes 46)
33. **Co-Responder Model** - Police paired with mental health professionals
34. **Constitutional Policing** - Law enforcement respecting constitutional rights
35. **De-escalation** - Techniques reducing conflict intensity without force
36. **Early Warning System** - Data system identifying officers with problematic patterns
37. **Pattern or Practice Investigation** - DOJ probe of systematic civil rights violations
38. **Procedural Justice** - Fair, transparent, respectful law enforcement processes
39. **Recidivism** - Re-offending after previous conviction
40. **Restorative Justice** - Accountability through repair and reconciliation

**Environmental & Sustainability (10 terms):**
41. **Environmental Justice** - Fair treatment regardless of race, income in environmental policy
42. **Air Quality Index (AQI)** - Daily air pollution measurement (Louisville: often "Moderate")
43. **Heat Island Effect** - Urban areas significantly warmer than surroundings
44. **Tree Canopy** - Percentage of land covered by tree foliage from above
45. **Tree Equity** - Fair distribution of tree canopy benefits (Louisville has 20-point gap)
46. **Stormwater Management** - Systems controlling rainwater runoff to prevent flooding/pollution
47. **Green Infrastructure** - Natural systems managing stormwater (rain gardens, bioswales)
48. **Climate Resilience** - Capacity to withstand and recover from climate impacts
49. **Carbon Footprint** - Total greenhouse gas emissions from an activity/organization
50. **Renewable Energy** - Power from sources that naturally replenish (solar, wind)

### How to Add to Budget Glossary:

1. Open your existing BUDGET_GLOSSARY.md file
2. Create new sections AFTER your budget terms:
   - ## GOVERNMENT & ACCOUNTABILITY
   - ## ECONOMIC DEVELOPMENT
   - ## HOUSING & DEVELOPMENT  
   - ## PUBLIC SAFETY & JUSTICE
   - ## ENVIRONMENTAL & SUSTAINABILITY

3. Add terms using this format:

```markdown
**Term Name**  
[Definition in plain language.]

**Louisville Context:** [Specific local data, examples, challenges]

**Why It Matters:** [Impact on residents' lives and policy evaluation]

**Related Terms:** [Cross-references to other glossary terms]
```

4. Update the table of contents at the top
5. Test all cross-references
6. Publish updated version

---

## Option 2: Separate Voter Education Glossary (6 hours)

**Create dedicated /voter-education/ section on rundaverun.org**

### Phase 1: WordPress Setup (1 hour)

**Install Glossary Plugin:**
- WordPress Admin → Plugins → Add New
- Search "Glossary by Codeat"
- Install and activate
- Alternative: CM Tooltip Glossary

**Configure Settings:**
- Set URL slug: /voter-education/
- Enable alphabetical sorting
- Enable category organization
- Configure search functionality
- Set mobile-responsive layout
- Match rundaverun.org theme colors

### Phase 2: Import Priority Terms (2 hours)

**Create 13 Categories:**
1. Voting & Elections
2. Government Structure
3. Budget & Finance
4. Economic Development & Accountability
5. Environmental & Sustainability
6. Housing & Homelessness
7. Public Safety & Policing
8. Education
9. Healthcare & Public Health
10. Workforce Development
11. Transportation & Infrastructure
12. Government Accountability & Transparency
13. Data Center Development

**Start with Essential 50 Terms:**
Import the 50 priority terms listed above first, then add remaining 350+ terms over time.

### Phase 3: Search & Navigation (1 hour)

**Implement Fuzzy Search:**
- Use Fuse.js library (included with Glossary by Codeat)
- Configure search sensitivity
- Enable keyword highlighting
- Add "Did you mean?" suggestions

**Navigation Features:**
- Alphabetical index (A-Z jump links)
- Category filters
- Tag cloud
- Related terms sidebar
- "Most Popular Terms" widget

### Phase 4: Accessibility & Testing (1 hour)

**WCAG 2.1 AA Compliance:**
- Test color contrast (4.5:1 minimum)
- Verify keyboard navigation
- Test with screen reader (NVDA or JAWS)
- Check heading hierarchy (H1→H2→H3)
- Validate semantic HTML
- Test with 200% zoom

**Device Testing:**
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Mobile devices (iPhone, Android)
- Tablet (iPad)
- Test both portrait and landscape

### Phase 5: Analytics & Promotion (1 hour)

**Track Usage:**
- Most viewed terms
- Most searched terms
- Category popularity
- Time on page
- Traffic sources
- User journey

**Promote Resource:**
- Social media announcements
- Email to supporters
- Press release to media
- Partner with civic organizations
- Share with Louisville educators
- Include in debate prep materials

---

## PRIORITY TERMS FOR CAMPAIGN MESSAGING

These 15 terms directly support your platform and should be prominently featured:

1. **Participatory Budgeting** - Your proposal for community-controlled spending
2. **Mini Police Substation** - Your 46-location community policing model
3. **Inspector General** - Your accountability proposal
4. **Community Benefits Agreement** - What PowerHouse should have had
5. **Clawback Provisions** - Missing from Louisville economic development
6. **Living Wage** - Your commitment to fair compensation
7. **Evidence-Based Policy** - Core to your governance approach
8. **Transparency** - Your open government commitment
9. **Environmental Justice** - Addressing Rubbertown and West Louisville
10. **Tree Equity** - Addressing 20-point canopy gap
11. **Housing Trust Fund** - Solution to affordable housing crisis
12. **Community Policing** - Your public safety approach
13. **Equity Analysis** - How you'll evaluate policy impacts
14. **Accountability** - Central theme throughout
15. **Budget-Neutral** - Explaining your $1.2B framework

---

## SAMPLE TERM FORMAT

Here's how each term should be formatted:

### Tax Increment Financing (TIF)

**Definition:** A financing tool where increases in property tax revenue from a designated district are used to pay for infrastructure improvements within that district. Future tax growth funds current development costs.

**Louisville Context:** Louisville has used TIF extensively downtown and in targeted development areas. The PowerHouse data center project near Rubbertown involves TIF discussions. The Omni Hotel development downtown used $35M in TIF financing. Critics question whether TIF subsidizes projects that would happen anyway, while supporters argue it enables projects in challenging areas.

**How It Works:**
1. City designates TIF district
2. Baseline property tax revenue established
3. New development increases property values
4. Tax revenue growth (increment) dedicated to district improvements
5. After TIF period ends, all revenue goes to general fund

**Louisville Examples:**
- Downtown TIF district: Waterfront Park, Museum Plaza discussions
- NuLu area: Infrastructure supporting restaurant/gallery district
- Proposed for various projects throughout city

**Questions to Ask:**
- Would this project happen without TIF subsidy?
- What community benefits are guaranteed?
- When do full tax revenues return to general fund?
- Who oversees TIF spending?

**Why It Matters:** TIF diverts tax revenue from schools, libraries, and other services for 20-25 years. Understanding when TIF is appropriate versus when it subsidizes projects that don't need help is crucial for accountable economic development. Voters should know how much current services are reduced to fund TIF projects.

**Related Terms:** PILOT, Tax Abatement, Economic Development Incentives, Community Benefits Agreement, Clawback Provisions, Property Tax

---

## LOUISVILLE-SPECIFIC DATA TO INCLUDE

Integrate this data throughout relevant terms:

**Budget & Finance:**
- Total budget: $1.2 billion approved
- Occupational tax: 2.2% (1.45% city, 0.75% county)
- Property tax revenue: ~$200M+ annually
- No local sales tax option

**Economic Development:**
- PowerHouse: 400 MW, 25-year tax abatement
- Job creation claims often unverified
- Incentive tracking inadequate
- Few clawback provisions enforced

**Housing:**
- 30,000 unit affordable housing shortage
- 10,000-12,000 annual eviction filings
- 40%+ renters cost-burdened
- 75% of land zoned single-family only

**Public Safety:**
- DOJ consent decree (Breonna Taylor case)
- LMPD accountability concerns
- Crime concentrated in specific neighborhoods
- Community policing limited

**Environment:**
- Rubbertown pollution (west Louisville)
- 20-point tree canopy gap (east vs. west)
- Heat island effect in low-tree areas
- Air quality "moderate" most days

**Workforce:**
- 40-50% workers earn below living wage
- Living wage: $16-18/hour single, $30-35/hour with children
- Minimum wage: $7.25/hour (state)
- 150,000+ adults with criminal records limiting employment

---

## CROSS-REFERENCING STRATEGY

Link related terms to create knowledge web:

**Example Network:**
- **Living Wage** → links to: Wage Theft, Employee Misclassification, Benefits Cliff, Economic Development Incentives, Job Quality
- **Tax Abatement** → links to: TIF, PILOT, Economic Development Incentives, Clawback Provisions, Community Benefits Agreement
- **Community Policing** → links to: Mini Police Substation, Constitutional Policing, Procedural Justice, Community Trust, Civilian Oversight

**Implementation:**
- Limit to 5-7 related terms per definition
- Link only when genuinely helpful
- Create circular references (A links to B, B links to A)
- Use "See also:" at end of definitions

---

## CONTENT MANAGEMENT

**Update Schedule:**
- Review quarterly for accuracy
- Add new terms as issues emerge
- Update data when new reports published
- Refine based on user feedback
- Track which terms need expansion

**Community Input:**
- "Suggest a Term" form
- User feedback on clarity
- Teacher/educator reviews
- Community organization input
- Voter questions from events

**Quality Control:**
- Fact-check all Louisville data
- Verify sources
- Test readability (8th grade level target)
- Check for bias
- Ensure consistency

---

## PROMOTION STRATEGY

### Social Media Campaign
**"Term of the Week" Series:**
- Monday: Post term definition with graphic
- Wednesday: Louisville context and data
- Friday: "Why it matters" explanation
- Use #LouisvilleVoterEd #RunDaveRun

### Community Engagement
- Partner with libraries for glossary handouts
- Work with JCPS civics teachers
- Present at neighborhood association meetings
- Share with community organizations
- Offer "Civic Literacy 101" sessions

### Media Strategy
- Press release: "New Voter Education Resource"
- Op-ed on civic education importance
- Make available to journalists as reference
- Highlight during debates/forums
- Reference in policy announcements

### Voter Contact
- Include glossary links in campaign emails
- Reference during canvassing ("Learn more at...")
- Use in debate prep materials
- Provide to volunteers for training
- Include in endorsement packages

---

## DIFFERENTIATION VALUE

**What Makes This Unique:**

1. **Louisville-Specific Throughout:** Every term includes local data, not generic definitions
2. **Comprehensive Scope:** 400+ terms vs. typical campaign's 0-20
3. **Evidence-Based:** Cites actual data and research
4. **Non-Partisan Education:** Useful regardless of candidate preference
5. **Accountability Focus:** Highlights transparency and oversight gaps
6. **Equity Lens:** Centers disparities and justice
7. **Plain Language:** Accessible to all voters
8. **Interconnected:** Shows how issues relate
9. **Actionable:** Connects to specific solutions
10. **Living Resource:** Can grow over time

**Campaign Benefits:**
- Demonstrates deep policy knowledge
- Shows commitment to voter empowerment
- Provides media talking points
- Educates volunteers
- Differentiates from opponents
- Builds long-term community resource
- Supports "listening and responding" theme

---

## TECHNICAL SPECIFICATIONS

### File Format
- JSON for data storage
- Markdown for documentation
- HTML for web display
- CSV for bulk import

### WordPress Plugin Requirements
- PHP 7.4+
- WordPress 5.0+
- Fuse.js library (search)
- Mobile-responsive theme
- WCAG 2.1 AA compliant

### Performance Targets
- Page load: <3 seconds
- Search response: <500ms
- Mobile-optimized: 100% functional
- Accessibility: WCAG AA compliant
- SEO-optimized: meta tags, schema markup

---

## NEXT STEPS CHECKLIST

### Immediate (This Week)
- [ ] Review this implementation guide
- [ ] Decide: Quick Enhancement (Option 1) or Dedicated Section (Option 2)
- [ ] Backup current website
- [ ] Test in staging environment if available
- [ ] If Option 1: Update BUDGET_GLOSSARY.md with 50 priority terms
- [ ] If Option 2: Install WordPress glossary plugin

### Short-Term (Next 2 Weeks)
- [ ] Import all priority terms (50-100)
- [ ] Test search functionality
- [ ] Verify mobile responsiveness
- [ ] Run accessibility tests
- [ ] Set up analytics tracking
- [ ] Create social media graphics

### Medium-Term (Next Month)
- [ ] Complete all 400+ term imports
- [ ] Launch promotion campaign
- [ ] Partner with community organizations
- [ ] Gather user feedback
- [ ] Refine based on usage data
- [ ] Add terms based on campaign issues

### Ongoing
- [ ] Weekly "Term of the Week" social posts
- [ ] Monthly data updates
- [ ] Quarterly comprehensive review
- [ ] Continuous user feedback integration
- [ ] Expansion based on emerging issues

---

## SUPPORT RESOURCES

**Included in Project:**
- consolidated_voter_glossary_master.json (all terms data)
- glossary_implementation_checklist.md (detailed steps)
- glossary_project_comprehensive_summary.md (development history)
- glossary_sample_terms_by_category.md (examples from each category)

**WordPress Plugins:**
- Primary: Glossary by Codeat
- Alternative: CM Tooltip Glossary
- Alternative: Simple WordPress Glossary

**Search Library:**
- Fuse.js (fuzzy search)
- Documentation: fusejs.io

**Accessibility Testing:**
- WAVE: wave.webaim.org
- Lighthouse: Chrome DevTools
- Screen readers: NVDA (free), JAWS

---

## CONCLUSION

You now have one of the most comprehensive civic education resources ever developed for a municipal campaign. This voter education glossary:

✅ **Empowers voters** with knowledge to understand complex issues  
✅ **Demonstrates your competence** and serious policy preparation  
✅ **Differentiates your campaign** from typical political rhetoric  
✅ **Builds long-term value** beyond the election  
✅ **Supports your platform** of accountability and transparency  
✅ **Provides multiple uses** from education to media to training

**This is not just a website feature—it's a commitment to informed democracy.**

Implementation is straightforward (4-6 hours), and the resource will serve Louisville voters for years to come.

---

**Campaign:** Run Dave Run  
**Website:** rundaverun.org  
**Contact:** dave@rundaverun.org

*"A Mayor That Listens, A Government That Responds"*
