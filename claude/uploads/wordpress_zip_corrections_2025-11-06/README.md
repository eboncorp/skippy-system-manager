# WordPress ZIP Code Corrections - November 6, 2025

**Date:** November 6, 2025
**Session:** ZIP Code Count Correction (73 → 63)
**Source:** rundaverun-local (Local by Flywheel)

---

## Overview

This directory contains WordPress content corrected to reflect the accurate number of ZIP code areas in Jefferson County, KY for mini substation planning.

**Based on research:**
- Jefferson County has 63 mapped ZIP code areas (deliverable addresses)
- Previous content incorrectly stated "73 potential locations"
- Corrected to "63 ZIP code areas"

---

## Corrections Applied

### Change: "73 potential locations" → "63 ZIP code areas"

**Rationale:**
Jefferson County ZIP code research (Nov 6, 2025) shows:
- 83 total ZIP codes (including PO Box and business mail)
- 63 mapped ZIP codes with deliverable addresses (per Felt GIS dataset)
- 63 is the accurate number for planning mini substation locations

---

## Files Corrected

### 1. Page 105 - Homepage
**File:** `post_105.json`
**Change:** 73 potential locations → 63 ZIP code areas
**Status:** ✅ CORRECTED

### 2. Page 107 - Our Plan
**File:** `post_107.json`
**Change:** 73 potential locations → 63 ZIP code areas
**Status:** ✅ CORRECTED

### 3. Page 337 - Voter Education
**File:** `post_337.json`
**Change:** 73 potential locations → 63 ZIP code areas
**Status:** ✅ CORRECTED

### 4. Policy 245 - About Dave Biggers
**File:** `post_245.json`
**Change:** 73 potential locations → 63 ZIP code areas
**Status:** ✅ CORRECTED

### 5. Policy 699 - Public Safety & Community Policing
**File:** `post_699.json`
**Change:** 73 potential locations → 63 ZIP code areas
**Status:** ✅ CORRECTED

### 6. Policy 941 - Phone Banking Script
**File:** `post_941.json`
**Change:** 73 potential locations → 63 ZIP code areas
**Status:** ✅ CORRECTED

### 7. Policy 942 - Canvassing Talking Points
**File:** `post_942.json`
**Change:** 73 potential locations → 63 ZIP code areas
**Status:** ✅ CORRECTED

---

## How to Use These Files

### Import to WordPress:
```bash
# Import single post
wp post update <POST_ID> --post_content="$(cat post_<ID>.json | jq -r '.post_content')"

# Example for homepage:
wp post update 105 --post_content="$(cat post_105.json | jq -r '.post_content')"
```

### Verify Corrections:
```bash
# Check for 63 ZIP code areas
wp post get 105 --field=post_content | grep "63 ZIP code"
```

---

## Research Sources

**Downloaded November 6, 2025:**
- Google Search: "How many zip codes in Jefferson County KY"
- Jefferson County PVA: Satellite Cities document

**Key Findings:**
- 83 incorporated taxing jurisdictions in Jefferson County
- 83 total ZIP codes (per Jefferson County PVA)
- 73 unique ZIP codes (per zipcodestogo.com)
- **63 mapped ZIP codes** (per Felt GIS dataset) ← Used for substations
- 38 Census ZIP Code Tabulation Areas (ZCTAs)

**Why 63?**
The 63 number represents mapped, deliverable ZIP code areas excluding:
- PO Box-only ZIP codes
- Unique business/volume mail ZIP codes
- Non-residential ZIP codes

This is the appropriate number for planning physical mini substation locations.

---

## Related Documentation

**Work Session:**
`/home/dave/skippy/work/wordpress/rundaverun-local/20251106_134609_zip_code_corrections/`

**Research Documents:**
- `/home/dave/skippy/claude/downloads/how many zip codes in jefferson county ky - Google Search.pdf`
- `/home/dave/skippy/claude/downloads/Satellite Cities _ Jefferson County PVA.pdf`

**Previous Fact-Check:**
- Authoritative Fact Sheet: `/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md`

---

## Summary Stats

**Content Reviewed:** 7 posts (3 pages + 4 policy documents)
**Corrections Made:** 7 items
**Text Replacements:** "73 potential locations" → "63 ZIP code areas"
**Impact:** More accurate representation of mini substation deployment plan

---

## Files in This Directory

- `post_105.json` - Homepage (ZIP count corrected)
- `post_107.json` - Our Plan (ZIP count corrected)
- `post_337.json` - Voter Education (ZIP count corrected)
- `post_245.json` - About Dave (ZIP count corrected)
- `post_699.json` - Public Safety policy (ZIP count corrected)
- `post_941.json` - Phone Banking Script (ZIP count corrected)
- `post_942.json` - Canvassing Talking Points (ZIP count corrected)
- `README.md` - This file

---

**Exported:** November 6, 2025
**Status:** Ready for deployment to production

**Note:** These corrections update the mini substation language from "73 potential locations" to "63 ZIP code areas" based on official Jefferson County ZIP code mapping data.
