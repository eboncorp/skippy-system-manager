# Crypto Portfolio Manager - Complete Trading System

An intelligent cryptocurrency trading system with 130+ market signals, automated trading agents, and comprehensive backtesting.

## Features

- **130+ Market Signals** across 16 categories
- **5 Trading Strategies** (DCA, Swing, Mean Reversion, Grid, Rebalance)
- **Full Backtesting Engine** with performance metrics
- **Risk Management** with position limits and drawdown protection
- **Paper Trading** for safe testing
- **Exchange Integration** (Coinbase ready, extensible)

## Quick Start

```bash
# Install dependencies
pip install aiohttp --break-system-packages

# Run signal analysis
python cli.py unified BTC

# Backtest a strategy
python backtest_cli.py run dca --days 365

# Compare all strategies
python backtest_cli.py compare

# Paper trade
python trading_cli.py paper --strategies dca,swing
```

## Components

### 1. Signal Analysis (cli.py)

130+ market indicators organized into categories:

| Category | Signals | Examples |
|----------|---------|----------|
| Technical | 16 | RSI, MA, MACD, Bollinger, Order Flow |
| Sentiment | 14 | Fear & Greed, Social, News |
| On-Chain | 24 | MVRV, SOPR, Exchange Flows, Whale Activity |
| Derivatives | 16 | Funding, OI, Liquidations, Options |
| Smart Money | 12 | LTH/STH SOPR, Accumulation, Dormancy |
| Cycle Position | 16 | Pi Cycle, Rainbow, Halving, Mayer Multiple |
| Macro | 16 | DXY, VIX, Cross-chain, Correlations |
| Institutional | 10+ | ETF Flows, Grayscale, DeFi metrics |

### 2. Trading Agent (trading_cli.py)

Automated execution based on signals:

```bash
# Paper trading (always start here!)
python trading_cli.py paper

# Multiple strategies
python trading_cli.py paper --strategies dca,swing

# Custom configuration
python trading_cli.py paper --cash 50000 --assets BTC,ETH,SOL
```

**Strategies:**
- **DCA**: Signal-adjusted buying (0.25x-3x multiplier)
- **Swing**: Large buys in fear, sells in greed
- **Mean Reversion**: Buy below MA, sell above
- **Grid**: Ladder orders at price intervals
- **Rebalance**: Maintain target allocation

### 3. Backtester (backtest_cli.py)

Test strategies against historical data:

```bash
# Single strategy
python backtest_cli.py run dca --days 730 --capital 10000

# Compare strategies
python backtest_cli.py compare --days 365

# Monte Carlo simulation
python backtest_cli.py monte-carlo dca --simulations 200
```

**Performance Metrics:**
- Returns: Total, Annualized, Alpha vs Buy & Hold
- Risk: Volatility, Max Drawdown, VaR
- Ratios: Sharpe, Sortino, Calmar
- Trades: Win Rate, Profit Factor, Avg Trade

## Signal Score Interpretation

| Score | Condition | DCA Multiplier | Action |
|-------|-----------|----------------|--------|
| -100 to -60 | EXTREME FEAR | 3.0x | Maximum accumulation |
| -60 to -40 | FEAR | 2.5x | Aggressive buying |
| -40 to -20 | MILD FEAR | 2.0x | Increased buying |
| -20 to 0 | SLIGHT FEAR | 1.5x | Mild increase |
| 0 to 20 | NEUTRAL | 1.0x | Normal DCA |
| 20 to 40 | MILD GREED | 0.75x | Reduced buying |
| 40 to 60 | GREED | 0.5x | Minimal buying |
| 60 to 100 | EXTREME GREED | 0.25x | Consider profits |

## Risk Management

Built-in protections:

```python
RiskLimits(
    max_position_size_pct = 10%      # Per position
    max_portfolio_risk_pct = 2%      # Per trade
    max_daily_loss_pct = 5%          # Daily stop
    max_drawdown_pct = 20%           # Total stop
    min_cash_reserve_pct = 10%       # Emergency fund
)
```

## Project Structure

```
crypto-portfolio-manager/
├── agents/
│   ├── extended_signals.py   # Base 60 signals
│   ├── expanded_signals.py   # Additional 70 signals
│   ├── unified_analyzer.py   # Combined 130+ analysis
│   ├── trading_agent.py      # Execution engine
│   └── backtester.py         # Historical testing
├── cli.py                    # Signal analysis CLI
├── trading_cli.py            # Trading CLI
├── backtest_cli.py           # Backtesting CLI
└── README.md
```

## Programmatic Usage

```python
import asyncio
from agents import (
    UnifiedSignalAnalyzer,
    BacktestEngine, 
    create_paper_agent,
    DCASignalStrategy,
)

# Signal Analysis
async def analyze():
    analyzer = UnifiedSignalAnalyzer()
    result = await analyzer.analyze("BTC")
    print(f"Score: {result.composite_score}")
    print(f"Action: {result.primary_recommendation.action}")
    await analyzer.close()

# Backtesting
async def backtest():
    from agents.backtester import run_strategy_backtest
    result = await run_strategy_backtest("dca", days=365)
    print(f"Return: {result.metrics.total_return_pct}%")
    print(f"Sharpe: {result.metrics.sharpe_ratio}")

# Paper Trading
async def trade():
    agent = create_paper_agent(strategies=["dca", "swing"])
    await agent.initialize()
    trades = await agent.run_cycle()
    print(agent.get_status())
    await agent.close()

asyncio.run(analyze())
```

## Backtesting Best Practices

1. **Test Multiple Periods**: Bull markets, bear markets, sideways
2. **Use Realistic Assumptions**: Include fees (0.1%), slippage (0.1%)
3. **Compare to Benchmark**: Always measure Alpha vs Buy & Hold
4. **Check Risk Metrics**: Sharpe > 1, Max DD < 30%
5. **Monte Carlo**: Test robustness across random scenarios
6. **Paper Trade First**: Always validate before real money

## Warning

⚠️ **Trading cryptocurrencies involves substantial risk of loss.**

- Past performance does not guarantee future results
- Always start with paper trading
- Never invest more than you can afford to lose
- This software is for educational purposes

## License

MIT License
