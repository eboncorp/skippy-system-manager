#!/usr/bin/env python3
"""
Import Markdown Policy and Budget Documents to WordPress
Converts markdown files to HTML and imports them as WordPress pages
"""

import os
import sys
import json
import subprocess
import markdown
import re

# Configuration
WP_DIR = "/home/dave/Local Sites/rundaverun-local/app/public"
CAMPAIGN_DIR = "/home/dave/rundaverun/campaign"

# Policy documents to import
POLICY_DOCS = [
    ("POLICY_01_PUBLIC_SAFETY_COMMUNITY_POLICING.md", "Policy #1: Public Safety & Community Policing", "policy-01-public-safety"),
    ("POLICY_02_CRIMINAL_JUSTICE_REFORM.md", "Policy #2: Criminal Justice Reform", "policy-02-criminal-justice"),
    ("POLICY_03_COMMUNITY_HEALTH_SERVICES.md", "Policy #3: Community Health Services", "policy-03-health-services"),
    ("POLICY_04_BUDGET_FINANCIAL_MANAGEMENT.md", "Policy #4: Budget & Financial Management", "policy-04-budget"),
    ("POLICY_05_AFFORDABLE_HOUSING_ANTI_DISPLACEMENT.md", "Policy #5: Affordable Housing & Anti-Displacement", "policy-05-housing"),
    ("POLICY_06_EDUCATION_YOUTH_DEVELOPMENT.md", "Policy #6: Education & Youth Development", "policy-06-education"),
    ("POLICY_07_ENVIRONMENTAL_JUSTICE_CLIMATE_ACTION.md", "Policy #7: Environmental Justice & Climate Action", "policy-07-environment"),
    ("POLICY_08_ECONOMIC_DEVELOPMENT_JOBS.md", "Policy #8: Economic Development & Jobs", "policy-08-economic-development"),
    ("POLICY_09_INFRASTRUCTURE_TRANSPORTATION.md", "Policy #9: Infrastructure & Transportation", "policy-09-infrastructure"),
    ("POLICY_10_ARTS_CULTURE_TOURISM.md", "Policy #10: Arts, Culture & Tourism", "policy-10-arts-culture"),
    ("POLICY_11_TECHNOLOGY_INNOVATION.md", "Policy #11: Technology & Innovation", "policy-11-technology"),
    ("POLICY_12_PUBLIC_HEALTH_WELLNESS.md", "Policy #12: Public Health & Wellness", "policy-12-public-health"),
    ("POLICY_13_NEIGHBORHOOD_DEVELOPMENT.md", "Policy #13: Neighborhood Development", "policy-13-neighborhoods"),
    ("POLICY_14_SENIOR_SERVICES.md", "Policy #14: Senior Services", "policy-14-seniors"),
    ("POLICY_15_DISABILITY_RIGHTS_ACCESSIBILITY.md", "Policy #15: Disability Rights & Accessibility", "policy-15-disability-rights"),
    ("POLICY_16_FOOD_SYSTEMS_URBAN_AGRICULTURE.md", "Policy #16: Food Systems & Urban Agriculture", "policy-16-food-systems"),
]

# Budget documents
BUDGET_DOCS = [
    ("BUDGET_DETAILED_LINE_ITEMS_INTEGRATED.md", "Detailed Line-Item Budget: Louisville Metro FY 2025-2026", "budget-detailed-line-items"),
    ("BUDGET_INTEGRATION_SUMMARY.md", "Budget Integration Summary", "budget-summary"),
    ("BUDGET_COMPARISON_CURRENT_VS_BIGGERS.md", "Budget Comparison: Current Administration vs. Dave Biggers", "budget-comparison"),
]

def convert_markdown_to_html(markdown_text):
    """Convert markdown to HTML"""
    md = markdown.Markdown(extensions=['extra', 'tables', 'toc'])
    html = md.convert(markdown_text)
    return html

def check_page_exists(slug):
    """Check if a WordPress page with this slug already exists"""
    try:
        result = subprocess.run(
            ['wp', 'post', 'list', f'--name={slug}', '--post_type=page', '--format=ids'],
            cwd=WP_DIR,
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())
    except Exception as e:
        print(f"Error checking page existence: {e}")
        return False

def create_wordpress_page(title, slug, html_content):
    """Create a WordPress page with the given content"""
    try:
        # Create the page
        result = subprocess.run(
            [
                'wp', 'post', 'create',
                '--post_type=page',
                f'--post_title={title}',
                f'--post_name={slug}',
                '--post_status=publish',
                f'--post_content={html_content}',
            ],
            cwd=WP_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)

def import_document(filename, title, slug):
    """Import a single markdown document"""
    filepath = os.path.join(CAMPAIGN_DIR, filename)

    if not os.path.exists(filepath):
        print(f"  ✗ File not found: {filename}")
        return False

    # Check if already exists
    if check_page_exists(slug):
        print(f"  ⊙ Already exists: {title}")
        return True

    # Read markdown file
    with open(filepath, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Convert to HTML
    html_content = convert_markdown_to_html(markdown_content)

    # Create WordPress page
    success, message = create_wordpress_page(title, slug, html_content)

    if success:
        print(f"  ✓ Created: {title}")
        return True
    else:
        print(f"  ✗ Failed: {title}")
        print(f"    Error: {message}")
        return False

def main():
    print("=" * 60)
    print("Importing Markdown Documents to WordPress")
    print("=" * 60)
    print()

    # Import policy documents
    print("Importing Policy Documents (16 documents)...")
    policy_success = 0
    for filename, title, slug in POLICY_DOCS:
        if import_document(filename, title, slug):
            policy_success += 1
    print(f"  Summary: {policy_success}/{len(POLICY_DOCS)} policy documents imported\n")

    # Import budget documents
    print("Importing Budget Documents (3 documents)...")
    budget_success = 0
    for filename, title, slug in BUDGET_DOCS:
        if import_document(filename, title, slug):
            budget_success += 1
    print(f"  Summary: {budget_success}/{len(BUDGET_DOCS)} budget documents imported\n")

    # Final summary
    print("=" * 60)
    print(f"Import Complete!")
    print(f"  Policy Documents: {policy_success}/{len(POLICY_DOCS)}")
    print(f"  Budget Documents: {budget_success}/{len(BUDGET_DOCS)}")
    print(f"  Total: {policy_success + budget_success}/{len(POLICY_DOCS) + len(BUDGET_DOCS)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
