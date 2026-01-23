# QuickBooks Reconciliation Analysis

**Date:** 2026-01-22
**Prepared by:** Claude (automated analysis)
**Session Directory:** `/home/dave/skippy/work/business/20260120_024924_account_reconciliation/`

---

## Executive Summary

Analysis of 297 bank statements and transaction files reveals the root causes of the ~$67K QuickBooks discrepancies. The primary issue is **comingled personal and business funds** in the OLD QuickBooks file, with ~$149K of "income" that was likely misclassified W-2 payroll and personal deposits.

---

## 1. The Income Gap Explained

### OLD QB vs NEW QB Income Comparison

| Account | OLD QB | NEW QB | Difference |
|---------|--------|--------|------------|
| **Services Income** | $180,705.76 | $31,455.71 | **$149,250.05** |
| Sales/Product | $3,206.30 | $1,891.00 | $1,315.30 |
| Total Income | $183,723.08 | $33,346.71 | $150,376.37 |

### Where the $149K "Missing" Income Actually Is

The OLD QB appears to have classified these as "Services" income:
- **W-2 Payroll (Thomas Car Wash)** - Personal employment income deposited to business account
- **Personal Cash Deposits** - ATM deposits from personal sources
- **Transfers from Personal Accounts** - Zelle/cash app movements

**Verified from 2023 Bank Statements:**

| Source | Dirty Daves (9207) | Chase 2118 | Notes |
|--------|-------------------|------------|-------|
| Square (TRUE business) | $15,216.69 | - | Actual business income |
| Thomas Car Wash W-2 | $9,803.47 | $15,433.62 | Split across both accts! |
| ATM Cash | - | $13,790.00 | Personal |
| IRS Refund | - | $1,322.00 | Personal |

The **TRUE business income** in 2023 was approximately **$15,217** (Square payments only).

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

### Immediate Actions

1. **Correct Opening Balances**
   - Dirty Daves (9207): Set opening balance to actual Jan 2023 starting balance (~$67.14)
   - Credit Card (4095): Verify opening balance from first statement

2. **Remove Personal W-2 from Business Income**
   - Thomas Car Wash payroll deposits to 9207 (~$10K/year) are NOT business income
   - Should be recorded as owner contribution or transfer, not Services income

3. **Reclassify Personal Expenses**
   - Vehicle fuel (personal use), groceries, gambling should NOT be in business QB

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

1. **Separate QuickBooks files** for business vs personal
2. **Only record TRUE business income** (Square payments, client payments)
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
2. [ ] Decide whether to fix OLD QB or start fresh with NEW QB
3. [ ] Create adjusting journal entries for correct balances
4. [ ] Reconcile each account month-by-month
5. [ ] Establish clean separation of business/personal going forward

---

*Analysis completed: 2026-01-22*
*Session: /home/dave/skippy/work/business/20260120_024924_account_reconciliation/*
