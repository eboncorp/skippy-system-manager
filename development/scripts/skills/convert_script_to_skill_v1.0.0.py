#!/usr/bin/env python3
"""
Script to Skill Converter v1.0.0
Converts scripts/workflows into Claude Code Skills
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, Optional

class ScriptToSkillConverter:
    def __init__(self, skills_dir: str = "~/.claude/skills"):
        self.skills_dir = Path(skills_dir).expanduser()

    def analyze_script(self, script_path: Path) -> Dict:
        """Extract information from script for skill creation"""
        content = script_path.read_text()
        lines = content.split('\n')

        # Extract description from comments/docstring
        description = ""
        usage_info = []

        for i, line in enumerate(lines[:100]):
            # Python docstring
            if ('"""' in line or "'''" in line) and i < 20:
                doc_lines = []
                in_doc = True
                for j in range(i+1, min(i+20, len(lines))):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        break
                    doc_lines.append(lines[j].strip())
                description = ' '.join(doc_lines[:3])
                break

            # Bash comments
            if line.strip().startswith('#') and not line.startswith('#!'):
                comment = line.strip('# ').strip()
                if len(comment) > 20 and not comment.startswith('='):
                    if not description and 'usage' not in comment.lower():
                        description = comment
                    if 'usage' in comment.lower() or 'how to' in comment.lower():
                        usage_info.append(comment)

        # Extract functions for usage examples
        functions = re.findall(r'(?:def|function)\s+(\w+)\s*\(', content)

        return {
            'description': description or f"Provides {script_path.stem.replace('_', ' ')} functionality",
            'functions': functions[:10],  # Top 10 functions
            'usage_info': usage_info,
            'has_config': 'config' in content.lower() and ('yaml' in content.lower() or 'json' in content.lower()),
            'is_daemon': 'daemon' in content.lower() or 'service' in content.lower(),
            'is_interactive': 'input(' in content or 'prompt' in content.lower()
        }

    def generate_skill_content(self, script_path: Path, skill_name: str, analysis: Dict) -> str:
        """Generate SKILL.md content"""

        description = analysis['description'][:200]

        content = f"""---
name: {skill_name}
description: {description}
---

# {skill_name.replace('-', ' ').title()}

**Script:** `{script_path.name}`
**Location:** `{script_path}`

## When to Use This Skill

This skill should be automatically invoked when:
- User mentions {skill_name.replace('-', ' ')}
- Working with {script_path.stem.replace('_', ' ')} tasks
- Need to {description.lower()}

## Quick Start

### Basic Usage

```bash
{script_path}
```

"""

        # Add function reference if available
        if analysis['functions']:
            content += "### Available Functions\n\n"
            for func in analysis['functions'][:5]:
                content += f"- `{func}()`\n"
            content += "\n"

        # Configuration section if applicable
        if analysis['has_config']:
            content += """## Configuration

This script uses configuration files. Check the script for:
- Configuration file locations
- Required settings
- Environment variables

"""

        # Service management if daemon
        if analysis['is_daemon']:
            content += """## Service Management

This is a daemon/service script:

```bash
# Start
sudo systemctl start {script}

# Stop
sudo systemctl stop {script}

# Status
sudo systemctl status {script}
```

"""

        # Examples section
        content += """## Examples

### Example 1: Basic execution

```bash
# Run the script
{script}
```

### Example 2: With options

```bash
# Check status
{script} status

# Run with verbose output
{script} --verbose
```

## Troubleshooting

**Common issues:**
1. Permission denied → Check file permissions with `ls -la {script}`
2. Module not found → Install requirements: `pip install -r requirements.txt`
3. Service fails → Check logs: `journalctl -u {script} -n 50`

## Best Practices

1. **Before running:** Review the script to understand what it does
2. **Backups:** Ensure backups exist before running destructive operations
3. **Testing:** Test in non-production first when possible
4. **Monitoring:** Watch logs during execution

## Resources

- Script location: `{path}`
- Related documentation: Check script header comments
"""

        return content.replace('{script}', script_path.name).replace('{path}', str(script_path))

    def create_skill(self, script_path: Path, skill_name: str, dry_run: bool = False) -> tuple:
        """Create a skill from a script"""

        # Check if skill already exists
        skill_dir = self.skills_dir / skill_name
        if skill_dir.exists():
            return False, f"Skill already exists: {skill_name}"

        # Analyze script
        try:
            analysis = self.analyze_script(script_path)
        except Exception as e:
            return False, f"Failed to analyze script: {e}"

        # Generate skill content
        skill_content = self.generate_skill_content(script_path, skill_name, analysis)

        if dry_run:
            return True, f"Would create skill: {skill_name}"

        # Create skill directory and file
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(skill_content)

        # Copy script to skill directory as reference
        script_copy = skill_dir / script_path.name
        shutil.copy2(script_path, script_copy)

        return True, f"✅ Created skill: {skill_name}"

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Convert script to Claude Code Skill")
    parser.add_argument('script_path', help="Path to script file")
    parser.add_argument('--skill-name', help="Skill name (auto-generated if not provided)")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be done")

    args = parser.parse_args()

    script_path = Path(args.script_path)
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    # Generate skill name
    if args.skill_name:
        skill_name = args.skill_name
    else:
        # Auto-generate from filename
        name = re.sub(r'_v\d+\.\d+\.\d+', '', script_path.stem)
        skill_name = name.replace('_', '-')

    converter = ScriptToSkillConverter()
    success, message = converter.create_skill(script_path, skill_name, args.dry_run)

    print(message)

    if success and not args.dry_run:
        print(f"\n📄 Skill created at: ~/.claude/skills/{skill_name}/SKILL.md")
        print(f"🔧 Review and customize the skill before using it")
