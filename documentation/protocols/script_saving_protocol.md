# Script Saving Protocol

**Version**: 1.0.0
**Last Updated**: 2025-11-05
**Owner**: Skippy Development Team

## Context

This protocol defines how to save, version, and organize scripts within the Skippy System Manager to ensure consistency, maintainability, and discoverability.

## Guidelines

1. **Consistent Naming**: All scripts follow a standardized naming convention
2. **Semantic Versioning**: Version numbers indicate the nature of changes
3. **Proper Organization**: Scripts are organized by category
4. **Documentation**: All scripts include header documentation
5. **Testing**: Scripts are tested before being marked as active

## Naming Convention

### Format

```
<script_name>_v<MAJOR>.<MINOR>.<PATCH>.<extension>
```

### Examples

- `wordpress_backup_v1.0.0.sh`
- `system_monitor_v2.1.3.py`
- `data_processor_v1.0.0.sh`

### Version Numbers

- **MAJOR**: Breaking changes, incompatible API changes
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, minor improvements

## Directory Structure

```
scripts/
├── automation/       # Automated tasks
├── backup/           # Backup operations
├── deployment/       # Deployment scripts
├── maintenance/      # Maintenance tasks
├── monitoring/       # System monitoring
├── security/         # Security tools
├── wordpress/        # WordPress management
└── ...              # Other categories
```

## Procedure

### 1. Create New Script

```bash
# Choose appropriate directory
cd scripts/<category>/

# Create script with proper naming
touch script_name_v1.0.0.sh

# Make executable
chmod +x script_name_v1.0.0.sh
```

### 2. Add Header Documentation

```bash
#!/bin/bash
# Script Name: script_name_v1.0.0.sh
# Version: 1.0.0
# Purpose: Brief description of what the script does
# Usage: ./script_name_v1.0.0.sh [options]
# Author: Your Name
# Created: YYYY-MM-DD
# Last Modified: YYYY-MM-DD

set -euo pipefail

# Script content...
```

### 3. Update Script Index

```bash
# Update SCRIPT_INDEX.json (if it exists)
# Or document in SCRIPT_STATUS.md
```

### 4. Test Script

```bash
# Test in development environment
./script_name_v1.0.0.sh --dry-run

# Verify output
# Check for errors
```

### 5. Version Control

```bash
# Add to git
git add scripts/<category>/script_name_v1.0.0.sh

# Commit with descriptive message
git commit -m "feat: add script_name v1.0.0"

# Push to repository
git push origin <branch>
```

## Versioning Examples

### Initial Release: v1.0.0

```bash
# First version of the script
wordpress_backup_v1.0.0.sh
```

### Minor Update: v1.1.0

```bash
# Added new feature (backward compatible)
wordpress_backup_v1.1.0.sh

# Old version becomes deprecated
mv wordpress_backup_v1.0.0.sh scripts/archive/
```

### Major Update: v2.0.0

```bash
# Breaking changes, new approach
wordpress_backup_v2.0.0.sh

# v1.x.x moved to legacy
mv wordpress_backup_v1.1.0.sh scripts/legacy_system_managers/
```

### Patch: v2.0.1

```bash
# Bug fix, no new features
wordpress_backup_v2.0.1.sh

# Previous patch replaced
rm wordpress_backup_v2.0.0.sh
```

## Script Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| automation | Automated tasks | Document scanning, music organization |
| backup | Backup operations | WordPress backup, system backup |
| deployment | Deployment scripts | WordPress deployment, server setup |
| maintenance | Maintenance tasks | Cleanup, optimization, updates |
| monitoring | System monitoring | Dashboard, alerts, metrics |
| security | Security tools | Scans, audits, hardening |
| wordpress | WordPress management | Updates, themes, plugins |
| disaster_recovery | DR procedures | Restore, failover, recovery |
| network | Network operations | Connectivity, configuration |
| testing | Test scripts | Unit tests, integration tests |

## Deprecation Process

### When to Deprecate

- Newer version exists
- Script no longer needed
- Better alternative available
- Security vulnerabilities

### Steps

1. **Mark as deprecated** in SCRIPT_STATUS.md
2. **Move to appropriate location**:
   - `scripts/legacy_system_managers/` - Still functional
   - `scripts/archive/` - No longer maintained
3. **Update references** in documentation
4. **Notify team** of deprecation
5. **Set removal date** (typically 90 days)

## Best Practices

### 1. Descriptive Names

❌ Bad: `backup.sh`, `script1.sh`, `test.py`
✅ Good: `wordpress_backup_v1.0.0.sh`, `system_monitor_v1.0.0.py`

### 2. Consistent Extensions

- `.sh` - Bash scripts
- `.py` - Python scripts
- `.js` - JavaScript/Node.js scripts

### 3. Error Handling

```bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Check dependencies
command -v jq >/dev/null 2>&1 || { echo "jq required"; exit 1; }

# Validate inputs
if [ -z "${REQUIRED_VAR:-}" ]; then
    echo "REQUIRED_VAR not set"
    exit 1
fi
```

### 4. Logging

```bash
# Use consistent logging
LOG_FILE="/var/log/skippy/script_name.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

log "Script started"
```

## Related Protocols

- [Git Workflow Protocol](git_workflow_protocol.md) - How to commit scripts
- [Testing Standards Protocol](testing_standards_protocol.md) - How to test scripts
- [Error Logging Protocol](error_logging_protocol.md) - How to log errors

## References

- [Semantic Versioning](https://semver.org/)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [PEP 8 - Python Style Guide](https://pep8.org/)
```
