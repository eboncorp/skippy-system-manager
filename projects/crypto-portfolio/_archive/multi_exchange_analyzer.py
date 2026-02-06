"""
Multi-Exchange Portfolio Analyzer
Aggregates and analyzes crypto holdings across Coinbase, Kraken, and Crypto.com.

Usage:
    python multi_exchange_analyzer.py
    python multi_exchange_analyzer.py --exchanges coinbase kraken
    python multi_exchange_analyzer.py --summary-only
"""

import os
import argparse
from typing import Optional
from dotenv import load_dotenv
from tabulate import tabulate

# Import exchange clients
from coinbase_client import CoinbaseClient
from kraken_client import KrakenClient
from cryptocom_client import CryptoComClient
from gemini_client import GeminiClient


class MultiExchangeAnalyzer:
    """Aggregates portfolio data from multiple exchanges."""
    
    def __init__(self):
        load_dotenv()
        self.clients = {}
        self.holdings_by_exchange = {}
        self.aggregated_holdings = {}
        
    def connect_coinbase(self) -> bool:
        """Initialize Coinbase connection."""
        api_key = os.getenv("COINBASE_API_KEY")
        api_secret = os.getenv("COINBASE_API_SECRET")
        
        if api_key and api_secret:
            self.clients["Coinbase"] = CoinbaseClient(api_key, api_secret)
            print("✓ Coinbase connected")
            return True
        else:
            print("○ Coinbase: API keys not configured")
            return False
    
    def connect_kraken(self) -> bool:
        """Initialize Kraken connection."""
        api_key = os.getenv("KRAKEN_API_KEY")
        api_secret = os.getenv("KRAKEN_API_SECRET")
        
        if api_key and api_secret:
            self.clients["Kraken"] = KrakenClient(api_key, api_secret)
            # Test connection
            if self.clients["Kraken"].get_server_time():
                print("✓ Kraken connected")
                return True
            else:
                print("✗ Kraken: Connection failed")
                del self.clients["Kraken"]
                return False
        else:
            print("○ Kraken: API keys not configured")
            return False
    
    def connect_cryptocom(self) -> bool:
        """Initialize Crypto.com connection."""
        api_key = os.getenv("CRYPTOCOM_API_KEY")
        api_secret = os.getenv("CRYPTOCOM_API_SECRET")
        
        if api_key and api_secret:
            self.clients["Crypto.com"] = CryptoComClient(api_key, api_secret)
            print("✓ Crypto.com connected")
            return True
        else:
            print("○ Crypto.com: API keys not configured")
            return False
    
    def connect_gemini(self) -> bool:
        """Initialize Gemini connection."""
        api_key = os.getenv("GEMINI_API_KEY")
        api_secret = os.getenv("GEMINI_API_SECRET")
        
        if api_key and api_secret:
            self.clients["Gemini"] = GeminiClient(api_key, api_secret)
            print("✓ Gemini connected")
            return True
        else:
            print("○ Gemini: API keys not configured")
            return False
    
    def connect_all(self, exchanges: list = None) -> int:
        """Connect to all configured exchanges or specified subset."""
        print("\n🔗 Connecting to exchanges...")
        print("-" * 40)
        
        connected = 0
        
        if exchanges is None or "coinbase" in exchanges:
            if self.connect_coinbase():
                connected += 1
        
        if exchanges is None or "kraken" in exchanges:
            if self.connect_kraken():
                connected += 1
        
        if exchanges is None or "cryptocom" in exchanges:
            if self.connect_cryptocom():
                connected += 1
        
        if exchanges is None or "gemini" in exchanges:
            if self.connect_gemini():
                connected += 1
        
        print("-" * 40)
        print(f"Connected to {connected} exchange(s)\n")
        return connected
    
    def fetch_holdings(self, exchange_name: str, client) -> dict:
        """Fetch holdings from a specific exchange."""
        holdings = {}
        
        try:
            accounts = client.get_accounts()
            
            for account in accounts:
                currency = account.get("currency", "UNKNOWN")
                
                # Skip fiat (we'll handle stablecoins)
                if currency in ["USD", "EUR", "GBP", "ZUSD", "ZEUR"]:
                    continue
                
                # Detect staked assets
                is_staked = account.get("is_staked", False)
                if "(Staked)" in currency:
                    is_staked = True
                
                # Get balance
                balance_info = account.get("available_balance", {})
                balance = float(balance_info.get("value", 0))
                
                if balance <= 0:
                    continue
                
                # Normalize currency name for pricing
                price_currency = currency.replace(" (Staked)", "")
                
                # Get current price
                price = client.get_spot_price(price_currency, "USD")
                
                # If no USD price, try USDT (common for some exchanges)
                if price is None and hasattr(client, 'get_spot_price'):
                    price = client.get_spot_price(price_currency, "USDT")
                
                # Stablecoins are ~$1
                if price_currency in ["USDC", "USDT"]:
                    price = 1.0
                
                usd_value = balance * price if price else 0
                
                # Get price changes if available
                changes = None
                if hasattr(client, 'get_price_changes') and price:
                    changes = client.get_price_changes(price_currency, "USD")
                
                holdings[currency] = {
                    "balance": balance,
                    "price": price,
                    "usd_value": usd_value,
                    "changes": changes,
                    "is_staked": is_staked,
                    "apy": account.get("apy"),
                    "accrued_interest": account.get("accrued_interest")
                }
                
        except Exception as e:
            print(f"Error fetching from {exchange_name}: {e}")
        
        return holdings
    
    def fetch_all_holdings(self):
        """Fetch holdings from all connected exchanges."""
        print("📊 Fetching portfolio data...")
        print("-" * 40)
        
        self.holdings_by_exchange = {}
        self.aggregated_holdings = {}
        
        for name, client in self.clients.items():
            print(f"  Fetching from {name}...")
            holdings = self.fetch_holdings(name, client)
            self.holdings_by_exchange[name] = holdings
            
            # Aggregate holdings across exchanges
            for currency, data in holdings.items():
                # Normalize currency name for aggregation (remove staking indicators)
                base_currency = currency.replace(" (Staked)", "")
                
                if base_currency not in self.aggregated_holdings:
                    self.aggregated_holdings[base_currency] = {
                        "total_balance": 0,
                        "staked_balance": 0,
                        "liquid_balance": 0,
                        "price": data["price"],
                        "total_usd_value": 0,
                        "staked_usd_value": 0,
                        "changes": data["changes"],
                        "exchanges": {},
                        "staking_info": []
                    }
                
                self.aggregated_holdings[base_currency]["total_balance"] += data["balance"]
                self.aggregated_holdings[base_currency]["total_usd_value"] += data["usd_value"]
                self.aggregated_holdings[base_currency]["exchanges"][name] = data["balance"]
                
                # Track staking separately
                if data.get("is_staked"):
                    self.aggregated_holdings[base_currency]["staked_balance"] += data["balance"]
                    self.aggregated_holdings[base_currency]["staked_usd_value"] += data["usd_value"]
                    self.aggregated_holdings[base_currency]["staking_info"].append({
                        "exchange": name,
                        "balance": data["balance"],
                        "apy": data.get("apy"),
                        "accrued": data.get("accrued_interest")
                    })
                else:
                    self.aggregated_holdings[base_currency]["liquid_balance"] += data["balance"]
        
        print("-" * 40)
    
    def display_exchange_breakdown(self):
        """Display holdings by exchange."""
        if not self.holdings_by_exchange:
            print("No holdings data available.")
            return
        
        for exchange_name, holdings in self.holdings_by_exchange.items():
            if not holdings:
                continue
            
            print(f"\n{'='*60}")
            print(f"📈 {exchange_name} Holdings")
            print(f"{'='*60}")
            
            total_value = sum(h["usd_value"] for h in holdings.values())
            
            table_data = []
            for currency, data in sorted(holdings.items(), key=lambda x: x[1]["usd_value"], reverse=True):
                row = [
                    currency,
                    f"{data['balance']:.8f}".rstrip('0').rstrip('.'),
                    f"${data['price']:,.2f}" if data['price'] else "N/A",
                    f"${data['usd_value']:,.2f}",
                    f"{(data['usd_value']/total_value*100):.1f}%" if total_value > 0 else "0%"
                ]
                
                # Add 24h change if available
                if data["changes"] and data["changes"].get("change_24h") is not None:
                    change = data["changes"]["change_24h"]
                    emoji = "🟢" if change >= 0 else "🔴"
                    row.append(f"{emoji} {change:+.2f}%")
                else:
                    row.append("-")
                
                table_data.append(row)
            
            headers = ["Asset", "Balance", "Price", "Value", "% of Portfolio", "24h"]
            print(tabulate(table_data, headers=headers, tablefmt="simple"))
            print(f"\n💰 {exchange_name} Total: ${total_value:,.2f}")
    
    def display_aggregated_portfolio(self):
        """Display combined holdings across all exchanges."""
        if not self.aggregated_holdings:
            print("No holdings data available.")
            return
        
        print(f"\n{'='*70}")
        print(f"🌐 COMBINED PORTFOLIO - All Exchanges")
        print(f"{'='*70}")
        
        total_value = sum(h["total_usd_value"] for h in self.aggregated_holdings.values())
        
        table_data = []
        for currency, data in sorted(
            self.aggregated_holdings.items(), 
            key=lambda x: x[1]["total_usd_value"], 
            reverse=True
        ):
            # Build exchange distribution string
            exchange_dist = ", ".join([
                f"{ex}: {bal:.6f}".rstrip('0').rstrip('.')
                for ex, bal in data["exchanges"].items()
            ])
            
            row = [
                currency,
                f"{data['total_balance']:.8f}".rstrip('0').rstrip('.'),
                f"${data['price']:,.2f}" if data['price'] else "N/A",
                f"${data['total_usd_value']:,.2f}",
                f"{(data['total_usd_value']/total_value*100):.1f}%" if total_value > 0 else "0%",
            ]
            
            # Add performance columns
            changes = data["changes"]
            if changes:
                for period in ["change_24h", "change_7d", "change_30d"]:
                    if changes.get(period) is not None:
                        change = changes[period]
                        emoji = "🟢" if change >= 0 else "🔴"
                        row.append(f"{emoji} {change:+.1f}%")
                    else:
                        row.append("-")
            else:
                row.extend(["-", "-", "-"])
            
            table_data.append(row)
        
        headers = ["Asset", "Total Balance", "Price", "Total Value", "% Port", "24h", "7d", "30d"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
        
        print(f"\n{'='*70}")
        print(f"💎 TOTAL PORTFOLIO VALUE: ${total_value:,.2f}")
        print(f"{'='*70}")
        
        # Show exchange totals
        print("\n📊 Value by Exchange:")
        for exchange_name, holdings in self.holdings_by_exchange.items():
            exchange_total = sum(h["usd_value"] for h in holdings.values())
            pct = (exchange_total / total_value * 100) if total_value > 0 else 0
            print(f"  • {exchange_name}: ${exchange_total:,.2f} ({pct:.1f}%)")
    
    def display_performance_alerts(self):
        """Display underperformers and top performers."""
        if not self.aggregated_holdings:
            return
        
        underperformers = []
        top_performers = []
        
        for currency, data in self.aggregated_holdings.items():
            if data["changes"] and data["changes"].get("change_30d") is not None:
                change_30d = data["changes"]["change_30d"]
                if change_30d <= -10:
                    underperformers.append((currency, change_30d, data["total_usd_value"]))
                elif change_30d >= 10:
                    top_performers.append((currency, change_30d, data["total_usd_value"]))
        
        if underperformers:
            print(f"\n⚠️  UNDERPERFORMERS (>10% down in 30 days)")
            print("-" * 50)
            for currency, change, value in sorted(underperformers, key=lambda x: x[1]):
                print(f"  🔴 {currency}: {change:+.1f}% (${value:,.2f})")
        
        if top_performers:
            print(f"\n🚀 TOP PERFORMERS (>10% up in 30 days)")
            print("-" * 50)
            for currency, change, value in sorted(top_performers, key=lambda x: x[1], reverse=True):
                print(f"  🟢 {currency}: {change:+.1f}% (${value:,.2f})")
    
    def display_asset_distribution(self):
        """Show where each asset is held across exchanges."""
        if not self.aggregated_holdings:
            return
        
        print(f"\n📍 ASSET DISTRIBUTION ACROSS EXCHANGES")
        print("-" * 60)
        
        for currency, data in sorted(
            self.aggregated_holdings.items(),
            key=lambda x: x[1]["total_usd_value"],
            reverse=True
        ):
            if len(data["exchanges"]) > 1:
                print(f"\n{currency} (${data['total_usd_value']:,.2f} total):")
                for exchange, balance in data["exchanges"].items():
                    pct = (balance / data["total_balance"] * 100)
                    print(f"  • {exchange}: {balance:.8f}".rstrip('0').rstrip('.') + f" ({pct:.1f}%)")
    
    def display_staking_summary(self):
        """Show staking positions across all exchanges."""
        if not self.aggregated_holdings:
            return
        
        # Collect all staking positions
        staking_positions = []
        total_staked_usd = 0
        
        for currency, data in self.aggregated_holdings.items():
            if data.get("staked_balance", 0) > 0:
                total_staked_usd += data.get("staked_usd_value", 0)
                for stake_info in data.get("staking_info", []):
                    staking_positions.append({
                        "currency": currency,
                        "exchange": stake_info["exchange"],
                        "balance": stake_info["balance"],
                        "usd_value": stake_info["balance"] * (data["price"] or 0),
                        "apy": stake_info.get("apy"),
                        "accrued": stake_info.get("accrued")
                    })
        
        if not staking_positions:
            return
        
        print(f"\n{'='*70}")
        print(f"🔒 STAKING SUMMARY")
        print(f"{'='*70}")
        
        table_data = []
        for pos in sorted(staking_positions, key=lambda x: x["usd_value"], reverse=True):
            row = [
                pos["currency"],
                pos["exchange"],
                f"{pos['balance']:.8f}".rstrip('0').rstrip('.'),
                f"${pos['usd_value']:,.2f}",
            ]
            
            # APY
            if pos.get("apy"):
                row.append(f"{pos['apy']:.2f}%")
            else:
                row.append("-")
            
            # Accrued interest
            if pos.get("accrued"):
                row.append(f"{pos['accrued']:.8f}".rstrip('0').rstrip('.'))
            else:
                row.append("-")
            
            table_data.append(row)
        
        headers = ["Asset", "Exchange", "Staked Amount", "Value", "APY", "Accrued"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
        
        print(f"\n💎 Total Staked Value: ${total_staked_usd:,.2f}")
    
    def run_analysis(self, show_breakdown: bool = True, show_distribution: bool = False, show_staking: bool = True):
        """Run the full portfolio analysis."""
        if not self.clients:
            print("❌ No exchanges connected. Please configure API keys in .env file.")
            return
        
        self.fetch_all_holdings()
        
        if show_breakdown:
            self.display_exchange_breakdown()
        
        self.display_aggregated_portfolio()
        self.display_performance_alerts()
        
        if show_distribution:
            self.display_asset_distribution()
        
        if show_staking:
            self.display_staking_summary()


def main():
    parser = argparse.ArgumentParser(description="Multi-Exchange Crypto Portfolio Analyzer")
    parser.add_argument(
        "--exchanges", "-e",
        nargs="+",
        choices=["coinbase", "kraken", "cryptocom", "gemini"],
        help="Specific exchanges to analyze (default: all configured)"
    )
    parser.add_argument(
        "--summary-only", "-s",
        action="store_true",
        help="Show only combined portfolio summary"
    )
    parser.add_argument(
        "--distribution", "-d",
        action="store_true",
        help="Show asset distribution across exchanges"
    )
    parser.add_argument(
        "--no-staking",
        action="store_true",
        help="Hide staking summary"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔐 MULTI-EXCHANGE CRYPTO PORTFOLIO ANALYZER")
    print("=" * 70)
    
    analyzer = MultiExchangeAnalyzer()
    connected = analyzer.connect_all(args.exchanges)
    
    if connected > 0:
        analyzer.run_analysis(
            show_breakdown=not args.summary_only,
            show_distribution=args.distribution,
            show_staking=not args.no_staking
        )
    else:
        print("\n❌ No exchanges connected.")
        print("Please configure at least one exchange in your .env file:")
        print("  - COINBASE_API_KEY / COINBASE_API_SECRET")
        print("  - KRAKEN_API_KEY / KRAKEN_API_SECRET")  
        print("  - CRYPTOCOM_API_KEY / CRYPTOCOM_API_SECRET")
        print("  - GEMINI_API_KEY / GEMINI_API_SECRET")


if __name__ == "__main__":
    main()
