#!/usr/bin/env python3
"""
Multi-Exchange Trading CLI
Unified command-line interface for trading across Coinbase, Kraken, Crypto.com, and Gemini.

Usage:
    python multi_trading_cli.py portfolio
    python multi_trading_cli.py buy coinbase BTC 100
    python multi_trading_cli.py sell kraken ETH 0.5
    python multi_trading_cli.py prices BTC ETH SOL
    python multi_trading_cli.py arbitrage BTC
"""

import os
import argparse
from typing import Optional, Dict, List
from dotenv import load_dotenv
from tabulate import tabulate

# Import exchange clients
from exchanges import CoinbaseClient, KrakenClient, CryptoComClient, GeminiClient


class MultiExchangeTrader:
    """Unified trading interface for multiple exchanges."""

    EXCHANGE_NAMES = {
        "coinbase": "Coinbase",
        "kraken": "Kraken",
        "cryptocom": "Crypto.com",
        "gemini": "Gemini"
    }

    # Trading pair formats per exchange
    PAIR_FORMATS = {
        "coinbase": "{base}-{quote}",      # BTC-USD
        "kraken": "{base}{quote}",          # XBTUSD (with symbol mapping)
        "cryptocom": "{base}_{quote}",      # BTC_USDT
        "gemini": "{base}{quote}",          # btcusd (lowercase)
    }

    def __init__(self):
        load_dotenv()
        self.clients: Dict[str, object] = {}
        self.connected = []

    def connect(self, exchange: str = None) -> bool:
        """Connect to specified exchange or all configured exchanges."""
        if exchange:
            return self._connect_single(exchange.lower())

        # Connect to all
        success = False
        for ex in self.EXCHANGE_NAMES.keys():
            if self._connect_single(ex):
                success = True
        return success

    def _connect_single(self, exchange: str) -> bool:
        """Connect to a single exchange."""
        exchange = exchange.lower()

        if exchange == "coinbase":
            key = os.getenv("COINBASE_API_KEY")
            secret = os.getenv("COINBASE_API_SECRET")
            if key and secret:
                self.clients["coinbase"] = CoinbaseClient(key, secret)
                self.connected.append("coinbase")
                return True

        elif exchange == "kraken":
            key = os.getenv("KRAKEN_API_KEY")
            secret = os.getenv("KRAKEN_API_SECRET")
            if key and secret:
                client = KrakenClient(key, secret)
                if client.get_server_time():
                    self.clients["kraken"] = client
                    self.connected.append("kraken")
                    return True

        elif exchange == "cryptocom":
            key = os.getenv("CRYPTOCOM_API_KEY")
            secret = os.getenv("CRYPTOCOM_API_SECRET")
            if key and secret:
                self.clients["cryptocom"] = CryptoComClient(key, secret)
                self.connected.append("cryptocom")
                return True

        elif exchange == "gemini":
            key = os.getenv("GEMINI_API_KEY")
            secret = os.getenv("GEMINI_API_SECRET")
            if key and secret:
                self.clients["gemini"] = GeminiClient(key, secret)
                self.connected.append("gemini")
                return True

        return False

    def get_client(self, exchange: str):
        """Get client for specified exchange."""
        exchange = exchange.lower()
        if exchange not in self.clients:
            if not self._connect_single(exchange):
                raise ValueError(f"Exchange '{exchange}' not configured or connection failed")
        return self.clients[exchange]

    def format_pair(self, exchange: str, base: str, quote: str = "USD") -> str:
        """Format trading pair for specific exchange."""
        exchange = exchange.lower()

        if exchange == "kraken":
            # Kraken has special symbol mappings
            client = self.clients.get("kraken")
            if client:
                base = client._normalize_symbol(base)
                quote = client._normalize_symbol(quote)
            return f"{base}{quote}"

        elif exchange == "gemini":
            return f"{base.lower()}{quote.lower()}"

        elif exchange == "cryptocom":
            # Crypto.com primarily uses USDT
            if quote == "USD":
                quote = "USDT"
            return f"{base.upper()}_{quote.upper()}"

        else:  # coinbase
            return f"{base.upper()}-{quote.upper()}"

    def get_all_prices(self, assets: List[str]) -> Dict[str, Dict[str, float]]:
        """Get prices for assets across all connected exchanges."""
        prices = {asset: {} for asset in assets}

        for exchange, client in self.clients.items():
            for asset in assets:
                try:
                    price = client.get_spot_price(asset, "USD")
                    if price:
                        prices[asset][exchange] = price
                except Exception as e:
                    pass  # Skip if price not available

        return prices

    def find_arbitrage(self, asset: str, min_spread_pct: float = 0.5) -> Optional[dict]:
        """
        Find arbitrage opportunities for an asset across exchanges.

        Returns opportunity if spread exceeds min_spread_pct.
        """
        prices = self.get_all_prices([asset])
        asset_prices = prices.get(asset, {})

        if len(asset_prices) < 2:
            return None

        # Find min and max
        min_exchange = min(asset_prices, key=asset_prices.get)
        max_exchange = max(asset_prices, key=asset_prices.get)

        min_price = asset_prices[min_exchange]
        max_price = asset_prices[max_exchange]

        spread_pct = ((max_price - min_price) / min_price) * 100

        if spread_pct >= min_spread_pct:
            return {
                "asset": asset,
                "buy_exchange": min_exchange,
                "buy_price": min_price,
                "sell_exchange": max_exchange,
                "sell_price": max_price,
                "spread_pct": spread_pct,
                "spread_usd": max_price - min_price,
                "all_prices": asset_prices
            }

        return None

    def market_buy(self, exchange: str, asset: str, usd_amount: float, confirm: bool = True) -> Optional[dict]:
        """Execute market buy on specified exchange."""
        client = self.get_client(exchange)
        pair = self.format_pair(exchange, asset, "USD")

        # Get current price for display
        price = client.get_spot_price(asset, "USD")

        print(f"\n{'='*50}")
        print("📈 MARKET BUY ORDER")
        print(f"{'='*50}")
        print(f"Exchange:  {self.EXCHANGE_NAMES.get(exchange, exchange)}")
        print(f"Asset:     {asset}")
        print(f"Amount:    ${usd_amount:,.2f}")
        print(f"Est Price: ${price:,.2f}" if price else "Est Price: N/A")
        print(f"Pair:      {pair}")
        print(f"{'='*50}")

        if confirm:
            response = input("\nConfirm order? (yes/no): ").strip().lower()
            if response not in ["yes", "y"]:
                print("Order cancelled.")
                return None

        result = client.market_buy(pair, usd_amount)

        if result:
            print("\n✅ Order submitted successfully!")
            print(f"Result: {result}")
        else:
            print("\n❌ Order failed")

        return result

    def market_sell(self, exchange: str, asset: str, amount: float, confirm: bool = True) -> Optional[dict]:
        """Execute market sell on specified exchange."""
        client = self.get_client(exchange)
        pair = self.format_pair(exchange, asset, "USD")

        # Get current price for display
        price = client.get_spot_price(asset, "USD")
        usd_value = amount * price if price else 0

        print(f"\n{'='*50}")
        print("📉 MARKET SELL ORDER")
        print(f"{'='*50}")
        print(f"Exchange:  {self.EXCHANGE_NAMES.get(exchange, exchange)}")
        print(f"Asset:     {asset}")
        print(f"Amount:    {amount} {asset}")
        print(f"Est Value: ${usd_value:,.2f}" if price else "Est Value: N/A")
        print(f"Est Price: ${price:,.2f}" if price else "Est Price: N/A")
        print(f"Pair:      {pair}")
        print(f"{'='*50}")

        if confirm:
            response = input("\nConfirm order? (yes/no): ").strip().lower()
            if response not in ["yes", "y"]:
                print("Order cancelled.")
                return None

        result = client.market_sell(pair, amount)

        if result:
            print("\n✅ Order submitted successfully!")
            print(f"Result: {result}")
        else:
            print("\n❌ Order failed")

        return result

    def limit_buy(self, exchange: str, asset: str, amount: float, price: float, confirm: bool = True) -> Optional[dict]:
        """Place limit buy order on specified exchange."""
        client = self.get_client(exchange)
        pair = self.format_pair(exchange, asset, "USD")

        total_cost = amount * price

        print(f"\n{'='*50}")
        print("📊 LIMIT BUY ORDER")
        print(f"{'='*50}")
        print(f"Exchange:   {self.EXCHANGE_NAMES.get(exchange, exchange)}")
        print(f"Asset:      {asset}")
        print(f"Amount:     {amount} {asset}")
        print(f"Limit:      ${price:,.2f}")
        print(f"Total Cost: ${total_cost:,.2f}")
        print(f"Pair:       {pair}")
        print(f"{'='*50}")

        if confirm:
            response = input("\nConfirm order? (yes/no): ").strip().lower()
            if response not in ["yes", "y"]:
                print("Order cancelled.")
                return None

        result = client.limit_buy(pair, amount, price)

        if result:
            print("\n✅ Limit order placed!")
            print(f"Result: {result}")
        else:
            print("\n❌ Order failed")

        return result

    def limit_sell(self, exchange: str, asset: str, amount: float, price: float, confirm: bool = True) -> Optional[dict]:
        """Place limit sell order on specified exchange."""
        client = self.get_client(exchange)
        pair = self.format_pair(exchange, asset, "USD")

        total_value = amount * price

        print(f"\n{'='*50}")
        print("📊 LIMIT SELL ORDER")
        print(f"{'='*50}")
        print(f"Exchange:    {self.EXCHANGE_NAMES.get(exchange, exchange)}")
        print(f"Asset:       {asset}")
        print(f"Amount:      {amount} {asset}")
        print(f"Limit:       ${price:,.2f}")
        print(f"Total Value: ${total_value:,.2f}")
        print(f"Pair:        {pair}")
        print(f"{'='*50}")

        if confirm:
            response = input("\nConfirm order? (yes/no): ").strip().lower()
            if response not in ["yes", "y"]:
                print("Order cancelled.")
                return None

        result = client.limit_sell(pair, amount, price)

        if result:
            print("\n✅ Limit order placed!")
            print(f"Result: {result}")
        else:
            print("\n❌ Order failed")

        return result

    def get_orders(self, exchange: str = None) -> Dict[str, list]:
        """Get open orders from one or all exchanges."""
        orders = {}

        exchanges = [exchange] if exchange else self.connected

        for ex in exchanges:
            if ex in self.clients:
                try:
                    client = self.clients[ex]
                    ex_orders = client.get_orders()
                    if ex_orders:
                        orders[ex] = ex_orders
                except Exception as e:
                    print(f"Error getting orders from {ex}: {e}")

        return orders

    def cancel_order(self, exchange: str, order_id: str, instrument: str = None) -> Optional[dict]:
        """Cancel an order on specified exchange."""
        client = self.get_client(exchange)

        # Crypto.com requires instrument name
        if exchange.lower() == "cryptocom" and instrument:
            return client.cancel_order(order_id, instrument)

        return client.cancel_order(order_id)

    def display_portfolio(self):
        """Display combined portfolio from all exchanges."""
        print(f"\n{'='*70}")
        print("🌐 MULTI-EXCHANGE PORTFOLIO")
        print(f"{'='*70}")

        total_value = 0
        exchange_totals = {}

        for exchange, client in self.clients.items():
            print(f"\n📈 {self.EXCHANGE_NAMES.get(exchange, exchange)}")
            print("-" * 50)

            try:
                accounts = client.get_accounts()
                exchange_value = 0

                table_data = []
                for account in accounts:
                    currency = account.get("currency", "UNKNOWN")
                    balance = float(account.get("available_balance", {}).get("value", 0))

                    if balance <= 0:
                        continue

                    # Get price
                    base_currency = currency.replace(" (Staked)", "")
                    price = client.get_spot_price(base_currency, "USD")

                    # Handle stablecoins
                    if base_currency in ["USD", "USDC", "USDT"]:
                        price = 1.0

                    usd_value = balance * price if price else 0
                    exchange_value += usd_value

                    is_staked = account.get("is_staked", False) or "(Staked)" in currency
                    staking_indicator = "🔒" if is_staked else ""

                    table_data.append([
                        f"{staking_indicator} {currency}",
                        f"{balance:.8f}".rstrip('0').rstrip('.'),
                        f"${price:,.2f}" if price else "N/A",
                        f"${usd_value:,.2f}"
                    ])

                if table_data:
                    print(tabulate(table_data, headers=["Asset", "Balance", "Price", "Value"], tablefmt="simple"))
                    print(f"\n💰 Subtotal: ${exchange_value:,.2f}")
                else:
                    print("No holdings")

                exchange_totals[exchange] = exchange_value
                total_value += exchange_value

            except Exception as e:
                print(f"Error: {e}")

        print(f"\n{'='*70}")
        print(f"💎 TOTAL PORTFOLIO VALUE: ${total_value:,.2f}")
        print(f"{'='*70}")

        if len(exchange_totals) > 1:
            print("\n📊 Distribution:")
            for ex, value in sorted(exchange_totals.items(), key=lambda x: x[1], reverse=True):
                pct = (value / total_value * 100) if total_value > 0 else 0
                print(f"  • {self.EXCHANGE_NAMES.get(ex, ex)}: ${value:,.2f} ({pct:.1f}%)")

    def display_prices(self, assets: List[str]):
        """Display prices across all exchanges."""
        prices = self.get_all_prices(assets)

        print(f"\n{'='*70}")
        print("💱 PRICE COMPARISON ACROSS EXCHANGES")
        print(f"{'='*70}")

        headers = ["Asset"] + [self.EXCHANGE_NAMES.get(ex, ex) for ex in self.connected] + ["Spread"]
        table_data = []

        for asset in assets:
            asset_prices = prices.get(asset, {})
            row = [asset]

            for ex in self.connected:
                price = asset_prices.get(ex)
                row.append(f"${price:,.2f}" if price else "-")

            # Calculate spread
            valid_prices = [p for p in asset_prices.values() if p]
            if len(valid_prices) >= 2:
                spread = ((max(valid_prices) - min(valid_prices)) / min(valid_prices)) * 100
                row.append(f"{spread:.2f}%")
            else:
                row.append("-")

            table_data.append(row)

        print(tabulate(table_data, headers=headers, tablefmt="simple"))

    def display_arbitrage(self, assets: List[str], min_spread: float = 0.5):
        """Display arbitrage opportunities."""
        print(f"\n{'='*70}")
        print(f"🔄 ARBITRAGE SCANNER (min spread: {min_spread}%)")
        print(f"{'='*70}")

        opportunities = []

        for asset in assets:
            opp = self.find_arbitrage(asset, min_spread)
            if opp:
                opportunities.append(opp)

        if opportunities:
            for opp in sorted(opportunities, key=lambda x: x["spread_pct"], reverse=True):
                print(f"\n✨ {opp['asset']}: {opp['spread_pct']:.2f}% spread")
                print(f"   Buy on {self.EXCHANGE_NAMES.get(opp['buy_exchange'], opp['buy_exchange'])}: ${opp['buy_price']:,.2f}")
                print(f"   Sell on {self.EXCHANGE_NAMES.get(opp['sell_exchange'], opp['sell_exchange'])}: ${opp['sell_price']:,.2f}")
                print(f"   Profit per unit: ${opp['spread_usd']:,.2f}")
        else:
            print("\nNo significant arbitrage opportunities found.")
            print("(Consider lowering the minimum spread threshold)")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Exchange Crypto Trading CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s portfolio                      # View holdings across all exchanges
  %(prog)s prices BTC ETH SOL             # Compare prices across exchanges
  %(prog)s arbitrage BTC ETH SOL          # Find arbitrage opportunities
  %(prog)s buy coinbase BTC 100           # Buy $100 of BTC on Coinbase
  %(prog)s sell kraken ETH 0.5            # Sell 0.5 ETH on Kraken
  %(prog)s limit-buy gemini BTC 0.01 95000  # Limit buy on Gemini
  %(prog)s orders                         # View open orders
  %(prog)s cancel kraken ORDER123         # Cancel order
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Portfolio command
    sub_portfolio = subparsers.add_parser("portfolio", help="View portfolio across exchanges")
    sub_portfolio.add_argument("-e", "--exchange", help="Specific exchange only")

    # Prices command
    sub_prices = subparsers.add_parser("prices", help="Compare prices across exchanges")
    sub_prices.add_argument("assets", nargs="+", help="Assets to check (e.g., BTC ETH SOL)")

    # Arbitrage command
    sub_arb = subparsers.add_parser("arbitrage", help="Find arbitrage opportunities")
    sub_arb.add_argument("assets", nargs="+", help="Assets to scan")
    sub_arb.add_argument("-m", "--min-spread", type=float, default=0.5, help="Minimum spread %% (default: 0.5)")

    # Buy command
    sub_buy = subparsers.add_parser("buy", help="Market buy")
    sub_buy.add_argument("exchange", help="Exchange (coinbase, kraken, cryptocom, gemini)")
    sub_buy.add_argument("asset", help="Asset to buy (e.g., BTC)")
    sub_buy.add_argument("amount", type=float, help="USD amount to spend")
    sub_buy.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    # Sell command
    sub_sell = subparsers.add_parser("sell", help="Market sell")
    sub_sell.add_argument("exchange", help="Exchange")
    sub_sell.add_argument("asset", help="Asset to sell")
    sub_sell.add_argument("amount", type=float, help="Amount of asset to sell")
    sub_sell.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    # Limit buy command
    sub_lbuy = subparsers.add_parser("limit-buy", help="Limit buy order")
    sub_lbuy.add_argument("exchange", help="Exchange")
    sub_lbuy.add_argument("asset", help="Asset to buy")
    sub_lbuy.add_argument("amount", type=float, help="Amount of asset")
    sub_lbuy.add_argument("price", type=float, help="Limit price")
    sub_lbuy.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    # Limit sell command
    sub_lsell = subparsers.add_parser("limit-sell", help="Limit sell order")
    sub_lsell.add_argument("exchange", help="Exchange")
    sub_lsell.add_argument("asset", help="Asset to sell")
    sub_lsell.add_argument("amount", type=float, help="Amount of asset")
    sub_lsell.add_argument("price", type=float, help="Limit price")
    sub_lsell.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    # Orders command
    sub_orders = subparsers.add_parser("orders", help="View open orders")
    sub_orders.add_argument("-e", "--exchange", help="Specific exchange only")

    # Cancel command
    sub_cancel = subparsers.add_parser("cancel", help="Cancel an order")
    sub_cancel.add_argument("exchange", help="Exchange")
    sub_cancel.add_argument("order_id", help="Order ID to cancel")
    sub_cancel.add_argument("-i", "--instrument", help="Instrument (required for Crypto.com)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize trader
    trader = MultiExchangeTrader()

    # Connect to exchanges based on command
    if args.command in ["buy", "sell", "limit-buy", "limit-sell", "cancel"]:
        if not trader.connect(args.exchange):
            print(f"❌ Failed to connect to {args.exchange}. Check your API keys.")
            return
    else:
        trader.connect()
        if not trader.connected:
            print("❌ No exchanges connected. Configure API keys in .env file.")
            return

    # Execute command
    if args.command == "portfolio":
        trader.display_portfolio()

    elif args.command == "prices":
        trader.display_prices(args.assets)

    elif args.command == "arbitrage":
        trader.display_arbitrage(args.assets, args.min_spread)

    elif args.command == "buy":
        trader.market_buy(args.exchange, args.asset, args.amount, confirm=not args.yes)

    elif args.command == "sell":
        trader.market_sell(args.exchange, args.asset, args.amount, confirm=not args.yes)

    elif args.command == "limit-buy":
        trader.limit_buy(args.exchange, args.asset, args.amount, args.price, confirm=not args.yes)

    elif args.command == "limit-sell":
        trader.limit_sell(args.exchange, args.asset, args.amount, args.price, confirm=not args.yes)

    elif args.command == "orders":
        orders = trader.get_orders(args.exchange)
        if orders:
            for ex, ex_orders in orders.items():
                print(f"\n📋 {trader.EXCHANGE_NAMES.get(ex, ex)} Open Orders:")
                print("-" * 50)
                for order in ex_orders:
                    print(f"  {order}")
        else:
            print("\nNo open orders found.")

    elif args.command == "cancel":
        result = trader.cancel_order(args.exchange, args.order_id, args.instrument)
        if result:
            print(f"✅ Order cancelled: {result}")
        else:
            print("❌ Failed to cancel order")


if __name__ == "__main__":
    main()
