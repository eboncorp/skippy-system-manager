#!/usr/bin/env python3
"""
Export Skills to Claude.ai v1.0.0
Converts Claude Code skills to claude.ai-compatible format

This script:
1. Reads all skills from ~/.claude/skills/
2. Validates and truncates name (≤64 chars) and description (≤200 chars)
3. Renames SKILL.md to Skill.md (claude.ai requirement)
4. Creates ZIP packages with correct structure

Usage:
    python3 export_skills_to_claude_ai_v1.0.0.py [--output-dir DIR] [--skill NAME]

Created: 2025-12-07
"""

import os
import sys
import argparse
import zipfile
import shutil
import re
from pathlib import Path
from datetime import datetime

# Configuration
SKILLS_SOURCE = Path.home() / ".claude" / "skills"
DEFAULT_OUTPUT = Path.home() / "skippy" / "operations" / "claude_ai_skills_export"
MAX_NAME_LEN = 64
MAX_DESC_LEN = 200


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from skill content."""
    frontmatter = {}
    body = content

    # Check for YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_section = parts[1].strip()
            body = parts[2].strip()

            # Parse simple YAML
            for line in yaml_section.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()

    return frontmatter, body


def truncate_with_ellipsis(text: str, max_len: int) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def sanitize_name(name: str) -> str:
    """Ensure name meets claude.ai requirements: lowercase, hyphens, max 64 chars."""
    # Already lowercase with hyphens in our skills
    name = name.lower().strip()
    # Remove any invalid characters
    name = re.sub(r'[^a-z0-9-]', '-', name)
    # Collapse multiple hyphens
    name = re.sub(r'-+', '-', name)
    # Trim to 64 chars
    return name[:MAX_NAME_LEN]


def convert_skill(skill_dir: Path, output_dir: Path) -> dict:
    """Convert a single skill to claude.ai format."""
    skill_name = skill_dir.name
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return {"skill": skill_name, "status": "skipped", "reason": "No SKILL.md found"}

    # Read content
    content = skill_file.read_text(encoding="utf-8")
    frontmatter, body = extract_frontmatter(content)

    # Get and validate name
    name = frontmatter.get("name", skill_name)
    original_name = name
    name = sanitize_name(name)
    name_truncated = len(original_name) > MAX_NAME_LEN

    # Get and validate description
    description = frontmatter.get("description", "")
    original_desc_len = len(description)
    description = truncate_with_ellipsis(description, MAX_DESC_LEN)
    desc_truncated = original_desc_len > MAX_DESC_LEN

    # Build new frontmatter
    new_frontmatter = f"---\nname: {name}\ndescription: {description}\n"

    # Add optional fields if present
    if "version" in frontmatter:
        new_frontmatter += f"version: {frontmatter['version']}\n"

    new_frontmatter += "---\n\n"

    # Combine with body
    new_content = new_frontmatter + body

    # Create output structure
    skill_output_dir = output_dir / "individual" / name
    skill_output_dir.mkdir(parents=True, exist_ok=True)

    # Write Skill.md (note: capital S for claude.ai)
    skill_output_file = skill_output_dir / "Skill.md"
    skill_output_file.write_text(new_content, encoding="utf-8")

    # Create ZIP file
    zip_output_dir = output_dir / "zipped"
    zip_output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = zip_output_dir / f"{name}.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add with directory structure: skill-name/Skill.md
        zf.write(skill_output_file, f"{name}/Skill.md")

    return {
        "skill": skill_name,
        "status": "converted",
        "name": name,
        "name_truncated": name_truncated,
        "desc_truncated": desc_truncated,
        "original_desc_len": original_desc_len,
        "zip_path": str(zip_path)
    }


def create_combined_zip(output_dir: Path, skills: list[dict]) -> str:
    """Create a combined ZIP with all skills."""
    combined_zip = output_dir / "all_skills_combined.zip"

    with zipfile.ZipFile(combined_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        individual_dir = output_dir / "individual"
        for skill_dir in individual_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "Skill.md"
                if skill_file.exists():
                    zf.write(skill_file, f"{skill_dir.name}/Skill.md")

    return str(combined_zip)


def main():
    parser = argparse.ArgumentParser(description="Export Claude Code skills to claude.ai format")
    parser.add_argument("--output-dir", "-o", type=Path, default=DEFAULT_OUTPUT,
                        help="Output directory for exported skills")
    parser.add_argument("--skill", "-s", type=str, default=None,
                        help="Export only a specific skill (by directory name)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List available skills without exporting")
    args = parser.parse_args()

    # Check source directory
    if not SKILLS_SOURCE.exists():
        print(f"Error: Skills directory not found: {SKILLS_SOURCE}")
        sys.exit(1)

    # Get skill directories
    skill_dirs = [d for d in SKILLS_SOURCE.iterdir()
                  if d.is_dir() and not d.name.startswith("_")]

    if args.list:
        print(f"Found {len(skill_dirs)} skills in {SKILLS_SOURCE}:\n")
        for d in sorted(skill_dirs, key=lambda x: x.name):
            print(f"  - {d.name}")
        return

    if args.skill:
        skill_dirs = [d for d in skill_dirs if d.name == args.skill]
        if not skill_dirs:
            print(f"Error: Skill '{args.skill}' not found")
            sys.exit(1)

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Exporting {len(skill_dirs)} skills to claude.ai format...")
    print(f"Output directory: {output_dir}\n")

    # Process skills
    results = []
    for skill_dir in sorted(skill_dirs, key=lambda x: x.name):
        result = convert_skill(skill_dir, output_dir)
        results.append(result)

        status_icon = "✅" if result["status"] == "converted" else "⚠️"
        warnings = []
        if result.get("name_truncated"):
            warnings.append("name truncated")
        if result.get("desc_truncated"):
            warnings.append(f"desc truncated ({result['original_desc_len']}→200)")

        warning_str = f" ({', '.join(warnings)})" if warnings else ""
        print(f"  {status_icon} {result['skill']}{warning_str}")

    # Create combined ZIP
    combined_path = create_combined_zip(output_dir, results)

    # Summary
    converted = sum(1 for r in results if r["status"] == "converted")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    truncated_names = sum(1 for r in results if r.get("name_truncated"))
    truncated_descs = sum(1 for r in results if r.get("desc_truncated"))

    print(f"\n{'='*60}")
    print("EXPORT COMPLETE")
    print(f"{'='*60}")
    print(f"  Skills converted: {converted}")
    print(f"  Skills skipped:   {skipped}")
    print(f"  Names truncated:  {truncated_names}")
    print(f"  Descs truncated:  {truncated_descs}")
    print(f"\nOutput locations:")
    print(f"  Individual ZIPs:  {output_dir}/zipped/")
    print(f"  Skill folders:    {output_dir}/individual/")
    print(f"  Combined ZIP:     {combined_path}")
    print(f"\nTo upload to claude.ai:")
    print(f"  1. Go to claude.ai → Settings → Skills")
    print(f"  2. Click 'Add Skill'")
    print(f"  3. Upload individual ZIPs from: {output_dir}/zipped/")

    # Write manifest
    manifest_path = output_dir / "MANIFEST.md"
    with open(manifest_path, "w") as f:
        f.write("# Claude.ai Skills Export Manifest\n\n")
        f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Source:** {SKILLS_SOURCE}\n")
        f.write(f"**Total Skills:** {converted}\n\n")
        f.write("## Skills Included\n\n")
        for r in sorted(results, key=lambda x: x.get("name", x["skill"])):
            if r["status"] == "converted":
                warnings = []
                if r.get("name_truncated"):
                    warnings.append("name truncated")
                if r.get("desc_truncated"):
                    warnings.append(f"desc truncated")
                warning_str = f" ⚠️ *{', '.join(warnings)}*" if warnings else ""
                f.write(f"- {r['name']}{warning_str}\n")

        if skipped > 0:
            f.write("\n## Skipped Skills\n\n")
            for r in results:
                if r["status"] == "skipped":
                    f.write(f"- {r['skill']}: {r.get('reason', 'Unknown')}\n")


if __name__ == "__main__":
    main()
