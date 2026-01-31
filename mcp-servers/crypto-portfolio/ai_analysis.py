"""
AI Analysis Module
Outputs structured data and reports optimized for Claude Code analysis.

This module provides JSON-based outputs that Claude Code can easily parse
and analyze, plus generates markdown reports for human-readable summaries.
"""

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from pathlib import Path
from dotenv import load_dotenv


class PortfolioAnalyzer:
    """Generate analysis reports for Claude Code."""
    
    def __init__(self):
        load_dotenv()
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)
        self.clients = {}
        self._init_clients()
    
    def _init_clients(self):
        """Initialize available exchange clients."""
        from exchanges import CoinbaseClient, KrakenClient, CryptoComClient, GeminiClient

        # Coinbase
        if os.getenv("COINBASE_API_KEY"):
            self.clients["coinbase"] = CoinbaseClient(
                os.getenv("COINBASE_API_KEY"),
                os.getenv("COINBASE_API_SECRET")
            )

        # Kraken
        if os.getenv("KRAKEN_API_KEY"):
            self.clients["kraken"] = KrakenClient(
                os.getenv("KRAKEN_API_KEY"),
                os.getenv("KRAKEN_API_SECRET")
            )

        # Crypto.com
        if os.getenv("CRYPTOCOM_API_KEY"):
            self.clients["cryptocom"] = CryptoComClient(
                os.getenv("CRYPTOCOM_API_KEY"),
                os.getenv("CRYPTOCOM_API_SECRET")
            )

        # Gemini
        if os.getenv("GEMINI_API_KEY"):
            self.clients["gemini"] = GeminiClient(
                os.getenv("GEMINI_API_KEY"),
                os.getenv("GEMINI_API_SECRET")
            )
    
    def get_full_snapshot(self) -> Dict[str, Any]:
        """
        Get complete portfolio snapshot as structured JSON.
        This is the primary method for Claude Code to get data.
        """
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "exchanges": {},
            "holdings": {},
            "totals": {
                "portfolio_value_usd": 0,
                "by_exchange": {},
                "by_asset": {},
                "staked_value_usd": 0
            },
            "performance": {},
            "alerts": []
        }
        
        for exchange_name, client in self.clients.items():
            try:
                accounts = client.get_accounts()
                exchange_total = 0
                exchange_holdings = []
                
                for account in accounts:
                    currency = account.get("currency", "UNKNOWN")
                    
                    # Skip fiat
                    if currency in ["USD", "EUR", "GBP", "ZUSD", "ZEUR"]:
                        continue
                    
                    # Get balance
                    balance_info = account.get("available_balance", {})
                    balance = float(balance_info.get("value", 0))
                    
                    if balance <= 0:
                        continue
                    
                    # Normalize staked asset names
                    base_currency = currency.replace(" (Staked)", "").replace(".S", "")
                    is_staked = account.get("is_staked", False) or "(Staked)" in currency or ".S" in currency
                    
                    # Get price
                    price = None
                    if hasattr(client, 'get_spot_price'):
                        price = client.get_spot_price(base_currency, "USD")
                    
                    # Stablecoins
                    if base_currency in ["USDC", "USDT", "DAI"]:
                        price = 1.0
                    
                    usd_value = balance * price if price else 0
                    exchange_total += usd_value
                    
                    # Get performance
                    changes = None
                    if hasattr(client, 'get_price_changes') and price:
                        changes = client.get_price_changes(base_currency, "USD")
                    
                    holding = {
                        "asset": base_currency,
                        "balance": balance,
                        "price_usd": price,
                        "value_usd": usd_value,
                        "is_staked": is_staked,
                        "exchange": exchange_name,
                        "performance": {
                            "change_24h": changes.get("change_24h") if changes else None,
                            "change_7d": changes.get("change_7d") if changes else None,
                            "change_30d": changes.get("change_30d") if changes else None
                        } if changes else None
                    }
                    
                    exchange_holdings.append(holding)
                    
                    # Aggregate by asset
                    if base_currency not in snapshot["holdings"]:
                        snapshot["holdings"][base_currency] = {
                            "total_balance": 0,
                            "total_value_usd": 0,
                            "price_usd": price,
                            "staked_balance": 0,
                            "liquid_balance": 0,
                            "exchanges": {},
                            "performance": holding["performance"]
                        }
                    
                    snapshot["holdings"][base_currency]["total_balance"] += balance
                    snapshot["holdings"][base_currency]["total_value_usd"] += usd_value
                    snapshot["holdings"][base_currency]["exchanges"][exchange_name] = balance
                    
                    if is_staked:
                        snapshot["holdings"][base_currency]["staked_balance"] += balance
                        snapshot["totals"]["staked_value_usd"] += usd_value
                    else:
                        snapshot["holdings"][base_currency]["liquid_balance"] += balance
                
                snapshot["exchanges"][exchange_name] = {
                    "connected": True,
                    "holdings": exchange_holdings,
                    "total_value_usd": exchange_total
                }
                
                snapshot["totals"]["portfolio_value_usd"] += exchange_total
                snapshot["totals"]["by_exchange"][exchange_name] = exchange_total
                
            except Exception as e:
                snapshot["exchanges"][exchange_name] = {
                    "connected": False,
                    "error": str(e)
                }
        
        # Calculate asset totals
        for asset, data in snapshot["holdings"].items():
            snapshot["totals"]["by_asset"][asset] = data["total_value_usd"]
        
        # Generate alerts
        snapshot["alerts"] = self._generate_alerts(snapshot)
        
        return snapshot
    
    def _generate_alerts(self, snapshot: Dict) -> List[Dict]:
        """Generate alerts based on portfolio data."""
        alerts = []
        
        for asset, data in snapshot["holdings"].items():
            perf = data.get("performance")
            if not perf:
                continue
            
            # Big movers (24h)
            if perf.get("change_24h") is not None:
                change = perf["change_24h"]
                if change <= -10:
                    alerts.append({
                        "type": "price_drop",
                        "severity": "high" if change <= -15 else "medium",
                        "asset": asset,
                        "message": f"{asset} down {change:.1f}% in 24h",
                        "value_at_risk": data["total_value_usd"]
                    })
                elif change >= 15:
                    alerts.append({
                        "type": "price_surge",
                        "severity": "info",
                        "asset": asset,
                        "message": f"{asset} up {change:.1f}% in 24h"
                    })
            
            # 30d underperformers
            if perf.get("change_30d") is not None and perf["change_30d"] <= -20:
                alerts.append({
                    "type": "underperformer",
                    "severity": "medium",
                    "asset": asset,
                    "message": f"{asset} down {perf['change_30d']:.1f}% in 30 days",
                    "value_usd": data["total_value_usd"]
                })
        
        # Concentration risk
        total = snapshot["totals"]["portfolio_value_usd"]
        if total > 0:
            for asset, data in snapshot["holdings"].items():
                pct = (data["total_value_usd"] / total) * 100
                if pct > 50:
                    alerts.append({
                        "type": "concentration_risk",
                        "severity": "medium",
                        "asset": asset,
                        "message": f"{asset} is {pct:.1f}% of portfolio",
                        "recommendation": "Consider diversifying"
                    })
        
        return alerts
    
    def save_snapshot_json(self, filepath: str = None) -> str:
        """Save snapshot as JSON file."""
        snapshot = self.get_full_snapshot()
        
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.output_dir / f"portfolio_snapshot_{timestamp}.json"
        
        Path(filepath).write_text(json.dumps(snapshot, indent=2, default=str))
        return str(filepath)
    
    def generate_markdown_report(self, filepath: str = None) -> str:
        """
        Generate a markdown report for human reading.
        Claude Code can also read this for context.
        """
        snapshot = self.get_full_snapshot()
        
        lines = [
            f"# Portfolio Report",
            f"",
            f"**Generated:** {snapshot['timestamp']}",
            f"",
            f"## Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Portfolio Value | ${snapshot['totals']['portfolio_value_usd']:,.2f} |",
            f"| Staked Value | ${snapshot['totals']['staked_value_usd']:,.2f} |",
            f"| Assets Tracked | {len(snapshot['holdings'])} |",
            f"| Exchanges Connected | {len([e for e in snapshot['exchanges'].values() if e.get('connected')])} |",
            f"",
            f"## Holdings by Asset",
            f"",
            f"| Asset | Balance | Price | Value | 24h | 7d | 30d |",
            f"|-------|---------|-------|-------|-----|----|----|",
        ]
        
        # Sort by value
        sorted_holdings = sorted(
            snapshot["holdings"].items(),
            key=lambda x: x[1]["total_value_usd"],
            reverse=True
        )
        
        for asset, data in sorted_holdings:
            perf = data.get("performance") or {}
            
            def fmt_change(val):
                if val is None:
                    return "-"
                return f"{val:+.1f}%"
            
            lines.append(
                f"| {asset} | {data['total_balance']:.6f} | "
                f"${data['price_usd']:,.2f} | ${data['total_value_usd']:,.2f} | "
                f"{fmt_change(perf.get('change_24h'))} | "
                f"{fmt_change(perf.get('change_7d'))} | "
                f"{fmt_change(perf.get('change_30d'))} |"
            )
        
        lines.extend([
            f"",
            f"## Exchange Breakdown",
            f"",
            f"| Exchange | Value | % of Portfolio |",
            f"|----------|-------|----------------|",
        ])
        
        total = snapshot["totals"]["portfolio_value_usd"]
        for exchange, value in snapshot["totals"]["by_exchange"].items():
            pct = (value / total * 100) if total > 0 else 0
            lines.append(f"| {exchange.title()} | ${value:,.2f} | {pct:.1f}% |")
        
        # Alerts section
        if snapshot["alerts"]:
            lines.extend([
                f"",
                f"## Alerts",
                f"",
            ])
            for alert in snapshot["alerts"]:
                severity_emoji = {"high": "🔴", "medium": "🟡", "info": "🟢"}.get(alert["severity"], "⚪")
                lines.append(f"- {severity_emoji} **{alert['type']}**: {alert['message']}")
        
        # Recommendations
        lines.extend([
            f"",
            f"## Analysis Notes",
            f"",
            f"*This section is for Claude Code to add analysis insights.*",
            f"",
        ])
        
        report = "\n".join(lines)
        
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.output_dir / f"portfolio_report_{timestamp}.md"
        
        Path(filepath).write_text(report)
        return str(filepath)
    
    def print_summary_for_ai(self):
        """
        Print a concise summary optimized for Claude Code to read.
        This goes to stdout so Claude Code sees it directly.
        """
        snapshot = self.get_full_snapshot()
        
        print("=" * 60)
        print("PORTFOLIO DATA FOR ANALYSIS")
        print("=" * 60)
        print(f"Timestamp: {snapshot['timestamp']}")
        print(f"Total Value: ${snapshot['totals']['portfolio_value_usd']:,.2f}")
        print(f"Staked: ${snapshot['totals']['staked_value_usd']:,.2f}")
        print()
        
        print("HOLDINGS:")
        for asset, data in sorted(
            snapshot["holdings"].items(),
            key=lambda x: x[1]["total_value_usd"],
            reverse=True
        ):
            perf = data.get("performance") or {}
            change_str = ""
            if perf.get("change_24h") is not None:
                change_str = f" | 24h: {perf['change_24h']:+.1f}%"
            
            print(f"  {asset}: {data['total_balance']:.6f} = ${data['total_value_usd']:,.2f}{change_str}")
        
        print()
        print("EXCHANGE DISTRIBUTION:")
        for exchange, value in snapshot["totals"]["by_exchange"].items():
            pct = (value / snapshot["totals"]["portfolio_value_usd"] * 100) if snapshot["totals"]["portfolio_value_usd"] > 0 else 0
            print(f"  {exchange}: ${value:,.2f} ({pct:.1f}%)")
        
        if snapshot["alerts"]:
            print()
            print("ALERTS:")
            for alert in snapshot["alerts"]:
                print(f"  [{alert['severity'].upper()}] {alert['message']}")
        
        print("=" * 60)
        
        return snapshot


def analyze_portfolio():
    """
    Main function for Claude Code to call.
    Returns structured data and prints summary.
    """
    analyzer = PortfolioAnalyzer()
    
    # Print summary for Claude Code to see
    snapshot = analyzer.print_summary_for_ai()
    
    # Save detailed files
    json_path = analyzer.save_snapshot_json()
    md_path = analyzer.generate_markdown_report()
    
    print(f"\nFiles saved:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    
    return snapshot


def get_portfolio_json() -> Dict:
    """Quick function to get portfolio as JSON dict."""
    analyzer = PortfolioAnalyzer()
    return analyzer.get_full_snapshot()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-friendly Portfolio Analysis")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--report", action="store_true", help="Generate markdown report only")
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    analyzer = PortfolioAnalyzer()
    
    if args.json:
        snapshot = analyzer.get_full_snapshot()
        if args.output:
            Path(args.output).write_text(json.dumps(snapshot, indent=2, default=str))
            print(f"Saved to {args.output}")
        else:
            print(json.dumps(snapshot, indent=2, default=str))
    
    elif args.report:
        path = analyzer.generate_markdown_report(args.output)
        print(f"Report saved to: {path}")
    
    else:
        analyze_portfolio()
