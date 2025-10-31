# Package Creation Protocol

**Date Created**: 2025-10-28
**Purpose**: Standardized procedures for creating distribution packages
**Applies To**: All packages (glossary, documentation, scripts, releases)
**Priority**: MEDIUM-HIGH (done frequently, quality matters)

## Overview

This protocol standardizes how to create packages for distribution, whether uploading to claude.ai, sharing with stakeholders, or releasing versions. Following these standards ensures packages are complete, well-documented, and easy to use.

## Package Types

### 1. Documentation Packages (Glossary, Policies)
### 2. Script/Tool Packages
### 3. Upload Packages (for claude.ai)
### 4. Release Packages (public distribution)
### 5. Backup Packages

---

## Universal Package Requirements

Every package MUST include:

### 1. Version Number
- Use semantic versioning: `v1.0.0`
- Format: `package_name_v{major}.{minor}.{patch}.{ext}`

### 2. README File
- Always include `readme.md` or `readme.txt`
- Explain what's in the package
- Provide usage instructions
- List requirements/dependencies

### 3. Complete Package Structure
- All necessary files included
- No missing dependencies
- No broken links/references
- Tested before distribution

### 4. Proper Naming
- Lowercase with underscores
- Descriptive name
- Include version
- Include date if relevant

### 5. File Organization
- Logical directory structure
- Related files grouped together
- Clear file naming
- Remove unnecessary files

---

## Documentation Package Protocol

**Examples**: Glossary, policy documents, voter education materials

### Pre-Creation Checklist

#### Content Complete
- [ ] All documents finalized
- [ ] Proofreading completed
- [ ] Links verified (all working)
- [ ] Images included and optimized
- [ ] Version numbers updated
- [ ] Date stamps current

#### Technical Validation
```bash
# For HTML files
# Check for broken links
grep -r "href=" *.html | grep -v "^#" | cut -d'"' -f2 | sort -u > links.txt

# Validate HTML (if validator available)
# Check file sizes (optimize if needed)
ls -lh *.html *.css *.js
```

- [ ] HTML validates (no major errors)
- [ ] CSS loads correctly
- [ ] JavaScript works (no console errors)
- [ ] Mobile responsive
- [ ] Browser tested (Chrome, Firefox)

#### Accessibility Check
- [ ] Images have alt text
- [ ] Headings properly structured (h1 → h2 → h3)
- [ ] Links are descriptive
- [ ] Color contrast sufficient
- [ ] Text readable (minimum 16px)

### Package Structure

```
louisville_voter_glossary_v4.0/
├── readme.md                          # Package overview and usage
├── glossary_v4.0.html                 # Main HTML file
├── glossary_v4.0_print.html          # Print version (if applicable)
├── assets/                            # Supporting files
│   ├── css/
│   │   └── glossary_styles.css
│   ├── js/
│   │   └── glossary_search.js
│   └── images/
│       └── logo.png
├── documentation/                     # Documentation
│   ├── usage_guide.md
│   ├── installation_instructions.md
│   └── version_history.md
└── source/                            # Source files (optional)
    ├── glossary_terms.csv
    └── generation_script.py
```

### README Template (Documentation Package)

```markdown
# Louisville Voter Education Glossary v4.0

**Date**: 2025-10-28
**Version**: 4.0.0
**Total Terms**: 499
**Purpose**: Comprehensive voter education resource for Louisville, Kentucky

## Contents

- `glossary_v4.0.html` - Main interactive glossary (52KB)
- `glossary_v4.0_print.html` - Print-friendly version (48KB)
- `assets/` - CSS, JavaScript, images
- `documentation/` - Usage guides and version history
- `source/` - Source data files

## Usage

### Viewing Locally
1. Extract the ZIP file
2. Open `glossary_v4.0.html` in any modern web browser
3. Use search box to find terms
4. Click terms to see definitions

### Deploying to Website
1. Upload all files maintaining directory structure
2. Link to `glossary_v4.0.html` from your site
3. Or embed using iframe:
   ```html
   <iframe src="glossary_v4.0.html" width="100%" height="800px"></iframe>
   ```

### Printing
1. Open `glossary_v4.0_print.html`
2. Print from browser (Ctrl+P)
3. Recommended: Use "Save as PDF" option

## Requirements

- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)
- JavaScript enabled
- No server required (runs entirely in browser)

## Version History

### v4.0.0 (2025-10-28)
- Added 50 new terms (449 → 499)
- Improved mobile layout
- Added quick navigation menu
- Enhanced search functionality

### v3.0.0 (2025-10-15)
- Initial comprehensive glossary
- 449 terms covering 8 categories
- Mobile-responsive design

## Support

For questions or issues:
- Email: contact@rundaverun.org
- Website: https://rundaverun.org/glossary

## License

© 2025 Dave Biggers for Mayor Campaign
Educational use permitted with attribution.
```

### Creation Steps

```bash
# 1. Create package directory
PACKAGE_NAME="louisville_voter_glossary_v4.0"
PACKAGE_DIR="/home/dave/skippy/claude/uploads/$PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR"/{assets/{css,js,images},documentation,source}

# 2. Copy files to package
cp glossary_v4.0.html "$PACKAGE_DIR/"
cp glossary_styles.css "$PACKAGE_DIR/assets/css/"
cp glossary_search.js "$PACKAGE_DIR/assets/js/"

# 3. Create README
cat > "$PACKAGE_DIR/readme.md" <<'EOF'
[README content as above]
EOF

# 4. Create documentation
cat > "$PACKAGE_DIR/documentation/usage_guide.md" <<'EOF'
[Usage guide content]
EOF

# 5. Verify package completeness
cd "$PACKAGE_DIR"
tree -L 3
ls -lh

# 6. Test HTML files
# Open in browser to verify everything works

# 7. Create ZIP archive
cd /home/dave/skippy/claude/uploads/
zip -r "${PACKAGE_NAME}.zip" "$PACKAGE_NAME/"

# 8. Verify ZIP
unzip -l "${PACKAGE_NAME}.zip" | head -20
```

### Quality Checklist

- [ ] All files present in package
- [ ] README complete and accurate
- [ ] Version number consistent throughout
- [ ] All links work (no broken references)
- [ ] Images display correctly
- [ ] ZIP extracts without errors
- [ ] File sizes reasonable (optimized)
- [ ] Tested on clean system (as end user would use it)

---

## Script/Tool Package Protocol

**Examples**: Automation scripts, utilities, development tools

### Pre-Creation Checklist

#### Script Validation
- [ ] Script tested and working
- [ ] Error handling implemented
- [ ] Version number updated
- [ ] Documentation header complete
- [ ] Usage instructions clear
- [ ] Dependencies documented

#### Code Quality
```bash
# Check for common issues
grep -n "TODO" *.sh *.py
grep -n "FIXME" *.sh *.py
grep -n "XXX" *.sh *.py

# Check for hardcoded paths that should be variables
grep -n "/home/dave" *.sh | grep -v "# Example"

# Verify all scripts have proper shebangs
head -1 *.sh *.py
```

- [ ] No TODO/FIXME in production code
- [ ] No hardcoded credentials
- [ ] No hardcoded paths (use variables)
- [ ] Proper shebangs (#!/bin/bash, #!/usr/bin/env python3)
- [ ] Executable permissions set

### Package Structure

```
wordpress_backup_toolkit_v1.0/
├── readme.md                          # Package overview
├── scripts/
│   ├── backup_wordpress.sh            # Main scripts
│   ├── restore_wordpress.sh
│   ├── migrate_wordpress.sh
│   └── verify_backup.sh
├── config/
│   ├── config.example.sh              # Example configuration
│   └── config_template.sh
├── documentation/
│   ├── installation.md                # Setup instructions
│   ├── usage_guide.md                 # How to use
│   ├── troubleshooting.md             # Common issues
│   └── api_reference.md               # If applicable
├── tests/                             # Optional
│   ├── test_backup.sh
│   └── test_restore.sh
└── examples/                          # Optional
    ├── basic_backup.sh
    └── advanced_migration.sh
```

### README Template (Script Package)

```markdown
# WordPress Backup Toolkit v1.0

**Date**: 2025-10-28
**Version**: 1.0.0
**Purpose**: Complete WordPress backup and migration toolkit

## Features

- ✅ Full WordPress backup (database + files)
- ✅ Selective backup (database only, files only)
- ✅ Automated restoration
- ✅ Migration between environments
- ✅ Backup verification
- ✅ Compression and archiving

## Requirements

- Bash 4.0+
- WP-CLI installed
- MySQL client
- zip/unzip utilities
- Sufficient disk space for backups

## Installation

### Quick Install
```bash
cd /home/dave/skippy/scripts/wordpress/
cp wordpress_backup_toolkit_v1.0/scripts/*.sh .
chmod +x *.sh
cp wordpress_backup_toolkit_v1.0/config/config.example.sh config.sh
# Edit config.sh with your settings
```

### Detailed Setup
See `documentation/installation.md`

## Usage

### Basic Backup
```bash
./backup_wordpress.sh --site rundaverun-local
```

### Restore Backup
```bash
./restore_wordpress.sh --backup /path/to/backup.zip
```

### Migrate Site
```bash
./migrate_wordpress.sh \
  --source rundaverun-local \
  --dest production \
  --url-replace "rundaverun-local.local" "rundaverun.org"
```

### Full Documentation
See `documentation/usage_guide.md`

## Configuration

Edit `config.sh`:
```bash
# WordPress installations
LOCAL_WP_PATH="/home/dave/Local Sites/rundaverun-local/app/public"
PROD_WP_PATH="/var/www/html"

# Backup location
BACKUP_DIR="/home/dave/rundaverun/backups"

# WP-CLI flags
WPCLI_FLAGS="--allow-root"
```

## Troubleshooting

**Issue**: "WP-CLI not found"
**Solution**: Install WP-CLI or update WPCLI_PATH in config.sh

**Issue**: "Permission denied"
**Solution**: Ensure scripts have executable permissions (chmod +x)

See `documentation/troubleshooting.md` for more.

## Version History

### v1.0.0 (2025-10-28)
- Initial release
- Core backup/restore functionality
- Migration support
- Verification system

## License

© 2025 - GPL-3.0

## Support

Issues: https://github.com/username/repo/issues
Docs: https://docs.example.com
```

### Creation Steps

```bash
# 1. Create package directory
PACKAGE_NAME="wordpress_backup_toolkit_v1.0"
PACKAGE_DIR="/home/dave/skippy/claude/uploads/$PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR"/{scripts,config,documentation,tests,examples}

# 2. Copy scripts
cp backup_wordpress_v*.sh "$PACKAGE_DIR/scripts/"
cp restore_wordpress_v*.sh "$PACKAGE_DIR/scripts/"

# 3. Create config template
cat > "$PACKAGE_DIR/config/config.example.sh" <<'EOF'
#!/bin/bash
# Configuration template
# Copy to config.sh and customize

# WordPress paths
LOCAL_WP_PATH="/home/dave/Local Sites/rundaverun-local/app/public"
PROD_WP_PATH="/var/www/html"

# Backup directory
BACKUP_DIR="/home/dave/rundaverun/backups"

# WP-CLI
WPCLI_PATH="wp"
WPCLI_FLAGS="--allow-root"
EOF

# 4. Create documentation
cat > "$PACKAGE_DIR/documentation/installation.md" <<'EOF'
[Installation instructions]
EOF

# 5. Set permissions
chmod +x "$PACKAGE_DIR/scripts/"*.sh

# 6. Verify scripts work
cd "$PACKAGE_DIR/scripts"
bash -n *.sh  # Syntax check

# 7. Create README
cat > "$PACKAGE_DIR/readme.md" <<'EOF'
[README content as above]
EOF

# 8. Create package
cd /home/dave/skippy/claude/uploads/
zip -r "${PACKAGE_NAME}.zip" "$PACKAGE_NAME/"

# 9. Verify
unzip -l "${PACKAGE_NAME}.zip"
```

### Quality Checklist

- [ ] All scripts included
- [ ] Config template provided (no sensitive data)
- [ ] Documentation complete
- [ ] Examples provided
- [ ] Scripts tested
- [ ] Permissions correct (executable)
- [ ] No hardcoded paths/credentials
- [ ] Dependencies documented
- [ ] Version consistent throughout

---

## Upload Package Protocol (for claude.ai)

**Purpose**: Packages to upload to claude.ai for context/analysis

### Special Considerations

Claude.ai has limitations:
- File size limits (check current limits)
- Prefers text-readable formats
- Can handle: .txt, .md, .html, .css, .js, .py, .sh, .json, .xml
- Cannot process: .exe, .bin, large images

### Package Structure

```
rundaverun_wordpress_context_v1.0/
├── readme.md                          # What's in this package
├── site_overview.md                   # High-level site description
├── theme/                             # Theme files
│   ├── functions.php
│   ├── header.php
│   ├── footer.php
│   └── style.css
├── plugins/                           # Custom plugins
│   └── mobile-menu-injector.php
├── content/                           # Content samples
│   ├── sample_pages.md
│   └── policy_list.md
├── configuration/                     # Config files
│   ├── wp-config-sample.php          # Sanitized (no credentials)
│   └── nginx.conf                     # Or apache config
└── documentation/                     # Project docs
    ├── development_workflow.md
    └── deployment_process.md
```

### README Template (Upload Package)

```markdown
# RunDaveRun WordPress Context Package v1.0

**Date**: 2025-10-28
**Version**: 1.0.0
**Purpose**: Context package for Claude.ai to understand RunDaveRun WordPress site

## Contents Overview

### Site Information
- **Type**: WordPress political campaign site
- **Purpose**: Dave Biggers for Louisville Mayor campaign
- **Environment**: Local by Flywheel (local), GoDaddy Managed WordPress (production)
- **WordPress Version**: 6.3.2
- **PHP Version**: 8.1

### Package Contents

1. **site_overview.md** - High-level description of site purpose, structure, features
2. **theme/** - Custom theme files (campaign theme)
3. **plugins/** - Custom plugins (mobile-menu-injector)
4. **content/** - Sample content and policy documents
5. **configuration/** - Config files (sanitized, no credentials)
6. **documentation/** - Development and deployment docs

### Key Features

- Custom glossary system (499 terms)
- Policy document library (31 policies)
- Mobile-responsive design
- Custom mobile menu injector
- Voter education hub

### Important Notes

#### GoDaddy-Specific
- Custom table prefix: `wp_7e1ce15f22_`
- Managed WordPress (limited server access)
- Deployment via GitHub Actions

#### Local Development
- Uses Local by Flywheel
- Requires `--allow-root` flag for WP-CLI
- Local URL: `http://rundaverun-local.local`
- Production URL: `https://rundaverun.org`

### How to Use This Package

**With Claude.ai**:
1. Upload ZIP to Claude conversation
2. Ask Claude to review specific files
3. Reference this context for questions about:
   - Site structure
   - Deployment process
   - Troubleshooting issues
   - Feature implementation

**Example Prompts**:
- "Review the mobile menu injector and suggest improvements"
- "How should I deploy changes to production?"
- "What's the best way to add a new policy document?"

### What's NOT Included

- Database dumps (too large)
- Credentials (security)
- Backup files
- wp-content/uploads (media files)
- Third-party plugins (only custom code)

### Related Documentation

- Deployment: See `documentation/deployment_process.md`
- WordPress protocols: `/home/dave/skippy/conversations/wordpress_maintenance_protocol.md`
- Backup strategy: `/home/dave/skippy/conversations/backup_strategy_protocol.md`

## Questions This Package Can Help Answer

- How is the glossary system implemented?
- What's the deployment workflow?
- How does the mobile menu work?
- What's the site structure?
- How are policies organized?
- What customizations exist?

## Support Files

If Claude needs additional context not in this package:
- Database schema: Available separately
- Full theme: Available in Git repo
- Backup files: Located in `/home/dave/rundaverun/backups/`
```

### Creation Steps

```bash
# 1. Create package directory
PACKAGE_NAME="rundaverun_wordpress_context_v1.0"
PACKAGE_DIR="/home/dave/skippy/claude/uploads/$PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR"/{theme,plugins,content,configuration,documentation}

# 2. Copy relevant files (SANITIZED - no credentials!)
# Theme
cp "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/themes/campaign/"*.php \
   "$PACKAGE_DIR/theme/" 2>/dev/null

# Custom plugins
cp "/home/dave/Local Sites/rundaverun-local/app/public/wp-content/mu-plugins/"*.php \
   "$PACKAGE_DIR/plugins/" 2>/dev/null

# 3. Create site overview
cat > "$PACKAGE_DIR/site_overview.md" <<'EOF'
# RunDaveRun Site Overview

## Purpose
Political campaign website for Dave Biggers running for Louisville Mayor

## Key Features
1. Policy library (31 comprehensive policies)
2. Voter education glossary (499 terms)
3. Mobile-responsive design
4. Contact forms
5. Endorsements section

## Technology Stack
- WordPress 6.3.2
- Custom theme (campaign)
- PHP 8.1
- MySQL database
- GoDaddy Managed WordPress (production)
- Local by Flywheel (development)
EOF

# 4. Create README
cat > "$PACKAGE_DIR/readme.md" <<'EOF'
[README content as above]
EOF

# 5. Copy documentation
cp /home/dave/skippy/conversations/wordpress_maintenance_protocol.md \
   "$PACKAGE_DIR/documentation/"

# 6. Sanitize any files with credentials
grep -r "password" "$PACKAGE_DIR/" && echo "⚠️ WARNING: Found 'password' in files!"
grep -r "secret" "$PACKAGE_DIR/" && echo "⚠️ WARNING: Found 'secret' in files!"

# 7. Check package size (Claude has limits)
du -sh "$PACKAGE_DIR"

# 8. Create ZIP
cd /home/dave/skippy/claude/uploads/
zip -r "${PACKAGE_NAME}.zip" "$PACKAGE_NAME/"

# 9. Verify size
ls -lh "${PACKAGE_NAME}.zip"
```

### Quality Checklist (Upload Package)

- [ ] README explains package purpose
- [ ] No credentials or secrets included
- [ ] File size within Claude limits
- [ ] Text-readable formats preferred
- [ ] Context is clear and complete
- [ ] Examples provided
- [ ] Documentation included
- [ ] ZIP extracts cleanly

---

## Release Package Protocol

**Purpose**: Public releases, version distributions

### Pre-Release Checklist

#### Version Management
- [ ] Version number incremented appropriately
- [ ] Version number consistent across all files
- [ ] CHANGELOG.md updated
- [ ] Release notes drafted

#### Quality Assurance
- [ ] All tests passing
- [ ] No known critical bugs
- [ ] Performance acceptable
- [ ] Security reviewed
- [ ] Dependencies updated

#### Documentation
- [ ] README accurate and complete
- [ ] Installation instructions tested
- [ ] API documentation current (if applicable)
- [ ] Examples work
- [ ] Troubleshooting guide updated

#### Legal/Licensing
- [ ] License file included (LICENSE.md)
- [ ] Copyright notices present
- [ ] Third-party licenses acknowledged
- [ ] Terms of use clear

### Package Structure

```
project_name_v1.0.0/
├── readme.md                          # Overview
├── license.md                         # License terms
├── changelog.md                       # Version history
├── install.md                         # Installation guide
├── src/                               # Source code
│   └── [application files]
├── docs/                              # Documentation
│   ├── user_guide.md
│   ├── api_reference.md
│   └── troubleshooting.md
├── examples/                          # Usage examples
│   ├── basic_usage.sh
│   └── advanced_usage.sh
├── tests/                             # Test suite
│   └── [test files]
└── dist/                              # Compiled/built files
    └── [distribution files]
```

### CHANGELOG Template

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-28

### Added
- Initial release
- Core backup functionality
- WordPress integration
- Automated restoration

### Changed
- N/A (initial release)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.9.0] - 2025-10-15

### Added
- Beta release for testing
- Core functionality implemented

### Known Issues
- Performance optimization needed
- Documentation incomplete
```

### Creation Steps

```bash
# 1. Prepare release
VERSION="1.0.0"
PROJECT_NAME="wordpress_backup_toolkit"
PACKAGE_NAME="${PROJECT_NAME}_v${VERSION}"
RELEASE_DIR="/home/dave/releases/$PACKAGE_NAME"

# 2. Clean build
mkdir -p "$RELEASE_DIR"/{src,docs,examples,tests,dist}

# 3. Copy source files
cp -r /home/dave/skippy/scripts/wordpress/ "$RELEASE_DIR/src/"

# 4. Build/compile if necessary
# (For compiled languages)

# 5. Copy documentation
cp readme.md license.md changelog.md install.md "$RELEASE_DIR/"
cp -r documentation/* "$RELEASE_DIR/docs/"

# 6. Run final tests
cd "$RELEASE_DIR/tests"
./run_all_tests.sh

# 7. Create distribution archives
cd /home/dave/releases/
# ZIP for Windows users
zip -r "${PACKAGE_NAME}.zip" "$PACKAGE_NAME/"
# TAR.GZ for Linux users
tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME/"

# 8. Generate checksums
sha256sum "${PACKAGE_NAME}.zip" > "${PACKAGE_NAME}.zip.sha256"
sha256sum "${PACKAGE_NAME}.tar.gz" > "${PACKAGE_NAME}.tar.gz.sha256"

# 9. Create release notes
cat > "${PACKAGE_NAME}_release_notes.md" <<'EOF'
# WordPress Backup Toolkit v1.0.0 Release Notes

**Release Date**: 2025-10-28
**Type**: Major release

## Highlights
- First stable release
- Complete backup/restore functionality
- WordPress migration support

## Downloads
- [ZIP](wordpress_backup_toolkit_v1.0.0.zip) (Windows)
- [TAR.GZ](wordpress_backup_toolkit_v1.0.0.tar.gz) (Linux/Mac)

## Checksums (SHA256)
See .sha256 files

## Installation
See INSTALL.md

## Requirements
- Bash 4.0+
- WP-CLI
- MySQL client

## Known Issues
None

## Future Plans (v1.1.0)
- Scheduled backups
- Cloud storage integration
- Email notifications
EOF
```

### Quality Checklist (Release Package)

- [ ] Version number incremented
- [ ] CHANGELOG updated
- [ ] All tests passing
- [ ] Documentation complete
- [ ] License included
- [ ] No debug code
- [ ] No hardcoded credentials
- [ ] Multiple archive formats (zip, tar.gz)
- [ ] Checksums generated
- [ ] Release notes written
- [ ] Tagged in git (if using git)

---

## Backup Package Protocol

**Purpose**: System backups, disaster recovery

### Package Structure

```
backup_2025-10-28_1430_pre_deployment/
├── readme.md                          # What's backed up, how to restore
├── metadata.json                      # Backup metadata
├── database/
│   ├── wordpress_db.sql               # Database dump
│   └── database_info.txt              # DB details
├── files/
│   ├── wp-content/                    # WordPress files
│   └── custom_code/                   # Custom files
├── configuration/
│   ├── wp-config.php
│   ├── .htaccess
│   └── server_config/
├── logs/
│   ├── backup_log.txt                 # Backup process log
│   └── file_manifest.txt              # List of all files
└── verification/
    ├── checksums.md5                  # File checksums
    └── directory_structure.txt        # Directory tree
```

### Metadata Template

```json
{
  "backup_date": "2025-10-28T14:30:00Z",
  "backup_type": "pre_deployment",
  "backup_version": "1.0",
  "source": {
    "environment": "production",
    "site_url": "https://rundaverun.org",
    "wordpress_version": "6.3.2",
    "php_version": "8.1",
    "database_version": "MySQL 8.0"
  },
  "contents": {
    "database": true,
    "files": true,
    "configuration": true,
    "uploads": false
  },
  "size": {
    "database_mb": 15.2,
    "files_mb": 120.5,
    "total_mb": 135.7
  },
  "restore_instructions": "See readme.md",
  "created_by": "Claude Code",
  "retention": "30 days minimum"
}
```

### README Template (Backup Package)

```markdown
# Backup: Pre-Deployment 2025-10-28

**Date**: 2025-10-28 14:30
**Type**: Pre-deployment backup
**Purpose**: Safety backup before deployment of policy updates

## Contents

- ✅ Database (wordpress_db.sql - 15.2 MB)
- ✅ WordPress files (wp-content - 120.5 MB)
- ✅ Configuration (wp-config.php, .htaccess)
- ❌ Media files (not included - too large)

## System State

### WordPress
- Version: 6.3.2
- Site URL: https://rundaverun.org
- Table Prefix: wp_7e1ce15f22_

### Database
- Size: 15.2 MB
- Tables: 25
- Last modified: 2025-10-28 14:25

### Files
- Theme: campaign (custom)
- Plugins: 12 active
- Custom code: mobile-menu-injector.php

## Restoration Instructions

### Full Restore

```bash
# 1. Enable maintenance mode
wp maintenance-mode activate --allow-root

# 2. Restore database
wp db reset --yes --allow-root
wp db import database/wordpress_db.sql --allow-root

# 3. Restore files
rsync -av files/wp-content/ /var/www/html/wp-content/

# 4. Restore configuration
cp configuration/wp-config.php /var/www/html/
cp configuration/.htaccess /var/www/html/

# 5. Verify
wp db check --allow-root
wp core verify-checksums --allow-root

# 6. Disable maintenance mode
wp maintenance-mode deactivate --allow-root
```

### Selective Restore

**Database Only**:
```bash
wp db import database/wordpress_db.sql --allow-root
```

**Specific Files**:
```bash
rsync -av files/wp-content/themes/campaign/ /var/www/html/wp-content/themes/campaign/
```

## Verification

### Checksums
MD5 checksums available in: `verification/checksums.md5`

```bash
cd files/
md5sum -c ../verification/checksums.md5
```

### File List
Complete file manifest: `logs/file_manifest.txt`

## Retention

**Keep Until**: 2025-11-28 (30 days minimum)
**Can Delete After**: Verify new deployment successful for 30+ days

## Notes

- Created automatically by deployment script
- Database credentials NOT included (security)
- Media files excluded (available in separate backup)
- Tested restoration procedure: ✅ Verified working
```

### Creation Script

```bash
#!/bin/bash
# Create backup package

# Configuration
BACKUP_DATE=$(date +%Y-%m-%d_%H%M)
BACKUP_NAME="backup_${BACKUP_DATE}_pre_deployment"
BACKUP_DIR="/home/dave/rundaverun/backups/$BACKUP_NAME"
WP_PATH="/var/www/html"

# Create structure
mkdir -p "$BACKUP_DIR"/{database,files,configuration,logs,verification}

# Backup database
echo "Backing up database..."
wp db export "$BACKUP_DIR/database/wordpress_db.sql" --allow-root

# Backup files
echo "Backing up files..."
rsync -av --exclude="uploads/" "$WP_PATH/wp-content" "$BACKUP_DIR/files/"

# Backup configuration
echo "Backing up configuration..."
cp "$WP_PATH/wp-config.php" "$BACKUP_DIR/configuration/"
cp "$WP_PATH/.htaccess" "$BACKUP_DIR/configuration/"

# Generate checksums
echo "Generating checksums..."
cd "$BACKUP_DIR/files"
find . -type f -exec md5sum {} \; > "../verification/checksums.md5"

# Create file manifest
echo "Creating file manifest..."
find "$BACKUP_DIR/files" -type f > "$BACKUP_DIR/logs/file_manifest.txt"

# Create directory structure
echo "Creating directory structure..."
tree -L 4 "$BACKUP_DIR" > "$BACKUP_DIR/verification/directory_structure.txt"

# Create metadata
cat > "$BACKUP_DIR/metadata.json" <<EOF
{
  "backup_date": "$(date -Iseconds)",
  "backup_type": "pre_deployment",
  "backup_version": "1.0",
  "source": {
    "environment": "production",
    "site_url": "https://rundaverun.org"
  }
}
EOF

# Create README
cat > "$BACKUP_DIR/readme.md" <<'EOF'
[README content as above]
EOF

# Create backup log
cat > "$BACKUP_DIR/logs/backup_log.txt" <<EOF
Backup Log
==========
Date: $(date)
Status: SUCCESS

Steps:
1. Database backup: ✅
2. Files backup: ✅
3. Configuration backup: ✅
4. Checksums generated: ✅
5. Manifest created: ✅
6. Metadata created: ✅

Total size: $(du -sh "$BACKUP_DIR" | cut -f1)
EOF

echo "✅ Backup complete: $BACKUP_DIR"
```

---

## Integration with Other Protocols

### With Script Saving Protocol
Reference: `/home/dave/skippy/conversations/script_saving_protocol.md`
- Package creation scripts saved to `/home/dave/skippy/scripts/utility/`
- Use version numbers consistently
- Document script purpose

### With Deployment Checklist Protocol
Reference: `/home/dave/skippy/conversations/deployment_checklist_protocol.md`
- Create backup package before deployment
- Include backup verification in deployment checklist
- Document backup location in deployment log

### With Error Logging Protocol
Reference: `/home/dave/skippy/conversations/error_logging_protocol.md`
- Log packaging errors
- Document solutions
- Update protocol if issues found

### With Documentation Standards Protocol
Reference: `/home/dave/skippy/conversations/documentation_standards_protocol.md`
- Follow documentation standards for README files
- Use consistent formatting
- Include all required sections

---

## Quick Reference

### Package Checklist (Universal)
- [ ] Version number (semantic versioning)
- [ ] README included
- [ ] All files present
- [ ] Dependencies documented
- [ ] Tested before distribution
- [ ] Proper naming (lowercase, underscores)
- [ ] No credentials/secrets
- [ ] File organization logical

### Common Package Locations
```bash
# Upload packages (for claude.ai)
/home/dave/skippy/claude/uploads/

# Release packages
/home/dave/releases/

# Backup packages
/home/dave/rundaverun/backups/
/home/dave/skippy/backups/

# Documentation packages
/home/dave/rundaverun/campaign/
```

### Package Creation Commands
```bash
# Create ZIP
zip -r package_name.zip package_directory/

# Create TAR.GZ
tar -czf package_name.tar.gz package_directory/

# Generate checksums
sha256sum package_name.zip > package_name.zip.sha256

# Verify archive
unzip -t package_name.zip
tar -tzf package_name.tar.gz

# Check size
du -sh package_name.zip
ls -lh package_name.zip
```

---

**This protocol is part of the persistent memory system.**
**Reference when creating any package for distribution or backup.**
