#!/usr/bin/env python3
"""
Transaction Analyzer - Analyze actual Coinbase transaction history

Analyzes your real transactions and compares performance against:
- Buy & Hold (if you bought everything at start)
- Pure DCA (equal buys regardless of conditions)
- Signal-adjusted DCA (what the system would recommend)

Usage:
    python transaction_analyzer.py analyze
    python transaction_analyzer.py summary
    python transaction_analyzer.py compare
"""

import csv
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import asyncio

# Add crypto_trading to path
sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

TRANSACTION_DIR = '/home/dave/skippy/lib/python/crypto_trading/data/transactions'

@dataclass
class Transaction:
    id: str
    timestamp: datetime
    tx_type: str
    asset: str
    quantity: Decimal
    price_usd: Decimal
    subtotal: Decimal
    total: Decimal
    fees: Decimal
    notes: str

@dataclass
class AssetSummary:
    symbol: str
    total_bought: Decimal = Decimal('0')
    total_sold: Decimal = Decimal('0')
    total_staking: Decimal = Decimal('0')
    total_fees: Decimal = Decimal('0')
    quantity_held: Decimal = Decimal('0')
    cost_basis: Decimal = Decimal('0')
    buy_count: int = 0
    sell_count: int = 0
    staking_count: int = 0
    first_buy: Optional[datetime] = None
    last_buy: Optional[datetime] = None

@dataclass
class YearlySummary:
    year: int
    total_invested: Decimal = Decimal('0')
    total_sold: Decimal = Decimal('0')
    total_staking: Decimal = Decimal('0')
    total_fees: Decimal = Decimal('0')
    transaction_count: int = 0
    unique_assets: set = field(default_factory=set)

def parse_usd(value: str) -> Decimal:
    """Parse USD string like '$1,234.56' to Decimal."""
    if not value or value == '':
        return Decimal('0')
    clean = value.replace('$', '').replace(',', '').strip()
    try:
        return Decimal(clean)
    except:
        return Decimal('0')

def load_transactions(year: Optional[int] = None) -> List[Transaction]:
    """Load transactions from CSV files."""
    transactions = []

    files = [
        f'{TRANSACTION_DIR}/coinbase_transactions_2023.csv',
        f'{TRANSACTION_DIR}/coinbase_transactions_2024.csv',
        f'{TRANSACTION_DIR}/coinbase_transactions_2025.csv',
    ]

    for filepath in files:
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r') as f:
            lines = f.readlines()

        # Find header line
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('ID,'):
                start_idx = i
                break

        reader = csv.DictReader(lines[start_idx:])
        for row in reader:
            try:
                ts_str = row.get('Timestamp', '')
                if not ts_str:
                    continue

                ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S UTC')

                if year and ts.year != year:
                    continue

                tx = Transaction(
                    id=row.get('ID', ''),
                    timestamp=ts,
                    tx_type=row.get('Transaction Type', ''),
                    asset=row.get('Asset', ''),
                    quantity=Decimal(row.get('Quantity Transacted', '0') or '0'),
                    price_usd=parse_usd(row.get('Price at Transaction', '')),
                    subtotal=parse_usd(row.get('Subtotal', '')),
                    total=parse_usd(row.get('Total (inclusive of fees and/or spread)', '')),
                    fees=parse_usd(row.get('Fees and/or Spread', '')),
                    notes=row.get('Notes', ''),
                )
                transactions.append(tx)
            except Exception as e:
                continue

    return sorted(transactions, key=lambda x: x.timestamp)

def analyze_by_asset(transactions: List[Transaction]) -> Dict[str, AssetSummary]:
    """Analyze transactions grouped by asset."""
    assets: Dict[str, AssetSummary] = {}

    for tx in transactions:
        if tx.asset not in assets:
            assets[tx.asset] = AssetSummary(symbol=tx.asset)

        summary = assets[tx.asset]

        if tx.tx_type == 'Buy':
            summary.total_bought += tx.total
            summary.quantity_held += tx.quantity
            summary.cost_basis += tx.total
            summary.buy_count += 1
            summary.total_fees += tx.fees
            if not summary.first_buy:
                summary.first_buy = tx.timestamp
            summary.last_buy = tx.timestamp

        elif tx.tx_type == 'Sell':
            summary.total_sold += tx.total
            summary.quantity_held -= tx.quantity
            summary.sell_count += 1
            summary.total_fees += tx.fees

        elif tx.tx_type == 'Staking Income':
            summary.total_staking += tx.subtotal
            summary.quantity_held += tx.quantity
            summary.staking_count += 1

        elif tx.tx_type == 'Send':
            summary.quantity_held -= tx.quantity

        elif tx.tx_type in ('Receive', 'Deposit'):
            summary.quantity_held += tx.quantity

    return assets

def analyze_by_year(transactions: List[Transaction]) -> Dict[int, YearlySummary]:
    """Analyze transactions grouped by year."""
    years: Dict[int, YearlySummary] = {}

    for tx in transactions:
        year = tx.timestamp.year
        if year not in years:
            years[year] = YearlySummary(year=year)

        summary = years[year]
        summary.transaction_count += 1
        summary.unique_assets.add(tx.asset)

        if tx.tx_type == 'Buy':
            summary.total_invested += tx.total
            summary.total_fees += tx.fees
        elif tx.tx_type == 'Sell':
            summary.total_sold += tx.total
            summary.total_fees += tx.fees
        elif tx.tx_type == 'Staking Income':
            summary.total_staking += tx.subtotal

    return years

def analyze_dca_pattern(transactions: List[Transaction]) -> Dict:
    """Analyze DCA buying patterns."""
    buys = [tx for tx in transactions if tx.tx_type == 'Buy']

    if len(buys) < 2:
        return {'pattern': 'insufficient_data'}

    # Group by day
    daily_buys: Dict[str, Decimal] = defaultdict(Decimal)
    for tx in buys:
        day = tx.timestamp.strftime('%Y-%m-%d')
        daily_buys[day] += tx.total

    # Calculate stats
    amounts = list(daily_buys.values())
    avg_daily = sum(amounts) / len(amounts)

    # Calculate variance from average
    variance = sum((a - avg_daily) ** 2 for a in amounts) / len(amounts)
    std_dev = variance ** Decimal('0.5')

    # Determine pattern
    cv = std_dev / avg_daily if avg_daily else Decimal('0')

    if cv < Decimal('0.3'):
        pattern = 'consistent_dca'
    elif cv < Decimal('0.7'):
        pattern = 'variable_dca'
    else:
        pattern = 'opportunistic'

    return {
        'pattern': pattern,
        'total_buy_days': len(daily_buys),
        'avg_daily_buy': float(avg_daily),
        'std_deviation': float(std_dev),
        'coefficient_of_variation': float(cv),
        'total_invested': float(sum(amounts)),
    }

async def get_current_prices(assets: List[str]) -> Dict[str, Decimal]:
    """Fetch current prices from CoinGecko."""
    import aiohttp

    # Map common symbols to CoinGecko IDs
    symbol_map = {
        'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
        'ADA': 'cardano', 'DOT': 'polkadot', 'ATOM': 'cosmos',
        'XRP': 'ripple', 'DOGE': 'dogecoin', 'LTC': 'litecoin',
        'LINK': 'chainlink', 'AVAX': 'avalanche-2', 'MATIC': 'matic-network',
        'XTZ': 'tezos', 'ALGO': 'algorand', 'HBAR': 'hedera-hashgraph',
        'MANA': 'decentraland', 'SAND': 'the-sandbox', 'KSM': 'kusama',
        'INJ': 'injective-protocol', 'POL': 'matic-network',
        'NEAR': 'near', 'FIL': 'filecoin', 'ICP': 'internet-computer',
        'UNI': 'uniswap', 'AAVE': 'aave', 'GRT': 'the-graph',
    }

    prices = {}
    ids = [symbol_map.get(a, a.lower()) for a in assets if a != 'USD']
    ids = list(set(ids))[:50]  # Limit to 50 for API

    if not ids:
        return prices

    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ids)}&vs_currencies=usd"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Reverse map
                    reverse_map = {v: k for k, v in symbol_map.items()}
                    for cg_id, price_data in data.items():
                        symbol = reverse_map.get(cg_id, cg_id.upper())
                        prices[symbol] = Decimal(str(price_data.get('usd', 0)))
    except Exception as e:
        print(f"Warning: Could not fetch prices: {e}")

    return prices

def print_summary(transactions: List[Transaction]):
    """Print comprehensive summary."""
    print("=" * 70)
    print("COINBASE TRANSACTION ANALYSIS")
    print("=" * 70)

    # Yearly summary
    years = analyze_by_year(transactions)
    print("\n📅 YEARLY SUMMARY")
    print("-" * 70)
    print(f"{'Year':<8} {'Transactions':>12} {'Invested':>14} {'Sold':>12} {'Staking':>12} {'Fees':>10}")
    print("-" * 70)

    total_invested = Decimal('0')
    total_sold = Decimal('0')
    total_staking = Decimal('0')
    total_fees = Decimal('0')

    for year in sorted(years.keys()):
        s = years[year]
        total_invested += s.total_invested
        total_sold += s.total_sold
        total_staking += s.total_staking
        total_fees += s.total_fees
        print(f"{year:<8} {s.transaction_count:>12,} ${s.total_invested:>12,.2f} ${s.total_sold:>10,.2f} ${s.total_staking:>10,.2f} ${s.total_fees:>8,.2f}")

    print("-" * 70)
    print(f"{'TOTAL':<8} {len(transactions):>12,} ${total_invested:>12,.2f} ${total_sold:>10,.2f} ${total_staking:>10,.2f} ${total_fees:>8,.2f}")

    # Asset summary
    assets = analyze_by_asset(transactions)
    print("\n💰 TOP HOLDINGS BY INVESTMENT")
    print("-" * 70)
    print(f"{'Asset':<8} {'Invested':>12} {'Quantity':>14} {'Cost Basis':>12} {'Staking':>10} {'Buys':>6}")
    print("-" * 70)

    sorted_assets = sorted(assets.items(), key=lambda x: x[1].total_bought, reverse=True)
    for symbol, s in sorted_assets[:20]:
        if s.total_bought > 0:
            avg_price = s.cost_basis / s.quantity_held if s.quantity_held else Decimal('0')
            print(f"{symbol:<8} ${s.total_bought:>10,.2f} {float(s.quantity_held):>14.6f} ${s.cost_basis:>10,.2f} ${s.total_staking:>8,.2f} {s.buy_count:>6}")

    # DCA pattern analysis
    dca = analyze_dca_pattern(transactions)
    print("\n📊 DCA PATTERN ANALYSIS")
    print("-" * 70)
    print(f"Pattern Type: {dca.get('pattern', 'unknown').replace('_', ' ').title()}")
    print(f"Total Buy Days: {dca.get('total_buy_days', 0):,}")
    print(f"Average Daily Buy: ${dca.get('avg_daily_buy', 0):,.2f}")
    print(f"Consistency (CV): {dca.get('coefficient_of_variation', 0):.2%}")

    # Transaction type breakdown
    print("\n📋 TRANSACTION TYPES")
    print("-" * 70)
    tx_types = defaultdict(int)
    for tx in transactions:
        tx_types[tx.tx_type] += 1

    for tx_type, count in sorted(tx_types.items(), key=lambda x: -x[1]):
        print(f"  {tx_type:<25} {count:>8,}")

async def print_portfolio_value(transactions: List[Transaction]):
    """Calculate and print current portfolio value."""
    assets = analyze_by_asset(transactions)

    # Get symbols with holdings
    symbols = [s for s, a in assets.items() if a.quantity_held > 0 and s != 'USD']

    print("\n💎 CURRENT PORTFOLIO VALUE")
    print("-" * 70)
    print("Fetching current prices...")

    prices = await get_current_prices(symbols)

    print(f"\n{'Asset':<8} {'Quantity':>14} {'Price':>12} {'Value':>14} {'Cost Basis':>12} {'P/L':>12}")
    print("-" * 70)

    total_value = Decimal('0')
    total_cost = Decimal('0')

    for symbol in sorted(symbols, key=lambda s: assets[s].total_bought, reverse=True)[:25]:
        a = assets[symbol]
        if a.quantity_held <= 0:
            continue

        price = prices.get(symbol, Decimal('0'))
        value = a.quantity_held * price
        cost = a.cost_basis
        pl = value - cost

        total_value += value
        total_cost += cost

        if price > 0:
            print(f"{symbol:<8} {float(a.quantity_held):>14.6f} ${price:>10,.2f} ${value:>12,.2f} ${cost:>10,.2f} ${pl:>10,.2f}")

    print("-" * 70)
    total_pl = total_value - total_cost
    pl_pct = (total_pl / total_cost * 100) if total_cost else Decimal('0')
    print(f"{'TOTAL':<8} {'':<14} {'':<12} ${total_value:>12,.2f} ${total_cost:>10,.2f} ${total_pl:>10,.2f}")
    print(f"\nUnrealized P/L: ${total_pl:,.2f} ({pl_pct:+.1f}%)")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analyze Coinbase transaction history')
    parser.add_argument('command', choices=['analyze', 'summary', 'portfolio', 'compare', 'assets'],
                       default='analyze', nargs='?', help='Command to run')
    parser.add_argument('-y', '--year', type=int, help='Filter by year')
    parser.add_argument('-a', '--asset', type=str, help='Filter by asset')

    args = parser.parse_args()

    print("Loading transactions...")
    transactions = load_transactions(args.year)
    print(f"Loaded {len(transactions):,} transactions")

    if args.command == 'analyze' or args.command == 'summary':
        print_summary(transactions)
        asyncio.run(print_portfolio_value(transactions))

    elif args.command == 'portfolio':
        asyncio.run(print_portfolio_value(transactions))

    elif args.command == 'assets':
        assets = analyze_by_asset(transactions)
        print("\n📊 ALL ASSETS")
        print("-" * 70)
        for symbol, a in sorted(assets.items(), key=lambda x: x[1].total_bought, reverse=True):
            if a.total_bought > 0 or a.total_staking > 0:
                print(f"{symbol}: Invested=${a.total_bought:.2f}, Staking=${a.total_staking:.2f}, Qty={a.quantity_held:.6f}")

    elif args.command == 'compare':
        print("\n📈 STRATEGY COMPARISON")
        print("-" * 70)
        print("Comparing your actual performance vs theoretical strategies...")
        print("(This would compare against pure DCA, buy & hold, and signal-based)")
        # TODO: Implement full strategy comparison

if __name__ == '__main__':
    main()
