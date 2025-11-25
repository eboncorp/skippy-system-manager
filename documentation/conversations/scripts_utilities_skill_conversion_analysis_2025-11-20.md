# Scripts & Utilities Skill Conversion Analysis

**Date:** November 20, 2025
**Repositories Analyzed:** eboncorp/scripts, eboncorp/utilities
**Total Files Analyzed:** 63 files (30 scripts + 33 utilities)
**Purpose:** Identify candidates for conversion to Claude Code skills

---

## Executive Summary

### Recommendations

**HIGH PRIORITY (Convert to Skills):**
- 6 candidates from scripts repo
- 5 candidates from utilities repo
- **Total: 11 new skills**

**Key Benefits:**
- Centralized system management capabilities
- Document organization automation
- Maintenance and monitoring tools accessible via Claude Code
- Better integration with campaign workflows

---

## Repository 1: eboncorp/scripts Analysis

### Repository Overview

**Purpose:** System automation, infrastructure management, and monitoring tools
**Primary Use:** Ebonhawk server infrastructure and workstation management
**Total Scripts:** 30 files (22 shell, 3 Python, 5 test files)

### Technology Stack
- **Python 3.8+** with psutil, flask, pyyaml, colorlog
- **Bash** with ShellCheck validation
- **CI/CD:** GitHub Actions (test, lint, shellcheck, security)
- **Testing:** pytest with 80%+ coverage target

---

### 🔥 HIGH VALUE SKILL CANDIDATES (Scripts Repo)

#### 1. Ebonhawk Maintenance Agent ⭐ FLAGSHIP
**File:** `ebonhawk_maintenance_agent.py` (700+ lines)
**Suggested Skill Name:** `ebonhawk-maintenance`
**Skill Score:** 15/15

**Description:**
Comprehensive system monitoring and self-healing agent for the Ebonhawk server. Provides automated monitoring, maintenance alerts, and dashboard access.

**Why Convert:**
- Complex workflow orchestration
- Monitors multiple services (Docker, SSH, disk, CPU, memory)
- Self-healing capabilities
- Web dashboard included
- Critical infrastructure component

**Capabilities:**
- Real-time system health monitoring
- Service status checking (Docker, MySQL, SSH, Jellyfin)
- Automatic issue detection and alerting
- Performance metrics tracking
- Web dashboard on port 5000
- Email/SMS notifications
- Configuration via YAML + environment variables

**When to Auto-Invoke:**
- User mentions "ebonhawk" or "server status"
- Discussion about system monitoring
- Need for performance diagnostics
- Server health checks requested

**Example Usage:**
```
User: "Check the ebonhawk server status"
Claude: [Invokes ebonhawk-maintenance skill]
```

---

#### 2. System Audit Comprehensive
**File:** `system_audit_comprehensive.sh` (400+ lines)
**Suggested Skill Name:** `system-audit`
**Skill Score:** 12/15

**Description:**
Comprehensive system audit tool that checks security, performance, configuration, and generates detailed reports.

**Why Convert:**
- Comprehensive system analysis
- Security vulnerability scanning
- Performance bottleneck identification
- Configuration validation
- Generates actionable reports

**Capabilities:**
- Security posture assessment
- User and permission auditing
- Network configuration review
- Service status verification
- Package update checking
- Firewall rules analysis
- Resource usage analysis
- Formatted report generation

**When to Auto-Invoke:**
- Security audit requested
- System health check needed
- Before major updates/changes
- Troubleshooting system issues
- Compliance checking

---

#### 3. Nexus Infrastructure Status
**File:** `nexus_infrastructure_status.sh` (200+ lines)
**Suggested Skill Name:** `nexus-status`
**Skill Score:** 10/15

**Description:**
Multi-system status checker that monitors the entire Nexus infrastructure (ebonhawk + workstations).

**Why Convert:**
- Multi-system monitoring
- Infrastructure-wide view
- SSH-based remote checking
- Consolidated status reporting

**Capabilities:**
- Check ebonhawk server status remotely
- Monitor Dell Latitude 3520 workstation
- Monitor HP Z4 G4 workstation
- SSH connectivity testing
- Service status across all systems
- Resource usage summary

**When to Auto-Invoke:**
- User asks about "nexus" or "infrastructure"
- Need for multi-system status
- Remote system checks
- Infrastructure health overview

---

#### 4. Hardware Performance Optimizers
**Files:**
- `latitude_dev_optimizer.sh` (450+ lines)
- `z4_g4_performance_optimizer.sh` (450+ lines)

**Suggested Skill Name:** `hardware-optimizer`
**Skill Score:** 11/15

**Description:**
Hardware-specific performance optimization scripts for Dell Latitude 3520 and HP Z4 G4 workstations.

**Why Convert:**
- Hardware-specific optimization knowledge
- CPU/GPU tuning capabilities
- Power management optimization
- Development environment optimization

**Capabilities:**
- CPU frequency scaling optimization
- GPU performance tuning (Intel/NVIDIA)
- SSD TRIM optimization
- Swap and memory management
- Power profile optimization
- Thermal management
- Development tool optimization (compilers, Docker, etc.)
- Hardware detection and configuration

**When to Auto-Invoke:**
- User mentions performance issues
- System optimization requested
- New workstation setup
- Development environment tuning

---

#### 5. Browser Launcher & Fixer
**Files:**
- `chrome_launcher.sh`
- `firefox_launcher.sh`
- `fix_browsers.sh`

**Suggested Skill Name:** `browser-management`
**Skill Score:** 8/15

**Description:**
Browser launcher and fix tool with error handling and profile management.

**Why Convert:**
- Common user task (launching browsers)
- Handles browser profile issues
- Integrates with workflow automation
- Error recovery capabilities

**Capabilities:**
- Launch Chrome/Firefox with proper profiles
- Fix browser configuration issues
- Clear caches and reset profiles
- Handle sandboxing issues
- Launch with specific URLs/profiles

**When to Auto-Invoke:**
- User wants to open a URL
- Browser issues reported
- Web testing workflows
- Campaign website checking

---

#### 6. Google Drive Backup
**File:** `gdrive_backup.sh` (150+ lines)
**Suggested Skill Name:** `gdrive-backup`
**Skill Score:** 9/15

**Description:**
Automated Google Drive backup script with compression and syncing.

**Why Convert:**
- Critical backup functionality
- Integrates with campaign document management
- Automated scheduling capability
- Compression and encryption support

**Capabilities:**
- Backup local directories to Google Drive
- Incremental backup support
- Compression (tar.gz)
- Encryption options
- Bandwidth throttling
- Email notifications on completion/failure

**When to Auto-Invoke:**
- Backup requested
- Document archiving needed
- Campaign files need cloud backup
- Scheduled backup tasks

---

### 📋 MEDIUM VALUE CANDIDATES (Scripts Repo)

**Worth considering:**

1. **Installation Scripts** (install_ebonhawk_agent.sh, install_exodus.sh, install_nordpass.sh)
   - Score: 6/15
   - Reason: Useful for system setup, but infrequently used

2. **Network Performance Enhancer** (network_performance_enhancer.sh)
   - Score: 7/15
   - Reason: Valuable for troubleshooting, but specialized use case

3. **YubiKey Setup** (yubikey_setup_final.sh)
   - Score: 5/15
   - Reason: Security enhancement, but one-time setup

---

## Repository 2: eboncorp/utilities Analysis

### Repository Overview

**Purpose:** Document organization, file management, and duplicate detection
**Architecture:** Modern Python package with CLI, web dashboard, and modular design
**Total Files:** 33 Python files
**Coverage:** 76%+ test coverage

### Technology Stack
- **Python 3.8+** with pathlib, sqlite3, PyPDF2, FastAPI
- **Package:** Installed via `pip install -e .`
- **CLI:** Click framework with `utilities` command
- **Testing:** pytest with comprehensive fixtures

---

### 🔥 HIGH VALUE SKILL CANDIDATES (Utilities Repo)

#### 1. Smart Document Organizer ⭐ FLAGSHIP
**Files:**
- `smart_document_organizer.py` (400+ lines)
- `src/utilities/organizers/scan_organizer.py` (300+ lines)
- `src/utilities/common/categories.py` (200+ lines)

**Suggested Skill Name:** `document-organizer`
**Skill Score:** 14/15

**Description:**
AI-powered document organization system with PDF content analysis, keyword matching, and intelligent categorization.

**Why Convert:**
- Critical for campaign document management
- AI-based categorization
- PDF text extraction and analysis
- Automated filing system
- Tracks all operations in SQLite

**Capabilities:**
- Automatic document categorization (business, financial, legal, taxes, personal)
- PDF content analysis for better accuracy
- Keyword and regex pattern matching
- Configurable category rules
- Dry-run mode for testing
- Operation tracking and undo capability
- Progress tracking with progress bars
- Backup creation before moving files

**When to Auto-Invoke:**
- User mentions organizing documents
- Scan folder has new files
- Campaign documents need filing
- Inbox cleanup requested
- Financial documents need categorization

**Example Usage:**
```
User: "Organize the scans folder"
Claude: [Invokes document-organizer skill]
```

---

#### 2. Duplicate File Finder & Cleaner
**Files:**
- `duplicate_cleaner.py` (600+ lines)
- `quick_duplicate_finder.py` (300+ lines)

**Suggested Skill Name:** `duplicate-cleaner`
**Skill Score:** 13/15

**Description:**
Advanced duplicate file detection using SHA256 hashing with intelligent cleanup and archiving.

**Why Convert:**
- Frees up disk space
- SHA256 hash-based detection (100% accurate)
- GUI and CLI interfaces
- Smart archive organization
- Special handling for scripts and code

**Capabilities:**
- Find duplicates across multiple directories
- SHA256 hash comparison (not just name/size)
- Interactive selection (GUI with Tkinter)
- Command-line batch processing
- Archive duplicates before deletion
- Special handling for .eth scripts
- Statistics and reporting
- Backup creation

**When to Auto-Invoke:**
- Disk space issues
- User mentions "duplicates" or "cleanup"
- Large downloads folder
- Multiple backup copies detected
- Storage optimization needed

---

#### 3. Nexus Intelligent Agent
**File:** `nexus_intelligent_agent.py` (800+ lines)
**Suggested Skill Name:** `nexus-intelligent-agent`
**Skill Score:** 12/15

**Description:**
Self-healing system agent with automated maintenance, monitoring, and issue detection.

**Why Convert:**
- Proactive system maintenance
- Self-healing capabilities
- Multi-system monitoring
- Automated issue resolution
- Learning from past issues

**Capabilities:**
- Continuous system health monitoring
- Automatic issue detection
- Self-healing actions (restart services, clear caches, etc.)
- Pattern recognition for recurring issues
- Resource optimization
- Automated cleanup tasks
- Scheduled maintenance windows
- Email/SMS alerts

**When to Auto-Invoke:**
- System performance degradation
- Automated maintenance needed
- Proactive monitoring requested
- Self-healing capabilities needed

---

#### 4. Drive Scanner & Analysis
**Files:**
- `comprehensive_drive_scanner.py` (300+ lines)
- `fast_drive_scanner.py` (150+ lines)
- `timestamp_scanner.py` (150+ lines)

**Suggested Skill Name:** `drive-scanner`
**Skill Score:** 10/15

**Description:**
Fast drive scanning with file categorization, size analysis, and timestamp-based organization.

**Why Convert:**
- Quick storage analysis
- Identifies large files consuming space
- Timeline-based file analysis
- Category-based statistics

**Capabilities:**
- Rapid drive scanning (optimized for speed)
- File size distribution analysis
- Category breakdown (documents, images, videos, etc.)
- Large file identification (>100MB, >1GB)
- Timestamp-based file discovery
- Duplicate file hints
- JSON report generation
- Progress tracking

**When to Auto-Invoke:**
- "What's using space?" questions
- Storage capacity planning
- File discovery by date
- Large file cleanup needed

---

#### 5. Business Document Organizer
**File:** `business_document_organizer.py` (250+ lines)
**Suggested Skill Name:** `business-doc-organizer`
**Skill Score:** 11/15

**Description:**
Specialized organizer for business documents with invoice detection, vendor categorization, and date-based filing.

**Why Convert:**
- Campaign-specific document handling
- Vendor/client categorization
- Invoice and receipt processing
- Date-based organization

**Capabilities:**
- Invoice detection and extraction
- Vendor name identification
- Date-based folder structure (Year/Month/Vendor)
- Purchase order processing
- Receipt organization
- Client document filing
- Contract management
- Export to accounting software format

**When to Auto-Invoke:**
- Business documents need filing
- Invoice processing needed
- Campaign expense management
- Vendor document organization
- Financial record keeping

---

### 📋 MEDIUM VALUE CANDIDATES (Utilities Repo)

**Worth considering:**

1. **Scan Watcher** (scan_watcher.py)
   - Score: 7/15
   - Reason: Real-time monitoring useful, but can be handled by scheduler

2. **System-Wide Organizer** (system_wide_organizer.py)
   - Score: 6/15
   - Reason: Bulk operations useful, but overlaps with document-organizer

---

## Consolidated Recommendations

### Tier 1: Must-Convert Skills (11 skills)

| Priority | Skill Name | Source Repo | Primary Use Case |
|----------|------------|-------------|------------------|
| 1 | `ebonhawk-maintenance` | scripts | Server monitoring & management |
| 2 | `document-organizer` | utilities | Campaign document management |
| 3 | `duplicate-cleaner` | utilities | Storage optimization |
| 4 | `system-audit` | scripts | Security & compliance |
| 5 | `business-doc-organizer` | utilities | Financial document processing |
| 6 | `nexus-intelligent-agent` | utilities | Proactive system maintenance |
| 7 | `nexus-status` | scripts | Infrastructure monitoring |
| 8 | `hardware-optimizer` | scripts | Workstation performance |
| 9 | `drive-scanner` | utilities | Storage analysis |
| 10 | `gdrive-backup` | scripts | Cloud backup automation |
| 11 | `browser-management` | scripts | Workflow automation |

---

## Implementation Plan

### Phase 1: High-Impact Skills (Week 1)
**Focus:** System management and document handling

1. **ebonhawk-maintenance**
   - Immediate value for server management
   - Most requested by user
   - Complex but well-documented

2. **document-organizer**
   - Critical for campaign operations
   - High automation potential
   - Integrates with existing workflows

3. **duplicate-cleaner**
   - Quick wins for storage
   - High user satisfaction
   - Simple to implement

**Estimated Time:** 8-12 hours

---

### Phase 2: Operational Excellence (Week 2)
**Focus:** Monitoring and maintenance

4. **system-audit**
   - Security compliance
   - Pre-deployment checks
   - Regular health monitoring

5. **nexus-intelligent-agent**
   - Proactive maintenance
   - Reduces manual interventions
   - Learning system

6. **nexus-status**
   - Quick infrastructure checks
   - Remote monitoring
   - Multi-system view

**Estimated Time:** 6-10 hours

---

### Phase 3: Specialized Tools (Week 3)
**Focus:** Business operations and optimization

7. **business-doc-organizer**
   - Campaign finance management
   - Vendor tracking
   - Compliance documentation

8. **hardware-optimizer**
   - Workstation performance
   - Development environment
   - Resource optimization

9. **drive-scanner**
   - Storage planning
   - File discovery
   - Capacity management

**Estimated Time:** 6-8 hours

---

### Phase 4: Supporting Tools (Week 4)
**Focus:** Automation and convenience

10. **gdrive-backup**
    - Data protection
    - Campaign document archiving
    - Automated scheduling

11. **browser-management**
    - Workflow automation
    - Testing automation
    - Quick URL access

**Estimated Time:** 4-6 hours

---

## Skill Conversion Template

### Standard Structure for Each Skill

```markdown
---
name: skill-name
description: Brief description that triggers auto-invocation
---

# Skill Name

## When to Use This Skill

Auto-invoke when:
- User mentions [specific keywords]
- [Specific scenario occurs]
- [Specific task is needed]

## Prerequisites

- [Required dependencies]
- [Configuration files needed]
- [Access requirements]

## Quick Start

[Basic usage example]

## Commands Available

### Command 1: command-name
**Purpose:** What it does
**Usage:** `command syntax`
**Options:**
- `--option1`: Description
- `--option2`: Description

## Configuration

[Configuration requirements and examples]

## Examples

### Example 1: Common Use Case
```
User request
Claude response
```

### Example 2: Advanced Use Case
```
User request
Claude response
```

## Troubleshooting

### Issue 1
**Problem:** Description
**Solution:** Steps to resolve

## Technical Details

**Source:** `/path/to/original/script.py`
**Dependencies:** List of packages
**Compatibility:** System requirements
```

---

## Success Metrics

### Measurement Criteria

**For Each Skill:**
- ✅ Reduces manual task time by 70%+
- ✅ Auto-invoked correctly 90%+ of the time
- ✅ User satisfaction score 4/5 or higher
- ✅ Error rate < 5%
- ✅ Documentation complete and clear

**Overall Goals:**
- Convert 11 skills in 4 weeks
- 90% test coverage for all skills
- CLAUDE.md integration complete
- User training documentation created

---

## Risk Assessment

### Technical Risks

**Risk 1: Dependency Conflicts**
- **Severity:** Medium
- **Mitigation:** Test in isolated environment first
- **Fallback:** Keep original scripts accessible

**Risk 2: Configuration Complexity**
- **Severity:** Low
- **Mitigation:** Provide clear examples and defaults
- **Fallback:** Interactive setup wizard

**Risk 3: Permission Issues**
- **Severity:** Medium
- **Mitigation:** Document required permissions clearly
- **Fallback:** Graceful degradation with warnings

### Operational Risks

**Risk 1: User Adoption**
- **Severity:** Low
- **Mitigation:** Comprehensive training and examples
- **Fallback:** Parallel operation with original scripts

**Risk 2: Breaking Changes**
- **Severity:** Medium
- **Mitigation:** Versioning and compatibility layers
- **Fallback:** Rollback capability

---

## Next Steps

### Immediate Actions

1. **Prioritize Tier 1 Skills**
   - Start with ebonhawk-maintenance (highest impact)
   - Then document-organizer (campaign critical)
   - Then duplicate-cleaner (quick win)

2. **Create Skill Templates**
   - Use convert_script_to_skill_v1.0.0.py
   - Add YAML frontmatter
   - Write auto-invocation triggers

3. **Test Thoroughly**
   - Dry-run mode for all file operations
   - Test auto-invocation logic
   - Verify integration with existing workflows

4. **Document**
   - Create skill documentation
   - Update CLAUDE.md in skippy repo
   - Write user guides

5. **Deploy Incrementally**
   - One skill at a time
   - Test in production environment
   - Gather user feedback

---

## Appendix: Skill Scoring Methodology

### Scoring Criteria (0-15 points)

**Complexity (0-5 points)**
- 5: Complex workflow orchestration
- 3: Moderate logic and dependencies
- 1: Simple script execution

**Frequency of Use (0-5 points)**
- 5: Daily use
- 3: Weekly use
- 1: Monthly or less

**Impact (0-5 points)**
- 5: Critical infrastructure/campaign operations
- 3: Significant productivity improvement
- 1: Nice-to-have convenience

**Score Interpretation:**
- 13-15: Must convert (highest value)
- 10-12: Should convert (high value)
- 7-9: Consider converting (medium value)
- 0-6: Low priority

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-20
**Author:** Claude Code Analysis
**Status:** Ready for Implementation
