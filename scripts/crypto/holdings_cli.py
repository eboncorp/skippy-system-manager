#!/usr/bin/env python3
"""
Holdings Import CLI
===================
Import your crypto holdings and get Personal/Business allocation recommendations.

Usage:
    python holdings_cli.py import holdings.csv
    python holdings_cli.py import holdings.csv --export output.csv
    python holdings_cli.py template                    # Generate template CSV
    python holdings_cli.py demo                        # Run with sample data
    
File Format (CSV):
    symbol,quantity,current_account,cost_basis
    BTC,0.5,personal,25000
    ETH,10,business,15000
    SOL,100,,                    # Unknown account, no cost basis
    
Or simple format (space/tab separated):
    BTC 0.5 personal
    ETH 10 business
    
Or just symbols (one per line):
    BTC
    ETH
"""

import asyncio
import aiohttp
import argparse
import csv
import sys
import os
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


# ============================================================================
# CONSTANTS
# ============================================================================

STABLECOINS = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "GUSD", "FRAX", 
               "LUSD", "USDD", "EURC", "PYUSD", "FDUSD", "USDJ", "UST", "USTC"}

WRAPPED = {"WBTC", "WETH", "STETH", "RETH", "CBETH", "WSTETH", "HBTC", 
           "RENBTC", "WBNB", "WMATIC", "WAVAX", "WFTM", "WSOL"}

EXCHANGE_TOKENS = {"BNB", "CRO", "FTT", "OKB", "KCS", "HT", "LEO", "GT", "MX"}

PRIVACY_COINS = {"XMR", "ZEC", "DASH", "ZEN", "SCRT", "ARRR", "FIRO", "BEAM", "GRIN"}

SECURITY_RISKS = {"LUNA", "LUNC", "UST", "USTC", "FTT", "SRM"}

BLUE_CHIPS = {"BTC", "ETH"}

# Assets best held in business treasury (institutional grade, liquid)
INSTITUTIONAL = {"BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK", "MATIC", "ATOM", "LTC"}

# Staking rates (higher on Coinbase One = prefer personal)
STAKING_RATES = {
    "ETH":   {"coinbase": 3.8, "kraken": 3.2},
    "SOL":   {"coinbase": 6.5, "kraken": 6.0},
    "ADA":   {"coinbase": 3.2, "kraken": 3.0},
    "DOT":   {"coinbase": 11.0, "kraken": 10.0},
    "ATOM":  {"coinbase": 8.5, "kraken": 7.5},
    "AVAX":  {"coinbase": 7.0, "kraken": 6.5},
    "MATIC": {"coinbase": 4.5, "kraken": 4.0},
    "NEAR":  {"coinbase": 6.0, "kraken": 5.5},
    "ALGO":  {"coinbase": 5.0, "kraken": 4.5},
    "XTZ":   {"coinbase": 5.5, "kraken": 5.0},
    "MINA":  {"coinbase": 10.0, "kraken": 9.0},
    "OSMO":  {"coinbase": 8.0, "kraken": 7.5},
    "FLOW":  {"coinbase": 6.0, "kraken": 5.5},
    "ROSE":  {"coinbase": 4.0, "kraken": 3.5},
    "KAVA":  {"coinbase": 4.5, "kraken": 4.0},
    "INJ":   {"coinbase": 15.0, "kraken": 14.0},
    "TIA":   {"coinbase": 12.0, "kraken": 11.0},
    "SEI":   {"coinbase": 4.0, "kraken": 3.5},
}

# CoinGecko ID mapping for price lookups
COINGECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "XRP": "ripple", "ADA": "cardano", "DOGE": "dogecoin",
    "AVAX": "avalanche-2", "DOT": "polkadot", "LINK": "chainlink",
    "MATIC": "matic-network", "ATOM": "cosmos", "LTC": "litecoin",
    "UNI": "uniswap", "NEAR": "near", "APT": "aptos",
    "FIL": "filecoin", "ARB": "arbitrum", "OP": "optimism",
    "INJ": "injective-protocol", "RENDER": "render-token",
    "ALGO": "algorand", "XTZ": "tezos", "MINA": "mina-protocol",
    "FLOW": "flow", "OSMO": "osmosis", "SHIB": "shiba-inu",
    "PEPE": "pepe", "BONK": "bonk", "WIF": "dogwifcoin",
    "AAVE": "aave", "MKR": "maker", "CRV": "curve-dao-token",
    "SNX": "synthetix-network-token", "COMP": "compound-governance-token",
    "LDO": "lido-dao", "GRT": "the-graph", "IMX": "immutable-x",
    "SAND": "the-sandbox", "MANA": "decentraland", "AXS": "axie-infinity",
    "FET": "fetch-ai", "TRX": "tron", "ETC": "ethereum-classic",
    "BCH": "bitcoin-cash", "XLM": "stellar", "VET": "vechain",
    "HBAR": "hedera", "FTM": "fantom", "XMR": "monero",
    "SUI": "sui", "SEI": "sei-network", "TIA": "celestia",
    "JUP": "jupiter-exchange-solana", "PYTH": "pyth-network",
    "WLD": "worldcoin-wld", "STRK": "starknet", "BLUR": "blur",
    "USDT": "tether", "USDC": "usd-coin", "BNB": "binancecoin",
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Holding:
    symbol: str
    quantity: float
    current_account: str
    cost_basis: float
    price: float = 0.0
    value: float = 0.0
    target_account: str = ""
    reason: str = ""
    needs_move: bool = False
    staking_cb: Optional[float] = None
    staking_kr: Optional[float] = None


# ============================================================================
# CORE LOGIC
# ============================================================================

def get_recommendation(symbol: str, staking_threshold: float = 5.0) -> tuple:
    """
    Determine which account a symbol should be held in.
    
    Returns:
        (target_account, reason)
    """
    symbol = symbol.upper()
    
    # Exclusions first
    if symbol in STABLECOINS:
        return "excluded", "stablecoin"
    if symbol in WRAPPED:
        return "excluded", "wrapped asset"
    if symbol in EXCHANGE_TOKENS:
        return "excluded", "exchange token"
    if symbol in PRIVACY_COINS:
        return "excluded", "privacy coin"
    if symbol in SECURITY_RISKS:
        return "excluded", "security risk"
    
    # High staking rewards -> personal (Coinbase One has higher rates)
    if symbol in STAKING_RATES:
        apy = STAKING_RATES[symbol]["coinbase"]
        if apy >= staking_threshold:
            return "personal", f"staking {apy}%"
        else:
            return "business", f"staking {apy}% (below threshold)"
    
    # Blue chips -> business treasury
    if symbol in BLUE_CHIPS:
        return "business", "treasury"
    
    # Institutional grade -> business
    if symbol in INSTITUTIONAL:
        return "business", "institutional"
    
    # Everything else -> personal (for 0% trading fees)
    return "personal", "default"


def parse_holdings_file(filepath: str) -> List[Dict]:
    """
    Parse holdings from CSV or text file.
    
    Supported formats:
    1. CSV: symbol,quantity,current_account,cost_basis
    2. Simple: symbol quantity account
    3. List: Just symbols
    """
    holdings = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # CSV format
        if ',' in line:
            parts = [p.strip() for p in line.split(',')]
            symbol = parts[0].upper()
            
            # Skip header
            if symbol.lower() in ('symbol', 'ticker', 'coin', 'asset'):
                continue
            
            holdings.append({
                "symbol": symbol,
                "quantity": float(parts[1]) if len(parts) > 1 and parts[1] else 1.0,
                "current_account": parts[2].lower() if len(parts) > 2 and parts[2] else "unknown",
                "cost_basis": float(parts[3]) if len(parts) > 3 and parts[3] else 0.0
            })
        
        # Space/tab separated
        elif ' ' in line or '\t' in line:
            parts = line.split()
            holdings.append({
                "symbol": parts[0].upper(),
                "quantity": float(parts[1]) if len(parts) > 1 else 1.0,
                "current_account": parts[2].lower() if len(parts) > 2 else "unknown"
            })
        
        # Just symbol
        else:
            holdings.append({
                "symbol": line.upper(),
                "quantity": 1.0,
                "current_account": "unknown"
            })
    
    return holdings


async def fetch_prices(symbols: List[str]) -> Dict[str, float]:
    """Fetch current prices from CoinGecko"""
    prices = {}
    
    # Build list of CoinGecko IDs
    ids_to_fetch = []
    symbol_to_id = {}
    
    for symbol in symbols:
        symbol = symbol.upper()
        coin_id = COINGECKO_IDS.get(symbol, symbol.lower())
        ids_to_fetch.append(coin_id)
        symbol_to_id[coin_id] = symbol
    
    async with aiohttp.ClientSession() as session:
        # Fetch in batches
        for i in range(0, len(ids_to_fetch), 100):
            batch = ids_to_fetch[i:i+100]
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": ",".join(batch), "vs_currencies": "usd"}
            
            try:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for coin_id, symbol in symbol_to_id.items():
                            if coin_id in data:
                                prices[symbol] = data[coin_id]["usd"]
                    elif resp.status == 429:
                        print("  Rate limited, waiting 60s...")
                        await asyncio.sleep(60)
            except Exception as e:
                print(f"  Warning: Price fetch error: {e}")
            
            await asyncio.sleep(1.5)  # Rate limit
    
    return prices


def analyze_holdings(holdings: List[Dict], prices: Dict[str, float]) -> tuple:
    """
    Analyze holdings and generate recommendations.
    
    Returns:
        (personal_holdings, business_holdings, excluded_holdings, needs_move)
    """
    personal = []
    business = []
    excluded = []
    needs_move = []
    
    for h in holdings:
        symbol = h["symbol"]
        qty = h["quantity"]
        current = h.get("current_account", "unknown")
        cost = h.get("cost_basis", 0)
        price = prices.get(symbol, 0)
        value = qty * price
        
        target, reason = get_recommendation(symbol)
        
        holding = Holding(
            symbol=symbol,
            quantity=qty,
            current_account=current,
            cost_basis=cost,
            price=price,
            value=value,
            target_account=target,
            reason=reason,
            needs_move=(current != "unknown" and current != target and target != "excluded"),
            staking_cb=STAKING_RATES.get(symbol, {}).get("coinbase"),
            staking_kr=STAKING_RATES.get(symbol, {}).get("kraken"),
        )
        
        if target == "personal":
            personal.append(holding)
        elif target == "business":
            business.append(holding)
        else:
            excluded.append(holding)
        
        if holding.needs_move:
            needs_move.append(holding)
    
    # Sort by value
    personal.sort(key=lambda x: x.value, reverse=True)
    business.sort(key=lambda x: x.value, reverse=True)
    excluded.sort(key=lambda x: x.value, reverse=True)
    
    return personal, business, excluded, needs_move


def print_report(personal: List[Holding], business: List[Holding], 
                excluded: List[Holding], needs_move: List[Holding]):
    """Print formatted holdings report"""
    
    total_value = sum(h.value for h in personal + business + excluded)
    personal_value = sum(h.value for h in personal)
    business_value = sum(h.value for h in business)
    excluded_value = sum(h.value for h in excluded)
    
    print()
    print("=" * 90)
    print("  HOLDINGS IMPORT ANALYSIS")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 90)
    
    # Summary
    print()
    print("SUMMARY")
    print("-" * 90)
    print(f"Total Holdings:     {len(personal) + len(business) + len(excluded):>6}")
    print(f"Total Value:        ${total_value:>15,.2f}")
    print()
    
    pct_p = (personal_value / total_value * 100) if total_value else 0
    pct_b = (business_value / total_value * 100) if total_value else 0
    pct_e = (excluded_value / total_value * 100) if total_value else 0
    
    print(f"Personal (Coinbase One):  {len(personal):>4} assets  ${personal_value:>12,.2f}  ({pct_p:>5.1f}%)")
    print(f"Business (Kraken):        {len(business):>4} assets  ${business_value:>12,.2f}  ({pct_b:>5.1f}%)")
    print(f"Excluded:                 {len(excluded):>4} assets  ${excluded_value:>12,.2f}  ({pct_e:>5.1f}%)")
    
    # Personal portfolio
    if personal:
        print()
        print("PERSONAL PORTFOLIO (Coinbase One) - 0% fees, higher staking")
        print("-" * 90)
        print(f"{'Symbol':<8} {'Quantity':>14} {'Price':>10} {'Value':>14} {'Stake':>8} {'Reason':<20}")
        print("-" * 90)
        
        for h in personal[:30]:
            stake = f"{h.staking_cb:.1f}%" if h.staking_cb else "-"
            print(f"{h.symbol:<8} {h.quantity:>14,.4f} ${h.price:>9,.2f} ${h.value:>13,.2f} {stake:>8} {h.reason:<20}")
        
        if len(personal) > 30:
            print(f"  ... and {len(personal) - 30} more")
    
    # Business portfolio
    if business:
        print()
        print("BUSINESS PORTFOLIO (Kraken) - Treasury, institutional grade")
        print("-" * 90)
        print(f"{'Symbol':<8} {'Quantity':>14} {'Price':>10} {'Value':>14} {'Stake':>8} {'Reason':<20}")
        print("-" * 90)
        
        for h in business[:30]:
            stake = f"{h.staking_kr:.1f}%" if h.staking_kr else "-"
            print(f"{h.symbol:<8} {h.quantity:>14,.4f} ${h.price:>9,.2f} ${h.value:>13,.2f} {stake:>8} {h.reason:<20}")
        
        if len(business) > 30:
            print(f"  ... and {len(business) - 30} more")
    
    # Excluded
    if excluded:
        print()
        print("EXCLUDED (Consider Selling or Manual Override)")
        print("-" * 90)
        for h in excluded:
            print(f"  {h.symbol:<8} ${h.value:>12,.2f}  - {h.reason}")
    
    # Transfers needed
    if needs_move:
        print()
        print("ASSETS NEEDING ACCOUNT TRANSFER")
        print("-" * 90)
        print(f"{'Symbol':<8} {'Value':>14} {'From':<12} {'To':<12} {'Reason':<20}")
        print("-" * 90)
        
        for h in needs_move:
            print(f"{h.symbol:<8} ${h.value:>13,.2f} {h.current_account:<12} {h.target_account:<12} {h.reason:<20}")
        
        total_move = sum(h.value for h in needs_move)
        print()
        print(f"Total value to transfer: ${total_move:,.2f}")
    else:
        print()
        print("✓ All assets are in their recommended accounts")
    
    print()
    print("=" * 90)


def export_csv(personal: List[Holding], business: List[Holding], 
               excluded: List[Holding], output_path: str):
    """Export analysis to CSV"""
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Symbol', 'Quantity', 'Price', 'Value', 'Current', 'Target', 
                        'Reason', 'Needs Move', 'CB Stake', 'KR Stake'])
        
        for h in personal + business + excluded:
            writer.writerow([
                h.symbol, h.quantity, h.price, h.value, h.current_account,
                h.target_account, h.reason, h.needs_move,
                h.staking_cb or '', h.staking_kr or ''
            ])
    
    print(f"Exported to: {output_path}")


def generate_template():
    """Generate template CSV file"""
    template = """# Crypto Holdings Template
# Format: symbol,quantity,current_account,cost_basis
# current_account: personal, business, or leave empty if unknown
# cost_basis: optional, what you paid total
symbol,quantity,current_account,cost_basis
BTC,0.5,personal,25000
ETH,10,personal,18000
SOL,100,personal,8000
XRP,5000,business,3500
ADA,10000,,
DOGE,50000,personal,
"""
    
    with open('holdings_template.csv', 'w') as f:
        f.write(template)
    
    print("Generated: holdings_template.csv")
    print()
    print("Fill in your holdings and run:")
    print("  python holdings_cli.py import holdings_template.csv")


def run_demo():
    """Run with sample data (no API needed)"""
    
    # Sample holdings
    holdings = [
        {"symbol": "BTC", "quantity": 0.75, "current_account": "personal", "cost_basis": 45000},
        {"symbol": "ETH", "quantity": 8.5, "current_account": "personal", "cost_basis": 18000},
        {"symbol": "SOL", "quantity": 150, "current_account": "personal", "cost_basis": 12000},
        {"symbol": "XRP", "quantity": 5000, "current_account": "business", "cost_basis": 3500},
        {"symbol": "ADA", "quantity": 10000, "current_account": "personal", "cost_basis": 4500},
        {"symbol": "DOGE", "quantity": 50000, "current_account": "personal", "cost_basis": 8000},
        {"symbol": "AVAX", "quantity": 200, "current_account": "personal", "cost_basis": 5000},
        {"symbol": "DOT", "quantity": 500, "current_account": "personal", "cost_basis": 3000},
        {"symbol": "LINK", "quantity": 300, "current_account": "business", "cost_basis": 4500},
        {"symbol": "MATIC", "quantity": 8000, "current_account": "personal", "cost_basis": 3200},
        {"symbol": "ATOM", "quantity": 400, "current_account": "personal", "cost_basis": 2800},
        {"symbol": "LTC", "quantity": 25, "current_account": "business", "cost_basis": 2500},
        {"symbol": "INJ", "quantity": 100, "current_account": "personal", "cost_basis": 2500},
        {"symbol": "NEAR", "quantity": 1000, "current_account": "personal", "cost_basis": 2500},
        {"symbol": "SHIB", "quantity": 50000000, "current_account": "personal", "cost_basis": 500},
        {"symbol": "PEPE", "quantity": 100000000, "current_account": "personal", "cost_basis": 300},
        {"symbol": "USDT", "quantity": 5000, "current_account": "personal", "cost_basis": 5000},
        {"symbol": "USDC", "quantity": 3000, "current_account": "business", "cost_basis": 3000},
        {"symbol": "XMR", "quantity": 10, "current_account": "personal", "cost_basis": 2000},
        {"symbol": "BNB", "quantity": 5, "current_account": "personal", "cost_basis": 1500},
    ]
    
    # Sample prices
    prices = {
        "BTC": 91500, "ETH": 3150, "SOL": 195, "XRP": 2.15, "ADA": 0.98,
        "DOGE": 0.35, "AVAX": 78, "DOT": 8.5, "LINK": 47, "MATIC": 0.85,
        "ATOM": 10.2, "LTC": 105, "INJ": 38, "NEAR": 5.2,
        "SHIB": 0.000022, "PEPE": 0.0000015, "USDT": 1, "USDC": 1,
        "XMR": 195, "BNB": 680
    }
    
    print("Running demo with sample data...")
    personal, business, excluded, needs_move = analyze_holdings(holdings, prices)
    print_report(personal, business, excluded, needs_move)


async def cmd_import(args):
    """Import and analyze holdings"""
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return
    
    # Parse file
    print(f"Parsing {args.file}...")
    holdings = parse_holdings_file(args.file)
    print(f"Found {len(holdings)} holdings")
    
    # Fetch prices
    if not args.no_fetch:
        print("Fetching current prices...")
        symbols = [h["symbol"] for h in holdings]
        prices = await fetch_prices(symbols)
        print(f"Got prices for {len(prices)} assets")
    else:
        prices = {}
    
    # Analyze
    personal, business, excluded, needs_move = analyze_holdings(holdings, prices)
    
    # Print report
    print_report(personal, business, excluded, needs_move)
    
    # Export if requested
    if args.export:
        export_csv(personal, business, excluded, args.export)


def main():
    parser = argparse.ArgumentParser(
        description="Import crypto holdings and get allocation recommendations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python holdings_cli.py import holdings.csv
  python holdings_cli.py import holdings.csv --export analysis.csv
  python holdings_cli.py import holdings.csv --no-fetch
  python holdings_cli.py template
  python holdings_cli.py demo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import holdings file')
    import_parser.add_argument('file', help='Path to holdings CSV file')
    import_parser.add_argument('--export', '-e', help='Export results to CSV')
    import_parser.add_argument('--no-fetch', action='store_true', 
                               help='Skip price fetching (offline mode)')
    
    # Template command
    subparsers.add_parser('template', help='Generate template CSV file')
    
    # Demo command
    subparsers.add_parser('demo', help='Run with sample data')
    
    args = parser.parse_args()
    
    if args.command == 'import':
        asyncio.run(cmd_import(args))
    elif args.command == 'template':
        generate_template()
    elif args.command == 'demo':
        run_demo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
