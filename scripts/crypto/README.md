# Crypto Automation Scripts

**Location:** `/home/dave/skippy/scripts/crypto/`
**Last Updated:** January 28, 2026

---

## Two-Account Strategy

### Account Structure

| Account | Exchange | Purpose | Fee | Allocation |
|---------|----------|---------|-----|------------|
| **Personal** | Coinbase One | Day trading, high risk/reward | 0% | 30% |
| **Business** | Kraken | Long-term staking | Standard | 70% |

### Asset Distribution

**Business (Kraken) - Staking Assets:**
- BTC, ETH, DOT (12% APY), ATOM (10% APY), SOL (6% APY)
- AVAX, ADA, NEAR (9% APY), KAVA, MINA, LINK, LTC, XRP, XLM

**Personal (Coinbase One) - Trading Assets:**
- Meme coins: DOGE, SHIB, PEPE, BONK, WIF, FLOKI
- Layer 1: SUI, APT, SEI, TIA, INJ
- Layer 2: ARB, OP
- All other speculative plays

---

## Scripts Overview

### Core Analysis

| Script | Purpose | Usage |
|--------|---------|-------|
| `portfolio_v2.py` | Two-account strategy analysis | `python3 portfolio_v2.py` |
| `portfolio_automation.py` | Daily signal-based DCA | `python3 portfolio_automation.py` |
| `coin50_analysis.py` | COIN50 methodology | `python3 coin50_analysis.py` |

### Comparison & Backtesting

| Script | Purpose | Usage |
|--------|---------|-------|
| `daily_dca_comparison.py` | Compare DCA strategies | `python3 daily_dca_comparison.py` |
| `strategy_comparison_v2.py` | Historical strategy comparison | `python3 strategy_comparison_v2.py` |
| `fair_comparison.py` | Fair strategy comparison | `python3 fair_comparison.py` |
| `transaction_analyzer.py` | Analyze Coinbase transactions | `python3 transaction_analyzer.py` |

### Holdings & Index

| Script | Purpose | Usage |
|--------|---------|-------|
| `holdings_cli.py` | Holdings management | `python3 holdings_cli.py` |
| `index_cli.py` | Index management | `python3 index_cli.py` |
| `ath_analysis.py` | All-time high analysis | `python3 ath_analysis.py` |

---

## Daily Workflow

### 1. Check Market Conditions
```bash
python3 portfolio_v2.py
```
Shows:
- Fear & Greed Index → DCA multiplier
- Account balances and staking income
- Rebalancing recommendations

### 2. Execute DCA (Based on Signal)

| Fear & Greed | DCA Multiplier | Action |
|--------------|----------------|--------|
| 0-25 (Extreme Fear) | 2.5x-3.0x | Heavy buying |
| 25-50 (Fear) | 1.5x-2.0x | Increased buying |
| 50-75 (Greed) | 0.5x-0.75x | Reduced buying |
| 75-100 (Extreme Greed) | 0.25x | Minimal/pause |

### 3. Weekly Rebalancing
- Move staking assets to Kraken
- Take profits on winners in Personal
- Maintain 70/30 split

---

## Transaction Data

Located in `/home/dave/skippy/lib/python/crypto_trading/data/transactions/`:

| File | Records | Period |
|------|---------|--------|
| `coinbase_transactions_2023.csv` | 3,108 | 2023 |
| `coinbase_transactions_2024.csv` | 4,812 | 2024 |
| `coinbase_transactions_2025.csv` | 11,899 | 2025 |
| **Total** | **19,819** | - |

---

## Integration with Trading Library

Full trading system at `/home/dave/skippy/lib/python/crypto_trading/`:

```bash
# 130+ signal analysis
python3 /home/dave/skippy/lib/python/crypto_trading/cli.py unified BTC

# Backtesting
python3 /home/dave/skippy/lib/python/crypto_trading/backtest_cli.py run dca --days 365

# Paper trading
python3 /home/dave/skippy/lib/python/crypto_trading/trading_cli.py paper
```

---

## Current Portfolio (Jan 28, 2026)

| Metric | Value |
|--------|-------|
| Total Value | $8,151 |
| Business (Kraken) | $5,051 (62%) |
| Personal (Coinbase) | $3,101 (38%) |
| Staking Income | ~$154/year |
| Total Invested | $19,850 |
| Assets Held | 170 |

---

## Staking APY Reference (Kraken)

| Asset | APY |
|-------|-----|
| DOT | 12% |
| ATOM | 10% |
| NEAR | 9% |
| SOL | 6% |
| AVAX | 5% |
| ETH | 3.5% |
| ADA | 3% |

---

## Risk Disclaimer

⚠️ **Trading cryptocurrencies involves substantial risk of loss.**

- Past performance does not guarantee future results
- Never invest more than you can afford to lose
- Always paper trade before real money
