#!/usr/bin/env python3
"""
Coinbase Trading Suite - Main Entry Point

A comprehensive crypto trading toolkit with:
- Portfolio analysis
- Automated rebalancing
- Dollar-cost averaging (DCA)
- Stop-loss and take-profit alerts
- Safety guardrails

Usage:
    python trading_cli.py [command]

Commands:
    portfolio   - View portfolio and performance
    rebalance   - Preview/execute rebalancing
    dca         - Manage DCA schedules
    alerts      - Manage price alerts
    trade       - Execute manual trades
    config      - View/edit configuration
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from exchanges import CoinbaseClient
from portfolio_analyzer import PortfolioAnalyzer
from trading_engine import TradingEngine
from rebalancer import Rebalancer
from dca_bot import DCABot
from alerts import AlertMonitor
from config import TradingConfig, TradingMode, load_config_from_env


def get_client() -> CoinbaseClient:
    """Get authenticated Coinbase client."""
    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ Error: COINBASE_API_KEY and COINBASE_API_SECRET must be set")
        print("   Copy .env.example to .env and add your credentials")
        sys.exit(1)
    
    return CoinbaseClient(api_key, api_secret)


def cmd_portfolio(args):
    """View portfolio and performance."""
    client = get_client()
    analyzer = PortfolioAnalyzer(client)
    
    if args.json:
        import json
        data = analyzer.get_portfolio_data()
        print(json.dumps(data, indent=2, default=str))
    else:
        analyzer.display_portfolio()
        
        if args.performance:
            analyzer.display_performance()
        
        if args.underperformers:
            analyzer.display_underperformers()


def cmd_rebalance(args):
    """Preview or execute portfolio rebalancing."""
    client = get_client()
    config = load_config_from_env()
    
    # Parse target allocations
    if args.targets:
        targets = {}
        for item in args.targets:
            asset, pct = item.split(":")
            targets[asset.upper()] = float(pct)
        config.rebalance.target_allocations = targets
    
    if not config.rebalance.target_allocations:
        print("❌ No target allocations set")
        print("   Use --targets BTC:50 ETH:30 SOL:20")
        print("   Or set in config.py")
        return
    
    engine = TradingEngine(client, config)
    rebalancer = Rebalancer(client, engine, config)
    
    rebalancer.display_allocation_status()
    
    if args.execute:
        if args.dry_run:
            print("\n⚠️  DRY RUN - No trades will be executed")
        rebalancer.execute_rebalance(dry_run=args.dry_run)
    else:
        print("\nUse --execute to run trades (add --dry-run to simulate)")


def cmd_dca(args):
    """Manage DCA schedules."""
    client = get_client()
    config = load_config_from_env()
    engine = TradingEngine(client, config)
    bot = DCABot(client, engine, config)
    
    if args.add:
        asset, amount = args.add.split(":")
        bot.add_schedule(asset.upper(), float(amount), args.interval)
    
    elif args.remove:
        bot.remove_schedule(args.remove.upper())
    
    elif args.run:
        results = bot.execute_dca()
        print(f"\nExecuted {len(results)} DCA purchase(s)")
    
    elif args.daemon:
        print("Starting DCA daemon (Ctrl+C to stop)...")
        bot.start_daemon()
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            bot.stop_daemon()
    
    else:
        bot.display_schedules()


def cmd_alerts(args):
    """Manage price alerts."""
    client = get_client()
    config = load_config_from_env()
    engine = TradingEngine(client, config)
    monitor = AlertMonitor(client, engine, config)
    
    if args.stop_loss:
        asset, pct = args.stop_loss.split(":")
        monitor.add_stop_loss(asset.upper(), float(pct))
    
    elif args.take_profit:
        asset, pct = args.take_profit.split(":")
        monitor.add_take_profit(asset.upper(), float(pct))
    
    elif args.trailing:
        asset, pct = args.trailing.split(":")
        monitor.add_trailing_stop(asset.upper(), float(pct))
    
    elif args.price:
        parts = args.price.split(":")
        asset = parts[0].upper()
        direction = parts[1]  # above/below
        price = float(parts[2])
        monitor.add_price_alert(asset, price, direction)
    
    elif args.remove:
        monitor.remove_alert(args.remove.upper())
    
    elif args.cost_basis:
        asset, price = args.cost_basis.split(":")
        monitor.set_cost_basis(asset.upper(), float(price))
    
    elif args.check:
        events = monitor.check_alerts()
        if events:
            print(f"\n🚨 {len(events)} alert(s) triggered!")
        else:
            print("✅ No alerts triggered")
    
    elif args.monitor:
        print("Starting alert monitor (Ctrl+C to stop)...")
        monitor.start_monitoring()
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
    
    else:
        monitor.display_alerts()


def cmd_trade(args):
    """Execute manual trades."""
    client = get_client()
    config = load_config_from_env()
    
    # Override mode if specified
    if args.paper:
        config.mode = TradingMode.PAPER
    elif args.live:
        config.mode = TradingMode.LIVE
    
    engine = TradingEngine(client, config)
    
    if args.buy:
        asset, amount = args.buy.split(":")
        result = engine.buy(asset.upper(), float(amount))
        _print_trade_result(result)
    
    elif args.sell:
        asset, amount = args.sell.split(":")
        result = engine.sell(asset.upper(), float(amount))
        _print_trade_result(result)
    
    elif args.preview:
        asset, side, amount = args.preview.split(":")
        preview = engine.preview_trade(
            f"{asset.upper()}-USD",
            side.upper(),
            usd_amount=float(amount) if side.upper() == "BUY" else None,
            asset_amount=float(amount) if side.upper() == "SELL" else None
        )
        import json
        print(json.dumps(preview, indent=2, default=str))
    
    elif args.status:
        summary = engine.get_trade_summary()
        print("\n📊 Trading Status")
        print(f"   Mode: {summary['mode']}")
        print(f"   Today's trades: {summary['today']['trades']}/{summary['limits']['max_trades_per_day']}")
        print(f"   Today's volume: ${summary['today']['volume_usd']:.2f}/${summary['limits']['max_daily_volume_usd']:.2f}")
    
    else:
        print("Specify --buy, --sell, or --preview")
        print("Examples:")
        print("  --buy BTC:100     Buy $100 of BTC")
        print("  --sell ETH:0.5    Sell 0.5 ETH")
        print("  --preview BTC:BUY:50  Preview buying $50 of BTC")


def _print_trade_result(result):
    """Print trade execution result."""
    if result.executed:
        print(f"\n✅ Trade executed!")
        print(f"   Order ID: {result.order_id}")
        print(f"   {result.side} {result.fill_amount:.8f} @ ${result.fill_price:.2f}")
        print(f"   Total: ${result.requested_usd:.2f}")
    else:
        print(f"\n❌ Trade failed: {result.error}")


def cmd_config(args):
    """View or modify configuration."""
    config = load_config_from_env()
    
    if args.show:
        print("\n📋 Current Configuration")
        print(f"\nMode: {config.mode.value}")
        
        print("\nSafety Limits:")
        print(f"  Max trade: ${config.safety.max_trade_usd}")
        print(f"  Max daily trades: {config.safety.max_trades_per_day}")
        print(f"  Max daily volume: ${config.safety.max_daily_volume_usd}")
        print(f"  Max sell %: {config.safety.max_sell_percent}%")
        print(f"  Cooldown: {config.safety.trade_cooldown_seconds}s")
        
        if config.rebalance.target_allocations:
            print("\nRebalance Targets:")
            for asset, pct in config.rebalance.target_allocations.items():
                print(f"  {asset}: {pct}%")
        
        if config.dca.dca_amounts:
            print(f"\nDCA ({config.dca.interval}):")
            for asset, amt in config.dca.dca_amounts.items():
                print(f"  {asset}: ${amt}")
    
    elif args.example:
        example = TradingConfig.load_example()
        print("\n📋 Example Configuration (Paper Trading)")
        print("\nCopy this to customize your settings:")
        print("""
from config import TradingConfig, TradingMode, SafetyLimits, RebalanceConfig, DCAConfig, AlertConfig

config = TradingConfig(
    mode=TradingMode.PAPER,  # Change to CONFIRM or LIVE when ready
    
    safety=SafetyLimits(
        max_trade_usd=100.0,
        max_trades_per_day=10,
        max_daily_volume_usd=500.0,
        blacklist=["SHIB", "DOGE"]
    ),
    
    rebalance=RebalanceConfig(
        target_allocations={
            "BTC": 50.0,
            "ETH": 30.0,
            "SOL": 20.0
        },
        rebalance_threshold=5.0
    ),
    
    dca=DCAConfig(
        dca_amounts={"BTC": 50, "ETH": 25},
        interval="weekly",
        day_of_week=0,  # Monday
        hour=9
    ),
    
    alerts=AlertConfig(
        stop_loss_percent={"BTC": -20, "ETH": -25},
        take_profit_percent={"BTC": 100, "ETH": 100}
    )
)
""")
    
    else:
        print("Use --show to view config or --example for a template")


def main():
    parser = argparse.ArgumentParser(
        description="Coinbase Trading Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Portfolio command
    port_parser = subparsers.add_parser("portfolio", help="View portfolio")
    port_parser.add_argument("--json", action="store_true", help="Output as JSON")
    port_parser.add_argument("--performance", "-p", action="store_true", help="Show performance")
    port_parser.add_argument("--underperformers", "-u", action="store_true", help="Show underperformers")
    
    # Rebalance command
    reb_parser = subparsers.add_parser("rebalance", help="Rebalance portfolio")
    reb_parser.add_argument("--targets", "-t", nargs="+", help="Target allocations (BTC:50 ETH:30)")
    reb_parser.add_argument("--execute", "-e", action="store_true", help="Execute trades")
    reb_parser.add_argument("--dry-run", "-d", action="store_true", help="Simulate only")
    
    # DCA command
    dca_parser = subparsers.add_parser("dca", help="Manage DCA schedules")
    dca_parser.add_argument("--add", "-a", help="Add schedule (BTC:50)")
    dca_parser.add_argument("--remove", "-r", help="Remove schedule (BTC)")
    dca_parser.add_argument("--interval", "-i", default="weekly", help="Interval for new schedules")
    dca_parser.add_argument("--run", action="store_true", help="Execute pending DCAs now")
    dca_parser.add_argument("--daemon", action="store_true", help="Run as background daemon")
    
    # Alerts command
    alert_parser = subparsers.add_parser("alerts", help="Manage price alerts")
    alert_parser.add_argument("--stop-loss", "-sl", help="Add stop-loss (BTC:-20)")
    alert_parser.add_argument("--take-profit", "-tp", help="Add take-profit (BTC:50)")
    alert_parser.add_argument("--trailing", "-tr", help="Add trailing stop (BTC:10)")
    alert_parser.add_argument("--price", "-p", help="Add price alert (BTC:above:50000)")
    alert_parser.add_argument("--remove", "-r", help="Remove alerts for asset")
    alert_parser.add_argument("--cost-basis", "-cb", help="Set cost basis (BTC:45000)")
    alert_parser.add_argument("--check", "-c", action="store_true", help="Check alerts now")
    alert_parser.add_argument("--monitor", "-m", action="store_true", help="Start monitoring daemon")
    
    # Trade command
    trade_parser = subparsers.add_parser("trade", help="Execute trades")
    trade_parser.add_argument("--buy", "-b", help="Buy asset (BTC:100 for $100)")
    trade_parser.add_argument("--sell", "-s", help="Sell asset (ETH:0.5 for 0.5 ETH)")
    trade_parser.add_argument("--preview", "-p", help="Preview trade (BTC:BUY:100)")
    trade_parser.add_argument("--status", action="store_true", help="Show trading status")
    trade_parser.add_argument("--paper", action="store_true", help="Paper trading mode")
    trade_parser.add_argument("--live", action="store_true", help="Live trading mode")
    
    # Config command
    cfg_parser = subparsers.add_parser("config", help="View/edit configuration")
    cfg_parser.add_argument("--show", "-s", action="store_true", help="Show current config")
    cfg_parser.add_argument("--example", "-e", action="store_true", help="Show example config")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        "portfolio": cmd_portfolio,
        "rebalance": cmd_rebalance,
        "dca": cmd_dca,
        "alerts": cmd_alerts,
        "trade": cmd_trade,
        "config": cmd_config
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
