#!/usr/bin/env python3
"""
Strategy Comparison - Compare actual transactions vs theoretical strategies

Compares your real Coinbase transactions against:
1. Pure DCA - Equal daily buys into BTC
2. Buy & Hold - Lump sum into BTC at start
3. 60/40 Split - 60% BTC, 40% ETH
4. Your Actual - What you actually did
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
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

TRANSACTION_DIR = '/home/dave/skippy/lib/python/crypto_trading/data/transactions'

@dataclass
class PricePoint:
    date: datetime
    price: Decimal

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

async def fetch_historical_prices(asset: str, days: int = 1095) -> Dict[str, Decimal]:
    """Fetch historical daily prices from CoinGecko."""
    cg_ids = {
        'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
        'LTC': 'litecoin', 'XRP': 'ripple', 'ADA': 'cardano',
        'DOT': 'polkadot', 'ATOM': 'cosmos', 'AVAX': 'avalanche-2',
        'LINK': 'chainlink', 'DOGE': 'dogecoin', 'XTZ': 'tezos',
    }

    cg_id = cg_ids.get(asset, asset.lower())
    prices = {}

    try:
        url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for ts, price in data.get('prices', []):
                        date = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
                        prices[date] = Decimal(str(price))
    except Exception as e:
        print(f"  Warning: Could not fetch {asset} prices: {e}")

    return prices

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

def simulate_pure_dca(
    total_to_invest: Decimal,
    start_date: datetime,
    end_date: datetime,
    prices: Dict[str, Decimal],
    asset: str = 'BTC'
) -> StrategyResult:
    """Simulate pure DCA - equal daily buys."""

    # Get trading days
    trading_days = []
    current = start_date
    while current <= end_date:
        date_str = current.strftime('%Y-%m-%d')
        if date_str in prices:
            trading_days.append(date_str)
        current += timedelta(days=1)

    if not trading_days:
        return StrategyResult(
            name=f"Pure DCA ({asset})",
            total_invested=Decimal('0'),
            final_value=Decimal('0'),
            total_return=Decimal('0'),
            return_pct=Decimal('0'),
            assets_held={}
        )

    daily_amount = total_to_invest / len(trading_days)
    total_asset = Decimal('0')

    for date_str in trading_days:
        price = prices[date_str]
        if price > 0:
            bought = daily_amount / price
            total_asset += bought

    # Get final price (last available)
    final_price = prices.get(trading_days[-1], Decimal('0'))
    final_value = total_asset * final_price
    total_return = final_value - total_to_invest
    return_pct = (total_return / total_to_invest * 100) if total_to_invest else Decimal('0')

    return StrategyResult(
        name=f"Pure DCA ({asset})",
        total_invested=total_to_invest,
        final_value=final_value,
        total_return=total_return,
        return_pct=return_pct,
        assets_held={asset: total_asset}
    )

def simulate_buy_and_hold(
    total_to_invest: Decimal,
    start_date: datetime,
    end_date: datetime,
    prices: Dict[str, Decimal],
    asset: str = 'BTC'
) -> StrategyResult:
    """Simulate lump sum buy at start."""

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    # Find first available price
    start_price = None
    current = start_date
    while current <= end_date and not start_price:
        date_str = current.strftime('%Y-%m-%d')
        if date_str in prices:
            start_price = prices[date_str]
            break
        current += timedelta(days=1)

    # Find last available price
    end_price = None
    current = end_date
    while current >= start_date and not end_price:
        date_str = current.strftime('%Y-%m-%d')
        if date_str in prices:
            end_price = prices[date_str]
            break
        current -= timedelta(days=1)

    if not start_price or not end_price:
        return StrategyResult(
            name=f"Buy & Hold ({asset})",
            total_invested=Decimal('0'),
            final_value=Decimal('0'),
            total_return=Decimal('0'),
            return_pct=Decimal('0'),
            assets_held={}
        )

    total_asset = total_to_invest / start_price
    final_value = total_asset * end_price
    total_return = final_value - total_to_invest
    return_pct = (total_return / total_to_invest * 100) if total_to_invest else Decimal('0')

    return StrategyResult(
        name=f"Buy & Hold ({asset})",
        total_invested=total_to_invest,
        final_value=final_value,
        total_return=total_return,
        return_pct=return_pct,
        assets_held={asset: total_asset}
    )

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
            if value > 0:
                assets_held[asset] = qty

    # Add sold value and staking to "returns"
    net_invested = total_invested - total_sold
    total_return = final_value - net_invested + staking_income
    return_pct = (total_return / total_invested * 100) if total_invested else Decimal('0')

    return StrategyResult(
        name="Your Actual Strategy",
        total_invested=total_invested,
        final_value=final_value + total_sold + staking_income,
        total_return=total_return,
        return_pct=return_pct,
        assets_held=assets_held
    )

async def run_comparison():
    """Run full strategy comparison."""

    print("=" * 70)
    print("STRATEGY COMPARISON")
    print("=" * 70)

    # Load transactions
    print("\n📊 Loading your transaction history...")
    transactions = load_transactions()
    print(f"   Loaded {len(transactions):,} transactions")

    # Calculate totals
    buys = [tx for tx in transactions if tx['type'] == 'Buy']
    total_invested = sum(tx['total'] for tx in buys)

    if not transactions:
        print("No transactions found!")
        return

    start_date = transactions[0]['timestamp']
    end_date = transactions[-1]['timestamp']

    print(f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"   Total Invested: ${total_invested:,.2f}")

    # Fetch historical prices
    print("\n📈 Fetching historical prices (this may take a moment)...")

    btc_prices = await fetch_historical_prices('BTC', days=1095)
    print(f"   BTC: {len(btc_prices)} daily prices")

    await asyncio.sleep(1.5)  # Rate limit

    eth_prices = await fetch_historical_prices('ETH', days=1095)
    print(f"   ETH: {len(eth_prices)} daily prices")

    # Fetch current prices for actual holdings
    print("\n💰 Fetching current prices...")
    assets = list(set(tx['asset'] for tx in transactions if tx['type'] == 'Buy'))
    current_prices = await fetch_current_prices(assets)
    print(f"   Got prices for {len(current_prices)} assets")

    # Run simulations
    print("\n🔄 Running strategy simulations...")

    results = []

    # 1. Pure DCA into BTC
    dca_btc = simulate_pure_dca(total_invested, start_date, end_date, btc_prices, 'BTC')
    results.append(dca_btc)
    print(f"   ✓ Pure DCA (BTC)")

    # 2. Pure DCA into ETH
    dca_eth = simulate_pure_dca(total_invested, start_date, end_date, eth_prices, 'ETH')
    results.append(dca_eth)
    print(f"   ✓ Pure DCA (ETH)")

    # 3. Buy & Hold BTC
    bh_btc = simulate_buy_and_hold(total_invested, start_date, end_date, btc_prices, 'BTC')
    results.append(bh_btc)
    print(f"   ✓ Buy & Hold (BTC)")

    # 4. Buy & Hold ETH
    bh_eth = simulate_buy_and_hold(total_invested, start_date, end_date, eth_prices, 'ETH')
    results.append(bh_eth)
    print(f"   ✓ Buy & Hold (ETH)")

    # 5. Actual performance
    actual = calculate_actual_performance(transactions, current_prices)
    results.append(actual)
    print(f"   ✓ Your Actual Strategy")

    # Print results
    print("\n" + "=" * 70)
    print("RESULTS COMPARISON")
    print("=" * 70)
    print(f"\n{'Strategy':<25} {'Invested':>14} {'Final Value':>14} {'Return':>14} {'%':>8}")
    print("-" * 70)

    # Sort by return
    results.sort(key=lambda x: x.return_pct, reverse=True)

    for r in results:
        marker = "👈" if r.name == "Your Actual Strategy" else ""
        print(f"{r.name:<25} ${r.total_invested:>12,.2f} ${r.final_value:>12,.2f} ${r.total_return:>12,.2f} {r.return_pct:>+7.1f}% {marker}")

    print("-" * 70)

    # Analysis
    print("\n📊 ANALYSIS")
    print("-" * 70)

    your_result = next(r for r in results if r.name == "Your Actual Strategy")
    best_result = results[0]
    worst_result = results[-1]

    if your_result.name == best_result.name:
        print("🏆 Your strategy OUTPERFORMED all simulated alternatives!")
    else:
        diff = best_result.return_pct - your_result.return_pct
        print(f"📉 Best alternative ({best_result.name}) beat your strategy by {diff:.1f}%")
        value_diff = best_result.final_value - your_result.final_value
        print(f"   That's ${value_diff:,.2f} difference in final value")

    if your_result.name == worst_result.name:
        print("⚠️  Your strategy underperformed all alternatives")
    elif your_result.name != best_result.name:
        # Find rank
        rank = next(i for i, r in enumerate(results) if r.name == "Your Actual Strategy") + 1
        print(f"📊 Your strategy ranked #{rank} out of {len(results)} strategies")

    # Diversification note
    print(f"\n💡 INSIGHTS")
    print("-" * 70)
    print(f"• You held {len(your_result.assets_held)} different assets")
    print(f"• Pure BTC strategies used only 1 asset")
    print(f"• Period: {(end_date - start_date).days} days ({(end_date - start_date).days / 365:.1f} years)")

    if dca_btc.return_pct > bh_btc.return_pct:
        print(f"• DCA beat lump sum for BTC by {dca_btc.return_pct - bh_btc.return_pct:.1f}%")
    else:
        print(f"• Lump sum beat DCA for BTC by {bh_btc.return_pct - dca_btc.return_pct:.1f}%")

def main():
    asyncio.run(run_comparison())

if __name__ == '__main__':
    main()
