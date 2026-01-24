"""
Kraken API Client
Handles authentication and API requests to Kraken.

API Documentation: https://docs.kraken.com/rest/
"""

import os
import json
import hashlib
import hmac
import base64
import time
import urllib.parse
import requests
from typing import Optional, Dict, Any
from datetime import datetime


def load_kraken_credentials(filepath: str = None) -> Dict[str, str]:
    """Load Kraken API credentials from JSON file."""
    if filepath is None:
        filepath = os.getenv("KRAKEN_API_KEY_FILE", "~/.config/kraken/api_key.json")

    with open(os.path.expanduser(filepath), 'r') as f:
        return json.load(f)


def create_kraken_client(
    api_key: str = None,
    api_secret: str = None,
    key_file: str = None
) -> "KrakenClient":
    """Factory function to create a Kraken client.

    Args:
        api_key: API key
        api_secret: Private/secret key (base64 encoded)
        key_file: Path to JSON file with credentials

    Returns:
        KrakenClient instance
    """
    # Try loading from file first
    if key_file or os.getenv("KRAKEN_API_KEY_FILE"):
        creds = load_kraken_credentials(key_file)
        api_key = creds.get("api_key")
        api_secret = creds.get("private_key") or creds.get("api_secret")

    # Fall back to environment variables
    if not api_key:
        api_key = os.getenv("KRAKEN_API_KEY")
    if not api_secret:
        api_secret = os.getenv("KRAKEN_PRIVATE_KEY") or os.getenv("KRAKEN_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError(
            "No Kraken credentials found. Provide either:\n"
            "  - KRAKEN_API_KEY_FILE environment variable\n"
            "  - KRAKEN_API_KEY and KRAKEN_PRIVATE_KEY environment variables"
        )

    return KrakenClient(api_key=api_key, api_secret=api_secret)


class KrakenClient:
    """Client for Kraken REST API."""
    
    BASE_URL = "https://api.kraken.com"
    
    # Map common symbols to Kraken's format
    # Kraken uses X prefix for crypto (XXBT for BTC) and Z prefix for fiat (ZUSD)
    SYMBOL_MAP = {
        "BTC": "XBT",   # Bitcoin is XBT on Kraken
        "DOGE": "XDG",  # Dogecoin
    }
    
    # Reverse mapping for display
    SYMBOL_REVERSE = {v: k for k, v in SYMBOL_MAP.items()}
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Convert common symbol to Kraken format."""
        return self.SYMBOL_MAP.get(symbol.upper(), symbol.upper())
    
    def _denormalize_symbol(self, kraken_symbol: str) -> str:
        """Convert Kraken symbol back to common format."""
        # Remove X/Z prefixes if present
        clean = kraken_symbol
        if len(clean) == 4 and clean[0] in ('X', 'Z'):
            clean = clean[1:]
        elif len(clean) > 4 and clean.startswith('X'):
            clean = clean[1:]
        return self.SYMBOL_REVERSE.get(clean, clean)
    
    def _get_kraken_pair(self, base: str, quote: str = "USD") -> str:
        """Get Kraken trading pair format."""
        base_k = self._normalize_symbol(base)
        quote_k = self._normalize_symbol(quote)
        return f"{base_k}{quote_k}"
    
    def _generate_signature(self, urlpath: str, data: dict) -> str:
        """Generate signature for private API endpoints."""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        
        mac = hmac.new(
            base64.b64decode(self.api_secret),
            message,
            hashlib.sha512
        )
        signature = base64.b64encode(mac.digest()).decode()
        return signature
    
    def _public_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make public API request (no authentication needed)."""
        url = f"{self.BASE_URL}/0/public/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("error") and len(data["error"]) > 0:
                print(f"Kraken API Error: {data['error']}")
                return None
            
            return data.get("result", {})
            
        except requests.exceptions.RequestException as e:
            print(f"Kraken Request Error: {e}")
            return None
    
    def _private_request(self, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make authenticated private API request."""
        if data is None:
            data = {}
        
        urlpath = f"/0/private/{endpoint}"
        url = f"{self.BASE_URL}{urlpath}"
        
        data["nonce"] = str(int(time.time() * 1000))
        
        headers = {
            "API-Key": self.api_key,
            "API-Sign": self._generate_signature(urlpath, data),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = self.session.post(url, headers=headers, data=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get("error") and len(result["error"]) > 0:
                print(f"Kraken API Error: {result['error']}")
                return None
            
            return result.get("result", {})
            
        except requests.exceptions.RequestException as e:
            print(f"Kraken Request Error: {e}")
            return None
    
    def get_spot_price(self, currency: str, quote_currency: str = "USD") -> Optional[float]:
        """Get current spot price for a currency pair."""
        pair = self._get_kraken_pair(currency, quote_currency)
        
        result = self._public_request("Ticker", {"pair": pair})
        if not result:
            # Try alternative pair format
            alt_pair = f"{currency}{quote_currency}"
            result = self._public_request("Ticker", {"pair": alt_pair})
        
        if result:
            # Kraken returns data keyed by pair name (which may differ)
            for pair_key, data in result.items():
                # 'c' is the last trade closed [price, lot volume]
                if 'c' in data:
                    return float(data['c'][0])
        
        return None
    
    def get_price_changes(self, currency: str, quote_currency: str = "USD") -> Optional[dict]:
        """Get price change percentages for 24h, 7d, and 30d."""
        pair = self._get_kraken_pair(currency, quote_currency)
        
        try:
            # Get current price from ticker
            current_price = self.get_spot_price(currency, quote_currency)
            if not current_price:
                return None
            
            changes = {
                "current_price": current_price,
                "change_24h": None,
                "change_7d": None,
                "change_30d": None,
            }
            
            now = int(time.time())
            
            # Get 24h change from ticker (Kraken provides this)
            ticker_result = self._public_request("Ticker", {"pair": pair})
            if ticker_result:
                for pair_key, data in ticker_result.items():
                    if 'o' in data:  # 'o' is today's opening price
                        open_price = float(data['o'])
                        if open_price > 0:
                            changes["change_24h"] = ((current_price - open_price) / open_price) * 100
            
            # Get 7d and 30d changes using OHLC data
            # interval: 1440 = 1 day in minutes
            ohlc_result = self._public_request("OHLC", {
                "pair": pair,
                "interval": 1440,  # Daily candles
                "since": now - (30 * 86400)
            })
            
            if ohlc_result:
                for pair_key, candles in ohlc_result.items():
                    if pair_key == "last":
                        continue
                    if isinstance(candles, list) and len(candles) > 0:
                        # Candles format: [time, open, high, low, close, vwap, volume, count]
                        # Find candles from ~7d and ~30d ago
                        for candle in candles:
                            candle_time = int(candle[0])
                            candle_open = float(candle[1])
                            days_ago = (now - candle_time) / 86400
                            
                            if 6.5 <= days_ago <= 7.5 and changes["change_7d"] is None:
                                if candle_open > 0:
                                    changes["change_7d"] = ((current_price - candle_open) / candle_open) * 100
                            
                            if 29.5 <= days_ago <= 30.5 and changes["change_30d"] is None:
                                if candle_open > 0:
                                    changes["change_30d"] = ((current_price - candle_open) / candle_open) * 100
            
            return changes
            
        except Exception as e:
            print(f"Error getting price changes for {currency}: {e}")
            return None
    
    def get_trade_history(self, limit: int = 50) -> list:
        """Get trade history."""
        result = self._private_request("TradesHistory", {"trades": True})
        if result and "trades" in result:
            trades = []
            for trade_id, trade in list(result["trades"].items())[:limit]:
                trades.append({
                    "trade_id": trade_id,
                    **trade
                })
            return trades
        return []
    
    def list_products(self) -> list:
        """List all available trading pairs."""
        result = self._public_request("AssetPairs")
        if result:
            products = []
            for pair_name, pair_info in result.items():
                products.append({
                    "product_id": pair_name,
                    "base_currency": pair_info.get("base", ""),
                    "quote_currency": pair_info.get("quote", ""),
                    "status": "online" if pair_info.get("status") == "online" else "offline"
                })
            return products
        return []
    
    def get_server_time(self) -> Optional[dict]:
        """Get server time (useful for testing connectivity)."""
        return self._public_request("Time")
    
    # ==================== TRADING METHODS ====================
    
    def create_order(
        self,
        product_id: str,
        side: str,  # "buy" or "sell"
        order_type: str,  # "market" or "limit"
        volume: Optional[str] = None,  # Amount of base currency
        price: Optional[str] = None,  # Required for limit orders
        quote_volume: Optional[str] = None,  # For market buys with quote currency
        validate: bool = False  # If True, validate only (don't execute)
    ) -> Optional[dict]:
        """
        Create a new order.
        
        Args:
            product_id: Trading pair (e.g., "XBTUSD", "ETHUSD")
            side: "buy" or "sell"
            order_type: "market" or "limit"
            volume: Amount of base currency to trade
            price: Limit price (required for limit orders)
            quote_volume: For market buys, spend this much quote currency
            validate: If True, validate order without executing
        
        Returns:
            Order result dict or None on failure
        """
        data = {
            "pair": product_id,
            "type": side.lower(),
            "ordertype": order_type.lower(),
        }
        
        if volume:
            data["volume"] = str(volume)
        
        if order_type.lower() == "limit" and price:
            data["price"] = str(price)
        
        # For market buys with quote currency amount
        if order_type.lower() == "market" and side.lower() == "buy" and quote_volume:
            data["oflags"] = "viqc"  # Volume in quote currency
            data["volume"] = str(quote_volume)
        
        if validate:
            data["validate"] = True
        
        result = self._private_request("AddOrder", data)
        return result
    
    def market_buy(self, product_id: str, usd_amount: float) -> Optional[dict]:
        """
        Market buy with USD amount.
        Example: market_buy("XBTUSD", 100) buys $100 worth of BTC
        """
        return self.create_order(
            product_id=product_id,
            side="buy",
            order_type="market",
            quote_volume=str(round(usd_amount, 2))
        )
    
    def market_sell(self, product_id: str, amount: float) -> Optional[dict]:
        """
        Market sell base currency amount.
        Example: market_sell("XBTUSD", 0.01) sells 0.01 BTC
        """
        return self.create_order(
            product_id=product_id,
            side="sell",
            order_type="market",
            volume=str(amount)
        )
    
    def limit_buy(self, product_id: str, amount: float, price: float) -> Optional[dict]:
        """
        Place a limit buy order.
        Example: limit_buy("XBTUSD", 0.01, 40000) buys 0.01 BTC at $40,000
        """
        return self.create_order(
            product_id=product_id,
            side="buy",
            order_type="limit",
            volume=str(amount),
            price=str(price)
        )
    
    def limit_sell(self, product_id: str, amount: float, price: float) -> Optional[dict]:
        """
        Place a limit sell order.
        Example: limit_sell("XBTUSD", 0.01, 50000) sells 0.01 BTC at $50,000
        """
        return self.create_order(
            product_id=product_id,
            side="sell",
            order_type="limit",
            volume=str(amount),
            price=str(price)
        )
    
    def cancel_order(self, order_id: str) -> Optional[dict]:
        """Cancel a pending order."""
        result = self._private_request("CancelOrder", {"txid": order_id})
        return result
    
    def cancel_all_orders(self) -> Optional[dict]:
        """Cancel all open orders."""
        result = self._private_request("CancelAll")
        return result
    
    def get_orders(self, trades: bool = True) -> list:
        """Get open orders."""
        result = self._private_request("OpenOrders", {"trades": trades})
        if result and "open" in result:
            orders = []
            for order_id, order in result["open"].items():
                orders.append({
                    "order_id": order_id,
                    **order
                })
            return orders
        return []
    
    def get_closed_orders(self, trades: bool = True) -> list:
        """Get closed orders."""
        result = self._private_request("ClosedOrders", {"trades": trades})
        if result and "closed" in result:
            orders = []
            for order_id, order in result["closed"].items():
                orders.append({
                    "order_id": order_id,
                    **order
                })
            return orders
        return []
    
    def get_order(self, order_id: str) -> Optional[dict]:
        """Get details of a specific order."""
        result = self._private_request("QueryOrders", {"txid": order_id})
        if result:
            return result.get(order_id)
        return None
    
    def get_trade_balance(self, asset: str = "ZUSD") -> Optional[dict]:
        """
        Get trade balance summary.
        Returns equity, margin, free margin, etc.
        """
        result = self._private_request("TradeBalance", {"asset": asset})
        return result
    
    # ==================== STAKING METHODS ====================
    
    def get_staking_assets(self) -> list:
        """Get list of assets available for staking."""
        result = self._private_request("Staking/Assets")
        if result:
            assets = []
            for asset in result:
                assets.append({
                    "asset": asset.get("asset"),
                    "staking_asset": asset.get("staking_asset"),
                    "method": asset.get("method"),
                    "apy_estimate": asset.get("rewards", {}).get("reward"),
                    "min_amount": asset.get("minimum_amount", {}).get("staking"),
                    "on_chain": asset.get("on_chain"),
                    "lock_period": asset.get("lock", {}).get("lockup")
                })
            return assets
        return []
    
    def get_staking_pending(self) -> list:
        """Get pending staking transactions."""
        result = self._private_request("Staking/Pending")
        if result:
            return result
        return []
    
    def get_staking_transactions(self) -> list:
        """Get staking transaction history."""
        result = self._private_request("Staking/Transactions")
        if result:
            return result
        return []
    
    def stake(self, asset: str, amount: float, method: str = None) -> Optional[dict]:
        """
        Stake an asset.
        
        Args:
            asset: Asset to stake (e.g., "ETH", "DOT")
            amount: Amount to stake
            method: Staking method (optional, uses default if not specified)
        """
        params = {
            "asset": asset,
            "amount": str(amount)
        }
        if method:
            params["method"] = method
        
        result = self._private_request("Stake", params)
        return result
    
    def unstake(self, asset: str, amount: float) -> Optional[dict]:
        """
        Unstake an asset.
        
        Args:
            asset: Asset to unstake
            amount: Amount to unstake
        """
        params = {
            "asset": asset,
            "amount": str(amount)
        }
        result = self._private_request("Unstake", params)
        return result
    
    def get_accounts(self) -> list:
        """
        Get all account balances including staked assets.
        Returns list in standardized format matching Coinbase structure.
        """
        result = self._private_request("Balance")
        if not result:
            return []
        
        accounts = []
        for asset, balance in result.items():
            balance_float = float(balance)
            if balance_float > 0:
                # Normalize the symbol for display
                display_symbol = self._denormalize_symbol(asset)
                
                # Detect staked assets (Kraken uses .S suffix)
                is_staked = asset.endswith('.S') or '.S' in asset
                if is_staked:
                    display_symbol = display_symbol.replace('.S', '') + ' (Staked)'
                
                accounts.append({
                    "currency": display_symbol,
                    "available_balance": {
                        "value": balance,
                        "currency": display_symbol
                    },
                    "hold": {
                        "value": "0",
                        "currency": display_symbol
                    },
                    "uuid": asset,  # Use Kraken's asset name as ID
                    "name": f"{display_symbol} Wallet",
                    "type": "ACCOUNT_TYPE_STAKING" if is_staked else (
                        "ACCOUNT_TYPE_CRYPTO" if asset not in ["ZUSD", "ZEUR", "ZGBP"] else "ACCOUNT_TYPE_FIAT"
                    ),
                    "is_staked": is_staked
                })

        return accounts

    def _extract_base_asset(self, asset: str) -> str:
        """Extract base asset from Kraken asset code, removing staking suffixes."""
        import re
        # Remove staking suffixes like .S, .B, .M, .P, or numbered variants like 14.S, 28.S, 07.S, 21.S
        base = re.sub(r'\d*\.[SBMP]$', '', asset)
        # Also handle .B suffix (bonded)
        base = re.sub(r'\.[SBMP]$', '', base)
        return self._denormalize_symbol(base)

    def _get_price_for_asset(self, base_asset: str, ticker_cache: dict) -> float:
        """Get USD price for an asset, trying multiple pair formats."""
        if base_asset in ticker_cache:
            return ticker_cache[base_asset]

        # Try different pair formats
        pair_formats = [
            f"{base_asset}USD",
            f"X{base_asset}ZUSD",
            f"{self._normalize_symbol(base_asset)}USD",
            f"X{self._normalize_symbol(base_asset)}ZUSD",
            f"{base_asset}USDT",
        ]

        for pair in pair_formats:
            result = self._public_request("Ticker", {"pair": pair})
            if result:
                for pair_key, data in result.items():
                    price = float(data.get("c", [0])[0])
                    if price > 0:
                        ticker_cache[base_asset] = price
                        return price

        ticker_cache[base_asset] = 0.0
        return 0.0

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary with USD values."""
        result = self._private_request("Balance")

        if not result:
            return {
                "exchange": "Kraken",
                "total_value_usd": 0,
                "holdings_count": 0,
                "holdings": [],
                "staking": [],
                "error": "Failed to fetch balance"
            }

        holdings = []
        staking_info = []
        total_value = 0.0
        ticker_cache = {}  # Cache prices to avoid duplicate lookups

        # Stablecoins - treat as $1
        stablecoins = {"USD", "USDT", "USDC", "USDD", "DAI", "ZUSD"}

        for asset, balance in result.items():
            balance_float = float(balance)
            if balance_float <= 0:
                continue

            # Detect staking
            is_staked = '.S' in asset or '.B' in asset or '.M' in asset or '.P' in asset

            # Extract base asset (remove staking suffixes)
            base_asset = self._extract_base_asset(asset)
            display_symbol = base_asset + (" (Staked)" if is_staked else "")

            if base_asset.upper() in stablecoins or asset == "ZUSD":
                # Stablecoin - direct value
                holdings.append({
                    "currency": "USD" if asset == "ZUSD" else base_asset,
                    "kraken_code": asset,
                    "balance": balance_float,
                    "price_usd": 1.0,
                    "value_usd": balance_float,
                    "is_staked": is_staked,
                })
                total_value += balance_float
            elif base_asset.upper() not in ["EUR", "GBP", "CAD", "JPY", "ZEUR", "ZGBP"]:
                # Crypto asset - get price
                price_usd = self._get_price_for_asset(base_asset, ticker_cache)
                value_usd = balance_float * price_usd

                holding = {
                    "currency": display_symbol,
                    "kraken_code": asset,
                    "balance": balance_float,
                    "price_usd": price_usd,
                    "value_usd": value_usd,
                    "is_staked": is_staked,
                }
                holdings.append(holding)
                total_value += value_usd

                if is_staked and value_usd > 0:
                    staking_info.append({
                        "asset": base_asset,
                        "staked_amount": balance_float,
                        "value_usd": value_usd,
                    })

        # Sort by value
        holdings.sort(key=lambda x: x['value_usd'], reverse=True)

        return {
            "exchange": "Kraken",
            "total_value_usd": round(total_value, 2),
            "holdings_count": len(holdings),
            "holdings": holdings,
            "staking": staking_info,
            "staking_value_usd": round(sum(s['value_usd'] for s in staking_info), 2),
        }


# Test function
def test_connection():
    """Test Kraken API connection."""
    try:
        client = create_kraken_client()

        # Test public endpoint first
        print("Testing public endpoint...")
        time_result = client.get_server_time()
        if time_result:
            print(f"Server time: {time_result}")

        ticker = client._public_request("Ticker", {"pair": "XBTUSD"})
        if ticker:
            for pair, data in ticker.items():
                print(f"BTC/USD: ${float(data['c'][0]):,.2f}")

        # Test private endpoint
        print("\nTesting private endpoint (account balance)...")
        result = client._private_request("Balance")
        if result:
            print("Balance retrieved successfully!")
            for asset, amount in result.items():
                if float(amount) > 0:
                    print(f"  {asset}: {amount}")
        else:
            print("Failed to get balance - check API credentials")
            return False

        # Get portfolio summary
        print("\nPortfolio Summary:")
        summary = client.get_portfolio_summary()
        print(f"  Total Value: ${summary['total_value_usd']:,.2f}")
        print(f"  Holdings: {summary['holdings_count']}")
        if summary.get('staking'):
            print(f"  Staked Value: ${summary['staking_value_usd']:,.2f}")

        for h in summary['holdings'][:10]:
            print(f"    {h['currency']}: {h['balance']:.6f} = ${h['value_usd']:,.2f}")

        return True

    except Exception as e:
        print(f"Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_connection()
