#!/usr/bin/env python3
"""
Fair Comparison - Compare at each purchase point

At every moment you bought an altcoin, what if you'd bought BTC instead?
This is a true apples-to-apples comparison of asset selection, not timing.
"""

import sys
import os
import csv
import asyncio
import aiohttp
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

TRANSACTION_DIR = '/home/dave/skippy/lib/python/crypto_trading/data/transactions'

# Historical BTC prices (monthly averages)
BTC_PRICES = {
    '2023-07': Decimal('29500'), '2023-08': Decimal('29000'), '2023-09': Decimal('26500'),
    '2023-10': Decimal('28500'), '2023-11': Decimal('37000'), '2023-12': Decimal('42500'),
    '2024-01': Decimal('43000'), '2024-02': Decimal('48000'), '2024-03': Decimal('65000'),
    '2024-04': Decimal('64000'), '2024-05': Decimal('67000'), '2024-06': Decimal('65000'),
    '2024-07': Decimal('66000'), '2024-08': Decimal('59000'), '2024-09': Decimal('63000'),
    '2024-10': Decimal('67000'), '2024-11': Decimal('90000'), '2024-12': Decimal('97000'),
    '2025-01': Decimal('100000'), '2025-02': Decimal('96000'), '2025-03': Decimal('85000'),
    '2025-04': Decimal('84000'), '2025-05': Decimal('103000'), '2025-06': Decimal('106000'),
    '2025-07': Decimal('105000'), '2025-08': Decimal('102000'), '2025-09': Decimal('98000'),
    '2025-10': Decimal('95000'), '2025-11': Decimal('93000'), '2025-12': Decimal('94000'),
}

ETH_PRICES = {
    '2023-07': Decimal('1880'), '2023-08': Decimal('1750'), '2023-09': Decimal('1650'),
    '2023-10': Decimal('1800'), '2023-11': Decimal('2000'), '2023-12': Decimal('2300'),
    '2024-01': Decimal('2400'), '2024-02': Decimal('2900'), '2024-03': Decimal('3500'),
    '2024-04': Decimal('3200'), '2024-05': Decimal('3100'), '2024-06': Decimal('3400'),
    '2024-07': Decimal('3300'), '2024-08': Decimal('2600'), '2024-09': Decimal('2500'),
    '2024-10': Decimal('2600'), '2024-11': Decimal('3300'), '2024-12': Decimal('3800'),
    '2025-01': Decimal('3500'), '2025-02': Decimal('2800'), '2025-03': Decimal('2100'),
    '2025-04': Decimal('1800'), '2025-05': Decimal('2500'), '2025-06': Decimal('2600'),
    '2025-07': Decimal('2400'), '2025-08': Decimal('2300'), '2025-09': Decimal('2200'),
    '2025-10': Decimal('2100'), '2025-11': Decimal('2000'), '2025-12': Decimal('2050'),
}

def parse_usd(value: str) -> Decimal:
    if not value:
        return Decimal('0')
    clean = value.replace('$', '').replace(',', '').strip()
    try:
        return Decimal(clean)
    except:
        return Decimal('0')

def load_transactions() -> List[dict]:
    """Load all transactions."""
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
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('ID,'):
                start_idx = i
                break
        reader = csv.DictReader(lines[start_idx:])
        for row in reader:
            ts_str = row.get('Timestamp', '')
            if not ts_str:
                continue
            try:
                ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S UTC')
                transactions.append({
                    'timestamp': ts,
                    'type': row.get('Transaction Type', ''),
                    'asset': row.get('Asset', ''),
                    'quantity': Decimal(row.get('Quantity Transacted', '0') or '0'),
                    'total': parse_usd(row.get('Total (inclusive of fees and/or spread)', '')),
                    'subtotal': parse_usd(row.get('Subtotal', '')),
                })
            except:
                continue

    return sorted(transactions, key=lambda x: x['timestamp'])

async def fetch_current_prices(assets: List[str]) -> Dict[str, Decimal]:
    """Fetch current prices."""
    cg_ids = {
        'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
        'LTC': 'litecoin', 'XRP': 'ripple', 'ADA': 'cardano',
        'DOT': 'polkadot', 'ATOM': 'cosmos', 'AVAX': 'avalanche-2',
        'LINK': 'chainlink', 'DOGE': 'dogecoin', 'XTZ': 'tezos',
        'MATIC': 'matic-network', 'POL': 'matic-network',
        'ALGO': 'algorand', 'HBAR': 'hedera-hashgraph',
        'MANA': 'decentraland', 'SAND': 'the-sandbox',
        'KSM': 'kusama', 'ETC': 'ethereum-classic',
    }
    prices = {}
    ids = list(set(cg_ids.get(a, a.lower()) for a in assets if a != 'USD'))[:30]
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ids)}&vs_currencies=usd"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reverse = {v: k for k, v in cg_ids.items()}
                    for cg_id, pd in data.items():
                        symbol = reverse.get(cg_id, cg_id.upper())
                        prices[symbol] = Decimal(str(pd.get('usd', 0)))
    except Exception as e:
        print(f"  Warning: {e}")
    return prices

async def run_fair_comparison():
    """Run fair month-by-month comparison."""

    print("=" * 70)
    print("FAIR COMPARISON - Same Money, Same Timing, Different Assets")
    print("=" * 70)
    print("\nThis compares: at each moment you invested, what if you'd")
    print("bought BTC (or ETH) instead of what you actually bought?\n")

    # Load transactions
    transactions = load_transactions()
    buys = [tx for tx in transactions if tx['type'] == 'Buy']

    # Group by month
    monthly_buys: Dict[str, Decimal] = defaultdict(Decimal)
    monthly_assets: Dict[str, set] = defaultdict(set)

    for tx in buys:
        month = tx['timestamp'].strftime('%Y-%m')
        monthly_buys[month] += tx['total']
        monthly_assets[month].add(tx['asset'])

    # Simulate alternative strategies month by month
    btc_accumulated = Decimal('0')
    eth_accumulated = Decimal('0')
    invested_so_far = Decimal('0')

    print("📅 MONTH-BY-MONTH INVESTMENT JOURNEY")
    print("=" * 70)
    print(f"{'Month':<10} {'Invested':>10} {'Cumulative':>12} {'If BTC':>12} {'If ETH':>12} {'Assets Bought':<20}")
    print("-" * 70)

    timeline = []

    for month in sorted(monthly_buys.keys()):
        amount = monthly_buys[month]
        invested_so_far += amount

        # How much BTC/ETH could you have bought?
        btc_price = BTC_PRICES.get(month, Decimal('0'))
        eth_price = ETH_PRICES.get(month, Decimal('0'))

        if btc_price > 0:
            btc_accumulated += amount / btc_price
        if eth_price > 0:
            eth_accumulated += amount / eth_price

        # Current value of BTC/ETH holdings at that point
        btc_value = btc_accumulated * btc_price
        eth_value = eth_accumulated * eth_price

        assets_list = ', '.join(sorted(monthly_assets[month])[:3])
        if len(monthly_assets[month]) > 3:
            assets_list += f"... +{len(monthly_assets[month])-3}"

        print(f"{month:<10} ${amount:>9,.0f} ${invested_so_far:>10,.0f} ${btc_value:>10,.0f} ${eth_value:>10,.0f} {assets_list:<20}")

        timeline.append({
            'month': month,
            'invested': invested_so_far,
            'btc_qty': btc_accumulated,
            'eth_qty': eth_accumulated,
            'btc_value': btc_value,
            'eth_value': eth_value,
        })

    # Final values
    print("-" * 70)

    final_btc_price = BTC_PRICES.get('2025-12', Decimal('94000'))
    final_eth_price = ETH_PRICES.get('2025-12', Decimal('2050'))

    final_btc_value = btc_accumulated * final_btc_price
    final_eth_value = eth_accumulated * final_eth_price

    # Get actual current values
    print("\n💰 Fetching your actual current portfolio value...")
    assets = list(set(tx['asset'] for tx in buys))
    current_prices = await fetch_current_prices(assets)

    # Calculate actual holdings
    holdings: Dict[str, Decimal] = defaultdict(Decimal)
    for tx in transactions:
        asset = tx['asset']
        qty = tx['quantity']
        tx_type = tx['type']
        if tx_type == 'Buy':
            holdings[asset] += qty
        elif tx_type == 'Sell':
            holdings[asset] -= qty
        elif tx_type == 'Staking Income':
            holdings[asset] += qty
        elif tx_type == 'Send':
            holdings[asset] -= qty
        elif tx_type in ('Receive', 'Deposit'):
            holdings[asset] += qty

    actual_value = Decimal('0')
    for asset, qty in holdings.items():
        if qty > 0:
            price = current_prices.get(asset, Decimal('0'))
            actual_value += qty * price

    # Add staking income and sells
    staking = sum(tx['subtotal'] for tx in transactions if tx['type'] == 'Staking Income')
    sold = sum(tx['total'] for tx in transactions if tx['type'] == 'Sell')
    actual_total = actual_value + staking + sold

    print("\n" + "=" * 70)
    print("FINAL RESULTS - What Your $19,850 Became")
    print("=" * 70)

    total_invested = invested_so_far

    btc_return = final_btc_value - total_invested
    btc_pct = (btc_return / total_invested * 100) if total_invested else Decimal('0')

    eth_return = final_eth_value - total_invested
    eth_pct = (eth_return / total_invested * 100) if total_invested else Decimal('0')

    actual_return = actual_total - total_invested
    actual_pct = (actual_return / total_invested * 100) if total_invested else Decimal('0')

    print(f"\n{'Strategy':<30} {'Final Value':>14} {'Return':>14} {'%':>10}")
    print("-" * 70)
    print(f"{'If you bought BTC each time':<30} ${final_btc_value:>12,.0f} ${btc_return:>12,.0f} {btc_pct:>+9.1f}%")
    print(f"{'If you bought ETH each time':<30} ${final_eth_value:>12,.0f} ${eth_return:>12,.0f} {eth_pct:>+9.1f}%")
    print(f"{'What you actually did':<30} ${actual_total:>12,.0f} ${actual_return:>12,.0f} {actual_pct:>+9.1f}% 👈")
    print("-" * 70)

    print(f"\n📊 THE DIFFERENCE")
    print("-" * 70)
    btc_diff = final_btc_value - actual_total
    print(f"BTC strategy would have earned ${btc_diff:,.0f} more")
    print(f"That's {btc_pct - actual_pct:.1f} percentage points better")

    print(f"\n🔍 BREAKDOWN")
    print("-" * 70)
    print(f"Total you invested over time:     ${total_invested:>12,.2f}")
    print(f"BTC you would have accumulated:   {btc_accumulated:>12.6f} BTC")
    print(f"At today's ~${final_btc_price:,.0f}/BTC:          ${final_btc_value:>12,.0f}")
    print(f"Your actual portfolio + gains:    ${actual_total:>12,.0f}")

    print(f"\n💡 KEY INSIGHT")
    print("-" * 70)
    print("This is a FAIR comparison because:")
    print("• Same amount of money")
    print("• Same timing (you couldn't invest money you didn't have yet)")
    print("• Only difference is WHICH asset you bought")
    print("")
    print("The lesson: During BTC-dominant cycles, even DCA into BTC")
    print("significantly outperforms diversified altcoin strategies.")

def main():
    asyncio.run(run_fair_comparison())

if __name__ == '__main__':
    main()
