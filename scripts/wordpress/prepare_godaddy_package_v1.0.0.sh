#!/bin/bash

TIMESTAMP=$(date +%Y-%m-%d)
PACKAGE_NAME="GODADDY_DEPLOYMENT_${TIMESTAMP}"
PACKAGE_DIR="/tmp/${PACKAGE_NAME}"

echo "========================================"
echo "PREPARING GODADDY DEPLOYMENT PACKAGE"
echo "========================================"
echo ""

# Create package directory structure
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR/1_WORDPRESS_PLUGIN"
mkdir -p "$PACKAGE_DIR/2_DATABASE_EXPORT"
mkdir -p "$PACKAGE_DIR/3_DEPLOYMENT_SCRIPTS"
mkdir -p "$PACKAGE_DIR/4_DOCUMENTATION"

echo "✓ Created package structure"

# 1. Copy WordPress Plugin
echo ""
echo "1. Copying WordPress plugin..."
cp -r "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/plugins/dave-biggers-policy-manager" "$PACKAGE_DIR/1_WORDPRESS_PLUGIN/"
echo "   ✓ Plugin copied"

# 2. Export Database
echo ""
echo "2. Exporting WordPress database..."
cd "/home/dave/Local Sites/rundaverun-local/app/public"

php << 'PHP_EXPORT'
<?php
define('WP_USE_THEMES', false);
require('./wp-load.php');

$export = array(
    'site_info' => array(
        'site_url' => get_option('siteurl'),
        'home_url' => get_option('home'),
        'site_name' => get_option('blogname'),
        'site_description' => get_option('blogdescription'),
        'admin_email' => get_option('admin_email'),
        'timezone' => get_option('timezone_string'),
        'date_format' => get_option('date_format'),
        'time_format' => get_option('time_format')
    ),
    'pages' => array(),
    'policy_documents' => array(),
    'categories' => array(),
    'tags' => array(),
    'settings' => array()
);

// Export all pages
$pages = get_posts(array(
    'post_type' => 'page',
    'post_status' => 'any',
    'posts_per_page' => -1,
    'orderby' => 'ID',
    'order' => 'ASC'
));

foreach ($pages as $page) {
    $export['pages'][] = array(
        'ID' => $page->ID,
        'title' => $page->post_title,
        'slug' => $page->post_name,
        'content' => $page->post_content,
        'excerpt' => $page->post_excerpt,
        'status' => $page->post_status,
        'parent' => $page->post_parent,
        'menu_order' => $page->menu_order,
        'date' => $page->post_date,
        'modified' => $page->post_modified
    );
}

// Export all policy documents
$docs = get_posts(array(
    'post_type' => 'policy_document',
    'post_status' => 'any',
    'posts_per_page' => -1,
    'orderby' => 'ID',
    'order' => 'ASC'
));

foreach ($docs as $doc) {
    $meta = get_post_meta($doc->ID);
    $export['policy_documents'][] = array(
        'ID' => $doc->ID,
        'title' => $doc->post_title,
        'slug' => $doc->post_name,
        'content' => $doc->post_content,
        'excerpt' => $doc->post_excerpt,
        'status' => $doc->post_status,
        'date' => $doc->post_date,
        'modified' => $doc->post_modified,
        'meta' => $meta
    );
}

// Export categories
$categories = get_terms(array('taxonomy' => 'policy_category', 'hide_empty' => false));
foreach ($categories as $cat) {
    $export['categories'][] = array(
        'term_id' => $cat->term_id,
        'name' => $cat->name,
        'slug' => $cat->slug,
        'description' => $cat->description
    );
}

// Export tags
$tags = get_terms(array('taxonomy' => 'policy_tag', 'hide_empty' => false));
foreach ($tags as $tag) {
    $export['tags'][] = array(
        'term_id' => $tag->term_id,
        'name' => $tag->name,
        'slug' => $tag->slug
    );
}

// Export important settings
$export['settings'] = array(
    'page_on_front' => get_option('page_on_front'),
    'page_for_posts' => get_option('page_for_posts'),
    'show_on_front' => get_option('show_on_front'),
    'posts_per_page' => get_option('posts_per_page'),
    'permalink_structure' => get_option('permalink_structure')
);

file_put_contents('/tmp/wordpress_full_export.json', json_encode($export, JSON_PRETTY_PRINT));
echo "   ✓ Database exported (" . count($export['pages']) . " pages, " . count($export['policy_documents']) . " policy docs)\n";
?>
PHP_EXPORT

mv /tmp/wordpress_full_export.json "$PACKAGE_DIR/2_DATABASE_EXPORT/"
echo "   ✓ Export file moved"

# 3. Create URL Replacement Script
echo ""
echo "3. Creating URL replacement script..."

cat > "$PACKAGE_DIR/3_DEPLOYMENT_SCRIPTS/url_replacement.php" << 'PHP_SCRIPT'
<?php
/**
 * URL Replacement Script for GoDaddy Deployment
 * 
 * This script updates all URLs from local development to production
 * Run this ONCE after importing database to GoDaddy
 */

// CONFIGURATION - UPDATE THESE WITH YOUR GODADDY DETAILS
$old_url = 'http://rundaverun-local.local';
$new_url = 'https://rundaverun.org';  // YOUR GODADDY DOMAIN

// Database connection - UPDATE WITH YOUR GODADDY DATABASE DETAILS
$db_host = 'localhost';  // Usually 'localhost' on GoDaddy
$db_name = 'YOUR_DATABASE_NAME';  // From GoDaddy cPanel
$db_user = 'YOUR_DATABASE_USER';  // From GoDaddy cPanel
$db_pass = 'YOUR_DATABASE_PASSWORD';  // From GoDaddy cPanel

echo "<h1>WordPress URL Replacement Tool</h1>";
echo "<p>Replacing: <strong>$old_url</strong> → <strong>$new_url</strong></p>";

try {
    $pdo = new PDO("mysql:host=$db_host;dbname=$db_name", $db_user, $db_pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    echo "<h2>Connected to database successfully!</h2>";
    
    // Tables to update
    $tables = array(
        'wp_options' => array('option_value'),
        'wp_posts' => array('post_content', 'guid'),
        'wp_postmeta' => array('meta_value')
    );
    
    $total_replaced = 0;
    
    foreach ($tables as $table => $columns) {
        foreach ($columns as $column) {
            $sql = "UPDATE $table SET $column = REPLACE($column, :old_url, :new_url)";
            $stmt = $pdo->prepare($sql);
            $stmt->execute(array(':old_url' => $old_url, ':new_url' => $new_url));
            $count = $stmt->rowCount();
            $total_replaced += $count;
            echo "<p>✓ Updated $count rows in <strong>$table.$column</strong></p>";
        }
    }
    
    echo "<h2 style='color: green;'>✓ SUCCESS! Replaced URLs in $total_replaced locations</h2>";
    echo "<h3>Next Steps:</h3>";
    echo "<ol>";
    echo "<li>Delete this file (url_replacement.php) from your server for security</li>";
    echo "<li>Clear WordPress cache (if using a cache plugin)</li>";
    echo "<li>Visit your site: <a href='$new_url'>$new_url</a></li>";
    echo "<li>Log into WordPress admin: <a href='$new_url/wp-admin/'>$new_url/wp-admin/</a></li>";
    echo "</ol>";
    
} catch (PDOException $e) {
    echo "<h2 style='color: red;'>ERROR: " . $e->getMessage() . "</h2>";
    echo "<p>Please check your database credentials in this file.</p>";
}
?>
PHP_SCRIPT

echo "   ✓ URL replacement script created"

# 4. Create Database Import Script
cat > "$PACKAGE_DIR/3_DEPLOYMENT_SCRIPTS/import_data.php" << 'PHP_IMPORT'
<?php
/**
 * WordPress Data Import Script
 * 
 * This script imports pages and policy documents from the JSON export
 * Run this AFTER installing WordPress and activating the plugin
 */

define('WP_USE_THEMES', false);
require('./wp-load.php');

echo "<h1>WordPress Data Import Tool</h1>";

// Read the export file
$export_file = '../2_DATABASE_EXPORT/wordpress_full_export.json';
if (!file_exists($export_file)) {
    die("<p style='color: red;'>ERROR: Export file not found at $export_file</p>");
}

$data = json_decode(file_get_contents($export_file), true);

echo "<h2>Found:</h2>";
echo "<ul>";
echo "<li>" . count($data['pages']) . " pages</li>";
echo "<li>" . count($data['policy_documents']) . " policy documents</li>";
echo "<li>" . count($data['categories']) . " categories</li>";
echo "<li>" . count($data['tags']) . " tags</li>";
echo "</ul>";

// Import categories
echo "<h2>Importing Categories...</h2>";
foreach ($data['categories'] as $cat) {
    $term = term_exists($cat['name'], 'policy_category');
    if (!$term) {
        wp_insert_term($cat['name'], 'policy_category', array(
            'slug' => $cat['slug'],
            'description' => $cat['description']
        ));
        echo "<p>✓ Created category: {$cat['name']}</p>";
    }
}

// Import tags
echo "<h2>Importing Tags...</h2>";
foreach ($data['tags'] as $tag) {
    $term = term_exists($tag['name'], 'policy_tag');
    if (!$term) {
        wp_insert_term($tag['name'], 'policy_tag', array('slug' => $tag['slug']));
        echo "<p>✓ Created tag: {$tag['name']}</p>";
    }
}

// Import pages
echo "<h2>Importing Pages...</h2>";
$page_ids = array();
foreach ($data['pages'] as $page) {
    $existing = get_page_by_path($page['slug']);
    if (!$existing) {
        $new_id = wp_insert_post(array(
            'post_title' => $page['title'],
            'post_name' => $page['slug'],
            'post_content' => $page['content'],
            'post_excerpt' => $page['excerpt'],
            'post_status' => $page['status'],
            'post_type' => 'page',
            'menu_order' => $page['menu_order']
        ));
        $page_ids[$page['ID']] = $new_id;
        echo "<p>✓ Created page: {$page['title']}</p>";
    }
}

// Import policy documents
echo "<h2>Importing Policy Documents...</h2>";
foreach ($data['policy_documents'] as $doc) {
    $existing = get_page_by_path($doc['slug'], OBJECT, 'policy_document');
    if (!$existing) {
        $new_id = wp_insert_post(array(
            'post_title' => $doc['title'],
            'post_name' => $doc['slug'],
            'post_content' => $doc['content'],
            'post_excerpt' => $doc['excerpt'],
            'post_status' => $doc['status'],
            'post_type' => 'policy_document'
        ));
        
        // Import metadata
        if (!empty($doc['meta'])) {
            foreach ($doc['meta'] as $key => $values) {
                if (is_array($values) && count($values) > 0) {
                    update_post_meta($new_id, $key, $values[0]);
                }
            }
        }
        
        echo "<p>✓ Created policy document: {$doc['title']}</p>";
    }
}

// Update settings
echo "<h2>Updating Settings...</h2>";
if (!empty($page_ids[$data['settings']['page_on_front']])) {
    update_option('show_on_front', 'page');
    update_option('page_on_front', $page_ids[$data['settings']['page_on_front']]);
    echo "<p>✓ Set homepage</p>";
}

echo "<h2 style='color: green;'>✓ IMPORT COMPLETE!</h2>";
echo "<h3>Next Steps:</h3>";
echo "<ol>";
echo "<li>Run the URL replacement script: <a href='url_replacement.php'>url_replacement.php</a></li>";
echo "<li>Delete these import files from your server for security</li>";
echo "<li>Visit your site to verify everything works</li>";
echo "</ol>";
?>
PHP_IMPORT

echo "   ✓ Database import script created"

# 5. Create .htaccess file for WordPress
cat > "$PACKAGE_DIR/3_DEPLOYMENT_SCRIPTS/.htaccess" << 'HTACCESS'
# BEGIN WordPress
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
RewriteBase /
RewriteRule ^index\.php$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.php [L]
</IfModule>
# END WordPress

# Security Headers
<IfModule mod_headers.c>
Header set X-Content-Type-Options "nosniff"
Header set X-Frame-Options "SAMEORIGIN"
Header set X-XSS-Protection "1; mode=block"
</IfModule>

# Disable directory browsing
Options -Indexes

# Protect wp-config.php
<files wp-config.php>
order allow,deny
deny from all
</files>
HTACCESS

echo "   ✓ .htaccess file created"

# 6. Create deployment documentation
cat > "$PACKAGE_DIR/4_DOCUMENTATION/DEPLOYMENT_GUIDE.md" << 'DEPLOY_DOC'
# GoDaddy Deployment Guide
**Date:** $(date +%Y-%m-%d)
**Site:** rundaverun.org

---

## 📋 CHECKLIST BEFORE YOU START

- [ ] GoDaddy account login credentials
- [ ] FTP access credentials (from GoDaddy cPanel)
- [ ] Database name, username, and password (from GoDaddy cPanel)
- [ ] This deployment package downloaded
- [ ] 30-60 minutes to complete deployment

---

## 🚀 DEPLOYMENT STEPS

### STEP 1: Set Up WordPress on GoDaddy (15 minutes)

1. **Log into GoDaddy**
   - Go to https://www.godaddy.com/
   - Sign in to your account

2. **Access cPanel**
   - Go to My Products
   - Find your hosting account
   - Click "cPanel Admin"

3. **Install WordPress**
   - Find "WordPress" in cPanel (under Applications)
   - Click "Install"
   - Choose your domain: rundaverun.org
   - Fill in:
     - Site Name: Dave Biggers for Mayor
     - Admin Username: (choose secure username)
     - Admin Password: (choose strong password - SAVE THIS!)
     - Admin Email: dave@rundaverun.org
   - Click "Install"
   - **SAVE the database credentials shown**

4. **Note Your Database Info**
   Write down:
   - Database Name: _______________
   - Database User: _______________
   - Database Password: _______________
   - Database Host: localhost (usually)

---

### STEP 2: Upload Plugin via FTP (10 minutes)

1. **Get FTP Credentials**
   - In GoDaddy cPanel, find "FTP Accounts"
   - Create or use existing FTP account
   - Note: FTP Host, Username, Password

2. **Connect via FTP**
   - Use FileZilla (free): https://filezilla-project.org/
   - Host: ftp.rundaverun.org (or from GoDaddy)
   - Username: (from step 1)
   - Password: (from step 1)
   - Port: 21

3. **Upload Plugin**
   - Navigate to: /public_html/wp-content/plugins/
   - Upload entire folder: 1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/
   - Wait for upload to complete (150+ files, ~5 minutes)

4. **Upload Scripts**
   - Navigate to: /public_html/
   - Upload from 3_DEPLOYMENT_SCRIPTS/:
     - import_data.php
     - url_replacement.php
     - .htaccess (if not already present)

5. **Upload Database Export**
   - Create folder: /public_html/database_import/
   - Upload: 2_DATABASE_EXPORT/wordpress_full_export.json

---

### STEP 3: Activate Plugin (2 minutes)

1. **Log into WordPress Admin**
   - Go to: https://rundaverun.org/wp-admin/
   - Username: (from STEP 1)
   - Password: (from STEP 1)

2. **Activate Plugin**
   - Go to: Plugins > Installed Plugins
   - Find "Dave Biggers Policy Manager"
   - Click "Activate"

---

### STEP 4: Import Data (5 minutes)

1. **Run Import Script**
   - Visit: https://rundaverun.org/import_data.php
   - Wait for import to complete
   - You should see:
     - 5 pages imported
     - 17+ policy documents imported
     - Categories and tags created

2. **Verify Import**
   - Go to WordPress Admin
   - Check: Pages (should see Home, Contact, About, etc.)
   - Check: Policy Documents (should see all documents)

---

### STEP 5: Replace URLs (5 minutes)

1. **Edit URL Replacement Script**
   - Via FTP, download: /public_html/url_replacement.php
   - Open in text editor
   - Find lines 11-14:
     ```php
     $db_host = 'localhost';
     $db_name = 'YOUR_DATABASE_NAME';  // UPDATE THIS
     $db_user = 'YOUR_DATABASE_USER';  // UPDATE THIS
     $db_pass = 'YOUR_DATABASE_PASSWORD';  // UPDATE THIS
     ```
   - Replace with your database credentials from STEP 1
   - Save and upload back to server

2. **Run URL Replacement**
   - Visit: https://rundaverun.org/url_replacement.php
   - You should see: "SUCCESS! Replaced URLs in X locations"

3. **Delete Scripts (IMPORTANT!)**
   - Via FTP, delete:
     - /public_html/import_data.php
     - /public_html/url_replacement.php
     - /public_html/database_import/ (entire folder)

---

### STEP 6: Configure WordPress (5 minutes)

1. **Set Homepage**
   - Go to: Settings > Reading
   - "Your homepage displays": Select "A static page"
   - Homepage: Select "Home"
   - Click "Save Changes"

2. **Set Permalinks**
   - Go to: Settings > Permalinks
   - Select "Post name"
   - Click "Save Changes"

3. **Update Site Settings**
   - Go to: Settings > General
   - WordPress Address: https://rundaverun.org
   - Site Address: https://rundaverun.org
   - Click "Save Changes"

---

### STEP 7: Test Everything (10 minutes)

**Homepage:**
- [ ] Visit https://rundaverun.org/
- [ ] Buttons align properly
- [ ] Grid layouts display correctly
- [ ] All sections look good on desktop
- [ ] Test on mobile device

**Pages:**
- [ ] About Dave: https://rundaverun.org/about-dave/
- [ ] Contact: https://rundaverun.org/contact/ (should say "Reach Out")
- [ ] Get Involved: https://rundaverun.org/get-involved/
- [ ] Our Plan: https://rundaverun.org/our-plan/

**Policy Documents:**
- [ ] Visit: https://rundaverun.org/policy/
- [ ] Check: A Day in the Life (should have Jordan and Maria)
- [ ] Check: Our Plan for Louisville (4th pillar horizontal)
- [ ] Verify: 4 documents are NOT visible (unpublished)

**Admin:**
- [ ] Can log into: https://rundaverun.org/wp-admin/
- [ ] Can edit pages
- [ ] Can edit policy documents
- [ ] Plugin is active and working

---

## 🔧 TROUBLESHOOTING

### "Database connection error"
- Check wp-config.php has correct database credentials
- Verify database exists in GoDaddy cPanel

### "Page not found" errors
- Re-save permalinks: Settings > Permalinks > Save Changes
- Check .htaccess file exists in /public_html/

### Images or styling missing
- Run URL replacement script again
- Clear browser cache
- Check file paths in Media Library

### Plugin not showing
- Verify plugin folder uploaded correctly
- Check file permissions (should be 755 for folders, 644 for files)
- Try deactivating and reactivating

### Can't log in
- Use "Lost your password?" link
- Or reset via database in cPanel > phpMyAdmin

---

## 📞 SUPPORT RESOURCES

**GoDaddy Support:**
- Phone: 480-505-8877
- Chat: Available in cPanel
- Help: https://www.godaddy.com/help

**WordPress Support:**
- Documentation: https://wordpress.org/support/
- Forums: https://wordpress.org/support/forums/

---

## ✅ POST-DEPLOYMENT CHECKLIST

After everything is live:
- [ ] Test site on desktop browser
- [ ] Test site on mobile phone
- [ ] Test site on tablet
- [ ] Send test email to verify email signup works
- [ ] Share site URL with trusted friend for feedback
- [ ] Set up Google Analytics (optional)
- [ ] Set up Google Search Console (optional)
- [ ] Back up the site (GoDaddy has backup tools)

---

## 🎉 SUCCESS!

Your Dave Biggers campaign website is now live!

**Next steps:**
1. Share the site with your campaign team
2. Post on social media
3. Add to campaign materials
4. Monitor traffic and engagement

**Remember:**
- Keep WordPress and plugins updated
- Back up regularly
- Monitor for security issues
- Update content as campaign progresses

---

**Deployment package created:** $(date +%Y-%m-%d)
**Questions?** Review this guide or contact support
DEPLOY_DOC

echo "   ✓ Deployment guide created"

# 7. Create Quick Start document
cat > "$PACKAGE_DIR/4_DOCUMENTATION/QUICK_START.md" << 'QUICKSTART'
# Quick Start - 5 Steps to Go Live

## 1️⃣ Install WordPress on GoDaddy
- Log into GoDaddy > cPanel
- Click "WordPress" installer
- Choose rundaverun.org
- Save database credentials!

## 2️⃣ Upload Plugin via FTP
- Use FileZilla (free FTP client)
- Upload: 1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/
- To: /public_html/wp-content/plugins/

## 3️⃣ Activate Plugin
- Log into: https://rundaverun.org/wp-admin/
- Go to: Plugins
- Activate: Dave Biggers Policy Manager

## 4️⃣ Import Data
- Upload import_data.php to /public_html/
- Visit: https://rundaverun.org/import_data.php
- Follow instructions

## 5️⃣ Replace URLs
- Edit url_replacement.php with your database credentials
- Upload to /public_html/
- Visit: https://rundaverun.org/url_replacement.php
- Delete both scripts when done

## ✅ Done!
Visit: https://rundaverun.org/

**Full instructions:** See DEPLOYMENT_GUIDE.md
QUICKSTART

echo "   ✓ Quick start guide created"

# 8. Create troubleshooting guide
cat > "$PACKAGE_DIR/4_DOCUMENTATION/TROUBLESHOOTING.md" << 'TROUBLE'
# Troubleshooting Common Issues

## Issue: Can't connect to database
**Solution:**
1. Check wp-config.php has correct credentials
2. Verify database exists in GoDaddy cPanel
3. Check database user has proper permissions

## Issue: Pages show "404 Not Found"
**Solution:**
1. Go to Settings > Permalinks
2. Click "Save Changes" (even without changing anything)
3. Check .htaccess file exists in /public_html/

## Issue: Site looks broken / no styling
**Solution:**
1. Run url_replacement.php script again
2. Clear browser cache (Ctrl+Shift+Delete)
3. Check if theme is active in Appearance > Themes

## Issue: Plugin not visible
**Solution:**
1. Verify folder uploaded to correct location:
   /public_html/wp-content/plugins/dave-biggers-policy-manager/
2. Check file permissions (755 for folders, 644 for files)
3. Look for errors in WordPress admin

## Issue: Images or links broken
**Solution:**
1. Run url_replacement.php to fix URLs
2. Check Media Library uploads
3. Re-upload missing images via WordPress admin

## Issue: Can't log into WordPress
**Solution:**
1. Use "Lost your password?" link
2. Or reset via GoDaddy cPanel > phpMyAdmin:
   - Find wp_users table
   - Update user_pass with MD5 hash of new password

## Issue: Changes not appearing
**Solution:**
1. Clear WordPress cache (if cache plugin installed)
2. Clear browser cache
3. Check page is actually published (not draft)

## Still Having Issues?

**Contact GoDaddy Support:**
- Phone: 480-505-8877
- Live Chat: Available in cPanel
- Email: Through your GoDaddy account

**WordPress Forums:**
- https://wordpress.org/support/forums/
TROUBLE

echo "   ✓ Troubleshooting guide created"

# 9. Create file manifest
cat > "$PACKAGE_DIR/4_DOCUMENTATION/FILE_MANIFEST.md" << 'MANIFEST'
# File Manifest - What's Included

## 1_WORDPRESS_PLUGIN/
Complete WordPress plugin ready to upload:
- dave-biggers-policy-manager/ (152+ files)
  - Plugin PHP files
  - Markdown source files (updated with all changes)
  - CSS files (with enhanced styling)
  - JavaScript files
  - Templates
  - All assets

## 2_DATABASE_EXPORT/
- wordpress_full_export.json (Complete database export)
  - 5 pages (Home, Contact, About, Our Plan, Get Involved)
  - 17+ policy documents
  - Categories and tags
  - Site settings
  - All metadata

## 3_DEPLOYMENT_SCRIPTS/
- import_data.php (Imports pages and policy documents)
- url_replacement.php (Replaces local URLs with production URLs)
- .htaccess (WordPress rewrite rules and security headers)

## 4_DOCUMENTATION/
- DEPLOYMENT_GUIDE.md (Complete step-by-step instructions)
- QUICK_START.md (5-step quick deployment)
- TROUBLESHOOTING.md (Common issues and solutions)
- FILE_MANIFEST.md (This file)

## Recent Updates Included

✅ All character name changes (Alex→Jordan, Tanya→Maria)
✅ Fixed homepage layout (added display: flex/grid)
✅ Contact page heading changed to "Reach Out"
✅ Our Plan 4th pillar horizontal layout
✅ 4 documents unpublished (draft status)
✅ All text wrapping issues fixed
✅ Mobile responsive improvements

## Total Package Size
Approximately 1-2 MB (compressed)

## What You DON'T Need to Upload
These stay on your local machine:
- Old versions/archives
- Internal documentation
- Development notes
- This manifest

## What You DO Need
Everything in this package!
MANIFEST

echo "   ✓ File manifest created"

# 10. Create wp-config.php template
cat > "$PACKAGE_DIR/4_DOCUMENTATION/wp-config-template.php" << 'WPCONFIG'
<?php
/**
 * WordPress Configuration Template for GoDaddy
 * 
 * INSTRUCTIONS:
 * 1. Rename this file to: wp-config.php
 * 2. Fill in your GoDaddy database credentials below
 * 3. Generate new salts at: https://api.wordpress.org/secret-key/1.1/salt/
 * 4. Upload to /public_html/ (same folder as wp-load.php)
 */

// ** MySQL settings from GoDaddy cPanel ** //
define( 'DB_NAME', 'your_database_name' );     // Database name
define( 'DB_USER', 'your_database_user' );     // Database username  
define( 'DB_PASSWORD', 'your_database_pass' ); // Database password
define( 'DB_HOST', 'localhost' );              // Usually 'localhost'
define( 'DB_CHARSET', 'utf8mb4' );
define( 'DB_COLLATE', '' );

// ** Authentication Unique Keys and Salts ** //
// Generate new ones at: https://api.wordpress.org/secret-key/1.1/salt/
define('AUTH_KEY',         'put your unique phrase here');
define('SECURE_AUTH_KEY',  'put your unique phrase here');
define('LOGGED_IN_KEY',    'put your unique phrase here');
define('NONCE_KEY',        'put your unique phrase here');
define('AUTH_SALT',        'put your unique phrase here');
define('SECURE_AUTH_SALT', 'put your unique phrase here');
define('LOGGED_IN_SALT',   'put your unique phrase here');
define('NONCE_SALT',       'put your unique phrase here');

// ** WordPress Database Table prefix ** //
$table_prefix = 'wp_';

// ** For developers: WordPress debugging mode ** //
define( 'WP_DEBUG', false );

// ** Absolute path to the WordPress directory ** //
if ( ! defined( 'ABSPATH' ) ) {
    define( 'ABSPATH', __DIR__ . '/' );
}

// ** Sets up WordPress vars and included files ** //
require_once ABSPATH . 'wp-settings.php';
WPCONFIG

echo "   ✓ wp-config template created"

echo ""
echo "10. Creating final zip package..."

# Create the zip
cd /tmp
zip -r "${PACKAGE_NAME}.zip" "${PACKAGE_NAME}" -q

# Move to campaign directory
mv "${PACKAGE_NAME}.zip" "/home/dave/Documents/Government/budgets/RunDaveRun/campaign/"

# Get file size
SIZE=$(du -h "/home/dave/Documents/Government/budgets/RunDaveRun/campaign/${PACKAGE_NAME}.zip" | cut -f1)

# Cleanup
rm -rf "$PACKAGE_DIR"

echo ""
echo "========================================"
echo "✅ GODADDY PACKAGE READY!"
echo "========================================"
echo ""
echo "📦 Package: ${PACKAGE_NAME}.zip"
echo "📍 Location: /home/dave/Documents/Government/budgets/RunDaveRun/campaign/"
echo "📏 Size: $SIZE"
echo ""
echo "📂 Package Contents:"
echo "   ✓ Complete WordPress plugin (152+ files)"
echo "   ✓ Full database export (pages + policy docs)"
echo "   ✓ Deployment scripts (import + URL replacement)"
echo "   ✓ Complete documentation (step-by-step guides)"
echo "   ✓ Troubleshooting guide"
echo "   ✓ wp-config.php template"
echo ""
echo "📋 What's Included:"
echo "   ✓ All recent updates (name changes, layout fixes)"
echo "   ✓ Fixed homepage (display: flex/grid added)"
echo "   ✓ Contact page ('Reach Out' heading)"
echo "   ✓ 4 documents unpublished"
echo "   ✓ Mobile responsive improvements"
echo ""
echo "🚀 Next Steps:"
echo "   1. Extract this zip on your computer"
echo "   2. Read: 4_DOCUMENTATION/QUICK_START.md"
echo "   3. Follow: 4_DOCUMENTATION/DEPLOYMENT_GUIDE.md"
echo "   4. Deploy to GoDaddy (30-60 minutes)"
echo ""
echo "📞 Need Help?"
echo "   - GoDaddy Support: 480-505-8877"
echo "   - See: TROUBLESHOOTING.md"
echo ""
echo "========================================"

