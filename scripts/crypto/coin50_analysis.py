#!/usr/bin/env python3
"""
COIN50 Analysis - Apply COIN50 methodology to current holdings

Analyzes your 172 assets and shows:
1. Which pass COIN50 eligibility
2. Recommended weights
3. Personal vs Business allocation
4. Rebalancing actions
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
from typing import Dict, List, Optional, Set
from enum import Enum

sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

TRANSACTION_DIR = '/home/dave/skippy/lib/python/crypto_trading/data/transactions'

# COIN50 Exclusion lists
STABLECOINS = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "GUSD", "FRAX",
               "LUSD", "USDD", "EURC", "PYUSD", "FDUSD", "USDE", "GYEN", "UST"}
WRAPPED = {"WBTC", "WETH", "STETH", "RETH", "CBETH", "WSTETH", "LIDO"}
EXCHANGE_TOKENS = {"BNB", "CRO", "OKB", "KCS", "HT", "LEO", "FTT", "GT", "MX"}
PRIVACY_COINS = {"XMR", "ZEC", "DASH", "SCRT", "FIRO", "ZEN"}
SECURITY_CONCERNS = {"LUNA", "LUNC", "UST", "USTC", "FTT", "SRM"}

# Staking APY (Coinbase One)
STAKING_APY = {
    'SOL': 6.5, 'DOT': 11.0, 'ATOM': 8.5, 'ADA': 3.5, 'AVAX': 8.0,
    'XTZ': 5.5, 'ALGO': 4.0, 'NEAR': 9.0, 'INJ': 15.0, 'MATIC': 4.0,
    'POL': 4.0, 'ETH': 3.5, 'OSMO': 10.0, 'KAVA': 7.0,
}

# Business-grade assets (treasury suitable)
BUSINESS_ASSETS = {'BTC', 'ETH', 'XRP', 'LTC', 'BCH', 'LINK', 'XLM', 'HBAR'}

class AccountType(Enum):
    PERSONAL = "Personal (Coinbase)"
    BUSINESS = "Business (Kraken)"
    EXCLUDED = "Excluded"

@dataclass
class Asset:
    symbol: str
    quantity: Decimal
    cost_basis: Decimal
    current_price: Decimal = Decimal('0')
    current_value: Decimal = Decimal('0')
    market_cap: Decimal = Decimal('0')
    volume_24h: Decimal = Decimal('0')
    eligible: bool = True
    exclusion_reason: str = ""
    account: AccountType = AccountType.PERSONAL
    target_weight: Decimal = Decimal('0')
    target_value: Decimal = Decimal('0')
    staking_apy: float = 0.0

def parse_usd(value: str) -> Decimal:
    if not value:
        return Decimal('0')
    clean = value.replace('$', '').replace(',', '').strip()
    try:
        return Decimal(clean)
    except:
        return Decimal('0')

def load_holdings() -> Dict[str, Asset]:
    holdings: Dict[str, Decimal] = defaultdict(Decimal)
    cost_basis: Dict[str, Decimal] = defaultdict(Decimal)

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
            try:
                asset = row.get('Asset', '')
                qty = Decimal(row.get('Quantity Transacted', '0') or '0')
                total = parse_usd(row.get('Total (inclusive of fees and/or spread)', ''))
                tx_type = row.get('Transaction Type', '')

                if tx_type == 'Buy':
                    holdings[asset] += qty
                    cost_basis[asset] += total
                elif tx_type == 'Sell':
                    holdings[asset] -= qty
                elif tx_type == 'Staking Income':
                    holdings[asset] += qty
                elif tx_type == 'Send':
                    holdings[asset] -= qty
                elif tx_type in ('Receive', 'Deposit'):
                    holdings[asset] += qty
            except:
                continue

    result = {}
    for symbol, qty in holdings.items():
        if qty > 0:
            result[symbol] = Asset(
                symbol=symbol,
                quantity=qty,
                cost_basis=cost_basis[symbol],
                staking_apy=STAKING_APY.get(symbol, 0.0),
            )
    return result

async def fetch_market_data(symbols: List[str]) -> Dict[str, dict]:
    """Fetch prices and market caps from CoinGecko."""
    cg_ids = {
        'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
        'LTC': 'litecoin', 'XRP': 'ripple', 'ADA': 'cardano',
        'DOT': 'polkadot', 'ATOM': 'cosmos', 'AVAX': 'avalanche-2',
        'LINK': 'chainlink', 'DOGE': 'dogecoin', 'XTZ': 'tezos',
        'MATIC': 'matic-network', 'POL': 'matic-network',
        'ALGO': 'algorand', 'HBAR': 'hedera-hashgraph',
        'MANA': 'decentraland', 'SAND': 'the-sandbox',
        'KSM': 'kusama', 'ETC': 'ethereum-classic',
        'INJ': 'injective-protocol', 'NEAR': 'near',
        'FIL': 'filecoin', 'AAVE': 'aave', 'UNI': 'uniswap',
        'XLM': 'stellar', 'BCH': 'bitcoin-cash', 'SUI': 'sui',
    }

    data = {}
    ids = [cg_ids.get(s, s.lower()) for s in symbols if s not in STABLECOINS]
    ids = list(set(ids))[:100]

    try:
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={','.join(ids)}&order=market_cap_desc&per_page=100"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    coins = await resp.json()
                    reverse = {v: k for k, v in cg_ids.items()}
                    for coin in coins:
                        cg_id = coin.get('id', '')
                        symbol = reverse.get(cg_id, coin.get('symbol', '').upper())
                        data[symbol] = {
                            'price': Decimal(str(coin.get('current_price', 0) or 0)),
                            'market_cap': Decimal(str(coin.get('market_cap', 0) or 0)),
                            'volume': Decimal(str(coin.get('total_volume', 0) or 0)),
                        }
    except Exception as e:
        print(f"  Market data error: {e}")

    return data

def apply_eligibility(asset: Asset) -> None:
    """Apply COIN50 eligibility rules."""
    symbol = asset.symbol

    if symbol in STABLECOINS:
        asset.eligible = False
        asset.exclusion_reason = "Stablecoin"
        asset.account = AccountType.EXCLUDED
    elif symbol in WRAPPED:
        asset.eligible = False
        asset.exclusion_reason = "Wrapped asset"
        asset.account = AccountType.EXCLUDED
    elif symbol in EXCHANGE_TOKENS:
        asset.eligible = False
        asset.exclusion_reason = "Exchange token"
        asset.account = AccountType.EXCLUDED
    elif symbol in PRIVACY_COINS:
        asset.eligible = False
        asset.exclusion_reason = "Privacy coin"
        asset.account = AccountType.EXCLUDED
    elif symbol in SECURITY_CONCERNS:
        asset.eligible = False
        asset.exclusion_reason = "Security concern"
        asset.account = AccountType.EXCLUDED
    elif asset.market_cap < Decimal('100000000') and asset.market_cap > 0:
        asset.eligible = False
        asset.exclusion_reason = f"Market cap ${asset.market_cap/1000000:.0f}M < $100M"
        asset.account = AccountType.EXCLUDED
    elif asset.volume_24h < Decimal('1000000') and asset.volume_24h > 0:
        asset.eligible = False
        asset.exclusion_reason = f"Volume ${asset.volume_24h/1000000:.1f}M < $1M"
        asset.account = AccountType.EXCLUDED

def assign_account(asset: Asset) -> None:
    """Assign to Personal or Business account."""
    if not asset.eligible:
        return

    symbol = asset.symbol

    # Business: Treasury assets
    if symbol in BUSINESS_ASSETS:
        asset.account = AccountType.BUSINESS
    # Personal: High staking APY
    elif asset.staking_apy >= 5.0:
        asset.account = AccountType.PERSONAL
    # Personal: Higher volatility/speculation
    elif symbol in {'DOGE', 'SHIB', 'PEPE', 'BONK', 'WIF', 'FLOKI'}:
        asset.account = AccountType.PERSONAL
    # Default to personal
    else:
        asset.account = AccountType.PERSONAL

def calculate_weights(assets: List[Asset], total_value: Decimal) -> None:
    """Calculate COIN50 weights based on market cap."""
    if total_value <= 0:
        return

    eligible = [a for a in assets if a.eligible and a.market_cap > 0]
    if not eligible:
        return

    # Sort by market cap
    eligible.sort(key=lambda a: a.market_cap, reverse=True)

    # Take top 50
    top50 = eligible[:50]

    # Calculate total market cap
    total_mcap = sum(a.market_cap for a in top50)
    if total_mcap <= 0:
        return

    # Raw weights by market cap
    for a in top50:
        raw_weight = (a.market_cap / total_mcap) * 100

        # Cap at 40%
        a.target_weight = min(Decimal(str(raw_weight)), Decimal('40'))

    # Normalize to 100%
    total_weight = sum(a.target_weight for a in top50)
    if total_weight > 0:
        for a in top50:
            a.target_weight = (a.target_weight / total_weight) * 100
            a.target_value = total_value * (a.target_weight / 100)

async def run_coin50_analysis():
    print("=" * 70)
    print("COIN50 ANALYSIS - Applying Index Methodology to Your Portfolio")
    print("=" * 70)

    # Load holdings
    print("\n📊 Loading your holdings...")
    holdings = load_holdings()
    print(f"   Found {len(holdings)} assets")

    # Fetch market data
    print("\n📈 Fetching market data...")
    market_data = await fetch_market_data(list(holdings.keys()))
    print(f"   Got data for {len(market_data)} assets")

    # Update holdings with market data
    total_value = Decimal('0')
    total_cost = Decimal('0')

    for symbol, asset in holdings.items():
        data = market_data.get(symbol, {})
        asset.current_price = data.get('price', Decimal('0'))
        asset.market_cap = data.get('market_cap', Decimal('0'))
        asset.volume_24h = data.get('volume', Decimal('0'))
        asset.current_value = asset.quantity * asset.current_price
        total_value += asset.current_value
        total_cost += asset.cost_basis

    # Apply eligibility
    print("\n🔍 Applying COIN50 eligibility filters...")
    for asset in holdings.values():
        apply_eligibility(asset)
        if asset.eligible:
            assign_account(asset)

    assets = list(holdings.values())
    eligible = [a for a in assets if a.eligible]
    excluded = [a for a in assets if not a.eligible]

    print(f"   Eligible: {len(eligible)} assets")
    print(f"   Excluded: {len(excluded)} assets")

    # Calculate weights
    calculate_weights(assets, total_value)

    # Separate by account
    personal = [a for a in eligible if a.account == AccountType.PERSONAL]
    business = [a for a in eligible if a.account == AccountType.BUSINESS]

    personal_value = sum(a.current_value for a in personal)
    business_value = sum(a.current_value for a in business)
    excluded_value = sum(a.current_value for a in excluded)

    # Print results
    print("\n" + "=" * 70)
    print("PORTFOLIO SUMMARY")
    print("=" * 70)

    print(f"\n{'Category':<30} {'Assets':>8} {'Value':>14} {'%':>8}")
    print("-" * 60)
    print(f"{'COIN50 Eligible':<30} {len(eligible):>8} ${sum(a.current_value for a in eligible):>12,.0f} {sum(a.current_value for a in eligible)/total_value*100 if total_value else 0:>7.1f}%")
    print(f"  - Personal (Coinbase)        {len(personal):>8} ${personal_value:>12,.0f}")
    print(f"  - Business (Kraken)          {len(business):>8} ${business_value:>12,.0f}")
    print(f"{'Excluded':<30} {len(excluded):>8} ${excluded_value:>12,.0f} {excluded_value/total_value*100 if total_value else 0:>7.1f}%")
    print("-" * 60)
    print(f"{'TOTAL':<30} {len(assets):>8} ${total_value:>12,.0f}")

    # Eligible assets by account
    print("\n" + "=" * 70)
    print("COIN50 ELIGIBLE ASSETS")
    print("=" * 70)

    print("\n🏢 BUSINESS ACCOUNT (Kraken) - Treasury Assets")
    print("-" * 70)
    print(f"{'Asset':<8} {'Qty':>12} {'Value':>10} {'Target':>10} {'Action':>12} {'Reason':<20}")
    print("-" * 70)

    business.sort(key=lambda a: a.current_value, reverse=True)
    for a in business[:15]:
        diff = a.target_value - a.current_value
        action = f"+${diff:,.0f}" if diff > 0 else f"-${abs(diff):,.0f}" if diff < 0 else "OK"
        reason = "Treasury" if a.symbol in {'BTC', 'ETH'} else "Institutional"
        print(f"{a.symbol:<8} {float(a.quantity):>12.4f} ${a.current_value:>8,.0f} ${a.target_value:>8,.0f} {action:>12} {reason:<20}")

    print(f"\n👤 PERSONAL ACCOUNT (Coinbase One) - Staking & Growth")
    print("-" * 70)
    print(f"{'Asset':<8} {'Qty':>12} {'Value':>10} {'Target':>10} {'APY':>6} {'Action':>10}")
    print("-" * 70)

    personal.sort(key=lambda a: a.current_value, reverse=True)
    for a in personal[:20]:
        diff = a.target_value - a.current_value
        action = f"+${diff:,.0f}" if diff > 0 else f"-${abs(diff):,.0f}" if diff < 0 else "OK"
        apy = f"{a.staking_apy:.1f}%" if a.staking_apy else "-"
        print(f"{a.symbol:<8} {float(a.quantity):>12.4f} ${a.current_value:>8,.0f} ${a.target_value:>8,.0f} {apy:>6} {action:>10}")

    # Excluded assets
    print("\n" + "=" * 70)
    print("EXCLUDED ASSETS (Consider Liquidating)")
    print("=" * 70)
    print(f"{'Asset':<8} {'Value':>10} {'Reason':<40}")
    print("-" * 60)

    excluded.sort(key=lambda a: a.current_value, reverse=True)
    for a in excluded[:20]:
        if a.current_value > 1:
            print(f"{a.symbol:<8} ${a.current_value:>8,.0f} {a.exclusion_reason:<40}")

    # Rebalancing summary
    print("\n" + "=" * 70)
    print("REBALANCING RECOMMENDATIONS")
    print("=" * 70)

    # Target allocation
    target_business = total_value * Decimal('0.60')  # 60% business
    target_personal = total_value * Decimal('0.40')  # 40% personal

    print(f"\n{'Account':<25} {'Current':>12} {'Target':>12} {'Action':>12}")
    print("-" * 60)
    print(f"{'Business (60%)':<25} ${business_value:>10,.0f} ${target_business:>10,.0f} ${target_business - business_value:>+10,.0f}")
    print(f"{'Personal (40%)':<25} ${personal_value:>10,.0f} ${target_personal:>10,.0f} ${target_personal - personal_value:>+10,.0f}")
    print(f"{'Excluded (liquidate)':<25} ${excluded_value:>10,.0f} ${'0':>10} ${-excluded_value:>+10,.0f}")

    print("\n💡 KEY ACTIONS:")
    print("-" * 70)
    if excluded_value > 50:
        print(f"1. Liquidate ${excluded_value:,.0f} in excluded assets (stablecoins, low cap, etc.)")
    if business_value < target_business:
        print(f"2. Move ${target_business - business_value:,.0f} into Business assets (BTC, ETH, LTC)")
    print(f"3. Focus future DCA on COIN50 eligible assets only")
    print(f"4. Stake all stakeable assets for yield")

    # What COIN50 portfolio would look like
    print("\n" + "=" * 70)
    print("RECOMMENDED COIN50 ALLOCATION (Top 10)")
    print("=" * 70)

    eligible.sort(key=lambda a: a.market_cap, reverse=True)
    top10 = eligible[:10]

    print(f"\n{'Rank':<5} {'Asset':<8} {'Account':<15} {'Weight':>8} {'Value':>12}")
    print("-" * 50)

    for i, a in enumerate(top10, 1):
        acct = "Business" if a.account == AccountType.BUSINESS else "Personal"
        print(f"{i:<5} {a.symbol:<8} {acct:<15} {a.target_weight:>7.1f}% ${a.target_value:>10,.0f}")

def main():
    asyncio.run(run_coin50_analysis())

if __name__ == '__main__':
    main()
