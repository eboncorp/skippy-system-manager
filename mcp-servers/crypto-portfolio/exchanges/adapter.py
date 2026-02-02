"""
Exchange Adapter Layer
======================

Bridges the ExchangeClient interface (used by real exchange clients like
CoinbaseClient, KrakenClient) to the ExchangeInterface (used by trading
agents like PaperDCAAgent, PaperDayTrader, TradingAgent).

This adapter enables trading agents to execute orders on real exchanges
while maintaining the same interface they use with PaperExchange.

Usage:
    from exchanges import CoinbaseClient
    from exchanges.adapter import LiveExchangeAdapter, MultiExchangeAdapter

    # Single exchange
    client = CoinbaseClient.from_key_file("~/.config/coinbase/cdp_api_key.json")
    adapter = LiveExchangeAdapter(client, "coinbase")
    balance = await adapter.get_balance("BTC")

    # Multi-exchange with routing
    adapters = {"coinbase": adapter, "kraken": kraken_adapter}
    routing = {"BTC": "coinbase", "ETH": "kraken"}
    multi = MultiExchangeAdapter(adapters, routing)
"""

import logging
import time
from decimal import Decimal
from typing import Dict, List, Optional

from exchanges.base import ExchangeClient, Balance
from agents.trading_agent import (
    ExchangeInterface,
    Order,
    OrderSide,
    OrderStatus,
)

logger = logging.getLogger(__name__)


class LiveExchangeAdapter(ExchangeInterface):
    """Wraps a real ExchangeClient to implement ExchangeInterface.

    Translates between:
    - ExchangeInterface.get_balance(currency) -> ExchangeClient.get_balances()
    - ExchangeInterface.get_price(symbol) -> ExchangeClient.get_ticker_price(asset)
    - ExchangeInterface.place_order(Order) -> ExchangeClient.place_market_order(...)
    """

    def __init__(self, client: ExchangeClient, name: str, cache_ttl: int = 30):
        self.client = client
        self.name = name
        self._cache_ttl = cache_ttl
        self._balances_cache: Dict[str, Balance] = {}
        self._balances_cache_time: float = 0
        self._price_cache: Dict[str, Decimal] = {}
        self._price_cache_time: Dict[str, float] = {}

    async def get_balance(self, currency: str) -> Decimal:
        """Get available balance for a currency from the real exchange."""
        now = time.monotonic()
        if now - self._balances_cache_time > self._cache_ttl:
            try:
                self._balances_cache = await self.client.get_balances()
                self._balances_cache_time = now
            except Exception as e:
                logger.warning(f"[{self.name}] Balance fetch failed: {e}")
                # Return cached if available
                if self._balances_cache:
                    pass
                else:
                    return Decimal("0")

        bal = self._balances_cache.get(currency)
        return bal.available if bal else Decimal("0")

    async def get_price(self, symbol: str) -> Decimal:
        """Get current price for a symbol from the real exchange."""
        now = time.monotonic()
        cached_time = self._price_cache_time.get(symbol, 0)

        if now - cached_time > self._cache_ttl:
            try:
                price = await self.client.get_ticker_price(symbol)
                self._price_cache[symbol] = price
                self._price_cache_time[symbol] = now
                return price
            except Exception as e:
                logger.warning(f"[{self.name}] Price fetch failed for {symbol}: {e}")
                return self._price_cache.get(symbol, Decimal("0"))

        return self._price_cache.get(symbol, Decimal("0"))

    async def place_order(self, order: Order) -> Order:
        """Place an order on the real exchange via ExchangeClient.place_market_order().

        Only market orders are supported. The Order dataclass is translated to
        the ExchangeClient's place_market_order(asset, side, amount, quote_amount)
        signature, and the OrderResult is mapped back.
        """
        side = "buy" if order.side == OrderSide.BUY else "sell"

        try:
            if order.side == OrderSide.BUY:
                # For buys, specify USD amount (quote_amount)
                quote_amount = order.quantity * (order.price or Decimal("0"))
                if quote_amount <= 0:
                    # Try to get current price
                    price = await self.get_price(order.symbol)
                    quote_amount = order.quantity * price

                result = await self.client.place_market_order(
                    asset=order.symbol,
                    side=side,
                    quote_amount=quote_amount,
                )
            else:
                # For sells, specify asset amount
                result = await self.client.place_market_order(
                    asset=order.symbol,
                    side=side,
                    amount=order.quantity,
                )

            if result.success:
                order.status = OrderStatus.FILLED
                order.filled_quantity = result.filled_amount
                order.filled_price = result.filled_price
                order.fees = result.fee
                order.id = result.order_id or order.id
                order.exchange_order_id = result.order_id

                logger.info(
                    f"[{self.name}] Order filled: {side} {order.filled_quantity} "
                    f"{order.symbol} @ {order.filled_price}"
                )

                # Invalidate balance cache after trade
                self._balances_cache_time = 0
            else:
                order.status = OrderStatus.REJECTED
                logger.warning(
                    f"[{self.name}] Order rejected for {order.symbol}: {result.error}"
                )

        except Exception as e:
            order.status = OrderStatus.REJECTED
            logger.error(f"[{self.name}] Order execution failed for {order.symbol}: {e}")

        return order

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel not supported for market orders."""
        return False

    async def get_order_status(self, order_id: str) -> Order:
        """Not implemented — market orders fill immediately."""
        raise NotImplementedError("Market orders fill immediately")

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """No open orders — market orders fill immediately."""
        return []

    def invalidate_cache(self):
        """Force refresh on next call."""
        self._balances_cache_time = 0
        self._price_cache_time.clear()

    def __repr__(self) -> str:
        return f"<LiveExchangeAdapter({self.name})>"


class MultiExchangeAdapter(ExchangeInterface):
    """Routes orders to the correct exchange based on asset routing rules.

    Used when a strategy needs to place orders across multiple exchanges.
    For example, the GTI ETF routes BTC to Coinbase GTI and ETH to Kraken
    Business based on etf_config.ExchangeRoute.

    Usage:
        adapters = {
            "coinbase_gti": LiveExchangeAdapter(coinbase_gti_client, "coinbase_gti"),
            "kraken_business": LiveExchangeAdapter(kraken_biz_client, "kraken_business"),
        }
        routing = {"BTC": "coinbase_gti", "ETH": "kraken_business"}
        multi = MultiExchangeAdapter(adapters, routing)
    """

    def __init__(
        self,
        adapters: Dict[str, LiveExchangeAdapter],
        routing: Dict[str, str],
        default_adapter: Optional[str] = None,
    ):
        self.adapters = adapters
        self.routing = routing
        self.default_adapter = default_adapter or next(iter(adapters))

    async def get_balance(self, currency: str) -> Decimal:
        """Get balance for a currency, summed across all exchanges."""
        if currency == "USD":
            total = Decimal("0")
            for adapter in self.adapters.values():
                total += await adapter.get_balance(currency)
            return total

        # For crypto assets, check the routed exchange
        target = self.routing.get(currency, self.default_adapter)
        adapter = self.adapters.get(target)
        if adapter:
            return await adapter.get_balance(currency)
        return Decimal("0")

    async def get_price(self, symbol: str) -> Decimal:
        """Get price from the first exchange that returns a valid value."""
        # Try routed exchange first
        target = self.routing.get(symbol, self.default_adapter)
        adapter = self.adapters.get(target)
        if adapter:
            price = await adapter.get_price(symbol)
            if price > 0:
                return price

        # Fall back to any exchange
        for name, adapter in self.adapters.items():
            if name == target:
                continue
            price = await adapter.get_price(symbol)
            if price > 0:
                return price

        return Decimal("0")

    async def place_order(self, order: Order) -> Order:
        """Route order to the correct exchange based on routing rules."""
        target = self.routing.get(order.symbol, self.default_adapter)
        adapter = self.adapters.get(target)

        if not adapter:
            order.status = OrderStatus.REJECTED
            logger.error(
                f"No exchange adapter for {order.symbol} "
                f"(routing target: {target})"
            )
            return order

        logger.info(f"Routing {order.symbol} order to {target}")
        return await adapter.place_order(order)

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel not supported for market orders."""
        return False

    async def get_order_status(self, order_id: str) -> Order:
        """Not implemented — market orders fill immediately."""
        raise NotImplementedError("Market orders fill immediately")

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """No open orders — market orders fill immediately."""
        return []

    def get_adapter_for(self, symbol: str) -> Optional[LiveExchangeAdapter]:
        """Get the specific adapter that handles a given symbol."""
        target = self.routing.get(symbol, self.default_adapter)
        return self.adapters.get(target)

    def invalidate_all_caches(self):
        """Force refresh on all adapters."""
        for adapter in self.adapters.values():
            adapter.invalidate_cache()

    def __repr__(self) -> str:
        names = ", ".join(self.adapters.keys())
        return f"<MultiExchangeAdapter({names})>"
