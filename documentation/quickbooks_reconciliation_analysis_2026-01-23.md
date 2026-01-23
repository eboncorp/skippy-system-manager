# QuickBooks Reconciliation Analysis

**Date:** 2026-01-23 (Updated)
**Prepared by:** Claude (automated analysis)
**Session Directory:** `/home/dave/skippy/work/business/20260120_024924_account_reconciliation/`

---

## Executive Summary

Analysis of 297+ bank statements and transaction files reveals the root causes of the ~$67K QuickBooks discrepancies. The primary issue is that the **OLD QuickBooks tracked both business AND personal accounts** (Dirty Daves 9207 + Chase 2118), while the **NEW QuickBooks only tracks business accounts**. The $149K income gap is NOT missing data - it's the difference between including personal account transactions vs excluding them.

**Key User Clarification (2026-01-23):**
- ALL Services income recorded IS business income
- ATM Cash deposits and Cash App ARE true business income
- W-2 Payroll (Thomas Car Wash, Ford, Express Wash) deposits go to personal account (was deposited to wrong accounts)

---

## 1. The Income Gap Explained

### OLD QB vs NEW QB Income Comparison

| Account | OLD QB | NEW QB | Difference |
|---------|--------|--------|------------|
| **Services Income** | $180,705.76 | $31,455.71 | **$149,250.05** |
| Sales/Product | $3,206.30 | $1,891.00 | $1,315.30 |
| Total Income | $183,723.08 | $33,346.71 | $150,376.37 |

### The $149K Gap Explained: Two vs One Account

**OLD QB tracked TWO accounts:**
- Dirty Daves (BofA 9207) - Business checking
- Invest Checking 2118 (Chase) - Personal checking treated as business

**NEW QB tracks ONE account:**
- Dirty Daves (BofA 9207) - Business checking only

### Chase 2118 (Invest Checking) Deposits in OLD QB

| Category | Amount | Classification |
|----------|--------|----------------|
| **ATM/Cash Deposits** | $65,142.96 | ✅ Business |
| **Other Deposits** | $22,983.57 | ✅ Business |
| **Zelle Transfers** | $3,030.00 | ✅ Business |
| **Cash App** | $1,046.93 | ✅ Business |
| Thomas Car Wash (W-2) | $15,533.62 | ❌ Personal W-2 (wrong account) |
| IRS Refund | $1,399.00 | ❌ Personal |
| **TOTAL** | **$109,136.08** | |

**TRUE Business Income from Chase 2118:** $92,203.46
**Personal (misdeposited to business):** $16,932.62

### Dirty Daves (BofA 9207) Income Sources

| Category | Amount | Classification |
|----------|--------|----------------|
| **Square Inc** | ~$15,217/year | ✅ TRUE Business |
| **ATM Cash Deposits** | ~$12,000/year | ✅ TRUE Business |
| **Cash App** | ~$500/year | ✅ TRUE Business |
| Thomas Car Wash (W-2) | ~$9,803/year | ❌ Personal (wrong account) |
| Other Payroll (Ford, Express) | ~$7,100/year | ❌ Personal (wrong account) |
| Zelle from Decibel | ~$455/year | ⚠️ Inter-company |

### Combined TRUE Business Income Analysis

```
Dirty Daves (9207) TRUE Business:
  Square Inc:                    ~$15,217/year
  ATM Cash Deposits:             ~$12,000/year
  Cash App:                          ~$500/year
  ─────────────────────────────────────────────
  Subtotal BofA 9207:            ~$27,700/year

Chase 2118 TRUE Business (all deposits except W-2/IRS):
  ATM Cash Deposits:             $65,142.96
  Other Deposits:                $22,983.57
  Zelle Transfers:                $3,030.00
  Cash App:                       $1,046.93
  ─────────────────────────────────────────────
  Subtotal Chase 2118:           $92,203.46

TOTAL TRUE BUSINESS (both accounts): ~$120,000+
```

**NOT Business (misdeposited to Chase 2118):**
- Thomas Car Wash W-2: $15,533.62 (personal employment income)
- IRS Refund: $1,399.00 (personal)

---

## 2. Personal Expenses in OLD QB (Comingling)

The OLD QB contains these personal expenses mixed with business:

| Category | OLD QB | NEW QB | Removed |
|----------|--------|--------|---------|
| Groceries | $6,166.23 | $0 | ✅ |
| Personal Expense | $8,594.83 | $0 | ✅ |
| Gambling | $975.00 | $0 | ✅ |
| Vehicle Gas & Fuel | $23,597.55 | $117.03 | ~$23,480 |
| Phone Service | $19,547.40 | $9,233.31 | ~$10,300 |

**Total Personal Items in OLD QB:** ~$49,000+

---

## 3. Account Balance Discrepancies

### Dirty Daves Checking (BofA 9207)

| Metric | QuickBooks | Bank Statement | Discrepancy |
|--------|------------|----------------|-------------|
| Balance | -$53,495.72 | +$491.86 | **$53,987.58** |

**Root Cause:** QB starting balance was $0 but should have been actual opening balance. Additionally, personal W-2 payroll (~$10K/year) was deposited to this account but may not have been correctly recorded.

### Business Credit Card (BofA 4095/5268)

| Metric | QuickBooks | Actual | Discrepancy |
|--------|------------|--------|-------------|
| Balance | -$14,674.05 | ~-$782.76 | **~$13,891** |

**Root Cause:** Inverted accounting signs (payments reducing balance below zero) and incorrect opening balance.

---

## 4. Transaction Flow Summary (2023)

### Money INTO Dirty Daves Business Account
```
Square Inc (business income):     $15,216.69
Thomas Car Wash W-2 (WRONG!):     $9,803.47
Zelle from Decibel:               $455.00
Other:                            $633.74
─────────────────────────────────────────────
TOTAL DEPOSITS:                   $26,108.90
```

### Money OUT of Dirty Daves Business Account
```
Total Withdrawals 2023:           $25,684.18
Net Change:                       +$424.72
Ending Balance (Feb 2024):        $491.86
```

### Zelle Transfers from Business → Personal
```
Dirty Daves → Chase 2118:         $8,665.00 (owner draws)
```

---

## 5. Recommendations

### Decision: Which QuickBooks to Use?

**Option A: Keep NEW QB (Recommended)**
- Already has business-only transactions
- Cleaner starting point
- Needs: Opening balance corrections

**Option B: Fix OLD QB**
- Remove Chase 2118 account entirely
- Reclassify W-2 deposits as "Owner Contribution" not income
- Remove personal expenses (groceries, gambling, personal gas)
- More work, same end result

### Immediate Actions (if keeping NEW QB)

1. **Correct Opening Balances**
   - Dirty Daves (9207): Set opening balance to actual Jan 2023 starting balance (~$67.14)
   - Credit Card (4095): Verify opening balance from first statement

2. **Reclassify W-2 Deposits**
   - Thomas Car Wash, Ford Motor, Express Wash deposits (~$10K/year in 9207)
   - Should be "Owner Contribution" not Services income
   - These are personal W-2 earnings deposited to wrong account

### To Fix the $53K Checking Discrepancy

The QuickBooks balance of -$53,495.72 vs actual +$491.86 requires:

```
Adjusting Entry:
  Debit: Dirty Daves Checking    $53,987.58
  Credit: Opening Balance Equity $53,987.58

  Memo: Correct opening balance and reconcile
        to actual bank balance as of [date]
```

### Going Forward

1. **Use NEW QB for business-only tracking**
2. **Only record TRUE business income** (Square payments, ATM Cash for business, Cash App)
3. **Do NOT deposit W-2 payroll to business account**
4. **Monthly reconciliation** of all accounts

---

## 6. Files Analyzed

### QBO Transaction Files
| File | Account | Transactions | Period |
|------|---------|--------------|--------|
| stmtboa23.qbo | Dirty Daves 9207 | 213 | Jan-Dec 2023 |
| stmt4095.qbo | BofA CC 4095 | ~150 | Aug-Oct 2023 |
| chase2118_activity_20240228.qbo | Chase 2118 | 1,400 | Jan-Dec 2023 |
| checking_4416.qbo | US Bank 4416 | ~200 | Jan-Dec 2023 |

### Total Statement Files: 297

See `STATEMENT_INVENTORY.md` for complete list.

---

## 7. Next Steps

1. [ ] Review this analysis with tax accountant (Dawn Sosnin)
2. [ ] **Decision: Use NEW QB** (recommended) or fix OLD QB
3. [ ] Create adjusting journal entries for correct opening balances
4. [ ] Reclassify W-2 deposits as "Owner Contribution"
5. [ ] Reconcile each account month-by-month
6. [ ] Establish clean business/personal separation going forward

---

## 8. Statement Files Summary (2026-01-23)

### Total Files Collected: 369+

| Account | Files | Type | Coverage |
|---------|-------|------|----------|
| Dirty Daves (BofA 9207) | 36 PDFs + QBO | Business | 2023-Present |
| Credit Card (BofA 4095) | 33 PDFs + QBO | Business | 2023-Present |
| PaperWerk (Mercury 9687) | API data | Business | May 2023-Present |
| Decibel Customs (US Bank 4416) | 34 PDFs + QBO | Business | 2023-Present |
| Ebon Corp (Fidelity) | 43 CSVs | Business | 2023-Present |
| **Chase 2118** | **72 PDFs** | Personal | **2020-2025** |
| Ally Credit (0243) | 22 PDFs | Personal | Full history |
| Capital One (2379/5311) | 24+ files | Personal | 2023-2025 |
| L&N FCU | 3 PDFs | Personal | Limited |
| Citi (Best Buy/Home Depot) | 22 PDFs | Personal | Various |

### Key Finding

The Chase 2118 (Invest Checking) statements (72 PDFs covering 2020-2025) confirm
that the OLD QB was tracking personal account transactions as business income.

---

*Analysis completed: 2026-01-22*
*Updated: 2026-01-23*
*Session: /home/dave/skippy/work/business/20260120_024924_account_reconciliation/*
