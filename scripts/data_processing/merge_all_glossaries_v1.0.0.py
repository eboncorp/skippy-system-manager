#!/usr/bin/env python3
"""
Merge all glossary JSON files into one WordPress-compatible glossary
For Dave Biggers Campaign - Run Dave Run
"""

import json
from pathlib import Path

def load_json_file(filepath):
    """Load a JSON file and return the data."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  Error loading {filepath}: {e}")
        return []

def normalize_term_format(term_data):
    """Convert various term formats to WordPress plugin format."""

    # Handle different field names
    term_name = term_data.get('term') or term_data.get('name') or term_data.get('Name', '')
    definition = term_data.get('definition') or term_data.get('Definition', '')
    category = term_data.get('category') or term_data.get('Category', 'Uncategorized')

    # Handle related terms (might be array or string)
    related = term_data.get('relatedTerms') or term_data.get('related_terms') or []
    if isinstance(related, list):
        related_str = ', '.join(related)
    else:
        related_str = str(related)

    # Build normalized term
    normalized = {
        'term': term_name,
        'definition': definition,
        'category': category,
        'louisville_context': term_data.get('louisville_context') or term_data.get('Louisville Context', ''),
        'why_it_matters': term_data.get('why_it_matters') or term_data.get('Why This Matters', ''),
        'related_terms': related_str,
        'dave_proposal': term_data.get('dave_proposal') or term_data.get("Dave's Proposal", ''),
        'aliases': ', '.join(term_data.get('aliases', [])) if isinstance(term_data.get('aliases'), list) else ''
    }

    return normalized

def main():
    extract_dir = Path('/home/dave/skippy/claude/downloads/extracted')

    # List of JSON files to merge
    json_files = [
        '01_DATA_CENTER_TERMS.json',
        '02_VOTING_ELECTIONS_TERMS.json',
        '03_GOVERNMENT_STRUCTURE_TERMS.json',
        '04_CRIMINAL_JUSTICE_TERMS.json',
        'glossary_terms_CLEANED.json',
    ]

    print("🔄 Merging glossary files...")
    print()

    all_terms = []
    term_names_seen = set()  # Track duplicates

    for json_file in json_files:
        filepath = extract_dir / json_file
        if not filepath.exists():
            print(f"⚠️  Skipping {json_file} (not found)")
            continue

        print(f"📂 Loading {json_file}...")
        data = load_json_file(filepath)

        if isinstance(data, list):
            count = 0
            duplicates = 0
            for term_data in data:
                normalized = normalize_term_format(term_data)
                term_name = normalized['term'].lower().strip()

                # Skip duplicates
                if term_name in term_names_seen:
                    duplicates += 1
                    continue

                term_names_seen.add(term_name)
                all_terms.append(normalized)
                count += 1

            print(f"   ✅ Added {count} terms")
            if duplicates > 0:
                print(f"   ⚠️  Skipped {duplicates} duplicates")
        else:
            print(f"   ⚠️  Unexpected format (not an array)")
        print()

    # Sort alphabetically by term name
    all_terms.sort(key=lambda x: x['term'].lower())

    # Write merged output
    output_file = extract_dir / 'glossary_master_merged.json'
    print(f"💾 Writing merged glossary to: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_terms, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print(f"✅ SUCCESS!")
    print(f"   Total unique terms: {len(all_terms)}")
    print(f"   Output file: {output_file}")
    print("=" * 60)
    print()

    # Show category breakdown
    categories = {}
    for term in all_terms:
        cat = term['category'] or 'Uncategorized'
        categories[cat] = categories.get(cat, 0) + 1

    print("📊 Terms by category:")
    for cat in sorted(categories.keys()):
        print(f"   {cat}: {categories[cat]}")

    # Show sample term
    if all_terms:
        print()
        print("📝 Sample term (first in list):")
        sample = all_terms[0]
        print(f"   Term: {sample['term']}")
        print(f"   Category: {sample['category']}")
        print(f"   Definition: {sample['definition'][:100]}...")

if __name__ == '__main__':
    main()
