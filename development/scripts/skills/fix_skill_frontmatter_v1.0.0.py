#!/usr/bin/env python3
"""
Skill Frontmatter Fixer v1.0.0
Automatically adds proper YAML frontmatter to Claude Code Skills
"""

import os
import re
from pathlib import Path
from typing import Dict, Tuple

class SkillFixer:
    def __init__(self, skills_dir: str = "~/.claude/skills"):
        self.skills_dir = Path(skills_dir).expanduser()
        self.backup_dir = Path("~/.claude/skills_backup").expanduser()

    def extract_description(self, content: str, skill_name: str) -> str:
        """Extract or generate description from skill content"""
        lines = content.split('\n')

        # Look for "When to Use" section
        for i, line in enumerate(lines):
            if 'when to use' in line.lower() or 'auto-invoke' in line.lower():
                # Get next few lines
                desc_lines = []
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip() and not lines[j].startswith('#'):
                        desc_lines.append(lines[j].strip('- ').strip())
                        if len(' '.join(desc_lines)) > 100:
                            break
                if desc_lines:
                    desc = ' '.join(desc_lines)[:200]
                    return desc

        # Look for first paragraph
        for line in lines[:30]:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('**') and len(line) > 30:
                # Clean up
                line = re.sub(r'\*\*.*?\*\*', '', line)  # Remove bold
                line = line.strip('- ').strip()
                if len(line) > 20:
                    return line[:200]

        # Fallback: generate from name
        readable_name = skill_name.replace('-', ' ').title()
        return f"Provides {readable_name} capabilities for Claude Code. Use when working with {readable_name.lower()} tasks."

    def fix_skill(self, skill_path: Path, dry_run: bool = False) -> Tuple[bool, str]:
        """Fix a single skill by adding frontmatter"""
        try:
            content = skill_path.read_text()
        except Exception as e:
            return False, f"Cannot read file: {e}"

        # Check if already has frontmatter
        if content.startswith('---'):
            return False, "Already has frontmatter"

        skill_name = skill_path.parent.name
        description = self.extract_description(content, skill_name)

        # Build proper frontmatter
        frontmatter = f"""---
name: {skill_name}
description: {description}
---

"""

        new_content = frontmatter + content

        if dry_run:
            return True, f"Would add frontmatter (description: {description[:80]}...)"

        # Create backup
        backup_path = self.backup_dir / skill_name / "SKILL.md"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(content)

        # Write fixed content
        skill_path.write_text(new_content)

        return True, f"✅ Fixed (backed up to {backup_path})"

    def fix_all_skills(self, dry_run: bool = False) -> Dict[str, str]:
        """Fix all skills"""
        results = {}

        for skill_path in sorted(self.skills_dir.glob("*/SKILL.md")):
            skill_name = skill_path.parent.name
            fixed, message = self.fix_skill(skill_path, dry_run)
            results[skill_name] = message

        return results

if __name__ == "__main__":
    import sys

    fixer = SkillFixer()

    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    if dry_run:
        print("DRY RUN MODE - No files will be modified\n")
    else:
        print("⚠️  This will modify all skill files!")
        print("Backups will be created in ~/.claude/skills_backup/\n")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    print("\nProcessing skills...\n")
    results = fixer.fix_all_skills(dry_run)

    # Print results
    fixed_count = sum(1 for msg in results.values() if msg.startswith("✅") or msg.startswith("Would"))
    skipped_count = len(results) - fixed_count

    for skill_name, message in sorted(results.items()):
        print(f"{skill_name}: {message}")

    print("\n" + "=" * 70)
    print(f"Total Skills: {len(results)}")
    print(f"Fixed: {fixed_count}")
    print(f"Skipped: {skipped_count}")
    if not dry_run and fixed_count > 0:
        print(f"\n✅ Backups saved to: {fixer.backup_dir}")
