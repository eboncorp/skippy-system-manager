#!/usr/bin/env python3
"""
Portfolio Manager v2 - Two Account Strategy

PERSONAL (Coinbase One): Day trading, high risk/reward, 0% fees
BUSINESS (Kraken): Long-term staking, treasury

Run: python portfolio_v2.py daily
"""

import sys
import os
import csv
import asyncio
import aiohttp
import json
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

TRANSACTION_DIR = '/home/dave/skippy/lib/python/crypto_trading/data/transactions'
OUTPUT_DIR = '/home/dave/skippy/work/crypto/automation'

class Account(Enum):
    PERSONAL = "Personal (Coinbase One)"  # Day trading, 0% fees
    BUSINESS = "Business (Kraken)"        # Long-term staking

# Kraken staking APY (higher than Coinbase)
KRAKEN_STAKING = {
    'DOT': 12.0, 'ATOM': 10.0, 'SOL': 6.0, 'AVAX': 8.0, 'ETH': 3.5,
    'ADA': 3.5, 'XTZ': 5.5, 'ALGO': 4.0, 'NEAR': 9.0, 'KAVA': 7.0,
    'MATIC': 4.0, 'FLOW': 5.0, 'MINA': 12.0, 'SCRT': 15.0,
}

# Long-term hold assets (Business/Kraken)
BUSINESS_ASSETS = {
    # Treasury (BTC, ETH)
    'BTC', 'ETH',
    # High staking yield
    'DOT', 'ATOM', 'SOL', 'AVAX', 'ADA', 'NEAR', 'KAVA', 'MINA',
    # Blue chips for long-term
    'LINK', 'LTC', 'XRP', 'XLM',
}

# Day trading / high risk assets (Personal/Coinbase One)
PERSONAL_ASSETS = {
    # Memecoins
    'DOGE', 'SHIB', 'PEPE', 'BONK', 'WIF', 'FLOKI',
    # Volatile/speculative
    'SUI', 'APT', 'ARB', 'OP', 'INJ', 'TIA', 'SEI',
    # DeFi/Gaming (high volatility)
    'UNI', 'AAVE', 'SAND', 'MANA', 'AXS', 'IMX',
    # New/trending
    'RENDER', 'FET', 'TAO', 'RNDR',
}

# Excluded (liquidate or ignore)
EXCLUDED = {
    'USDC', 'USDT', 'DAI', 'USD', 'BUSD', 'GUSD',  # Stablecoins
    'WBTC', 'WETH', 'STETH',  # Wrapped
    'GYEN', 'EUROC',  # Fiat-pegged
}

@dataclass
class Holding:
    symbol: str
    quantity: Decimal
    cost_basis: Decimal
    current_price: Decimal = Decimal('0')
    current_value: Decimal = Decimal('0')
    account: Account = Account.PERSONAL
    staking_apy: float = 0.0
    action: str = ""
    target_pct: float = 0.0

def parse_usd(value: str) -> Decimal:
    if not value:
        return Decimal('0')
    clean = value.replace('$', '').replace(',', '').strip()
    try:
        return Decimal(clean)
    except:
        return Decimal('0')

def load_holdings() -> Dict[str, Holding]:
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
        if qty > 0 and symbol not in EXCLUDED:
            # Determine account
            if symbol in BUSINESS_ASSETS:
                account = Account.BUSINESS
                apy = KRAKEN_STAKING.get(symbol, 0.0)
            else:
                account = Account.PERSONAL
                apy = 0.0

            result[symbol] = Holding(
                symbol=symbol,
                quantity=qty,
                cost_basis=cost_basis[symbol],
                account=account,
                staking_apy=apy,
            )
    return result

async def fetch_prices(symbols: List[str]) -> Dict[str, Decimal]:
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
        'XLM': 'stellar', 'SHIB': 'shiba-inu', 'PEPE': 'pepe',
        'SUI': 'sui', 'APT': 'aptos', 'ARB': 'arbitrum',
        'OP': 'optimism', 'TIA': 'celestia', 'SEI': 'sei-network',
    }

    prices = {}
    ids = list(set(cg_ids.get(s, s.lower()) for s in symbols))[:50]

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
        print(f"  Price error: {e}")

    return prices

async def fetch_fear_greed() -> int:
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return int(data['data'][0]['value'])
    except:
        pass
    return 50

def get_dca_multiplier(fear_greed: int) -> float:
    if fear_greed < 20:
        return 3.0    # Extreme fear
    elif fear_greed < 35:
        return 2.0    # Fear
    elif fear_greed < 50:
        return 1.5    # Neutral-fear
    elif fear_greed < 65:
        return 1.0    # Neutral-greed
    elif fear_greed < 80:
        return 0.5    # Greed
    else:
        return 0.25   # Extreme greed

async def run_daily():
    print("=" * 75)
    print("PORTFOLIO MANAGER v2 - Two Account Strategy")
    print("=" * 75)
    print(f"\nPersonal (Coinbase One): Day trading, 0% fees")
    print(f"Business (Kraken): Long-term staking")

    # Load holdings
    print("\n📊 Loading holdings...")
    holdings = load_holdings()
    print(f"   Found {len(holdings)} assets")

    # Fetch prices
    print("\n💰 Fetching prices...")
    prices = await fetch_prices(list(holdings.keys()))

    # Update holdings
    total_value = Decimal('0')
    for symbol, h in holdings.items():
        h.current_price = prices.get(symbol, Decimal('0'))
        h.current_value = h.quantity * h.current_price
        total_value += h.current_value

    # Separate by account
    personal = {s: h for s, h in holdings.items() if h.account == Account.PERSONAL}
    business = {s: h for s, h in holdings.items() if h.account == Account.BUSINESS}

    personal_value = sum(h.current_value for h in personal.values())
    business_value = sum(h.current_value for h in business.values())

    # Fetch sentiment
    fear_greed = await fetch_fear_greed()
    multiplier = get_dca_multiplier(fear_greed)

    # Print summary
    print("\n" + "=" * 75)
    print("ACCOUNT SUMMARY")
    print("=" * 75)

    print(f"\n{'Account':<35} {'Assets':>8} {'Value':>14} {'%':>8}")
    print("-" * 65)
    print(f"{'Business (Kraken) - Staking':<35} {len(business):>8} ${business_value:>12,.0f} {business_value/total_value*100 if total_value else 0:>7.1f}%")
    print(f"{'Personal (Coinbase One) - Trading':<35} {len(personal):>8} ${personal_value:>12,.0f} {personal_value/total_value*100 if total_value else 0:>7.1f}%")
    print("-" * 65)
    print(f"{'TOTAL':<35} {len(holdings):>8} ${total_value:>12,.0f}")

    # Business account details (staking)
    print("\n" + "=" * 75)
    print("🏢 BUSINESS (Kraken) - Long-term Staking")
    print("=" * 75)
    print(f"\n{'Asset':<8} {'Qty':>12} {'Value':>10} {'APY':>8} {'Annual Yield':>14}")
    print("-" * 55)

    total_yield = Decimal('0')
    for h in sorted(business.values(), key=lambda x: x.current_value, reverse=True)[:15]:
        if h.current_value > 0:
            annual = h.current_value * Decimal(str(h.staking_apy / 100))
            total_yield += annual
            apy_str = f"{h.staking_apy:.1f}%" if h.staking_apy else "-"
            print(f"{h.symbol:<8} {float(h.quantity):>12.4f} ${h.current_value:>8,.0f} {apy_str:>8} ${annual:>12,.0f}")

    print("-" * 55)
    print(f"{'TOTAL':<8} {'':<12} ${business_value:>8,.0f} {'':<8} ${total_yield:>12,.0f}/yr")

    # Personal account details (trading)
    print("\n" + "=" * 75)
    print("👤 PERSONAL (Coinbase One) - Day Trading / High Risk")
    print("=" * 75)
    print(f"\n{'Asset':<8} {'Qty':>12} {'Value':>10} {'Cost':>10} {'P/L':>10} {'P/L %':>8}")
    print("-" * 60)

    for h in sorted(personal.values(), key=lambda x: x.current_value, reverse=True)[:20]:
        if h.current_value > 0 or h.cost_basis > 10:
            pl = h.current_value - h.cost_basis
            pl_pct = (pl / h.cost_basis * 100) if h.cost_basis > 0 else Decimal('0')
            print(f"{h.symbol:<8} {float(h.quantity):>12.4f} ${h.current_value:>8,.0f} ${h.cost_basis:>8,.0f} ${pl:>8,.0f} {pl_pct:>+7.0f}%")

    # Market sentiment & recommendations
    print("\n" + "=" * 75)
    print("📈 MARKET SENTIMENT & ACTIONS")
    print("=" * 75)

    condition = "EXTREME FEAR" if fear_greed < 20 else "FEAR" if fear_greed < 35 else "NEUTRAL" if fear_greed < 65 else "GREED" if fear_greed < 80 else "EXTREME GREED"
    print(f"\nFear & Greed Index: {fear_greed} ({condition})")
    print(f"DCA Multiplier: {multiplier}x")

    # Daily DCA suggestion
    base_dca = Decimal('40')
    adjusted_dca = base_dca * Decimal(str(multiplier))

    print(f"\n📊 DAILY DCA ALLOCATION (${adjusted_dca:.0f} total)")
    print("-" * 50)

    # Business allocation (70% of DCA for long-term)
    biz_dca = adjusted_dca * Decimal('0.7')
    print(f"\n🏢 Business (Kraken) - ${biz_dca:.0f} (70%)")
    print(f"   BTC: ${biz_dca * Decimal('0.50'):.0f} (50%)")
    print(f"   ETH: ${biz_dca * Decimal('0.30'):.0f} (30%)")
    print(f"   DOT/ATOM/SOL: ${biz_dca * Decimal('0.20'):.0f} (20% - staking)")

    # Personal allocation (30% for trading)
    pers_dca = adjusted_dca * Decimal('0.3')
    print(f"\n👤 Personal (Coinbase One) - ${pers_dca:.0f} (30%)")
    print(f"   High-risk plays (memes, new listings)")
    print(f"   Swing trades on volatility")
    print(f"   0% fees = trade freely")

    # Rebalancing actions
    print("\n" + "=" * 75)
    print("🔄 REBALANCING ACTIONS")
    print("=" * 75)

    # Target: 70% business, 30% personal
    target_biz = total_value * Decimal('0.70')
    target_pers = total_value * Decimal('0.30')

    print(f"\n{'Account':<35} {'Current':>12} {'Target (70/30)':>14} {'Action':>12}")
    print("-" * 75)
    print(f"{'Business (Kraken)':<35} ${business_value:>10,.0f} ${target_biz:>12,.0f} ${target_biz - business_value:>+10,.0f}")
    print(f"{'Personal (Coinbase One)':<35} ${personal_value:>10,.0f} ${target_pers:>12,.0f} ${target_pers - personal_value:>+10,.0f}")

    # Specific actions
    print("\n💡 RECOMMENDED ACTIONS:")
    print("-" * 50)

    if business_value < target_biz:
        gap = target_biz - business_value
        print(f"1. Move ${gap:,.0f} to Kraken for staking")
        print(f"   - Transfer LTC, ETH, BTC to Kraken")
        print(f"   - Stake DOT (12%), ATOM (10%), SOL (6%)")

    if personal_value > target_pers:
        excess = personal_value - target_pers
        print(f"2. Reduce Personal by ${excess:,.0f}")
        print(f"   - Take profits on winners")
        print(f"   - Transfer staking assets to Kraken")

    # Assets to move
    print("\n📦 ASSETS TO TRANSFER TO KRAKEN:")
    print("-" * 50)
    for h in personal.values():
        if h.symbol in BUSINESS_ASSETS and h.current_value > 10:
            print(f"   {h.symbol}: {h.quantity:.4f} (${h.current_value:.0f}) → Kraken for {KRAKEN_STAKING.get(h.symbol, 0)}% APY")

    # Save report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_value': float(total_value),
        'business_value': float(business_value),
        'personal_value': float(personal_value),
        'fear_greed': fear_greed,
        'multiplier': multiplier,
        'annual_staking_yield': float(total_yield),
    }
    with open(f"{OUTPUT_DIR}/portfolio_v2_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to {OUTPUT_DIR}/")

def main():
    asyncio.run(run_daily())

if __name__ == '__main__':
    main()
