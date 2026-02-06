"""
Gemini API Client
Handles authentication and API requests to Gemini Exchange.

API Documentation: https://docs.gemini.com/rest-api/

Supports:
- Portfolio/balance reading
- Spot trading
- Staking (Gemini Earn/Staking)
"""

import hashlib
import hmac
import base64
import json
import time
import requests
from typing import Optional
from datetime import datetime


class GeminiClient:
    """Client for Gemini REST API."""
    
    BASE_URL = "https://api.gemini.com"
    
    def __init__(self, api_key: str, api_secret: str, sandbox: bool = False):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key
            api_secret: Gemini API secret
            sandbox: Use sandbox environment for testing
        """
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.session = requests.Session()
        
        if sandbox:
            self.BASE_URL = "https://api.sandbox.gemini.com"
    
    def _generate_signature(self, payload: dict) -> tuple:
        """Generate signature for API authentication."""
        payload["nonce"] = str(int(time.time() * 1000))
        
        encoded_payload = base64.b64encode(
            json.dumps(payload).encode()
        )
        
        signature = hmac.new(
            self.api_secret,
            encoded_payload,
            hashlib.sha384
        ).hexdigest()
        
        return encoded_payload, signature
    
    def _private_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make authenticated private API request."""
        url = f"{self.BASE_URL}{endpoint}"
        
        payload = {
            "request": endpoint,
        }
        if params:
            payload.update(params)
        
        encoded_payload, signature = self._generate_signature(payload)
        
        headers = {
            "Content-Type": "text/plain",
            "Content-Length": "0",
            "X-GEMINI-APIKEY": self.api_key,
            "X-GEMINI-PAYLOAD": encoded_payload.decode(),
            "X-GEMINI-SIGNATURE": signature,
            "Cache-Control": "no-cache"
        }
        
        try:
            response = self.session.post(url, headers=headers)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            print(f"Gemini HTTP Error: {e}")
            if e.response:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Response: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Gemini Request Error: {e}")
            return None
    
    def _public_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make public API request (no authentication needed)."""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Gemini Request Error: {e}")
            return None
    
    def get_accounts(self) -> list:
        """
        Get all account balances including spot and earn.
        Returns list in standardized format matching other clients.
        """
        # Get spot balances
        result = self._private_request("/v1/balances")
        if not result:
            return []
        
        accounts = []
        
        for balance in result:
            currency = balance.get("currency", "UNKNOWN")
            available = float(balance.get("available", 0))
            amount = float(balance.get("amount", 0))  # Total including holds
            
            if amount > 0:
                accounts.append({
                    "currency": currency,
                    "available_balance": {
                        "value": str(available),
                        "currency": currency
                    },
                    "hold": {
                        "value": str(amount - available),
                        "currency": currency
                    },
                    "uuid": currency,
                    "name": f"{currency} Wallet",
                    "type": "ACCOUNT_TYPE_CRYPTO" if currency != "USD" else "ACCOUNT_TYPE_FIAT",
                    "is_staked": False
                })
        
        # Get staking/earn balances
        earn_balances = self.get_earn_balances()
        for earn in earn_balances:
            currency = earn.get("currency", "UNKNOWN")
            balance = float(earn.get("balance", 0))
            
            if balance > 0:
                accounts.append({
                    "currency": f"{currency} (Staked)",
                    "available_balance": {
                        "value": str(balance),
                        "currency": currency
                    },
                    "hold": {
                        "value": "0",
                        "currency": currency
                    },
                    "uuid": f"{currency}_EARN",
                    "name": f"{currency} Earn/Staking",
                    "type": "ACCOUNT_TYPE_STAKING",
                    "is_staked": True,
                    "apy": earn.get("apy"),
                    "accrued_interest": earn.get("accruedInterest")
                })
        
        return accounts
    
    def get_earn_balances(self) -> list:
        """Get Gemini Earn/Staking balances."""
        result = self._private_request("/v1/earn/balances")
        if result:
            return result
        return []
    
    def get_earn_rates(self) -> list:
        """Get current Gemini Earn interest rates."""
        result = self._private_request("/v1/earn/rates")
        if result:
            return result
        return []
    
    def get_earn_history(self, currency: str = None, limit: int = 50) -> list:
        """Get Gemini Earn transaction history (deposits, withdrawals, interest)."""
        params = {"limit": limit}
        if currency:
            params["currency"] = currency
        
        result = self._private_request("/v1/earn/history", params)
        if result:
            return result
        return []
    
    def deposit_to_earn(self, currency: str, amount: float) -> Optional[dict]:
        """Deposit funds to Gemini Earn."""
        params = {
            "currency": currency,
            "amount": str(amount)
        }
        return self._private_request("/v1/earn/deposit", params)
    
    def withdraw_from_earn(self, currency: str, amount: float) -> Optional[dict]:
        """Withdraw funds from Gemini Earn."""
        params = {
            "currency": currency,
            "amount": str(amount)
        }
        return self._private_request("/v1/earn/withdraw", params)
    
    def get_spot_price(self, currency: str, quote_currency: str = "USD") -> Optional[float]:
        """Get current spot price for a currency pair."""
        symbol = f"{currency.lower()}{quote_currency.lower()}"
        
        result = self._public_request(f"/v1/pubticker/{symbol}")
        if result and "last" in result:
            return float(result["last"])
        
        return None
    
    def get_price_changes(self, currency: str, quote_currency: str = "USD") -> Optional[dict]:
        """Get price change percentages for 24h, 7d, and 30d."""
        symbol = f"{currency.lower()}{quote_currency.lower()}"
        
        try:
            current_price = self.get_spot_price(currency, quote_currency)
            if not current_price:
                return None
            
            changes = {
                "current_price": current_price,
                "change_24h": None,
                "change_7d": None,
                "change_30d": None,
            }
            
            # Get 24h ticker data
            ticker = self._public_request(f"/v2/ticker/{symbol}")
            if ticker and "changes" in ticker:
                # Gemini provides percentage changes directly
                changes_data = ticker["changes"]
                if isinstance(changes_data, list) and len(changes_data) > 0:
                    changes["change_24h"] = float(changes_data[0]) if changes_data[0] else None
            
            # Get candles for 7d and 30d
            now = int(time.time() * 1000)
            
            # Daily candles
            candles = self._public_request(f"/v2/candles/{symbol}/1day")
            
            if candles and isinstance(candles, list):
                for candle in candles:
                    # Candle format: [time, open, high, low, close, volume]
                    candle_time = candle[0]
                    candle_open = float(candle[1])
                    days_ago = (now - candle_time) / (86400 * 1000)
                    
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
    
    def get_trade_history(self, symbol: str = None, limit: int = 50) -> list:
        """Get trade history."""
        params = {"limit_trades": limit}
        if symbol:
            params["symbol"] = symbol
        
        result = self._private_request("/v1/mytrades", params)
        if result:
            return result
        return []
    
    def list_products(self) -> list:
        """List all available trading symbols."""
        result = self._public_request("/v1/symbols")
        if result:
            products = []
            for symbol in result:
                # Parse symbol (e.g., "btcusd" -> BTC, USD)
                # Most are 6 chars (3+3), but some are longer
                if len(symbol) >= 6:
                    base = symbol[:-3].upper()
                    quote = symbol[-3:].upper()
                    products.append({
                        "product_id": symbol,
                        "base_currency": base,
                        "quote_currency": quote,
                        "status": "online"
                    })
            return products
        return []
    
    def get_symbol_details(self, symbol: str) -> Optional[dict]:
        """Get trading rules for a symbol (min order size, tick size, etc.)."""
        result = self._public_request(f"/v1/symbols/details/{symbol}")
        return result
    
    # ==================== TRADING METHODS ====================
    
    def create_order(
        self,
        symbol: str,
        side: str,  # "buy" or "sell"
        order_type: str,  # "exchange limit" or "exchange market" (Gemini naming)
        amount: Optional[str] = None,  # Amount of base currency
        price: Optional[str] = None,  # Required for limit orders
        options: list = None  # ["maker-or-cancel", "immediate-or-cancel", "fill-or-kill"]
    ) -> Optional[dict]:
        """
        Create a new order.
        
        Args:
            symbol: Trading pair (e.g., "btcusd", "ethusd")
            side: "buy" or "sell"
            order_type: "exchange limit" or "exchange market"
            amount: Amount of base currency to trade
            price: Limit price (required for limit orders)
            options: Order options like "maker-or-cancel"
        
        Returns:
            Order result dict or None on failure
        """
        params = {
            "symbol": symbol.lower(),
            "side": side.lower(),
            "type": order_type,
            "amount": str(amount)
        }
        
        if price:
            params["price"] = str(price)
        
        if options:
            params["options"] = options
        
        result = self._private_request("/v1/order/new", params)
        return result
    
    def market_buy(self, symbol: str, usd_amount: float) -> Optional[dict]:
        """
        Market buy with USD amount.
        Note: Gemini doesn't have true market orders, uses limit with high price.
        """
        # Get current price and add buffer for slippage
        current_price = self.get_spot_price(symbol.replace("usd", "").upper(), "USD")
        if not current_price:
            print(f"Could not get price for {symbol}")
            return None
        
        # Calculate amount with 2% slippage buffer
        execution_price = current_price * 1.02
        amount = usd_amount / execution_price
        
        return self.create_order(
            symbol=symbol,
            side="buy",
            order_type="exchange limit",
            amount=str(round(amount, 8)),
            price=str(round(execution_price, 2)),
            options=["immediate-or-cancel"]
        )
    
    def market_sell(self, symbol: str, amount: float) -> Optional[dict]:
        """
        Market sell base currency amount.
        Note: Gemini doesn't have true market orders, uses limit with low price.
        """
        current_price = self.get_spot_price(symbol.replace("usd", "").upper(), "USD")
        if not current_price:
            print(f"Could not get price for {symbol}")
            return None
        
        # 2% slippage buffer below current price
        execution_price = current_price * 0.98
        
        return self.create_order(
            symbol=symbol,
            side="sell",
            order_type="exchange limit",
            amount=str(amount),
            price=str(round(execution_price, 2)),
            options=["immediate-or-cancel"]
        )
    
    def limit_buy(self, symbol: str, amount: float, price: float) -> Optional[dict]:
        """Place a limit buy order."""
        return self.create_order(
            symbol=symbol,
            side="buy",
            order_type="exchange limit",
            amount=str(amount),
            price=str(price)
        )
    
    def limit_sell(self, symbol: str, amount: float, price: float) -> Optional[dict]:
        """Place a limit sell order."""
        return self.create_order(
            symbol=symbol,
            side="sell",
            order_type="exchange limit",
            amount=str(amount),
            price=str(price)
        )
    
    def cancel_order(self, order_id: str) -> Optional[dict]:
        """Cancel a pending order."""
        params = {"order_id": order_id}
        result = self._private_request("/v1/order/cancel", params)
        return result
    
    def cancel_all_orders(self) -> Optional[dict]:
        """Cancel all open orders."""
        result = self._private_request("/v1/order/cancel/all")
        return result
    
    def get_order(self, order_id: str) -> Optional[dict]:
        """Get details of a specific order."""
        params = {"order_id": order_id}
        result = self._private_request("/v1/order/status", params)
        return result
    
    def get_orders(self) -> list:
        """Get all active orders."""
        result = self._private_request("/v1/orders")
        if result:
            return result
        return []
    
    def get_notional_volume(self) -> Optional[dict]:
        """Get 30-day trading volume and fee tier."""
        result = self._private_request("/v1/notionalvolume")
        return result
    
    def get_trade_volume(self) -> Optional[dict]:
        """Get detailed trade volume breakdown."""
        result = self._private_request("/v1/tradevolume")
        return result


# Staking-specific helper class
class GeminiStakingManager:
    """Helper class for managing Gemini Earn/Staking."""
    
    def __init__(self, client: GeminiClient):
        self.client = client
    
    def get_staking_summary(self) -> dict:
        """Get summary of all staked assets with rates and earnings."""
        balances = self.client.get_earn_balances()
        rates = self.client.get_earn_rates()
        
        # Build rate lookup
        rate_lookup = {}
        for rate in rates:
            rate_lookup[rate.get("currency")] = rate
        
        summary = {
            "total_staked_usd": 0,
            "total_accrued_usd": 0,
            "positions": []
        }
        
        for balance in balances:
            currency = balance.get("currency")
            amount = float(balance.get("balance", 0))
            accrued = float(balance.get("accruedInterest", 0))
            
            # Get current price
            price = self.client.get_spot_price(currency, "USD") or 0
            
            # Get APY
            rate_info = rate_lookup.get(currency, {})
            apy = float(rate_info.get("rate", 0)) * 100  # Convert to percentage
            
            usd_value = amount * price
            accrued_usd = accrued * price
            
            summary["total_staked_usd"] += usd_value
            summary["total_accrued_usd"] += accrued_usd
            
            summary["positions"].append({
                "currency": currency,
                "amount": amount,
                "usd_value": usd_value,
                "apy": apy,
                "accrued": accrued,
                "accrued_usd": accrued_usd
            })
        
        return summary
    
    def get_available_for_staking(self) -> list:
        """Get list of assets available for staking with current rates."""
        rates = self.client.get_earn_rates()
        available = []
        
        for rate in rates:
            available.append({
                "currency": rate.get("currency"),
                "apy": float(rate.get("rate", 0)) * 100,
                "min_deposit": rate.get("minDepositAmount"),
                "max_deposit": rate.get("maxDepositAmount")
            })
        
        return sorted(available, key=lambda x: x["apy"], reverse=True)
