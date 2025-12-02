# Configuration Variables Protocol

**Protocol Version**: 1.0.0
**Date Created**: 2025-10-28
**Purpose**: Centralized configuration for protocol system portability
**Applies To**: All protocols in the system

---

## Purpose

This protocol defines configuration variables used throughout the protocol system, enabling easy adaptation to different:
- Projects
- Users
- Hosting environments
- Local development setups

By centralizing these values, the entire protocol system can be adapted to new contexts by updating this single file.

---

## Variable Categories

### Project Variables

```yaml
PROJECT_NAME: rundaverun
PROJECT_DESCRIPTION: Mayoral campaign website
PROJECT_DOMAIN: rundaverun.org
PROJECT_DOMAIN_WWW: www.rundaverun.org
LOCAL_DOMAIN: rundaverun-local.local
PROJECT_OWNER: Dave Biggers
PROJECT_TYPE: WordPress (political campaign)
```

**Usage**: Referenced when discussing project-specific operations

---

### Path Variables

```yaml
# User Paths
USER_HOME: /home/dave
USER_NAME: dave

# Project Structure
PROJECT_ROOT: /home/dave/skippy
SCRIPTS_DIR: /home/dave/skippy/scripts
CONVERSATIONS_DIR: /home/dave/skippy/conversations
BACKUPS_DIR: /home/dave/skippy/backups
DOCUMENTATION_DIR: /home/dave/skippy/documentation

# Claude Code Integration
CLAUDE_CONFIG: /home/dave/.claude/claude.md
PROTOCOL_INSTALL_PATH: /home/dave/skippy/conversations/

# WordPress Local
LOCAL_WP_ROOT: /Users/dave/Local Sites/rundaverun-local/app/public
LOCAL_WP_CONFIG: /Users/dave/Local Sites/rundaverun-local/app/public/wp-config.php
```

**Usage**: All script saving, file operations, and path references

---

### WordPress Variables

```yaml
# Production WordPress
WP_PROD_DOMAIN: rundaverun.org
WP_PROD_URL: https://rundaverun.org
WP_PROD_TABLE_PREFIX: wp_7e1ce15f22_
WP_PROD_HOST: GoDaddy Managed WordPress
WP_PROD_SSH: Limited access

# Local WordPress
WP_LOCAL_DOMAIN: rundaverun-local.local
WP_LOCAL_URL: http://rundaverun-local.local
WP_LOCAL_TABLE_PREFIX: wp_
WP_LOCAL_HOST: Local by Flywheel
WP_LOCAL_CLI_FLAGS: --allow-root

# WordPress Paths
WP_CONTENT: wp-content
WP_PLUGINS: wp-content/plugins
WP_THEMES: wp-content/themes
WP_UPLOADS: wp-content/uploads
```

**Usage**: WordPress maintenance, deployment, database operations

---

### Hosting Variables

```yaml
# GoDaddy Specific
HOSTING_PROVIDER: GoDaddy Managed WordPress
HOSTING_FILE_PERMISSIONS: 600 (often restrictive)
HOSTING_CACHE_LAYERS: Multiple (aggressive)
HOSTING_SSH_ACCESS: Limited
HOSTING_CPANEL: Available
HOSTING_FILE_MANAGER: Available (files only, no DB backup)

# GoDaddy Quirks
GODADDY_TABLE_PREFIX: wp_7e1ce15f22_
GODADDY_CACHE_LOCATIONS: 
  - Browser cache
  - CDN cache  
  - Server cache
  - WordPress cache
```

**Usage**: Referenced in GoDaddy quirks, deployment, troubleshooting

---

### Development Environment Variables

```yaml
# Local Development
LOCAL_ENV: Local by Flywheel
LOCAL_OS: macOS
LOCAL_PHP: 8.1
LOCAL_MYSQL: 8.0

# System Tools
WP_CLI: Available (requires --allow-root)
GIT: Available
SSH: Available
BASH_VERSION: 5.x
```

**Usage**: Development protocols, script creation, troubleshooting

---

### Authorization & Security Variables

```yaml
# Authorization Windows
AUTH_WINDOW_DURATION: 4 hours
AUTH_MASS_OPERATION_THRESHOLD: 10+ items
AUTH_PRODUCTION_REQUIRED: Always for production changes

# Git Settings
GIT_USER_NAME: Dave Biggers
GIT_USER_EMAIL: [configured separately]
GIT_COMMIT_SIGNING: Configured
GIT_FORCE_PUSH: Never allowed
```

**Usage**: Authorization protocol, git workflow, security operations

---

### Backup Variables

```yaml
# Backup Locations
BACKUP_ROOT: /home/dave/skippy/backups
BACKUP_DB_DIR: /home/dave/skippy/backups/database
BACKUP_FILES_DIR: /home/dave/skippy/backups/files
BACKUP_SCRIPTS_DIR: /home/dave/skippy/backups/scripts

# Backup Retention
BACKUP_RETENTION_DAILY: 7 days
BACKUP_RETENTION_WEEKLY: 4 weeks
BACKUP_RETENTION_MONTHLY: 12 months

# Backup Format
BACKUP_DB_FORMAT: SQL (compressed .gz)
BACKUP_FILES_FORMAT: tar.gz
BACKUP_NAMING: {type}_{project}_{date}_{time}
```

**Usage**: Backup strategy protocol, disaster recovery

---

### Testing & QA Variables

```yaml
# Testing Domains
TEST_LOCAL: http://rundaverun-local.local
TEST_STAGING: [not currently used]
TEST_PRODUCTION: https://rundaverun.org

# Mobile Testing
MOBILE_TEST_DEVICES:
  - iPhone 14 Pro
  - iPad Pro
  - Samsung Galaxy S23
  - Google Pixel 7

# Browser Testing
BROWSER_TEST_TARGETS:
  - Chrome (latest)
  - Firefox (latest)
  - Safari (latest)
  - Edge (latest)
```

**Usage**: Testing protocols, mobile testing, QA procedures

---

## How to Use This Protocol

### For Current Project (rundaverun)

All protocols use these exact values as currently configured. No changes needed.

### For New Project Adaptation

**Step 1: Copy This File**
```bash
cp configuration_variables_protocol.md my_project_configuration.md
```

**Step 2: Update All Variables**
Edit the copied file with your project's values:
```yaml
PROJECT_NAME: my_project
PROJECT_DOMAIN: myproject.com
USER_HOME: /home/myusername
# ... update all relevant values
```

**Step 3: Find and Replace in Protocols**

Use these patterns to update protocols:

**Pattern 1: Project Name**
```bash
# Find: rundaverun
# Replace with: ${PROJECT_NAME}

# Example:
# Before: http://rundaverun-local.local
# After: http://${PROJECT_NAME}-local.local
```

**Pattern 2: User Paths**
```bash
# Find: /home/dave
# Replace with: ${USER_HOME}

# Example:
# Before: /home/dave/skippy/scripts
# After: ${USER_HOME}/skippy/scripts
```

**Pattern 3: WordPress Specifics**
```bash
# Find: wp_7e1ce15f22_
# Replace with: ${WP_PROD_TABLE_PREFIX}

# Example:
# Before: wp_7e1ce15f22_posts
# After: ${WP_PROD_TABLE_PREFIX}posts
```

### For Generic/Template Version

**Create Placeholder Version**:
Replace all specific values with variable notation:
- `rundaverun` → `{PROJECT_NAME}`
- `/home/dave` → `{USER_HOME}`
- `wp_7e1ce15f22_` → `{WP_TABLE_PREFIX}`

**Include Setup Instructions**:
Provide configuration guide for new users to fill in their values.

---

## Variable Naming Conventions

### Format Rules
- **All caps with underscores**: `PROJECT_NAME`
- **Hierarchical naming**: `WP_PROD_TABLE_PREFIX` (WordPress → Production → Table Prefix)
- **Descriptive names**: Use full words, not abbreviations
- **Consistent prefixes**: Related variables use same prefix

### Prefix Standards
- `PROJECT_` - Project identification
- `WP_` - WordPress related
- `LOCAL_` - Local development
- `BACKUP_` - Backup configuration
- `AUTH_` - Authorization/security
- `TEST_` - Testing/QA
- `USER_` - User/system paths

---

## Integration with Protocols

### How Variables Are Used

**Example 1: Script Saving Protocol**
```bash
# Current hardcoded version:
SCRIPT_DIR="/home/dave/skippy/scripts"

# Variable-based version:
SCRIPT_DIR="${USER_HOME}/skippy/scripts"
# Where USER_HOME=/home/dave from configuration
```

**Example 2: WordPress Maintenance**
```bash
# Current hardcoded version:
wp search-replace 'http://rundaverun-local.local' 'https://rundaverun.org'

# Variable-based version:
wp search-replace '${WP_LOCAL_URL}' '${WP_PROD_URL}'
# Where:
#   WP_LOCAL_URL=http://rundaverun-local.local
#   WP_PROD_URL=https://rundaverun.org
```

**Example 3: Deployment**
```bash
# Current hardcoded version:
ssh user@rundaverun.org

# Variable-based version:
ssh user@${PROJECT_DOMAIN}
# Where PROJECT_DOMAIN=rundaverun.org
```

---

## Validation Checklist

When setting up for a new project:

### Required Variables
- [ ] PROJECT_NAME set
- [ ] PROJECT_DOMAIN set
- [ ] USER_HOME set
- [ ] SCRIPTS_DIR set
- [ ] WP_PROD_URL set (if WordPress)
- [ ] WP_LOCAL_URL set (if WordPress)

### WordPress-Specific
- [ ] WP_PROD_TABLE_PREFIX identified
- [ ] WP_LOCAL_TABLE_PREFIX set
- [ ] HOSTING_PROVIDER documented
- [ ] WP_CONTENT path verified

### Path Validation
- [ ] All directories exist or can be created
- [ ] Permissions correct for all paths
- [ ] Claude Code can access all configured paths

### Testing
- [ ] Local URL responds
- [ ] Production URL responds (if applicable)
- [ ] WP-CLI works with configured paths
- [ ] Scripts can be saved to SCRIPTS_DIR

---

## Common Configurations

### Configuration Template: New WordPress Project

```yaml
PROJECT_NAME: my_project
PROJECT_DOMAIN: myproject.com
LOCAL_DOMAIN: my_project-local.local
USER_HOME: /home/username
PROJECT_ROOT: /home/username/projects/my_project
SCRIPTS_DIR: /home/username/projects/my_project/scripts
WP_PROD_URL: https://myproject.com
WP_LOCAL_URL: http://my_project-local.local
WP_PROD_TABLE_PREFIX: wp_
HOSTING_PROVIDER: [Your Host]
```

### Configuration Template: Non-WordPress Project

```yaml
PROJECT_NAME: my_app
PROJECT_DOMAIN: myapp.com
USER_HOME: /home/username
PROJECT_ROOT: /home/username/projects/my_app
SCRIPTS_DIR: /home/username/projects/my_app/scripts
GIT_REPO: https://github.com/username/my_app
```

---

## Version History

### v1.0.0 (2025-10-28)
- Initial configuration protocol
- Extracted variables from existing rundaverun setup
- Established naming conventions
- Created adaptation guide

---

## Maintenance

### When to Update This Protocol

**Immediately Update When**:
- Project name or domain changes
- Hosting provider changes
- Table prefix changes (WordPress)
- Local environment changes
- Directory structure reorganization

**Review Quarterly**:
- Add new variables as protocols expand
- Remove deprecated variables
- Update version numbers
- Validate all paths still correct

---

## Benefits of This Protocol

### Portability
- ✅ Adapt entire protocol system to new project in 15-30 minutes
- ✅ Share protocols with team using different paths
- ✅ Create generic templates for distribution

### Maintainability  
- ✅ Change value once, affects all protocols
- ✅ Clear documentation of environment setup
- ✅ Easier to spot inconsistencies

### Clarity
- ✅ New team members see configuration at a glance
- ✅ Understand project structure immediately
- ✅ Know what values are project-specific vs. standard

---

## Related Protocols

- **Script Saving Protocol**: Uses path variables
- **WordPress Maintenance Protocol**: Uses WordPress variables
- **Deployment Checklist Protocol**: Uses project and hosting variables
- **Backup Strategy Protocol**: Uses backup variables
- **Git Workflow Protocol**: Uses git and user variables

---

## Notes

- This protocol was created to enhance portability of the v2.0 protocol system
- All current protocols work with hardcoded values (no changes required)
- Variable-based approach is optional enhancement for reusability
- Creating a variable-based version is recommended if:
  - Working on multiple projects
  - Sharing protocols with team
  - Creating generic templates

**Status**: ✅ Optional Enhancement - Recommended for Reusability

---

**End of Protocol**
