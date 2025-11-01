# Claude Conversations & Protocols - Complete Index

**Location**: `/home/dave/skippy/conversations/`
**Purpose**: Persistent memory system for Claude Code
**Last Updated**: 2025-10-31
**Status**: ✅ Complete - 18 protocols + 4 quick references

## Overview

This directory contains the complete protocol system for Claude Code - a comprehensive set of procedures, standards, and references that persist across all sessions. These protocols ensure consistent, professional, and efficient work.

---

## Core Protocols (Foundational)

### 0. Pre-Commit Sanitization Protocol ✨ NEW - CRITICAL SECURITY
**File**: `pre_commit_sanitization_protocol.md` | **Size**: ~800 lines | **Priority**: CRITICAL

**Purpose**: Prevent credentials and sensitive data from being committed to Git

**Key Rules**:
- ✅ Automated pre-commit hook scans for credentials BEFORE every commit
- ✅ Comprehensive .gitignore patterns for API keys, tokens, passwords
- ✅ Content scanning for Anthropic, GitHub, AWS, and other API key patterns
- ✅ BLOCKS commit if credentials detected
- ✅ Emergency response procedures if credentials are pushed

**When to Reference**: AUTOMATIC - Pre-commit hook runs before every commit

**Created:** Oct 31, 2025 (Triggered by Anthropic API key exposure incident)

---

### 1. Script Creation Protocol ✨
**File**: `script_creation_protocol.md` | **Size**: ~600 lines | **Priority**: CRITICAL

**Purpose**: ALWAYS check existing scripts before creating new ones

**Key Rules**:
- ✅ MUST search `/home/dave/skippy/scripts/` BEFORE creating ANY script
- ✅ 226 scripts already available - check for similar ones first
- ✅ Modify existing scripts instead of creating duplicates
- ✅ Inform user of existing options
- ✅ Only create new if no suitable match exists

**When to Reference**: BEFORE creating ANY script (mandatory first step)

**Search Commands**:
```bash
# Search by keyword
grep -r "KEYWORD" /home/dave/skippy/scripts/ --include="*.sh" --include="*.py" -l

# List category
ls -lh /home/dave/skippy/scripts/[CATEGORY]/
```

---

### 2. Script Saving Protocol
**File**: `script_saving_protocol.md` | **Size**: ~500 lines | **Priority**: HIGH

**Purpose**: Standardized script creation and management

**Key Rules**:
- ALL scripts save to: `/home/dave/skippy/scripts/[category]/`
- Mandatory semantic versioning: `script_name_v1.0.0.sh`
- Custom descriptive names required
- Complete documentation headers
- Executable permissions (chmod +x)
- Update index after creation

**When to Reference**: Every time creating or updating a script (after checking existing)

**Categories**:
- automation, backup, data_processing, deployment, maintenance
- monitoring, network, utility, web, wordpress

---

### 3. Error Logging Protocol
**File**: `error_logging_protocol.md` | **Size**: ~700 lines | **Priority**: HIGH

**Purpose**: Systematic error tracking and troubleshooting

**Key Features**:
- Error logs save to `error_logs/YYYY-MM/`
- Standardized log format
- Solution documentation
- Recurring issue tracking
- Root cause analysis
- Prevention measures

**When to Reference**: When errors occur, for troubleshooting patterns

**Directory Structure**:
```
error_logs/
├── 2025-10/         - Current month logs
├── recurring/       - Recurring issues
├── resolved/        - Permanently resolved
└── index.md         - Error index
```

---

### 4. Git Workflow Protocol
**File**: `git_workflow_protocol.md` | **Size**: ~800 lines | **Priority**: CRITICAL

**Purpose**: Git operations and commit standards

**Core Rules**:
- ✅ NEVER commit without explicit user request
- ✅ NEVER run destructive git commands without user approval
- ✅ ALWAYS check authorship before amending
- ✅ NEVER force push to main/master

**Commit Format**:
```
[Category] Brief description (max 50 chars)

Detailed explanation (wrap at 72 chars)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Categories**: Feature, Fix, Refactor, Perf, Content, Style, Docs, Config, Deploy, Chore, Test

**When to Reference**: Before any git operation, especially commits

---

### 5. Backup Strategy Protocol
**File**: `backup_strategy_protocol.md` | **Size**: ~700 lines | **Priority**: HIGH

**Purpose**: Backup procedures before risky operations

**Backup Types**:
1. Directory structure backups
2. Configuration backups
3. Database backups
4. File content backups
5. Git snapshots

**When Required**:
- Before mass operations (10+ files)
- Before database modifications
- Before risky system changes
- Before deployments

**When to Reference**: Before any operation that could cause data loss

---

### 6. Authorization Protocol
**File**: `authorization_protocol.md` | **Size**: ~12KB | **Priority**: CRITICAL

**Purpose**: When and how to use Claude authorization for sensitive operations

**Requires Authorization**:
- Mass operations (10+ items)
- Production changes
- Database drops/resets
- System configuration changes

**Authorization Command**:
```bash
bash /home/dave/scripts/system/authorize_claude
```

**Grant Window**: 4 hours

**When to Reference**: Before requesting user authorization

---

## WordPress Protocols (Specialized)

### 6. WordPress Maintenance Protocol
**File**: `wordpress_maintenance_protocol.md` | **Size**: ~25KB, ~1000 lines | **Priority**: CRITICAL

**Purpose**: Complete WordPress workflows and procedures

**Covers**:
- Database operations (export, import, search-replace)
- WP-CLI commands (with --allow-root requirement)
- GoDaddy Managed WordPress quirks
- Plugin/theme management
- Content management
- Debugging procedures
- Common WordPress issues

**Core Rules**:
- ✅ ALWAYS test locally before production
- ✅ ALWAYS backup database before major operations
- ✅ ALWAYS use `--allow-root` flag (Local by Flywheel)
- ✅ NEVER edit production database directly

**When to Reference**: For ALL WordPress-related work (40% of recent tasks)

---

### 7. Deployment Checklist Protocol
**File**: `deployment_checklist_protocol.md` | **Size**: ~15KB | **Priority**: HIGH

**Purpose**: Step-by-step deployment procedures with verification

**Checklist Phases**:
1. **Pre-Deployment**: Testing, backups, git commit
2. **Deployment**: File upload, database, cache clearing
3. **Post-Deployment**: Verification, monitoring
4. **Rollback**: Emergency recovery procedures

**Deployment Types**:
- WordPress site deployment
- Script deployment
- Package/release deployment
- Emergency/hotfix deployment

**When to Reference**: Before EVERY deployment

---

### 8. Debugging Workflow Protocol
**File**: `debugging_workflow_protocol.md` | **Size**: ~15KB | **Priority**: HIGH

**Purpose**: Systematic debugging methodology

**5-Step Process**:
1. Problem Identification
2. Information Gathering
3. Hypothesis Formation
4. Testing & Validation
5. Documentation & Prevention

**Decision Trees For**:
- WordPress database issues
- File permission issues
- Plugin/theme issues
- Deployment issues
- Mobile issues

**When to Reference**: When debugging any issue (prevents trial-and-error)

---

## Development Protocols (Standards)

### 9. Documentation Standards Protocol
**File**: `documentation_standards_protocol.md` | **Size**: ~20KB | **Priority**: MEDIUM-HIGH

**Purpose**: Standardized documentation practices

**Covers**:
- File naming standards
- Markdown standards
- README templates
- Code documentation (headers, comments)
- Protocol documentation format
- Version history format

**Core Principles**:
- Write for future self (assume you'll forget)
- Write for others (explain clearly)
- Keep documentation current
- Make it discoverable

**When to Reference**: When creating any documentation

---

### 10. Package Creation Protocol
**File**: `package_creation_protocol.md` | **Size**: ~18KB | **Priority**: MEDIUM-HIGH

**Purpose**: Creating distribution packages

**Package Types**:
1. Documentation packages (glossary, policies)
2. Script/tool packages
3. Upload packages (for claude.ai)
4. Release packages
5. Backup packages

**Universal Requirements**:
- Version number (semantic versioning)
- README file
- Complete structure
- Proper naming (lowercase_with_underscores)
- File organization

**When to Reference**: When creating any package for distribution

---

### 11. Testing & QA Protocol
**File**: `testing_qa_protocol.md` | **Size**: ~15KB | **Priority**: HIGH

**Purpose**: Testing and quality assurance procedures

**Testing Levels**:
1. Unit testing (code level)
2. Integration testing
3. System testing
4. User acceptance testing

**Testing Types**:
- WordPress testing (WP-CLI, browser, mobile)
- Script testing (functionality, error handling, edge cases)
- Deployment testing (pre/post deployment)
- Regression testing

**When to Reference**: Before any deployment or code release

---

## Quick References (Fast Lookup)

### 12. WP-CLI Quick Reference
**File**: `wp_cli_quick_reference.md` | **Size**: ~10KB | **Priority**: HIGH

**Purpose**: Common WP-CLI commands at a glance

**Sections**:
- Database commands (export, import, search-replace)
- Core commands (version, update, verify)
- Plugin commands (list, activate, deactivate, update)
- Theme commands
- Post commands
- Option commands
- Cache/maintenance commands
- Useful combinations

**Local by Flywheel Note**: ALWAYS use `--allow-root` flag

**When to Reference**: During any WordPress work

---

### 13. GoDaddy Quirks Reference
**File**: `godaddy_quirks_reference.md` | **Size**: ~12KB | **Priority**: HIGH

**Purpose**: GoDaddy-specific issues and workarounds

**Major Quirks**:
- Custom table prefix: `wp_7e1ce15f22_` (not standard `wp_`)
- File permissions: Often 600 instead of 644
- File Manager backup: Files only (no database)
- Limited SSH access
- Multiple cache layers
- phpMyAdmin session timeouts

**Quick Fix Table**: Issue → Cause → Quick Fix for 12 common problems

**When to Reference**: When working with GoDaddy production site

---

### 14. Common Errors & Solutions Guide
**File**: `common_errors_solutions_guide.md` | **Size**: ~15KB | **Priority**: HIGH

**Purpose**: Quick solutions for frequently encountered errors

**Error Categories**:
- WordPress errors
- WP-CLI errors
- File permission errors
- Database errors
- Git errors
- SSH/connection errors
- Mobile/browser errors
- Cache errors

**Format**: For each error:
- Symptom
- Common causes
- Quick fix (one-liner)
- Detailed solution (step-by-step)

**When to Reference**: When encountering any error

---

### 15. Mobile Testing Checklist
**File**: `mobile_testing_checklist.md` | **Size**: ~8KB | **Priority**: HIGH

**Purpose**: Mobile testing procedures

**Testing Areas**:
- Visual/Layout (viewport, scrolling, text, images)
- Navigation (mobile menu, links)
- Touch interaction (tap, scroll, swipe)
- Content (text, media, icons)
- Functionality (load, buttons, forms)
- Performance (speed, resources)
- Browser compatibility (iOS Safari, Android Chrome)
- Accessibility (screen reader, keyboard)

**Testing Workflow**:
- Quick test (5 min): Every deployment
- Standard test (15 min): Significant changes
- Comprehensive test (30-45 min): Major releases

**When to Reference**: Before ANY deployment

---

## System Documentation

### Protocol System Summary
**File**: `protocol_system_summary.md` | **Size**: ~14KB

**Purpose**: Complete implementation documentation

**Statistics**:
- Files created: 15+ protocols + 4 quick references
- Lines of documentation: 10,000+
- Coverage: All major workflows

**Implementation Details**:
- What was created
- Directory structure
- How protocols work
- Integration points
- Success metrics

**When to Reference**: To understand the protocol system architecture

---

## Directory Structure

```
/home/dave/skippy/conversations/
├── readme.md                                    # This file - complete index
│
├── Core Protocols
├── script_saving_protocol.md                    # Script management
├── error_logging_protocol.md                    # Error tracking
├── git_workflow_protocol.md                     # Git standards
├── backup_strategy_protocol.md                  # Backup procedures
├── authorization_protocol.md                    # Authorization workflow
│
├── WordPress Protocols
├── wordpress_maintenance_protocol.md            # WordPress procedures
├── deployment_checklist_protocol.md             # Deployment steps
├── debugging_workflow_protocol.md               # Debugging methodology
│
├── Development Protocols
├── documentation_standards_protocol.md          # Documentation standards
├── package_creation_protocol.md                 # Package creation
├── testing_qa_protocol.md                       # Testing procedures
│
├── Quick References
├── wp_cli_quick_reference.md                    # WP-CLI commands
├── godaddy_quirks_reference.md                  # GoDaddy issues
├── common_errors_solutions_guide.md             # Error solutions
├── mobile_testing_checklist.md                  # Mobile testing
│
├── System Documentation
├── protocol_system_summary.md                   # Implementation details
│
└── Error Logs
    └── error_logs/
        ├── 2025-10/                             # Current month
        ├── recurring/                           # Recurring issues
        └── resolved/                            # Resolved issues
```

---

## How Protocols Load

### Automatic Loading Hierarchy

1. **Global Instructions** (Always loaded)
   - `/home/dave/.claude/claude.md`
   - Contains references to all protocols
   - Loaded in EVERY Claude session

2. **Project-Specific Instructions** (When in project directory)
   - `/home/dave/rundaverun/.claude/claude.md` (RunDaveRun)
   - `/home/dave/skippy/.claude/claude.md` (Skippy)
   - Auto-loaded when working in project directory

3. **Protocol Files** (Referenced as needed)
   - `/home/dave/skippy/conversations/*.md`
   - Referenced by Claude during relevant tasks
   - Persistent across all sessions

### No User Action Required
- Files persist automatically
- No #memory commands needed
- Available in all future sessions
- Updates take effect immediately

---

## When to Reference Each Protocol

### Always Reference Before
- **Script Saving**: Creating any script
- **Git Workflow**: Any git operation
- **Authorization**: Requesting user authorization
- **Backup Strategy**: Risky operations
- **Deployment Checklist**: Any deployment

### Reference During
- **WordPress Maintenance**: All WordPress work
- **Debugging Workflow**: When troubleshooting issues
- **Testing & QA**: Testing code or sites
- **Documentation Standards**: Writing documentation

### Quick Lookup When Needed
- **WP-CLI Reference**: WordPress commands
- **GoDaddy Quirks**: Production site issues
- **Common Errors**: Error messages
- **Mobile Testing**: Mobile testing tasks

---

## Protocol Usage Statistics

Based on gap analysis of recent work (Aug-Oct 2025):

| Protocol | Frequency | Impact | Time Saved |
|----------|-----------|--------|------------|
| WordPress Maintenance | 40% of work | CRITICAL | 2-4 hrs/week |
| Deployment Checklist | Weekly | HIGH | 1-2 hrs/deployment |
| Debugging Workflow | 2-3x/week | HIGH | 1 hr/issue |
| WP-CLI Reference | Daily | HIGH | 15 min/day |
| Common Errors | 2-3x/week | HIGH | 30 min/error |
| Mobile Testing | Every deploy | MEDIUM | 20 min/deployment |
| GoDaddy Quirks | As needed | HIGH | 1 hr/issue |

**Estimated Total Time Savings**: 5-10 hours per week

---

## Protocol Maintenance

### Monthly Review
- [ ] Review error logs for patterns
- [ ] Update common errors guide with new issues
- [ ] Check if protocols need clarification
- [ ] Archive old error logs

### After Major Projects
- [ ] Update protocols with lessons learned
- [ ] Add new categories if needed
- [ ] Refine procedures based on experience
- [ ] Update examples

### Continuous Improvement
- Add new errors to common errors guide
- Update quirks reference with new findings
- Improve documentation based on usage
- Track time saved

---

## Integration with Projects

### RunDaveRun Campaign
**Location**: `/home/dave/rundaverun/`
**Protocols Used**:
- WordPress Maintenance (heavily)
- Deployment Checklist (every deploy)
- WP-CLI Reference (daily)
- GoDaddy Quirks (production issues)
- Mobile Testing (every deploy)

### Skippy System
**Location**: `/home/dave/skippy/`
**Protocols Used**:
- Script Saving (all scripts)
- Error Logging (debugging)
- Git Workflow (version control)
- Documentation Standards (all docs)
- Package Creation (releases)

---

## Key Principles

1. **Persistence**: All protocols persist across sessions automatically
2. **Hierarchy**: Global → Project → Protocol (layered approach)
3. **Comprehensive**: Covers all major workflows
4. **Searchable**: Organized and indexed
5. **Maintainable**: Easy to update and extend
6. **Practical**: Based on actual work patterns
7. **Time-Saving**: Prevents repeated troubleshooting
8. **Quality**: Ensures professional standards

---

## Quick Access Summary

### Most Critical (Reference Daily/Weekly)
1. **WordPress Maintenance Protocol** - 40% of work
2. **WP-CLI Quick Reference** - WordPress commands
3. **Deployment Checklist Protocol** - Every deployment
4. **Common Errors Solutions Guide** - Troubleshooting

### Important (Reference Frequently)
5. **Debugging Workflow Protocol** - Systematic troubleshooting
6. **Mobile Testing Checklist** - Pre-deployment testing
7. **GoDaddy Quirks Reference** - Production issues
8. **Git Workflow Protocol** - Version control

### Reference As Needed
9. **Script Saving Protocol** - Creating scripts
10. **Testing & QA Protocol** - Quality assurance
11. **Documentation Standards** - Writing docs
12. **Package Creation Protocol** - Distributions
13. **Authorization Protocol** - Sensitive operations
14. **Error Logging Protocol** - Tracking issues
15. **Backup Strategy Protocol** - Data protection

---

## Success Metrics

### Immediate Benefits (Achieved)
✅ Complete protocol coverage established
✅ All major workflows documented
✅ Quick references available
✅ Cross-referenced and indexed

### Short-term (1-4 weeks)
- Reduced time troubleshooting recurring issues
- Faster deployments (checklist-driven)
- Consistent script quality
- Better error documentation

### Long-term (1-3 months)
- 5-10 hours saved per week
- Fewer deployment issues
- Comprehensive error knowledge base
- Consistent professional standards

---

## Getting Help

### If Protocol Unclear
- Read related protocols (cross-referenced)
- Check quick references first
- See common errors guide for examples

### If Protocol Incomplete
- Document what's missing
- Update protocol with findings
- Cross-reference related protocols

### If New Pattern Emerges
- Document in error log
- Update relevant protocol
- Add to common errors if recurring

---

**Status**: ✅ Complete and Active
**Version**: 2.0
**Date**: 2025-10-28
**Coverage**: Comprehensive - All major workflows covered

**This protocol system is live and active across all Claude Code sessions.**
