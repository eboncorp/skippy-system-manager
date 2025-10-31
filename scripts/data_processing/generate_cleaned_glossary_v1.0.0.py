#!/usr/bin/env python3
"""
Generate cleaned glossary files from glossary_terms_CLEANED.json
Creates both Markdown and HTML versions
"""

import json
from datetime import datetime
from collections import defaultdict

# Load cleaned glossary
with open('glossary_terms_CLEANED.json', 'r') as f:
    terms = json.load(f)

print(f"Loaded {len(terms)} cleaned terms")

# Group by category
by_category = defaultdict(list)
for term in terms:
    by_category[term['category']].append(term)

# Generate Markdown
markdown = f"""# Louisville Voter Education Glossary

**Version:** 1.1 (Cleaned)  
**Updated:** {datetime.now().strftime('%B %d, %Y')}  
**Total Terms:** {len(terms)}

---

## About This Glossary

This glossary provides clear, accessible definitions for terms related to Louisville Metro government, budgets, voting, and civic engagement. Written for everyday citizens who want to understand how their local government works.

**Key Features:**
- Plain language explanations
- Louisville-specific examples
- No jargon or bureaucratic language
- Organized by category for easy navigation

---

## Table of Contents

"""

# Add TOC
for category in sorted(by_category.keys()):
    markdown += f"- [{category}](#{category.lower().replace(' ', '-').replace('&', 'and')})\n"

markdown += "\n---\n\n"

# Add terms by category
for category in sorted(by_category.keys()):
    markdown += f"## {category}\n\n"
    
    # Sort terms alphabetically within category
    category_terms = sorted(by_category[category], key=lambda x: x['name'].lower())
    
    for term in category_terms:
        markdown += f"### {term['name']}\n\n"
        markdown += f"{term['definition']}\n\n"
        markdown += "---\n\n"

# Add alphabetical index
markdown += "## Complete Alphabetical Index\n\n"
for term in sorted(terms, key=lambda x: x['name'].lower()):
    category_anchor = term['category'].lower().replace(' ', '-').replace('&', 'and')
    term_anchor = term['name'].lower().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')
    markdown += f"- **{term['name']}** ({term['category']})\n"

markdown += "\n---\n\n"
markdown += "*This glossary is part of the rundaverun.org civic education initiative.*\n"

# Save Markdown
with open('COMPLETE_VOTER_EDUCATION_GLOSSARY_v1.1_CLEANED.md', 'w') as f:
    f.write(markdown)

print("✓ Markdown file created: COMPLETE_VOTER_EDUCATION_GLOSSARY_v1.1_CLEANED.md")

# Generate HTML
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Louisville Voter Education Glossary v1.1</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c5aa0;
            border-bottom: 3px solid #2c5aa0;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2c5aa0;
            margin-top: 40px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 8px;
        }}
        h3 {{
            color: #333;
            margin-top: 25px;
        }}
        .meta {{
            color: #666;
            font-size: 0.95em;
            margin-bottom: 30px;
        }}
        .term {{
            margin-bottom: 30px;
            padding: 15px;
            background: #f9f9f9;
            border-left: 4px solid #2c5aa0;
            border-radius: 4px;
        }}
        .term-name {{
            font-weight: bold;
            font-size: 1.15em;
            color: #2c5aa0;
            margin-bottom: 8px;
        }}
        .term-definition {{
            color: #444;
        }}
        .category-section {{
            margin-top: 50px;
        }}
        .toc {{
            background: #f0f7ff;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .toc a {{
            color: #2c5aa0;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Louisville Voter Education Glossary</h1>
        
        <div class="meta">
            <strong>Version:</strong> 1.1 (Cleaned)<br>
            <strong>Updated:</strong> {datetime.now().strftime('%B %d, %Y')}<br>
            <strong>Total Terms:</strong> {len(terms)}
        </div>
        
        <div style="padding: 20px; background: #e8f4f8; border-radius: 4px; margin-bottom: 30px;">
            <strong>About This Glossary</strong><br>
            This glossary provides clear, accessible definitions for terms related to Louisville Metro government, 
            budgets, voting, and civic engagement. Written for everyday citizens who want to understand how their 
            local government works.
        </div>
        
        <div class="toc">
            <h2 style="margin-top: 0;">Categories</h2>
            <ul>
"""

for category in sorted(by_category.keys()):
    category_id = category.lower().replace(' ', '-').replace('&', 'and')
    html += f'                <li><a href="#{category_id}">{category}</a> ({len(by_category[category])} terms)</li>\n'

html += """            </ul>
        </div>
        
"""

# Add terms by category
for category in sorted(by_category.keys()):
    category_id = category.lower().replace(' ', '-').replace('&', 'and')
    html += f'        <div class="category-section" id="{category_id}">\n'
    html += f'            <h2>{category}</h2>\n'
    
    category_terms = sorted(by_category[category], key=lambda x: x['name'].lower())
    
    for term in category_terms:
        html += '            <div class="term">\n'
        html += f'                <div class="term-name">{term["name"]}</div>\n'
        html += f'                <div class="term-definition">{term["definition"]}</div>\n'
        html += '            </div>\n'
    
    html += '        </div>\n\n'

html += """        <div class="footer">
            <p>This glossary is part of the rundaverun.org civic education initiative.</p>
            <p><strong>A Mayor That Listens, A Government That Responds</strong></p>
        </div>
    </div>
</body>
</html>
"""

# Save HTML
with open('COMPLETE_VOTER_EDUCATION_GLOSSARY_v1.1_CLEANED.html', 'w') as f:
    f.write(html)

print("✓ HTML file created: COMPLETE_VOTER_EDUCATION_GLOSSARY_v1.1_CLEANED.html")

# Generate statistics
print("\n" + "="*60)
print("STATISTICS")
print("="*60)
print(f"\nTotal terms: {len(terms)}")
print("\nBreakdown by category:")
for category in sorted(by_category.keys()):
    print(f"  {category}: {len(by_category[category])} terms")

print("\n✓ All files generated successfully!")
