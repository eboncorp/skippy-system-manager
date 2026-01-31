"""
Cross-Exchange Arbitrage Detector
Monitors price differences across exchanges and alerts on opportunities.

Usage:
    python arbitrage_detector.py scan BTC ETH SOL
    python arbitrage_detector.py monitor BTC ETH --threshold 1.0
    python arbitrage_detector.py history
"""

import os
import time
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from tabulate import tabulate

# Import exchange clients
from exchanges import CoinbaseClient, KrakenClient, CryptoComClient, GeminiClient


class ArbitrageDetector:
    """Detects and monitors cross-exchange arbitrage opportunities."""
    
    EXCHANGE_NAMES = {
        "coinbase": "Coinbase",
        "kraken": "Kraken", 
        "cryptocom": "Crypto.com",
        "gemini": "Gemini"
    }
    
    # Estimated fees per exchange (maker/taker average)
    EXCHANGE_FEES = {
        "coinbase": 0.006,   # 0.6% average
        "kraken": 0.0026,    # 0.26% average
        "cryptocom": 0.004,  # 0.4% average
        "gemini": 0.004,     # 0.4% average (ActiveTrader)
    }
    
    # Estimated withdrawal fees in USD (varies by asset)
    WITHDRAWAL_FEES = {
        "coinbase": 0,       # Free for most
        "kraken": 1,         # Varies
        "cryptocom": 0,      # Often free
        "gemini": 0,         # 10 free/month
    }
    
    def __init__(self):
        load_dotenv()
        self.clients: Dict[str, object] = {}
        self.history: List[dict] = []
        self._history_file = "arbitrage_history.json"
        self._load_history()
        
    def _load_history(self):
        """Load opportunity history from file."""
        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = []
    
    def _save_history(self):
        """Save opportunity history to file."""
        # Keep last 1000 entries
        self.history = self.history[-1000:]
        with open(self._history_file, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)
    
    def connect_all(self) -> int:
        """Connect to all configured exchanges."""
        connected = 0
        
        # Coinbase
        key = os.getenv("COINBASE_API_KEY")
        secret = os.getenv("COINBASE_API_SECRET")
        if key and secret:
            self.clients["coinbase"] = CoinbaseClient(key, secret)
            connected += 1
        
        # Kraken
        key = os.getenv("KRAKEN_API_KEY")
        secret = os.getenv("KRAKEN_API_SECRET")
        if key and secret:
            client = KrakenClient(key, secret)
            if client.get_server_time():
                self.clients["kraken"] = client
                connected += 1
        
        # Crypto.com
        key = os.getenv("CRYPTOCOM_API_KEY")
        secret = os.getenv("CRYPTOCOM_API_SECRET")
        if key and secret:
            self.clients["cryptocom"] = CryptoComClient(key, secret)
            connected += 1
        
        # Gemini
        key = os.getenv("GEMINI_API_KEY")
        secret = os.getenv("GEMINI_API_SECRET")
        if key and secret:
            self.clients["gemini"] = GeminiClient(key, secret)
            connected += 1
        
        return connected
    
    def get_prices(self, assets: List[str]) -> Dict[str, Dict[str, float]]:
        """Get prices for assets across all connected exchanges."""
        prices = {asset: {} for asset in assets}
        
        for exchange, client in self.clients.items():
            for asset in assets:
                try:
                    price = client.get_spot_price(asset, "USD")
                    if price:
                        prices[asset][exchange] = price
                except Exception:
                    pass
        
        return prices
    
    def calculate_arbitrage(
        self, 
        asset: str, 
        prices: Dict[str, float],
        trade_amount_usd: float = 1000,
        include_fees: bool = True
    ) -> Optional[dict]:
        """
        Calculate arbitrage opportunity for an asset.
        
        Args:
            asset: Asset symbol
            prices: Dict of exchange -> price
            trade_amount_usd: Amount to trade in USD
            include_fees: Whether to account for trading fees
        
        Returns:
            Arbitrage opportunity details or None
        """
        if len(prices) < 2:
            return None
        
        # Find min and max prices
        buy_exchange = min(prices, key=prices.get)
        sell_exchange = max(prices, key=prices.get)
        
        buy_price = prices[buy_exchange]
        sell_price = prices[sell_exchange]
        
        # Calculate raw spread
        raw_spread_pct = ((sell_price - buy_price) / buy_price) * 100
        
        # Calculate profit
        units_bought = trade_amount_usd / buy_price
        gross_revenue = units_bought * sell_price
        gross_profit = gross_revenue - trade_amount_usd
        
        if include_fees:
            # Subtract trading fees
            buy_fee = trade_amount_usd * self.EXCHANGE_FEES.get(buy_exchange, 0.005)
            sell_fee = gross_revenue * self.EXCHANGE_FEES.get(sell_exchange, 0.005)
            
            # Withdrawal fee (moving asset from buy to sell exchange)
            withdrawal_fee = self.WITHDRAWAL_FEES.get(buy_exchange, 1)
            
            total_fees = buy_fee + sell_fee + withdrawal_fee
            net_profit = gross_profit - total_fees
            net_spread_pct = (net_profit / trade_amount_usd) * 100
        else:
            total_fees = 0
            net_profit = gross_profit
            net_spread_pct = raw_spread_pct
        
        return {
            "asset": asset,
            "timestamp": datetime.now().isoformat(),
            "buy_exchange": buy_exchange,
            "buy_price": buy_price,
            "sell_exchange": sell_exchange,
            "sell_price": sell_price,
            "raw_spread_pct": raw_spread_pct,
            "net_spread_pct": net_spread_pct,
            "trade_amount": trade_amount_usd,
            "gross_profit": gross_profit,
            "total_fees": total_fees,
            "net_profit": net_profit,
            "profitable": net_profit > 0,
            "all_prices": prices
        }
    
    def scan(
        self, 
        assets: List[str], 
        min_spread: float = 0.5,
        trade_amount: float = 1000,
        include_fees: bool = True
    ) -> List[dict]:
        """
        Scan for arbitrage opportunities.
        
        Args:
            assets: List of assets to scan
            min_spread: Minimum spread percentage to report
            trade_amount: USD amount for profit calculation
            include_fees: Whether to account for fees
        
        Returns:
            List of opportunities
        """
        prices = self.get_prices(assets)
        opportunities = []
        
        for asset in assets:
            asset_prices = prices.get(asset, {})
            opp = self.calculate_arbitrage(asset, asset_prices, trade_amount, include_fees)
            
            if opp and opp["raw_spread_pct"] >= min_spread:
                opportunities.append(opp)
                self.history.append(opp)
        
        self._save_history()
        
        return sorted(opportunities, key=lambda x: x["net_spread_pct"], reverse=True)
    
    def display_scan_results(self, opportunities: List[dict], show_all_prices: bool = False):
        """Display scan results in formatted table."""
        if not opportunities:
            print("\n📊 No significant arbitrage opportunities found.")
            return
        
        print(f"\n{'='*80}")
        print(f"🔄 ARBITRAGE OPPORTUNITIES ({len(opportunities)} found)")
        print(f"{'='*80}")
        
        for opp in opportunities:
            profit_emoji = "✅" if opp["profitable"] else "⚠️"
            
            print(f"\n{profit_emoji} {opp['asset']}")
            print(f"   Raw Spread:  {opp['raw_spread_pct']:.2f}%")
            print(f"   Net Spread:  {opp['net_spread_pct']:.2f}% (after fees)")
            print(f"   Buy on:      {self.EXCHANGE_NAMES.get(opp['buy_exchange'], opp['buy_exchange'])} @ ${opp['buy_price']:,.2f}")
            print(f"   Sell on:     {self.EXCHANGE_NAMES.get(opp['sell_exchange'], opp['sell_exchange'])} @ ${opp['sell_price']:,.2f}")
            print(f"   Trade Size:  ${opp['trade_amount']:,.2f}")
            print(f"   Est Profit:  ${opp['net_profit']:,.2f} (fees: ${opp['total_fees']:,.2f})")
            
            if show_all_prices:
                print(f"   All Prices:")
                for ex, price in sorted(opp['all_prices'].items(), key=lambda x: x[1]):
                    print(f"      {self.EXCHANGE_NAMES.get(ex, ex)}: ${price:,.2f}")
    
    def monitor(
        self, 
        assets: List[str],
        min_spread: float = 1.0,
        interval_seconds: int = 30,
        alert_callback=None
    ):
        """
        Continuously monitor for arbitrage opportunities.
        
        Args:
            assets: Assets to monitor
            min_spread: Minimum spread to alert on
            interval_seconds: Seconds between scans
            alert_callback: Function to call when opportunity found
        """
        print(f"\n🔍 Starting arbitrage monitor...")
        print(f"   Assets: {', '.join(assets)}")
        print(f"   Threshold: {min_spread}% spread")
        print(f"   Interval: {interval_seconds}s")
        print(f"   Press Ctrl+C to stop\n")
        
        scan_count = 0
        alert_count = 0
        
        try:
            while True:
                scan_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                opportunities = self.scan(assets, min_spread)
                
                if opportunities:
                    alert_count += len(opportunities)
                    print(f"\n🚨 [{timestamp}] ARBITRAGE ALERT!")
                    self.display_scan_results(opportunities)
                    
                    if alert_callback:
                        for opp in opportunities:
                            alert_callback(opp)
                else:
                    # Print status dot
                    print(f"[{timestamp}] Scan #{scan_count} - No opportunities (threshold: {min_spread}%)", end="\r")
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print(f"\n\n📊 Monitor stopped.")
            print(f"   Total scans: {scan_count}")
            print(f"   Alerts triggered: {alert_count}")
    
    def display_history(self, limit: int = 20):
        """Display recent arbitrage opportunity history."""
        if not self.history:
            print("\n📜 No arbitrage history found.")
            return
        
        print(f"\n{'='*80}")
        print(f"📜 ARBITRAGE HISTORY (last {limit} opportunities)")
        print(f"{'='*80}")
        
        table_data = []
        for opp in self.history[-limit:]:
            table_data.append([
                opp.get("timestamp", "N/A")[:19],
                opp.get("asset", "N/A"),
                f"{opp.get('raw_spread_pct', 0):.2f}%",
                f"{opp.get('net_spread_pct', 0):.2f}%",
                f"{self.EXCHANGE_NAMES.get(opp.get('buy_exchange', ''), opp.get('buy_exchange', ''))} → {self.EXCHANGE_NAMES.get(opp.get('sell_exchange', ''), opp.get('sell_exchange', ''))}",
                f"${opp.get('net_profit', 0):,.2f}"
            ])
        
        headers = ["Time", "Asset", "Raw %", "Net %", "Route", "Est Profit"]
        print(tabulate(table_data, headers=headers, tablefmt="simple"))
    
    def get_statistics(self) -> dict:
        """Get statistics from arbitrage history."""
        if not self.history:
            return {}
        
        profitable = [o for o in self.history if o.get("profitable", False)]
        
        stats = {
            "total_opportunities": len(self.history),
            "profitable_opportunities": len(profitable),
            "avg_raw_spread": sum(o.get("raw_spread_pct", 0) for o in self.history) / len(self.history),
            "avg_net_spread": sum(o.get("net_spread_pct", 0) for o in self.history) / len(self.history),
            "max_spread": max(o.get("raw_spread_pct", 0) for o in self.history),
            "total_potential_profit": sum(o.get("net_profit", 0) for o in profitable),
            "most_common_buy": {},
            "most_common_sell": {},
            "most_common_asset": {}
        }
        
        # Count occurrences
        for opp in self.history:
            buy_ex = opp.get("buy_exchange", "unknown")
            sell_ex = opp.get("sell_exchange", "unknown")
            asset = opp.get("asset", "unknown")
            
            stats["most_common_buy"][buy_ex] = stats["most_common_buy"].get(buy_ex, 0) + 1
            stats["most_common_sell"][sell_ex] = stats["most_common_sell"].get(sell_ex, 0) + 1
            stats["most_common_asset"][asset] = stats["most_common_asset"].get(asset, 0) + 1
        
        return stats


def main():
    parser = argparse.ArgumentParser(description="Cross-Exchange Arbitrage Detector")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan for arbitrage opportunities")
    scan_parser.add_argument("assets", nargs="+", help="Assets to scan (e.g., BTC ETH SOL)")
    scan_parser.add_argument("-m", "--min-spread", type=float, default=0.5, help="Minimum spread %% (default: 0.5)")
    scan_parser.add_argument("-a", "--amount", type=float, default=1000, help="Trade amount for profit calc (default: $1000)")
    scan_parser.add_argument("--no-fees", action="store_true", help="Don't include fees in calculation")
    scan_parser.add_argument("-v", "--verbose", action="store_true", help="Show all exchange prices")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Continuously monitor for opportunities")
    monitor_parser.add_argument("assets", nargs="+", help="Assets to monitor")
    monitor_parser.add_argument("-m", "--min-spread", type=float, default=1.0, help="Alert threshold %% (default: 1.0)")
    monitor_parser.add_argument("-i", "--interval", type=int, default=30, help="Scan interval seconds (default: 30)")
    
    # History command
    history_parser = subparsers.add_parser("history", help="View arbitrage history")
    history_parser.add_argument("-n", "--limit", type=int, default=20, help="Number of entries to show")
    history_parser.add_argument("-s", "--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    detector = ArbitrageDetector()
    connected = detector.connect_all()
    
    if connected < 2:
        print(f"⚠️  Only {connected} exchange(s) connected. Need at least 2 for arbitrage detection.")
        print("Configure more exchanges in .env file.")
        if connected == 0:
            return
    
    print(f"✓ Connected to {connected} exchanges")
    
    if args.command == "scan":
        opportunities = detector.scan(
            args.assets, 
            args.min_spread, 
            args.amount,
            include_fees=not args.no_fees
        )
        detector.display_scan_results(opportunities, args.verbose)
    
    elif args.command == "monitor":
        detector.monitor(args.assets, args.min_spread, args.interval)
    
    elif args.command == "history":
        if args.stats:
            stats = detector.get_statistics()
            print(f"\n📊 ARBITRAGE STATISTICS")
            print(f"   Total opportunities: {stats.get('total_opportunities', 0)}")
            print(f"   Profitable: {stats.get('profitable_opportunities', 0)}")
            print(f"   Avg raw spread: {stats.get('avg_raw_spread', 0):.2f}%")
            print(f"   Max spread seen: {stats.get('max_spread', 0):.2f}%")
            print(f"   Total potential profit: ${stats.get('total_potential_profit', 0):,.2f}")
        else:
            detector.display_history(args.limit)


if __name__ == "__main__":
    main()
