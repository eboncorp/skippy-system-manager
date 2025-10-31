# Skippy Project - Claude Instructions

**Project**: System Automation & Management Suite
**Last Updated**: 2025-10-28
**Project Type**: Python/Bash automation toolkit

## Project Overview

Skippy is a collection of system automation tools, network management utilities, and home server infrastructure scripts. This is your main workspace for creating, testing, and organizing automation scripts.

## Key Locations

### Main Directory
- **Root**: `/home/dave/skippy/`
- **Scripts**: `/home/dave/skippy/scripts/` - ALL new scripts go here
- **Conversations**: `/home/dave/skippy/conversations/` - Session logs and protocols
- **Documentation**: `/home/dave/skippy/documentation/` - Technical documentation
- **Development**: `/home/dave/skippy/development/` - Work in progress

### Subdirectories
```
/home/dave/skippy/
├── scripts/                 - NEW scripts created by Claude (versioned)
├── conversations/           - Claude session logs and memory files
├── claude/
│   ├── uploads/            - Packages for claude.ai upload
│   └── downloads/          - Downloaded packages
├── claude_work/            - Working files for Claude sessions
├── development/            - Development projects
│   └── unified_system_manager/ - System manager project
├── documentation/          - Technical docs (network, Ethereum, etc.)
├── downloads/              - General downloads
├── github/                 - GitHub repositories
├── google_drive/           - Google Drive sync (skippy copy)
├── networks_files/         - Network analysis files
├── nexus_controller_v2/    - Nexus controller system
├── personal/               - Personal files
└── projects/               - Active projects
```

### Main Python Scripts (Root Level)
- `advanced_system_manager.py` - System management
- `unified-gui.py` - GUI interface
- `home_server_master.py` - Home server management
- `ai_maintenance_engine_v2.py` - AI-powered maintenance
- `web_system_manager.py` - Web management interface
- `active_network_scan.py` - Network scanning
- `cloud_monitoring_integration.py` - Cloud monitoring
- `multi_server_manager.py` - Multi-server management

## Script Management Protocol

### Mandatory Location
**ALL new scripts MUST be saved to**: `/home/dave/skippy/scripts/[category]/`

### Categories
```
/home/dave/skippy/scripts/
├── automation/          - Automated tasks and workflows
├── backup/              - Backup scripts
├── data_processing/     - Data manipulation and analysis
├── deployment/          - Deployment automation
├── maintenance/         - System maintenance
├── monitoring/          - Monitoring and alerting
├── network/             - Network utilities
├── utility/             - General utilities
├── web/                 - Web-related scripts
└── wordpress/           - WordPress-specific tools
```

### Versioning Requirements
**Format**: `script_name_v{major}.{minor}.{patch}.{ext}`

**Examples**:
- `network_scanner_v1.0.0.py`
- `wordpress_backup_v2.1.0.sh`
- `system_monitor_v1.0.5.py`

**Header Template**:
```bash
#!/bin/bash
# Script Name: descriptive_script_name
# Version: 1.0.0
# Date: 2025-10-28
# Author: Claude Code
# Purpose: What this script does
# Usage: How to run it
# Dependencies: Required tools/packages
# Notes: Important information
#
# Changelog:
# v1.0.0 (2025-10-28): Initial release
```

### After Creating Script
1. ✅ Save to `/home/dave/skippy/scripts/[category]/`
2. ✅ Set executable: `chmod +x script_name_v1.0.0.sh`
3. ✅ Update scripts index
4. ✅ Notify user with full path and usage

### Full Protocol
See: `/home/dave/skippy/conversations/script_saving_protocol.md`

## Development Workflow

### Creating New Scripts
1. Discuss requirements with user
2. Write script with full documentation
3. Save to appropriate category in `/home/dave/skippy/scripts/`
4. Test script (if appropriate)
5. Add to scripts index

### Updating Existing Scripts
1. Check for existing script in `/home/dave/skippy/scripts/`
2. Read current version
3. Increment version number (major/minor/patch)
4. Save new version (keep old version)
5. Update changelog in header

### Testing Scripts
- Test in `/home/dave/skippy/claude_work/` if needed
- Don't test on production systems without permission
- Always ask before running potentially destructive scripts

## Python Environment

### Virtual Environments
- Check for venv: `/home/dave/.venvs/`
- Activate if needed for dependencies
- Document required packages in script header

### Common Dependencies
- Python 3.x (system default)
- Standard library modules preferred
- Document any pip packages required

## Documentation

### Technical Documentation Location
`/home/dave/skippy/documentation/`

**Contains**:
- Network setup guides
- Ethereum node documentation
- NETGEAR router PDFs
- Security implementation guides
- Home server setup guides

### Creating Documentation
- Save to `/home/dave/skippy/documentation/`
- Use markdown format (.md)
- Include date and version
- Cross-reference related scripts

## Conversation Logs

### Memory Files
`/home/dave/skippy/conversations/`

**Purpose**:
- Store protocol files (script_saving_protocol.md)
- Error logs and troubleshooting
- Session summaries
- Project documentation

### Creating Memory Files
```bash
/home/dave/skippy/conversations/
├── script_saving_protocol.md       - Script management protocol
├── error_logs/                     - Error tracking
├── session_summaries/              - Session documentation
└── project_notes/                  - Project-specific notes
```

## Upload Packages

### Claude.ai Upload Preparation
**Location**: `/home/dave/skippy/claude/uploads/`

**When creating packages**:
1. Create directory: `package_name_YYYY-MM-DD/`
2. Collect all relevant files
3. Create README with context
4. Zip package: `package_name_YYYY-MM-DD.zip`
5. Create text-only version if needed (remove binaries)

**Naming Convention**:
- `project_description_YYYY-MM-DD.zip`
- `project_description_TEXT_ONLY_YYYY-MM-DD.zip`

## Network & Infrastructure

### Network Scanning
- `active_network_scan.py` - Network device discovery
- `active_network_scan_v2.py` - Enhanced version
- Results typically in `networks_files/`

### Home Server Management
- Main controller: `home_server_master.py`
- Documentation in `documentation/` subdirectory
- HP Z4 G4 hardware specs in docs

### Ethereum Node
- Setup scripts and guides in `documentation/`
- Configuration files in appropriate subdirs
- Version comparisons and recommendations documented

## System Management

### Unified System Manager
Location: `/home/dave/skippy/development/unified_system_manager/`

### Nexus Controller
Location: `/home/dave/skippy/nexus_controller_v2/`

### Monitoring Tools
- Various Python scripts for system monitoring
- Cloud integration available
- Multi-server management capabilities

## Git Workflow

### When Working in Skippy
- This directory is a git repository
- Create meaningful commit messages
- Test before committing
- Don't commit sensitive data

### Commit Format
```
[Category] Brief description

Details:
- What changed
- Why it changed
- Impact

Files:
- path/to/file1.py
- path/to/file2.sh
```

## Common Tasks

### Create New Automation Script
```python
#!/usr/bin/env python3
# Script Name: automation_task_v1.0.0
# Version: 1.0.0
# [full header]

def main():
    # Implementation
    pass

if __name__ == "__main__":
    main()
```

### Create Backup Script
```bash
#!/bin/bash
# Script Name: backup_target_v1.0.0
# Version: 1.0.0
# [full header]

# Configuration
BACKUP_DIR="/path/to/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# Implementation
# ...
```

### Update Scripts Index
Add entry to `/home/dave/skippy/scripts/index.md`:
```markdown
## Script Name v1.0.0
- **Location**: `/home/dave/skippy/scripts/category/script_name_v1.0.0.ext`
- **Purpose**: Brief description
- **Usage**: `command to run`
- **Last Updated**: 2025-10-28
```

## Best Practices

### Code Style
- Python: PEP 8 compliance
- Bash: Use ShellCheck recommendations
- Clear variable names
- Comment complex logic

### Error Handling
- Always include try/except in Python
- Check exit codes in Bash
- Provide meaningful error messages
- Log errors to appropriate location

### Security
- Never hardcode credentials
- Use environment variables
- Validate user input
- Check file permissions

## Troubleshooting

### Script Not Running
1. Check executable permissions: `ls -la script.sh`
2. Verify shebang line: `#!/bin/bash` or `#!/usr/bin/env python3`
3. Check for dependencies
4. Review error messages

### Python Import Errors
1. Check if module installed: `pip3 list | grep module`
2. Verify virtual environment active
3. Install missing packages: `pip3 install package`

### Path Issues
- Always use absolute paths in scripts
- Test path existence before operations
- Use proper path joining: `os.path.join()` in Python

## Resources

- Script protocol: `/home/dave/skippy/conversations/script_saving_protocol.md`
- Documentation: `/home/dave/skippy/documentation/`
- Examples: Check existing scripts in `/home/dave/skippy/scripts/`
- System scripts: `/home/dave/scripts/` (system-wide utilities)

## Quick Reference

### File Locations
```bash
# New scripts
/home/dave/skippy/scripts/[category]/

# Upload packages
/home/dave/skippy/claude/uploads/

# Documentation
/home/dave/skippy/documentation/

# Work in progress
/home/dave/skippy/claude_work/

# Memory files
/home/dave/skippy/conversations/
```

### Common Commands
```bash
# Make executable
chmod +x /home/dave/skippy/scripts/category/script_v1.0.0.sh

# Run Python script
python3 /home/dave/skippy/scripts/category/script_v1.0.0.py

# Run Bash script
bash /home/dave/skippy/scripts/category/script_v1.0.0.sh
```

---

**This file is automatically loaded when working in the skippy project directory.**
