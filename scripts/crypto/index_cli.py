#!/usr/bin/env python3
"""
Index Management CLI - Import holdings and generate allocation plans.

Usage:
    python index_cli.py import holdings.csv              # Import and analyze
    python index_cli.py import holdings.csv -c 100000   # With target capital
    python index_cli.py sort BTC ETH SOL ...            # Quick sort symbols
    python index_cli.py analyze BTC                      # Analyze single asset
"""

import asyncio
import argparse
import sys
from decimal import Decimal
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

from agents.index_manager import (
    IndexBuilder, IndexConfig, IndexRebalancer, IndexReporter,
    HoldingsImporter, AccountType, quick_sort,
    STABLECOINS, WRAPPED_ASSETS, EXCHANGE_TOKENS, PRIVACY_COINS,
    ASSET_SCORES, STAKING_RATES
)


def print_header():
    print("=" * 70)
    print("  CRYPTO INDEX MANAGER")
    print("  COIN50-Style Portfolio Construction")
    print("=" * 70)
    print()


async def cmd_import(args):
    """Import holdings from file and generate allocation plan"""
    print_header()
    
    filepath = args.file
    
    if not Path(filepath).exists():
        print(f"Error: File not found: {filepath}")
        return None
    
    print(f"Importing: {filepath}")
    print()
    
    holdings = HoldingsImporter.import_file(filepath)
    
    if not holdings:
        print("No holdings found in file.")
        print()
        print("Supported formats:")
        print("  CSV:  Symbol,Quantity,Value columns (flexible headers)")
        print("  TXT:  One symbol per line, optionally: SYMBOL QUANTITY VALUE")
        print("  JSON: Array of objects with symbol/quantity/value keys")
        return None
    
    print(f"Found {len(holdings)} holdings")
    
    config = IndexConfig(
        target_count=args.count,
        max_weight_pct=Decimal(str(args.max_weight)),
        personal_target_pct=Decimal(str(args.personal)),
        business_target_pct=Decimal(str(args.business)),
    )
    
    if args.exclude:
        config.manual_exclusions = set(s.strip().upper() for s in args.exclude.split(','))
    
    builder = IndexBuilder(config)
    
    total_capital = Decimal(str(args.capital)) if args.capital else None
    
    portfolio = await builder.build_from_holdings(
        holdings=holdings,
        name=args.name or f"Portfolio-{datetime.now().strftime('%Y%m%d')}",
        total_capital=total_capital,
        fetch_prices=not args.no_fetch
    )
    
    print()
    print(IndexReporter.summary(portfolio))
    
    if portfolio.total_value > 0 and not args.no_rebalance:
        print()
        rebalancer = IndexRebalancer(config)
        plan = rebalancer.generate_plan(portfolio)
        print(IndexReporter.rebalance_summary(plan))
    
    if args.output:
        if args.output.endswith('.csv'):
            content = IndexReporter.to_csv(portfolio)
        else:
            content = IndexReporter.summary(portfolio)
        
        with open(args.output, 'w') as f:
            f.write(content)
        print()
        print(f"Saved to: {args.output}")
    
    return portfolio


async def cmd_sort(args):
    """Quick sort symbols into personal vs business"""
    print_header()
    
    if not args.symbols:
        print("No symbols provided.")
        print("Usage: python index_cli.py sort BTC ETH SOL DOGE SHIB ...")
        return
    
    symbols = [s.upper() for s in args.symbols]
    print(f"Sorting {len(symbols)} symbols...\n")
    
    result = await quick_sort(symbols)
    
    personal, business, split, excluded = [], [], [], []
    
    for symbol, account in result.items():
        if account == AccountType.PERSONAL:
            personal.append(symbol)
        elif account == AccountType.BUSINESS:
            business.append(symbol)
        elif account == AccountType.SPLIT:
            split.append(symbol)
        else:
            excluded.append(symbol)
    
    print("-" * 50)
    print("PERSONAL (Coinbase One) - Staking & Active Trading")
    print("-" * 50)
    if personal:
        for sym in sorted(personal):
            stake = STAKING_RATES['coinbase'].get(sym)
            stake_str = f" ({stake:.1f}% APY)" if stake else ""
            print(f"  {sym}{stake_str}")
    else:
        print("  (none)")
    print()
    
    print("-" * 50)
    print("BUSINESS (Kraken) - Treasury & Long-Term")
    print("-" * 50)
    if business:
        for sym in sorted(business):
            print(f"  {sym}")
    else:
        print("  (none)")
    print()
    
    if split:
        print("-" * 50)
        print("SPLIT (Either Account)")
        print("-" * 50)
        print("  " + ", ".join(sorted(split)))
        print()
    
    if excluded:
        print("-" * 50)
        print("EXCLUDED (Not Recommended)")
        print("-" * 50)
        for symbol in sorted(excluded):
            reason = "Stablecoin" if symbol in STABLECOINS else \
                     "Wrapped asset" if symbol in WRAPPED_ASSETS else \
                     "Exchange token" if symbol in EXCHANGE_TOKENS else \
                     "Privacy coin" if symbol in PRIVACY_COINS else "Security concern"
            print(f"  {symbol}: {reason}")
    
    print()
    print(f"Summary: {len(personal)} personal, {len(business)} business, {len(split)} split, {len(excluded)} excluded")


async def cmd_analyze(args):
    """Analyze a single asset"""
    print_header()
    
    symbol = args.symbol.upper()
    print(f"Analyzing: {symbol}\n")
    
    # Check exclusions
    if symbol in STABLECOINS:
        print(f"  {symbol} is a STABLECOIN - excluded from index")
        return
    if symbol in WRAPPED_ASSETS:
        print(f"  {symbol} is a WRAPPED ASSET - excluded from index")
        return
    if symbol in EXCHANGE_TOKENS:
        print(f"  {symbol} is an EXCHANGE TOKEN - excluded from index")
        return
    if symbol in PRIVACY_COINS:
        print(f"  {symbol} is a PRIVACY COIN - excluded from index")
        return
    
    if symbol in ASSET_SCORES:
        score = ASSET_SCORES[symbol]
        print(f"Pre-defined scores for {symbol}:")
        print()
        print("  BUSINESS FACTORS (higher = more suited for Kraken)")
        print(f"    Treasury Suitability:   {'★' * score.treasury_suitability}{'☆' * (5-score.treasury_suitability)} ({score.treasury_suitability}/5)")
        print(f"    Regulatory Clarity:     {'★' * score.regulatory_clarity}{'☆' * (5-score.regulatory_clarity)} ({score.regulatory_clarity}/5)")
        print(f"    Institutional Adoption: {'★' * score.institutional_adoption}{'☆' * (5-score.institutional_adoption)} ({score.institutional_adoption}/5)")
        print()
        print("  PERSONAL FACTORS (higher = more suited for Coinbase One)")
        print(f"    Volatility:             {'●' * score.volatility}{'○' * (5-score.volatility)} ({score.volatility}/5)")
        print(f"    Staking Advantage:      {'◆' * score.staking_advantage}{'◇' * (5-score.staking_advantage)} ({score.staking_advantage}/5)")
        print(f"    Trade Frequency:        {'▸' * score.trade_frequency}{'▹' * (5-score.trade_frequency)} ({score.trade_frequency}/5)")
        print(f"    Speculation Level:      {'!' * score.speculation_level}{'·' * (5-score.speculation_level)} ({score.speculation_level}/5)")
        print()
        print(f"  SCORES")
        print(f"    Personal Score: {score.personal_score:.2f}")
        print(f"    Business Score: {score.business_score:.2f}")
        print()
        
        cb_stake = STAKING_RATES['coinbase'].get(symbol)
        kr_stake = STAKING_RATES['kraken'].get(symbol)
        if cb_stake or kr_stake:
            print(f"  STAKING RATES")
            if cb_stake:
                print(f"    Coinbase One: {cb_stake:.1f}% APY")
            if kr_stake:
                print(f"    Kraken:       {kr_stake:.1f}% APY")
            print()
        
        rec = score.recommended_account.value.upper()
        print(f"  RECOMMENDATION: {rec}")
    else:
        result = await quick_sort([symbol])
        account = result.get(symbol, AccountType.SPLIT)
        print(f"No pre-defined score for {symbol}")
        print(f"Default recommendation: {account.value.upper()}")
        print()
        print("  This asset will be auto-scored based on market data when imported.")


async def cmd_help(args):
    """Show help"""
    print_header()
    print("""
COMMANDS
========

  import FILE    Import holdings from file and generate allocation plan
  sort SYMBOLS   Quick sort symbols into Personal vs Business  
  analyze SYMBOL Analyze a single asset with detailed scoring
  help           Show this help

IMPORT COMMAND
==============

  python index_cli.py import holdings.csv
  python index_cli.py import holdings.csv -c 100000
  python index_cli.py import holdings.csv -p 50 -b 50 -o output.csv

  Options:
    -c, --capital     Target total capital (default: sum of holdings)
    -p, --personal    Percentage to personal account (default: 40)
    -b, --business    Percentage to business account (default: 60)
    -w, --max-weight  Maximum weight per asset (default: 40%)
    -e, --exclude     Symbols to exclude (comma-separated)
    -o, --output      Output file (csv or txt)
    --no-fetch        Skip fetching live prices
    --no-rebalance    Skip generating rebalance plan

FILE FORMATS
============

  CSV (recommended):
    Symbol,Quantity,Value
    BTC,0.5,45000
    ETH,5,15000
    
  TXT (one per line):
    BTC 0.5 45000
    ETH 5 15000
    SOL
    
  JSON:
    [{"symbol": "BTC", "quantity": 0.5, "value": 45000}, ...]

EXAMPLES
========

  # Import your holdings
  python index_cli.py import my_holdings.csv
  
  # Import with $100k target, 50/50 split
  python index_cli.py import holdings.csv -c 100000 -p 50 -b 50
  
  # Quick sort symbols
  python index_cli.py sort BTC ETH SOL DOGE SHIB XMR USDT
  
  # Analyze single asset
  python index_cli.py analyze SOL
""")


def main():
    parser = argparse.ArgumentParser(description="Crypto Index Manager")
    subparsers = parser.add_subparsers(dest='cmd', help='Command')
    
    # Import
    import_p = subparsers.add_parser('import', help='Import holdings')
    import_p.add_argument('file', help='Holdings file')
    import_p.add_argument('-c', '--capital', type=float, help='Target capital')
    import_p.add_argument('-p', '--personal', type=float, default=40, help='Personal %')
    import_p.add_argument('-b', '--business', type=float, default=60, help='Business %')
    import_p.add_argument('-w', '--max-weight', type=float, default=40, help='Max weight %')
    import_p.add_argument('-n', '--count', type=int, default=100, help='Max assets')
    import_p.add_argument('-e', '--exclude', type=str, help='Exclude symbols')
    import_p.add_argument('-o', '--output', type=str, help='Output file')
    import_p.add_argument('--name', type=str, help='Portfolio name')
    import_p.add_argument('--no-fetch', action='store_true', help='Skip price fetch')
    import_p.add_argument('--no-rebalance', action='store_true', help='Skip rebalance')
    
    # Sort
    sort_p = subparsers.add_parser('sort', help='Sort symbols')
    sort_p.add_argument('symbols', nargs='*', help='Symbols')
    
    # Analyze
    analyze_p = subparsers.add_parser('analyze', help='Analyze asset')
    analyze_p.add_argument('symbol', help='Symbol')
    
    # Help
    subparsers.add_parser('help', help='Show help')
    
    args = parser.parse_args()
    
    if not args.cmd or args.cmd == 'help':
        asyncio.run(cmd_help(args))
    elif args.cmd == 'import':
        asyncio.run(cmd_import(args))
    elif args.cmd == 'sort':
        asyncio.run(cmd_sort(args))
    elif args.cmd == 'analyze':
        asyncio.run(cmd_analyze(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
