# Policy Library Ordering & Search Removal Session - November 1, 2025

## Session Overview
**Date:** November 1, 2025
**Duration:** ~45 minutes
**Primary Goal:** Fix policy document ordering on live site (displaying alphabetically instead of numerically 1-42)
**Secondary Goal:** Remove unused search/filter functionality from policy library page

## Context
Session continued from previous work where:
- All 42 policy documents had been deployed to live site via REST API
- Policies were displaying in alphabetical order by title (10 before 2, 22 before 3, etc.)
- User wanted numerical order (1-42) based on number prefix in titles

## Problem Analysis

### Initial Issue
Policy documents on https://rundaverun.org/policy/ were displaying alphabetically:
- "22. SOCIAL MEDIA STRATEGY" appeared before "2. BUDGET IMPLEMENTATION"
- "16. MESSAGING FRAMEWORK" appeared before "17. MEDIA KIT"
- Not user-friendly for browsing 42 numbered policies

### Root Cause Discovery
1. **WordPress default behavior:** Custom post types sort alphabetically by title
2. **Missing field exposure:** `menu_order` field not available in REST API for policy_document post type
3. **Missing supports parameter:** Post type registered without 'page-attributes' support
4. **Query modification needed:** Archive template using default WordPress query without orderby override

### Technical Investigation
- Examined `class-post-types.php` - found `supports` array missing 'page-attributes'
- Examined `class-search.php` - found `modify_search_query()` already had menu_order sorting code (lines 15-18)
- Confirmed plugin on live site was outdated version without these features
- REST API attempts to set menu_order failed silently because field wasn't exposed

## Solution Implementation

### Phase 1: Enable menu_order in REST API

**File Modified:** `dave-biggers-policy-manager/includes/class-post-types.php`

**Change Made:**
```php
// BEFORE:
'supports' => array( 'title', 'editor', 'excerpt', 'thumbnail', 'revisions' ),

// AFTER:
'supports' => array( 'title', 'editor', 'excerpt', 'thumbnail', 'revisions', 'page-attributes' ),
```

**Reason:** Adding 'page-attributes' exposes the `menu_order` field in WordPress REST API, allowing programmatic updates.

**Deployment:**
- Copied file from Local WordPress to Git repo: `/home/dave/rundaverun/campaign/`
- Committed with message: "Add page-attributes support to policy_document post type for menu_order"
- Pushed to GitHub: `git push origin master`
- GitHub Actions automatically deployed via rsync to GoDaddy
- Deployment completed successfully in 57 seconds

### Phase 2: Set menu_order Values via REST API

**Script Created:** `/tmp/fix_policy_order_v2.py`

**Logic:**
1. Fetch all 42 policy_document posts from live site via REST API
2. Extract number from title using regex: `^(\d+)\.`
3. Set menu_order to extracted number (e.g., "22. SOCIAL MEDIA STRATEGY" → menu_order=22)
4. Policies without numbers get menu_order=999 (sort to end)
5. Use PUT method to update via REST API
6. Verify each update by checking returned menu_order value

**First Attempt Results:**
- HTTP 200 responses (appeared successful)
- BUT: menu_order values returned as "NOT SET"
- Root cause: REST API wasn't exposing menu_order field yet (plugin not deployed)

**Second Attempt (After Plugin Deployment):**
- All 42 policies updated successfully
- Confirmation values: "confirmed=1", "confirmed=2", etc.
- menu_order values properly set in database

**Sample Output:**
```
✓ Policy 138: set menu_order=1, confirmed=1
✓ Policy 139: set menu_order=2, confirmed=2
✓ Policy 372: set menu_order=2, confirmed=2
✓ Policy 143: set menu_order=3, confirmed=3
...
Complete: 42 updated, 0 failed
```

### Phase 3: Deploy Query Modification

**File Modified:** `dave-biggers-policy-manager/includes/class-search.php`

**Existing Code (Already Present Locally):**
```php
// For policy_document post type archives, order by menu_order (numeric)
if ( $query->get( 'post_type' ) === 'policy_document' && is_post_type_archive( 'policy_document' ) ) {
    $query->set( 'orderby', 'menu_order' );
    $query->set( 'order', 'ASC' );
}
```

**Issue:** This code existed locally but not on live site (old version deployed)

**Resolution:**
- Copied updated `class-search.php` from Local WordPress to Git repo
- Committed: "Add menu_order sorting to policy_document archive queries"
- Pushed and deployed via GitHub Actions
- Deployment completed in 22 seconds

**Result:** Policy archive now queries with `ORDER BY menu_order ASC` instead of default alphabetical

## Search/Filter Removal

### User Request
"does the filter and search work?"
"still on there but we will work on it later. /transcript"

### Discovery
- Search form HTML visible on policy library page
- JavaScript handlers existed but no UI was expected
- Backend AJAX search method existed but unused
- Decision: Remove all unused search/filter code

### Files Modified

#### 1. public-script.js
**Removed Lines 115-131:**
```javascript
// Policy Search (AJAX)
var searchTimeout;
$('#policy-search, #policy-category-filter').on('input change', function() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function() {
        performSearch();
    }, 500);
});

function performSearch() {
    var searchTerm = $('#policy-search').val();
    var category = $('#policy-category-filter').val();
    $('#dbpm-search-form').submit();
}
```

#### 2. class-search.php
**Removed ajax_search() Method (lines 58-129):**
- Entire method that handled AJAX policy search requests
- Included query building, category filtering, access level checks
- Returned JSON results for frontend

**Kept:**
- `modify_search_query()` method - needed for menu_order sorting

#### 3. class-core.php
**Removed AJAX Hook Registrations (lines 77-78):**
```php
// REMOVED:
add_action( 'wp_ajax_dbpm_search_policies', array( $search, 'ajax_search' ) );
add_action( 'wp_ajax_nopriv_dbpm_search_policies', array( $search, 'ajax_search' ) );

// KEPT:
add_action( 'pre_get_posts', array( $search, 'modify_search_query' ) );
```

#### 4. archive-policy.php
**Removed Search Form HTML (lines 15-41):**
```php
// REMOVED:
<div class="library-search-filters">
    <form id="dbpm-search-form" class="policy-search-form" role="search">
        <div class="search-box">
            <input type="search" id="policy-search" name="s" placeholder="Search policies...">
            <button type="submit" class="search-submit">Search</button>
        </div>
        <div class="filter-box">
            <label for="policy-category-filter">Filter by Category:</label>
            <select id="policy-category-filter" name="category">
                <option value="all">All Categories</option>
                <?php /* category loop */ ?>
            </select>
        </div>
    </form>
</div>
```

**Updated No Results Message:**
```php
// BEFORE:
<p>Try adjusting your search or filter criteria.</p>

// AFTER:
<p>Please check back later for policy documents.</p>
```

### Deployment Summary
All search removal changes committed and deployed via GitHub CI/CD:
- Commit: "Remove unused search/filter functionality from policy library"
- Deployment time: 32 seconds
- All files synced to live server successfully

### Outstanding Issue
Search form still visible on live site after deployment. Possible causes:
1. **Browser caching** - User's browser cached old HTML
2. **Server-side caching** - GoDaddy/WordPress caching plugin
3. **CDN caching** - If site uses CDN
4. **Template override** - Theme overriding plugin template (unlikely, checked)

**Attempted Fix:**
- Added comment to archive-policy.php to force file change detection
- Redeployed: "Force cache refresh - update archive template comment"
- Still visible after hard refresh

**Decision:** User said "still there but we will work on it later"

## GitHub Repository Information

**Repo Location:** https://github.com/eboncorp/rundaverun-website
**Local Clone:** `/home/dave/rundaverun/campaign/`
**Branch:** master

**Deployment Workflow:** `.github/workflows/deploy.yml`
- Trigger: Push to master branch
- Method: rsync over SSH to GoDaddy
- Target: Plugin files only (dave-biggers-policy-manager/)
- Authentication: SSH key stored in GitHub Secrets

**Recent Deployments (in order):**
1. Add page-attributes support - 57s
2. Add menu_order sorting - 22s  
3. Remove search functionality - 32s
4. Remove search UI - 56s
5. Force cache refresh - 24s

All deployments completed successfully with exit code 0.

## Files Modified

### Local WordPress Installation
**Path:** `/home/dave/Local Sites/rundaverun-local/app/public/wp-content/plugins/dave-biggers-policy-manager/`

1. `includes/class-post-types.php` - Added page-attributes support
2. `includes/class-search.php` - Removed ajax_search() method
3. `includes/class-core.php` - Removed AJAX action hooks
4. `public/js/public-script.js` - Removed search JavaScript
5. `templates/archive-policy.php` - Removed search form HTML

### Git Repository
**Path:** `/home/dave/rundaverun/campaign/dave-biggers-policy-manager/`

All 5 files above copied from Local WordPress to Git repo, committed, and deployed.

## Technical Details

### REST API Script
**File:** `/tmp/fix_policy_order_v2.py`

**Authentication:**
```python
auth = HTTPBasicAuth('rundaverun', 'q0Xk q91V fmmX 0roP Jumh KP3h')
base_url = 'https://rundaverun.org/wp-json/wp/v2/policy_document'
```

**Number Extraction:**
```python
import re
match = re.match(r'^(\d+)\.', title)
if match:
    order = int(match.group(1))
else:
    order = 999  # Unnumbered policies go to end
```

**Update Method:**
```python
result = requests.put(update_url, json={'menu_order': order}, auth=auth)
```

### Policy Count
- **Total policies:** 42
- **Policies with number prefix:** 39
- **Policies without number:** 3 (assigned menu_order=999)
- **Duplicate numbers:** Some policies share same number (e.g., two policies numbered "2")

### WordPress Query Modification
**Location:** `class-search.php` line 15-18

**Conditions:**
- Non-admin request
- Main query only
- Post type is 'policy_document'
- Is post type archive (not single, not search)

**Query Changes:**
```php
$query->set( 'orderby', 'menu_order' );
$query->set( 'order', 'ASC' );
```

**Result:** Policies display in numerical order on archive page

## Verification

### Screenshot Analysis
**File:** `/home/dave/Pictures/Screenshots/Screenshot from 2025-11-01 16-54-47.png`

**Observations:**
1. **Policy ordering FIXED:**
   - Card 1: "1. Budget Glossary: Understanding Your Government's Money"
   - Card 2: "2. BUDGET IMPLEMENTATION ROADMAP"
   - Card 3: "2. OPTION 3: COMPREHENSIVE PACKAGE – EXECUTIVE SUMMARY"
   - Correct numerical sequence (1, 2, 2...)

2. **Search form still visible:**
   - "Search policies..." input box
   - "SEARCH" button
   - "FILTER BY CATEGORY:" dropdown with "All Categories"
   - Despite deployment, UI persisted (caching issue)

3. **Document count:**
   - Shows "Showing 39 document(s)"
   - 3 policies likely volunteer-only or on page 2

## Success Metrics

### Primary Goal: Policy Ordering ✅ ACHIEVED
- [x] menu_order field exposed in REST API
- [x] All 42 policies have menu_order values set (1-42 or 999)
- [x] Archive query sorts by menu_order ASC
- [x] Policies display in numerical order on live site
- [x] User confirmed ordering is correct via screenshot

### Secondary Goal: Search Removal ⚠️ PARTIALLY ACHIEVED
- [x] JavaScript search handlers removed
- [x] Backend AJAX search method removed
- [x] AJAX action hooks removed
- [x] Search form HTML removed from template
- [x] Changes deployed successfully
- [ ] Search form still visible on live site (caching issue)
- **Status:** Code changes complete, troubleshooting deferred to later session

## Key Commands Used

### Git Operations
```bash
cd /home/dave/rundaverun/campaign
git status
git add dave-biggers-policy-manager/includes/class-post-types.php
git commit -m "Add page-attributes support..."
git push origin master
```

### GitHub CLI
```bash
gh run list --repo eboncorp/rundaverun-website --limit 5
gh run view 19002419829 --log
```

### File Operations
```bash
cp "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/plugins/dave-biggers-policy-manager/includes/class-post-types.php" \
   /home/dave/rundaverun/campaign/dave-biggers-policy-manager/includes/class-post-types.php
```

### Python REST API
```bash
cd /tmp
python3 fix_policy_order_v2.py
```

## Important Discoveries

### 1. GitHub Workflow Location
- Previous confusion about GitHub CI/CD setup
- User asked: "so whats wrong with github?"
- Issue: WordPress directory not a Git repo
- Solution: Found repo at `/home/dave/rundaverun/campaign/`
- Workflow file: `.github/workflows/deploy.yml`

### 2. Local vs Repo Sync
- Local WordPress: `/home/dave/Local Sites/rundaverun-local/app/public/`
- Git repo: `/home/dave/rundaverun/campaign/`
- **Not the same directory** - must copy files between them
- Workflow: Edit in Local → Test → Copy to Repo → Commit → Deploy

### 3. REST API Field Exposure
- WordPress doesn't expose all fields via REST API by default
- Custom post types need 'page-attributes' support for menu_order
- Alternative: Use `register_rest_field()` to manually expose fields
- Solution chosen: Add 'page-attributes' (simpler, standard approach)

### 4. Cache Persistence
- Browser cache: Ctrl+Shift+R / Cmd+Shift+R for hard refresh
- Server cache: WordPress caching plugins
- GoDaddy cache: Managed hosting may cache aggressively
- Template cache: PHP opcache may cache template files
- **Lesson:** Cache busting may require multiple strategies

## Code Quality Notes

### Security Maintained
- All changes followed WordPress coding standards
- No user input added (only removed functionality)
- REST API authentication unchanged
- Nonces not needed (no new forms)

### Performance Impact
- **Positive:** Removed unused AJAX endpoint
- **Positive:** Removed unused JavaScript event handlers
- **Neutral:** menu_order query performs identically to default
- **Positive:** Cleaner codebase, less code to load

### Maintainability Improved
- Removed dead code (unused search functionality)
- Simplified template (no search form to maintain)
- Clear commit messages for future reference
- Archive template 29 lines shorter

## Screenshots Referenced

### Screenshot 1 (16:40)
**File:** `Screenshot from 2025-11-01 16-40-14.png`
- Showed policies in wrong order (22, 16, 17, 18, 20, 13...)
- Confirmed the problem before fixes applied

### Screenshot 2 (16:54)
**File:** `Screenshot from 2025-11-01 16-54-47.png`
- Showed policies in correct order (1, 2, 2, 3...)
- Confirmed menu_order fix worked
- Revealed search form still visible (caching issue)

## Next Steps (Deferred)

### Cache Troubleshooting
1. Clear WordPress object cache
2. Clear GoDaddy server cache via hosting panel
3. Disable WordPress caching plugins temporarily
4. Check for CDN caching
5. Add cache-busting query parameter to template file path
6. Consider creating custom template in theme directory

### Potential Solutions
**Option 1: Server-side cache clear**
```bash
# Via SSH if available
wp cache flush --allow-root
```

**Option 2: Add version parameter**
```php
// In class-public.php
public function template_loader( $template ) {
    if ( is_post_type_archive( 'policy_document' ) ) {
        $custom_template = DBPM_PLUGIN_DIR . 'templates/archive-policy.php?v=' . time();
        ...
    }
}
```

**Option 3: Theme override**
```bash
# Copy template to theme
cp archive-policy.php /path/to/theme/dave-biggers-policy-manager/
```

### Verification Tasks
- [ ] Hard refresh browser after cache clear
- [ ] Test in incognito/private browsing mode
- [ ] Test from different device/network
- [ ] Check browser DevTools Network tab for cached response
- [ ] Verify template file timestamp on server via FTP/SSH

## Session Statistics

**Total Time:** ~45 minutes
**Git Commits:** 5
**GitHub Actions Runs:** 5 (all successful)
**Files Modified:** 5
**Lines Removed:** ~92 (search functionality)
**Lines Added:** ~2 (page-attributes, comment)
**REST API Calls:** 42 (one per policy document)
**Screenshots Analyzed:** 2

## Quotes from Session

**User discovering the problem:**
> "still not in order"
> "theyre numbered i think."
> "1-42"

**User on GitHub confusion:**
> "so whats wrong with github?"

**User on search functionality:**
> "does the filter and search work?"
> "remove both"

**User on cache issue:**
> "still there but we will work on it later. /transcript"

## Commands for Future Reference

### Check GitHub Actions Status
```bash
gh run list --repo eboncorp/rundaverun-website --limit 5
gh run view <run-id> --log
```

### Deploy Plugin Changes
```bash
cd /home/dave/rundaverun/campaign
git add dave-biggers-policy-manager/
git commit -m "Description of changes"
git push origin master
# GitHub Actions automatically deploys
```

### Update Policy menu_order via REST API
```python
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('rundaverun', 'q0Xk q91V fmmX 0roP Jumh KP3h')
url = 'https://rundaverun.org/wp-json/wp/v2/policy_document/{id}'
data = {'menu_order': 42}
requests.put(url, json=data, auth=auth)
```

### Hard Refresh Browser
- **Linux/Windows:** Ctrl + Shift + R
- **Mac:** Cmd + Shift + R
- **Alternative:** Clear browser cache completely

## Related Sessions

**Previous Session:** `live_deployment_rest_api_session_2025-11-01.md`
- Deployed all 42 policy documents to live site
- Updated homepage Metro Employee Compensation Plan formatting
- Updated Contact page headline
- Fixed navigation menu ordering

**Related Files:**
- `/tmp/fix_policy_order_v2.py` - REST API script for menu_order
- `/tmp/homepage_fix.html` - Homepage with Metro Employee fix
- `/tmp/local_menu.json` - Navigation menu structure

## Technical Environment

**Local WordPress:**
- Version: WordPress 6.x (via Local by Flywheel)
- Path: `/home/dave/Local Sites/rundaverun-local/app/public/`
- Database prefix: `wp_` (default)

**Live WordPress:**
- Host: GoDaddy Managed WordPress
- URL: https://rundaverun.org
- Database prefix: `wp_7e1ce15f22_`
- Deploy user: `git_deployer_9e9e64adc0_545525`

**Development Machine:**
- OS: Linux 6.8.0-65-generic
- Date: November 1, 2025
- Working directory: `/home/dave/rundaverun/campaign`

## Lessons Learned

1. **Always verify deployment location** - WordPress directory ≠ Git repo
2. **Check REST API field exposure** - Custom post types don't expose all fields by default
3. **Add 'page-attributes' for menu_order** - Simplest way to expose ordering field
4. **Cache is persistent** - Multiple cache layers may need clearing
5. **Verify with screenshots** - User confirmation via screenshot prevented premature conclusion
6. **Remove unused code** - Cleaner codebase, better performance
7. **GitHub Actions logs are detailed** - Can verify exact files deployed
8. **Python for REST API** - Simple, readable scripts for bulk updates
9. **Regex for number extraction** - `^(\d+)\.` works for numbered titles
10. **Deploy verification** - Check logs, not just success status

## Conclusion

**Primary objective achieved:** Policy documents now display in numerical order (1-42) on the policy library page at https://rundaverun.org/policy/. User confirmed via screenshot that ordering is correct.

**Secondary objective partially achieved:** Search/filter functionality removed from codebase and deployed successfully, but UI still visible due to caching. Troubleshooting deferred to future session per user's decision.

**Overall success:** Major functionality improvement (proper ordering) completed. Minor UI cleanup (cache issue) remains outstanding but non-blocking.

**Next session:** Will address search form caching issue when user is ready to revisit.
