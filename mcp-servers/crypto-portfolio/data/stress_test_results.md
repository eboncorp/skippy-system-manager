# Crypto Portfolio - Stress Test Results

**Date:** 2026-02-01 23:44–23:53 EST
**Commit:** 5a3bd38 (post-QA + stablecoin fix)
**Mode:** Paper (all tests)
**System:** Linux 6.8.0-65, Python 3.12

---

## Test 1: Multi-Cycle Endurance (10 cycles, both agents)

**Command:** `python3 agent_runner.py --mode paper --cycles 10 --verbose`

| Metric | Result |
|--------|--------|
| Cycles completed | 10/10 |
| Cycle counting | Correct (no double-count after fix) |
| Total runtime | ~6.6s |
| Business DCA orders/cycle | 24, 24, 22, 16, 15, 25, 15, 25, 13, 22 |
| Business spend/cycle | $27.99, $27.98, $27.81, $32.24, $40.58, $40.55, $46.91, $44.90, $53.18, $55.34 |
| Budget escalation | Expected — F&G=14 (extreme fear) → 3.0x multiplier, $84/day ceiling |
| Personal trades/cycle | 0 all cycles (score ~25, ranging mode — correct behavior) |
| Personal portfolio | $1000 stable (no trades = no change) |
| Errors from our code | 0 |
| External errors | 1 (Altcoin Season Index SSL cert — not our code) |
| Stablecoin error | Fixed — now logs WARNING instead of print() |

### Business DCA Budget Analysis

```
Base budget:     $28/day
F&G index:       14 (extreme fear)
War chest mult:  3.0x
Effective max:   $84/day
```

Spend increased across cycles because the rebalancing algorithm generates larger orders as accumulated positions create wider gaps between actual and target allocations. All spending stayed within the $84/day extreme-fear ceiling.

### War Chest Multiplier Table

| F&G Range | Label | Multiplier | Effective Budget |
|-----------|-------|------------|------------------|
| 0–19 | Extreme Fear | 3.0x | $84.00 |
| 20–39 | Fear | 2.0x | $56.00 |
| 40–69 | Normal | 1.0x | $28.00 |
| 70–79 | Greed | 0.7x | $19.60 |
| 80–100 | Extreme Greed | 0.5x | $14.00 |

---

## Test 2: Live Adapter Stress (all 4 exchanges)

**All 4 exchange accounts connected and tested:**

| Account | Type | USD Balance | Status |
|---------|------|-------------|--------|
| Coinbase Personal | Personal | $0 | CONNECTED |
| Coinbase GTI | Business | $0 | CONNECTED |
| Kraken Personal | Personal | $3.00 | CONNECTED |
| Kraken Business | Business | $0 | CONNECTED |

### Rapid Balance Fetches (20 calls)

```
20 balance calls in 1.74s
0 errors
Avg: 87ms per call (cached after first round)
```

### Price Fetches (5 assets × 4 adapters = 20 calls)

```
20 price calls in 1.8s
0 errors
Valid prices: 20/20
```

| Asset | Coinbase Personal | Coinbase GTI | Kraken Personal | Kraken Business |
|-------|-------------------|--------------|-----------------|-----------------|
| BTC | $75,849.47 | $75,848.01 | $75,873.30 | $75,873.30 |
| ETH | $2,244.90 | $2,244.90 | $2,244.85 | $2,244.85 |
| SOL | $100.35 | $100.37 | $100.40 | $100.40 |
| XRP | $1.58 | $1.58 | $1.58 | $1.58 |
| DOGE | $0.10 | $0.10 | $0.10 | $0.10 |

### Cache Invalidation

```
4 fresh fetches (post-invalidation) in 1.02s
All returned consistent balances
```

### MultiExchangeAdapter Routing

```
BTC via coinbase_gti:     $75,843.99  ✓
ETH via kraken_business:  $2,244.85   ✓
SOL (fallback routing):   $100.35     ✓
USD (summed across):      $0          ✓
```

---

## Test 3: Edge Cases (15/15 passed)

| # | Test | Result |
|---|------|--------|
| 1 | Zero price gives zero quote_amount | PASS |
| 2 | Guard rejects zero quote_amount | PASS |
| 3 | MAX_STALE_BALANCE_AGE is 300s | PASS |
| 4 | PaperExchange has _prices | PASS |
| 5 | Live adapter lacks _prices | PASS |
| 6 | seed_prices with no _prices does not crash | PASS |
| 7 | initialize with no _prices does not crash | PASS |
| 8 | BTC routes to exchange_a | PASS |
| 9 | ETH routes to exchange_b | PASS |
| 10 | Unrouted DOGE returns 0 | PASS |
| 11 | Unknown asset routes to default adapter | PASS |
| 12 | Live mode aborts on "no" | PASS |
| 13 | Live mode aborts on empty input | PASS |
| 14 | DCA standalone backward compat | PASS |
| 15 | Trader standalone backward compat | PASS |

---

## Test 4: Trade Log Integrity

**File:** `data/agent_logs/trade_log.json`

| Check | Result |
|-------|--------|
| File exists | ✓ (4,412 bytes) |
| Valid JSON | ✓ |
| Entry count | 20 (10 business + 10 personal) |
| Required fields (business) | agent, type, mode, timestamp, fear_greed, orders, total_usd, trades — ✓ |
| Required fields (personal) | agent, type, mode, timestamp, trades, buys, sells, portfolio_value, pnl — ✓ |
| Timestamp format | All valid ISO 8601 — ✓ |
| Log rotation | 20/1000 capacity — ✓ |

**Runner Log:** `data/agent_logs/agent_runner.log` — 613 lines, 60,040 bytes

---

## Test 5: Live Mode Safety

```
$ echo "no" | python3 agent_runner.py --mode live --cycles 1

============================================================
WARNING: LIVE TRADING MODE
============================================================
This will place REAL orders with REAL money on:
  - Coinbase GTI (Business)
  - Kraken Business
  - Coinbase Personal
  - Kraken Personal
============================================================
Type 'yes' to confirm live trading: Aborted. Use --mode paper for paper trading.
```

Both "no" and empty input correctly abort. Only exact "yes" proceeds.

---

## Bugs Found During Stress Test

### 1. Stablecoin fetch print() instead of logger (FIXED)

**File:** `agents/extended_signals.py:642`
**Issue:** `print(f"Stablecoin fetch failed: {e}")` bypassed logging framework
**Root Cause:** CoinGecko returns a dict (rate-limit response) instead of a list, causing `'str' object has no attribute 'get'` when iterating over dict keys
**Fix:** Added `isinstance(data, list)` type guard + replaced `print()` with `logger.warning()`
**Commit:** `5a3bd38`

### 2. CoinGecko Rate Limiting (Expected, Not a Bug)

During rapid 10-cycle testing, later cycles sometimes showed CoinGecko rate-limit responses (`dict` instead of `list`). This is expected behavior for free-tier API usage during sub-second cycle intervals. In production (daily/hourly cycles), this won't occur.

---

## QA Fixes Verified by Stress Test

All 8 QA audit fixes (commit `0a61d31`) confirmed working:

| # | Fix | Verified By |
|---|-----|-------------|
| 1 | _prices AttributeError guard | Edge case tests 4–7 |
| 2 | Zero quote_amount rejection | Edge case tests 1–2 |
| 3 | Stale cache handling | Live adapter cache invalidation test |
| 4 | Cycle count fix | 10-cycle test (10/10 correct) |
| 5 | Class docstring updates | Code inspection |
| 6 | FileHandler before log_dir | Runner log created successfully |
| 7 | Live mode safety confirmation | Safety prompt test |
| 8 | F&G fallback logging | 10-cycle WARNING output verified |

---

## Architecture Summary

```
agent_runner.py
  ├── BusinessAgent (PaperDCAAgent)
  │     ├── Coinbase GTI → LiveExchangeAdapter → MultiExchangeAdapter
  │     ├── Kraken Business → LiveExchangeAdapter ↗
  │     ├── ETF Config: 26 assets, 6 categories
  │     └── Budget: $28/day base ($84 extreme fear)
  │
  ├── PersonalAgent (PaperDayTrader)
  │     ├── Coinbase Personal → LiveExchangeAdapter → MultiExchangeAdapter
  │     ├── Kraken Personal → LiveExchangeAdapter ↗
  │     ├── Strategy: AdaptiveDayTrade (momentum + mean-reversion)
  │     └── Budget: $12/day
  │
  └── Shared: UnifiedSignalAnalyzer (130+ signals), APScheduler, CoinGecko prices
```

### Exchange Account Routing

| Account | Agent | Key File |
|---------|-------|----------|
| Coinbase Personal | Personal | ~/.config/coinbase/cdp_api_key.json |
| Coinbase GTI | Business | ~/.config/coinbase/gti_cdp_api_key.json |
| Kraken Personal | Personal | ~/.config/kraken/personal_api_key.json |
| Kraken Business | Business | ~/.config/kraken/business_api_key.json |

### ETF Asset Routing (Business)

- **COINBASE_GTI:** BTC, SOL, AVAX, XRP, HBAR, MANA, SAND, ONDO, LINK, NEAR, SUI, RENDER, FET, XTZ, LTC, ALGO, POL, DOGE, ARB, USDC
- **KRAKEN_BUSINESS:** ETH (staking), TRX, ATOM (staking), DOT (staking), ADA (staking)

---

## Commits (This Session)

| Hash | Type | Description |
|------|------|-------------|
| `aaad2ff` | fix | Add missing SignalResult/ComprehensiveSignalAnalysis types |
| `f7faad0` | feat | Add two-agent trading architecture with exchange adapter layer |
| `0a61d31` | fix | Resolve 8 QA audit issues in trading agent architecture |
| `5a3bd38` | fix | Replace stablecoin print() with logger.warning and add type guard |

---

**Generated:** 2026-02-02 04:53 UTC
**Total Tests:** 45+ (10 cycles × 2 agents + 20 live calls + 15 edge cases)
**Pass Rate:** 100%
