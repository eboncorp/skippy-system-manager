# Dave Biggers Policy Manager - Untapped Features Audit
**Date:** November 2, 2025
**Status:** 80% of features NOT being used!

---

## WHAT WE'RE USING NOW (20%)

✅ **Custom Post Type** - Policy documents
✅ **Taxonomies** - Categories and tags for policies
✅ **Volunteer Portal** - Registration, login, dashboard (just activated today)

---

## WHAT WE'RE NOT USING (80%)

### FEATURE 1: EMAIL SIGNUP SYSTEM (Built-in Alternative to CF7) ❌

**What It Does:**
- Standalone email collection with double opt-in verification
- Separate database table (not Contact Form 7)
- Tracks volunteer interest checkbox
- Tracks ZIP codes
- Email verification workflow
- CSV export for email campaigns
- GDPR-compliant unsubscribe

**Shortcode:**
```
[dbpm_signup_form]
[dbpm_signup_form show_volunteer="yes" show_zip="yes"]
[dbpm_signup_form show_volunteer="no" show_zip="no"]
```

**Admin Interface:**
- WordPress Admin → Policy Documents → Subscribers
- View all signups
- See verification status
- Track volunteer interest
- Export to CSV

**Current Status:**
- ✅ Active and functional
- ✅ Database table exists
- ✅ Has 1 subscriber (you - davidbiggers@yahoo.com)
- ❌ Not used on any page
- ❌ Using Contact Form 7 instead

**Why You Might Want This:**
- **Email verification** - Confirms email addresses are real
- **Better for email campaigns** - Export verified emails only
- **Volunteer segmentation** - Filter by volunteer interest
- **ZIP code tracking** - Target by location
- **GDPR compliant** - Built-in unsubscribe
- **No spam** - Double opt-in prevents fake signups

**Where to Use:**
- Replace or supplement CF7 email signup on homepage
- Standalone newsletter signup page
- Footer widget for email collection

---

### FEATURE 2: PDF GENERATION SYSTEM ❌

**What It Does:**
- Converts ANY policy document to downloadable PDF
- Professional Louisville Metro branding
- Custom headers and footers
- Tracks download counts per document
- Respects access permissions (public/volunteer/private)
- Auto-generates on first download, caches for speed

**PDF Features:**
- Header: "Dave Biggers for Mayor | [Document Title]"
- Footer: "rundaverun.org | Page X of Y"
- Louisville Metro blue/gold styling
- Professional typography
- Automatic page breaks

**Security:**
- Nonce verification
- Access level checks
- Download counting

**Current Status:**
- ✅ Code exists and functional
- ❌ mPDF library NOT installed (needs composer)
- ❌ Falls back to plain text if no library
- ❌ No PDF download links on site
- ❌ Download counts not tracking

**Why You Want This:**
- **Professional sharing** - Send PDFs to media, supporters
- **Print-friendly** - People can print your policies
- **Branding** - Every PDF has your campaign branding
- **Offline access** - People can save and read offline
- **Email campaigns** - Attach PDFs to emails
- **Track popularity** - See which policies people download most

**How to Activate:**
1. Install mPDF library (5 minutes)
2. Add "Download PDF" button to each policy document
3. Track which policies are most downloaded

**Example Use:**
- Policy Library page: Each policy has "Download PDF" button
- Our Plan page: "Download Complete Plan as PDF"
- Email campaigns: Attach PDF of budget plan
- Press kit: PDFs of all policies

---

### FEATURE 3: MARKDOWN DOCUMENT IMPORTER ❌

**What It Does:**
- Bulk import markdown (.md) files from directory
- Auto-categorizes by filename patterns
- Converts markdown to WordPress posts
- Sets access levels automatically
- Preserves formatting
- Draft status by default (safe import)

**Admin Interface:**
- WordPress Admin → Policy Documents → Import Documents
- One-click bulk import
- Shows progress and results
- Can delete all and re-import

**Auto-Categorization:**
Recognizes filenames like:
- `BUDGET_*.md` → Budget & Finance category
- `VOLUNTEER_*.md` → Volunteer Resources (volunteer-only access)
- `CAMPAIGN_*.md` → Campaign Materials
- `IMPLEMENTATION_*.md` → Implementation Guides

**Current Status:**
- ✅ Importer functional
- ❌ No markdown files to import
- ❌ Import page exists but unused

**Why You Might Want This:**
- **Bulk updates** - Update all policies at once
- **Version control** - Keep policies in markdown files
- **Collaboration** - Team can edit markdown files
- **Backup** - Markdown files are plain text backups
- **Portability** - Move policies between sites easily

**Use Cases:**
- If you write policies in markdown format
- If you have existing .md policy files
- If you want to update all policies at once
- If team members work in markdown editors

---

### FEATURE 4: ADVANCED SEARCH SYSTEM ❌

**What It Does:**
- Full-text search across all policy documents
- Category filtering
- Access-level aware (hides restricted docs from non-logged-in users)
- Fast AJAX search (no page reload)
- Search title, content, excerpts

**Current Status:**
- ✅ Search code active
- ✅ Integrated with WordPress search
- ❌ No custom search interface built
- ❌ Using default WordPress search only

**Why You Want This:**
- **Better user experience** - Find policies fast
- **Smart filtering** - Search within categories
- **Security** - Automatically hides volunteer-only docs
- **Fast results** - AJAX instant search

**How to Activate:**
Create custom search page or widget with:
- Search input field
- Category filter dropdown
- AJAX results display
- "No results" messaging

**Potential Locations:**
- Policy Library page header
- Site-wide header search
- Homepage "Find a Policy" section
- Widget in sidebar

---

### FEATURE 5: RESTRICTED CONTENT SYSTEM ❌

**What It Does:**
- Mark any policy document as "Volunteer Only"
- Non-logged-in users see login/register prompt instead
- Logged-in volunteers see full content
- Three access levels: Public, Volunteer Only, Private (admin only)

**Meta Box in Editor:**
When editing any policy document:
- Radio buttons: Public / Volunteer Only / Private
- Saves as post meta
- Automatically enforced on frontend

**Current Status:**
- ✅ Code active and functional
- ✅ Access level meta box in editor
- ❌ No documents marked as "Volunteer Only"
- ❌ All policies are public
- ❌ Not utilizing volunteer-exclusive content

**Why You Want This:**
- **Exclusive content** - Reward committed volunteers
- **Internal resources** - Training materials, scripts
- **Sensitive info** - Schedules, contact lists
- **Tiered access** - Public vs. insider content

**What to Make Volunteer-Only:**
1. **Training Materials:**
   - Phone banking scripts
   - Canvassing talking points
   - Door-to-door guides
   - How to handle objections

2. **Internal Schedules:**
   - Event calendars
   - Volunteer shifts
   - Team meeting times

3. **Strategy Documents:**
   - Neighborhood targeting plans
   - Volunteer coordinator contacts
   - Internal messaging guidelines

4. **Resources:**
   - Volunteer handbook
   - Social media templates
   - Email templates for volunteers

**How to Use:**
1. Create/edit any policy document
2. Set "Access Level" to "Volunteer Only"
3. Publish
4. Non-volunteers see: "This content is for registered volunteers only. [Register] or [Login]"
5. Volunteers see: Full content

---

### FEATURE 6: DOWNLOAD TRACKING & ANALYTICS ❌

**What It Does:**
- Counts downloads for each policy document
- Stores count in post meta: `_policy_download_count`
- Increments each time PDF is downloaded
- Can sort policies by popularity

**Current Status:**
- ✅ Code exists
- ❌ Not tracking (no PDFs being downloaded)
- ❌ No analytics dashboard

**Why You Want This:**
- **Measure interest** - Which policies people care about
- **Content strategy** - Create more of what's popular
- **Campaign insights** - What issues resonate
- **Media tracking** - See when press downloads materials

**Potential Dashboard:**
- Most downloaded policies
- Downloads per week/month
- Policy popularity rankings
- Download trends over time

---

### FEATURE 7: EMAIL NOTIFICATIONS & AUTOMATION ❌

**What It's Doing (Already Active):**

**Volunteer Registration:**
1. User fills out `[dbpm_volunteer_register]` form
2. **Admin email sent** to you (eboncorp@gmail.com)
3. **Welcome email sent** to volunteer with temp password
4. Account created with "pending_volunteer" role
5. You approve in admin
6. **Approval email sent** to volunteer with login link

**Email Signup (if using built-in system):**
1. User fills out `[dbpm_signup_form]`
2. **Verification email sent** to user
3. User clicks verification link
4. Email marked as verified
5. (Optional) Welcome email after verification

**Current Status:**
- ✅ Volunteer notification emails active
- ❌ Not using email signup system (using CF7 instead)
- ⚠️ Emails might not send on local (need SMTP)

**Why You Want This:**
- **Automated onboarding** - Volunteers get instant response
- **No manual work** - System handles email/password
- **Professional** - Immediate confirmation
- **Engagement** - People know you received their signup

**To Test:**
- Create test volunteer account
- Check email for notifications
- May need SMTP plugin on local (MailHog or WP Mail SMTP)
- Will work on live site with GoDaddy SMTP

---

### FEATURE 8: CUSTOM FIELDS & META BOXES ❌

**What's Available:**
When editing policy documents, meta boxes for:
- Access Level (Public/Volunteer/Private)
- Download Count (auto-tracked)
- Featured Policy (checkbox)
- Related Policies (link other policies)

**Current Status:**
- ✅ Meta boxes exist
- ❌ Not using custom fields
- ❌ No featured policies set
- ❌ No related policies linked

**Why You Want This:**
- **Featured Policy** - Highlight "must-read" policies
- **Related Policies** - Link budget to public safety plan
- **Better navigation** - "If you liked this, read..."
- **Content organization** - Create policy "pathways"

**How to Use:**
1. Edit any policy document
2. Check "Featured Policy" box
3. Display featured policies on homepage
4. Link related policies at bottom of each document

---

### FEATURE 9: ADMIN DASHBOARD & STATISTICS ❌

**What Exists:**
- WordPress Admin → Policy Documents → Settings
- Plugin statistics page
- Shortcode reference
- Campaign information display

**What It Could Show:**
- Total policy documents
- Total email subscribers
- Total volunteers (pending + approved)
- Most downloaded policies
- Recent activity

**Current Status:**
- ✅ Settings page exists
- ❌ Haven't explored what's inside
- ❌ Not using for analytics

**Why You Want This:**
- **Campaign dashboard** - One-stop overview
- **Quick stats** - How many volunteers, subscribers
- **Performance** - Which policies are popular
- **Growth tracking** - Watch numbers grow

---

### FEATURE 10: CATEGORY & TAG SYSTEM ❌

**What's Built In:**

**Categories Available:**
- Campaign Materials
- Budget & Finance
- Implementation Guides
- Volunteer Resources
- Public Safety
- Community Wellness
- Community Engagement

**Tags Available:**
- Budget, Public Safety, Wellness
- Substations, Community
- And more...

**Current Status:**
- ✅ Categories exist
- ✅ 42 policies exist
- ❌ Most using default categories only
- ❌ Not fully categorized
- ❌ Not using tags effectively
- ❌ No category-based navigation

**Why You Want This:**
- **Browse by topic** - Users find related policies
- **Filter on Policy Library** - "Show me all Budget policies"
- **SEO** - Better search engine organization
- **Cross-linking** - Related policy suggestions

**How to Use Better:**
1. Review all 42 policies
2. Assign appropriate categories
3. Add relevant tags
4. Create category archive pages
5. Add category filter to Policy Library

---

## PRIORITY RANKING: WHAT TO ACTIVATE NEXT

### 🔥 HIGH PRIORITY (Do Soon)

**1. PDF Generation System**
- **Effort:** 5 minutes (install mPDF)
- **Impact:** HIGH - Professional document sharing
- **Use:** Media kit, email campaigns, offline access
- **Action:** Install mPDF library, add download buttons

**2. Restricted Content (Volunteer-Only)**
- **Effort:** 30 minutes
- **Impact:** HIGH - Exclusive value for volunteers
- **Use:** Training materials, schedules, scripts
- **Action:** Create 3-5 volunteer-only documents

**3. Download Tracking**
- **Effort:** Already active, just add dashboard
- **Impact:** MEDIUM - Useful analytics
- **Use:** See which policies resonate
- **Action:** Display download counts in admin

### 📊 MEDIUM PRIORITY (Later)

**4. Built-in Email Signup System**
- **Effort:** 15 minutes
- **Impact:** MEDIUM - Better than CF7 for email lists
- **Use:** Verified emails, volunteer tracking, ZIP codes
- **Action:** Replace or supplement CF7 homepage signup

**5. Custom Search Interface**
- **Effort:** 1-2 hours
- **Impact:** MEDIUM - Better UX
- **Use:** Policy Library filtering
- **Action:** Build AJAX search widget

**6. Featured Policies**
- **Effort:** 30 minutes
- **Impact:** MEDIUM - Content highlighting
- **Use:** Homepage "Must-Read Policies" section
- **Action:** Mark key policies as featured, create display

### 📦 LOW PRIORITY (Nice to Have)

**7. Markdown Importer**
- **Effort:** N/A (no markdown files)
- **Impact:** LOW - Only if workflow changes
- **Use:** Bulk policy updates
- **Action:** None unless you start using markdown

**8. Email Automation Enhancement**
- **Effort:** Already active
- **Impact:** LOW - Already working
- **Use:** Test notifications
- **Action:** Install SMTP plugin for local testing

**9. Better Category Organization**
- **Effort:** 1-2 hours
- **Impact:** LOW-MEDIUM - Organizational
- **Use:** Policy browsing
- **Action:** Audit and re-categorize all 42 policies

---

## RECOMMENDED ACTION PLAN

### This Week: Quick Wins (1-2 hours total)

**Day 1: PDF Generation (30 minutes)**
```bash
# Install mPDF library
cd /path/to/plugin/includes/libraries
composer require mpdf/mpdf

# Add download button to policy templates
# Test with one policy
```

**Day 2: Volunteer-Only Content (30 minutes)**
- Create "Volunteer Training Guide" document
- Set access level to "Volunteer Only"
- Create "Phone Banking Script" (volunteer-only)
- Create "Canvassing Talking Points" (volunteer-only)
- Test: Try viewing while not logged in (should see prompt)

**Day 3: Featured Policies (30 minutes)**
- Mark 3-5 key policies as "Featured"
- Add "Featured Policies" section to homepage
- Style with Louisville Metro branding

### Next Week: Medium Efforts (3-4 hours total)

**Week 2: Email System Switch**
- Test built-in email signup vs CF7
- Consider switching homepage to `[dbpm_signup_form]`
- Export CF7 emails, import to built-in system
- Compare features

**Week 3: Analytics Dashboard**
- Add download count display to admin
- Create "Popular Policies" widget
- Track volunteer growth

**Week 4: Search Enhancement**
- Build custom Policy Library search
- Add category filter dropdown
- AJAX results display

---

## FEATURE COMPARISON

### Email Signup: CF7 vs Built-in

| Feature | Contact Form 7 | Built-in System |
|---------|---------------|-----------------|
| Email collection | ✅ Yes | ✅ Yes |
| Email verification | ❌ No | ✅ Yes (double opt-in) |
| Volunteer interest checkbox | ✅ Yes (custom) | ✅ Yes (built-in) |
| ZIP code collection | ✅ Yes (custom) | ✅ Yes (built-in) |
| Database storage | ✅ Flamingo | ✅ Custom table |
| CSV export | ✅ Yes | ✅ Yes |
| Spam protection | ⚠️ reCAPTCHA needed | ✅ Verification required |
| Unsubscribe | ❌ Manual | ✅ Auto (GDPR) |
| Segmentation | ❌ No | ✅ By volunteer/ZIP |

**Winner:** Built-in system for email campaigns, CF7 for general contact

---

## UNTAPPED POTENTIAL SUMMARY

**Features Built but Not Used:** 8 major systems
**Estimated Value:** Professional campaign management suite
**Current Usage:** ~20% of plugin capabilities
**Missing Out On:**
- PDF downloads for media/supporters
- Volunteer-exclusive content
- Email list with verification
- Download analytics
- Advanced search
- Featured content highlighting

**Total Time to Activate Core Features:** 3-4 hours
**Impact:** Transform from basic site to professional campaign platform

---

## NEXT STEPS - YOUR DECISION

**Quick Question:** What sounds most useful to you right now?

**A) PDF Downloads** (5 min setup, big impact)
- Professional document sharing
- Media kit ready
- Print-friendly policies

**B) Volunteer-Only Content** (30 min)
- Training materials
- Exclusive resources
- Reward committed volunteers

**C) Both A + B** (35 min total)
- Maximum impact
- Full volunteer experience
- Professional materials

**D) Email System Switch** (15 min)
- Better email management
- Verified subscriber list
- ZIP code targeting

**E) Analytics Dashboard** (1 hour)
- See what's working
- Track downloads
- Measure popularity

**F) Leave as-is for now**
- Current setup works
- Revisit later

What would help your campaign most?
