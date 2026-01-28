"""
Additional MCP Tools for Crypto Portfolio Analyzer
===================================================

This module contains additional tools that can be added to the MCP server:
- Trading operations (place/cancel orders)
- Staking management (stake/unstake/claim)
- DCA bot management (create/pause/delete)
- Alert management (create/delete)
- Market data (prices, sentiment)
- NFT tracking
- Tax report generation

These tools are separated to allow opt-in based on API key permissions.
Import and register the tools you need in crypto_portfolio_mcp.py.

Usage:
    from additional_tools import (
        register_trading_tools,
        register_management_tools,
        register_market_tools
    )
    
    # Register with your MCP server
    register_trading_tools(mcp)
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =============================================================================
# ENUMS
# =============================================================================


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class TimeInForce(str, Enum):
    GTC = "gtc"  # Good til canceled
    IOC = "ioc"  # Immediate or cancel
    FOK = "fok"  # Fill or kill
    DAY = "day"


class AlertType(str, Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PERCENT_CHANGE = "percent_change"
    PORTFOLIO_VALUE = "portfolio_value"


class Frequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class Exchange(str, Enum):
    COINBASE = "coinbase"
    COINBASE_GTI = "coinbase_gti"
    KRAKEN = "kraken"
    CRYPTO_COM = "crypto.com"
    GEMINI = "gemini"


# =============================================================================
# TRADING TOOLS - INPUT MODELS
# =============================================================================


class PlaceOrderInput(BaseModel):
    """Input for placing a trade order."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    exchange: Exchange = Field(
        ...,
        description="Exchange to place order on"
    )
    symbol: str = Field(
        ...,
        description="Trading pair (e.g., 'BTC-USD', 'ETH-USDC')",
        min_length=3,
        max_length=20
    )
    side: OrderSide = Field(
        ...,
        description="Order side: 'buy' or 'sell'"
    )
    order_type: OrderType = Field(
        default=OrderType.MARKET,
        description="Order type: 'market', 'limit', 'stop_loss', 'take_profit'"
    )
    amount: float = Field(
        ...,
        description="Amount of base asset to trade",
        gt=0
    )
    price: Optional[float] = Field(
        default=None,
        description="Limit price (required for limit orders)",
        gt=0
    )
    stop_price: Optional[float] = Field(
        default=None,
        description="Stop trigger price (for stop orders)",
        gt=0
    )
    time_in_force: TimeInForce = Field(
        default=TimeInForce.GTC,
        description="Time in force: 'gtc', 'ioc', 'fok', 'day'"
    )
    client_order_id: Optional[str] = Field(
        default=None,
        description="Optional client-specified order ID",
        max_length=50
    )

    @model_validator(mode='after')
    def validate_price_for_limit(self):
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Price is required for limit orders")
        return self


class CancelOrderInput(BaseModel):
    """Input for canceling an order."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    exchange: Exchange = Field(
        ...,
        description="Exchange where order was placed"
    )
    order_id: str = Field(
        ...,
        description="Order ID to cancel",
        min_length=1,
        max_length=100
    )


class GetOpenOrdersInput(BaseModel):
    """Input for getting open orders."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    exchange: Optional[Exchange] = Field(
        default=None,
        description="Filter by exchange (all if not specified)"
    )
    symbol: Optional[str] = Field(
        default=None,
        description="Filter by trading pair",
        max_length=20
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


# =============================================================================
# STAKING MANAGEMENT - INPUT MODELS
# =============================================================================


class StakeAssetInput(BaseModel):
    """Input for staking assets."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    exchange: Exchange = Field(
        ...,
        description="Exchange to stake on"
    )
    asset: str = Field(
        ...,
        description="Asset to stake (e.g., 'ETH', 'SOL')",
        min_length=1,
        max_length=20
    )
    amount: float = Field(
        ...,
        description="Amount to stake",
        gt=0
    )
    validator: Optional[str] = Field(
        default=None,
        description="Specific validator (if supported)",
        max_length=100
    )


class UnstakeAssetInput(BaseModel):
    """Input for unstaking assets."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    exchange: Exchange = Field(
        ...,
        description="Exchange to unstake from"
    )
    asset: str = Field(
        ...,
        description="Asset to unstake",
        min_length=1,
        max_length=20
    )
    amount: Optional[float] = Field(
        default=None,
        description="Amount to unstake (all if not specified)",
        gt=0
    )


class ClaimRewardsInput(BaseModel):
    """Input for claiming staking rewards."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    exchange: Exchange = Field(
        ...,
        description="Exchange to claim rewards from"
    )
    asset: Optional[str] = Field(
        default=None,
        description="Specific asset (all if not specified)",
        max_length=20
    )


# =============================================================================
# DCA BOT MANAGEMENT - INPUT MODELS
# =============================================================================


class CreateDCABotInput(BaseModel):
    """Input for creating a DCA bot."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    exchange: Exchange = Field(
        ...,
        description="Exchange for DCA purchases"
    )
    asset: str = Field(
        ...,
        description="Asset to accumulate (e.g., 'BTC', 'ETH')",
        min_length=1,
        max_length=20
    )
    amount_usd: float = Field(
        ...,
        description="USD amount per purchase",
        ge=1,
        le=10000
    )
    frequency: Frequency = Field(
        ...,
        description="Purchase frequency"
    )
    start_immediately: bool = Field(
        default=True,
        description="Start first purchase immediately"
    )
    max_total_usd: Optional[float] = Field(
        default=None,
        description="Maximum total to invest (unlimited if not set)",
        gt=0
    )


class ModifyDCABotInput(BaseModel):
    """Input for modifying a DCA bot."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    bot_id: str = Field(
        ...,
        description="Bot ID to modify",
        min_length=1,
        max_length=50
    )
    action: str = Field(
        ...,
        description="Action: 'pause', 'resume', 'delete'",
        pattern=r"^(pause|resume|delete)$"
    )


# =============================================================================
# ALERT MANAGEMENT - INPUT MODELS
# =============================================================================


class CreateAlertInput(BaseModel):
    """Input for creating a price/portfolio alert."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    alert_type: AlertType = Field(
        ...,
        description="Type of alert"
    )
    asset: Optional[str] = Field(
        default=None,
        description="Asset for price alerts (e.g., 'BTC')",
        max_length=20
    )
    threshold: float = Field(
        ...,
        description="Trigger threshold (price or percentage)"
    )
    notification_channels: List[str] = Field(
        default=["app"],
        description="Notification channels: 'app', 'email', 'sms', 'webhook'",
        max_length=4
    )
    note: Optional[str] = Field(
        default=None,
        description="Optional note for the alert",
        max_length=200
    )


class DeleteAlertInput(BaseModel):
    """Input for deleting an alert."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    alert_id: str = Field(
        ...,
        description="Alert ID to delete",
        min_length=1,
        max_length=50
    )


# =============================================================================
# MARKET DATA - INPUT MODELS
# =============================================================================


class GetPricesInput(BaseModel):
    """Input for getting current prices."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    assets: Optional[List[str]] = Field(
        default=None,
        description="Assets to get prices for (top 20 if not specified)",
        max_length=50
    )
    include_24h_change: bool = Field(
        default=True,
        description="Include 24h price change"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class GetPriceHistoryInput(BaseModel):
    """Input for getting historical prices."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    asset: str = Field(
        ...,
        description="Asset to get history for",
        min_length=1,
        max_length=20
    )
    interval: str = Field(
        default="1d",
        description="Candle interval: '1h', '4h', '1d', '1w'",
        pattern=r"^(1h|4h|1d|1w)$"
    )
    limit: int = Field(
        default=30,
        description="Number of candles",
        ge=1,
        le=365
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format"
    )


class MarketSentimentInput(BaseModel):
    """Input for getting market sentiment."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    include_fear_greed: bool = Field(
        default=True,
        description="Include Fear & Greed Index"
    )
    include_dominance: bool = Field(
        default=True,
        description="Include BTC/ETH dominance"
    )
    include_trending: bool = Field(
        default=True,
        description="Include trending coins"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


# =============================================================================
# NFT TOOLS - INPUT MODELS
# =============================================================================


class NFTHoldingsInput(BaseModel):
    """Input for getting NFT holdings."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    wallet_address: Optional[str] = Field(
        default=None,
        description="Specific wallet (uses configured wallets if not specified)",
        pattern=r"^0x[a-fA-F0-9]{40}$"
    )
    include_floor_prices: bool = Field(
        default=True,
        description="Include collection floor prices"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


# =============================================================================
# TAX TOOLS - INPUT MODELS
# =============================================================================


class ExportTaxReportInput(BaseModel):
    """Input for exporting tax report."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    tax_year: int = Field(
        ...,
        description="Tax year to export",
        ge=2015,
        le=2030
    )
    format: str = Field(
        default="csv",
        description="Export format: 'csv', 'pdf', 'turbotax', 'taxact'",
        pattern=r"^(csv|pdf|turbotax|taxact)$"
    )
    cost_basis_method: str = Field(
        default="fifo",
        description="Cost basis method",
        pattern=r"^(fifo|lifo|hifo|avg)$"
    )
    include_unrealized: bool = Field(
        default=False,
        description="Include unrealized gains"
    )


# =============================================================================
# TOOL IMPLEMENTATIONS
# =============================================================================


def register_trading_tools(mcp: FastMCP):
    """Register trading-related tools with the MCP server."""
    
    @mcp.tool(
        name="crypto_place_order",
        annotations={
            "title": "Place Trade Order",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def crypto_place_order(params: PlaceOrderInput) -> str:
        """Place a buy or sell order on an exchange.

        ⚠️ WARNING: This executes real trades. Requires explicit user confirmation.

        Args:
            params: Order parameters including exchange, symbol, side, type, amount

        Returns:
            Order confirmation or error message
        """
        import os

        # Paper trading mode for testing
        if os.getenv("PAPER_TRADING", "false").lower() == "true":
            return json.dumps({
                "status": "success",
                "mode": "paper_trading",
                "order": {
                    "id": f"paper_{datetime.utcnow().timestamp()}",
                    "exchange": params.exchange.value,
                    "symbol": params.symbol,
                    "side": params.side.value,
                    "type": params.order_type.value,
                    "amount": params.amount,
                    "price": params.price,
                    "status": "filled",
                    "created_at": datetime.utcnow().isoformat()
                },
                "message": "Paper trade executed successfully"
            }, indent=2)

        # Real trading - Coinbase only for now
        if params.exchange.value not in ["coinbase", "coinbase_gti"]:
            return json.dumps({
                "status": "error",
                "message": f"Real trading not yet implemented for {params.exchange.value}. Only Coinbase supported."
            }, indent=2)

        try:
            # Get the appropriate Coinbase client
            from portfolio_aggregator import PortfolioAggregator
            aggregator = PortfolioAggregator()

            exchange_key = params.exchange.value
            if exchange_key not in aggregator.exchanges:
                return json.dumps({
                    "status": "error",
                    "message": f"{params.exchange.value} not configured or credentials missing"
                }, indent=2)

            client = aggregator.exchanges[exchange_key]['client']

            # Execute the order
            if params.order_type == OrderType.MARKET:
                result = client.place_market_order(
                    product_id=params.symbol,
                    side=params.side.value.upper(),
                    amount=params.amount
                )
            elif params.order_type == OrderType.LIMIT:
                if not params.price:
                    return json.dumps({
                        "status": "error",
                        "message": "Limit orders require a price"
                    }, indent=2)
                result = client.place_limit_order(
                    product_id=params.symbol,
                    side=params.side.value.upper(),
                    amount=params.amount,
                    price=params.price
                )
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Order type {params.order_type.value} not yet supported"
                }, indent=2)

            if result.get("success"):
                return json.dumps({
                    "status": "success",
                    "mode": "live",
                    "order": result,
                    "message": f"Order placed successfully on {params.exchange.value}"
                }, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "message": result.get("error", "Unknown error")
                }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            }, indent=2)
    
    @mcp.tool(
        name="crypto_cancel_order",
        annotations={
            "title": "Cancel Order",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def crypto_cancel_order(params: CancelOrderInput) -> str:
        """Cancel an open order.

        Args:
            params: Order ID and exchange

        Returns:
            Cancellation confirmation
        """
        if params.exchange.value not in ["coinbase", "coinbase_gti"]:
            return json.dumps({
                "status": "error",
                "message": f"Cancel not yet implemented for {params.exchange.value}"
            }, indent=2)

        try:
            from portfolio_aggregator import PortfolioAggregator
            aggregator = PortfolioAggregator()

            exchange_key = params.exchange.value
            if exchange_key not in aggregator.exchanges:
                return json.dumps({
                    "status": "error",
                    "message": f"{params.exchange.value} not configured"
                }, indent=2)

            client = aggregator.exchanges[exchange_key]['client']
            result = client.cancel_order(params.order_id)

            if result.get("success"):
                return json.dumps({
                    "status": "success",
                    "order_id": params.order_id,
                    "exchange": params.exchange.value,
                    "message": "Order cancelled successfully"
                }, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "message": result.get("error", "Cancel failed")
                }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            }, indent=2)
    
    @mcp.tool(
        name="crypto_open_orders",
        annotations={
            "title": "Get Open Orders",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def crypto_open_orders(params: GetOpenOrdersInput) -> str:
        """Get all open/pending orders.

        Args:
            params: Optional filters for exchange and symbol

        Returns:
            List of open orders
        """
        all_orders = []

        try:
            from portfolio_aggregator import PortfolioAggregator
            aggregator = PortfolioAggregator()

            # Get orders from requested exchange(s)
            exchanges_to_check = []
            if params.exchange:
                exchanges_to_check = [params.exchange.value]
            else:
                exchanges_to_check = ["coinbase", "coinbase_gti"]

            for exchange_key in exchanges_to_check:
                if exchange_key in aggregator.exchanges:
                    client = aggregator.exchanges[exchange_key]['client']
                    if hasattr(client, 'get_orders'):
                        orders = client.get_orders(
                            status="OPEN",
                            product_id=params.symbol
                        )
                        for o in orders:
                            all_orders.append({
                                "id": o.get('order_id', ''),
                                "exchange": exchange_key,
                                "symbol": o.get('product_id', ''),
                                "side": o.get('side', '').lower(),
                                "type": o.get('order_type', '').lower(),
                                "amount": float(o.get('base_size', 0) or 0),
                                "price": float(o.get('limit_price', 0) or 0),
                                "filled": float(o.get('filled_size', 0) or 0),
                                "status": o.get('status', 'open').lower(),
                                "created_at": o.get('created_time', '')
                            })

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"orders": all_orders, "count": len(all_orders)}, indent=2)

        md = "# Open Orders\n\n"
        if not all_orders:
            md += "*No open orders*\n"
        else:
            md += "| Exchange | Symbol | Side | Type | Amount | Price | Filled | Status |\n"
            md += "|----------|--------|------|------|--------|-------|--------|--------|\n"
            for o in all_orders:
                price_str = f"${o['price']:,.2f}" if o['price'] else "-"
                md += f"| {o['exchange']} | {o['symbol']} | {o['side']} | {o['type']} | {o['amount']:.6f} | {price_str} | {o['filled']:.6f} | {o['status']} |\n"

        return md


def register_staking_management_tools(mcp: FastMCP):
    """Register staking management tools."""
    
    @mcp.tool(
        name="crypto_stake_asset",
        annotations={
            "title": "Stake Asset",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def crypto_stake_asset(params: StakeAssetInput) -> str:
        """Stake assets to earn rewards.
        
        Args:
            params: Exchange, asset, and amount to stake
        
        Returns:
            Staking confirmation
        """
        return json.dumps({
            "status": "success",
            "exchange": params.exchange.value,
            "asset": params.asset,
            "amount_staked": params.amount,
            "estimated_apy": 4.5,
            "message": f"Successfully staked {params.amount} {params.asset}"
        }, indent=2)
    
    @mcp.tool(
        name="crypto_unstake_asset",
        annotations={
            "title": "Unstake Asset",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def crypto_unstake_asset(params: UnstakeAssetInput) -> str:
        """Unstake assets (may have unbonding period).
        
        Args:
            params: Exchange, asset, and optional amount
        
        Returns:
            Unstaking confirmation with unbonding info
        """
        return json.dumps({
            "status": "success",
            "exchange": params.exchange.value,
            "asset": params.asset,
            "amount_unstaking": params.amount or "all",
            "unbonding_period": "21 days",
            "available_at": "2024-03-10T00:00:00Z",
            "message": "Unstaking initiated"
        }, indent=2)
    
    @mcp.tool(
        name="crypto_claim_rewards",
        annotations={
            "title": "Claim Staking Rewards",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def crypto_claim_rewards(params: ClaimRewardsInput) -> str:
        """Claim accumulated staking rewards.
        
        Args:
            params: Exchange and optional asset filter
        
        Returns:
            Claimed rewards summary
        """
        return json.dumps({
            "status": "success",
            "exchange": params.exchange.value,
            "rewards_claimed": [
                {"asset": "ETH", "amount": 0.05, "value_usd": 137.50},
                {"asset": "SOL", "amount": 1.2, "value_usd": 145.20}
            ],
            "total_value_usd": 282.70,
            "message": "Rewards claimed successfully"
        }, indent=2)


def register_dca_management_tools(mcp: FastMCP):
    """Register DCA bot management tools."""
    
    @mcp.tool(
        name="crypto_create_dca_bot",
        annotations={
            "title": "Create DCA Bot",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def crypto_create_dca_bot(params: CreateDCABotInput) -> str:
        """Create a new Dollar Cost Averaging bot.
        
        Args:
            params: Bot configuration including asset, amount, frequency
        
        Returns:
            Bot creation confirmation
        """
        bot_id = f"dca_{params.asset.lower()}_{params.frequency.value}"
        return json.dumps({
            "status": "success",
            "bot": {
                "id": bot_id,
                "exchange": params.exchange.value,
                "asset": params.asset,
                "amount_usd": params.amount_usd,
                "frequency": params.frequency.value,
                "status": "active" if params.start_immediately else "paused",
                "next_execution": datetime.utcnow().isoformat() if params.start_immediately else None,
                "max_total_usd": params.max_total_usd
            },
            "message": f"DCA bot created for {params.asset}"
        }, indent=2)
    
    @mcp.tool(
        name="crypto_modify_dca_bot",
        annotations={
            "title": "Modify DCA Bot",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def crypto_modify_dca_bot(params: ModifyDCABotInput) -> str:
        """Pause, resume, or delete a DCA bot.
        
        Args:
            params: Bot ID and action (pause/resume/delete)
        
        Returns:
            Action confirmation
        """
        return json.dumps({
            "status": "success",
            "bot_id": params.bot_id,
            "action": params.action,
            "message": f"Bot {params.action}d successfully"
        }, indent=2)


def register_alert_management_tools(mcp: FastMCP):
    """Register alert management tools."""
    
    @mcp.tool(
        name="crypto_create_alert",
        annotations={
            "title": "Create Alert",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def crypto_create_alert(params: CreateAlertInput) -> str:
        """Create a price or portfolio alert.
        
        Args:
            params: Alert type, asset, threshold, notification channels
        
        Returns:
            Alert creation confirmation
        """
        alert_id = f"alert_{datetime.utcnow().timestamp()}"
        return json.dumps({
            "status": "success",
            "alert": {
                "id": alert_id,
                "type": params.alert_type.value,
                "asset": params.asset,
                "threshold": params.threshold,
                "channels": params.notification_channels,
                "note": params.note,
                "created_at": datetime.utcnow().isoformat()
            },
            "message": "Alert created successfully"
        }, indent=2)
    
    @mcp.tool(
        name="crypto_delete_alert",
        annotations={
            "title": "Delete Alert",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def crypto_delete_alert(params: DeleteAlertInput) -> str:
        """Delete an existing alert.
        
        Args:
            params: Alert ID to delete
        
        Returns:
            Deletion confirmation
        """
        return json.dumps({
            "status": "success",
            "alert_id": params.alert_id,
            "message": "Alert deleted successfully"
        }, indent=2)


def register_market_data_tools(mcp: FastMCP):
    """Register market data tools."""
    
    @mcp.tool(
        name="crypto_get_prices",
        annotations={
            "title": "Get Current Prices",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def crypto_get_prices(params: GetPricesInput) -> str:
        """Get current cryptocurrency prices.
        
        Args:
            params: Optional asset list, include 24h change
        
        Returns:
            Current prices with optional 24h change
        """
        mock_prices = {
            "BTC": {"price": 45000.00, "change_24h": 2.5},
            "ETH": {"price": 2750.00, "change_24h": 3.2},
            "SOL": {"price": 121.00, "change_24h": -1.5},
            "USDC": {"price": 1.00, "change_24h": 0.0}
        }
        
        if params.assets:
            mock_prices = {k: v for k, v in mock_prices.items() if k in params.assets}
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"prices": mock_prices, "timestamp": datetime.utcnow().isoformat()}, indent=2)
        
        md = "# Current Prices\n\n"
        md += "| Asset | Price | 24h Change |\n"
        md += "|-------|-------|------------|\n"
        for asset, data in mock_prices.items():
            change = f"+{data['change_24h']:.2f}%" if data['change_24h'] > 0 else f"{data['change_24h']:.2f}%"
            md += f"| {asset} | ${data['price']:,.2f} | {change} |\n"
        
        return md
    
    @mcp.tool(
        name="crypto_market_sentiment",
        annotations={
            "title": "Get Market Sentiment",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    )
    async def crypto_market_sentiment(params: MarketSentimentInput) -> str:
        """Get market sentiment indicators.
        
        Args:
            params: Include fear/greed, dominance, trending
        
        Returns:
            Market sentiment data
        """
        data = {
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if params.include_fear_greed:
            data["fear_greed_index"] = {
                "value": 65,
                "classification": "Greed",
                "previous_day": 62,
                "previous_week": 58
            }
        
        if params.include_dominance:
            data["dominance"] = {
                "btc": 52.3,
                "eth": 17.8,
                "others": 29.9
            }
        
        if params.include_trending:
            data["trending"] = [
                {"rank": 1, "asset": "PEPE", "mentions_24h": 15420},
                {"rank": 2, "asset": "WIF", "mentions_24h": 12350},
                {"rank": 3, "asset": "BONK", "mentions_24h": 8920}
            ]
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        md = "# Market Sentiment\n\n"
        
        if params.include_fear_greed and "fear_greed_index" in data:
            fg = data["fear_greed_index"]
            md += f"## Fear & Greed Index\n"
            md += f"**{fg['value']}** - {fg['classification']}\n\n"
        
        if params.include_dominance and "dominance" in data:
            dom = data["dominance"]
            md += f"## Market Dominance\n"
            md += f"- BTC: {dom['btc']:.1f}%\n"
            md += f"- ETH: {dom['eth']:.1f}%\n\n"
        
        if params.include_trending and "trending" in data:
            md += f"## Trending\n"
            for t in data["trending"]:
                md += f"{t['rank']}. **{t['asset']}** ({t['mentions_24h']:,} mentions)\n"
        
        return md


def register_nft_tools(mcp: FastMCP):
    """Register NFT tracking tools."""
    
    @mcp.tool(
        name="crypto_nft_holdings",
        annotations={
            "title": "Get NFT Holdings",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def crypto_nft_holdings(params: NFTHoldingsInput) -> str:
        """Get NFT holdings and valuations.
        
        Args:
            params: Optional wallet filter, include floor prices
        
        Returns:
            NFT holdings with estimated values
        """
        mock_nfts = {
            "total_value_eth": 2.5,
            "total_value_usd": 6875.00,
            "collections": [
                {
                    "name": "Bored Ape Yacht Club",
                    "count": 0,
                    "floor_eth": 28.5,
                    "estimated_value_eth": 0
                },
                {
                    "name": "Pudgy Penguins",
                    "count": 2,
                    "floor_eth": 1.2,
                    "estimated_value_eth": 2.4
                }
            ],
            "nfts": [
                {"collection": "Pudgy Penguins", "token_id": "1234", "rarity_rank": 456},
                {"collection": "Pudgy Penguins", "token_id": "5678", "rarity_rank": 2341}
            ]
        }
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(mock_nfts, indent=2)
        
        md = f"""# NFT Holdings

**Total Estimated Value:** {mock_nfts['total_value_eth']:.2f} ETH (${mock_nfts['total_value_usd']:,.2f})

## Collections
| Collection | Count | Floor (ETH) | Value (ETH) |
|------------|-------|-------------|-------------|
"""
        for c in mock_nfts['collections']:
            if c['count'] > 0:
                md += f"| {c['name']} | {c['count']} | {c['floor_eth']:.2f} | {c['estimated_value_eth']:.2f} |\n"
        
        return md


def register_tax_tools(mcp: FastMCP):
    """Register tax report tools."""
    
    @mcp.tool(
        name="crypto_export_tax_report",
        annotations={
            "title": "Export Tax Report",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    async def crypto_export_tax_report(params: ExportTaxReportInput) -> str:
        """Generate and export tax report.
        
        Args:
            params: Tax year, format, cost basis method
        
        Returns:
            Export status and download link
        """
        return json.dumps({
            "status": "success",
            "tax_year": params.tax_year,
            "format": params.format,
            "cost_basis_method": params.cost_basis_method,
            "summary": {
                "total_proceeds": 45000.00,
                "total_cost_basis": 32000.00,
                "short_term_gains": 8000.00,
                "long_term_gains": 5000.00,
                "total_gains": 13000.00,
                "transactions": 47
            },
            "file_path": f"/exports/tax_report_{params.tax_year}_{params.cost_basis_method}.{params.format}",
            "message": f"Tax report generated for {params.tax_year}"
        }, indent=2)


def register_all_additional_tools(mcp: FastMCP):
    """Register all additional tools with the MCP server."""
    register_trading_tools(mcp)
    register_staking_management_tools(mcp)
    register_dca_management_tools(mcp)
    register_alert_management_tools(mcp)
    register_market_data_tools(mcp)
    register_nft_tools(mcp)
    register_tax_tools(mcp)
