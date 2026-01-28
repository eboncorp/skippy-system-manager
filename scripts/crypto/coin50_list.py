#!/usr/bin/env python3
"""
COIN50 Full List - Top 50 assets by market cap with weights
"""

import sys
import asyncio
import aiohttp
from decimal import Decimal

# COIN50 Exclusions
EXCLUDED = {
    # Stablecoins
    "USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "GUSD", "FRAX", "PYUSD", "FDUSD",
    # Wrapped
    "WBTC", "WETH", "STETH", "WSTETH", "CBETH", "RETH",
    # Exchange tokens
    "BNB", "CRO", "OKB", "KCS", "LEO", "FTT", "GT",
    # Privacy
    "XMR", "ZEC", "DASH",
}

# Staking APY
STAKING_APY = {
    'SOL': 6.5, 'DOT': 11.0, 'ATOM': 8.5, 'ADA': 3.5, 'AVAX': 8.0,
    'XTZ': 5.5, 'ALGO': 4.0, 'NEAR': 9.0, 'INJ': 15.0, 'MATIC': 4.0,
    'POL': 4.0, 'ETH': 3.5, 'OSMO': 10.0, 'TIA': 12.0, 'SEI': 5.0,
    'SUI': 3.0, 'APT': 7.0, 'ROSE': 8.0, 'KAVA': 7.0, 'FET': 5.0,
}

# Business-grade (treasury)
BUSINESS_ASSETS = {'BTC', 'ETH', 'XRP', 'LTC', 'BCH', 'LINK', 'XLM', 'HBAR', 'ETC'}

async def fetch_top_coins():
    """Fetch top 100 coins by market cap."""
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=30) as resp:
            if resp.status == 200:
                return await resp.json()
    return []

async def main():
    print("=" * 85)
    print("COIN50 INDEX - Top 50 Crypto Assets by Market Cap")
    print("=" * 85)
    print("\nFetching market data...")

    coins = await fetch_top_coins()

    # Filter excluded
    eligible = []
    for coin in coins:
        symbol = coin.get('symbol', '').upper()
        if symbol not in EXCLUDED:
            eligible.append({
                'symbol': symbol,
                'name': coin.get('name', ''),
                'price': Decimal(str(coin.get('current_price', 0) or 0)),
                'market_cap': Decimal(str(coin.get('market_cap', 0) or 0)),
                'volume': Decimal(str(coin.get('total_volume', 0) or 0)),
                'change_24h': coin.get('price_change_percentage_24h', 0) or 0,
            })

    # Take top 50
    top50 = eligible[:50]

    # Calculate weights (market cap weighted, 40% cap)
    total_mcap = sum(c['market_cap'] for c in top50)

    for c in top50:
        raw_weight = (c['market_cap'] / total_mcap * 100) if total_mcap else 0
        c['weight'] = min(float(raw_weight), 40.0)  # Cap at 40%

    # Normalize
    total_weight = sum(c['weight'] for c in top50)
    for c in top50:
        c['weight'] = (c['weight'] / total_weight * 100) if total_weight else 0
        c['apy'] = STAKING_APY.get(c['symbol'], 0)
        c['account'] = 'Business' if c['symbol'] in BUSINESS_ASSETS else 'Personal'

    # Print table
    print(f"\n{'Rank':<5} {'Symbol':<8} {'Name':<20} {'Price':>12} {'Mkt Cap':>14} {'Weight':>8} {'APY':>6} {'Account':<10}")
    print("-" * 95)

    business_weight = 0
    personal_weight = 0

    for i, c in enumerate(top50, 1):
        apy_str = f"{c['apy']:.1f}%" if c['apy'] else "-"
        mcap_b = c['market_cap'] / 1_000_000_000

        print(f"{i:<5} {c['symbol']:<8} {c['name'][:20]:<20} ${c['price']:>10,.2f} ${mcap_b:>11,.1f}B {c['weight']:>7.2f}% {apy_str:>6} {c['account']:<10}")

        if c['account'] == 'Business':
            business_weight += c['weight']
        else:
            personal_weight += c['weight']

    print("-" * 95)

    # Summary
    print(f"\n{'SUMMARY':=^85}")
    print(f"\n{'Account Allocation':}")
    print(f"  Business (Kraken):  {business_weight:>6.1f}%  - Treasury, institutional, long-term")
    print(f"  Personal (Coinbase): {personal_weight:>6.1f}%  - Staking, growth, speculative")

    # Top 10 breakdown
    print(f"\n{'Top 10 Concentration':}")
    top10_weight = sum(c['weight'] for c in top50[:10])
    print(f"  Top 10 assets: {top10_weight:.1f}% of portfolio")
    print(f"  Top 3 (BTC/ETH/XRP): {sum(c['weight'] for c in top50[:3]):.1f}%")

    # Staking opportunities
    staking = [c for c in top50 if c['apy'] >= 5.0]
    print(f"\n{'Staking Opportunities (5%+ APY)':}")
    for c in staking[:10]:
        print(f"  {c['symbol']:<8} {c['apy']:>5.1f}% APY  (Personal account)")

    # For $10k portfolio
    print(f"\n{'EXAMPLE: $10,000 Portfolio':=^85}")
    print(f"\n{'Rank':<5} {'Symbol':<8} {'Weight':>8} {'$10k Alloc':>12} {'Account':<10}")
    print("-" * 50)

    for i, c in enumerate(top50[:20], 1):
        alloc = c['weight'] / 100 * 10000
        if alloc >= 10:
            print(f"{i:<5} {c['symbol']:<8} {c['weight']:>7.2f}% ${alloc:>10,.0f} {c['account']:<10}")

    print("-" * 50)
    print(f"{'...':<5} {'(30 more)':<8} {sum(c['weight'] for c in top50[20:]):>7.2f}% ${sum(c['weight'] for c in top50[20:])/100*10000:>10,.0f}")

if __name__ == '__main__':
    asyncio.run(main())
