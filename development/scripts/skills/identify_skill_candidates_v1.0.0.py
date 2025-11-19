#!/usr/bin/env python3
"""
Skill Candidate Identifier v1.0.0
Identifies scripts/workflows that should be converted to Skills
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

class SkillCandidateAnalyzer:
    def __init__(self, scripts_dir: str = "/home/dave/skippy/development/scripts",
                 projects_dir: str = "/home/dave/skippy/development/projects"):
        self.scripts_dir = Path(scripts_dir)
        self.projects_dir = Path(projects_dir)
        self.existing_skills = self._load_existing_skills()

    def _load_existing_skills(self) -> set:
        """Load names of existing skills"""
        skills_dir = Path("~/.claude/skills").expanduser()
        return {skill.name for skill in skills_dir.iterdir() if skill.is_dir()}

    def analyze_script(self, script_path: Path) -> Dict:
        """Analyze a script for skill candidacy"""
        try:
            content = script_path.read_text()
        except:
            return None

        # Extract metadata from comments
        description = ""
        purpose = ""

        lines = content.split('\n')[:50]  # First 50 lines
        for line in lines:
            if re.search(r'#.*Description:', line, re.I):
                description = line.split(':', 1)[1].strip()
            elif re.search(r'#.*Purpose:', line, re.I):
                purpose = line.split(':', 1)[1].strip()
            elif line.startswith('"""') or line.startswith("'''"):
                # Python docstring
                desc_lines = []
                for i, l in enumerate(lines):
                    if i > 0 and ('"""' in l or "'''" in l):
                        break
                    desc_lines.append(l.strip())
                description = ' '.join(desc_lines[:3])
                break

        # Score based on characteristics
        score = 0
        reasons = []

        # High score: Complex workflows
        if 'workflow' in content.lower() or 'pipeline' in content.lower():
            score += 3
            reasons.append("Contains workflow/pipeline logic")

        # High score: Multi-step processes
        function_count = len(re.findall(r'def \w+\(|function \w+\(', content))
        if function_count > 5:
            score += 3
            reasons.append(f"Complex ({function_count} functions)")

        # Medium score: Configuration management
        if 'config' in content.lower() and 'yaml' in content.lower():
            score += 2
            reasons.append("Uses configuration files")

        # Medium score: External tool orchestration
        if 'subprocess' in content or 'docker' in content or 'systemctl' in content:
            score += 2
            reasons.append("Orchestrates external tools")

        # High score: Frequently used patterns
        if script_path.name.startswith('nexus_') or 'status' in script_path.name:
            score += 2
            reasons.append("Core infrastructure script")

        # Medium score: Has error handling
        if 'try:' in content and 'except' in content:
            score += 1
            reasons.append("Has error handling")

        # Size matters
        lines_count = len(content.split('\n'))
        if lines_count > 200:
            score += 2
            reasons.append(f"Substantial size ({lines_count} lines)")

        return {
            'path': script_path,
            'name': script_path.name,
            'score': score,
            'reasons': reasons,
            'description': description or purpose,
            'size': lines_count
        }

    def identify_candidates(self) -> Dict[str, List[Dict]]:
        """Identify all skill candidates"""
        candidates = defaultdict(list)

        # Analyze scripts
        for script_path in self.scripts_dir.rglob("*.sh"):
            if 'archive' in str(script_path) or '__pycache__' in str(script_path):
                continue

            analysis = self.analyze_script(script_path)
            if analysis and analysis['score'] >= 3:
                candidates['high_value_scripts'].append(analysis)
            elif analysis and analysis['score'] >= 1:
                candidates['medium_value_scripts'].append(analysis)

        for script_path in self.scripts_dir.rglob("*.py"):
            if 'archive' in str(script_path) or '__pycache__' in str(script_path):
                continue
            if script_path.name.startswith('test_'):
                continue

            analysis = self.analyze_script(script_path)
            if analysis and analysis['score'] >= 3:
                candidates['high_value_scripts'].append(analysis)
            elif analysis and analysis['score'] >= 1:
                candidates['medium_value_scripts'].append(analysis)

        # Sort by score
        for category in candidates:
            candidates[category].sort(key=lambda x: x['score'], reverse=True)

        return candidates

    def suggest_skill_name(self, script_name: str) -> str:
        """Suggest a skill name from script name"""
        # Remove version numbers
        name = re.sub(r'_v\d+\.\d+\.\d+', '', script_name)
        # Remove extension
        name = name.rsplit('.', 1)[0]
        # Clean up
        name = name.replace('_', '-')
        return name

    def generate_report(self, candidates: Dict[str, List[Dict]]) -> str:
        """Generate candidate report"""
        report = []
        report.append("=" * 80)
        report.append("SKILL CANDIDATE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # High value candidates
        high_value = candidates.get('high_value_scripts', [])
        report.append(f"🔥 HIGH VALUE CANDIDATES (Score >= 3): {len(high_value)}")
        report.append("-" * 80)

        for i, candidate in enumerate(high_value[:15], 1):  # Top 15
            suggested_name = self.suggest_skill_name(candidate['name'])
            existing = "⚠️  ALREADY EXISTS" if suggested_name in self.existing_skills else ""

            report.append(f"\n{i}. {candidate['name']} (Score: {candidate['score']}) {existing}")
            report.append(f"   Suggested Skill: {suggested_name}")
            report.append(f"   Path: {candidate['path']}")
            report.append(f"   Reasons:")
            for reason in candidate['reasons']:
                report.append(f"     • {reason}")
            if candidate['description']:
                report.append(f"   Description: {candidate['description'][:100]}")

        # Medium value candidates
        report.append("\n\n" + "=" * 80)
        medium_value = candidates.get('medium_value_scripts', [])
        report.append(f"📋 MEDIUM VALUE CANDIDATES (Score 1-2): {len(medium_value)}")
        report.append(f"(Showing top 10)")
        report.append("-" * 80)

        for i, candidate in enumerate(medium_value[:10], 1):
            suggested_name = self.suggest_skill_name(candidate['name'])
            report.append(f"{i}. {candidate['name']} (Score: {candidate['score']}) → {suggested_name}")

        # Projects that could be Skills
        report.append("\n\n" + "=" * 80)
        report.append("🚀 PROJECTS TO CONSIDER")
        report.append("-" * 80)

        for project in self.projects_dir.iterdir():
            if project.is_dir() and not project.name.startswith('.'):
                suggested_name = project.name.replace('_', '-')
                existing = "✅ Has skill" if suggested_name in self.existing_skills else "❌ No skill yet"
                report.append(f"• {project.name} → {suggested_name} {existing}")

        # Summary
        report.append("\n\n" + "=" * 80)
        report.append("SUMMARY")
        report.append("=" * 80)
        report.append(f"Existing Skills: {len(self.existing_skills)}")
        report.append(f"High-value candidates: {len(high_value)}")
        report.append(f"Medium-value candidates: {len(medium_value)}")
        report.append("")
        report.append("💡 RECOMMENDATION: Start with top 5 high-value candidates")

        return "\n".join(report)

if __name__ == "__main__":
    analyzer = SkillCandidateAnalyzer()

    print("Analyzing scripts and workflows...")
    print("This may take a minute...\n")

    candidates = analyzer.identify_candidates()
    report = analyzer.generate_report(candidates)

    print(report)

    # Save report
    output_path = Path("/home/dave/skippy/documentation/conversations/skill_candidates_analysis_2025-11-18.md")
    output_path.write_text(report)
    print(f"\n📄 Report saved to: {output_path}")
