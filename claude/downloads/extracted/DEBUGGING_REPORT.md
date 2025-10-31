# Louisville Voter Glossary - Debugging Report

**Date:** October 27, 2025  
**Original Version:** v1.0  
**Cleaned Version:** v1.1

---

## Executive Summary

The original glossary contained **263 entries**, of which **172 (65.4%)** were artifacts from policy documents rather than actual glossary definitions. These have been removed, leaving **91 legitimate terms (34.6%)**.

### Key Problems Identified

1. **Policy Document Headers Scraped as Terms** (171 entries)
   - Headers like "What It Is:", "Cost:", "Evidence:", "Total:", etc.
   - These were formatting labels from source documents, not glossary terms

2. **Incomplete/Fragment Entries** (42 entries)
   - Definitions under 30 characters
   - Often just data points without context

3. **Formatting Artifacts** (1 entry)
   - "Updated: October 13, 2025" - clearly a document date stamp

---

## Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Original Total** | 263 | 100% |
| **Legitimate Terms** | 91 | 34.6% |
| **Removed Artifacts** | 172 | 65.4% |

### Cleaned Glossary Breakdown by Category

| Category | Term Count |
|----------|------------|
| Budget & Finance | 37 |
| Health & Social Services | 26 |
| Criminal Justice | 9 |
| Government Structure | 9 |
| Louisville-Specific | 9 |
| Voting & Elections | 1 |
| **TOTAL** | **91** |

---

## Most Common Artifacts Removed

| Artifact Type | Count | Examples |
|--------------|-------|----------|
| "What It Is:" | 20 | Policy section headers |
| "Cost:" | 6 | Budget line items |
| "Evidence:" | 6 | Research citations |
| "When:" | 4 | Timeline info |
| "Dave's budget:" | 3 | Campaign-specific labels |
| "Coverage:" | 3 | Service area descriptions |
| "Examples:" | 3 | Illustration labels |
| "Total:" | 2 | Sum labels |
| "Where:" | 2 | Location info |
| Various others | 123 | Many one-off headers |

---

## Examples of Removed Artifacts

### Example 1: Date Stamp (Not a Term)
```
Name: "Updated:"
Definition: "October 13, 2025\n\n---"
```
**Issue:** This is a document metadata date, not a glossary term.

### Example 2: Budget Fragment (Not a Definition)
```
Name: "Cost:"
Definition: "$650,000 per station annually"
```
**Issue:** This is a data point from a budget table, not a glossary definition. No context about what term is being defined.

### Example 3: Section Header (Not a Term)
```
Name: "What It Is:"
Definition: [various policy descriptions]
```
**Issue:** This appears 20 times! It's a section header format from policy documents. Each instance had different content but the same problematic label.

### Example 4: Evidence Fragment
```
Name: "Evidence:"
Definition: "20-30% average crime reduction in 50+ cities using this model"
```
**Issue:** This is a citation/statistic, not a term definition. It's supporting data for another concept.

---

## Sample of Legitimate Terms Kept

### Budget & Finance
- **Appropriation**: Money officially allocated by Metro Council for a specific purpose...
- **Capital Budget**: Money spent on long-term assets like buildings, roads, and equipment...
- **Fiscal Year (FY)**: Louisville's budget year runs from July 1 to June 30...

### Criminal Justice
- **Community Policing**: Philosophy where police and residents work together as partners...
- **Use of Force**: Physical action taken by police to control a situation...
- **Qualified Immunity**: Legal doctrine that protects police from lawsuits...

### Health & Social Services
- **Harm Reduction**: Public health strategy focused on minimizing negative consequences...
- **Social Determinants of Health**: Conditions where people live, work, and age...
- **Crisis Intervention Team (CIT)**: Specialized police training for mental health calls...

---

## Files Generated

### 1. glossary_terms_CLEANED.json
- **91 legitimate glossary terms**
- Sorted alphabetically
- Ready for production use

### 2. REMOVED_ARTIFACTS.json
- **172 removed entries**
- Preserved for review
- Shows what was filtered out

### 3. This Report (DEBUGGING_REPORT.md)
- Complete analysis
- Examples and statistics
- Recommendations

---

## Root Cause Analysis

The artifacts likely originated from:

1. **Web scraping** that captured section headers as terms
2. **Document parsing** that didn't distinguish between:
   - Actual glossary definitions
   - Policy document formatting (headers, labels)
   - Data tables (cost figures, statistics)
   - Metadata (dates, document info)

3. **Copy-paste operations** from structured policy documents where formatting labels got included

---

## Recommendations

### Immediate Actions
1. ✅ **Use cleaned glossary** (glossary_terms_CLEANED.json)
2. ✅ **Review removed artifacts** to ensure no legitimate terms were caught
3. ✅ **Regenerate HTML/Markdown** from cleaned JSON

### Process Improvements
1. **Add validation rules** when ingesting new terms:
   - Term names should NOT end with ":"
   - Definitions must be > 30 characters
   - Definitions should explain a concept, not just state data

2. **Manual review stage** for any terms that:
   - Are very short
   - Contain only numbers/dates
   - Look like section headers

3. **Source document handling**:
   - Strip formatting before importing
   - Separate glossary terms from policy content
   - Use structured templates for new entries

---

## Quality Assurance

The cleaned glossary has been verified for:
- ✅ No duplicate terms
- ✅ All entries have proper structure (name, definition, category, section)
- ✅ Alphabetical ordering
- ✅ Consistent formatting
- ✅ Meaningful definitions (not fragments)

---

## Next Steps

1. Review REMOVED_ARTIFACTS.json to verify nothing important was removed
2. Regenerate the HTML and Markdown glossary files from the cleaned JSON
3. Update version number to v1.1 in all files
4. Test the glossary on your website
5. Consider adding the missing terms properly if any were caught in error

---

**Questions or concerns?** Review the REMOVED_ARTIFACTS.json file to see exactly what was removed and why.
