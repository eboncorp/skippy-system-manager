# Ebon Initiative Group - Final Reconciliation Summary

**Date:** 2026-01-20
**Prepared by:** Claude (automated analysis)
**Status:** Pending Statements

---

## Executive Summary

Comprehensive analysis of two QuickBooks files revealed **~$67,000+ in discrepancies** between QuickBooks and actual bank balances. Root cause identified: income miscategorization and incorrect opening balances.

---

## 1. ROOT CAUSE ANALYSIS

### Primary Issue: Missing Income in NEW QuickBooks

| Metric | OLD QB | NEW QB | GAP |
|--------|--------|--------|-----|
| **Services Income** | $180,705.76 | $32,455.72 | **$148,250.04** |

**What happened:** When migrating to new QB, $148K of Services income was NOT transferred. The old QB had income split between Dirty Daves (business) and Invest Checking (personal). Only Dirty Daves portion made it to new QB.

### Secondary Issue: Wrong Opening Balances

| Account | QB Opening | Actual Opening | Error |
|---------|------------|----------------|-------|
| Dirty Daves (9207) | $0.00 | $67.14 (Jan 2023) | -$67.14 |
| Credit Card (5268) | Unknown | TBD | Inverted accounting |

### Tertiary Issue: Credit Card Inverted Accounting

The credit card account (5268/4095) has **inverted signs** - payments are reducing balance below zero, indicating the account type is set up incorrectly (asset vs liability).

---

## 2. ACCOUNT DISCREPANCIES IDENTIFIED

### Bank Accounts vs QuickBooks

| Account | Bank Statement | QuickBooks | Discrepancy |
|---------|----------------|------------|-------------|
| **Dirty Daves (BofA 9207)** | +$250.16 | -$53,495.72 | ❌ **$53,746 OFF** |
| **Decibel Customs (US Bank 4416)** | +$43.63 | +$336.30 | ❌ $293 OFF |
| **Cash Mgmt (Fidelity 1582)** | +$105.37 | +$116.22 | ⚠️ $11 OFF |
| **Ebon Corp (Fidelity 0313)** | Unverified | +$450.12 | ⚠️ Need stmt |

### Credit Cards vs QuickBooks

| Account | Actual Balance | QuickBooks | Discrepancy |
|---------|----------------|------------|-------------|
| **Corp Card (BofA 5268)** | ~$782.76 | -$14,674.05 | ❌ **$13,891 OFF** |
| **Ally Credit (0243)** | Unknown | -$13,020.38 | ⚠️ Need stmt |
| **Dirty Daves Credit** | Unknown | $586.86 | ⚠️ Need stmt |
| **Dirty Daves Credit Rewards** | Unknown | -$22,765.58 | ⚠️ Need stmt |

---

## 3. CORPORATE STRUCTURE (Verified)

```
Ebon Initiative Group (Parent - QuickBooks Entity)
├── Dirty Daves, Incorporated
│   └── Bank of America 9207
│   └── Credit Cards (5268/4095)
├── Decibel Customs
│   └── US Bank 4416
├── GTI
│   └── Capital One (business)
├── PaperWerk
│   └── Mercury Bank 9687
└── Ebon Corp
    └── Fidelity 0313
    └── Fidelity Cash Management 1582
```

---

## 4. STATEMENTS NEEDED TO COMPLETE RECONCILIATION

### CRITICAL (Fix Major Discrepancies)

| # | Account | Bank | Last 4 | Period | Why |
|---|---------|------|--------|--------|-----|
| 1 | **Dirty Daves Checking** | Bank of America | 9207 | Jan 2023 → Present | $53,746 discrepancy - verify all deposits |
| 2 | **Business Credit Card** | Bank of America | 5268 | Jan 2023 → Present | $13,891 discrepancy - rebuild from scratch |
| 3 | **Ally Credit** | Ally Bank | 0243 | Full history | $13,020 balance unverified |

### HIGH PRIORITY (Verify Subsidiaries)

| # | Account | Bank | Last 4 | Period | Why |
|---|---------|------|--------|--------|-----|
| 4 | **PaperWerk** | Mercury | 9687 | Full history | Subsidiary not reconciled |
| 5 | **Decibel Customs** | US Bank | 4416 | 2023 → Present | $293 discrepancy |
| 6 | **Ebon Corp** | Fidelity | 0313 | 2023 → Present | Balance unverified |
| 7 | **Fidelity Ebon Corp** | Fidelity | (separate) | 2023 → Present | Balance unverified |

### MEDIUM (Assets & Investments)

| # | Account | Type | Period | Why |
|---|---------|------|--------|-----|
| 8 | **Brokerage 5744** | Investment | Current | $24.95 balance verify |
| 9 | **Crypto** | Crypto exchanges | 2023 → Present | $10,780 balance verify |

### ADDITIONAL CREDIT CARDS (if business)

| # | Account | Last 4 | Period | Notes |
|---|---------|--------|--------|-------|
| 10 | Dirty Daves Credit | ? | Full history | $586.86 |
| 11 | Dirty Daves Credit Rewards | ? | Full history | $22,765.58 |

---

## 5. WHAT I CAN DO WITH STATEMENTS

Once statements are provided, I will:

1. **Transaction-by-Transaction Matching**
   - Compare every QB entry to bank record
   - Identify missing transactions
   - Flag duplicates or errors

2. **Opening Balance Calculation**
   - Calculate correct starting balance for each account
   - Generate adjustment journal entries

3. **Income Reconciliation**
   - Find the $148K in missing Services income
   - Determine which deposits weren't recorded

4. **Credit Card Rebuild**
   - Start fresh with correct accounting direction
   - Import all transactions properly

5. **Generate Fix Report**
   - Exact journal entries to correct QB
   - Step-by-step instructions for corrections

---

## 6. STATEMENTS ALREADY ANALYZED

| Statement | Account | Date | Key Finding |
|-----------|---------|------|-------------|
| eStmt_2025-12-31.pdf | Dirty Daves 9207 | Dec 2025 | Actual balance +$250.16 |
| eStmt_2023-01-31.pdf | Dirty Daves 9207 | Jan 2023 | Opening balance $67.14 |
| December_Statement_2023-12-20.pdf | Credit Card | Dec 2023 | Sent to Dawn (proves 5268 = 4095) |
| Statement12312025.csv | Fidelity 1582 | Dec 2025 | Cash Mgmt $105.37 |
| US Bank statement | Decibel 4416 | Dec 2025 | Actual $43.63 |

---

## 7. FILES IN SESSION DIRECTORY

| File | Description |
|------|-------------|
| RECONCILIATION_REPORT.md | Detailed analysis (14 sections) |
| FINAL_RECONCILIATION_SUMMARY.md | This document |
| business_only_gl.csv | Old QB with personal removed |
| personal_removed_gl.csv | Personal transactions extracted |
| fresh_export_gl.csv | Fresh QB export |
| file1_csv/ | Old QB converted to CSV |
| file2_csv/ | New QB converted to CSV |

---

## 8. RECOMMENDED ACTION PLAN

### Phase 1: Gather Statements
- [ ] Download Dirty Daves (9207) - Jan 2023 to Present
- [ ] Download Credit Card (5268) - Jan 2023 to Present
- [ ] Download Ally Credit (0243) - Full history
- [ ] Download Mercury/PaperWerk (9687) - Full history
- [ ] Download US Bank/Decibel (4416) - 2023 to Present
- [ ] Download Fidelity accounts - 2023 to Present

### Phase 2: Reconciliation
- Claude analyzes statements vs QB
- Generate discrepancy report
- Create journal entry corrections

### Phase 3: Fix QuickBooks
- Apply opening balance adjustments
- Record missing income
- Rebuild credit card account
- Verify all balances match

---

## 9. CONTACT FOR TAX QUESTIONS

**Dawn Sosnin, CPA**
- Email: dawn@bpa.tax
- Status: Sent December 2023 credit card statement (2026-01-20)
- Question: Why does QB show $8,436 credit card balance when Dec 2023 statement shows $726.36?

---

*Final Summary Created: 2026-01-20 05:35 AM*
*Session Directory: /home/dave/skippy/work/business/20260120_024924_account_reconciliation/*
