#!/usr/bin/env python3
"""
ATH Analysis - What if your portfolio reaches all-time highs?

Compares current value vs ATH value for your holdings.
"""

import sys
import os
import csv
import asyncio
import aiohttp
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from typing import Dict, List

sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

TRANSACTION_DIR = '/home/dave/skippy/lib/python/crypto_trading/data/transactions'

# Approximate ATH prices for common altcoins
ATH_PRICES = {
    # Major
    'BTC': Decimal('109000'),   # Nov 2024
    'ETH': Decimal('4800'),     # Nov 2021
    'SOL': Decimal('260'),      # Nov 2024
    'BNB': Decimal('720'),      # Jun 2024
    'XRP': Decimal('3.40'),     # Jan 2018
    'ADA': Decimal('3.10'),     # Sep 2021
    'DOGE': Decimal('0.73'),    # May 2021
    'DOT': Decimal('55'),       # Nov 2021
    'AVAX': Decimal('146'),     # Nov 2021
    'LINK': Decimal('53'),      # May 2021
    'LTC': Decimal('412'),      # May 2021
    'ATOM': Decimal('44'),      # Jan 2022
    'MATIC': Decimal('2.92'),   # Dec 2021
    'POL': Decimal('2.92'),     # Same as MATIC
    'ALGO': Decimal('3.28'),    # Jun 2019
    'XTZ': Decimal('9.18'),     # Oct 2021
    'NEAR': Decimal('20.42'),   # Jan 2022
    'FIL': Decimal('236'),      # Apr 2021
    'HBAR': Decimal('0.57'),    # Nov 2021
    'ICP': Decimal('700'),      # May 2021
    'SAND': Decimal('8.44'),    # Nov 2021
    'MANA': Decimal('5.90'),    # Nov 2021
    'AXS': Decimal('166'),      # Nov 2021
    'AAVE': Decimal('666'),     # May 2021
    'GRT': Decimal('2.88'),     # Feb 2021
    'ETC': Decimal('176'),      # May 2021
    'INJ': Decimal('52'),       # Mar 2024
    'KSM': Decimal('623'),      # May 2021
    'VET': Decimal('0.28'),     # Apr 2021
    'FTM': Decimal('3.46'),     # Oct 2021
    'ONE': Decimal('0.38'),     # Jan 2022
    'CRV': Decimal('6.51'),     # Jan 2022
    'RUNE': Decimal('21'),      # May 2021
    'KAVA': Decimal('9.12'),    # Sep 2021
    'ENJ': Decimal('4.85'),     # Nov 2021
    'CHZ': Decimal('0.89'),     # Mar 2021
    'ZIL': Decimal('0.26'),     # May 2021
    'LRC': Decimal('3.83'),     # Nov 2021
    'BAT': Decimal('1.92'),     # Nov 2021
    'COMP': Decimal('910'),     # May 2021
    'SUSHI': Decimal('23'),     # Mar 2021
    '1INCH': Decimal('7.87'),   # May 2021
    'SNX': Decimal('28.77'),    # Feb 2021
    'UNI': Decimal('44.92'),    # May 2021
    'YFI': Decimal('93000'),    # May 2021
    'MKR': Decimal('6339'),     # May 2021
    'ANKR': Decimal('0.22'),    # Apr 2021
    'STORJ': Decimal('3.91'),   # Mar 2021
    'REN': Decimal('1.83'),     # Feb 2021
    'CVC': Decimal('1.60'),     # Dec 2017
    'OMG': Decimal('28.35'),    # Jan 2018
    'ZRX': Decimal('2.50'),     # Apr 2021
    'SKL': Decimal('1.22'),     # Mar 2021
    'NKN': Decimal('1.41'),     # Apr 2021
    'OGN': Decimal('3.39'),     # Apr 2021
    'BAND': Decimal('23.19'),   # Aug 2020
    'COTI': Decimal('0.69'),    # Sep 2021
    'CTK': Decimal('2.99'),     # Apr 2021
    'BNT': Decimal('10.27'),    # Apr 2021
    'AUDIO': Decimal('4.99'),   # Mar 2021
    'RLC': Decimal('15.41'),    # May 2021
    'NMR': Decimal('89.07'),    # Jun 2017
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
        'GRT': 'the-graph', 'COMP': 'compound-governance-token',
        'SNX': 'havven', 'MKR': 'maker', 'SUSHI': 'sushi',
        'YFI': 'yearn-finance', '1INCH': '1inch',
    }
    prices = {}
    ids = list(set(cg_ids.get(a, a.lower()) for a in assets if a not in ['USD', 'USDC', 'USDT']))[:50]
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

async def run_ath_analysis():
    print("=" * 70)
    print("ATH ANALYSIS - What If Altcoins Pump?")
    print("=" * 70)

    transactions = load_transactions()

    # Calculate holdings
    holdings: Dict[str, Decimal] = defaultdict(Decimal)
    total_invested = Decimal('0')

    for tx in transactions:
        asset = tx['asset']
        qty = tx['quantity']
        tx_type = tx['type']

        if tx_type == 'Buy':
            holdings[asset] += qty
            total_invested += tx['total']
        elif tx_type == 'Sell':
            holdings[asset] -= qty
        elif tx_type == 'Staking Income':
            holdings[asset] += qty
        elif tx_type == 'Send':
            holdings[asset] -= qty
        elif tx_type in ('Receive', 'Deposit'):
            holdings[asset] += qty

    # Get current prices
    print("\n📊 Fetching current prices...")
    assets = [a for a, q in holdings.items() if q > 0]
    current_prices = await fetch_current_prices(assets)

    # Calculate values
    print("\n" + "=" * 70)
    print("YOUR HOLDINGS - Current vs ATH")
    print("=" * 70)

    results = []
    total_current = Decimal('0')
    total_ath = Decimal('0')
    assets_with_ath = 0

    for asset, qty in sorted(holdings.items(), key=lambda x: -x[1] * ATH_PRICES.get(x[0], Decimal('0'))):
        if qty <= 0 or asset in ['USD', 'USDC', 'USDT']:
            continue

        current_price = current_prices.get(asset, Decimal('0'))
        ath_price = ATH_PRICES.get(asset, Decimal('0'))

        current_value = qty * current_price
        ath_value = qty * ath_price

        total_current += current_value
        if ath_price > 0:
            total_ath += ath_value
            assets_with_ath += 1
            results.append({
                'asset': asset,
                'qty': qty,
                'current_price': current_price,
                'ath_price': ath_price,
                'current_value': current_value,
                'ath_value': ath_value,
                'upside': ath_value - current_value,
                'multiplier': (ath_price / current_price) if current_price > 0 else Decimal('0'),
            })

    # Sort by ATH value
    results.sort(key=lambda x: x['ath_value'], reverse=True)

    print(f"\n{'Asset':<8} {'Quantity':>12} {'Current':>10} {'ATH':>10} {'Current $':>12} {'ATH $':>12} {'Upside':>10}")
    print("-" * 85)

    for r in results[:25]:
        mult = r['multiplier']
        mult_str = f"{mult:.1f}x" if mult > 0 else "?"
        print(f"{r['asset']:<8} {float(r['qty']):>12.4f} ${r['current_price']:>8,.2f} ${r['ath_price']:>8,.2f} ${r['current_value']:>10,.0f} ${r['ath_value']:>10,.0f} {mult_str:>10}")

    print("-" * 85)
    print(f"{'TOTAL':<8} {'':<12} {'':<10} {'':<10} ${total_current:>10,.0f} ${total_ath:>10,.0f}")

    # Summary
    upside = total_ath - total_current
    upside_pct = (upside / total_current * 100) if total_current > 0 else Decimal('0')

    print(f"\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nTotal Invested:        ${total_invested:>12,.0f}")
    print(f"Current Value:         ${total_current:>12,.0f}")
    print(f"Value at ATH:          ${total_ath:>12,.0f}")
    print(f"Potential Upside:      ${upside:>12,.0f} (+{upside_pct:.0f}%)")

    # ROI scenarios
    print(f"\n📈 SCENARIO ANALYSIS")
    print("-" * 70)

    current_return = total_current - total_invested
    current_pct = (current_return / total_invested * 100) if total_invested > 0 else Decimal('0')

    ath_return = total_ath - total_invested
    ath_pct = (ath_return / total_invested * 100) if total_invested > 0 else Decimal('0')

    # Partial recovery scenarios
    recovery_50 = total_current + (upside * Decimal('0.5'))
    recovery_75 = total_current + (upside * Decimal('0.75'))

    print(f"Current:               ${total_current:>10,.0f}  ({current_pct:>+6.1f}% ROI)")
    print(f"50% recovery to ATH:   ${recovery_50:>10,.0f}  ({((recovery_50 - total_invested) / total_invested * 100):>+6.1f}% ROI)")
    print(f"75% recovery to ATH:   ${recovery_75:>10,.0f}  ({((recovery_75 - total_invested) / total_invested * 100):>+6.1f}% ROI)")
    print(f"Full ATH:              ${total_ath:>10,.0f}  ({ath_pct:>+6.1f}% ROI)")

    # Compare to BTC ATH scenario
    btc_qty = Decimal('0.310226')  # From earlier analysis
    btc_ath = Decimal('109000')
    btc_current = Decimal('94000')
    btc_ath_value = btc_qty * btc_ath
    btc_current_value = btc_qty * btc_current

    print(f"\n🔶 BTC COMPARISON (if you had done BTC DCA)")
    print("-" * 70)
    print(f"BTC you would have:    {btc_qty:.6f} BTC")
    print(f"At current ~$94k:      ${btc_current_value:>10,.0f}")
    print(f"At ATH ~$109k:         ${btc_ath_value:>10,.0f}")

    print(f"\n💡 KEY INSIGHT")
    print("-" * 70)

    if total_ath > btc_ath_value:
        diff = total_ath - btc_ath_value
        print(f"IF all your altcoins hit ATH: ${total_ath:,.0f}")
        print(f"IF BTC hits ATH:              ${btc_ath_value:,.0f}")
        print(f"Your altcoin bet WINS by:     ${diff:,.0f}")
        print("")
        print("The altcoin gamble pays off IF there's a full altcoin season.")
        print("But altcoins rarely ALL hit ATH at the same time.")
    else:
        diff = btc_ath_value - total_ath
        print(f"Even at full ATH, BTC would still win by ${diff:,.0f}")

    # Realistic scenario
    print(f"\n⚠️  REALITY CHECK")
    print("-" * 70)
    print("Most altcoins from 2021 NEVER recovered to ATH.")
    print("New altcoins often replace old ones each cycle.")
    print(f"Your {assets_with_ath} altcoins need an EXTREME altcoin season to recover.")

def main():
    asyncio.run(run_ath_analysis())

if __name__ == '__main__':
    main()
