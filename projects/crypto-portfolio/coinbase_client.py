"""
Coinbase Advanced Trade API Client
Handles authentication and API requests to Coinbase.

Uses the official coinbase-advanced-py SDK which supports:
- CDP API keys (JSON file with EC private key)
- Legacy API keys (key + secret)

Install: pip install coinbase-advanced-py
"""

import os
import json
from typing import Optional, List, Dict, Any
from coinbase.rest import RESTClient


def create_coinbase_client(
    api_key: str = None,
    api_secret: str = None,
    cdp_key_file: str = None
) -> "CoinbaseClientWrapper":
    """Factory function to create a Coinbase client.

    Args:
        api_key: Legacy API key
        api_secret: Legacy API secret
        cdp_key_file: Path to CDP key JSON file (preferred)

    Returns:
        CoinbaseClientWrapper instance
    """
    # Check environment variables if not provided
    if cdp_key_file is None:
        cdp_key_file = os.getenv("CDP_API_KEY_FILE")
    if api_key is None:
        api_key = os.getenv("COINBASE_API_KEY")
    if api_secret is None:
        api_secret = os.getenv("COINBASE_API_SECRET")

    # Create client - prefer CDP key file
    if cdp_key_file and os.path.exists(os.path.expanduser(cdp_key_file)):
        client = RESTClient(key_file=os.path.expanduser(cdp_key_file))
    elif api_key and api_secret:
        client = RESTClient(api_key=api_key, api_secret=api_secret)
    else:
        raise ValueError(
            "No Coinbase credentials found. Provide either:\n"
            "  - CDP_API_KEY_FILE environment variable (path to CDP key JSON)\n"
            "  - COINBASE_API_KEY and COINBASE_API_SECRET environment variables"
        )

    return CoinbaseClientWrapper(client)


# Known staked/wrapped tokens
STAKED_TOKENS = {
    "CBETH": {"base_asset": "ETH", "provider": "Coinbase Wrapped Staked ETH", "apy": 3.2},
    "STETH": {"base_asset": "ETH", "provider": "Lido Staked ETH", "apy": 3.5},
    "WSTETH": {"base_asset": "ETH", "provider": "Wrapped Lido Staked ETH", "apy": 3.5},
    "RETH": {"base_asset": "ETH", "provider": "Rocket Pool ETH", "apy": 3.1},
    "MSOL": {"base_asset": "SOL", "provider": "Marinade Staked SOL", "apy": 6.5},
    "STSOL": {"base_asset": "SOL", "provider": "Lido Staked SOL", "apy": 6.3},
    "JITOASOL": {"base_asset": "SOL", "provider": "Jito Staked SOL", "apy": 7.0},
}


class CoinbaseClientWrapper:
    """Wrapper around official Coinbase SDK for consistent interface."""

    def __init__(self, client: RESTClient):
        self.client = client

    def get_accounts(self, limit: int = 250) -> List[Dict[str, Any]]:
        """Get all accounts with balances."""
        result = self.client.get_accounts(limit=limit)
        accounts = []

        for acc in result.accounts:
            # Parse balance - handle both dict and object response formats
            try:
                ab = getattr(acc, 'available_balance', None)
                if ab is None:
                    balance = 0
                elif isinstance(ab, dict):
                    balance = float(ab.get('value', 0))
                elif hasattr(ab, 'value'):
                    balance = float(ab.value)
                else:
                    balance = float(ab) if ab else 0
            except:
                balance = 0

            # Handle both dict and object for currency/name
            if isinstance(acc, dict):
                currency = acc.get('currency', '')
                name = acc.get('name', '')
            else:
                currency = getattr(acc, 'currency', '')
                name = getattr(acc, 'name', '')

            # Check for staking indicators
            is_staked = currency in STAKED_TOKENS
            staking_info = STAKED_TOKENS.get(currency, {})

            account_data = {
                "uuid": getattr(acc, 'uuid', ''),
                "name": name,
                "currency": currency,
                "balance": balance,
                "available_balance": {"value": str(balance)},
                "is_staked": is_staked,
            }

            if is_staked:
                account_data["staked_asset"] = staking_info.get("base_asset", currency)
                account_data["staking_provider"] = staking_info.get("provider", "Unknown")
                account_data["estimated_apy"] = staking_info.get("apy", 0)
                account_data["type"] = "ACCOUNT_TYPE_STAKING"

            accounts.append(account_data)

        return accounts

    def get_spot_price(self, currency: str, quote_currency: str = "USD") -> Optional[float]:
        """Get current spot price, trying USD then USDC pairs."""
        # Try USD pair first
        try:
            product = self.client.get_product(f"{currency}-{quote_currency}")
            if product and product.price:
                return float(product.price)
        except:
            pass

        # Try USDC pair as fallback
        if quote_currency == "USD":
            try:
                product = self.client.get_product(f"{currency}-USDC")
                if product and product.price:
                    return float(product.price)
            except:
                pass

        return None

    def list_products(self) -> List[Dict[str, Any]]:
        """List available products."""
        try:
            result = self.client.get_products()
            return [{"product_id": p.product_id} for p in result.products]
        except:
            return []

    def get_fills(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order fills."""
        try:
            result = self.client.get_fills(limit=limit)
            return [vars(f) for f in result.fills] if result.fills else []
        except:
            return []

    def get_orders(self, status: str = "OPEN", product_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get orders."""
        try:
            result = self.client.list_orders(order_status=[status], limit=limit, product_id=product_id)
            return [vars(o) for o in result.orders] if result.orders else []
        except:
            return []

    def place_market_order(self, product_id: str, side: str, amount: float,
                           quote_size: float = None) -> Dict[str, Any]:
        """Place a market order.

        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            side: 'BUY' or 'SELL'
            amount: Base currency amount (for SELL) or None if using quote_size
            quote_size: Quote currency amount (for BUY with dollar amount)

        Returns:
            Order details or error
        """
        import uuid
        client_order_id = str(uuid.uuid4())

        try:
            if side.upper() == "BUY" and quote_size:
                # Buy with quote currency (e.g., $100 of BTC)
                result = self.client.market_order_buy(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    quote_size=str(quote_size)
                )
            elif side.upper() == "BUY":
                # Buy specific base amount
                result = self.client.market_order_buy(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=str(amount)
                )
            else:
                # Sell base currency
                result = self.client.market_order_sell(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=str(amount)
                )

            return {
                "success": True,
                "order_id": getattr(result, 'order_id', client_order_id),
                "client_order_id": client_order_id,
                "product_id": product_id,
                "side": side.upper(),
                "type": "MARKET",
                "status": getattr(result, 'status', 'PENDING'),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def place_limit_order(self, product_id: str, side: str, amount: float,
                          price: float, time_in_force: str = "GTC") -> Dict[str, Any]:
        """Place a limit order.

        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            side: 'BUY' or 'SELL'
            amount: Base currency amount
            price: Limit price
            time_in_force: GTC, IOC, FOK, or GTD

        Returns:
            Order details or error
        """
        import uuid
        client_order_id = str(uuid.uuid4())

        try:
            if side.upper() == "BUY":
                result = self.client.limit_order_gtc_buy(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=str(amount),
                    limit_price=str(price)
                )
            else:
                result = self.client.limit_order_gtc_sell(
                    client_order_id=client_order_id,
                    product_id=product_id,
                    base_size=str(amount),
                    limit_price=str(price)
                )

            return {
                "success": True,
                "order_id": getattr(result, 'order_id', client_order_id),
                "client_order_id": client_order_id,
                "product_id": product_id,
                "side": side.upper(),
                "type": "LIMIT",
                "price": price,
                "amount": amount,
                "status": getattr(result, 'status', 'PENDING'),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order by ID.

        Args:
            order_id: The order ID to cancel

        Returns:
            Cancellation result
        """
        try:
            result = self.client.cancel_orders([order_id])
            return {
                "success": True,
                "order_id": order_id,
                "message": "Order cancelled"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_products(self, product_type: str = None) -> List[Dict[str, Any]]:
        """Get available trading products/pairs.

        Args:
            product_type: Filter by type (e.g., 'SPOT')

        Returns:
            List of tradable products
        """
        try:
            result = self.client.get_products(product_type=product_type)
            return [
                {
                    "product_id": getattr(p, 'product_id', ''),
                    "base_currency": getattr(p, 'base_currency_id', ''),
                    "quote_currency": getattr(p, 'quote_currency_id', ''),
                    "price": float(getattr(p, 'price', 0) or 0),
                    "status": getattr(p, 'status', ''),
                }
                for p in result.products
            ] if result.products else []
        except:
            return []

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary including staked positions.

        Uses get_portfolio_breakdown for accurate totals including staking.
        """
        try:
            # Get portfolio breakdown for accurate totals including staking
            portfolios = self.client.get_portfolios()
            if not portfolios.portfolios:
                return self._get_portfolio_from_accounts()

            portfolio_uuid = portfolios.portfolios[0].uuid
            breakdown = self.client.get_portfolio_breakdown(portfolio_uuid)
            bd = breakdown.breakdown
            balances = bd.portfolio_balances
            positions = bd.spot_positions

            total_value = float(balances['total_balance']['value'])
            total_crypto = float(balances['total_crypto_balance']['value'])
            total_cash = float(balances['total_cash_equivalent_balance']['value'])

            holdings = []
            staking_positions = []

            for p in positions:
                asset = getattr(p, 'asset', '')
                fiat = getattr(p, 'total_balance_fiat', 0)
                crypto = getattr(p, 'total_balance_crypto', 0)
                available_crypto = getattr(p, 'available_to_trade_crypto', 0)
                cost_basis_obj = getattr(p, 'cost_basis', {})
                cost = float(cost_basis_obj.get('value', 0)) if isinstance(cost_basis_obj, dict) else 0
                pnl = getattr(p, 'unrealized_pnl', 0)

                # Detect staking: if available to trade is less than total, difference is staked
                staked_amount = crypto - available_crypto if crypto > available_crypto else 0
                is_staked = staked_amount > 0

                holding = {
                    "currency": asset,
                    "balance": crypto,
                    "available_balance": available_crypto,
                    "staked_balance": staked_amount,
                    "price_usd": fiat / crypto if crypto > 0 else 0,
                    "value_usd": fiat,
                    "cost_basis_usd": cost,
                    "unrealized_pnl": pnl,
                    "is_staked": is_staked,
                }

                if is_staked:
                    holding["staked_value_usd"] = staked_amount * (fiat / crypto) if crypto > 0 else 0
                    staking_positions.append(holding)

                holdings.append(holding)

            # Sort by value
            holdings.sort(key=lambda x: x['value_usd'], reverse=True)
            staking_positions.sort(key=lambda x: x.get('staked_value_usd', 0), reverse=True)

            return {
                "total_value_usd": total_value,
                "total_crypto_usd": total_crypto,
                "total_cash_usd": total_cash,
                "holdings_count": len(holdings),
                "holdings": holdings,
                "staking_positions": staking_positions,
                "staking_count": len(staking_positions),
                "total_staked_usd": sum(h.get('staked_value_usd', 0) for h in staking_positions),
            }
        except Exception as e:
            # Fallback to account-based calculation
            return self._get_portfolio_from_accounts()

    def _get_portfolio_from_accounts(self) -> Dict[str, Any]:
        """Fallback: Get portfolio from accounts (doesn't include staked amounts)."""
        accounts = self.get_accounts()
        total_value = 0
        holdings = []

        STABLECOINS = {
            'USD': 1.0, 'USDC': 1.0, 'USDT': 1.0, 'DAI': 1.0,
            'GUSD': 1.0, 'BUSD': 1.0, 'GYEN': 0.0065, 'PYUSD': 1.0
        }

        for acc in accounts:
            balance = acc.get('balance', 0)
            if balance <= 0:
                continue

            currency = acc.get('currency', '')

            if currency in STABLECOINS:
                price = STABLECOINS[currency]
                value_usd = balance * price
            else:
                price = self.get_spot_price(currency)
                value_usd = balance * price if price else 0
                price = price or 0

            total_value += value_usd
            holdings.append({
                "currency": currency,
                "balance": balance,
                "price_usd": price,
                "value_usd": value_usd,
                "is_staked": acc.get('is_staked', False),
            })

        holdings.sort(key=lambda x: x['value_usd'], reverse=True)

        return {
            "total_value_usd": total_value,
            "holdings_count": len(holdings),
            "holdings": holdings,
            "staking_positions": [],
            "staking_count": 0,
        }


# Legacy compatibility aliases
def load_cdp_key_file(filepath: str) -> dict:
    """Load CDP API key from JSON file."""
    with open(os.path.expanduser(filepath), 'r') as f:
        return json.load(f)
