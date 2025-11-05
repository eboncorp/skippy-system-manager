# TIER 2 Quick Reference Card

**Version:** 1.0.0
**Date:** November 4, 2025

---

## All TIER 2 Tools at a Glance

### 1. Secrets Manager

```bash
# Initialize
/home/dave/skippy/scripts/security/secrets_manager_v1.0.0.sh init

# Add credential
secrets_manager.sh add key_name "value"

# Get credential
secrets_manager.sh get key_name

# List all
secrets_manager.sh list

# Scan for exposed secrets
secrets_manager.sh scan

# Audit trail
secrets_manager.sh audit
```

**Use for:** Storing passwords, API keys, SSH credentials

---

### 2. WordPress Bulk Operations

```bash
# Fix apostrophes
/home/dave/skippy/scripts/wordpress/wp_bulk_operations_v1.0.0.sh fix-apostrophes

# Fix budget figures
wp_bulk_operations.sh fix-budget-figures

# Update email
wp_bulk_operations.sh update-email "old@email.com" "new@email.com"

# Fix links
wp_bulk_operations.sh fix-links

# Clean revisions
wp_bulk_operations.sh clean-revisions

# Clean trash
wp_bulk_operations.sh clean-trash

# Dry run mode (add to any command)
wp_bulk_operations.sh <command> --dry-run

# Generate report (add to any command)
wp_bulk_operations.sh <command> --report
```

**Use for:** Bulk content updates, cleanup, maintenance

---

### 3. WordPress Content Sync

```bash
# Compare local vs production
/home/dave/skippy/scripts/wordpress/wp_content_sync_v1.0.0.sh compare all

# Pull from production
wp_content_sync.sh pull posts --backup

# Push to production
wp_content_sync.sh push pages --backup

# Specific content types
wp_content_sync.sh <command> posts|pages|policies|all
```

**Use for:** Keeping local and production in sync

---

### 4. WordPress Quick Deploy

```bash
# Full deployment with all safety checks
/home/dave/skippy/scripts/wordpress/wp_quick_deploy_v1.0.0.sh

# Dry run
wp_quick_deploy.sh --dry-run

# Skip validation (not recommended)
wp_quick_deploy.sh --skip-validation

# Skip facts check
wp_quick_deploy.sh --skip-facts
```

**Use for:** Deploying to production safely

**Steps automated:**
1. Fact check
2. Pre-deployment validation
3. Backup creation
4. Content export
5. Production deployment
6. Post-deployment verification

---

### 5. Development Environment Setup

```bash
# Check environment
/home/dave/skippy/scripts/utility/dev_environment_setup_v1.0.0.sh check

# Fix issues
dev_environment_setup.sh fix

# Install tools
dev_environment_setup.sh install-tools

# Full setup (new machine)
dev_environment_setup.sh full-setup

# Setup cron jobs
dev_environment_setup.sh setup-cron

# Configure WordPress
dev_environment_setup.sh configure-wordpress
```

**Use for:** New machine setup, environment validation

---

### 6. Code Snippet Manager

```bash
# Initialize with built-in snippets
/home/dave/skippy/scripts/utility/snippet_manager_v1.0.0.sh init

# List all snippets
snippet_manager.sh list

# List by category
snippet_manager.sh list bash

# Show snippet
snippet_manager.sh show bash-error-handler

# Insert into script
snippet_manager.sh insert bash-colors >> my_script.sh

# Search
snippet_manager.sh search "wordpress"

# Add custom snippet
snippet_manager.sh add my-snippet snippet_file.sh

# Categories
snippet_manager.sh categories
```

**Built-in snippets:**
- bash-error-handler
- bash-colors
- bash-logging
- wp-db-query
- wp-search-replace
- git-commit
- backup-rotation
- audit-log
- python-error-handler
- mysql-backup

**Use for:** Reusable code patterns, faster script development

---

### 7. Shell Script Debugger

```bash
# Check syntax
/home/dave/skippy/scripts/utility/script_debugger_v1.0.0.sh syntax script.sh

# Full analysis
script_debugger.sh full-debug script.sh --report

# Analyze (shellcheck)
script_debugger.sh analyze script.sh

# Trace execution
script_debugger.sh trace script.sh arg1 arg2

# Profile performance
script_debugger.sh profile script.sh

# Lint style
script_debugger.sh lint script.sh

# Find issues
script_debugger.sh find-issues script.sh

# Auto-fix
script_debugger.sh fix script.sh

# Explain line
script_debugger.sh explain script.sh 42
```

**Use for:** Debugging, performance analysis, code quality

---

### 8. Template Generator

```bash
# Basic bash script
/home/dave/skippy/scripts/utility/template_generator_v1.0.0.sh bash-script new_script.sh

# WordPress tool
template_generator.sh wordpress-tool wp_tool.sh --name "My Tool"

# Backup script
template_generator.sh backup-script backup.sh

# Deployment script
template_generator.sh deployment-script deploy.sh

# Monitoring script
template_generator.sh monitoring-script health_check.sh

# Security scanner
template_generator.sh security-scanner scanner.sh

# Python script
template_generator.sh python-script script.py

# With options
template_generator.sh <type> <output> --name "Name" --description "Desc"
```

**Template types:**
- bash-script
- wordpress-tool
- backup-script
- deployment-script
- monitoring-script
- security-scanner
- cron-job
- python-script
- validation-script
- sync-script

**Use for:** Quick script scaffolding with best practices

---

### 9. Skippy Quick Launcher (BONUS)

```bash
# Launch interactive menu
/home/dave/skippy/scripts/utility/skippy_launcher_v1.0.0.sh
```

**Provides access to:**
- All WordPress operations
- Security & backup tools
- Development tools
- System monitoring
- Logs and reports

**Use for:** Quick access to all Skippy tools, guided workflows

---

## Common Workflows

### New Script Development

```bash
# 1. Generate template
template_generator.sh bash-script my_tool.sh --name "My Tool"

# 2. Add common patterns
snippet_manager.sh insert bash-error-handler >> my_tool.sh
snippet_manager.sh insert bash-logging >> my_tool.sh

# 3. Write custom logic
nano my_tool.sh

# 4. Debug
script_debugger.sh full-debug my_tool.sh --report

# 5. Fix issues
script_debugger.sh fix my_tool.sh

# 6. Test
./my_tool.sh
```

---

### Deployment Workflow

```bash
# 1. Make changes locally
# ... edit content ...

# 2. Validate
/home/dave/skippy/scripts/wordpress/pre_deployment_validator_v1.0.0.sh

# 3. Check facts
/home/dave/skippy/scripts/wordpress/fact_checker_v1.0.0.sh

# 4. Deploy
/home/dave/skippy/scripts/wordpress/wp_quick_deploy_v1.0.0.sh

# 5. Verify in deployment report
```

---

### Security Workflow

```bash
# 1. Store credentials
secrets_manager.sh add credential_name "value"

# 2. Scan for exposed secrets
secrets_manager.sh scan

# 3. Run security scan
/home/dave/skippy/scripts/security/vulnerability_scanner_v1.0.0.sh

# 4. Review audit trail
secrets_manager.sh audit
```

---

### WordPress Maintenance

```bash
# 1. Fix common issues
wp_bulk_operations.sh fix-apostrophes --report
wp_bulk_operations.sh fix-budget-figures --report
wp_bulk_operations.sh fix-links --report

# 2. Clean up
wp_bulk_operations.sh clean-revisions
wp_bulk_operations.sh clean-trash

# 3. Sync if needed
wp_content_sync.sh compare all
```

---

## Integration with TIER 1

### Use with Pre-Deployment Validator

```bash
# Validator automatically checks for:
# - Secrets exposed
# - Budget figures (uses fact checker)
# - Broken links
# - Development URLs
```

### Use with Quick Deploy

```bash
# Quick deploy automatically:
# - Runs fact checker
# - Runs pre-deployment validator
# - Creates backup
# - Logs to audit trail
# - Sends alerts on failure
```

### Use with Secrets Manager

```bash
# Quick deploy retrieves credentials
PROD_HOST=$(secrets_manager.sh get prod_ssh_host)
PROD_USER=$(secrets_manager.sh get prod_ssh_user)
```

---

## File Locations

```
/home/dave/skippy/scripts/
├── security/
│   ├── secrets_manager_v1.0.0.sh
│   └── migrate_secrets_v1.0.0.sh
├── wordpress/
│   ├── wp_bulk_operations_v1.0.0.sh
│   ├── wp_content_sync_v1.0.0.sh
│   └── wp_quick_deploy_v1.0.0.sh
└── utility/
    ├── dev_environment_setup_v1.0.0.sh
    ├── snippet_manager_v1.0.0.sh
    ├── script_debugger_v1.0.0.sh
    ├── template_generator_v1.0.0.sh
    └── skippy_launcher_v1.0.0.sh
```

---

## Keyboard Shortcuts (in Quick Launcher)

```
Main Menu:
  1-18   Select tool
  h      Help
  q      Quit

Submenus:
  1-9    Select operation
  b      Back to main menu
  q      Quit
```

---

## Environment Variables (Optional)

```bash
# Set in ~/.bashrc for convenience

# Skippy base
export SKIPPY_BASE="/home/dave/skippy"

# Aliases
alias skippy="$SKIPPY_BASE/scripts/utility/skippy_launcher_v1.0.0.sh"
alias secrets="$SKIPPY_BASE/scripts/security/secrets_manager_v1.0.0.sh"
alias wp-deploy="$SKIPPY_BASE/scripts/wordpress/wp_quick_deploy_v1.0.0.sh"
alias wp-validate="$SKIPPY_BASE/scripts/wordpress/pre_deployment_validator_v1.0.0.sh"
alias snippet="$SKIPPY_BASE/scripts/utility/snippet_manager_v1.0.0.sh"
alias debug-script="$SKIPPY_BASE/scripts/utility/script_debugger_v1.0.0.sh"
alias new-script="$SKIPPY_BASE/scripts/utility/template_generator_v1.0.0.sh"
```

Then use:
```bash
skippy              # Launch quick launcher
secrets list        # List secrets
wp-deploy           # Deploy to production
snippet show bash-colors  # Show snippet
```

---

## Cron Jobs (Automated)

Set up by `dev_environment_setup.sh setup-cron`:

```cron
# Work files cleanup - 3:30 AM daily
30 3 * * * /home/dave/skippy/scripts/cleanup_work_files.sh

# Security scan - 2 AM Sundays
0 2 * * 0 /home/dave/skippy/scripts/security/vulnerability_scanner_v1.0.0.sh

# Backup verification - 4 AM on 1st of month
0 4 1 * * /home/dave/skippy/scripts/backup/backup_verification_test_v1.0.0.sh
```

---

## Help Resources

### Built-in Help
```bash
# Every tool has help
<tool_name>.sh --help
```

### Documentation
```bash
# Secrets management guide
cat /home/dave/skippy/documentation/SECRETS_MANAGEMENT_GUIDE.md

# TIER 2 summary
cat /home/dave/skippy/conversations/TIER_2_COMPLETION_SUMMARY.md

# Overall status
cat /home/dave/skippy/ENHANCEMENT_PROJECT_STATUS.md

# This reference
cat /home/dave/skippy/TIER_2_QUICK_REFERENCE.md
```

### Script Index
```bash
# Search all 300+ scripts
grep -i "keyword" /home/dave/skippy/SCRIPT_INDEX.md

# Or via quick launcher
skippy_launcher.sh → Option 14
```

---

## Troubleshooting

### Tool Not Found

```bash
# Make sure script is executable
chmod +x /home/dave/skippy/scripts/**/*.sh

# Or use absolute path
/home/dave/skippy/scripts/utility/skippy_launcher_v1.0.0.sh
```

### Permission Denied

```bash
# Fix ownership
sudo chown -R dave:dave /home/dave/skippy

# Fix permissions
find /home/dave/skippy -type f -name "*.sh" -exec chmod +x {} \;
```

### GPG Errors (Secrets Manager)

```bash
# Install GPG
sudo apt install gnupg

# Initialize vault
secrets_manager.sh init
```

### WP-CLI Not Found

```bash
# Install WP-CLI
dev_environment_setup.sh install-tools

# Or manually
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
sudo mv wp-cli.phar /usr/local/bin/wp
```

---

## Tips & Best Practices

1. **Always use dry-run first** for bulk operations
2. **Backup before syncing** (use --backup flag)
3. **Store all credentials in secrets vault**
4. **Use quick launcher** for guided workflows
5. **Generate reports** for important operations
6. **Review audit logs** regularly
7. **Use templates** for new scripts
8. **Reuse snippets** to save time
9. **Debug before deploying**
10. **Let cron handle automation**

---

## Next Steps

1. ✅ Initialize secrets vault
2. ✅ Migrate existing credentials
3. ⏳ Set up aliases in ~/.bashrc
4. ⏳ Install cron jobs
5. ⏳ First deployment with quick deploy
6. ⏳ Create first script with template
7. ⏳ Add custom snippets
8. ⏳ Use quick launcher daily

---

**Quick Reference Version:** 1.0.0
**Last Updated:** November 4, 2025
**Part of:** Skippy Enhancement Project - TIER 2

**Print this or bookmark for quick access!**
