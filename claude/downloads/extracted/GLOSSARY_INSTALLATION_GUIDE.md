# Voter Education Glossary - Installation & Usage Guide

## 📦 What's New in Version 1.1.0

Your WordPress plugin now includes a **complete Voter Education Glossary system** with 468+ terms ready to import!

### New Features:
- ✅ Custom "Glossary Term" post type
- ✅ 13 policy categories (Voting & Elections, Government Structure, etc.)
- ✅ Bulk import system with admin interface
- ✅ Beautiful public-facing templates
- ✅ Cross-referencing between terms
- ✅ "Why This Matters" sections for every term
- ✅ Louisville-specific context
- ✅ Campaign alignment tracking
- ✅ Featured terms system
- ✅ Priority marking (Campaign Essentials)
- ✅ Search and filtering
- ✅ Shortcodes for embedding terms
- ✅ Dashboard statistics widget

---

## 🚀 Quick Start (15 Minutes)

### Step 1: Upload Enhanced Plugin Files (5 minutes)

1. **Backup your current plugin** (just in case)
   - Go to WordPress Admin → Plugins
   - Deactivate "Dave Biggers Policy Manager"
   - Download a backup via FTP if possible

2. **Upload new plugin files**
   - Delete the old `dave-biggers-policy-manager` folder from `/wp-content/plugins/`
   - Upload the new enhanced plugin folder
   - The new files include:
     - `includes/class-glossary-post-type.php` (NEW)
     - `includes/class-glossary-importer.php` (NEW)
     - `admin/js/glossary-importer.js` (NEW)
     - `templates/archive-glossary_term.php` (NEW)
     - `templates/single-glossary_term.php` (NEW)
     - `assets/priority-terms-sample.json` (NEW)
     - `dave-biggers-policy-manager.php` (UPDATED)

3. **Reactivate the plugin**
   - Go to Plugins → Installed Plugins
   - Click "Activate" on Dave Biggers Policy Manager
   - The plugin will automatically create 13 glossary categories

### Step 2: Import Priority Terms (5 minutes)

1. **Go to Glossary Importer**
   - WordPress Admin → Voter Glossary → Import Terms

2. **Import sample terms**
   - Method 1: Upload the `priority-terms-sample.json` file
   - Method 2: Click "Import Top 50 Priority Terms" button
   - Wait for import to complete

3. **Verify import**
   - Go to Voter Glossary → All Terms
   - You should see your imported terms!

### Step 3: View Your Glossary (5 minutes)

1. **Visit the glossary page**
   - Go to: `https://rundaverun.org/glossary`
   - You'll see the beautiful index page with categories

2. **Click on a term**
   - See the full definition, Why This Matters, Louisville context, etc.

3. **Test the features**
   - Try the alphabetical filter
   - Test the search function
   - Filter by category

---

## 📋 Complete Feature Guide

### Admin Features

#### Managing Terms

**Add New Term Manually:**
1. Go to Voter Glossary → Add New
2. Enter term name (e.g., "Living Wage")
3. Write the definition in the main editor
4. Fill in custom fields:
   - Why This Matters **(required)**
   - Louisville-Specific Context **(required)**
   - Data & Statistics (optional)
   - Campaign Alignment (optional)
5. Select a category (one of the 13)
6. Add tags for cross-referencing
7. Select related terms
8. Set priority level (Normal, High, Campaign Essential)
9. Check "Featured Term" if applicable
10. Publish!

**Bulk Import Terms:**
1. Go to Voter Glossary → Import Terms
2. Three import methods available:
   - **Upload JSON file**: Prepared glossary export
   - **Paste JSON**: Copy/paste term data
   - **Priority Terms**: Import pre-selected important terms

**Edit Existing Terms:**
- Go to Voter Glossary → All Terms
- Click on any term to edit
- Update fields as needed
- Save changes

#### The 13 Categories

All terms must be assigned to one of these categories:

1. **Voting & Elections** - Registration, voting methods, ballot measures
2. **Government Structure** - How Louisville Metro government works
3. **Budget & Finance** - Taxes, spending, fiscal policy
4. **Economic Development & Accountability** - Jobs, business, accountability
5. **Environmental & Sustainability** - Climate, pollution, green policy
6. **Housing & Homelessness** - Affordable housing, evictions, homelessness
7. **Public Safety & Policing** - Police, crime, safety
8. **Education** - Schools, JCPS, education policy
9. **Healthcare & Public Health** - Health access, public health, disparities
10. **Workforce Development** - Jobs, training, wages
11. **Transportation & Infrastructure** - Roads, transit, infrastructure
12. **Government Accountability & Transparency** - Oversight, transparency, reform
13. **Data Center Development** - PowerHouse case study, tech development

#### Priority Levels

- **Normal**: Standard glossary term
- **High Priority**: Important for voter education
- **Campaign Essential**: Core to your campaign platform

#### Featured Terms

Featured terms appear:
- On the glossary homepage
- In the featured terms widget
- In special promotional materials

**Best candidates for featured terms:**
- Campaign Essential topics (Living Wage, Participatory Budgeting, Mini Substations)
- Terms with strong voter appeal
- Issues that differentiate your campaign

---

### Public-Facing Features

#### Glossary Index Page

URL: `https://rundaverun.org/glossary`

**Features:**
- Filter by all 13 categories
- Alphabetical navigation (A-Z)
- Search glossary terms
- Featured terms section
- Organized by first letter
- Term counts per category

#### Individual Term Pages

URL: `https://rundaverun.org/glossary/[term-name]`

**Each term displays:**
- Full definition
- "Why This Matters" section (highlighted)
- Louisville Metro context (with local icon)
- Data & statistics (if available)
- Campaign alignment (if applicable)
- Related terms (clickable links)
- Tags for cross-referencing
- Previous/Next term navigation
- Share and print buttons

#### Responsive Design

- ✅ Mobile-optimized layouts
- ✅ Touch-friendly navigation
- ✅ Readable on all screen sizes
- ✅ Print-friendly styling

---

### Shortcodes

#### Display a Specific Term

```
[glossary_term name="Living Wage"]
```

Creates a link to the Living Wage glossary term.

**With inline definition:**
```
[glossary_term name="Living Wage" show_link="no"]
```

Displays the term with a short excerpt inline.

#### Display Featured Terms

```
[featured_glossary_terms count="3"]
```

Displays 3 featured glossary terms with excerpts.

**Usage example in a page:**
```
<h2>Key Concepts</h2>
<p>Understanding these terms will help you evaluate our policies:</p>

[featured_glossary_terms count="5"]

<p>View the complete <a href="/glossary">Voter Education Glossary</a>.</p>
```

---

### Navigation Integration

The glossary is automatically added to your site navigation menu (if you have a primary menu set).

**Manual menu integration:**
1. Go to Appearance → Menus
2. Find "Custom Links"
3. Add URL: `/glossary`
4. Link text: "Voter Glossary" or "Education"
5. Save menu

---

## 📊 Dashboard Widget

After activation, your WordPress dashboard shows glossary statistics:
- Total terms
- Number of categories
- Featured terms count
- Campaign essentials count
- Quick links to manage glossary

---

## 🎨 Customization

### Styling

All glossary styles are in the templates. To customize:

1. **Colors:**
   - Edit the `<style>` section in `archive-glossary_term.php` or `single-glossary_term.php`
   - Change colors to match your brand (currently using `#0073aa` blue and `#d63638` red)

2. **Layout:**
   - Templates use flexbox and grid for responsive layouts
   - Adjust max-width, padding, margins as needed

3. **Typography:**
   - Update font sizes, weights in the style sections
   - Ensure readability on all devices

### Template Override

To customize templates without editing plugin files:

1. Copy templates to your theme:
   ```
   /wp-content/themes/your-theme/dave-biggers-policy/
   ├── archive-glossary_term.php
   └── single-glossary_term.php
   ```

2. WordPress will use your theme versions instead of plugin versions

---

## 📁 JSON Import Format

### Required Fields

```json
{
  "term": "Term Name",
  "definition": "Main definition text",
  "category": "One of the 13 categories",
  "why_matters": "Why voters should care",
  "louisville_context": "Louisville-specific information"
}
```

### Optional Fields

```json
{
  "tags": ["tag1", "tag2", "tag3"],
  "data_stats": "Relevant data and statistics",
  "campaign_alignment": "How it relates to campaign",
  "related_terms": ["Term 1", "Term 2"],
  "priority": "normal|high|campaign",
  "featured": true|false
}
```

### Complete Example

```json
[
  {
    "term": "Living Wage",
    "definition": "A wage sufficient to provide necessities...",
    "category": "Workforce Development",
    "tags": ["employment", "equity", "economy"],
    "why_matters": "Understanding living wage helps voters...",
    "louisville_context": "In Louisville Metro, the MIT Living Wage...",
    "data_stats": "According to MIT Living Wage Calculator...",
    "campaign_alignment": "Dave's Employee Compensation Plan...",
    "related_terms": ["Minimum Wage", "Income Inequality"],
    "priority": "campaign",
    "featured": true
  }
]
```

---

## 🔧 Troubleshooting

### Terms Not Showing on Frontend

**Problem:** Uploaded terms but glossary page is blank.

**Solutions:**
1. Go to Settings → Permalinks
2. Click "Save Changes" (doesn't matter if you change anything)
3. This flushes WordPress rewrite rules
4. Visit `/glossary` again

### Import Fails with JSON Error

**Problem:** JSON import shows "Invalid JSON format" error.

**Solutions:**
1. Validate your JSON at jsonlint.com
2. Common issues:
   - Missing commas between objects
   - Extra comma after last item
   - Unescaped quotes in text
   - Missing closing brackets

### Categories Not Showing

**Problem:** Category filter is empty.

**Solutions:**
1. Go to Voter Glossary → Categories
2. Verify all 13 categories exist
3. If missing, deactivate and reactivate plugin
4. Check that terms are assigned to categories

### Related Terms Not Linking

**Problem:** Related terms don't show as links.

**Solutions:**
1. Ensure related terms use exact term names
2. Related term must be published (not draft)
3. Run the "Process Related Terms Connections" function:
   - Add to functions.php temporarily:
   ```php
   add_action('init', function() {
       if (class_exists('DB_Glossary_Importer')) {
           $importer = new DB_Glossary_Importer();
           $processed = $importer->process_related_terms_connections();
           echo "Processed $processed connections";
       }
   });
   ```
   - Visit any page once
   - Remove the code

### Templates Not Loading

**Problem:** Glossary uses default WordPress templates instead of custom ones.

**Solutions:**
1. Verify template files exist in `/templates/` folder
2. Check file permissions (should be 644)
3. Clear all caches (WordPress, CDN, browser)
4. Try visiting `/glossary/?nocache=1`

---

## 📈 Best Practices

### Creating Quality Terms

**Do:**
- ✅ Write in plain language (8th-grade reading level)
- ✅ Explain WHY voters should care
- ✅ Include Louisville-specific context always
- ✅ Cite data sources when using statistics
- ✅ Connect to campaign proposals authentically
- ✅ Cross-reference related terms
- ✅ Keep definitions focused and clear

**Don't:**
- ❌ Use jargon without explanation
- ❌ Be overly academic or technical
- ❌ Make claims without data
- ❌ Ignore Louisville context
- ❌ Write obvious partisan attacks
- ❌ Create overly long definitions (>300 words)

### Launch Strategy

**Phase 1: Soft Launch (Week 1)**
- Import top 50 priority terms
- Test all functionality
- Get feedback from campaign team
- Make adjustments

**Phase 2: Public Launch (Week 2)**
- Complete import of all 468 terms
- Announce on social media
- Send email to supporters
- Reach out to local media
- Add glossary link to all campaign materials

**Phase 3: Promotion (Ongoing)**
- "Term of the Week" social media posts
- Feature relevant terms in blog posts
- Reference glossary in debates/speeches
- Encourage voters to explore
- Track most-viewed terms (analytics)

### Maintenance

**Weekly:**
- Review new term submissions (if you enable)
- Check for broken links
- Update data/statistics if needed

**Monthly:**
- Add new terms as issues emerge
- Review analytics for popular terms
- Consider featuring different terms
- Update campaign alignments as needed

**As Needed:**
- Correct errors reported by users
- Expand terms based on voter questions
- Add timely terms related to current events

---

## 🎯 Using the Glossary in Your Campaign

### On Social Media

**"Term of the Day" Posts:**
```
💡 VOTER EDUCATION: What is "Participatory Budgeting"?

It means YOU get to decide how Louisville spends public money.
Not politicians in a back room - actual residents.

Learn more: rundaverun.org/glossary/participatory-budgeting

#RunDaveRun #Louisville #Transparency
```

**Connecting Issues:**
```
People ask: "How will you improve police-community relations?"

Start by understanding what Community Policing really means:
rundaverun.org/glossary/community-policing

Then see our plan for 46 mini substations - one per neighborhood.

#LouisvillePolicing #PublicSafety
```

### In Debates/Forums

**Reference the glossary:**
"If voters want to understand what I mean by 'living wage' versus 'minimum wage,' we have clear, data-driven definitions at rundaverun.org/glossary."

### In Door-to-Door Canvassing

**Leave behind:**
- Printed list of top 20 glossary terms
- QR code linking to full glossary
- "Want to learn more? Visit our Voter Education Glossary"

### In Emails

**Educational series:**
Week 1: "Understanding Louisville's Budget"
Week 2: "What is Participatory Budgeting?"
Week 3: "Community Policing Explained"
(Each email features 2-3 glossary terms with links)

### In Press Releases

**Position yourself as educator:**
"The Biggers campaign continues its commitment to voter education with the launch of a comprehensive policy glossary at rundaverun.org/glossary. The resource explains 468+ terms relevant to Louisville Metro government and policy, empowering residents to make informed decisions."

---

## 📞 Support & Questions

### Technical Issues
- Check troubleshooting section above
- Review WordPress debug log
- Contact hosting support for server issues

### Content Questions
- Review best practices section
- Reference existing high-quality terms as models
- Focus on clarity and voter needs

### Feature Requests
- Document what feature would help
- Explain use case for campaign
- Consider if it can be added via customization

---

## ✅ Post-Installation Checklist

- [ ] Plugin activated successfully
- [ ] 13 glossary categories created
- [ ] Sample terms imported
- [ ] Glossary index page loads (`/glossary`)
- [ ] Individual terms display correctly
- [ ] Search functionality works
- [ ] Category filtering works
- [ ] Related terms link properly
- [ ] Mobile view looks good
- [ ] Print function works
- [ ] Shortcodes tested in a page
- [ ] Dashboard widget appears
- [ ] Navigation menu includes glossary
- [ ] Permalink structure working
- [ ] All styles loading correctly

---

## 🎊 You're Ready to Launch!

Your Voter Education Glossary is now ready to become a centerpiece of your campaign's commitment to informed democracy.

**Key Differentiator:** While other campaigns make promises, you're **educating voters** so they can evaluate those promises critically. This builds trust and demonstrates your commitment to transparency and accountability.

**Next Steps:**
1. Import your full 468-term glossary
2. Announce the launch
3. Promote regularly
4. Monitor usage analytics
5. Update based on voter feedback

---

**"A Mayor That Listens, A Government That Responds"**
**starts with informed voters.**

Good luck with your campaign!

---

*Dave Biggers Policy Manager v1.1.0*
*Voter Education Glossary System*
*October 28, 2025*
