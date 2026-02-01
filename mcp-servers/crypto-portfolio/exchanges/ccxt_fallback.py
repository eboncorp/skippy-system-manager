"""
CCXT Fallback Exchange Client
==============================

Generic exchange client using the CCXT library as a fallback for exchanges
that don't have a dedicated client implementation. Supports any exchange
supported by CCXT (100+).

Usage:
    from exchanges.ccxt_fallback import CCXTClient, CCXT_AVAILABLE

    if CCXT_AVAILABLE:
        client = CCXTClient("bitfinex", api_key="...", api_secret="...")
        balances = await client.get_balances()

Environment variables:
    {EXCHANGE}_API_KEY:    API key for the exchange
    {EXCHANGE}_API_SECRET: API secret for the exchange
    {EXCHANGE}_PASSWORD:   API passphrase (if required, e.g. OKX, KuCoin)
    CCXT_EXCHANGES:        Comma-separated list of exchanges to initialize
"""

import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from .base import Balance, ExchangeClient, OrderResult, StakingReward, Trade

logger = logging.getLogger(__name__)

try:
    import ccxt.async_support as ccxt_async
    CCXT_AVAILABLE = True
except ImportError:
    ccxt_async = None
    CCXT_AVAILABLE = False

# Exchanges known to work well with CCXT for portfolio tracking
RECOMMENDED_CCXT_EXCHANGES = {
    "bitfinex", "bitstamp", "bybit", "gate", "huobi",
    "kucoin", "mexc", "poloniex", "bitget", "phemex",
}

# Quote currencies to try when fetching ticker prices (in priority order)
QUOTE_CURRENCIES = ["USD", "USDT", "USDC"]


class CCXTClient(ExchangeClient):
    """Generic exchange client powered by CCXT.

    Implements the ExchangeClient ABC using CCXT's unified API.
    Staking operations are not supported via CCXT.
    """

    def __init__(self, exchange_id: str, api_key: str = "",
                 api_secret: str = "", password: str = "",
                 sandbox: bool = False):
        """Initialize CCXT client for a specific exchange.

        Args:
            exchange_id: CCXT exchange identifier (e.g. 'bitfinex', 'kucoin').
            api_key: Exchange API key.
            api_secret: Exchange API secret.
            password: API passphrase (for exchanges that require it).
            sandbox: Use sandbox/testnet mode.
        """
        if not CCXT_AVAILABLE:
            raise RuntimeError(
                "ccxt package is not installed. "
                "Install with: pip install ccxt"
            )

        self.exchange_id = exchange_id.lower()
        self.name = f"ccxt_{self.exchange_id}"

        exchange_class = getattr(ccxt_async, self.exchange_id, None)
        if exchange_class is None:
            raise ValueError(
                f"Unknown CCXT exchange: {self.exchange_id}. "
                f"Available: {', '.join(ccxt_async.exchanges[:10])}..."
            )

        config = {"enableRateLimit": True}
        if api_key:
            config["apiKey"] = api_key
        if api_secret:
            config["secret"] = api_secret
        if password:
            config["password"] = password

        self._exchange = exchange_class(config)

        if sandbox:
            self._exchange.set_sandbox_mode(True)

        logger.info(f"CCXT client initialized for {self.exchange_id}")

    async def close(self):
        """Close the CCXT exchange connection."""
        if self._exchange:
            await self._exchange.close()

    async def get_balances(self) -> Dict[str, Balance]:
        """Get all non-zero balances via CCXT fetch_balance()."""
        try:
            raw = await self._exchange.fetch_balance()
        except Exception as e:
            logger.error(f"CCXT {self.exchange_id} fetch_balance failed: {e}")
            return {}

        balances = {}
        total = raw.get("total", {})
        free = raw.get("free", {})

        for asset, amount in total.items():
            if amount is None or float(amount) == 0:
                continue

            available = float(free.get(asset, 0) or 0)
            total_amount = float(amount)

            balances[asset] = Balance(
                asset=asset,
                total=Decimal(str(total_amount)),
                available=Decimal(str(available)),
                staked=Decimal("0"),  # CCXT doesn't distinguish staked
            )

        return balances

    async def get_ticker_price(self, asset: str) -> Decimal:
        """Get current USD price, trying USD/USDT/USDC pairs."""
        for quote in QUOTE_CURRENCIES:
            symbol = f"{asset}/{quote}"
            try:
                ticker = await self._exchange.fetch_ticker(symbol)
                if ticker and ticker.get("last"):
                    return Decimal(str(ticker["last"]))
            except Exception:
                continue

        raise ValueError(
            f"No price available for {asset} on {self.exchange_id}"
        )

    async def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        asset: Optional[str] = None,
    ) -> List[Trade]:
        """Get trade history via CCXT fetch_my_trades().

        Note: Iterates through available markets to find trades.
        Some exchanges require specific symbol to be passed.
        """
        trades = []
        since = int(start_date.timestamp() * 1000) if start_date else None

        # If specific asset requested, try common pairs
        if asset:
            symbols = [f"{asset}/{q}" for q in QUOTE_CURRENCIES]
        else:
            # Load markets and iterate traded symbols
            try:
                await self._exchange.load_markets()
                symbols = list(self._exchange.symbols)[:50]  # Limit to avoid rate limits
            except Exception as e:
                logger.warning(f"CCXT {self.exchange_id} load_markets failed: {e}")
                return []

        for symbol in symbols:
            try:
                raw_trades = await self._exchange.fetch_my_trades(
                    symbol=symbol, since=since, limit=100
                )
            except Exception:
                continue

            for t in raw_trades:
                ts = datetime.fromtimestamp(t["timestamp"] / 1000)

                if end_date and ts > end_date:
                    continue

                base = t.get("symbol", "").split("/")[0] if "/" in t.get("symbol", "") else asset or ""

                trades.append(Trade(
                    id=str(t.get("id", "")),
                    timestamp=ts,
                    asset=base,
                    side=t.get("side", "buy"),
                    amount=Decimal(str(t.get("amount", 0))),
                    price=Decimal(str(t.get("price", 0))),
                    fee=Decimal(str(t.get("fee", {}).get("cost", 0) or 0)),
                    fee_asset=t.get("fee", {}).get("currency", "USD") or "USD",
                ))

        return sorted(trades, key=lambda t: t.timestamp)

    async def place_market_order(
        self,
        asset: str,
        side: str,
        amount: Optional[Decimal] = None,
        quote_amount: Optional[Decimal] = None,
    ) -> OrderResult:
        """Place a market order via CCXT."""
        # Find a valid symbol
        symbol = None
        for quote in QUOTE_CURRENCIES:
            test_sym = f"{asset}/{quote}"
            try:
                await self._exchange.load_markets()
                if test_sym in self._exchange.symbols:
                    symbol = test_sym
                    break
            except Exception:
                continue

        if not symbol:
            return OrderResult(
                success=False,
                error=f"No tradeable pair found for {asset} on {self.exchange_id}"
            )

        try:
            order_amount = float(amount) if amount else None

            # For buy with quote amount, some exchanges support createMarketBuyOrderWithCost
            if side == "buy" and quote_amount and not amount:
                if hasattr(self._exchange, "create_market_buy_order_with_cost"):
                    result = await self._exchange.create_market_buy_order_with_cost(
                        symbol, float(quote_amount)
                    )
                else:
                    # Estimate amount from price
                    ticker = await self._exchange.fetch_ticker(symbol)
                    price = ticker.get("last", 0)
                    if price:
                        order_amount = float(quote_amount) / price
                    else:
                        return OrderResult(success=False, error="Cannot determine price")

                    result = await self._exchange.create_market_order(
                        symbol, side, order_amount
                    )
            else:
                if order_amount is None:
                    return OrderResult(success=False, error="Amount required")
                result = await self._exchange.create_market_order(
                    symbol, side, order_amount
                )

            return OrderResult(
                success=True,
                order_id=str(result.get("id", "")),
                filled_amount=Decimal(str(result.get("filled", 0) or 0)),
                filled_price=Decimal(str(result.get("average", 0) or 0)),
                fee=Decimal(str(result.get("fee", {}).get("cost", 0) or 0)),
            )

        except Exception as e:
            return OrderResult(success=False, error=str(e))

    async def get_staking_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[StakingReward]:
        """Not supported via CCXT. Returns empty list."""
        logger.info(
            f"Staking rewards not available via CCXT for {self.exchange_id}. "
            "Use a dedicated exchange client for staking data."
        )
        return []

    async def stake(self, asset: str, amount: Decimal) -> bool:
        """Not supported via CCXT."""
        raise NotImplementedError(
            f"Staking is not supported via CCXT for {self.exchange_id}. "
            "Use the exchange's native API or web interface."
        )

    async def unstake(self, asset: str, amount: Decimal) -> bool:
        """Not supported via CCXT."""
        raise NotImplementedError(
            f"Unstaking is not supported via CCXT for {self.exchange_id}. "
            "Use the exchange's native API or web interface."
        )


def create_ccxt_client(exchange_id: str) -> Optional[CCXTClient]:
    """Factory to create a CCXT client from environment variables.

    Reads credentials from:
        {EXCHANGE_ID}_API_KEY
        {EXCHANGE_ID}_API_SECRET
        {EXCHANGE_ID}_PASSWORD (optional)

    Args:
        exchange_id: CCXT exchange identifier.

    Returns:
        CCXTClient if credentials found, None otherwise.
    """
    if not CCXT_AVAILABLE:
        return None

    env_prefix = exchange_id.upper().replace("-", "_").replace(".", "_")
    api_key = os.environ.get(f"{env_prefix}_API_KEY", "")
    api_secret = os.environ.get(f"{env_prefix}_API_SECRET", "")
    password = os.environ.get(f"{env_prefix}_PASSWORD", "")

    if not api_key:
        logger.debug(f"No API key found for CCXT exchange {exchange_id}")
        return None

    try:
        return CCXTClient(
            exchange_id=exchange_id,
            api_key=api_key,
            api_secret=api_secret,
            password=password,
        )
    except Exception as e:
        logger.error(f"Failed to create CCXT client for {exchange_id}: {e}")
        return None
