# Dave Biggers Mayoral Campaign Website
## Site Improvement Recommendations
**Review Date:** November 3, 2025
**Site URL:** http://rundaverun-local.local
**WordPress Version:** 6.8.3
**Theme:** Astra 4.11.13 with Astra Child 1.0.4

---

## Executive Summary

The Dave Biggers mayoral campaign website demonstrates strong content foundation with comprehensive policy documentation and clear messaging. However, there are critical technical SEO deficiencies, missing meta descriptions, and accessibility concerns that must be addressed before launch. The site has excellent structural elements (51+ policy documents, clean navigation, functional forms) but lacks essential SEO infrastructure and image optimization.

**Overall Score by Category:**
- Content Quality: 8/10
- Technical SEO: 3/10
- Accessibility: 5/10
- Performance: 6/10
- Conversion Optimization: 7/10

---

## CRITICAL ISSUES (Must Fix Before Launch)

### 1. Missing SEO Plugin & Meta Descriptions
**Location:** Site-wide
**Issue:** No SEO plugin installed (Yoast, Rank Math, etc.). Zero meta descriptions found across all pages.

**Impact:**
- Search engines will generate random snippets from page content
- Poor click-through rates from search results
- Missed opportunity to control first impression in SERPs
- No social media preview control (Open Graph tags missing)

**Recommended Fix:**
1. Install Yoast SEO or Rank Math plugin
2. Create unique meta descriptions for all pages (155-160 characters optimal)
3. Set custom SEO titles for key pages
4. Configure Open Graph tags for social sharing

**Suggested Meta Descriptions:**

**Homepage (ID: 105):**
```
Dave Biggers for Louisville Mayor 2026. Same $1.2B budget, better priorities: 46 mini substations, 24% employee raises, 18 wellness centers. A mayor that listens.
```

**About Dave (ID: 106):**
```
Learn about Dave Biggers' vision for Louisville. Independent candidate focused on public safety, government accountability, and community-driven solutions.
```

**Our Plan (ID: 107):**
```
Detailed policy plans for Louisville Metro: public safety, employee compensation, community wellness, and transparent budgeting. Evidence-based solutions.
```

**Get Involved (ID: 108):**
```
Join the grassroots movement. Volunteer, create DIY yard signs, and help elect Dave Biggers as Louisville's next mayor. Every voice matters.
```

**Contact (ID: 109):**
```
Contact Dave Biggers campaign. Email dave@rundaverun.org or info@rundaverun.org for questions, media inquiries, or volunteer coordination.
```

**Effort:** Quick (2-3 hours to write and implement all meta descriptions)

---

### 2. Missing Image Alt Text
**Location:** All uploaded images
**Issue:** Hero image (ID: 230) and other media assets lack alt text for accessibility and SEO.

**Impact:**
- Fails WCAG 2.1 accessibility standards
- Screen readers cannot describe images to visually impaired users
- Lost SEO value from image search
- Legal compliance risk under ADA

**Recommended Fix:**
Add descriptive alt text to all images:

**Hero Image (downtown2_hero_optimized.jpg):**
```alt
Louisville skyline featuring downtown buildings and the Ohio River at sunset
```

**Example alt text structure for campaign images:**
- Be descriptive and specific
- Include location/context where relevant
- Keep under 125 characters
- Don't start with "image of" or "picture of"

**Priority Images to Fix:**
1. Site logo (ID: 47) - "Dave Biggers for Louisville Mayor 2026 logo"
2. Hero image (ID: 230) - See above
3. Any images in policy documents
4. Social media sharing images

**Effort:** Quick (30 minutes for existing images)

---

### 3. Policy Pages Have No Content
**Location:** IDs 335, 338, 339, 331-334
**Issue:** Policy pages exist in database but show empty content (post_content = "-")

**Affected Pages:**
- Affordable Housing Expansion Plan (ID: 335)
- Mini Substations Implementation Plan (ID: 338)
- Community Wellness Centers Operations Guide (ID: 339)
- Environmental Justice Policy (ID: 331)
- Economic Development Accountability Framework (ID: 333)
- Data Center Accountability Framework (ID: 334)
- Government Transparency & Civic Engagement Initiative (ID: 332)

**Impact:**
- Users clicking policy links find empty pages
- Breaks trust and credibility
- Wastes valuable internal link equity
- Google may flag as thin/duplicate content

**Recommended Fix:**
**Option A - Import from source files:**
1. Locate markdown policy documents (should be in /home/dave/rundaverun-campaign-docs/)
2. Use Dave Biggers Policy Manager plugin import feature
3. Verify content displays correctly

**Option B - Manual content addition:**
1. Copy content from source markdown files
2. Paste into WordPress page editor
3. Format properly with headings, lists, links

**Note:** The plugin appears configured (dave-biggers-policy-manager v1.0.0) but policy_source_directory option is not set. This may prevent auto-import.

**Effort:** Moderate (2-4 hours depending on import method)

---

### 4. No Sitemap Configuration
**Location:** Site-wide
**Issue:** Without SEO plugin, no XML sitemap exists for search engines.

**Impact:**
- Search engines may miss pages during crawling
- Slower indexing of new content
- No priority signals to search engines
- Missed opportunity to exclude admin/utility pages

**Recommended Fix:**
1. Install Yoast SEO or Rank Math
2. Enable XML sitemap generation
3. Submit sitemap to Google Search Console
4. Submit to Bing Webmaster Tools
5. Exclude these page types from sitemap:
   - Volunteer Dashboard (ID: 934)
   - Volunteer Login (ID: 933)
   - Volunteer Registration (ID: 932)

**Effort:** Quick (15 minutes after SEO plugin installed)

---

### 5. Contact Form Missing on Contact Page
**Location:** Contact page (ID: 109)
**Issue:** Contact page content stored in external file reference: `$(cat /tmp/post109_fixed.html)`

**Impact:**
- Contact form may not render properly
- Users cannot submit inquiries
- Breaks primary conversion path
- Damages credibility

**Recommended Fix:**
1. Check actual page rendering in browser (may be displaying correctly despite database reference)
2. If broken, replace with Contact Form 7 shortcode: `[contact-form-7 id="927" title="Contact Form - Full"]`
3. Test form submission and email delivery
4. Verify Flamingo is storing submissions (currently 0 submissions)

**Effort:** Quick (30 minutes including testing)

---

## HIGH PRIORITY (Should Fix for Better UX)

### 6. Homepage Content Stored as File Reference
**Location:** Homepage (ID: 105)
**Issue:** Post_content field contains file reference instead of actual HTML: `$(cat /tmp/post105_email_real_fix.html)`

**Impact:**
- Potential rendering issues if file missing
- Difficult to edit content through WordPress admin
- Backup/migration complications
- Content not portable

**Recommended Fix:**
1. Load the referenced file content
2. Replace database entry with actual HTML
3. Test page rendering
4. Verify all shortcodes work: `[dbpm_signup_form]`, `[dbpm_volunteer_register]`

**Note:** This appears to be a development pattern. The post_content_filtered field contains full HTML, which suggests this may be working as designed. Verify in browser first.

**Effort:** Moderate (1-2 hours including testing)

---

### 7. Form Shortcodes May Not Be Rendering
**Location:** Homepage, Get Involved page
**Issue:** Content references placeholder shortcodes that may not be replaced with actual forms.

**Placeholders Found:**
- Email signup: `[dbpm_signup_form]`
- Volunteer registration: `[dbpm_volunteer_register]`

**Impact:**
- Users see placeholder text instead of functional forms
- Cannot capture email addresses
- Cannot recruit volunteers
- Primary conversion paths broken

**Recommended Fix:**
1. Verify custom plugin shortcodes are registered:
   - Check `/wp-content/plugins/dave-biggers-policy-manager/` for shortcode handlers
2. If missing, create shortcodes or replace with Contact Form 7:
   - Email signup: `[contact-form-7 id="926" title="Email Signup - Homepage"]`
   - Volunteer form: `[contact-form-7 id="928" title="Volunteer Signup Form"]`
3. Test form submissions
4. Configure email notifications to dave@rundaverun.org and info@rundaverun.org

**Effort:** Moderate (1-3 hours depending on plugin status)

---

### 8. No Header Hierarchy Review
**Location:** All pages
**Issue:** Cannot verify proper H1/H2/H3 usage without inspecting rendered HTML.

**Potential Impact:**
- Poor SEO if multiple H1 tags exist
- Confusing screen reader navigation
- Weak content structure signals to search engines

**Recommended Fix:**
1. Install SEO plugin with content analysis
2. Review each page for:
   - Only one H1 per page
   - Logical H2/H3 progression
   - No heading level skipping (H1 to H3)
3. Fix any issues found

**Key Pages to Check:**
- Homepage (ID: 105)
- About Dave (ID: 106)
- Our Plan (ID: 107)
- Voter Education (ID: 337)
- All policy pages

**Effort:** Moderate (2-3 hours for full site review)

---

### 9. Internal Linking Structure Incomplete
**Location:** Site-wide
**Issue:** Limited cross-linking between related content.

**Observations:**
- Voter Education page links to policy pages (good)
- Homepage has anchor links (#plan, #volunteer, #contact)
- Missing contextual links between related policies
- No blog posts to create topical authority

**Impact:**
- Weaker SEO authority distribution
- Users must use main navigation to discover related content
- Lower time-on-site metrics
- Reduced crawl depth

**Recommended Fix:**
1. Add "Related Policies" section to each policy page
2. Link budget pages to relevant policy implementations
3. Create breadcrumb navigation (SEO plugin can handle)
4. Add footer links to key pages:
   - Privacy Policy (already exists: ID 3)
   - Volunteer opportunities
   - Policy library
   - Newsletter signup

**Example Implementation:**
At bottom of "Mini Substations Implementation Plan":
```
Related Policies:
- [Community Wellness Centers Operations Guide](/community-wellness-centers-operations-guide/)
- [Public Safety Budget Details](/budget-detailed-line-items/)
- [Government Transparency Initiative](/government-transparency-civic-engagement-initiative/)
```

**Effort:** Moderate (3-4 hours for strategic link placement)

---

### 10. Mobile Menu Configuration Complex
**Location:** Theme functions.php
**Issue:** Multiple mobile menu overrides and forced settings indicate previous configuration issues.

**Code Concerns:**
```php
// Lines 52-73: Force disable mobile popup
// Lines 76-81: Backup filter to disable mobile popup
// Line 83: Comment about JavaScript causing mobile menu freeze
```

**Impact:**
- Potential mobile navigation issues
- Code complexity increases maintenance burden
- Multiple fallback mechanisms suggest unstable solution

**Recommended Fix:**
1. Test mobile menu on actual devices (iOS Safari, Android Chrome)
2. If working correctly, document why these overrides are needed
3. If issues exist, consider:
   - Updating Astra theme (currently 4.11.13)
   - Using different mobile menu approach
   - Consulting Astra support

**Testing Checklist:**
- [ ] Menu opens on mobile tap
- [ ] All menu items visible
- [ ] Submenus work correctly
- [ ] Menu closes properly
- [ ] No JavaScript errors in console

**Effort:** Moderate (2-3 hours testing + potential fixes)

---

## MEDIUM PRIORITY (Nice to Have)

### 11. Image Optimization Opportunities
**Location:** /wp-content/uploads/campaign-images/
**Issue:** Some images are large file sizes without optimization.

**File Sizes:**
- hurstbourne3.jpg: 340KB
- downtown2_hero.jpg: 335KB
- downtown2_hero_optimized.jpg: 289KB (better but still large)
- hurstbourne.jpg: 248KB
- hurstbourne1.jpg: 248KB

**Impact:**
- Slower page load times on mobile
- Higher bandwidth costs
- Lower PageSpeed scores
- Potential bounce rate increase

**Recommended Fix:**
1. Install Smush or ShortPixel image optimization plugin
2. Run bulk optimization on existing images
3. Set automatic optimization for future uploads
4. Target: <150KB per image, <50KB for thumbnails
5. Use WebP format with fallbacks

**Expected Results:**
- 40-60% file size reduction
- Faster page loads
- Better mobile experience
- Improved SEO rankings

**Effort:** Quick (30 minutes setup + 15 minutes bulk optimization)

---

### 12. No Schema Markup
**Location:** Site-wide
**Issue:** No structured data for enhanced search results.

**Missing Schema Types:**
- Organization (campaign details)
- Person (Dave Biggers profile)
- WebSite (search functionality)
- Article (policy documents)
- Event (campaign events if applicable)

**Impact:**
- No rich snippets in search results
- Missed knowledge panel opportunity
- Reduced search visibility
- No enhanced social sharing cards

**Recommended Fix:**
Install SEO plugin that includes Schema support:
1. Organization schema on homepage:
   - Name: Dave Biggers for Mayor 2026
   - Logo: [site logo URL]
   - Contact points: dave@rundaverun.org, info@rundaverun.org
   - Social profiles: [if applicable]

2. Person schema on About page:
   - Name: Dave Biggers
   - Description: Independent candidate for Louisville Mayor 2026
   - Job title: Mayoral Candidate

3. Article schema on policy pages:
   - Headline: [policy name]
   - Author: Dave Biggers Campaign
   - Date published: [publication date]

**Effort:** Moderate (1-2 hours for complete implementation)

---

### 13. Newsletter Signup Page Redundancy
**Location:** Newsletter Signup page (ID: 945)
**Issue:** Dedicated newsletter page when signup forms exist on homepage and Get Involved.

**Impact:**
- Potential user confusion
- Dilutes conversion focus
- Extra maintenance burden

**Recommended Fix:**
**Option A (Recommended):** Remove dedicated newsletter page
- Redirect /newsletter/ to Get Involved page
- Ensure newsletter signup is prominent on Get Involved

**Option B:** Keep but enhance
- Add value proposition: "Stay informed on campaign progress"
- Include recent newsletter samples
- Show subscriber count (social proof)
- Add email frequency promise

**Effort:** Quick (30 minutes for Option A, 1-2 hours for Option B)

---

### 14. Volunteer System Needs Testing
**Location:** Volunteer pages (IDs: 932, 933, 934)
**Issue:** Three volunteer pages but no clear user journey documentation.

**Pages:**
- Volunteer Registration (ID: 932)
- Volunteer Login (ID: 933)
- Volunteer Dashboard (ID: 934)

**Questions:**
- Do users register then receive login credentials?
- What content appears on Volunteer Dashboard?
- Is this system active and needed pre-launch?
- Should these pages be indexed by search engines?

**Recommended Fix:**
1. Document complete volunteer workflow
2. Test registration process end-to-end
3. Verify email notifications work
4. Add noindex to login/dashboard pages (keep private)
5. Consider if simpler form on Get Involved page is sufficient pre-launch

**Effort:** Moderate (2-3 hours for full testing and documentation)

---

### 15. Missing Privacy Policy Link in Forms
**Location:** Contact Form 7 forms (IDs: 927, 928)
**Issue:** Forms collect email addresses without privacy policy consent checkbox.

**Impact:**
- GDPR/privacy law compliance risk
- User trust concerns
- Potential legal issues

**Recommended Fix:**
Add to all forms collecting personal data:
```
[acceptance privacy-policy] I agree to the [privacy policy](/privacy-policy/) [/acceptance]
```

Update Privacy Policy page (ID: 3) to include:
- What data is collected
- How it's used
- Who has access
- Retention period
- User rights (access, deletion)

**Effort:** Moderate (1-2 hours including policy review)

---

### 16. Call-to-Action Button Consistency
**Location:** Throughout site
**Issue:** Multiple button styles and unclear hierarchy.

**Observations from Homepage:**
- "Read Our Plan" - Gold background, blue text
- "Join the Movement" - White background, blue text
- "Contact Dave" - Transparent with border
- Policy page links - Gold text, no background

**Impact:**
- Confusing visual hierarchy
- Unclear which actions are primary
- Reduced conversion rates

**Recommended Fix:**
Establish clear button hierarchy:

**Primary CTA (most important):**
- Background: Gold (#FFD700)
- Text: Dark blue (#003f87)
- Use for: Volunteer signup, Email signup

**Secondary CTA:**
- Background: Blue (#003f87)
- Text: White
- Use for: Read more, Learn more, View plans

**Tertiary CTA:**
- Outline only: Blue border
- Text: Blue
- Use for: Contact, Social sharing

Update CSS in child theme to standardize all buttons.

**Effort:** Moderate (2-3 hours including CSS updates and testing)

---

### 17. Social Sharing Capabilities Missing
**Location:** Site-wide
**Issue:** No social sharing buttons on policy pages or blog content.

**Impact:**
- Harder for supporters to spread message
- Missed viral potential
- Lower organic reach
- Reduced backlinks

**Recommended Fix:**
1. Install social sharing plugin (AddToAny, Social Warfare, or similar)
2. Add share buttons to:
   - Top of policy pages
   - Bottom of policy pages
   - Homepage (share campaign)
3. Configure Open Graph tags (requires SEO plugin):
   - og:title
   - og:description
   - og:image (use campaign logo or hero image)
   - og:type
4. Test sharing on Facebook, Twitter, LinkedIn

**Effort:** Quick (1 hour including testing)

---

### 18. Google Analytics & Tracking Setup
**Location:** Site-wide
**Issue:** No mention of analytics tracking setup.

**Impact:**
- Cannot measure traffic sources
- Cannot track conversion rates
- Cannot optimize based on user behavior
- No data for A/B testing

**Recommended Fix:**
1. Set up Google Analytics 4 (GA4) account
2. Install GA4 tracking code via:
   - Site Kit by Google plugin, OR
   - Manual header injection
3. Configure key events (goals):
   - Newsletter signup
   - Volunteer form submission
   - Contact form submission
   - Policy page views
   - Button clicks
4. Set up Google Search Console
5. Link GSC to GA4
6. Verify tracking in real-time reports

**Privacy Considerations:**
- Update Privacy Policy to mention analytics
- Consider cookie consent banner (CookieYes, Complianz)
- Anonymize IP addresses
- Respect Do Not Track settings

**Effort:** Moderate (2-3 hours for complete setup)

---

### 19. Page Load Speed Not Measured
**Location:** Site-wide
**Issue:** No performance testing conducted.

**Recommended Fix:**
Test all key pages with:
1. Google PageSpeed Insights
2. GTmetrix
3. WebPageTest

**Target Metrics:**
- First Contentful Paint: <1.8s
- Largest Contentful Paint: <2.5s
- Cumulative Layout Shift: <0.1
- Total Blocking Time: <200ms
- Speed Index: <3.4s

**Common Optimizations:**
- Enable caching plugin (WP Rocket, W3 Total Cache)
- Minify CSS/JS
- Defer non-critical JavaScript
- Lazy load images
- Optimize database
- Use CDN for static assets

**Effort:** Moderate (3-4 hours for testing and basic optimizations)

---

### 20. Accessibility Audit Needed
**Location:** Site-wide
**Issue:** WCAG 2.1 compliance not verified.

**Known Issues:**
- Missing alt text (see Critical #2)
- Need to verify:
  - Color contrast ratios
  - Keyboard navigation
  - Focus indicators
  - ARIA labels
  - Form labels
  - Heading structure
  - Link text descriptiveness

**Recommended Fix:**
1. Install WAVE browser extension
2. Run accessibility scan on key pages
3. Test with screen reader (NVDA or JAWS)
4. Test keyboard-only navigation
5. Fix all errors, address warnings

**Common Issues to Check:**
- Ensure all form fields have associated labels
- Links should describe destination ("Read housing policy" not "Click here")
- Sufficient color contrast (4.5:1 for normal text, 3:1 for large)
- Skip to content link for keyboard users
- No auto-playing media

**Effort:** Substantial (4-6 hours for full audit and fixes)

---

## LOW PRIORITY (Future Enhancements)

### 21. Blog/News Section for Content Marketing
**Location:** Not present
**Issue:** No blog posts exist (wp post list returned empty results).

**Opportunity:**
Create blog for:
- Campaign updates
- Event recaps
- Policy deep-dives
- Louisville news commentary
- Voter education articles
- Endorsement announcements

**Benefits:**
- Fresh content for SEO
- Increased keyword coverage
- Social media content
- Email newsletter content
- Community engagement

**Recommended Implementation:**
1. Create "News" or "Updates" section
2. Post 1-2 times per week
3. Focus on local issues
4. Keep posts 500-800 words
5. Include images and quotes
6. Share on social media

**Effort:** Ongoing (2-3 hours per post)

---

### 22. Email Newsletter Archive
**Location:** Not present
**Issue:** Past newsletters not accessible on website.

**Opportunity:**
- Demonstrate transparency
- Allow people to catch up on campaign
- Show consistent messaging
- SEO content boost

**Recommended Implementation:**
1. Create "Newsletter Archive" page
2. Post each newsletter after sending
3. Include:
   - Date sent
   - Subject line
   - Full content
   - Call-to-action to subscribe
4. Add navigation link to footer

**Effort:** Quick setup (1 hour), then 15 minutes per newsletter

---

### 23. Video Content Integration
**Location:** Not present
**Issue:** No video content detected (could enhance engagement).

**Opportunities:**
- Candidate introduction video on About page
- Policy explanation videos
- Community testimonials
- Event highlights
- Q&A sessions

**Benefits:**
- Increased time on page
- Better message delivery
- Emotional connection
- Social media content
- YouTube SEO opportunity

**Recommended Implementation:**
1. Create YouTube channel
2. Embed videos on relevant pages
3. Add video schema markup
4. Include captions for accessibility
5. Keep under 3 minutes for attention span

**Effort:** Substantial (depends on video production capabilities)

---

### 24. Multilingual Support
**Location:** Not present
**Issue:** Site only in English.

**Louisville Demographics:**
- Significant Spanish-speaking population
- Growing refugee communities
- Multiple language groups

**Opportunity:**
Translate key pages to Spanish:
- Homepage
- About Dave
- Our Plan summary
- Contact information
- Voter registration resources

**Recommended Implementation:**
1. Install TranslatePress or WPML
2. Prioritize Spanish translation
3. Hire professional translator (not Google Translate)
4. Add language switcher to header
5. Ensure proper hreflang tags

**Effort:** Substantial (6-10 hours + translation costs)

---

### 25. Interactive Budget Explorer
**Location:** Budget pages (IDs: 713, 714, 715, 735)
**Issue:** Budget data presented as static text.

**Opportunity:**
Create interactive visualization:
- Pie charts showing spending allocation
- Comparison sliders (current vs. proposed)
- Line-item drill-down
- "Build your budget" tool
- ROI calculators

**Benefits:**
- Increased engagement
- Better understanding of proposals
- Viral potential
- Press coverage opportunity
- Demonstrates transparency

**Recommended Tools:**
- Tableau Public (free)
- Google Data Studio
- Custom D3.js visualization
- Infogram

**Effort:** Substantial (10-20 hours depending on complexity)

---

### 26. Endorsement Showcase
**Location:** Not present
**Issue:** No endorsements displayed (if any exist).

**Opportunity:**
- Community leaders
- Organizations
- Former officials
- Union endorsements
- Newspaper editorials

**Recommended Implementation:**
1. Create "Endorsements" page
2. Include:
   - Organization/person name
   - Title/credentials
   - Quote or statement
   - Photo if available
   - Date of endorsement
3. Add testimonial slider to homepage
4. Update as new endorsements received

**Effort:** Moderate (2-3 hours setup, ongoing updates)

---

### 27. Volunteer Impact Dashboard
**Location:** Not present
**Issue:** No public metrics showing volunteer impact.

**Opportunity:**
Show campaign momentum:
- Number of volunteers
- Doors knocked
- Calls made
- Events hosted
- Counties covered

**Benefits:**
- Social proof
- Motivates volunteers
- Attracts new supporters
- Press coverage

**Recommended Implementation:**
1. Create live counter on Get Involved page
2. Update weekly
3. Include map of volunteer coverage
4. Show goal progress bars
5. Highlight top volunteers (with permission)

**Effort:** Moderate (3-4 hours initial setup + weekly updates)

---

### 28. FAQ Section
**Location:** Not present
**Issue:** Common questions must be answered repeatedly.

**Common Questions to Address:**
- How can I register to vote?
- When is the election?
- How do I request an absentee ballot?
- What are Dave's positions on [topic]?
- How can I volunteer?
- Can I donate to the campaign?
- How do I host an event?
- What districts does this cover?

**Benefits:**
- Reduces email inquiries
- SEO opportunity (question-based searches)
- Better user experience
- Shows thorough preparation

**Recommended Implementation:**
1. Create FAQ page
2. Organize by category
3. Use accordion/collapsible sections
4. Add FAQ schema markup
5. Link from footer and navigation

**Effort:** Moderate (3-4 hours for comprehensive FAQ)

---

### 29. Events Calendar
**Location:** Not present
**Issue:** No public calendar of campaign events.

**Opportunity:**
- Town halls
- Community meetings
- Canvassing events
- Phone banking
- Debates/forums
- Fundraisers

**Recommended Implementation:**
1. Install Events Calendar plugin
2. Add to main navigation
3. Include for each event:
   - Date/time
   - Location (with map)
   - Description
   - RSVP link
   - Contact for questions
4. Add schema markup (Event type)
5. Allow calendar export (iCal)

**Effort:** Moderate (2-3 hours setup + ongoing event management)

---

### 30. Mobile App Consideration
**Location:** Not present
**Issue:** All access through web browser.

**Future Opportunity:**
Progressive Web App (PWA) features:
- Offline access to policy docs
- Push notifications for events
- Add to home screen
- Faster loading
- Native app feel

**Benefits:**
- Enhanced mobile experience
- Volunteer coordination tool
- Event check-in
- Real-time updates

**Recommended Implementation:**
1. Install SuperPWA plugin
2. Configure manifest
3. Set up service worker
4. Test on iOS and Android
5. Promote installation

**Effort:** Moderate (4-6 hours for basic PWA setup)

---

## Technical Implementation Priority Matrix

### Week 1 (Before Launch)
**Must Complete:**
1. Install SEO plugin (Yoast or Rank Math)
2. Write and add meta descriptions to all pages
3. Add alt text to all images
4. Fix policy page content (import markdown files)
5. Set up XML sitemap
6. Verify contact form works
7. Test all form submissions
8. Verify privacy policy compliance

**Estimated Time:** 10-12 hours

---

### Week 2 (Launch Preparation)
**Should Complete:**
1. Fix homepage content storage
2. Verify all shortcodes render
3. Review header hierarchy site-wide
4. Add internal linking between policies
5. Test mobile menu thoroughly
6. Optimize images
7. Add schema markup
8. Set up Google Analytics
9. Run PageSpeed tests and fix critical issues

**Estimated Time:** 12-15 hours

---

### Week 3-4 (Post-Launch Refinement)
**Nice to Have:**
1. Standardize CTA buttons
2. Add social sharing buttons
3. Complete accessibility audit
4. Add privacy checkboxes to forms
5. Review newsletter page strategy
6. Test volunteer system end-to-end
7. Improve internal linking
8. Add FAQ section

**Estimated Time:** 10-12 hours

---

### Ongoing (Campaign Duration)
1. Blog posts 1-2x per week
2. Newsletter archive updates
3. Event calendar maintenance
4. Monitor analytics
5. Performance optimization
6. Content updates based on campaign progress

**Estimated Time:** 4-6 hours per week

---

## Measurement & Success Metrics

### SEO Metrics (Track Monthly)
- Organic search traffic
- Keyword rankings for:
  - "Dave Biggers"
  - "Louisville mayor"
  - "Louisville mayor 2026"
  - Policy-specific keywords
- Backlinks acquired
- Domain authority
- Pages indexed

**Tools:** Google Search Console, Google Analytics, Ahrefs/Moz

---

### User Engagement Metrics (Track Weekly)
- Page views
- Average time on page
- Bounce rate
- Pages per session
- Top landing pages
- Exit pages

**Tools:** Google Analytics

---

### Conversion Metrics (Track Daily)
- Email signups
- Volunteer registrations
- Contact form submissions
- Social shares
- Newsletter open rates
- Click-through rates on CTAs

**Tools:** Contact Form 7 + Flamingo, Email platform analytics, Google Analytics events

---

### Technical Performance Metrics (Track Monthly)
- PageSpeed Insights score (mobile & desktop)
- Core Web Vitals
- Largest Contentful Paint
- First Input Delay
- Cumulative Layout Shift
- Server response time

**Tools:** Google PageSpeed Insights, Google Search Console

---

### Accessibility Metrics (Quarterly Review)
- WAVE errors (target: 0)
- WAVE alerts (minimize)
- Keyboard navigation issues
- Screen reader compatibility
- Color contrast violations

**Tools:** WAVE, axe DevTools

---

## Budget Considerations

### Essential Costs (Critical Priority)
- **SEO Plugin:** FREE (Yoast/Rank Math free versions)
- **Image Optimization:** FREE (Smush free) or $49/year (ShortPixel)
- **Security Certificate:** Should be included with hosting
- **Google Analytics:** FREE
- **Google Search Console:** FREE

**Total Essential:** $0-49/year

---

### Recommended Investments (High Priority)
- **Premium SEO Plugin:** $99-199/year (better features)
- **Caching Plugin:** FREE (W3 Total Cache) or $49/year (WP Rocket)
- **Backup Plugin:** $50-100/year (UpdraftPlus Premium)
- **Social Sharing Plugin:** FREE or $29/year
- **Professional Translation:** $0.10-0.20 per word for Spanish

**Total Recommended:** $150-400/year

---

### Optional Enhancements (Medium-Low Priority)
- **Video Hosting:** FREE (YouTube) or $20/month (Vimeo Plus)
- **Email Marketing Platform:** FREE (MailChimp <2,000 contacts) or $20-50/month
- **Event Calendar Pro:** $89/year
- **Advanced Analytics:** FREE (GA4) or $150/month (Hotjar)
- **A/B Testing Tool:** FREE (Google Optimize) or $49/month

**Total Optional:** $100-500/year

---

## Content Quality Assessment

### Strengths
1. **Comprehensive Policy Documentation** - 51+ detailed documents demonstrate serious preparation
2. **Clear Messaging** - "A Mayor That Listens, A Government That Responds" is memorable
3. **Specific Numbers** - "$1.2 billion budget, 46 substations, 24% raises" builds credibility
4. **Grassroots Authenticity** - DIY yard sign approach aligns with "Not Me, We" message
5. **Evidence-Based Claims** - References to cities where policies worked
6. **Transparency Focus** - Budget breakdowns show commitment to accountability
7. **Consistent Voice** - Professional yet accessible tone throughout
8. **Strong CTAs** - Multiple clear paths to engagement
9. **Louisville-Specific** - ZIP code data, local references, Metro-specific plans
10. **Voter Education Focus** - 351-term glossary shows commitment to informed electorate

### Areas for Content Improvement

**1. Homepage Hero Section**
- Current: Strong value proposition
- Enhancement: Add specific accomplishment or credential above fold
- Example: "Former [role] with [X years] serving Louisville"

**2. Policy Page Navigation**
- Current: Links scattered across pages
- Enhancement: Create central policy hub page with filtering
- Categories: Public Safety, Health, Housing, Economic Development, Environment

**3. Storytelling**
- Current: Fact-heavy, policy-focused
- Enhancement: Add personal stories showing policy impact
- Example: "Meet Maria, whose family will benefit from community wellness centers"

**4. Visual Content**
- Current: Limited to stock Louisville images
- Enhancement:
  - Candidate photos at community events
  - Infographics explaining complex policies
  - Video introductions
  - Charts/graphs for budget data

**5. Social Proof**
- Current: Minimal testimonials
- Enhancement:
  - Community member quotes
  - Endorsements (if any)
  - Volunteer testimonials
  - Social media embeds showing support

**6. About Page**
- Current: Good overview of campaign approach
- Enhancement:
  - More personal biography
  - What led to running for mayor
  - Specific Louisville connections
  - Photos from 2018 campaign

**7. "Our Plan" Page**
- Current: Links to other pages
- Enhancement:
  - Executive summary of complete platform
  - One-page overview printable PDF
  - Comparison table vs. current administration
  - Timeline for implementation

**8. Counter-Arguments**
- Current: Presents policies without addressing objections
- Enhancement:
  - FAQ addressing common concerns
  - "But how will we pay for it?" section
  - Evidence from similar cities
  - Risk mitigation strategies

**9. Local Context**
- Current: Good Louisville-specific data
- Enhancement:
  - References to specific neighborhoods
  - Local news coverage links
  - Recognition of current administration's work
  - Specific Louisville challenges addressed

**10. Call-to-Action Urgency**
- Current: Generic "Join us" messaging
- Enhancement:
  - Countdown to election
  - "X volunteers needed by [date]"
  - Milestone progress bars
  - Specific asks ("Help us reach 10,000 doors this week")

---

## Accessibility Deep Dive

### Keyboard Navigation Requirements
**Test all pages for:**
- Tab order logical and sequential
- All interactive elements reachable via keyboard
- Focus indicators clearly visible
- No keyboard traps
- Skip navigation link present

**Known Issues to Fix:**
- Ensure dropdown menus work with keyboard
- Test form completion without mouse
- Verify modal dialogs can be closed with Escape key

---

### Screen Reader Compatibility
**Required ARIA Labels:**
- Main navigation: `<nav aria-label="Main navigation">`
- Search form: `<form role="search">`
- Buttons: Clear text or aria-label
- Form inputs: Associated label tags
- Images: Alt text (already flagged as Critical #2)

**Semantic HTML:**
- Use `<main>` for primary content
- Use `<article>` for policy documents
- Use `<aside>` for sidebar content
- Use proper heading hierarchy

---

### Color Contrast Issues to Check
**WCAG 2.1 Requirements:**
- Normal text: 4.5:1 contrast ratio
- Large text (18pt+): 3:1 contrast ratio
- Interactive elements: 3:1 against background

**High Risk Areas:**
- Blue (#003D7A) on white - GOOD
- Gold (#FFC72C) on blue - CHECK THIS
- White text on images - CHECK WITH OVERLAY
- Link colors - ensure distinguishable

**Tool:** WebAIM Contrast Checker

---

### Form Accessibility
**Required Elements:**
```html
<label for="email">Email Address</label>
<input type="email" id="email" name="email" required aria-required="true">

<span id="email-error" role="alert" aria-live="polite"></span>
```

**Checklist:**
- [ ] All inputs have associated labels
- [ ] Required fields marked with aria-required
- [ ] Error messages associated with fields
- [ ] Success messages announced to screen readers
- [ ] Submit buttons clearly labeled
- [ ] Fieldsets used for grouped inputs

---

### Mobile Accessibility
**Touch Target Size:**
- Minimum 44x44 pixels for all interactive elements
- Adequate spacing between links/buttons
- No hover-only functionality

**Zoom & Text Sizing:**
- Site usable at 200% zoom
- No horizontal scrolling at mobile sizes
- Text remains readable when enlarged
- No fixed pixel font sizes

---

## Security Recommendations

### Essential Security Measures

**1. SSL Certificate**
- Ensure HTTPS enforced site-wide
- No mixed content warnings
- Update WordPress site URL to https://

**2. Plugin Security**
- Keep all plugins updated
- Remove unused plugins
- Use only reputable plugin developers
- Check plugin last update date (<6 months preferred)

**3. WordPress Core**
- Currently on 6.8.3 - GOOD
- Enable automatic security updates
- Regular backup schedule

**4. User Accounts**
- Strong passwords required
- Limit admin accounts
- Two-factor authentication (Wordfence, iThemes)
- No "admin" username

**5. Form Spam Protection**
- Enable Contact Form 7 spam filtering
- Consider reCAPTCHA for high-traffic forms
- Enable Akismet if adding blog comments
- Monitor Flamingo submissions for spam

**6. File Upload Security**
- Limit allowed file types
- Scan uploads for malware
- Restrict execution permissions

**7. Database Security**
- Change default table prefix (wp_7e1ce15f22_ is GOOD)
- Regular database optimization
- Secure database credentials

**8. Backup Strategy**
- Daily database backups
- Weekly full site backups
- Offsite storage (not just server)
- Test restore process

**Recommended Plugins:**
- **Security:** Wordfence or Sucuri
- **Backups:** UpdraftPlus or BackupBuddy
- **2FA:** Wordfence Login Security
- **Malware Scan:** Sucuri or iThemes Security

---

## Performance Optimization Checklist

### Immediate Wins (Quick Fixes)

**Caching:**
- [ ] Install caching plugin (WP Super Cache or W3 Total Cache)
- [ ] Enable browser caching
- [ ] Enable gzip compression
- [ ] Set appropriate cache expiration headers

**Database:**
- [ ] Remove post revisions (limit to 3)
- [ ] Clean up auto-drafts
- [ ] Optimize database tables
- [ ] Remove spam comments
- [ ] Delete unused plugins

**Images:**
- [ ] Optimize all images (see Medium Priority #11)
- [ ] Enable lazy loading
- [ ] Use appropriate image dimensions
- [ ] Serve images in next-gen formats (WebP)

**CSS/JavaScript:**
- [ ] Minify CSS files
- [ ] Minify JavaScript
- [ ] Combine CSS files where possible
- [ ] Defer non-critical JavaScript
- [ ] Remove unused CSS

**Hosting:**
- [ ] Verify adequate hosting resources
- [ ] Check server response time (<200ms goal)
- [ ] Consider CDN (Cloudflare free tier)
- [ ] Enable HTTP/2

---

### Advanced Optimization (If Needed)

**Code Splitting:**
- Load policy documents on-demand
- Async load non-critical components
- Conditional loading based on page type

**Resource Hints:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="dns-prefetch" href="//maps.google.com">
```

**Critical CSS:**
- Inline above-fold CSS
- Defer below-fold styles
- Remove unused theme CSS

**Font Optimization:**
- Use system fonts where appropriate
- Limit custom font variations
- Use font-display: swap
- Subset fonts to needed characters

---

## Local SEO Opportunities

### Google Business Profile
**Action Items:**
1. Create Google Business Profile for campaign
2. Category: "Political Organization"
3. Add:
   - Campaign address (PO Box 33036, Louisville, KY 40232)
   - Phone number (if available)
   - Website URL
   - Hours (if applicable)
   - Description (155 characters)
   - Photos

**Benefits:**
- Appears in local search
- Shows on Google Maps
- Review capability
- Q&A section
- Posts for updates

---

### Local Citations
**Directory Listings:**
- Louisville Chamber of Commerce
- Louisville Tourism
- Local news sites
- Community calendars
- Nonprofit directories
- Political directories

**NAP Consistency (Name, Address, Phone):**
Ensure identical across:
- Website footer
- Google Business Profile
- Social media profiles
- Press releases
- Email signatures

---

### Louisville-Specific Keywords
**Target Terms:**
- "Louisville mayor election 2026"
- "Louisville Metro government"
- "Louisville mayoral candidate"
- "Louisville city budget"
- "Louisville public safety"
- "Louisville affordable housing"
- "Vote Louisville 2026"

**Long-Tail Opportunities:**
- "How to register to vote in Louisville"
- "Louisville Metro employee salary"
- "Louisville mini police substations"
- "Louisville community wellness centers"
- "Louisville participatory budgeting"

**Local News Monitoring:**
- Courier Journal Louisville news
- WFPL local coverage
- LEO Weekly articles
- Business First Louisville
- Wave3 local news

---

### Community Engagement for Links
**Outreach Targets:**
- Louisville bloggers
- Community organizations
- Neighborhood associations
- Local business owners
- University groups (UofL, Bellarmine)
- Issue-focused nonprofits

**Content Ideas for Link Building:**
- Guest posts on local blogs
- Expert quotes for journalists
- Community event sponsorships
- Policy guides for organizations
- Voter registration resources

---

## Mobile-First Considerations

### Mobile User Experience

**Current Strengths:**
- Astra theme is mobile-responsive
- Mobile menu configured (despite complexity)
- Touch-friendly navigation

**Areas to Verify:**
1. **Typography:**
   - Text readable without zooming
   - Line length appropriate (45-75 characters)
   - Sufficient line spacing (1.5x)

2. **Forms:**
   - Input fields large enough to tap
   - Appropriate input types (email, tel, number)
   - Autocomplete enabled
   - Minimal typing required

3. **Navigation:**
   - Hamburger menu functional
   - All pages accessible
   - Back button works correctly
   - No hover-dependent features

4. **Content:**
   - Images scale properly
   - Tables scrollable or responsive
   - Videos embedded responsively
   - Downloads clear and accessible

5. **Performance:**
   - Fast load on 3G connection
   - Progressive enhancement
   - Offline capability (future PWA)

**Testing Devices:**
- iPhone (Safari)
- Android phone (Chrome)
- iPad (Safari)
- Android tablet

---

### Mobile Conversion Optimization

**Thumb-Friendly Design:**
- CTA buttons bottom of screen
- Important actions within reach
- Avoid top navigation dependencies

**Reduced Friction:**
- Minimal form fields
- Social login options (future)
- Autofill enabled
- Clear error messages

**Speed Focus:**
- Compress images aggressively for mobile
- Reduce JavaScript execution
- Lazy load below-fold content
- Show content immediately (no spinners)

---

## Content Maintenance Plan

### Weekly Tasks
- [ ] Monitor form submissions
- [ ] Respond to contact inquiries
- [ ] Check for broken links
- [ ] Review analytics for issues
- [ ] Update event calendar
- [ ] Post social media content

**Time Required:** 2-3 hours/week

---

### Monthly Tasks
- [ ] Review SEO rankings
- [ ] Update policy documents if needed
- [ ] Check for WordPress/plugin updates
- [ ] Run security scan
- [ ] Review accessibility reports
- [ ] Analyze conversion rates
- [ ] Update volunteer metrics
- [ ] Backup entire site

**Time Required:** 4-5 hours/month

---

### Quarterly Tasks
- [ ] Comprehensive SEO audit
- [ ] Full accessibility review
- [ ] Performance optimization check
- [ ] Content freshness update
- [ ] Competitor analysis
- [ ] User feedback survey
- [ ] Link building campaign
- [ ] Email list cleaning

**Time Required:** 8-10 hours/quarter

---

## Competitor Analysis Framework

### What to Monitor
**Opponent Websites:**
- Messaging strategy
- Policy depth
- Design quality
- SEO performance
- Social media integration
- Email capture tactics
- Mobile experience

**Metrics to Track:**
- Domain authority (Moz)
- Keyword rankings (overlap)
- Backlink profile
- Social media followers
- Estimated traffic

**Tools:**
- SimilarWeb (free tier)
- Ahrefs (paid)
- SEMrush (paid)
- Manual review

**Competitive Advantages:**
- Policy detail depth
- Budget transparency
- Grassroots authenticity
- Voter education focus
- Technical implementation

---

## Crisis Communication Preparedness

### Website Contingencies

**Scenario 1: Site Goes Down**
- Have static HTML backup ready
- Keep social media updated
- Redirect domain if needed
- Contact info alternative (Google Doc)

**Scenario 2: Hack/Defacement**
- Restore from backup immediately
- Change all passwords
- Security audit
- Public statement if needed

**Scenario 3: Misinformation**
- Fact-check page ready
- Rapid response capability
- Archive of all statements
- Press contact ready

**Scenario 4: Traffic Surge**
- CDN ready (Cloudflare)
- Hosting upgrade plan
- Cached version available
- Key content in multiple formats

**Scenario 5: Content Dispute**
- Documentation of all sources
- Retraction/correction process
- Legal review contact
- Transparency in updates

---

## Final Pre-Launch Checklist

### Content Review
- [ ] All pages have content (no empty pages)
- [ ] All links work (no 404s)
- [ ] All images display correctly
- [ ] All forms submit successfully
- [ ] Email notifications working
- [ ] Contact information current
- [ ] Dates accurate
- [ ] Spelling/grammar checked
- [ ] Consistent messaging
- [ ] Clear calls-to-action

### Technical Review
- [ ] SSL certificate active (HTTPS)
- [ ] SEO plugin configured
- [ ] Meta descriptions on all pages
- [ ] Alt text on all images
- [ ] XML sitemap generated
- [ ] Google Analytics tracking
- [ ] Google Search Console connected
- [ ] Favicon appears correctly
- [ ] Social media tags working
- [ ] Schema markup implemented

### Legal/Compliance Review
- [ ] Privacy policy current
- [ ] Terms of service (if applicable)
- [ ] Cookie policy (if applicable)
- [ ] GDPR compliance (privacy checkboxes)
- [ ] ADA accessibility addressed
- [ ] Campaign finance compliance
- [ ] Disclaimer statements present
- [ ] Copyright notices

### Performance Review
- [ ] PageSpeed score >80
- [ ] Mobile-friendly test passes
- [ ] Core Web Vitals good
- [ ] Images optimized
- [ ] Caching enabled
- [ ] Database optimized
- [ ] No JavaScript errors
- [ ] Cross-browser tested

### Security Review
- [ ] Security plugin active
- [ ] Backup system running
- [ ] Strong passwords set
- [ ] Admin accounts limited
- [ ] File permissions correct
- [ ] Database prefix changed
- [ ] Remove default content
- [ ] Disable file editing

### Browser/Device Testing
- [ ] Chrome desktop
- [ ] Firefox desktop
- [ ] Safari desktop
- [ ] Edge desktop
- [ ] Chrome mobile
- [ ] Safari iOS
- [ ] Android browser
- [ ] Tablet (iPad/Android)

---

## Resource Links

### SEO Tools
- Google Search Console: https://search.google.com/search-console
- Google Analytics: https://analytics.google.com
- Google PageSpeed Insights: https://pagespeed.web.dev
- Bing Webmaster Tools: https://www.bing.com/webmasters
- Yoast SEO Plugin: https://yoast.com/wordpress/plugins/seo/
- Rank Math Plugin: https://rankmath.com

### Accessibility Tools
- WAVE Browser Extension: https://wave.webaim.org/extension/
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- axe DevTools: https://www.deque.com/axe/devtools/
- NVDA Screen Reader: https://www.nvaccess.org/download/

### Performance Tools
- GTmetrix: https://gtmetrix.com
- WebPageTest: https://www.webpagetest.org
- Pingdom: https://tools.pingdom.com
- Google Lighthouse: Built into Chrome DevTools

### Image Optimization
- TinyPNG: https://tinypng.com
- Squoosh: https://squoosh.app
- ImageOptim: https://imageoptim.com

### Learning Resources
- WordPress Codex: https://codex.wordpress.org
- Moz SEO Guide: https://moz.com/beginners-guide-to-seo
- Google SEO Starter Guide: https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/

---

## Conclusion

The Dave Biggers mayoral campaign website has a strong foundation with comprehensive policy content, clear messaging, and solid technical infrastructure. However, critical SEO and accessibility gaps must be addressed before launch to ensure the site performs effectively.

**Key Priorities:**
1. Implement SEO basics (meta descriptions, alt text, sitemap)
2. Fix empty policy pages
3. Verify all forms work correctly
4. Ensure mobile experience is seamless
5. Test, test, test before going live

**Strengths to Maintain:**
- Detailed, transparent policy documentation
- Authentic grassroots messaging
- Strong Louisville-specific focus
- Clear calls-to-action
- Voter education commitment

**Competitive Advantages:**
- Most detailed policy platform in race (likely)
- Budget transparency leadership
- Evidence-based approach
- Community-first messaging

With 10-15 hours of focused work on critical issues and another 20-25 hours on high-priority improvements, this site will be a powerful campaign tool that demonstrates both policy substance and technical competence.

The contrast between comprehensive policy detail and grassroots authenticity ("DIY yard signs") is compelling and differentiates this campaign. Ensure the website execution matches the message quality.

---

**Report Prepared By:** Claude (Anthropic AI)
**Review Date:** November 3, 2025
**Next Review Recommended:** Post-launch (2 weeks after going live)
**Questions/Follow-up:** Reference specific issue numbers from this report
