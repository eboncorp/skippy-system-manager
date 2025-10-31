#!/usr/bin/env python3
"""
Convert LOUISVILLE_GOVERNANCE_GLOSSARY_MASTER.md to WordPress-compatible JSON
For Dave Biggers Campaign - Run Dave Run
"""

import json
import re
from pathlib import Path

def parse_glossary_markdown(md_content):
    """Parse the markdown glossary into structured data."""

    terms = []
    current_category = "Uncategorized"
    current_term = None

    lines = md_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Detect category headers (e.g., "## 1. VOTING & DEMOCRACY (26 Terms)")
        if line.startswith('## ') and '(' in line and 'Terms)' in line:
            # Extract category name
            match = re.search(r'##\s+\d+\.\s+([^(]+)', line)
            if match:
                current_category = match.group(1).strip()
                print(f"Found category: {current_category}")

        # Detect term headers (### Term Name)
        elif line.startswith('### ') and not line == '### 14 Major Categories':
            # Save previous term if exists
            if current_term:
                terms.append(current_term)

            # Start new term
            term_name = line.replace('### ', '').strip()
            current_term = {
                'name': term_name,
                'category': current_category,
                'definition': '',
                'louisville_context': '',
                'why_matters': '',
                'related_terms': [],
                'dave_proposal': ''
            }
            print(f"  Found term: {term_name}")

        # Parse term content sections
        elif current_term:
            if line.startswith('**Definition:**'):
                # Capture definition (may span multiple lines until next ** section)
                definition = line.replace('**Definition:**', '').strip()
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('**'):
                    definition += ' ' + lines[i].strip()
                    i += 1
                current_term['definition'] = definition.strip()
                continue

            elif line.startswith('**Louisville Context:**'):
                context = line.replace('**Louisville Context:**', '').strip()
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('**'):
                    context += ' ' + lines[i].strip()
                    i += 1
                current_term['louisville_context'] = context.strip()
                continue

            elif line.startswith('**Why This Matters:**') or line.startswith('**Why It Matters:**'):
                why = line.replace('**Why This Matters:**', '').replace('**Why It Matters:**', '').strip()
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('**'):
                    why += ' ' + lines[i].strip()
                    i += 1
                current_term['why_matters'] = why.strip()
                continue

            elif line.startswith('**Related Terms:**'):
                related = line.replace('**Related Terms:**', '').strip()
                # Parse comma-separated related terms
                if related:
                    current_term['related_terms'] = [t.strip() for t in related.split(',')]

            elif line.startswith('**Dave') or line.startswith('**Proposed:**'):
                # Capture Dave's proposal
                proposal = line.replace('**Dave', '').replace('**Proposed:**', '').strip()
                if proposal.startswith("'s") or proposal.startswith(' Proposal:'):
                    proposal = proposal.replace("'s Proposal:", '').replace(' Proposal:', '').strip()
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('**') and not lines[i].strip().startswith('###'):
                    proposal += ' ' + lines[i].strip()
                    i += 1
                current_term['dave_proposal'] = proposal.strip()
                continue

        i += 1

    # Add last term
    if current_term:
        terms.append(current_term)

    return terms

def convert_to_wordpress_format(terms):
    """Convert terms to WordPress plugin compatible format."""

    wp_terms = []

    for term in terms:
        wp_term = {
            'term': term['name'],
            'definition': term['definition'],
            'category': term['category'],
            'louisville_context': term['louisville_context'],
            'why_it_matters': term['why_matters'],
            'related_terms': ', '.join(term['related_terms']) if term['related_terms'] else '',
            'dave_proposal': term['dave_proposal']
        }
        wp_terms.append(wp_term)

    return wp_terms

def main():
    # Read the markdown file
    input_file = Path('/home/dave/skippy/claude/downloads/extracted/LOUISVILLE_GOVERNANCE_GLOSSARY_MASTER.md')
    output_file = Path('/home/dave/skippy/claude/downloads/extracted/glossary_enhanced_519_terms.json')

    print(f"Reading from: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Parse the markdown
    print("\nParsing glossary terms...")
    terms = parse_glossary_markdown(md_content)

    print(f"\nFound {len(terms)} terms")

    # Convert to WordPress format
    wp_terms = convert_to_wordpress_format(terms)

    # Write JSON output
    print(f"\nWriting to: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(wp_terms, f, indent=2, ensure_ascii=False)

    print(f"\n✅ SUCCESS! Created {output_file}")
    print(f"   Total terms: {len(wp_terms)}")

    # Show sample term
    if wp_terms:
        print(f"\n📝 Sample term:")
        print(f"   Name: {wp_terms[0]['term']}")
        print(f"   Category: {wp_terms[0]['category']}")
        print(f"   Definition: {wp_terms[0]['definition'][:100]}...")

if __name__ == '__main__':
    main()
