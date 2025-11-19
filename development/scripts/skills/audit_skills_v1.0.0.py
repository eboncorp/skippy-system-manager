#!/usr/bin/env python3
"""
Skill Audit Tool v1.0.0
Audits Claude Code Skills for proper YAML frontmatter structure
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

class SkillAuditor:
    def __init__(self, skills_dir: str = "~/.claude/skills"):
        self.skills_dir = Path(skills_dir).expanduser()
        self.issues = []

    def audit_all_skills(self) -> Dict[str, List[str]]:
        """Audit all skills and return issues"""
        results = {}

        for skill_path in sorted(self.skills_dir.glob("*/SKILL.md")):
            skill_name = skill_path.parent.name
            issues = self.audit_skill(skill_path)
            if issues:
                results[skill_name] = issues

        return results

    def audit_skill(self, skill_path: Path) -> List[str]:
        """Audit a single skill file"""
        issues = []

        try:
            content = skill_path.read_text()
        except Exception as e:
            return [f"Cannot read file: {e}"]

        # Check for YAML frontmatter
        if not content.startswith('---'):
            issues.append("Missing YAML frontmatter opening '---'")
            return issues  # Can't check further without frontmatter

        # Extract frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            issues.append("Missing YAML frontmatter closing '---'")
            return issues

        frontmatter = parts[1]
        body = parts[2]

        # Check required fields
        if not re.search(r'^name:\s*.+$', frontmatter, re.MULTILINE):
            issues.append("Missing required 'name:' field")
        else:
            # Validate name format
            name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
            if name_match:
                name = name_match.group(1).strip()
                if len(name) > 64:
                    issues.append(f"Name too long ({len(name)} chars, max 64)")
                if not re.match(r'^[a-z0-9-]+$', name):
                    issues.append("Name must be lowercase letters, numbers, and hyphens only")
                if 'anthropic' in name.lower() or 'claude' in name.lower():
                    issues.append("Name contains reserved word (anthropic/claude)")

        if not re.search(r'^description:\s*.+$', frontmatter, re.MULTILINE):
            issues.append("Missing required 'description:' field")
        else:
            # Validate description
            desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
            if desc_match:
                desc = desc_match.group(1).strip()
                if len(desc) > 1024:
                    issues.append(f"Description too long ({len(desc)} chars, max 1024)")
                if '<' in desc and '>' in desc:
                    issues.append("Description may contain XML tags")

        # Check body content
        if not body.strip():
            issues.append("Empty skill body (no instructions)")

        return issues

    def generate_report(self, results: Dict[str, List[str]]) -> str:
        """Generate audit report"""
        total_skills = len(list(self.skills_dir.glob("*/SKILL.md")))
        problem_skills = len(results)

        report = []
        report.append("=" * 70)
        report.append("SKILL AUDIT REPORT")
        report.append("=" * 70)
        report.append(f"Total Skills: {total_skills}")
        report.append(f"Skills with Issues: {problem_skills}")
        report.append(f"Skills OK: {total_skills - problem_skills}")
        report.append("")

        if not results:
            report.append("✅ All skills have proper YAML frontmatter structure!")
            return "\n".join(report)

        report.append("⚠️  ISSUES FOUND:")
        report.append("")

        for skill_name, issues in sorted(results.items()):
            report.append(f"❌ {skill_name}")
            for issue in issues:
                report.append(f"   - {issue}")
            report.append("")

        return "\n".join(report)

    def suggest_fixes(self, skill_name: str, skill_path: Path) -> str:
        """Suggest frontmatter for a skill"""
        # Generate name from directory
        suggested_name = skill_path.parent.name

        # Try to extract description from content
        try:
            content = skill_path.read_text()
            # Look for first heading or paragraph
            lines = content.split('\n')
            description = ""
            for line in lines[:20]:
                if line.startswith('##'):
                    description = line.replace('#', '').strip()
                    break
                elif line.strip() and not line.startswith('#'):
                    description = line.strip()[:200]
                    break

            if not description:
                description = f"Provides {suggested_name.replace('-', ' ')} capabilities"
        except:
            description = f"Provides {suggested_name.replace('-', ' ')} capabilities"

        return f"""---
name: {suggested_name}
description: {description}
---
"""

if __name__ == "__main__":
    auditor = SkillAuditor()

    print("Auditing skills...")
    results = auditor.audit_all_skills()

    print(auditor.generate_report(results))

    if results:
        print("\n" + "=" * 70)
        print("SUGGESTED FIXES")
        print("=" * 70)
        print("\nExample frontmatter for first 5 problematic skills:")
        print("(Customize descriptions based on actual content)\n")

        for i, (skill_name, issues) in enumerate(sorted(results.items())[:5]):
            skill_path = auditor.skills_dir / skill_name / "SKILL.md"
            print(f"--- {skill_name} ---")
            print(auditor.suggest_fixes(skill_name, skill_path))
