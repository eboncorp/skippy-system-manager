# WP-CLI Quick Reference

**Date Created**: 2025-10-28
**Purpose**: Quick reference for commonly used WP-CLI commands
**Applies To**: WordPress development and maintenance
**Priority**: HIGH (used frequently)

## Essential Information

### Command Structure
```bash
wp <command> <subcommand> [options] [arguments]
```

### Local by Flywheel Requirement
```bash
# ALWAYS use --allow-root flag on Local by Flywheel
wp command --allow-root

# Change to WordPress directory first
cd "/home/dave/Local Sites/rundaverun-local/app/public"
```

### GoDaddy Production Notes
- Custom table prefix: `wp_7e1ce15f22_`
- Limited SSH access (check availability)
- May need to use phpMyAdmin for some operations

---

## Database Commands

### Export (Backup)
```bash
# Basic export
wp db export --allow-root

# Export with custom filename
wp db export backup_2025-10-28.sql --allow-root

# Export with full path
wp db export /home/dave/rundaverun/backups/backup_$(date +%Y%m%d_%H%M%S).sql --allow-root

# Export specific tables
wp db export --tables=wp_posts,wp_postmeta --allow-root
```

### Import
```bash
# Import database
wp db import backup.sql --allow-root

# Reset and import (WARNING: Deletes all data first!)
wp db reset --yes --allow-root
wp db import backup.sql --allow-root
```

### Search-Replace
```bash
# Basic search-replace (dry run first!)
wp search-replace 'old-url' 'new-url' --dry-run --allow-root

# Actual replacement
wp search-replace 'old-url' 'new-url' --all-tables --allow-root

# Common: Local to production
wp search-replace 'http://rundaverun-local.local' 'https://rundaverun.org' \
  --all-tables --allow-root

# Production to local
wp search-replace 'https://rundaverun.org' 'http://rundaverun-local.local' \
  --all-tables --allow-root

# With specific tables
wp search-replace 'old' 'new' wp_posts wp_postmeta --allow-root

# Skip specific columns
wp search-replace 'old' 'new' --skip-columns=guid --allow-root
```

### Database Check/Repair
```bash
# Check database
wp db check --allow-root

# Repair database
wp db repair --allow-root

# Optimize database
wp db optimize --allow-root
```

### Database Queries
```bash
# Run SQL query
wp db query "SELECT option_name, option_value FROM wp_options LIMIT 10" --allow-root

# Get site URL
wp db query "SELECT option_value FROM wp_options WHERE option_name = 'siteurl'" --allow-root

# Get home URL
wp db query "SELECT option_value FROM wp_options WHERE option_name = 'home'" --allow-root

# GoDaddy: Remember custom table prefix
wp db query "SELECT option_value FROM wp_7e1ce15f22_options WHERE option_name = 'siteurl'" --allow-root
```

---

## Core Commands

### Version Info
```bash
# WordPress version
wp core version --allow-root

# Full version info
wp core version --extra --allow-root
```

### Update Core
```bash
# Check for updates
wp core check-update --allow-root

# Update to latest version
wp core update --allow-root

# Update to specific version
wp core update --version=6.3.2 --allow-root
```

### Verify Core Files
```bash
# Verify core file checksums
wp core verify-checksums --allow-root
```

### Download WordPress
```bash
# Download latest WordPress
wp core download --allow-root

# Download specific version
wp core download --version=6.3.2 --allow-root
```

---

## Plugin Commands

### List Plugins
```bash
# List all plugins
wp plugin list --allow-root

# List active plugins
wp plugin list --status=active --allow-root

# List inactive plugins
wp plugin list --status=inactive --allow-root

# List with specific fields
wp plugin list --fields=name,status,version --allow-root

# Count plugins
wp plugin list --format=count --allow-root
```

### Activate/Deactivate Plugins
```bash
# Activate single plugin
wp plugin activate plugin-name --allow-root

# Activate all plugins
wp plugin activate --all --allow-root

# Deactivate single plugin
wp plugin deactivate plugin-name --allow-root

# Deactivate all plugins (useful for debugging)
wp plugin deactivate --all --allow-root
```

### Install Plugins
```bash
# Install plugin
wp plugin install plugin-name --allow-root

# Install and activate
wp plugin install plugin-name --activate --allow-root

# Install specific version
wp plugin install plugin-name --version=1.2.3 --allow-root
```

### Update Plugins
```bash
# Check for plugin updates
wp plugin list --update=available --allow-root

# Update single plugin
wp plugin update plugin-name --allow-root

# Update all plugins
wp plugin update --all --allow-root

# Dry run (see what would be updated)
wp plugin update --all --dry-run --allow-root
```

### Delete Plugins
```bash
# Delete inactive plugin
wp plugin delete plugin-name --allow-root

# Delete multiple plugins
wp plugin delete plugin1 plugin2 plugin3 --allow-root
```

---

## Theme Commands

### List Themes
```bash
# List all themes
wp theme list --allow-root

# List active theme
wp theme list --status=active --allow-root

# Get current theme name
wp theme list --status=active --field=name --allow-root
```

### Activate Theme
```bash
# Activate theme
wp theme activate theme-name --allow-root

# Common: Activate default theme (for debugging)
wp theme activate twentytwentythree --allow-root
```

### Install Themes
```bash
# Install theme
wp theme install theme-name --allow-root

# Install and activate
wp theme install theme-name --activate --allow-root
```

### Update Themes
```bash
# Update single theme
wp theme update theme-name --allow-root

# Update all themes
wp theme update --all --allow-root
```

---

## Post Commands

### List Posts
```bash
# List all posts
wp post list --allow-root

# List with specific fields
wp post list --fields=ID,post_title,post_status --allow-root

# List by status
wp post list --post_status=publish --allow-root
wp post list --post_status=draft --allow-root

# List by post type
wp post list --post_type=page --allow-root

# Count posts
wp post list --format=count --allow-root

# Search posts
wp post list --s="search term" --allow-root
```

### Create Post
```bash
# Create draft post
wp post create --post_title="My Post" --post_content="Content here" --allow-root

# Create published post
wp post create --post_title="My Post" --post_status=publish --allow-root

# Create page
wp post create --post_type=page --post_title="About" --post_status=publish --allow-root
```

### Update Post
```bash
# Update post title
wp post update 123 --post_title="New Title" --allow-root

# Update post status
wp post update 123 --post_status=publish --allow-root

# Update multiple posts
wp post update 123 124 125 --post_status=publish --allow-root
```

### Delete Posts
```bash
# Delete single post
wp post delete 123 --allow-root

# Force delete (bypass trash)
wp post delete 123 --force --allow-root

# Delete all posts with specific status
wp post delete $(wp post list --post_status=draft --format=ids --allow-root) --allow-root
```

### Get Post
```bash
# Get post details
wp post get 123 --allow-root

# Get specific field
wp post get 123 --field=post_title --allow-root
```

---

## Option Commands

### Get Options
```bash
# Get option value
wp option get siteurl --allow-root
wp option get home --allow-root
wp option get blogname --allow-root
wp option get admin_email --allow-root

# Get all options
wp option list --allow-root

# Search options
wp option list --search="*theme*" --allow-root
```

### Update Options
```bash
# Update option
wp option update siteurl 'https://rundaverun.org' --allow-root
wp option update home 'https://rundaverun.org' --allow-root

# Update site title
wp option update blogname 'Dave Biggers for Mayor' --allow-root
```

### Add/Delete Options
```bash
# Add option
wp option add custom_option 'value' --allow-root

# Delete option
wp option delete custom_option --allow-root
```

---

## Cache Commands

### Flush Cache
```bash
# Flush object cache
wp cache flush --allow-root

# Flush rewrite rules
wp rewrite flush --allow-root
```

---

## User Commands

### List Users
```bash
# List all users
wp user list --allow-root

# List with specific fields
wp user list --fields=ID,user_login,user_email --allow-root

# List by role
wp user list --role=administrator --allow-root
```

### Create User
```bash
# Create user
wp user create username user@example.com --role=administrator --allow-root

# Create with specific password
wp user create username user@example.com --role=administrator --user_pass=password123 --allow-root
```

### Update User
```bash
# Update user email
wp user update 1 --user_email=newemail@example.com --allow-root

# Update user password
wp user update 1 --user_pass=newpassword --allow-root

# Update user role
wp user set-role 2 editor --allow-root
```

### Delete User
```bash
# Delete user (reassign posts to another user)
wp user delete 2 --reassign=1 --allow-root
```

---

## Menu Commands

### List Menus
```bash
# List menus
wp menu list --allow-root

# List menu items
wp menu item list MENU_ID --allow-root
```

### Create Menu
```bash
# Create menu
wp menu create "Main Menu" --allow-root

# Get menu ID after creating
wp menu list --allow-root
```

---

## Media Commands

### List Media
```bash
# List media files
wp media list --allow-root

# List with specific fields
wp media list --fields=ID,post_title,post_mime_type --allow-root
```

### Import Media
```bash
# Import single file
wp media import /path/to/image.jpg --allow-root

# Import and set as featured image for post
wp media import /path/to/image.jpg --post_id=123 --featured_image --allow-root
```

### Regenerate Thumbnails
```bash
# Regenerate all thumbnails
wp media regenerate --allow-root

# Regenerate specific image
wp media regenerate 123 --allow-root
```

---

## Maintenance Mode

### Enable/Disable Maintenance Mode
```bash
# Enable maintenance mode
wp maintenance-mode activate --allow-root

# Disable maintenance mode
wp maintenance-mode deactivate --allow-root

# Check status
wp maintenance-mode status --allow-root
```

### Manual Maintenance Mode
```bash
# Create .maintenance file
echo '<?php $upgrading = time(); ?>' > .maintenance

# Remove .maintenance file
rm .maintenance
```

---

## Config Commands

### Get Config Values
```bash
# Get config value
wp config get DB_NAME --allow-root
wp config get DB_USER --allow-root
wp config get DB_HOST --allow-root
wp config get table_prefix --allow-root
```

### Set Config Values
```bash
# Set config value
wp config set WP_DEBUG true --raw --allow-root

# Set constant
wp config set WP_MEMORY_LIMIT 256M --allow-root
```

### Shuffle Salts
```bash
# Regenerate security salts
wp config shuffle-salts --allow-root
```

---

## Useful Combinations

### Complete Backup
```bash
#!/bin/bash
# Complete WordPress backup

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/dave/rundaverun/backups/backup_${DATE}"

mkdir -p "$BACKUP_DIR"

# Export database
cd "/home/dave/Local Sites/rundaverun-local/app/public"
wp db export "$BACKUP_DIR/database.sql" --allow-root

# Copy wp-content
cp -r wp-content "$BACKUP_DIR/"

echo "✅ Backup complete: $BACKUP_DIR"
```

### Migrate Local to Production
```bash
#!/bin/bash
# Migrate from local to production

# 1. Export local database
cd "/home/dave/Local Sites/rundaverun-local/app/public"
wp db export migration.sql --allow-root

# 2. Search-replace URLs in export
wp search-replace 'http://rundaverun-local.local' 'https://rundaverun.org' \
  migration.sql --export=migration_production.sql --allow-root

# 3. On production: Import database
# wp db import migration_production.sql --allow-root

# 4. Verify URLs
# wp option get siteurl --allow-root
# wp option get home --allow-root

# 5. Clear cache
# wp cache flush --allow-root
```

### Debug Plugin Issues
```bash
#!/bin/bash
# Debug plugin causing issues

cd "/home/dave/Local Sites/rundaverun-local/app/public"

# 1. List active plugins
echo "Active plugins:"
wp plugin list --status=active --allow-root

# 2. Deactivate all plugins
echo "Deactivating all plugins..."
wp plugin deactivate --all --allow-root

# 3. Test if issue is resolved
# (Manually test site)

# 4. Reactivate plugins one by one to find culprit
echo "Reactivating plugins one by one..."
for plugin in $(wp plugin list --status=inactive --field=name --allow-root); do
    echo "Activating: $plugin"
    wp plugin activate "$plugin" --allow-root
    read -p "Test now. Issue occurs? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "❌ Problem plugin: $plugin"
        break
    fi
done
```

### Clean Up Spam/Trash
```bash
#!/bin/bash
# Clean up WordPress database

cd "/home/dave/Local Sites/rundaverun-local/app/public"

# Delete spam comments
wp comment delete $(wp comment list --status=spam --format=ids --allow-root) --force --allow-root

# Delete trash comments
wp comment delete $(wp comment list --status=trash --format=ids --allow-root) --force --allow-root

# Empty post trash
wp post delete $(wp post list --post_status=trash --format=ids --allow-root) --force --allow-root

# Optimize database
wp db optimize --allow-root

echo "✅ Cleanup complete"
```

---

## Troubleshooting

### "Error: YIKES! It looks like you're running this as root."
**Solution**: Add `--allow-root` flag
```bash
wp command --allow-root
```

### "Error: This does not seem to be a WordPress installation."
**Solution**: Change to WordPress directory first
```bash
cd "/home/dave/Local Sites/rundaverun-local/app/public"
wp command --allow-root
```

### "Error: Error establishing a database connection."
**Solution**: Check wp-config.php database credentials
```bash
wp config get DB_NAME --allow-root
wp config get DB_USER --allow-root
wp config get DB_PASSWORD --allow-root
wp config get DB_HOST --allow-root
```

### "Error: Could not find the plugin."
**Solution**: Check exact plugin name
```bash
# List all plugins to get exact name
wp plugin list --allow-root

# Use exact name (often different from display name)
wp plugin activate correct-plugin-slug --allow-root
```

---

## Output Formats

WP-CLI supports multiple output formats:

```bash
# Table (default)
wp plugin list --allow-root

# JSON
wp plugin list --format=json --allow-root

# CSV
wp plugin list --format=csv --allow-root

# YAML
wp plugin list --format=yaml --allow-root

# Count
wp plugin list --format=count --allow-root

# IDs only (useful for piping)
wp plugin list --format=ids --allow-root

# Specific fields
wp plugin list --fields=name,status --allow-root
```

---

## Helpful Flags

### Common Flags
```bash
--allow-root              # Required on Local by Flywheel
--path=/path/to/wordpress # Specify WordPress path
--url=https://example.com # Specify site URL (for multisite)
--quiet                   # Suppress informational messages
--debug                   # Show debug output
--help                    # Show help for command
```

### Database Operation Flags
```bash
--dry-run                 # Show what would be done (no changes)
--all-tables              # Include all tables (search-replace)
--skip-columns=column     # Skip specific columns
--format=json             # Output format
--yes                     # Answer yes to all prompts
```

---

## Quick Reference Card

### Most Common Commands
```bash
# Database
wp db export backup.sql --allow-root
wp db import backup.sql --allow-root
wp search-replace 'old' 'new' --all-tables --allow-root

# Plugins
wp plugin list --allow-root
wp plugin activate plugin-name --allow-root
wp plugin deactivate --all --allow-root

# Cache
wp cache flush --allow-root
wp rewrite flush --allow-root

# Posts
wp post list --allow-root
wp post get 123 --allow-root

# Options
wp option get siteurl --allow-root
wp option update siteurl 'https://example.com' --allow-root

# Core
wp core version --allow-root
wp core verify-checksums --allow-root
```

---

**Reference**: [WP-CLI Official Documentation](https://wp-cli.org/)
**Local Path**: `/home/dave/Local Sites/rundaverun-local/app/public`
**Production**: GoDaddy Managed WordPress (custom prefix: `wp_7e1ce15f22_`)
