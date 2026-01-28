#!/usr/bin/env python3
"""
Crypto Trading Agent - Command Line Interface

Run automated trading strategies based on 130+ market signals.

Usage:
    python trading_cli.py paper              # Start paper trading
    python trading_cli.py paper --strategies dca,swing
    python trading_cli.py status             # Show agent status
    python trading_cli.py backtest           # Run backtest
    python trading_cli.py live               # Start live trading (requires API keys)

IMPORTANT: Always test with paper trading first!
"""

import asyncio
import argparse
import sys
import json
from decimal import Decimal
from datetime import datetime, timedelta

sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

from agents.trading_agent import (
    TradingAgent,
    TradingConfig,
    TradingMode,
    RiskLimits,
    PaperExchange,
    CoinbaseExchange,
    DCASignalStrategy,
    SwingStrategy,
    MeanReversionStrategy,
    GridStrategy,
    RebalanceStrategy,
    create_paper_agent,
)


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     CRYPTO TRADING AGENT - 130+ SIGNALS                       ║
║                                                                               ║
║  ⚠️  WARNING: Trading involves substantial risk of loss                       ║
║  Always start with paper trading and never risk more than you can afford     ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


def print_status(status: dict):
    """Print agent status in a nice format."""
    print("\n" + "=" * 70)
    print(f"  TRADING AGENT STATUS - {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)
    
    print(f"""
  Mode:           {status['mode'].upper()}
  Running:        {'✅ Yes' if status['is_running'] else '❌ No'}
  Strategies:     {', '.join(status['strategies'])}
  
  ┌─ PORTFOLIO ─────────────────────────────────────────────────────────┐
  │  Cash Balance:     ${Decimal(status['portfolio']['cash']):>12,.2f}                       │
  │  Total Value:      ${Decimal(status['portfolio']['total_value']):>12,.2f}                       │
  │  P&L:              ${Decimal(status['portfolio']['pnl']):>+12,.2f} ({Decimal(status['portfolio']['pnl_pct']):+.2f}%)            │
  └─────────────────────────────────────────────────────────────────────┘
""")
    
    if status['portfolio']['positions']:
        print("  POSITIONS:")
        for symbol, pos in status['portfolio']['positions'].items():
            print(f"    {symbol}:")
            print(f"      Quantity:      {Decimal(pos['quantity']):.8f}")
            print(f"      Entry Price:   ${Decimal(pos['entry_price']):,.2f}")
            print(f"      Current Price: ${Decimal(pos['current_price']):,.2f}")
            print(f"      Unrealized:    ${Decimal(pos['unrealized_pnl']):+,.2f}")
        print()
    
    print(f"""  RISK METRICS:
    Daily P&L:       ${Decimal(status['risk']['daily_pnl']):+,.2f}
    Daily Orders:    {status['risk']['daily_orders']}
    Peak Value:      ${Decimal(status['risk']['peak_value']):,.2f}
    
  ACTIVITY:
    Trades Today:    {status['trades_today']}
    Total Trades:    {status['total_trades']}
""")
    print("=" * 70)


async def run_paper_trading(
    strategies: list,
    initial_cash: float,
    interval: int,
    assets: list,
    cycles: int = None
):
    """Run paper trading simulation."""
    print_banner()
    print(f"\n🎮 Starting PAPER TRADING mode...")
    print(f"   Initial Cash: ${initial_cash:,.2f}")
    print(f"   Assets: {', '.join(assets)}")
    print(f"   Strategies: {', '.join(strategies)}")
    print(f"   Interval: {interval} seconds")
    if cycles:
        print(f"   Cycles: {cycles}")
    print()
    
    # Create agent
    config = TradingConfig(
        mode=TradingMode.PAPER,
        supported_assets=assets,
        dca_base_amount=Decimal(str(initial_cash / 100)),  # 1% of capital per DCA
        dca_frequency_hours=interval // 3600 if interval >= 3600 else 1,
    )
    
    exchange = PaperExchange(initial_balances={
        "USD": Decimal(str(initial_cash)),
        **{asset: Decimal("0") for asset in assets}
    })
    
    # Set initial prices (would come from live feed)
    # For demo, we'll fetch real prices
    import aiohttp
    async with aiohttp.ClientSession() as session:
        for asset in assets:
            try:
                coin_id = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}.get(asset, asset.lower())
                async with session.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd") as resp:
                    data = await resp.json()
                    price = Decimal(str(data[coin_id]["usd"]))
                    exchange.set_price(asset, price)
                    print(f"   {asset} price: ${price:,.2f}")
            except Exception as e:
                print(f"   ⚠️  Could not fetch {asset} price: {e}")
                exchange.set_price(asset, Decimal("50000") if asset == "BTC" else Decimal("3000"))
    
    # Build strategy list
    strategy_map = {
        "dca": DCASignalStrategy(config),
        "swing": SwingStrategy(config),
        "mean_reversion": MeanReversionStrategy(config),
        "grid": GridStrategy(config),
        "rebalance": RebalanceStrategy(config),
    }
    
    strategy_list = [strategy_map[s] for s in strategies if s in strategy_map]
    
    if not strategy_list:
        print("❌ No valid strategies selected!")
        return
    
    agent = TradingAgent(config, exchange, strategy_list)
    
    try:
        await agent.initialize()
        print(f"\n✅ Agent initialized with ${agent.portfolio.total_value:,.2f} portfolio")
        print("\n" + "-" * 70)
        print("  Starting trading cycles... (Ctrl+C to stop)")
        print("-" * 70 + "\n")
        
        cycle_count = 0
        while cycles is None or cycle_count < cycles:
            cycle_count += 1
            print(f"\n[Cycle {cycle_count}] {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            trades = await agent.run_cycle()
            
            if trades:
                for trade in trades:
                    emoji = "🟢" if trade.side.value == "buy" else "🔴"
                    print(f"  {emoji} {trade.side.value.upper()} {trade.quantity:.8f} {trade.symbol} @ ${trade.price:,.2f}")
                    print(f"     Strategy: {trade.strategy}")
            else:
                print("  ⏸️  No trades this cycle")
            
            # Update and show portfolio
            await agent._update_portfolio()
            print(f"  Portfolio: ${agent.portfolio.total_value:,.2f} ({agent.portfolio.total_pnl_percent:+.2f}%)")
            
            if cycles is None or cycle_count < cycles:
                print(f"\n  Waiting {interval} seconds for next cycle...")
                await asyncio.sleep(interval)
        
        print("\n" + "=" * 70)
        print("  PAPER TRADING SESSION COMPLETE")
        print("=" * 70)
        print_status(agent.get_status())
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping paper trading...")
    finally:
        await agent.close()


async def run_single_cycle(strategies: list, assets: list):
    """Run a single trading cycle (for testing)."""
    print_banner()
    print("\n🔄 Running single trading cycle...\n")
    
    agent = create_paper_agent(
        initial_cash=Decimal("10000"),
        assets=assets,
        strategies=strategies,
    )
    
    # Fetch prices
    import aiohttp
    async with aiohttp.ClientSession() as session:
        for asset in assets:
            try:
                coin_id = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}.get(asset, asset.lower())
                async with session.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd") as resp:
                    data = await resp.json()
                    price = Decimal(str(data[coin_id]["usd"]))
                    agent.exchange.set_price(asset, price)
            except:
                agent.exchange.set_price(asset, Decimal("50000") if asset == "BTC" else Decimal("3000"))
    
    try:
        await agent.initialize()
        trades = await agent.run_cycle()
        
        print_status(agent.get_status())
        
        if trades:
            print("\nTRADES EXECUTED:")
            for trade in trades:
                print(f"  {trade.side.value.upper()} {trade.quantity:.8f} {trade.symbol} @ ${trade.price:,.2f}")
        else:
            print("\nNo trades executed this cycle.")
            
    finally:
        await agent.close()


def print_strategies_help():
    """Print detailed strategy information."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           AVAILABLE STRATEGIES                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

  dca (Dollar-Cost Averaging)
  ────────────────────────────────────────────────────────────────────────────
  Signal-adjusted DCA that multiplies buy amounts based on market fear/greed.
  
  • Buys regularly regardless of price
  • Multiplies amount (0.25x to 3x) based on composite signal score
  • Deploys cash buffer during extreme fear
  • Lowest risk, best for long-term accumulation
  
  Signal Score → Multiplier:
    < -60: 3.0x    -40 to -20: 2.0x    0 to 20: 1.0x    40 to 60: 0.5x
    -60 to -40: 2.5x    -20 to 0: 1.5x    20 to 40: 0.75x    > 60: 0.25x

  swing
  ────────────────────────────────────────────────────────────────────────────
  Larger position trades based on significant signal moves.
  
  • Buys larger amounts during strong fear + accumulation phase
  • Sells portions during strong greed
  • Higher risk/reward than DCA
  • Best for those comfortable with volatility
  
  Triggers:
    BUY:  Score < -50 AND cycle in [accumulation, capitulation]
    SELL: Score > 50 AND has position

  mean_reversion
  ────────────────────────────────────────────────────────────────────────────
  Buys below moving average, sells above.
  
  • Uses 20-period simple moving average
  • Buys when price is >10% below SMA
  • Sells when price is >15% above SMA
  • Works best in ranging markets
  
  Triggers:
    BUY:  Price deviation < -10% from SMA
    SELL: Price deviation > +15% from SMA

  grid
  ────────────────────────────────────────────────────────────────────────────
  Places orders at regular price intervals.
  
  • Creates ladder of buy orders below current price
  • Creates ladder of sell orders above current price
  • Profits from volatility in either direction
  • Best in sideways/ranging markets
  
  Default: 10 levels, 2% spacing

  rebalance
  ────────────────────────────────────────────────────────────────────────────
  Maintains target portfolio allocation.
  
  • Default: 60% BTC, 30% ETH, 10% USD
  • Rebalances when allocation drifts >5% from target
  • Automatically sells winners, buys losers
  • Best for passive, balanced exposure

COMBINING STRATEGIES
────────────────────────────────────────────────────────────────────────────

You can run multiple strategies simultaneously:

  python trading_cli.py paper --strategies dca,swing

The agent will collect recommendations from all strategies and execute
those that pass risk management checks.

RECOMMENDED COMBINATIONS:
  • Conservative: dca only
  • Balanced: dca,rebalance
  • Active: dca,swing
  • Advanced: dca,swing,mean_reversion
""")


async def main():
    parser = argparse.ArgumentParser(
        description="Crypto Trading Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python trading_cli.py paper                     # Paper trade with DCA
  python trading_cli.py paper -s dca,swing        # Paper with multiple strategies
  python trading_cli.py paper -c 10               # Run 10 cycles then stop
  python trading_cli.py cycle                     # Run single cycle
  python trading_cli.py strategies                # Show strategy details
        """
    )
    
    parser.add_argument(
        "command",
        choices=["paper", "cycle", "status", "strategies", "help"],
        help="Command to run"
    )
    
    parser.add_argument(
        "-s", "--strategies",
        default="dca",
        help="Comma-separated list of strategies (dca,swing,mean_reversion,grid,rebalance)"
    )
    
    parser.add_argument(
        "-a", "--assets",
        default="BTC,ETH",
        help="Comma-separated list of assets to trade"
    )
    
    parser.add_argument(
        "-c", "--cycles",
        type=int,
        default=None,
        help="Number of cycles to run (default: infinite)"
    )
    
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=60,
        help="Seconds between trading cycles (default: 60)"
    )
    
    parser.add_argument(
        "--cash",
        type=float,
        default=10000,
        help="Initial cash for paper trading (default: 10000)"
    )
    
    args = parser.parse_args()
    
    strategies = [s.strip() for s in args.strategies.split(",")]
    assets = [a.strip().upper() for a in args.assets.split(",")]
    
    if args.command == "paper":
        await run_paper_trading(
            strategies=strategies,
            initial_cash=args.cash,
            interval=args.interval,
            assets=assets,
            cycles=args.cycles,
        )
    
    elif args.command == "cycle":
        await run_single_cycle(strategies=strategies, assets=assets)
    
    elif args.command == "strategies":
        print_strategies_help()
    
    elif args.command == "help":
        parser.print_help()
        print("\n" + "=" * 70)
        print("  For detailed strategy information: python trading_cli.py strategies")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
