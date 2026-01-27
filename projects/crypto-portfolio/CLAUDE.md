# CLAUDE.md - Project Context for Claude Code

## Project Overview

This is a cryptocurrency portfolio management system with 130+ market signals, automated trading strategies, and backtesting capabilities. The system is designed for intelligent DCA (Dollar-Cost Averaging) that adjusts buy amounts based on market conditions.

## Quick Commands

```bash
# Signal Analysis
python cli.py unified BTC          # Full analysis
python cli.py quick BTC            # Quick summary
python cli.py rec BTC              # Just recommendation

# Trading (Paper mode - safe)
python trading_cli.py paper        # Start paper trading
python trading_cli.py cycle        # Single cycle

# Backtesting
python backtest_cli.py run dca     # Test DCA strategy
python backtest_cli.py compare     # Compare all strategies
```

## Project Structure

```
crypto-portfolio-manager/
├── agents/                        # Core modules
│   ├── __init__.py               # All exports
│   ├── extended_signals.py       # Base 60 signals
│   ├── expanded_signals.py       # Additional 70 signals
│   ├── unified_analyzer.py       # Master 130+ aggregator
│   ├── trading_agent.py          # Trading execution
│   └── backtester.py             # Historical testing
├── data/
│   └── providers.py              # API integrations
├── cli.py                        # Signal analysis CLI
├── trading_cli.py                # Trading CLI
├── backtest_cli.py               # Backtesting CLI
└── README.md
```

## Key Classes

### Signal Analysis
```python
from agents import UnifiedSignalAnalyzer

analyzer = UnifiedSignalAnalyzer()
result = await analyzer.analyze("BTC")
print(f"Score: {result.composite_score}")
print(f"Action: {result.primary_recommendation.action}")
print(f"DCA Multiplier: {result.primary_recommendation.dca_multiplier}x")
await analyzer.close()
```

### Trading Agent
```python
from agents import create_paper_agent

agent = create_paper_agent(
    initial_cash=Decimal("10000"),
    strategies=["dca", "swing"]
)
await agent.initialize()
trades = await agent.run_cycle()
print(agent.get_status())
await agent.close()
```

### Backtesting
```python
from agents import run_strategy_backtest

result = await run_strategy_backtest("dca", days=365, initial_capital=10000)
print(f"Return: {result.metrics.total_return_pct}%")
print(f"Sharpe: {result.metrics.sharpe_ratio}")
```

## Signal Categories (130+ Total)

| Category | Count | Module |
|----------|-------|--------|
| Technical | 8 | extended_signals.py |
| Sentiment | 8 | extended_signals.py |
| On-Chain | 12 | extended_signals.py |
| Derivatives | 8 | extended_signals.py |
| Macro | 8 | extended_signals.py |
| Mining | 6 | extended_signals.py |
| Institutional | 5 | extended_signals.py |
| Additional | 5 | extended_signals.py |
| Smart Money | 12 | expanded_signals.py |
| DeFi/Altcoin | 12 | expanded_signals.py |
| Order Flow | 8 | expanded_signals.py |
| Calendar | 8 | expanded_signals.py |
| Cross-Chain | 8 | expanded_signals.py |
| Cycle Position | 8 | expanded_signals.py |
| Advanced On-Chain | 8 | expanded_signals.py |
| Advanced Sentiment | 6 | expanded_signals.py |

## Trading Strategies

| Strategy | Class | Description |
|----------|-------|-------------|
| DCA | `DCASignalStrategy` | Signal-adjusted buying (0.25x-3x) |
| Swing | `SwingStrategy` | Large buys in fear, sells in greed |
| Mean Reversion | `MeanReversionStrategy` | Buy below MA, sell above |
| Grid | `GridStrategy` | Ladder orders at intervals |
| Rebalance | `RebalanceStrategy` | Maintain target allocation |

## Composite Score Meaning

```
-100 to -60 = EXTREME FEAR    → 3.0x DCA + 75% buffer deploy
 -60 to -40 = FEAR            → 2.5x DCA + 50% buffer deploy
 -40 to -20 = MILD FEAR       → 2.0x DCA + 35% buffer deploy
 -20 to   0 = SLIGHT FEAR     → 1.5x DCA + 20% buffer deploy
   0 to  20 = NEUTRAL         → 1.0x DCA (normal)
  20 to  40 = MILD GREED      → 0.75x DCA
  40 to  60 = GREED           → 0.5x DCA
  60 to 100 = EXTREME GREED   → 0.25x DCA / take profits
```

## Risk Limits (Defaults)

```python
max_position_size_pct = 10%      # Max per position
max_portfolio_risk_pct = 2%      # Max risk per trade
max_daily_loss_pct = 5%          # Daily stop-loss
max_drawdown_pct = 20%           # Total drawdown limit
min_cash_reserve_pct = 10%       # Emergency cash
```

## Dependencies

```bash
pip install aiohttp --break-system-packages
```

## Common Tasks

### Add a new signal
1. Add to `extended_signals.py` or `expanded_signals.py`
2. Create fetch method for data
3. Add scoring logic
4. Register in category gathering

### Add a new exchange
1. Implement `ExchangeInterface` in `trading_agent.py`
2. Add API authentication
3. Implement all abstract methods

### Add a new strategy
1. Extend `TradingStrategy` base class
2. Implement `evaluate()` method
3. Register in CLI strategy_map

## Testing

```bash
# Paper trading is the primary test mode
python trading_cli.py paper --cycles 5

# Backtesting for historical validation
python backtest_cli.py run dca --days 365 --verbose

# Monte Carlo for robustness
python backtest_cli.py monte-carlo dca --simulations 100
```

## API Notes

**Working (Free):**
- CoinGecko: Prices, market caps, volumes
- Alternative.me: Fear & Greed Index
- Etherscan: ETH gas prices (free API key)

**Stubbed (Need API Keys):**
- Glassnode: On-chain metrics
- CryptoQuant: Exchange flows
- Coinglass: Derivatives data

System works with free APIs only, premium APIs improve signal coverage.

## Error Handling

All async operations use try/except with graceful degradation:
- Missing API data → signal marked "unavailable"
- Network errors → cached data or skip
- Invalid responses → log and continue

## Performance Notes

- All operations are async for speed
- 5-minute cache on API responses
- Parallel signal fetching where possible
- Batch operations for multiple assets

## Owner Context

This system is for Dave's company to use for cryptocurrency investing with potential trading capabilities. The focus is on:
1. Evidence-based market analysis
2. Automated DCA with signal adjustment
3. Risk management and capital preservation
4. Testing strategies before deployment

## Files to Avoid Modifying

- `extended_signals.py` - Core 60 signals (stable)
- `expanded_signals.py` - Additional 70 signals (stable)

## Files OK to Extend

- `trading_agent.py` - Add exchanges, strategies
- `backtester.py` - Add metrics, data sources
- CLI files - Add new commands
