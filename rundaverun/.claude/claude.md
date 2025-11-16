# RunDaveRun Campaign Project - Claude Instructions

**Project**: Dave Biggers For Mayor - Louisville Metro
**Last Updated**: 2025-10-28
**Project Type**: Political campaign website (WordPress)

## Project Overview

This is a political campaign website for Dave Biggers' mayoral campaign in Louisville, Kentucky. The site includes:
- 499-term voter education glossary (v4.0)
- 31+ policy documents
- Campaign information and volunteer resources
- Participatory budgeting plans
- Union engagement strategies

## Key Locations

### Campaign Files
- **Main directory**: `/home/dave/rundaverun/campaign/`
- **Policy documents**: All in campaign/ directory with descriptive names
- **WordPress site**: `/home/dave/Local Sites/rundaverun-local/app/public/`
- **Local URL**: `rundaverun-local.local`
- **Production**: `rundaverun.org`

### Important Files
- `00_readme_start_here.md` - Project overview and getting started
- `budget_3.1_comprehensive_package_plan.md` - Budget plan v3.1
- `employee_pay_plan.md` - Employee Bill of Rights
- `first_100_days_plan.md` - Implementation timeline
- All policy documents: `*_policy.md`, `*_plan.md`, `*_guide.md`

## WordPress Workflow

### Always Test Locally First
1. **Never make changes directly to production**
2. **Always test on Local**: `rundaverun-local.local`
3. **Verify changes work correctly**
4. **Then deploy to production**

### WP-CLI Commands
**ALWAYS use `--allow-root` flag**:
```bash
cd "/home/dave/Local Sites/rundaverun-local/app/public"
wp post list --allow-root
wp page list --allow-root
wp plugin list --allow-root
wp db export /path/to/backup.sql --allow-root
```

### Common Tasks

#### View Pages
```bash
wp page list --allow-root
```

#### View Posts
```bash
wp post list --allow-root
```

#### Check Plugins
```bash
wp plugin list --allow-root
```

#### Database Backup
```bash
wp db export /home/dave/rundaverun/backups/backup_$(date +%Y%m%d_%H%M%S).sql --allow-root
```

## Deployment Protocol

### GitHub Actions CI/CD
- **Repository**: Connected to GitHub with Actions workflow
- **Automatic deployment**: Push to main triggers deployment
- **SSH access**: Via git_deployer user on GoDaddy hosting

### Before Deploying
1. ✅ Test locally on `rundaverun-local.local`
2. ✅ Backup production database
3. ✅ Create git commit with descriptive message
4. ✅ Push to GitHub
5. ✅ Monitor GitHub Actions for success
6. ✅ Verify on production site

### Deployment Scripts
- `deploy-to-production.sh` - Manual deployment script
- `prepare_godaddy_package.sh` - Package creation for manual upload

## Glossary Management

### Current Version: v4.0 (499 terms)
- **Location**: `/wp-content/uploads/glossary_v4.html` and `.json`
- **WordPress Page**: Page 328 - "Complete Voter Education Glossary"
- **Categories**: 48 categories covering government, budgets, policies, etc.

### Glossary Sources
Six original glossary sources merged into v4.0:
- Located in previous upload packages
- See `comprehensive_glossary_v4.0_readme.md` for merge details

### Updating Glossary
1. Edit source JSON file
2. Regenerate HTML with search functionality
3. Upload to WordPress `/wp-content/uploads/`
4. Update page 328 iframe source if needed

## Policy Documents

### Current Policies (31 documents)
**Enhanced Policies** (7):
- Environmental Justice Policy
- Government Transparency & Civic Engagement Initiative
- Economic Development Accountability Framework
- Data Center Accountability Framework
- Affordable Housing Expansion Plan
- Mini Substations Implementation Guide
- Wellness Centers Operations Guide

**Original Policies** (16):
- Budget 3.1 Comprehensive Package Plan
- Employee Pay Plan (Employee Bill of Rights)
- First 100 Days Plan
- Participatory Budgeting Guide
- Plus 12 more core policies

**Strategy Documents** (5):
- Union Engagement Strategy
- Social Media Strategy
- Opposition Attack Responses
- Debate Prep Guide
- Immediate Action Checklist

**Volunteer Documents** (3):
- Volunteer Mobilization Guide
- Door to Door Talking Points
- Endorsement Package

### Policy Integration
- All policies link to glossary for term definitions
- Each policy page has glossary notice banner
- Voter Education hub page (337) organizes all policies

## Backup Protocol

### Before Major Changes
```bash
# Backup database
wp db export /home/dave/rundaverun/backups/pre_change_$(date +%Y%m%d_%H%M%S).sql --allow-root

# Backup wp-content
tar -czf /home/dave/rundaverun/backups/wp_content_$(date +%Y%m%d_%H%M%S).tar.gz /home/dave/Local\ Sites/rundaverun-local/app/public/wp-content/
```

### Backup Schedule
- **Before deployment**: Always
- **After major content updates**: Always
- **Before WordPress updates**: Always
- **Weekly**: Automated (if configured)

## Git Workflow

### Commit Message Format
```
[Category] Brief description

Detailed explanation of changes:
- What was changed
- Why it was changed
- Impact on site

Related files:
- file1.md
- file2.php
```

**Categories**:
- `[Content]` - Content updates (policies, pages, posts)
- `[Feature]` - New features
- `[Fix]` - Bug fixes
- `[Deploy]` - Deployment-related changes
- `[Docs]` - Documentation updates
- `[Style]` - CSS/design changes

### Branching Strategy
- `main` - Production-ready code
- `dev` - Development branch for testing
- `feature/feature-name` - New features
- Always test in `dev` before merging to `main`

## Content Guidelines

### Tone & Style
- Professional but accessible
- Louisville-specific context
- Emphasize transparency and accountability
- Union-friendly language
- Community-focused messaging

### Key Themes
- Participatory budgeting
- Government transparency
- Union support and worker rights
- Community safety through substations
- Wellness centers for holistic health
- Environmental justice
- Affordable housing

## Common Tasks Quick Reference

### Create New Policy Page
```bash
wp post create --post_type=page --post_title="Policy Title" --post_status=publish --allow-root
```

### Update Existing Page
```bash
wp post update <ID> --post_content="$(cat policy_file.md)" --allow-root
```

### Check Site Status
```bash
wp core version --allow-root
wp plugin list --allow-root
wp theme list --allow-root
```

### Search Content
```bash
wp post list --s="search term" --allow-root
```

## Upload Package Protocol

### For Claude.ai Upload
When creating packages for claude.ai:
1. **Location**: `/home/dave/skippy/claude/uploads/`
2. **Naming**: `project_description_YYYY-MM-DD.zip`
3. **Include**:
   - All campaign markdown files
   - WordPress database export
   - Policy documents
   - Glossary sources
   - README with context

### Text-Only Packages
- Strip binary files (images, fonts)
- Keep: .md, .txt, .json, .sql, .html, .php, .css, .js
- Size target: <20 MB for optimal upload

## Important Notes

### Production Site
- **URL**: `rundaverun.org`
- **Hosting**: GoDaddy Managed WordPress
- **SSH Access**: Via git_deployer user
- **Database**: MySQL on GoDaddy

### Local Development
- **Tool**: Local by Flywheel
- **Site Name**: rundaverun-local
- **URL**: `rundaverun-local.local`
- **PHP Version**: Check with `wp cli info --allow-root`

### Security
- Never commit sensitive credentials
- Use environment variables for secrets
- Keep .env files in .gitignore
- Authorization required for production changes

## Troubleshooting

### WordPress Not Loading
1. Check Local by Flywheel is running
2. Restart site in Local
3. Check error logs: `wp log list --allow-root`

### WP-CLI Not Working
- Always use `--allow-root` flag
- Ensure you're in site directory
- Check PHP version compatibility

### Deployment Fails
1. Check GitHub Actions logs
2. Verify SSH credentials
3. Check GoDaddy hosting status
4. Review deployment script errors

## Resources

- Campaign overview: `00_readme_start_here.md`
- Full reorganization docs: `/home/dave/reorganization_backup/`
- Script protocol: `/home/dave/skippy/conversations/script_saving_protocol.md`
- WordPress Codex: https://codex.wordpress.org/
- WP-CLI Docs: https://wp-cli.org/

---

**This file is automatically loaded when working in the rundaverun project directory.**
