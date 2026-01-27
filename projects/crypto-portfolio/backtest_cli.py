#!/usr/bin/env python3
"""
Crypto Backtesting CLI

Test trading strategies against historical data.

Usage:
    python backtest_cli.py run dca                    # Backtest DCA strategy
    python backtest_cli.py run swing --days 730       # 2-year swing backtest
    python backtest_cli.py compare                    # Compare all strategies
    python backtest_cli.py compare --days 365 --capital 50000

Examples:
    python backtest_cli.py run dca --assets BTC,ETH
    python backtest_cli.py compare --days 1095        # 3-year comparison
"""

import asyncio
import argparse
import sys
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, '/home/claude/crypto-portfolio-manager')

from agents.backtester import (
    BacktestEngine,
    BacktestResult,
    HistoricalDataProvider,
    format_backtest_report,
    compare_strategies,
    run_strategy_backtest,
    compare_all_strategies,
)
from agents.trading_agent import (
    TradingConfig,
    TradingMode,
    DCASignalStrategy,
    SwingStrategy,
    MeanReversionStrategy,
    GridStrategy,
    RebalanceStrategy,
)


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        CRYPTO STRATEGY BACKTESTER                             ║
║                                                                               ║
║  Test strategies against historical data before risking real capital          ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


async def run_single_backtest(
    strategy: str,
    days: int,
    capital: float,
    assets: list,
    verbose: bool = False,
):
    """Run backtest for a single strategy."""
    print_banner()
    print(f"📊 Backtesting {strategy.upper()} strategy")
    print(f"   Period: {days} days")
    print(f"   Capital: ${capital:,.2f}")
    print(f"   Assets: {', '.join(assets)}")
    print()
    
    try:
        result = await run_strategy_backtest(
            strategy_name=strategy,
            initial_capital=capital,
            days=days,
            assets=assets,
        )
        
        print(format_backtest_report(result))
        
        if verbose and result.trades:
            print("\n" + "=" * 80)
            print("ALL TRADES:")
            print("=" * 80)
            for trade in result.trades:
                emoji = "🟢" if trade.side.value == "buy" else "🔴"
                print(
                    f"{trade.timestamp.strftime('%Y-%m-%d %H:%M')} | {emoji} "
                    f"{trade.side.value.upper():4} {float(trade.quantity):.6f} {trade.symbol} "
                    f"@ ${float(trade.price):,.2f} | "
                    f"Signal: {trade.signal_score:+.0f} | "
                    f"Portfolio: ${float(trade.portfolio_value_after):,.2f}"
                )
        
        return result
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        raise


async def run_comparison(
    days: int,
    capital: float,
    assets: list,
    strategies: list = None,
):
    """Compare multiple strategies."""
    print_banner()
    print(f"📊 Comparing strategies over {days} days")
    print(f"   Capital: ${capital:,.2f}")
    print(f"   Assets: {', '.join(assets)}")
    print()
    
    strategies = strategies or ["dca", "swing", "mean_reversion", "rebalance"]
    
    # Fetch data once
    print("Fetching historical data...")
    provider = HistoricalDataProvider()
    data = {}
    
    for asset in assets:
        print(f"  → {asset}...", end=" ", flush=True)
        data[asset] = await provider.fetch_coingecko(asset, days)
        print(f"✓ ({len(data[asset])} candles)")
        await asyncio.sleep(1.5)  # Rate limit
    
    await provider.close()
    print()
    
    results = []
    
    for strat_name in strategies:
        print(f"Running {strat_name}...", end=" ", flush=True)
        
        config = TradingConfig(
            mode=TradingMode.BACKTEST,
            supported_assets=assets,
            dca_base_amount=Decimal(str(capital / 100)),
            dca_frequency_hours=24,
        )
        
        strategy_map = {
            "dca": DCASignalStrategy,
            "swing": SwingStrategy,
            "mean_reversion": MeanReversionStrategy,
            "grid": GridStrategy,
            "rebalance": RebalanceStrategy,
        }
        
        if strat_name not in strategy_map:
            print(f"⚠️  Unknown strategy: {strat_name}")
            continue
        
        strategy = strategy_map[strat_name](config)
        engine = BacktestEngine(initial_capital=Decimal(str(capital)))
        
        try:
            result = await engine.run(strategy, assets=assets, data=data)
            results.append(result)
            print(f"✓ Return: {result.metrics.total_return_pct:+.1f}%")
        except Exception as e:
            print(f"✗ Error: {e}")
        finally:
            await engine.close()
    
    if results:
        print(compare_strategies(results))
        
        # Print individual summaries
        print("\n" + "=" * 100)
        print("INDIVIDUAL STRATEGY SUMMARIES")
        print("=" * 100)
        
        for result in sorted(results, key=lambda r: r.metrics.sharpe_ratio, reverse=True):
            m = result.metrics
            print(f"""
┌─ {result.strategy_name.upper()} ─────────────────────────────────────────────────────────────────────
│  Return: {m.total_return_pct:+.1f}% (Ann: {m.annualized_return_pct:+.1f}%)
│  Risk:   Vol {m.annualized_volatility_pct:.1f}% | MaxDD {m.max_drawdown_pct:.1f}%
│  Ratios: Sharpe {m.sharpe_ratio:.2f} | Sortino {m.sortino_ratio:.2f} | Calmar {m.calmar_ratio:.2f}
│  Trades: {m.total_trades} total | Win rate {m.win_rate_pct:.0f}% | Profit factor {m.profit_factor:.2f}
│  Alpha:  {m.alpha_pct:+.1f}% vs Buy & Hold ({m.buy_hold_return_pct:+.1f}%)
└─────────────────────────────────────────────────────────────────────────────────""")
    
    return results


async def run_custom_period(
    strategy: str,
    start_date: str,
    end_date: str,
    capital: float,
    assets: list,
):
    """Run backtest for a custom date range."""
    print_banner()
    
    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    days = (end - start).days
    
    if days <= 0:
        print("❌ End date must be after start date")
        return
    
    print(f"📊 Custom period backtest: {start_date} to {end_date} ({days} days)")
    print(f"   Strategy: {strategy}")
    print(f"   Capital: ${capital:,.2f}")
    print()
    
    result = await run_strategy_backtest(
        strategy_name=strategy,
        initial_capital=capital,
        days=days,
        assets=assets,
    )
    
    print(format_backtest_report(result))
    return result


async def run_monte_carlo(
    strategy: str,
    days: int,
    capital: float,
    simulations: int = 100,
):
    """Run Monte Carlo simulation with synthetic data."""
    print_banner()
    print(f"🎲 Monte Carlo Simulation: {simulations} runs")
    print(f"   Strategy: {strategy}")
    print(f"   Period: {days} days")
    print(f"   Capital: ${capital:,.2f}")
    print()
    
    provider = HistoricalDataProvider()
    returns = []
    sharpes = []
    max_dds = []
    
    for i in range(simulations):
        # Generate synthetic data with random parameters
        import random
        volatility = random.uniform(0.02, 0.05)
        trend = random.uniform(-0.0001, 0.0003)
        
        data = {
            "BTC": provider.generate_synthetic(
                "BTC",
                start_price=Decimal("50000"),
                days=days,
                volatility=volatility,
                trend=trend,
            )
        }
        
        config = TradingConfig(
            mode=TradingMode.BACKTEST,
            supported_assets=["BTC"],
            dca_base_amount=Decimal(str(capital / 100)),
            dca_frequency_hours=24,
        )
        
        strategy_map = {
            "dca": DCASignalStrategy,
            "swing": SwingStrategy,
            "mean_reversion": MeanReversionStrategy,
            "rebalance": RebalanceStrategy,
        }
        
        strat = strategy_map.get(strategy, DCASignalStrategy)(config)
        engine = BacktestEngine(initial_capital=Decimal(str(capital)))
        
        try:
            result = await engine.run(strat, assets=["BTC"], data=data)
            returns.append(result.metrics.total_return_pct)
            sharpes.append(result.metrics.sharpe_ratio)
            max_dds.append(result.metrics.max_drawdown_pct)
            
            if (i + 1) % 10 == 0:
                print(f"  Completed {i + 1}/{simulations} simulations...")
        except:
            pass
        finally:
            await engine.close()
    
    await provider.close()
    
    if not returns:
        print("❌ No successful simulations")
        return
    
    import statistics
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      MONTE CARLO RESULTS ({simulations} simulations)                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

  RETURN DISTRIBUTION:
    Mean:       {statistics.mean(returns):+.1f}%
    Median:     {statistics.median(returns):+.1f}%
    Std Dev:    {statistics.stdev(returns):.1f}%
    Min:        {min(returns):+.1f}%
    Max:        {max(returns):+.1f}%
    
  SHARPE RATIO:
    Mean:       {statistics.mean(sharpes):.2f}
    Median:     {statistics.median(sharpes):.2f}
    
  MAX DRAWDOWN:
    Mean:       {statistics.mean(max_dds):.1f}%
    Worst:      {max(max_dds):.1f}%
    
  PROBABILITY OF PROFIT: {sum(1 for r in returns if r > 0) / len(returns) * 100:.0f}%
  PROBABILITY OF >20% RETURN: {sum(1 for r in returns if r > 20) / len(returns) * 100:.0f}%
  PROBABILITY OF LOSS >10%: {sum(1 for r in returns if r < -10) / len(returns) * 100:.0f}%
""")


def print_help():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        BACKTESTING CLI HELP                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

COMMANDS:

  run [STRATEGY]       Run backtest for a single strategy
  compare              Compare all strategies
  monte-carlo          Monte Carlo simulation (synthetic data)

STRATEGIES:
  dca                  Signal-adjusted Dollar Cost Averaging
  swing                Swing trading on fear/greed signals
  mean_reversion       Buy below MA, sell above
  grid                 Grid trading at price intervals
  rebalance            Portfolio rebalancing

OPTIONS:
  --days, -d           Number of days to backtest (default: 365)
  --capital, -c        Initial capital (default: 10000)
  --assets, -a         Comma-separated assets (default: BTC)
  --verbose, -v        Show all trades
  --simulations, -s    Monte Carlo simulation count (default: 100)

EXAMPLES:

  # Basic backtest
  python backtest_cli.py run dca
  
  # 2-year backtest with $50k
  python backtest_cli.py run swing --days 730 --capital 50000
  
  # Multi-asset backtest
  python backtest_cli.py run dca --assets BTC,ETH
  
  # Compare all strategies
  python backtest_cli.py compare --days 365
  
  # Monte Carlo simulation
  python backtest_cli.py monte-carlo dca --simulations 200

PERFORMANCE METRICS EXPLAINED:

  Sharpe Ratio     Risk-adjusted return (>1 good, >2 excellent)
  Sortino Ratio    Like Sharpe but only penalizes downside vol
  Calmar Ratio     Return / Max Drawdown
  Alpha            Excess return vs Buy & Hold
  Beta             Correlation to market movements
  Profit Factor    Gross profits / Gross losses (>1.5 good)
  Win Rate         % of profitable trades

INTERPRETING RESULTS:

  Good Strategy Characteristics:
  • Sharpe > 1.0
  • Sortino > Sharpe (limited downside)
  • Max Drawdown < 30%
  • Positive Alpha
  • Win Rate > 50% with Profit Factor > 1.5
  
  Warning Signs:
  • Sharpe < 0.5
  • Max Drawdown > 50%
  • Negative Alpha (underperforms B&H)
  • Win Rate < 40%

NOTE: Past performance doesn't guarantee future results.
      Always use paper trading before deploying real capital.
""")


async def main():
    parser = argparse.ArgumentParser(
        description="Crypto Strategy Backtester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "command",
        choices=["run", "compare", "monte-carlo", "help"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "strategy",
        nargs="?",
        default="dca",
        help="Strategy to backtest"
    )
    
    parser.add_argument(
        "-d", "--days",
        type=int,
        default=365,
        help="Number of days to backtest (default: 365)"
    )
    
    parser.add_argument(
        "-c", "--capital",
        type=float,
        default=10000,
        help="Initial capital (default: 10000)"
    )
    
    parser.add_argument(
        "-a", "--assets",
        default="BTC",
        help="Comma-separated list of assets (default: BTC)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed trade log"
    )
    
    parser.add_argument(
        "-s", "--simulations",
        type=int,
        default=100,
        help="Number of Monte Carlo simulations (default: 100)"
    )
    
    parser.add_argument(
        "--strategies",
        default=None,
        help="Strategies to compare (comma-separated)"
    )
    
    args = parser.parse_args()
    
    assets = [a.strip().upper() for a in args.assets.split(",")]
    
    if args.command == "help":
        print_help()
        return
    
    elif args.command == "run":
        await run_single_backtest(
            strategy=args.strategy,
            days=args.days,
            capital=args.capital,
            assets=assets,
            verbose=args.verbose,
        )
    
    elif args.command == "compare":
        strategies = None
        if args.strategies:
            strategies = [s.strip() for s in args.strategies.split(",")]
        
        await run_comparison(
            days=args.days,
            capital=args.capital,
            assets=assets,
            strategies=strategies,
        )
    
    elif args.command == "monte-carlo":
        await run_monte_carlo(
            strategy=args.strategy,
            days=args.days,
            capital=args.capital,
            simulations=args.simulations,
        )


if __name__ == "__main__":
    asyncio.run(main())
