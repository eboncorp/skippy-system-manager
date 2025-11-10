# Documentation Standards Protocol

**Date Created**: 2025-10-28
**Purpose**: Standardized documentation practices for all project files
**Applies To**: All documentation (README, protocols, code comments, user guides)
**Priority**: MEDIUM-HIGH (affects long-term maintainability)

## Purpose

This protocol establishes:
- Markdown formatting standards for all documentation
- File naming conventions across the project
- Code documentation requirements (headers, comments, docstrings)
- README, protocol, and user guide templates
- Version history and changelog standards

---

## Overview

This protocol establishes documentation standards to ensure all project documentation is consistent, clear, and maintainable. Well-documented code and processes are essential for long-term success.

## Core Documentation Principles

### 1. Write for Your Future Self
✅ Document as if you'll forget everything in 6 months
✅ Explain *why* decisions were made, not just *what*
✅ Include context and rationale
❌ Don't assume you'll remember

### 2. Write for Others
✅ Assume reader has general knowledge but not project-specific
✅ Define acronyms and technical terms
✅ Provide examples
❌ Don't use insider jargon without explanation

### 3. Keep Documentation Current
✅ Update docs when code changes
✅ Review docs regularly
✅ Remove outdated information
❌ Don't let docs become stale

### 4. Make It Discoverable
✅ Use clear file names
✅ Organize logically
✅ Create index files
✅ Cross-reference related docs

---

## File Naming Standards

### General Rules
- **Always lowercase**: `documentation_standards_protocol.md`
- **Use underscores**: Not hyphens, not spaces, not camelCase
- **Be descriptive**: `wordpress_backup_script.sh` not `backup.sh`
- **Include version**: `glossary_generator_v1.2.0.py`
- **Include date** (if relevant): `error_log_2025-10-28.md`

### Documentation File Names

**Protocol Files**:
```
script_saving_protocol.md
error_logging_protocol.md
git_workflow_protocol.md
backup_strategy_protocol.md
```

**README Files**:
```
readme.md                  # Package/directory overview
usage_guide.md            # How to use
installation_guide.md     # How to install
troubleshooting_guide.md  # Common issues
```

**Reference Files**:
```
wp_cli_quick_reference.md
godaddy_quirks_reference.md
common_errors_solutions.md
```

**Log Files**:
```
error_2025-10-28_1430_database_connection.md
deployment_log_2025-10-28.md
backup_log_2025-10-28_1430.md
```

---

## Markdown Standards

### File Structure

Every markdown document should follow this structure:

```markdown
# Document Title

**Date Created**: YYYY-MM-DD
**Date Updated**: YYYY-MM-DD (if applicable)
**Purpose**: One-line description of document purpose
**Applies To**: What this document covers
**Priority**: CRITICAL/HIGH/MEDIUM/LOW

## Overview

Brief (2-3 paragraph) overview of the document contents.

## Section 1

### Subsection 1.1

Content...

### Subsection 1.2

Content...

## Section 2

---

## Quick Reference (optional but recommended)

Summary or quick-lookup section at the end

---

**Final Notes/Footer**
```

### Heading Hierarchy

```markdown
# H1 - Document Title (only one per file)

## H2 - Major Sections

### H3 - Subsections

#### H4 - Sub-subsections (use sparingly)
```

**Rules**:
- Only ONE H1 per document (the title)
- Don't skip heading levels (don't go H2 → H4)
- Use consistent heading style throughout document

### Lists

**Unordered Lists**:
```markdown
- First item
- Second item
  - Nested item (2 spaces)
  - Another nested item
- Third item
```

**Ordered Lists**:
```markdown
1. First step
2. Second step
3. Third step
```

**Checklists**:
```markdown
- [ ] Incomplete task
- [x] Completed task
- [ ] Another incomplete task
```

### Code Blocks

**Inline Code**: Use backticks for `variable names`, `function_names()`, `file_paths`

**Code Blocks**: Use triple backticks with language identifier
````markdown
```bash
#!/bin/bash
echo "Example bash code"
```

```python
def example_function():
    return "Example Python code"
```

```php
<?php
// Example PHP code
function example_function() {
    return "Example";
}
?>
```
````

### Links

**Internal Links** (to other files):
```markdown
Reference: [Script Saving Protocol](script_saving_protocol.md)
See: `/home/dave/skippy/conversations/git_workflow_protocol.md`
```

**External Links**:
```markdown
Documentation: [WordPress Codex](https://codex.wordpress.org/)
```

**Anchors** (within same document):
```markdown
See [Installation Section](#installation)

## Installation
```

### Emphasis

```markdown
**Bold** for important terms, **WARNING**, **IMPORTANT**
*Italic* for emphasis or quotes
`Code` for technical terms, file names, commands
```

### Tables

```markdown
| Column 1      | Column 2      | Column 3      |
|---------------|---------------|---------------|
| Row 1 Data    | Row 1 Data    | Row 1 Data    |
| Row 2 Data    | Row 2 Data    | Row 2 Data    |
```

Keep tables simple. For complex data, consider using code blocks or lists instead.

### Horizontal Rules

Use `---` for section separators:
```markdown
## Section 1

Content...

---

## Section 2

Content...
```

---

## README Standards

Every project, package, or directory should have a `readme.md` file.

### README Template

```markdown
# Project/Package Name

**Version**: 1.0.0
**Date**: 2025-10-28
**Purpose**: One-line description

## Overview

Brief description of what this project/package does and why it exists.

## Contents

- File/directory listing with brief descriptions
- What's included in this package

## Requirements

### System Requirements
- Operating system
- Software dependencies
- Minimum versions

### Dependencies
- List all dependencies
- Include version requirements

## Installation

### Quick Install
```bash
# One-liner or simple installation
```

### Detailed Installation
Step-by-step installation instructions

## Usage

### Basic Usage
```bash
# Simple example
```

### Advanced Usage
```bash
# More complex examples
```

### Examples
Common use cases with full examples

## Configuration

How to configure (if applicable)

## Troubleshooting

Common issues and solutions

## Version History

### v1.0.0 (2025-10-28)
- Initial release
- Feature list

## Support

How to get help

## License

License information (if applicable)
```

---

## Code Documentation Standards

### Script Headers

**Every script must include**:

```bash
#!/bin/bash
################################################################################
# Script Name:  descriptive_script_name_v1.0.0.sh
# Version:      1.0.0
# Date:         2025-10-28
# Author:       Claude Code / Dave Biggers
# Description:  Brief description of what this script does
#
# Usage:        ./script_name.sh [options] [arguments]
#               ./script_name.sh --help
#
# Examples:     ./script_name.sh --input file.txt
#               ./script_name.sh --verbose --output results.txt
#
# Requirements: - Bash 4.0+
#               - wp-cli (for WordPress scripts)
#               - Additional tools
#
# Exit Codes:   0 - Success
#               1 - General error
#               2 - Missing dependency
#               3 - Invalid arguments
#
# Notes:        - Important notes about usage
#               - Caveats or warnings
#               - Known limitations
################################################################################
```

### Python Script Headers

```python
#!/usr/bin/env python3
"""
Script Name:  descriptive_script_name_v1.0.0.py
Version:      1.0.0
Date:         2025-10-28
Author:       Claude Code / Dave Biggers
Description:  Brief description of what this script does

Usage:
    python3 script_name.py [options] [arguments]
    python3 script_name.py --help

Examples:
    python3 script_name.py --input file.txt
    python3 script_name.py --verbose --output results.txt

Requirements:
    - Python 3.8+
    - pandas
    - requests

Exit Codes:
    0 - Success
    1 - General error
    2 - Missing dependency
    3 - Invalid arguments
"""
```

### Function Documentation

**Bash Functions**:
```bash
################################################################################
# Function:     backup_database
# Description:  Creates a backup of the specified database
# Arguments:    $1 - Database name
#               $2 - Output file path (optional)
# Returns:      0 on success, 1 on failure
# Outputs:      Backup file path on success, error message on stderr on failure
################################################################################
backup_database() {
    local db_name="$1"
    local output_file="${2:-backup_$(date +%Y%m%d_%H%M%S).sql}"

    # Function implementation...
}
```

**Python Functions**:
```python
def backup_database(db_name: str, output_file: str = None) -> str:
    """
    Creates a backup of the specified database.

    Args:
        db_name (str): Name of the database to backup
        output_file (str, optional): Path for backup file.
            Defaults to timestamped filename.

    Returns:
        str: Path to the created backup file

    Raises:
        DatabaseError: If database connection fails
        IOError: If unable to write backup file

    Example:
        >>> backup_database('wordpress_db')
        '/backups/wordpress_db_20251028_1430.sql'
    """
    # Function implementation...
```

### Inline Comments

**Do Comment**:
```bash
# Convert local URLs to production URLs for deployment
wp search-replace 'http://rundaverun-local.local' 'https://rundaverun.org' \
    --all-tables --allow-root

# GoDaddy uses custom table prefix, verify before operations
if [[ "$WP_TABLE_PREFIX" != "wp_7e1ce15f22_" ]]; then
    echo "Error: Wrong table prefix detected"
    exit 1
fi
```

**Don't Over-Comment**:
```bash
# BAD: Obvious comments
i=0  # Set i to 0
i=$((i + 1))  # Increment i

# GOOD: Meaningful comments
i=0  # Counter for processed files
i=$((i + 1))  # Move to next file
```

### TODO/FIXME/NOTE Comments

```bash
# TODO: Add error handling for network failures
# FIXME: Race condition when multiple instances run
# NOTE: This workaround is needed due to GoDaddy limitation
# WARNING: This operation is destructive, cannot be undone
```

**Rules**:
- Always include date: `# TODO (2025-10-28): Add feature`
- Include context: `# FIXME: Fails on files > 2GB due to memory limit`
- Track in issue tracker if appropriate
- Remove when resolved

---

## Protocol Documentation Standards

Protocols are specialized documentation for workflows and procedures.

### Protocol File Structure

```markdown
# Protocol Name

**Date Created**: YYYY-MM-DD
**Date Updated**: YYYY-MM-DD (if updated)
**Purpose**: What this protocol covers
**Applies To**: What situations/tasks this protocol applies to
**Priority**: CRITICAL/HIGH/MEDIUM/LOW (How often used / how important)

## Overview

2-3 paragraphs explaining:
- What this protocol is for
- When to use it
- What problems it solves

## Core Principles

List the fundamental principles/rules:
✅ DO: ...
✅ DO: ...
❌ DON'T: ...
❌ DON'T: ...

---

## Main Content Sections

Organized step-by-step or by category

### Section 1

### Section 2

---

## Quick Reference

Summary or quick-lookup information

---

## Integration with Other Protocols

### With [Protocol Name]
Reference: `/path/to/protocol.md`
- How this integrates
- Cross-references

---

**This protocol is part of the persistent memory system.**
**Reference when [situation].**
```

### Protocol Naming

```
[topic]_[type]_protocol.md

Examples:
script_saving_protocol.md
error_logging_protocol.md
wordpress_maintenance_protocol.md
backup_strategy_protocol.md
```

---

## Error Log Documentation Standards

Reference: `/home/dave/skippy/conversations/error_logging_protocol.md`

### Error Log File Structure

```markdown
# Error Log: [Brief Description]

**Date**: YYYY-MM-DD HH:MM
**Task**: [What you were trying to do]
**Severity**: [Critical/High/Medium/Low]

## Error Details

### Error Message
```
[Exact error message]
```

### Environment
- **Location**: Local / Production
- **OS**: [Operating system]
- **Related Software**: [WordPress version, PHP version, etc.]

### Reproduction Steps
1. Step 1
2. Step 2
3. Error occurs

## Investigation

### What Was Tried
1. Attempt 1: [What was tried] → Result: [Success/Failure]
2. Attempt 2: [What was tried] → Result: [Success/Failure]

## Solution

### What Fixed It
[Detailed explanation]

### Root Cause
[Why the problem occurred]

### Prevention
[How to prevent in the future]

## References
- Protocol: [Link to relevant protocol]
- Similar Issue: [Link to similar error log]
```

---

## User Guide Documentation Standards

User guides explain how to use features or systems.

### User Guide Structure

```markdown
# [Feature/System] User Guide

**Version**: 1.0.0
**Date**: 2025-10-28
**Audience**: [Who this guide is for]
**Skill Level**: Beginner / Intermediate / Advanced

## Introduction

What this guide covers and who it's for.

## Prerequisites

- Required knowledge
- Required tools
- Required access

## Getting Started

### Quick Start
Fastest way to get started (for experienced users)

### Detailed Setup
Step-by-step for beginners

## Basic Usage

### Task 1: [Task Name]

**Goal**: What you'll accomplish

**Steps**:
1. Step one
2. Step two
3. Step three

**Example**:
```bash
# Concrete example
```

**Expected Result**: What should happen

### Task 2: [Task Name]

[Same structure]

## Advanced Usage

### Advanced Task 1

[Same structure]

## Troubleshooting

### Problem 1: [Description]
**Symptoms**: What you'll see
**Cause**: Why it happens
**Solution**: How to fix

### Problem 2: [Description]
[Same structure]

## Frequently Asked Questions (FAQ)

### Question 1?
Answer...

### Question 2?
Answer...

## Reference

Quick reference tables, commands, etc.

## Additional Resources

- [Link to related guides]
- [Link to protocols]
- [External documentation]
```

---

## API Documentation Standards

For scripts/tools that function as APIs or libraries.

### API Documentation Structure

```markdown
# [API/Library Name] Reference

**Version**: 1.0.0
**Date**: 2025-10-28

## Overview

What this API/library does.

## Installation

How to install/include

## Quick Start

```bash
# Simple example
```

## Functions/Commands

### function_name

**Description**: What this function does

**Syntax**:
```bash
function_name [required_arg] [optional_arg]
```

**Parameters**:
- `required_arg` (type): Description
- `optional_arg` (type, optional): Description. Default: value

**Returns**:
- (type): Description of return value

**Exit Codes** (for scripts):
- 0: Success
- 1: Error type 1
- 2: Error type 2

**Example**:
```bash
function_name "input" "optional"
# Output: expected result
```

**Errors**:
- Error type 1: Cause and solution
- Error type 2: Cause and solution

### Next function...

[Same structure]

## Advanced Usage

More complex examples

## Troubleshooting

Common issues
```

---

## Version History Documentation

### CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/) standard:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Features in development

### Changed
- Changes in development

## [1.0.0] - 2025-10-28

### Added
- New feature 1
- New feature 2

### Changed
- Changed behavior 1
- Updated dependency X from 1.0 to 2.0

### Deprecated
- Feature Y will be removed in 2.0.0

### Removed
- Removed deprecated feature Z

### Fixed
- Fixed bug where X happened
- Fixed security issue Y

### Security
- Security improvement 1
```

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

Example: 1.2.3
- MAJOR (1): Incompatible API changes
- MINOR (2): Backwards-compatible new features
- PATCH (3): Backwards-compatible bug fixes
```

**When to increment**:
- **MAJOR**: Breaking changes, removed features
- **MINOR**: New features, no breaking changes
- **PATCH**: Bug fixes only

---

## Comment Standards for Different Languages

### Bash/Shell Scripts

```bash
#!/bin/bash

# Single-line comment

# Multi-line comment:
# Line 1
# Line 2

################################################################################
# Section header or important comment block
################################################################################

# Function documentation (see earlier section)
```

### Python

```python
#!/usr/bin/env python3

# Single-line comment

"""
Multi-line comment (docstring)
Used for module, class, and function documentation
"""

# TODO: Task description
# FIXME: Problem description
# NOTE: Important note
```

### PHP (WordPress)

```php
<?php
/**
 * File documentation header
 *
 * @package    PackageName
 * @subpackage SubpackageName
 * @author     Author Name
 * @license    GPL-2.0+
 * @link       https://example.com
 */

// Single-line comment

/**
 * Function documentation
 *
 * @param  string $param1 Description of parameter
 * @param  array  $param2 Description of parameter
 * @return bool           Description of return value
 */
function example_function( $param1, $param2 ) {
    // Function implementation
}
?>
```

### HTML

```html
<!-- Single-line comment -->

<!--
  Multi-line comment
  Line 2
  Line 3
-->

<!-- Section: Header -->
<!-- End Section: Header -->
```

### CSS

```css
/* Single-line comment */

/**
 * Multi-line comment
 * Section header
 */

/* Component: Navigation Menu */
.nav-menu {
    /* Comment about this rule */
}
```

### JavaScript

```javascript
// Single-line comment

/**
 * Multi-line comment / JSDoc
 * Function documentation
 *
 * @param {string} param1 - Description
 * @param {number} param2 - Description
 * @returns {boolean} Description
 */
function exampleFunction(param1, param2) {
    // Function implementation
}

// TODO: Task
// FIXME: Problem
// NOTE: Important note
```

---

## Documentation Maintenance

### When to Update Documentation

**ALWAYS update documentation when**:
- ✅ Code behavior changes
- ✅ New features added
- ✅ Bugs fixed that affect usage
- ✅ Configuration changes
- ✅ Dependencies change
- ✅ Breaking changes occur

**Document immediately, not later**

### Documentation Review Schedule

**Monthly**:
- [ ] Review README files for accuracy
- [ ] Update version numbers if needed
- [ ] Check for broken links
- [ ] Update examples if APIs changed

**Quarterly**:
- [ ] Comprehensive protocol review
- [ ] Update Quick Reference sections
- [ ] Consolidate similar documents
- [ ] Remove outdated information

**After Major Changes**:
- [ ] Update all affected documentation
- [ ] Update CHANGELOG
- [ ] Update version numbers
- [ ] Test all examples

### Documentation Quality Checklist

Before considering documentation complete:

- [ ] **Accuracy**: Information is correct and current
- [ ] **Completeness**: All necessary information included
- [ ] **Clarity**: Easy to understand
- [ ] **Examples**: Concrete examples provided
- [ ] **Organization**: Logical structure
- [ ] **Formatting**: Consistent markdown formatting
- [ ] **Links**: All links work (internal and external)
- [ ] **Code blocks**: All code blocks have language specified
- [ ] **Grammar**: Spell-checked and grammatically correct
- [ ] **Audience**: Appropriate for target audience

---

## Documentation Anti-Patterns

### Don't Do These

❌ **Outdated Documentation**
```markdown
# BAD: Documentation that's years old
Last Updated: 2020-01-01
[Information about version 1.0, but we're on 3.0 now]
```

❌ **Unclear Purpose**
```markdown
# BAD: No explanation of what this is for
# Some Script
Here are some commands...
```

❌ **Missing Examples**
```markdown
# BAD: Explanation without examples
This function processes data according to algorithm X.
[No examples showing what data looks like or how to use it]
```

❌ **Assuming Knowledge**
```markdown
# BAD: Using jargon without explanation
Run the CRON job to sync the ORM entities via REST API.
[Assumes reader knows what all these terms mean]
```

❌ **Wall of Text**
```markdown
# BAD: No structure, no headings, no formatting
This is a very long paragraph that explains everything in one
giant block of text with no structure or organization making it
very difficult to scan or find specific information...
[50 more lines of unbroken text]
```

❌ **Broken Links**
```markdown
# BAD: Links that don't work
See the [Installation Guide](installation.md)
[But installation.md doesn't exist]
```

### Do These Instead

✅ **Keep Documentation Current**
```markdown
# GOOD: Clear dates and versions
Last Updated: 2025-10-28
Version: 3.0.0
```

✅ **State Purpose Clearly**
```markdown
# GOOD: Clear purpose statement
**Purpose**: This script backs up WordPress databases and provides
automatic restoration capabilities for disaster recovery.
```

✅ **Provide Examples**
```markdown
# GOOD: Concrete examples
**Example**:
```bash
./backup.sh --database wordpress_db --output /backups/
# Output: backup_wordpress_db_20251028_1430.sql
```
```

✅ **Define Terms**
```markdown
# GOOD: Explain jargon
Run the CRON job (scheduled task) to sync the ORM (Object-Relational
Mapping) entities via REST API (web service).
```

✅ **Use Structure**
```markdown
# GOOD: Organized with headers and lists
## Installation

### Requirements
- Bash 4.0+
- WP-CLI

### Steps
1. Step one
2. Step two
```

✅ **Verify Links**
```markdown
# GOOD: Working links
See the [Installation Guide](installation_guide.md)
[Verify installation_guide.md exists]
```

---

## Documentation Templates

### Quick Reference Card Template

```markdown
# [Topic] Quick Reference

**Version**: 1.0.0
**Date**: 2025-10-28

## Common Commands

```bash
# Description of command
command --option argument

# Description of command 2
command2 --option argument
```

## Keyboard Shortcuts

| Shortcut      | Action           |
|---------------|------------------|
| Ctrl+C        | Copy             |
| Ctrl+V        | Paste            |

## Common Patterns

### Pattern 1: [Name]
```bash
# Example code
```

### Pattern 2: [Name]
```bash
# Example code
```

## Troubleshooting Quick Fixes

**Problem**: Description
**Fix**: `command to fix`

## Reference Links

- [Protocol Name](protocol_file.md)
- [External Docs](https://example.com)
```

### Installation Guide Template

```markdown
# [Project] Installation Guide

**Version**: 1.0.0
**Date**: 2025-10-28

## Prerequisites

### System Requirements
- Operating System: ...
- Minimum RAM: ...
- Disk Space: ...

### Software Requirements
- Dependency 1: Version X.X+
- Dependency 2: Version Y.Y+

## Quick Installation

```bash
# One-liner or simple install
curl -sSL install.sh | bash
```

## Detailed Installation

### Step 1: Prepare System

```bash
# Commands for step 1
```

### Step 2: Install Dependencies

```bash
# Commands for step 2
```

### Step 3: Install Application

```bash
# Commands for step 3
```

### Step 4: Configure

Edit `config.example.sh`:
```bash
# Configuration
```

### Step 5: Verify Installation

```bash
# Verification commands
```

## Post-Installation

### Optional Features
- Feature 1: How to enable
- Feature 2: How to enable

### Next Steps
1. What to do next
2. Where to go from here

## Troubleshooting Installation

### Issue 1: [Description]
**Symptoms**: ...
**Solution**: ...

### Issue 2: [Description]
**Symptoms**: ...
**Solution**: ...

## Uninstallation

```bash
# How to uninstall if needed
```
```

---

## Integration with Other Protocols

### With Script Saving Protocol
Reference: `/home/dave/skippy/conversations/script_saving_protocol.md`
- All scripts must have complete documentation headers
- README required for script directories
- Version numbers must match

### With Error Logging Protocol
Reference: `/home/dave/skippy/conversations/error_logging_protocol.md`
- Error logs follow standardized format
- Documentation updated with solutions
- Prevention measures documented

### With Package Creation Protocol
Reference: `/home/dave/skippy/conversations/package_creation_protocol.md`
- All packages must include README
- Documentation standards apply to package docs
- Version history required

### With Git Workflow Protocol
Reference: `/home/dave/skippy/conversations/git_workflow_protocol.md`
- Commit messages are documentation
- Update docs in same commit as code changes
- CHANGELOG updated with each release

---

## Quick Reference

### Essential Documentation Files

**Every project needs**:
- `readme.md` - Project overview
- `changelog.md` - Version history
- `license.md` - License (if applicable)

**Packages need**:
- `readme.md` - Package overview
- `install.md` or installation section
- Usage examples

**Scripts need**:
- Complete header with version, usage, examples
- Inline comments for complex logic
- Function documentation

### Documentation Checklist

- [ ] File name follows conventions (lowercase, underscores)
- [ ] Document has clear title and date
- [ ] Purpose stated clearly
- [ ] Proper heading hierarchy (H1 → H2 → H3)
- [ ] Code blocks have language specified
- [ ] Examples provided
- [ ] Links verified (work correctly)
- [ ] Spell-checked and grammatically correct
- [ ] Organized logically
- [ ] Quick reference section (if appropriate)

### Common Markdown Syntax

```markdown
**Bold**
*Italic*
`code`
[Link](url)
![Image](url)

# Heading 1
## Heading 2
### Heading 3

- Bullet list

1. Numbered list

- [ ] Checklist

```code block```

> Quote

---

Horizontal rule

| Table | Header |
|-------|--------|
| Cell  | Cell   |
```

---

**This protocol is part of the persistent memory system.**
**Reference when creating or updating any documentation.**
```
