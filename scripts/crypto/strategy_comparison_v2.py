#!/usr/bin/env python3
"""
Strategy Comparison v2 - Compare actual transactions vs theoretical strategies

Uses known historical prices for accurate comparison.
"""

import sys
import os
import csv
import asyncio
import aiohttp
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

TRANSACTION_DIR = '/home/dave/skippy/lib/python/crypto_trading/data/transactions'

# Historical BTC prices (monthly averages, approximate)
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

# Historical ETH prices (monthly averages, approximate)
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

@dataclass
class StrategyResult:
    name: str
    total_invested: Decimal
    final_value: Decimal
    total_return: Decimal
    return_pct: Decimal
    assets_held: Dict[str, Decimal]

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

def get_price(prices: Dict[str, Decimal], date: datetime) -> Decimal:
    """Get price for a given date from monthly prices."""
    month_key = date.strftime('%Y-%m')
    return prices.get(month_key, Decimal('0'))

def simulate_monthly_dca(
    monthly_investments: Dict[str, Decimal],
    prices: Dict[str, Decimal],
    asset: str
) -> StrategyResult:
    """Simulate DCA matching actual monthly investment amounts."""

    total_invested = Decimal('0')
    total_asset = Decimal('0')

    for month, amount in monthly_investments.items():
        price = prices.get(month, Decimal('0'))
        if price > 0 and amount > 0:
            bought = amount / price
            total_asset += bought
            total_invested += amount

    # Final value using last available price
    final_month = max(prices.keys())
    final_price = prices.get(final_month, Decimal('0'))
    final_value = total_asset * final_price
    total_return = final_value - total_invested
    return_pct = (total_return / total_invested * 100) if total_invested else Decimal('0')

    return StrategyResult(
        name=f"DCA into {asset}",
        total_invested=total_invested,
        final_value=final_value,
        total_return=total_return,
        return_pct=return_pct,
        assets_held={asset: total_asset}
    )

def simulate_lump_sum(
    total_to_invest: Decimal,
    start_month: str,
    prices: Dict[str, Decimal],
    asset: str
) -> StrategyResult:
    """Simulate lump sum at start."""

    start_price = prices.get(start_month, Decimal('0'))
    final_month = max(prices.keys())
    final_price = prices.get(final_month, Decimal('0'))

    if start_price <= 0 or final_price <= 0:
        return StrategyResult(
            name=f"Lump Sum {asset}",
            total_invested=Decimal('0'),
            final_value=Decimal('0'),
            total_return=Decimal('0'),
            return_pct=Decimal('0'),
            assets_held={}
        )

    total_asset = total_to_invest / start_price
    final_value = total_asset * final_price
    total_return = final_value - total_to_invest
    return_pct = (total_return / total_to_invest * 100) if total_to_invest else Decimal('0')

    return StrategyResult(
        name=f"Lump Sum {asset} (Jul 2023)",
        total_invested=total_to_invest,
        final_value=final_value,
        total_return=total_return,
        return_pct=return_pct,
        assets_held={asset: total_asset}
    )

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
        'NEAR': 'near', 'FIL': 'filecoin', 'INJ': 'injective-protocol',
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
        print(f"  Warning: Price fetch error: {e}")

    return prices

def calculate_actual_performance(
    transactions: List[dict],
    current_prices: Dict[str, Decimal]
) -> StrategyResult:
    """Calculate actual performance from transactions."""

    holdings: Dict[str, Decimal] = defaultdict(Decimal)
    total_invested = Decimal('0')
    total_sold = Decimal('0')
    staking_income = Decimal('0')

    for tx in transactions:
        asset = tx['asset']
        qty = tx['quantity']
        total = tx['total']
        tx_type = tx['type']

        if tx_type == 'Buy':
            holdings[asset] += qty
            total_invested += total
        elif tx_type == 'Sell':
            holdings[asset] -= qty
            total_sold += total
        elif tx_type == 'Staking Income':
            holdings[asset] += qty
            staking_income += tx['subtotal']
        elif tx_type == 'Send':
            holdings[asset] -= qty
        elif tx_type in ('Receive', 'Deposit'):
            holdings[asset] += qty

    # Calculate current value
    final_value = Decimal('0')
    assets_held = {}

    for asset, qty in holdings.items():
        if qty > 0:
            price = current_prices.get(asset, Decimal('0'))
            value = qty * price
            final_value += value
            if qty > 0:
                assets_held[asset] = qty

    # Net returns including sold and staking
    net_realized = total_sold + staking_income
    total_return = final_value + net_realized - total_invested
    return_pct = (total_return / total_invested * 100) if total_invested else Decimal('0')

    return StrategyResult(
        name="Your Actual Strategy",
        total_invested=total_invested,
        final_value=final_value + net_realized,
        total_return=total_return,
        return_pct=return_pct,
        assets_held=assets_held
    )

async def run_comparison():
    """Run full strategy comparison."""

    print("=" * 70)
    print("STRATEGY COMPARISON - Your Transactions vs Alternatives")
    print("=" * 70)

    # Load transactions
    print("\n📊 Loading transaction history...")
    transactions = load_transactions()
    print(f"   Loaded {len(transactions):,} transactions")

    # Calculate monthly investments
    buys = [tx for tx in transactions if tx['type'] == 'Buy']
    monthly_investments: Dict[str, Decimal] = defaultdict(Decimal)

    for tx in buys:
        month = tx['timestamp'].strftime('%Y-%m')
        monthly_investments[month] += tx['total']

    total_invested = sum(monthly_investments.values())
    start_month = min(monthly_investments.keys())
    end_month = max(monthly_investments.keys())

    print(f"   Period: {start_month} to {end_month}")
    print(f"   Total Invested: ${total_invested:,.2f}")
    print(f"   Active Months: {len(monthly_investments)}")

    # Show monthly breakdown
    print("\n📅 Monthly Investment Pattern:")
    print("-" * 50)
    for year in ['2023', '2024', '2025']:
        year_total = sum(v for k, v in monthly_investments.items() if k.startswith(year))
        if year_total > 0:
            print(f"   {year}: ${year_total:,.2f}")

    # Fetch current prices
    print("\n💰 Fetching current prices...")
    assets = list(set(tx['asset'] for tx in transactions if tx['type'] == 'Buy'))
    current_prices = await fetch_current_prices(assets)
    print(f"   Got prices for {len(current_prices)} assets")

    # Run simulations
    print("\n🔄 Running strategy simulations...")
    results = []

    # 1. DCA into BTC (matching your timing)
    dca_btc = simulate_monthly_dca(monthly_investments, BTC_PRICES, 'BTC')
    results.append(dca_btc)
    print(f"   ✓ {dca_btc.name}")

    # 2. DCA into ETH (matching your timing)
    dca_eth = simulate_monthly_dca(monthly_investments, ETH_PRICES, 'ETH')
    results.append(dca_eth)
    print(f"   ✓ {dca_eth.name}")

    # 3. Lump sum BTC at start
    lump_btc = simulate_lump_sum(total_invested, start_month, BTC_PRICES, 'BTC')
    results.append(lump_btc)
    print(f"   ✓ {lump_btc.name}")

    # 4. Lump sum ETH at start
    lump_eth = simulate_lump_sum(total_invested, start_month, ETH_PRICES, 'ETH')
    results.append(lump_eth)
    print(f"   ✓ {lump_eth.name}")

    # 5. 70/30 BTC/ETH DCA
    btc_portion = {k: v * Decimal('0.7') for k, v in monthly_investments.items()}
    eth_portion = {k: v * Decimal('0.3') for k, v in monthly_investments.items()}
    dca_btc_70 = simulate_monthly_dca(btc_portion, BTC_PRICES, 'BTC')
    dca_eth_30 = simulate_monthly_dca(eth_portion, ETH_PRICES, 'ETH')
    mixed_result = StrategyResult(
        name="70/30 BTC/ETH DCA",
        total_invested=dca_btc_70.total_invested + dca_eth_30.total_invested,
        final_value=dca_btc_70.final_value + dca_eth_30.final_value,
        total_return=dca_btc_70.total_return + dca_eth_30.total_return,
        return_pct=((dca_btc_70.total_return + dca_eth_30.total_return) / total_invested * 100),
        assets_held={'BTC': dca_btc_70.assets_held.get('BTC', Decimal('0')),
                     'ETH': dca_eth_30.assets_held.get('ETH', Decimal('0'))}
    )
    results.append(mixed_result)
    print(f"   ✓ {mixed_result.name}")

    # 6. Actual performance
    actual = calculate_actual_performance(transactions, current_prices)
    results.append(actual)
    print(f"   ✓ {actual.name}")

    # Print results
    print("\n" + "=" * 70)
    print("RESULTS COMPARISON")
    print("=" * 70)
    print(f"\n{'Strategy':<26} {'Invested':>12} {'Final Value':>14} {'Return':>12} {'%':>10}")
    print("-" * 70)

    # Sort by return %
    results.sort(key=lambda x: x.return_pct, reverse=True)

    for i, r in enumerate(results):
        marker = " 👈 YOU" if r.name == "Your Actual Strategy" else ""
        rank = f"#{i+1}"
        print(f"{rank:3} {r.name:<22} ${r.total_invested:>10,.0f} ${r.final_value:>12,.0f} ${r.total_return:>10,.0f} {r.return_pct:>+9.1f}%{marker}")

    print("-" * 70)

    # Analysis
    your_result = next(r for r in results if r.name == "Your Actual Strategy")
    best_result = results[0]
    your_rank = next(i for i, r in enumerate(results) if r.name == "Your Actual Strategy") + 1

    print(f"\n📊 ANALYSIS")
    print("-" * 70)
    print(f"Your Strategy Rank: #{your_rank} of {len(results)}")

    if your_rank == 1:
        print("🏆 Congratulations! Your strategy BEAT all alternatives!")
    else:
        diff_pct = best_result.return_pct - your_result.return_pct
        diff_value = best_result.final_value - your_result.final_value
        print(f"Best alternative: {best_result.name}")
        print(f"Performance gap: {diff_pct:.1f}% (${diff_value:,.0f})")

    print(f"\n💡 KEY INSIGHTS")
    print("-" * 70)

    # Calculate what $20k in BTC from start would be worth
    btc_start_price = BTC_PRICES.get('2023-07', Decimal('29500'))
    btc_end_price = BTC_PRICES.get('2025-12', Decimal('94000'))
    btc_gain = (btc_end_price / btc_start_price - 1) * 100
    print(f"• BTC went from ${btc_start_price:,.0f} (Jul 2023) to ${btc_end_price:,.0f} (Dec 2025) = +{btc_gain:.0f}%")

    eth_start_price = ETH_PRICES.get('2023-07', Decimal('1880'))
    eth_end_price = ETH_PRICES.get('2025-12', Decimal('2050'))
    eth_gain = (eth_end_price / eth_start_price - 1) * 100
    print(f"• ETH went from ${eth_start_price:,.0f} (Jul 2023) to ${eth_end_price:,.0f} (Dec 2025) = +{eth_gain:.0f}%")

    print(f"• You diversified across {len(actual.assets_held)} assets")
    print(f"• Many altcoins underperformed BTC during this period")

    if dca_btc.return_pct > lump_btc.return_pct:
        print(f"• DCA beat lump sum for BTC (entered at better avg price)")
    else:
        print(f"• Lump sum beat DCA for BTC (early entry captured more gains)")

    # Show what pure BTC DCA would have returned
    print(f"\n📈 IF YOU HAD DONE...")
    print("-" * 70)
    print(f"100% BTC DCA: ${dca_btc.final_value:,.0f} ({dca_btc.return_pct:+.1f}%)")
    print(f"100% ETH DCA: ${dca_eth.final_value:,.0f} ({dca_eth.return_pct:+.1f}%)")
    print(f"Your actual:  ${your_result.final_value:,.0f} ({your_result.return_pct:+.1f}%)")

def main():
    asyncio.run(run_comparison())

if __name__ == '__main__':
    main()
