#!/usr/bin/env python3
"""
Merge Part 4 expansion with existing 293-term glossary
Creates comprehensive glossary approaching 350 terms
"""

import json

# Load existing glossary (293 terms)
with open('/home/dave/skippy/claude/downloads/extracted/glossary_final_297_terms.json', 'r') as f:
    existing_terms = json.load(f)

# Load Part 4 expansion (47 terms)
with open('/home/dave/skippy/claude/downloads/extracted/glossary_expansion_part4_health_misc.json', 'r') as f:
    new_terms = json.load(f)

print(f"Existing terms: {len(existing_terms)}")
print(f"New terms to add: {len(new_terms)}")

# Check for duplicates by term name
existing_term_names = {term['term'].lower() for term in existing_terms}
duplicates = []
unique_new_terms = []

for term in new_terms:
    if term['term'].lower() in existing_term_names:
        duplicates.append(term['term'])
    else:
        unique_new_terms.append(term)

print(f"\nDuplicate terms (will skip): {len(duplicates)}")
if duplicates:
    for dup in duplicates:
        print(f"  - {dup}")

print(f"\nUnique new terms to add: {len(unique_new_terms)}")

# Merge
merged_glossary = existing_terms + unique_new_terms

# Sort alphabetically by term
merged_glossary.sort(key=lambda x: x['term'].lower())

print(f"\nFinal merged glossary: {len(merged_glossary)} terms")

# Count by category
category_counts = {}
for term in merged_glossary:
    cat = term.get('category', 'Uncategorized')
    category_counts[cat] = category_counts.get(cat, 0) + 1

print("\nTerms by category:")
for cat in sorted(category_counts.keys()):
    print(f"  {cat}: {category_counts[cat]}")

# Save merged glossary
output_file = '/home/dave/skippy/claude/downloads/extracted/glossary_comprehensive_340_terms.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(merged_glossary, f, indent=2, ensure_ascii=False)

# Also copy to WordPress plugin directory
wordpress_file = '/home/dave/Local Sites/rundaverun-local/app/public/wp-content/plugins/voter-education-glossary/glossary_comprehensive_340_terms.json'
with open(wordpress_file, 'w', encoding='utf-8') as f:
    json.dump(merged_glossary, f, indent=2, ensure_ascii=False)

print(f"\nSaved to: {output_file}")
print(f"Also copied to: {wordpress_file}")
print(f"Total terms: {len(merged_glossary)}")
print(f"\nProgress toward 350+ goal: {len(merged_glossary)}/350 ({len(merged_glossary)/350*100:.1f}%)")
remaining = max(0, 350 - len(merged_glossary))
print(f"Remaining terms needed: {remaining}")

if len(merged_glossary) >= 350:
    print("\n🎉 GOAL ACHIEVED! We have 350+ comprehensive terms!")
else:
    print(f"\n📊 Almost there! Just {remaining} more terms to reach 350+")
