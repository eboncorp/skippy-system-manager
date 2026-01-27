# Crypto Portfolio Manager - Project Report

**Project:** Intelligent Cryptocurrency Trading System  
**Date:** January 27, 2026  
**Author:** Dave (with Claude assistance)  
**Version:** 1.0 Complete

---

## Executive Summary

Over two conversation sessions, we built a complete cryptocurrency trading system featuring:

- **130+ market signals** across 16 categories
- **5 trading strategies** with automated execution
- **Full backtesting engine** with comprehensive metrics
- **Risk management** with position limits and drawdown protection
- **Paper trading** for safe testing before live deployment

The system transforms market analysis into actionable DCA (Dollar-Cost Averaging) recommendations, automatically adjusting buy amounts from 0.25x to 3.0x based on market conditions.

---

## Development Timeline

### Session 1: Foundation & Signal Expansion (Chat 1)
*https://claude.ai/chat/95671aa4-b46c-4c41-af1c-0ffdec0958a5*

**Objective:** Build intelligent dip-buying system with market signals

**Progress:**
1. Started with basic price-based dip detection
2. Added Fear & Greed Index integration
3. Expanded to 15 signals (technical, sentiment, on-chain)
4. Grew to 25 signals with derivatives and macro data
5. Final expansion to 60 signals across 8 categories

**Categories Implemented (60 signals):**
| Category | Count | Key Signals |
|----------|-------|-------------|
| Technical | 8 | RSI, MA, Bollinger, MACD, Volume |
| Sentiment | 8 | Fear & Greed, Social, News |
| On-Chain | 12 | MVRV, SOPR, NUPL, Exchange Flows |
| Derivatives | 8 | Funding, OI, Liquidations |
| Macro | 8 | DXY, VIX, Gold Correlation |
| Mining | 6 | Hash Rate, Difficulty, S2F |
| Institutional | 5 | ETF Flows, Grayscale |
| Additional | 5 | Stablecoin, DeFi TVL |

**Deliverables:**
- `extended_signals.py` - 3,425 lines, 60 signals
- `cli.py` - Command-line interface
- Basic composite scoring system

---

### Session 2: Complete Trading System (This Chat)
*Current conversation*

**Objective:** Expand signals, add trading agent, add backtesting

**Progress:**

#### Phase 1: Signal Expansion (60 → 130+)
Added 70 new signals in 8 categories:

| Category | Count | Key Signals |
|----------|-------|-------------|
| Smart Money | 12 | LTH/STH SOPR, Dormancy Flow, Accumulation |
| DeFi/Altcoin | 12 | ETH Gas, Burn Rate, L2 TVL, DEX Ratio |
| Order Flow | 8 | Spread, Depth, CVD, Taker Ratio |
| Calendar | 8 | FOMC, CPI, NFP, Halving Countdown |
| Cross-Chain | 8 | Arb Spreads, Bridge Volume, Depeg Risk |
| Cycle Position | 8 | Pi Cycle, Rainbow, Mayer Multiple |
| Advanced On-Chain | 8 | HODL Waves, VDD, Velocity |
| Advanced Sentiment | 6 | Dev Activity, Whale Alerts |

**Deliverables:**
- `expanded_signals.py` - 2,800+ lines, 70 signals
- `unified_analyzer.py` - Master 130+ signal aggregator

#### Phase 2: Trading Agent Framework
Built complete automated trading system:

**Strategies Implemented:**
| Strategy | Description | Risk Level |
|----------|-------------|------------|
| DCA Signal | Multiplies buys (0.25x-3x) by fear/greed | Low |
| Swing | Large buys in fear, sells in greed | Medium |
| Mean Reversion | Buy below MA, sell above | Medium |
| Grid | Ladder orders at price intervals | Medium |
| Rebalance | Maintain target allocation | Low |

**Risk Management:**
```python
RiskLimits(
    max_position_size_pct = 10%
    max_portfolio_risk_pct = 2%
    max_daily_loss_pct = 5%
    max_drawdown_pct = 20%
    min_cash_reserve_pct = 10%
)
```

**Exchange Support:**
- Paper Exchange (built-in simulation)
- Coinbase Advanced Trade API (ready)
- Extensible interface for others

**Deliverables:**
- `trading_agent.py` - 52,000+ characters
- `trading_cli.py` - Paper trading interface

#### Phase 3: Backtesting Engine
Complete historical testing system:

**Features:**
- Historical data from CoinGecko (or CSV import)
- Simulated signal generation from price action
- Realistic execution (0.1% fees, 0.1% slippage)
- Monte Carlo simulation for robustness testing

**Performance Metrics:**
| Category | Metrics |
|----------|---------|
| Returns | Total, Annualized, Alpha vs B&H |
| Risk | Volatility, Max Drawdown, Duration |
| Risk-Adjusted | Sharpe, Sortino, Calmar |
| Trade Stats | Win Rate, Profit Factor, Avg Trade |
| Comparison | Beta, Correlation to Market |

**Deliverables:**
- `backtester.py` - 44,000+ characters
- `backtest_cli.py` - Testing interface

---

## Final System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRYPTO PORTFOLIO MANAGER                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  DATA SOURCES   │───▶│  130+ SIGNALS   │───▶│  COMPOSITE   │ │
│  │  - CoinGecko    │    │  - Technical    │    │    SCORE     │ │
│  │  - Alternative  │    │  - On-Chain     │    │  (-100/+100) │ │
│  │  - Glassnode*   │    │  - Sentiment    │    └──────┬───────┘ │
│  │  - CryptoQuant* │    │  - Derivatives  │           │         │
│  └─────────────────┘    │  - Smart Money  │           ▼         │
│                         │  - Cycle        │    ┌──────────────┐ │
│                         └─────────────────┘    │  STRATEGIES  │ │
│                                                │  - DCA       │ │
│  ┌─────────────────┐    ┌─────────────────┐    │  - Swing     │ │
│  │   BACKTESTER    │    │  RISK MANAGER   │◀───│  - Grid      │ │
│  │  - Historical   │    │  - Position Lim │    │  - Rebalance │ │
│  │  - Monte Carlo  │    │  - Drawdown     │    └──────┬───────┘ │
│  │  - Comparison   │    │  - Daily Loss   │           │         │
│  └─────────────────┘    └─────────────────┘           ▼         │
│                                                ┌──────────────┐ │
│                                                │   EXCHANGE   │ │
│                                                │  - Paper     │ │
│                                                │  - Coinbase  │ │
│                                                └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘

* = Requires API key
```

---

## File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `agents/extended_signals.py` | ~3,400 | Base 60 signals |
| `agents/expanded_signals.py` | ~2,800 | Additional 70 signals |
| `agents/unified_analyzer.py` | ~750 | Master aggregator |
| `agents/trading_agent.py` | ~1,300 | Execution engine |
| `agents/backtester.py` | ~1,100 | Historical testing |
| `cli.py` | ~340 | Signal analysis CLI |
| `trading_cli.py` | ~400 | Trading CLI |
| `backtest_cli.py` | ~400 | Backtesting CLI |
| `README.md` | ~200 | Documentation |

**Total:** ~10,700 lines of Python code

---

## Usage Quick Reference

### Signal Analysis
```bash
python cli.py unified BTC          # Full 130+ signal analysis
python cli.py quick BTC            # Quick summary
python cli.py rec BTC              # DCA recommendation only
python cli.py category smart_money # Single category
```

### Trading
```bash
python trading_cli.py paper                    # Paper trade with DCA
python trading_cli.py paper -s dca,swing       # Multiple strategies
python trading_cli.py paper --cash 50000       # Custom capital
python trading_cli.py cycle                    # Single cycle test
```

### Backtesting
```bash
python backtest_cli.py run dca --days 365      # Single strategy
python backtest_cli.py compare                 # Compare all
python backtest_cli.py monte-carlo dca -s 200  # Robustness test
```

---

## Signal Score Interpretation

| Score | Condition | DCA Mult | Buffer | Action |
|-------|-----------|----------|--------|--------|
| -100 to -60 | EXTREME FEAR | 3.0x | 75% | Maximum accumulation |
| -60 to -40 | FEAR | 2.5x | 50% | Aggressive buying |
| -40 to -20 | MILD FEAR | 2.0x | 35% | Increased buying |
| -20 to 0 | SLIGHT FEAR | 1.5x | 20% | Mild increase |
| 0 to 20 | NEUTRAL | 1.0x | 0% | Normal DCA |
| 20 to 40 | MILD GREED | 0.75x | 0% | Reduced buying |
| 40 to 60 | GREED | 0.5x | 0% | Minimal buying |
| 60 to 100 | EXTREME GREED | 0.25x | 0% | Consider taking profits |

---

## API Requirements

**Free APIs (Working):**
- CoinGecko - Prices, market data
- Alternative.me - Fear & Greed Index
- Etherscan - Gas prices (needs free key)

**Premium APIs (Stub implementations):**
- Glassnode - On-chain metrics
- CryptoQuant - Exchange/whale data
- Coinglass - Derivatives data
- Kaiko - Order flow data

The system gracefully degrades when premium APIs aren't available, marking those signals as "unavailable" and adjusting weights accordingly.

---

## Recommended Next Steps

1. **Notifications** - Telegram/Discord alerts on trades
2. **Web Dashboard** - Visual monitoring interface
3. **More Exchanges** - Kraken, Binance integration
4. **Tax Reporting** - Cost basis and P&L tracking
5. **API Keys** - Add Glassnode/CryptoQuant for full signal coverage

---

## Risk Disclaimer

⚠️ **Trading cryptocurrencies involves substantial risk of loss.**

- Past performance does not guarantee future results
- Always paper trade before using real money
- Never invest more than you can afford to lose
- This system is for educational and informational purposes
- Consult a financial advisor before making investment decisions

---

## Technical Notes

- **Python 3.8+** required
- **aiohttp** for async HTTP requests
- All analysis is async for performance
- Caching reduces API calls (5-minute TTL)
- Modular design allows easy extension

---

*Report generated: January 27, 2026*
