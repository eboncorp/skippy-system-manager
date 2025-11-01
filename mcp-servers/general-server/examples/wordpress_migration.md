# WordPress Migration Workflow

**Use Case**: Migrating WordPress site from local to production or vice versa

**Tools Used**: wordpress_quick_backup, wp_db_export, wp_search_replace, wp_get_posts

---

## Scenario 1: Local to Production Migration

### Step 1: Backup Current Production Site

```
Create a WordPress backup of the production site before making changes
```

**What happens**:
- Creates full backup in `/home/dave/RunDaveRun/backups/full_backup_TIMESTAMP/`
- Includes database export + wp-content files
- Safe to proceed if this succeeds

### Step 2: Export Local Database

```
Export the WordPress database to prepare for migration
```

**What happens**:
- Creates SQL dump in `/home/dave/RunDaveRun/backups/`
- Timestamped: `wp_db_backup_YYYYMMDD_HHMMSS.sql`

### Step 3: Test URL Replacement (Dry-Run)

```
Search and replace localhost URLs with production URLs in dry-run mode:
- Search for: http://localhost:8080/rundaverun
- Replace with: https://rundaverun.com
- Dry run: true
```

**What happens**:
- Shows WHAT WOULD be replaced without actually changing anything
- Review the results carefully
- Check for unexpected matches

### Step 4: Apply URL Replacement (If Safe)

```
Apply the URL replacement:
- Search for: http://localhost:8080/rundaverun
- Replace with: https://rundaverun.com
- Dry run: false
```

**What happens**:
- Actually replaces URLs in database
- Irreversible (unless you restore from backup)

### Step 5: Verify Changes

```
List recent posts to verify URLs look correct
```

**What happens**:
- Shows post URLs and content
- Verify URLs are now using production domain

---

## Scenario 2: Production to Local Migration

### Step 1: Download Production Database

(Manual step - use hosting control panel or SSH to get database dump)

### Step 2: Import to Local WordPress

```bash
# Manual command in terminal
wp --path=/home/dave/RunDaveRun --allow-root db import production_backup.sql
```

### Step 3: Replace Production URLs with Local (Dry-Run)

```
Test URL replacement from production to local:
- Search for: https://rundaverun.com
- Replace with: http://localhost:8080/rundaverun
- Dry run: true
```

### Step 4: Apply URL Replacement

```
Apply the URL replacement from production to local:
- Search for: https://rundaverun.com
- Replace with: http://localhost:8080/rundaverun
- Dry run: false
```

### Step 5: Verify Local Site Works

```
List all published posts to verify they're accessible
```

---

## Common Migration Tasks

### Check Current Site URL

```
Run WP-CLI command: option get siteurl
```

### Check Home URL

```
Run WP-CLI command: option get home
```

### List All Posts Before Migration

```
Get published posts to document what exists before migration
```

### Verify Database After Migration

```
Execute safe MySQL query:
SELECT option_name, option_value FROM wp_options WHERE option_name LIKE '%url%'
```

---

## Safety Checklist

Before starting migration:
- [ ] Full backup created of source site
- [ ] Full backup created of destination site (if overwriting)
- [ ] Database export successful
- [ ] Tested search-replace with dry-run first
- [ ] Verified no unexpected matches in dry-run results

After migration:
- [ ] Site URL is correct
- [ ] Home URL is correct
- [ ] Posts load correctly
- [ ] Images load correctly (check wp-content paths)
- [ ] Admin panel accessible
- [ ] Permalinks working

---

## Troubleshooting

### URLs Still Wrong After Search-Replace

**Problem**: Some URLs didn't get replaced

**Solution**: WordPress serializes some data, need multiple passes
```
Run search-replace again with different patterns:
- Try with/without trailing slashes
- Check for escaped URLs (https:\/\/rundaverun.com)
```

### Images Not Loading

**Problem**: Image paths wrong after migration

**Solution**: Check wp-content is synchronized
```
Verify wp-content files were copied:
- Check /home/dave/RunDaveRun/wp-content/uploads/ exists
- Compare file counts between source and destination
```

### Database Import Fails

**Problem**: SQL import has errors

**Solution**: Check WordPress version compatibility
```
Run WP-CLI command: core version
```

Ensure source and destination WordPress versions match.

---

## Natural Language Examples

**Full migration workflow**:
```
1. "Create a complete WordPress backup"
2. "Export the WordPress database"
3. "Test replacing http://localhost:8080/rundaverun with https://rundaverun.com in dry-run mode"
4. "Now apply that URL replacement for real (dry_run=false)"
5. "List all published posts to verify the changes"
6. "Check the siteurl option in the database"
```

**Quick backup before risky operation**:
```
"Create a WordPress database backup before I make changes"
```

**Verify migration success**:
```
"Show me the first 20 published posts and verify their URLs"
```

---

**Related Tools**:
- `wordpress_quick_backup` - Full site backup
- `wp_db_export` - Database only backup
- `wp_search_replace` - URL replacement
- `wp_get_posts` - Verify posts after migration
- `mysql_query_safe` - Check database settings
- `wp_cli_command` - Any custom WP-CLI command

**Related Protocols**:
- WordPress Maintenance Protocol
- Pre-Commit Sanitization Protocol (if migrating code)
