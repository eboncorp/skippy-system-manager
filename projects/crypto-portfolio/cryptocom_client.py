"""
Crypto.com Exchange API Client
Handles authentication and API requests to Crypto.com Exchange.

API Documentation: https://exchange-docs.crypto.com/exchange/v1/rest-ws/index.html

Note: This is for the Crypto.com EXCHANGE API, not the Crypto.com App API.
The Exchange API is for advanced trading features.
"""

import hashlib
import hmac
import time
import json
import requests
from typing import Optional


class CryptoComClient:
    """Client for Crypto.com Exchange API."""
    
    # Crypto.com Exchange API (for trading)
    BASE_URL = "https://api.crypto.com/exchange/v1"
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
    
    def _generate_signature(self, method: str, request_id: int, params: dict, nonce: int) -> str:
        """Generate HMAC-SHA256 signature for API authentication."""
        # Build the parameter string for signing
        param_str = ""
        if params:
            # Sort params by key and build string
            sorted_params = sorted(params.items())
            param_str = "".join(f"{k}{v}" for k, v in sorted_params)
        
        # Signature payload: method + id + api_key + params + nonce
        sig_payload = f"{method}{request_id}{self.api_key}{param_str}{nonce}"
        
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            sig_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_request(self, method: str, params: dict = None) -> Optional[dict]:
        """Make authenticated request to Crypto.com API."""
        if params is None:
            params = {}
        
        request_id = int(time.time() * 1000)
        nonce = int(time.time() * 1000)
        
        signature = self._generate_signature(method, request_id, params, nonce)
        
        payload = {
            "id": request_id,
            "method": method,
            "api_key": self.api_key,
            "params": params,
            "sig": signature,
            "nonce": nonce
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.post(
                f"{self.BASE_URL}/{method}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                error_msg = data.get("message", "Unknown error")
                print(f"Crypto.com API Error: {error_msg} (code: {data.get('code')})")
                return None
            
            return data.get("result", {})
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text if e.response else 'No response'}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Crypto.com Request Error: {e}")
            return None
    
    def _public_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make public API request (no authentication needed)."""
        url = f"{self.BASE_URL}/public/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                error_msg = data.get("message", "Unknown error")
                print(f"Crypto.com API Error: {error_msg}")
                return None
            
            return data.get("result", {})
            
        except requests.exceptions.RequestException as e:
            print(f"Crypto.com Request Error: {e}")
            return None
    
    def get_accounts(self) -> list:
        """
        Get all account balances including staking.
        Returns list in standardized format matching Coinbase structure.
        """
        result = self._make_request("private/user-balance")
        if not result:
            return []
        
        accounts = []
        position_balances = result.get("data", [])
        
        for balance_data in position_balances:
            for balance in balance_data.get("position_balances", []):
                available = float(balance.get("quantity", 0))
                reserved = float(balance.get("reserved_qty", 0))
                
                if available > 0 or reserved > 0:
                    currency = balance.get("instrument_name", "UNKNOWN")
                    accounts.append({
                        "currency": currency,
                        "available_balance": {
                            "value": str(available),
                            "currency": currency
                        },
                        "hold": {
                            "value": str(reserved),
                            "currency": currency
                        },
                        "uuid": currency,
                        "name": f"{currency} Wallet",
                        "type": "ACCOUNT_TYPE_CRYPTO",
                        "is_staked": False
                    })
        
        # Get staking positions
        staking_positions = self.get_staking_positions()
        for stake in staking_positions:
            currency = stake.get("instrument_name", "UNKNOWN")
            staked_amount = float(stake.get("quantity", 0))
            
            if staked_amount > 0:
                accounts.append({
                    "currency": f"{currency} (Staked)",
                    "available_balance": {
                        "value": str(staked_amount),
                        "currency": currency
                    },
                    "hold": {
                        "value": "0",
                        "currency": currency
                    },
                    "uuid": f"{currency}_STAKED",
                    "name": f"{currency} Staking",
                    "type": "ACCOUNT_TYPE_STAKING",
                    "is_staked": True,
                    "apy": stake.get("apy"),
                    "reward_rate": stake.get("reward_rate"),
                    "unbonding_period": stake.get("unbonding_period")
                })
        
        return accounts
    
    def get_staking_positions(self) -> list:
        """Get all staking positions."""
        result = self._make_request("private/staking/get-staking-position")
        if result and "data" in result:
            return result["data"]
        return []
    
    def get_staking_instruments(self) -> list:
        """Get available staking instruments with APY info."""
        result = self._make_request("private/staking/get-staking-instruments")
        if result and "data" in result:
            return result["data"]
        return []
    
    def stake(self, instrument_name: str, quantity: float) -> Optional[dict]:
        """
        Stake an asset.
        
        Args:
            instrument_name: Asset to stake (e.g., "ETH", "CRO")
            quantity: Amount to stake
        """
        params = {
            "instrument_name": instrument_name,
            "quantity": str(quantity)
        }
        result = self._make_request("private/staking/stake", params)
        return result
    
    def unstake(self, instrument_name: str, quantity: float) -> Optional[dict]:
        """
        Unstake an asset (initiates unbonding period).
        
        Args:
            instrument_name: Asset to unstake
            quantity: Amount to unstake
        """
        params = {
            "instrument_name": instrument_name,
            "quantity": str(quantity)
        }
        result = self._make_request("private/staking/unstake", params)
        return result
    
    def get_staking_history(self, instrument_name: str = None, limit: int = 50) -> list:
        """Get staking transaction history."""
        params = {"page_size": limit}
        if instrument_name:
            params["instrument_name"] = instrument_name
        
        result = self._make_request("private/staking/get-staking-history", params)
        if result and "data" in result:
            return result["data"]
        return []
    
    def get_staking_rewards(self, instrument_name: str = None) -> list:
        """Get staking rewards history."""
        params = {}
        if instrument_name:
            params["instrument_name"] = instrument_name
        
        result = self._make_request("private/staking/get-reward-history", params)
        if result and "data" in result:
            return result["data"]
        return []
    
    def get_spot_price(self, currency: str, quote_currency: str = "USD") -> Optional[float]:
        """Get current spot price for a currency pair."""
        # Crypto.com uses USDT as primary quote currency, try both
        for quote in [quote_currency, "USDT"]:
            instrument = f"{currency.upper()}_{quote.upper()}"
            
            result = self._public_request("get-ticker", {"instrument_name": instrument})
            if result and "data" in result:
                data = result["data"]
                if isinstance(data, list) and len(data) > 0:
                    return float(data[0].get("a", 0))  # 'a' is best ask price
                elif isinstance(data, dict):
                    return float(data.get("a", 0))
        
        return None
    
    def get_price_changes(self, currency: str, quote_currency: str = "USD") -> Optional[dict]:
        """Get price change percentages for 24h, 7d, and 30d."""
        # Try USD first, then USDT
        for quote in [quote_currency, "USDT"]:
            instrument = f"{currency.upper()}_{quote.upper()}"
            
            try:
                # Get ticker for 24h change
                ticker_result = self._public_request("get-ticker", {"instrument_name": instrument})
                
                if ticker_result and "data" in ticker_result:
                    data = ticker_result["data"]
                    if isinstance(data, list) and len(data) > 0:
                        data = data[0]
                    
                    current_price = float(data.get("a", 0))  # Best ask
                    change_24h = float(data.get("c", 0))  # 24h price change percentage
                    
                    if current_price > 0:
                        changes = {
                            "current_price": current_price,
                            "change_24h": change_24h,
                            "change_7d": None,
                            "change_30d": None,
                        }
                        
                        # Get candlestick data for 7d and 30d changes
                        now = int(time.time() * 1000)  # Crypto.com uses milliseconds
                        
                        # Get daily candlesticks
                        candle_result = self._public_request("get-candlestick", {
                            "instrument_name": instrument,
                            "timeframe": "D",  # Daily
                        })
                        
                        if candle_result and "data" in candle_result:
                            candles = candle_result["data"]
                            if candles:
                                # Candles: [timestamp, open, high, low, close, volume]
                                for candle in candles:
                                    candle_time = int(candle.get("t", 0))
                                    candle_open = float(candle.get("o", 0))
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
                continue
        
        return None
    
    def get_trade_history(self, instrument: str = None, limit: int = 50) -> list:
        """Get trade history."""
        params = {"page_size": limit}
        if instrument:
            params["instrument_name"] = instrument
        
        result = self._make_request("private/get-trades", params)
        if result and "data" in result:
            return result["data"]
        return []
    
    def list_products(self) -> list:
        """List all available trading instruments."""
        result = self._public_request("get-instruments")
        if result and "data" in result:
            products = []
            for instrument in result["data"]:
                products.append({
                    "product_id": instrument.get("symbol", ""),
                    "base_currency": instrument.get("base_currency", ""),
                    "quote_currency": instrument.get("quote_currency", ""),
                    "status": "online"  # Crypto.com doesn't have status in listing
                })
            return products
        return []
    
    # ==================== TRADING METHODS ====================
    
    def create_order(
        self,
        instrument_name: str,
        side: str,  # "BUY" or "SELL"
        order_type: str,  # "MARKET" or "LIMIT"
        quantity: Optional[float] = None,  # Amount of base currency
        price: Optional[float] = None,  # Required for limit orders
        notional: Optional[float] = None,  # For market buys with quote currency
        time_in_force: str = "GOOD_TILL_CANCEL",  # GTC, IOC, FOK
        client_oid: Optional[str] = None
    ) -> Optional[dict]:
        """
        Create a new order.
        
        Args:
            instrument_name: Trading pair (e.g., "BTC_USDT", "ETH_USD")
            side: "BUY" or "SELL"
            order_type: "MARKET" or "LIMIT"
            quantity: Amount of base currency to trade
            price: Limit price (required for limit orders)
            notional: For market buys, spend this much quote currency
            time_in_force: Order validity (GOOD_TILL_CANCEL, IMMEDIATE_OR_CANCEL, FILL_OR_KILL)
            client_oid: Optional client order ID
        
        Returns:
            Order result dict or None on failure
        """
        params = {
            "instrument_name": instrument_name,
            "side": side.upper(),
            "type": order_type.upper(),
        }
        
        if quantity:
            params["quantity"] = str(quantity)
        
        if order_type.upper() == "LIMIT":
            if price:
                params["price"] = str(price)
            params["time_in_force"] = time_in_force
        
        # For market buys with quote currency (notional orders)
        if order_type.upper() == "MARKET" and notional:
            params["notional"] = str(notional)
            if "quantity" in params:
                del params["quantity"]
        
        if client_oid:
            params["client_oid"] = client_oid
        
        result = self._make_request("private/create-order", params)
        return result
    
    def market_buy(self, instrument_name: str, usd_amount: float) -> Optional[dict]:
        """
        Market buy with USD/USDT amount.
        Example: market_buy("BTC_USDT", 100) buys $100 worth of BTC
        """
        return self.create_order(
            instrument_name=instrument_name,
            side="BUY",
            order_type="MARKET",
            notional=round(usd_amount, 2)
        )
    
    def market_sell(self, instrument_name: str, amount: float) -> Optional[dict]:
        """
        Market sell base currency amount.
        Example: market_sell("BTC_USDT", 0.01) sells 0.01 BTC
        """
        return self.create_order(
            instrument_name=instrument_name,
            side="SELL",
            order_type="MARKET",
            quantity=amount
        )
    
    def limit_buy(self, instrument_name: str, amount: float, price: float) -> Optional[dict]:
        """
        Place a limit buy order.
        Example: limit_buy("BTC_USDT", 0.01, 40000) buys 0.01 BTC at $40,000
        """
        return self.create_order(
            instrument_name=instrument_name,
            side="BUY",
            order_type="LIMIT",
            quantity=amount,
            price=price
        )
    
    def limit_sell(self, instrument_name: str, amount: float, price: float) -> Optional[dict]:
        """
        Place a limit sell order.
        Example: limit_sell("BTC_USDT", 0.01, 50000) sells 0.01 BTC at $50,000
        """
        return self.create_order(
            instrument_name=instrument_name,
            side="SELL",
            order_type="LIMIT",
            quantity=amount,
            price=price
        )
    
    def cancel_order(self, order_id: str, instrument_name: str) -> Optional[dict]:
        """Cancel a pending order."""
        params = {
            "order_id": order_id,
            "instrument_name": instrument_name
        }
        result = self._make_request("private/cancel-order", params)
        return result
    
    def cancel_all_orders(self, instrument_name: str = None) -> Optional[dict]:
        """Cancel all open orders, optionally for a specific instrument."""
        params = {}
        if instrument_name:
            params["instrument_name"] = instrument_name
        
        result = self._make_request("private/cancel-all-orders", params)
        return result
    
    def get_orders(self, instrument_name: str = None, status: str = "ACTIVE") -> list:
        """
        Get orders filtered by status.
        Status: ACTIVE, CANCELED, FILLED, REJECTED, EXPIRED
        """
        params = {}
        if instrument_name:
            params["instrument_name"] = instrument_name
        
        # Use get-open-orders for active orders
        if status == "ACTIVE":
            result = self._make_request("private/get-open-orders", params)
        else:
            params["status"] = status
            result = self._make_request("private/get-order-history", params)
        
        if result and "data" in result:
            return result["data"]
        return []
    
    def get_order(self, order_id: str) -> Optional[dict]:
        """Get details of a specific order."""
        params = {"order_id": order_id}
        result = self._make_request("private/get-order-detail", params)
        if result and "data" in result:
            return result["data"]
        return None
    
    def get_account_summary(self) -> Optional[dict]:
        """Get account summary with equity and margin info."""
        result = self._make_request("private/get-account-summary")
        return result


class CryptoComAppClient:
    """
    Client for Crypto.com App API (Consumer API).
    This is separate from the Exchange API and is used for the mobile app.
    
    Note: The Crypto.com App API has different endpoints and authentication.
    This is a simplified implementation for basic operations.
    """
    
    BASE_URL = "https://api.crypto.com/v2"
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
    
    def _generate_signature(self, method: str, request_id: int, params: dict, nonce: int) -> str:
        """Generate HMAC-SHA256 signature."""
        param_str = ""
        if params:
            sorted_params = sorted(params.items())
            param_str = "".join(f"{k}{v}" for k, v in sorted_params)
        
        sig_payload = f"{method}{request_id}{self.api_key}{param_str}{nonce}"
        
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            sig_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_request(self, method: str, params: dict = None) -> Optional[dict]:
        """Make authenticated request."""
        if params is None:
            params = {}
        
        request_id = int(time.time() * 1000)
        nonce = int(time.time() * 1000)
        
        signature = self._generate_signature(method, request_id, params, nonce)
        
        payload = {
            "id": request_id,
            "method": method,
            "api_key": self.api_key,
            "params": params,
            "sig": signature,
            "nonce": nonce
        }
        
        try:
            response = self.session.post(
                f"{self.BASE_URL}/{method}",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                print(f"Crypto.com App API Error: {data.get('message')} (code: {data.get('code')})")
                return None
            
            return data.get("result", {})
            
        except requests.exceptions.RequestException as e:
            print(f"Crypto.com App Request Error: {e}")
            return None
    
    def get_accounts(self) -> list:
        """Get account balances from Crypto.com App."""
        result = self._make_request("private/get-account-summary")
        if not result:
            return []
        
        accounts = []
        for balance in result.get("accounts", []):
            available = float(balance.get("available", 0))
            if available > 0:
                currency = balance.get("currency", "UNKNOWN")
                accounts.append({
                    "currency": currency,
                    "available_balance": {
                        "value": str(available),
                        "currency": currency
                    },
                    "hold": {
                        "value": str(balance.get("order", 0)),
                        "currency": currency
                    },
                    "uuid": currency,
                    "name": f"{currency} Wallet",
                    "type": "ACCOUNT_TYPE_CRYPTO"
                })
        
        return accounts
