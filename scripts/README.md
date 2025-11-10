# Skippy System Manager - Scripts Directory

**Location:** `scripts/`
**Purpose:** Centralized script library for system management and automation
**Total Scripts:** 226+ utility scripts
**Organization:** By category (utility, monitoring, wordpress, etc.)

---

## 📂 Directory Structure

```
scripts/
├── utility/              ← General utilities (protocol validation, search)
├── monitoring/           ← System monitoring scripts
├── wordpress/            ← WordPress-specific tools
├── backup/               ← Backup and restore utilities
├── security/             ← Security scanning and auditing
└── [various others]      ← Additional categories
```

---

## 🎯 Essential Scripts

### Protocol Management

#### 1. Protocol Validation (v2.0.0)
**Location:** `scripts/utility/validate_protocols_v2.0.0.sh`
**Purpose:** Validate protocol files meet standards
**Use:** Check system health, find issues

**Usage:**
```bash
# Run validation
bash scripts/utility/validate_protocols_v2.0.0.sh

# Set custom base path
SKIPPY_BASE_PATH=/custom/path bash scripts/utility/validate_protocols_v2.0.0.sh
```

**Checks:**
- ✅ Header compliance (Version, Date, Purpose)
- ✅ Naming conventions
- ✅ Code block completeness
- ✅ Duplicate protocols
- ✅ Cross-references
- ✅ TODO/FIXME presence

**Output:**
- Protocol inventory
- Header compliance percentages
- Issues found with locations
- Warnings with recommendations
- Summary with next steps

**Exit codes:**
- `0` - All checks passed
- `1` - Issues or warnings found

---

#### 2. Protocol Search (v2.0.0)
**Location:** `scripts/utility/search_protocols_v2.0.0.sh`
**Purpose:** Search protocols by keyword, tag, or category
**Use:** Quick protocol discovery

**Usage:**
```bash
# Search by keyword
bash scripts/utility/search_protocols_v2.0.0.sh backup

# Search by tag
bash scripts/utility/search_protocols_v2.0.0.sh --tag wordpress

# Search by category
bash scripts/utility/search_protocols_v2.0.0.sh --category security

# Filter by priority
bash scripts/utility/search_protocols_v2.0.0.sh --priority critical

# Verbose output with context
bash scripts/utility/search_protocols_v2.0.0.sh -v deployment

# Search specific location
bash scripts/utility/search_protocols_v2.0.0.sh --location doc backup

# Show help
bash scripts/utility/search_protocols_v2.0.0.sh --help
```

**Search modes:**
- `-k, --keyword` - Search content for keyword
- `-t, --tag` - Search by tag (wordpress, git, security, etc.)
- `-c, --category` - Search by category (operations, development, etc.)
- `-p, --priority` - Filter by priority level
- `-l, --location` - Limit to doc/conv/all

**Categories supported:**
- security, operations, development, deployment
- data, documentation, system, workflow

**Output format:**
```
Found 5 protocol(s):

[1] wordpress_content_update_protocol
    Location: documentation/protocols/
    Version: 1.0.0
    Priority: CRITICAL
    Path: /path/to/protocol.md
```

---

### Protocol Validation (Legacy v1.0.0)
**Location:** `scripts/utility/validate_protocols_v1.0.0.sh`
**Status:** Deprecated (use v2.0.0)
**Purpose:** Original validation script
**Note:** Hardcoded paths, limited checks

---

### Protocol Search (Legacy v1.0.0)
**Location:** `scripts/utility/search_protocols_v1.0.0.sh`
**Status:** Deprecated (use v2.0.0)
**Purpose:** Original search script
**Note:** Basic functionality only

---

## 📋 Script Categories

### Utility Scripts (`scripts/utility/`)
- Protocol validation (v1.0.0, v2.0.0)
- Protocol search (v1.0.0, v2.0.0)
- File management utilities
- Text processing tools
- General system utilities

### Monitoring Scripts (`scripts/monitoring/`)
- Protocol metrics tracking
- Protocol violation checker
- System health monitoring
- Service status checks
- Alert management

### WordPress Scripts (`scripts/wordpress/`)
- Content deployment
- Database operations
- Plugin management
- Theme utilities
- Diagnostic tools

### Security Scripts (`scripts/security/`)
- Pre-commit security scans
- Credential detection
- Vulnerability scanning
- Access auditing
- Secret rotation

### Backup Scripts (`scripts/backup/`)
- Database backups
- File system backups
- Configuration backups
- Restore procedures
- Backup verification

---

## 🔧 Script Naming Conventions

### Standard Format
```
[name]_v[version].sh
```

**Examples:**
- `validate_protocols_v2.0.0.sh`
- `search_protocols_v2.0.0.sh`
- `pre_commit_security_scan_v1.0.0.sh`

### Versioning
- **Major.Minor.Patch** (semantic versioning)
- Major: Breaking changes
- Minor: New features, backward compatible
- Patch: Bug fixes only

### Best Practices
- ✅ Use descriptive names
- ✅ Include version number
- ✅ Use `.sh` extension
- ✅ Make executable (`chmod +x`)
- ✅ Include header comment block

---

## 📖 Script Header Template

Every script should have:

```bash
#!/bin/bash
# Script Name: script_name
# Version: X.Y.Z
# Purpose: Brief description
# Created: YYYY-MM-DD
# Protocol Reference: path/to/protocol.md (if applicable)
#
# Changelog:
# vX.Y.Z (YYYY-MM-DD): Changes made
# vX.Y.0 (YYYY-MM-DD): Previous changes
```

---

## 🚀 Using Scripts

### Making Scripts Executable
```bash
chmod +x scripts/utility/script_name.sh
```

### Running Scripts
```bash
# Direct execution
bash scripts/utility/script_name.sh

# Or if executable
./scripts/utility/script_name.sh

# With environment variables
VAR=value bash scripts/utility/script_name.sh
```

### Common Patterns

**Environment configuration:**
```bash
# Use environment variable for base path
BASE_PATH="${SKIPPY_BASE_PATH:-$(pwd)}"
```

**Help messages:**
```bash
# Always provide --help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi
```

**Error handling:**
```bash
# Check if required files exist
if [ ! -f "$REQUIRED_FILE" ]; then
    echo "Error: Required file not found"
    exit 1
fi
```

**Output formatting:**
```bash
# Use colors if terminal supports it
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    NC=''
fi

echo -e "${GREEN}Success${NC}"
echo -e "${RED}Error${NC}"
```

---

## 📚 Related Protocols

- **[Script Saving Protocol](../documentation/protocols/script_saving_protocol.md)** - How to save scripts
- **[Script Usage vs Creation Protocol](../documentation/protocols/script_usage_creation_protocol.md)** - When to use vs create
- **[Script Management Protocol](../conversations/script_management_protocol.md)** - Managing script library

---

## 🔍 Finding Scripts

### By Name
```bash
# Find script by name
find scripts -name "*backup*" -type f

# List all scripts
find scripts -name "*.sh" -type f | sort
```

### By Category
```bash
# List scripts in category
ls scripts/utility/
ls scripts/monitoring/
ls scripts/wordpress/
```

### By Version
```bash
# Find latest version
ls scripts/utility/validate_protocols_v*.sh | sort -V | tail -1
```

### By Purpose
```bash
# Search script headers
grep -r "Purpose:" scripts/ --include="*.sh" | grep "backup"
```

---

## ⚙️ Script Development

### Creating New Scripts

1. **Check if script exists**
   ```bash
   bash scripts/utility/search_protocols_v2.0.0.sh [functionality]
   find scripts -name "*[keyword]*"
   ```

2. **Follow naming convention**
   ```bash
   [descriptive_name]_v1.0.0.sh
   ```

3. **Use script template**
   ```bash
   # Copy from template or existing script
   cp scripts/utility/validate_protocols_v2.0.0.sh scripts/utility/new_script_v1.0.0.sh
   ```

4. **Include proper header**
   - Script name
   - Version
   - Purpose
   - Created date
   - Protocol reference (if applicable)

5. **Make executable**
   ```bash
   chmod +x scripts/utility/new_script_v1.0.0.sh
   ```

6. **Test thoroughly**
   ```bash
   bash scripts/utility/new_script_v1.0.0.sh
   ```

7. **Document in protocol**
   - Update relevant protocol with script reference
   - Add to this README if it's a key utility

---

## 🧪 Testing Scripts

### Before Committing

```bash
# 1. Run script with various inputs
bash script.sh --help
bash script.sh [test-case-1]
bash script.sh [test-case-2]

# 2. Check exit codes
bash script.sh && echo "Success" || echo "Failed"

# 3. Test error handling
bash script.sh invalid-input

# 4. Check for shellcheck issues (if available)
shellcheck script.sh

# 5. Verify no hardcoded paths
grep -E "(/home/dave|/home/user)" script.sh
```

---

## 📊 Script Statistics

**Total Scripts:** 226+

**By Category:**
- Utility: 20+
- Monitoring: 15+
- WordPress: 30+
- Security: 10+
- Backup: 15+
- Others: 136+

**Key Scripts:**
- Protocol validation (v2.0.0) ⭐
- Protocol search (v2.0.0) ⭐
- Pre-commit security scan (v1.0.0)
- WordPress diagnostic (v1.3.0)
- Backup automation (various)

**Version 2.0.0 Scripts:**
- validate_protocols_v2.0.0.sh (NEW)
- search_protocols_v2.0.0.sh (NEW)

---

## 🚨 Important Notes

### Environment Variables

**SKIPPY_BASE_PATH:**
- Used by protocol scripts for path configuration
- Default: Current working directory
- Override: `SKIPPY_BASE_PATH=/custom/path`

**Usage:**
```bash
SKIPPY_BASE_PATH=/home/dave/skippy bash scripts/utility/validate_protocols_v2.0.0.sh
```

### Deprecated Scripts

**v1.0.0 scripts are deprecated:**
- `validate_protocols_v1.0.0.sh` → Use v2.0.0
- `search_protocols_v1.0.0.sh` → Use v2.0.0

**Migration:**
- v2.0.0 scripts are backward compatible
- No breaking changes in basic usage
- Added features: More checks, better output, environment-agnostic

---

## 💡 Pro Tips

### 1. Use Latest Versions
```bash
# Always use highest version number
ls scripts/utility/validate_protocols_v*.sh | sort -V | tail -1
```

### 2. Check Help First
```bash
# All major scripts have --help
bash scripts/utility/search_protocols_v2.0.0.sh --help
```

### 3. Use Environment Variables
```bash
# For portable scripts
export SKIPPY_BASE_PATH=/path/to/skippy
bash scripts/utility/validate_protocols_v2.0.0.sh
```

### 4. Bookmark Common Scripts
```bash
# Create aliases for frequently used scripts
alias validate-protocols='bash scripts/utility/validate_protocols_v2.0.0.sh'
alias search-protocols='bash scripts/utility/search_protocols_v2.0.0.sh'
```

---

## 🔗 Quick Links

**Documentation:**
- [Main README](../README.md)
- [QUICKSTART Guide](../QUICKSTART.md)
- [Protocol Index](../conversations/PROTOCOL_INDEX.md)

**Key Scripts:**
- [validate_protocols_v2.0.0.sh](utility/validate_protocols_v2.0.0.sh)
- [search_protocols_v2.0.0.sh](utility/search_protocols_v2.0.0.sh)

**Protocols:**
- [Script Saving Protocol](../documentation/protocols/script_saving_protocol.md)
- [Script Usage vs Creation](../documentation/protocols/script_usage_creation_protocol.md)
- [Script Management](../conversations/script_management_protocol.md)

---

## ❓ FAQ

### Q: How do I find a script for a specific task?
**A:** Use `find scripts -name "*keyword*"` or search script headers with grep.

### Q: Which version should I use?
**A:** Always use the highest version number (e.g., v2.0.0 over v1.0.0).

### Q: Can I modify existing scripts?
**A:** Yes! Create a new version (increment version number) and document changes in the changelog.

### Q: Where do I save new scripts?
**A:** Save to the appropriate category directory. If unsure, use `scripts/utility/`.

### Q: How do I make scripts environment-agnostic?
**A:** Use environment variables like `${SKIPPY_BASE_PATH:-$(pwd)}` instead of hardcoded paths.

---

## 📞 Getting Help

**Script Issues:**
1. Check script's `--help` output
2. Review related protocol
3. Check script header for purpose/usage
4. Review recent changes in git log

**Script Development:**
1. Reference existing scripts as templates
2. Follow naming conventions
3. Use script header template
4. Test thoroughly before committing

---

**Last Updated:** 2025-11-10
**Version:** 1.0.0
**Total Scripts:** 226+
**Key Utilities:** validate_protocols v2.0.0, search_protocols v2.0.0
