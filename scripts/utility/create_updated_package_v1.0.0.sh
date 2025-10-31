#!/bin/bash

TIMESTAMP=$(date +%Y-%m-%d)
PACKAGE_NAME="DAVE_BIGGERS_WEBSITE_UPDATED_${TIMESTAMP}"
PACKAGE_DIR="/tmp/${PACKAGE_NAME}"

echo "Creating updated WordPress package..."
echo "Package: ${PACKAGE_NAME}"

# Create package directory
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Copy the WordPress plugin
echo "Copying plugin files..."
cp -r "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/plugins/dave-biggers-policy-manager" "$PACKAGE_DIR/"

# Export the database
echo "Exporting WordPress database..."
cd "/home/dave/Local Sites/rundaverun-local/app/public"
php << 'PHPEOF'
<?php
define('WP_USE_THEMES', false);
require('./wp-load.php');

$export_data = array(
    'site_url' => get_option('siteurl'),
    'home_url' => get_option('home'),
    'pages' => array(),
    'policy_documents' => array()
);

// Export pages
$pages = get_posts(array('post_type' => 'page', 'post_status' => 'any', 'posts_per_page' => -1));
foreach ($pages as $page) {
    $export_data['pages'][] = array(
        'ID' => $page->ID,
        'title' => $page->post_title,
        'content' => $page->post_content,
        'status' => $page->post_status,
        'slug' => $page->post_name,
        'modified' => $page->post_modified
    );
}

// Export policy documents
$docs = get_posts(array('post_type' => 'policy_document', 'post_status' => 'any', 'posts_per_page' => -1));
foreach ($docs as $doc) {
    $export_data['policy_documents'][] = array(
        'ID' => $doc->ID,
        'title' => $doc->post_title,
        'content' => $doc->post_content,
        'status' => $doc->post_status,
        'slug' => $doc->post_name,
        'modified' => $doc->post_modified,
        'meta' => get_post_meta($doc->ID)
    );
}

file_put_contents('/tmp/wordpress_export.json', json_encode($export_data, JSON_PRETTY_PRINT));
echo "Database exported to wordpress_export.json\n";
?>
PHPEOF

# Move export to package
mv /tmp/wordpress_export.json "$PACKAGE_DIR/"

# Create README
cat > "$PACKAGE_DIR/README.md" << 'READMEEOF'
# DAVE BIGGERS WORDPRESS SITE - UPDATED PACKAGE
**Date:** 2025-10-13
**Package Version:** 2.0 (with latest updates)

## RECENT UPDATES IN THIS PACKAGE

### Content Changes:
1. ✅ **Day in the Life document** - Character names changed (Alex→Jordan, Tanya→Maria)
2. ✅ **Our Plan page** - 4th pillar ($15M Participatory Budgeting) displayed horizontally
3. ✅ **Home page** - Fixed button overlapping, fixed "24% Compounded Raises" text wrapping
4. ✅ **Contact page** - Heading changed from "Contact Dave Biggers for Mayor" to "Reach Out"
5. ✅ **4 documents unpublished** - Changed to draft status (4-Week Timeline, Messaging Framework, Media Kit, Endorsement Package)

### Technical Changes:
- Updated markdown source files with all changes
- WordPress database export includes all pages and policy documents
- Non-breaking spaces added to prevent text wrapping issues

## PACKAGE CONTENTS

1. **dave-biggers-policy-manager/** - Complete WordPress plugin
   - Updated markdown files in assets/markdown-files/
   - All PHP, CSS, JS files
   - Plugin documentation

2. **wordpress_export.json** - WordPress database export
   - All pages (Home, Contact, About, etc.)
   - All policy documents
   - Post metadata

## TO USE THIS PACKAGE

### Option 1: Import to WordPress
1. Upload plugin to wp-content/plugins/
2. Activate plugin
3. Use import function to load policy documents

### Option 2: Fresh Setup
1. Install WordPress
2. Upload and activate plugin
3. Import wordpress_export.json data

## DEPLOYMENT NOTES

**Local Development URL:** http://rundaverun-local.local/
**Production URL:** https://rundaverun.org/ (GoDaddy)

When deploying to production:
- Update all URLs from rundaverun-local.local to rundaverun.org
- Import database
- Upload plugin files
- Test all pages

## FILES INCLUDED

- Complete WordPress plugin (152+ files)
- Database export (JSON format)
- This README

## SUPPORT

Questions? Email: dave@rundaverun.org

---

**Package created:** October 13, 2025
**WordPress Version:** 6.7.1
**PHP Version:** 8.2+
READMEEOF

# Create the zip
echo "Creating zip archive..."
cd /tmp
zip -r "${PACKAGE_NAME}.zip" "${PACKAGE_NAME}" -q

# Move to campaign directory
mv "${PACKAGE_NAME}.zip" "/home/dave/Documents/Government/budgets/RunDaveRun/campaign/"

# Get file size
SIZE=$(du -h "/home/dave/Documents/Government/budgets/RunDaveRun/campaign/${PACKAGE_NAME}.zip" | cut -f1)

echo ""
echo "✅ Package created successfully!"
echo "Location: /home/dave/Documents/Government/budgets/RunDaveRun/campaign/${PACKAGE_NAME}.zip"
echo "Size: $SIZE"
echo ""
echo "This package includes:"
echo "  - Complete WordPress plugin with updated markdown files"
echo "  - WordPress database export (all pages and policy documents)"
echo "  - README with deployment instructions"

# Cleanup
rm -rf "$PACKAGE_DIR"
