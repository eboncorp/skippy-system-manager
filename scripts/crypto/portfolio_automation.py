#!/usr/bin/env python3
"""
Portfolio Automation - Combines holdings, signals, and strategies

Automates:
1. Portfolio analysis from your transaction history
2. Signal analysis on all holdings
3. Strategy recommendations (DCA, Swing, Rebalance)
4. Account allocation (Personal vs Business)
5. Daily action items

Run daily via cron or manually:
    python portfolio_automation.py daily
    python portfolio_automation.py rebalance
    python portfolio_automation.py alerts
"""

import sys
import os
import csv
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

TRANSACTION_DIR = '/home/dave/skippy/lib/python/crypto_trading/data/transactions'
OUTPUT_DIR = '/home/dave/skippy/work/crypto/automation'

# Staking APY rates (approximate)
STAKING_APY = {
    'SOL': Decimal('6.5'), 'DOT': Decimal('11'), 'ATOM': Decimal('8.5'),
    'ADA': Decimal('3.5'), 'AVAX': Decimal('8'), 'XTZ': Decimal('5.5'),
    'ALGO': Decimal('4'), 'NEAR': Decimal('9'), 'INJ': Decimal('15'),
    'MATIC': Decimal('4'), 'POL': Decimal('4'), 'ETH': Decimal('3.5'),
}

# Account allocation rules
BUSINESS_ASSETS = {'BTC', 'ETH', 'XRP', 'ADA', 'LINK', 'LTC', 'BCH'}  # Treasury/institutional
EXCLUDED_ASSETS = {'USD', 'USDC', 'USDT', 'DAI', 'BUSD', 'WBTC', 'WETH'}  # Stablecoins/wrapped

class AccountType(Enum):
    PERSONAL = "personal"   # Coinbase One - staking, speculative
    BUSINESS = "business"   # Kraken - treasury, long-term
    EXCLUDED = "excluded"   # Stablecoins, not counted

class ActionType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STAKE = "STAKE"
    REBALANCE = "REBALANCE"

@dataclass
class Holding:
    symbol: str
    quantity: Decimal
    cost_basis: Decimal
    current_price: Decimal = Decimal('0')
    current_value: Decimal = Decimal('0')
    staking_apy: Decimal = Decimal('0')
    account: AccountType = AccountType.PERSONAL
    signal_score: float = 0.0
    signal_condition: str = "UNKNOWN"

@dataclass
class ActionItem:
    priority: int  # 1=high, 2=medium, 3=low
    action: ActionType
    symbol: str
    reason: str
    amount_usd: Optional[Decimal] = None
    multiplier: Optional[float] = None

@dataclass
class DailyReport:
    timestamp: datetime
    total_value: Decimal
    total_cost: Decimal
    unrealized_pnl: Decimal
    pnl_pct: Decimal
    holdings: List[Holding]
    actions: List[ActionItem]
    market_condition: str
    strategy_mode: str

def parse_usd(value: str) -> Decimal:
    if not value:
        return Decimal('0')
    clean = value.replace('$', '').replace(',', '').strip()
    try:
        return Decimal(clean)
    except:
        return Decimal('0')

def load_holdings_from_transactions() -> Dict[str, Holding]:
    """Load current holdings from transaction CSVs."""
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
        if qty > 0 and symbol not in EXCLUDED_ASSETS:
            # Determine account type
            if symbol in BUSINESS_ASSETS:
                account = AccountType.BUSINESS
            elif STAKING_APY.get(symbol, Decimal('0')) > Decimal('5'):
                account = AccountType.PERSONAL  # High staking = personal
            else:
                account = AccountType.PERSONAL  # Default to personal

            result[symbol] = Holding(
                symbol=symbol,
                quantity=qty,
                cost_basis=cost_basis[symbol],
                staking_apy=STAKING_APY.get(symbol, Decimal('0')),
                account=account,
            )

    return result

async def fetch_prices(symbols: List[str]) -> Dict[str, Decimal]:
    """Fetch current prices from CoinGecko."""
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
        print(f"  Price fetch error: {e}")

    return prices

async def fetch_fear_greed() -> Tuple[int, str]:
    """Fetch Fear & Greed Index."""
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    value = int(data['data'][0]['value'])
                    classification = data['data'][0]['value_classification']
                    return value, classification
    except:
        pass
    return 50, "Neutral"

def calculate_signal_score(fear_greed: int, price_change_24h: float = 0) -> Tuple[float, str]:
    """Calculate composite signal score."""
    # Simple scoring based on Fear & Greed
    # Real system uses 130+ signals, this is simplified

    # Convert F&G (0-100 where 0=fear) to score (-100 to +100 where negative=fear)
    score = (fear_greed - 50) * 2

    if score < -60:
        condition = "EXTREME_FEAR"
    elif score < -40:
        condition = "FEAR"
    elif score < -20:
        condition = "MILD_FEAR"
    elif score < 0:
        condition = "SLIGHT_FEAR"
    elif score < 20:
        condition = "NEUTRAL"
    elif score < 40:
        condition = "MILD_GREED"
    elif score < 60:
        condition = "GREED"
    else:
        condition = "EXTREME_GREED"

    return score, condition

def get_dca_multiplier(score: float) -> float:
    """Get DCA multiplier based on signal score."""
    if score < -60:
        return 3.0    # Extreme fear - max accumulation
    elif score < -40:
        return 2.5    # Fear - aggressive buying
    elif score < -20:
        return 2.0    # Mild fear - increased buying
    elif score < 0:
        return 1.5    # Slight fear - mild increase
    elif score < 20:
        return 1.0    # Neutral - normal DCA
    elif score < 40:
        return 0.75   # Mild greed - reduced buying
    elif score < 60:
        return 0.5    # Greed - minimal buying
    else:
        return 0.25   # Extreme greed - consider taking profits

def generate_actions(
    holdings: Dict[str, Holding],
    score: float,
    condition: str,
    daily_budget: Decimal = Decimal('40')
) -> List[ActionItem]:
    """Generate action items based on holdings and signals."""
    actions = []
    multiplier = get_dca_multiplier(score)
    adjusted_budget = daily_budget * Decimal(str(multiplier))

    # Sort holdings by value
    sorted_holdings = sorted(
        holdings.values(),
        key=lambda h: h.current_value,
        reverse=True
    )

    # DCA recommendation
    if score < 20:  # Fear to neutral - buy mode
        # Prioritize BTC/ETH for DCA
        btc_eth_pct = Decimal('0.7')  # 70% to BTC/ETH
        alt_pct = Decimal('0.3')  # 30% to alts

        actions.append(ActionItem(
            priority=1,
            action=ActionType.BUY,
            symbol="BTC",
            reason=f"DCA at {multiplier}x ({condition})",
            amount_usd=adjusted_budget * btc_eth_pct * Decimal('0.6'),
            multiplier=multiplier,
        ))
        actions.append(ActionItem(
            priority=1,
            action=ActionType.BUY,
            symbol="ETH",
            reason=f"DCA at {multiplier}x ({condition})",
            amount_usd=adjusted_budget * btc_eth_pct * Decimal('0.4'),
            multiplier=multiplier,
        ))

        # Top alts
        alt_budget = adjusted_budget * alt_pct
        top_alts = [h for h in sorted_holdings if h.symbol not in ['BTC', 'ETH']][:3]
        if top_alts:
            per_alt = alt_budget / len(top_alts)
            for h in top_alts:
                actions.append(ActionItem(
                    priority=2,
                    action=ActionType.BUY,
                    symbol=h.symbol,
                    reason=f"Altcoin DCA at {multiplier}x",
                    amount_usd=per_alt,
                    multiplier=multiplier,
                ))

    elif score > 60:  # Extreme greed - consider taking profits
        # Find positions with gains
        for h in sorted_holdings[:5]:
            if h.current_value > h.cost_basis * Decimal('1.5'):  # 50%+ gain
                actions.append(ActionItem(
                    priority=1,
                    action=ActionType.SELL,
                    symbol=h.symbol,
                    reason=f"Take profits ({condition}) - up {((h.current_value / h.cost_basis - 1) * 100):.0f}%",
                    amount_usd=h.current_value * Decimal('0.1'),  # Sell 10%
                ))

    # Staking recommendations
    for h in sorted_holdings:
        if h.staking_apy > 5 and h.current_value > 100:
            actions.append(ActionItem(
                priority=3,
                action=ActionType.STAKE,
                symbol=h.symbol,
                reason=f"Stake for {h.staking_apy}% APY",
            ))

    # Rebalance if any position > 15% of portfolio
    total_value = sum(h.current_value for h in sorted_holdings)
    if total_value > 0:
        for h in sorted_holdings:
            pct = (h.current_value / total_value) * 100
            if pct > 15 and h.symbol not in ['BTC', 'ETH']:
                actions.append(ActionItem(
                    priority=2,
                    action=ActionType.REBALANCE,
                    symbol=h.symbol,
                    reason=f"Position too large ({pct:.1f}% of portfolio)",
                ))

    return sorted(actions, key=lambda a: a.priority)

async def run_daily_analysis(daily_budget: Decimal = Decimal('40')):
    """Run full daily portfolio analysis."""

    print("=" * 70)
    print(f"DAILY PORTFOLIO AUTOMATION - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    # Load holdings
    print("\n📊 Loading holdings from transactions...")
    holdings = load_holdings_from_transactions()
    print(f"   Found {len(holdings)} assets with holdings")

    # Fetch prices
    print("\n💰 Fetching current prices...")
    symbols = list(holdings.keys())
    prices = await fetch_prices(symbols)
    print(f"   Got prices for {len(prices)} assets")

    # Update holdings with prices
    total_value = Decimal('0')
    total_cost = Decimal('0')
    for symbol, h in holdings.items():
        h.current_price = prices.get(symbol, Decimal('0'))
        h.current_value = h.quantity * h.current_price
        total_value += h.current_value
        total_cost += h.cost_basis

    # Fetch market sentiment
    print("\n📈 Fetching market sentiment...")
    fg_value, fg_class = await fetch_fear_greed()
    score, condition = calculate_signal_score(fg_value)
    multiplier = get_dca_multiplier(score)
    print(f"   Fear & Greed: {fg_value} ({fg_class})")
    print(f"   Signal Score: {score:+.1f} ({condition})")
    print(f"   DCA Multiplier: {multiplier}x")

    # Generate actions
    print("\n🎯 Generating action items...")
    actions = generate_actions(holdings, score, condition, daily_budget)

    # Print report
    print("\n" + "=" * 70)
    print("PORTFOLIO SUMMARY")
    print("=" * 70)

    pnl = total_value - total_cost
    pnl_pct = (pnl / total_cost * 100) if total_cost > 0 else Decimal('0')

    print(f"\n{'Metric':<25} {'Value':>20}")
    print("-" * 50)
    print(f"{'Total Cost Basis':<25} ${total_cost:>18,.2f}")
    print(f"{'Current Value':<25} ${total_value:>18,.2f}")
    print(f"{'Unrealized P/L':<25} ${pnl:>18,.2f}")
    print(f"{'P/L %':<25} {pnl_pct:>18.1f}%")
    print(f"{'Market Condition':<25} {condition:>20}")
    print(f"{'DCA Multiplier':<25} {multiplier:>19.2f}x")

    # Top holdings
    print("\n" + "-" * 70)
    print("TOP HOLDINGS")
    print("-" * 70)
    print(f"{'Asset':<8} {'Qty':>12} {'Price':>10} {'Value':>12} {'P/L':>10} {'Account':<10}")
    print("-" * 70)

    sorted_holdings = sorted(holdings.values(), key=lambda h: h.current_value, reverse=True)
    for h in sorted_holdings[:15]:
        if h.current_value > 0:
            h_pnl = h.current_value - h.cost_basis
            acct = "Personal" if h.account == AccountType.PERSONAL else "Business"
            print(f"{h.symbol:<8} {float(h.quantity):>12.4f} ${h.current_price:>8,.2f} ${h.current_value:>10,.0f} ${h_pnl:>8,.0f} {acct:<10}")

    # Action items
    print("\n" + "=" * 70)
    print("TODAY'S ACTION ITEMS")
    print("=" * 70)

    if not actions:
        print("\n  No actions recommended today.")
    else:
        for i, a in enumerate(actions[:10], 1):
            priority_icon = "🔴" if a.priority == 1 else "🟡" if a.priority == 2 else "🟢"
            amount_str = f"${a.amount_usd:.2f}" if a.amount_usd else ""
            print(f"\n  {priority_icon} {a.action.value}: {a.symbol} {amount_str}")
            print(f"     {a.reason}")

    # DCA allocation
    adjusted_budget = daily_budget * Decimal(str(multiplier))
    print("\n" + "-" * 70)
    print(f"SUGGESTED DCA TODAY: ${adjusted_budget:.2f} (base ${daily_budget} × {multiplier}x)")
    print("-" * 70)
    print(f"  BTC: ${adjusted_budget * Decimal('0.42'):.2f} (42%)")
    print(f"  ETH: ${adjusted_budget * Decimal('0.28'):.2f} (28%)")
    print(f"  SOL: ${adjusted_budget * Decimal('0.10'):.2f} (10%)")
    print(f"  Top Alts: ${adjusted_budget * Decimal('0.20'):.2f} (20%)")

    # Save report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_file = f"{OUTPUT_DIR}/daily_report_{datetime.now().strftime('%Y%m%d')}.json"

    report_data = {
        'timestamp': datetime.now().isoformat(),
        'total_value': float(total_value),
        'total_cost': float(total_cost),
        'pnl': float(pnl),
        'pnl_pct': float(pnl_pct),
        'fear_greed': fg_value,
        'signal_score': score,
        'condition': condition,
        'multiplier': multiplier,
        'actions': [
            {
                'action': a.action.value,
                'symbol': a.symbol,
                'reason': a.reason,
                'amount': float(a.amount_usd) if a.amount_usd else None,
            }
            for a in actions
        ],
    }

    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"\n📄 Report saved: {report_file}")

    return report_data

async def run_alerts():
    """Check for alert conditions."""
    print("=" * 70)
    print("ALERT CHECK")
    print("=" * 70)

    fg_value, fg_class = await fetch_fear_greed()
    score, condition = calculate_signal_score(fg_value)

    alerts = []

    if score < -40:
        alerts.append(f"🔴 FEAR ALERT: Market in {condition} (score: {score:+.0f})")
        alerts.append(f"   Consider increasing DCA to {get_dca_multiplier(score)}x")

    if score > 60:
        alerts.append(f"🟡 GREED ALERT: Market in {condition} (score: {score:+.0f})")
        alerts.append(f"   Consider taking profits or reducing DCA")

    if not alerts:
        print(f"\n  Market neutral: {condition} (score: {score:+.0f})")
        print("  No alerts triggered.")
    else:
        for alert in alerts:
            print(f"\n  {alert}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Portfolio Automation')
    parser.add_argument('command', choices=['daily', 'alerts', 'quick'],
                       default='daily', nargs='?')
    parser.add_argument('--budget', type=float, default=40,
                       help='Daily DCA budget in USD')

    args = parser.parse_args()

    if args.command == 'daily':
        asyncio.run(run_daily_analysis(Decimal(str(args.budget))))
    elif args.command == 'alerts':
        asyncio.run(run_alerts())
    elif args.command == 'quick':
        asyncio.run(run_alerts())

if __name__ == '__main__':
    main()
