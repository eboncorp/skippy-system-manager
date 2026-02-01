#!/usr/bin/env python3
"""
MCP Server for Crypto Portfolio Manager.

Exposes portfolio management tools to Claude Code via the Model Context Protocol.
This allows Claude to directly query and manage your portfolio.

Run with: python mcp_server.py
Or add to Claude Code config.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from config import settings, TARGET_ALLOCATION, calculate_blended_yield
from exchanges import CoinbaseClient, CoinbasePrimeClient, KrakenClient
from data.prices import PriceService
from data.storage import db
from tracking.portfolio import Portfolio
from tracking.staking import StakingTracker
from agents.rebalancer import Rebalancer
from agents.dca import DCAAgent
from agents.market_intel import MarketIntelAgent


# Initialize MCP server
server = Server("crypto-portfolio")

# Global state
_exchanges = {}
_clients = []
_price_service = None
_portfolio = None


def _init_clients():
    """Initialize exchange clients."""
    global _exchanges, _clients, _price_service, _portfolio

    _clients = []
    _exchanges = {}

    if settings.coinbase.is_configured:
        client = CoinbaseClient(
            settings.coinbase.api_key,
            settings.coinbase.api_secret,
        )
        _exchanges["coinbase"] = client
        _clients.append(client)

    if settings.coinbase_prime.is_configured:
        client = CoinbasePrimeClient(
            settings.coinbase_prime.api_key,
            settings.coinbase_prime.api_secret,
            settings.coinbase_prime.passphrase,
            settings.coinbase_prime.portfolio_id,
        )
        _exchanges["coinbase_prime"] = client
        _clients.append(client)

    if settings.kraken.is_configured:
        client = KrakenClient(
            settings.kraken.api_key,
            settings.kraken.api_secret,
        )
        _exchanges["kraken"] = client
        _clients.append(client)

    _price_service = PriceService()
    _portfolio = Portfolio(_clients, _price_service, TARGET_ALLOCATION)


def _json_serialize(obj: Any) -> Any:
    """Serialize objects for JSON output."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__dict__"):
        return {k: _json_serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if isinstance(obj, dict):
        return {k: _json_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_serialize(v) for v in obj]
    return obj


# =============================================================================
# MCP TOOLS
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available portfolio management tools."""
    return [
        Tool(
            name="portfolio_sync",
            description="Sync and get current portfolio state including all balances, allocations, and drift analysis",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="portfolio_summary",
            description="Get a formatted summary of current portfolio holdings and allocation",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="check_drift",
            description="Check if portfolio needs rebalancing based on drift threshold",
            inputSchema={
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "number",
                        "description": "Drift threshold percentage (default 5%)",
                        "default": 0.05,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="plan_rebalance",
            description="Generate a rebalancing plan showing what trades would bring portfolio back to target allocation",
            inputSchema={
                "type": "object",
                "properties": {
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true (default), only plan trades without executing",
                        "default": True,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="dca_status",
            description="Get DCA status including daily allocation and whether today's DCA has been executed",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="execute_dca",
            description="Execute DCA purchases for today. Use dry_run=true to preview without executing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true (default), simulate without executing trades",
                        "default": True,
                    },
                    "assets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of specific assets to buy (default: all in allocation)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="dca_performance",
            description="Get DCA performance statistics showing total invested, current value, and gains/losses",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: all time)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="staking_rewards",
            description="Get staking rewards summary for a time period",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 30)",
                        "default": 30,
                    },
                    "asset": {
                        "type": "string",
                        "description": "Optional: filter by specific asset",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="staking_sync",
            description="Sync staking rewards from all exchanges",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="market_overview",
            description="Get market overview including Fear & Greed Index, BTC dominance, and asset metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "assets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of assets to get detailed metrics for",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_price",
            description="Get current price for one or more assets",
            inputSchema={
                "type": "object",
                "properties": {
                    "assets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of asset symbols (e.g., ['BTC', 'ETH'])",
                    },
                },
                "required": ["assets"],
            },
        ),
        Tool(
            name="target_allocation",
            description="Get current target allocation configuration",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="expected_yield",
            description="Calculate expected annual yield from staking based on current holdings",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="portfolio_history",
            description="Get historical portfolio snapshots",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 7)",
                        "default": 7,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of snapshots to return (default: 50)",
                        "default": 50,
                    },
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a portfolio management tool."""

    # Initialize clients if needed
    if not _clients:
        _init_clients()

    try:
        result = await _execute_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _execute_tool(name: str, arguments: dict) -> dict:
    """Execute a specific tool and return results."""

    if name == "portfolio_sync":
        snapshot = await _portfolio.sync()
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "total_usd_value": float(snapshot.total_usd_value),
            "total_staked_value": float(snapshot.total_staked_value),
            "expected_annual_yield": float(snapshot.expected_annual_yield),
            "positions": {
                asset: {
                    "amount": float(pos.total_amount),
                    "staked": float(pos.staked_amount),
                    "usd_value": float(pos.usd_value),
                    "price": float(pos.price),
                    "allocation_pct": float(snapshot.actual_allocation.get(asset, 0)) * 100,
                    "target_pct": TARGET_ALLOCATION.get(asset, 0) * 100,
                    "drift_pct": float(snapshot.drift.get(asset, 0)) * 100,
                }
                for asset, pos in snapshot.positions.items()
                if pos.usd_value > 1
            },
            "needs_rebalance": snapshot.needs_rebalance(),
        }

    elif name == "portfolio_summary":
        snapshot = await _portfolio.sync()
        return {"summary": _portfolio.format_summary(snapshot)}

    elif name == "check_drift":
        threshold = arguments.get("threshold", 0.05)
        snapshot = await _portfolio.sync()
        drift_status = snapshot.get_drift_status(threshold)

        out_of_balance = [
            {"asset": asset, "status": status, "drift_pct": float(snapshot.drift.get(asset, 0)) * 100}
            for asset, status in drift_status.items()
            if status != "OK"
        ]

        return {
            "needs_rebalance": snapshot.needs_rebalance(threshold),
            "threshold_pct": threshold * 100,
            "out_of_balance_assets": out_of_balance,
            "max_drift_pct": max(abs(float(d)) for d in snapshot.drift.values()) * 100,
        }

    elif name == "plan_rebalance":
        dry_run = arguments.get("dry_run", True)
        rebalancer = Rebalancer(_portfolio, _exchanges)
        session = await rebalancer.rebalance(dry_run=dry_run)

        return {
            "status": session.status,
            "trades": [
                {
                    "asset": t.asset,
                    "side": t.side,
                    "usd_amount": float(t.usd_amount),
                    "exchange": t.exchange,
                    "status": t.status,
                }
                for t in session.trades
            ],
            "total_sell_volume": float(session.total_sell_volume),
            "total_buy_volume": float(session.total_buy_volume),
            "dry_run": dry_run,
        }

    elif name == "dca_status":
        dca_agent = DCAAgent(_exchanges, _price_service)
        allocations = dca_agent.get_daily_allocation()

        return {
            "daily_amount": float(dca_agent.daily_amount),
            "should_execute_today": dca_agent.should_execute_today(),
            "allocation": {asset: float(amount) for asset, amount in allocations.items()},
        }

    elif name == "execute_dca":
        dry_run = arguments.get("dry_run", True)
        assets = arguments.get("assets")

        dca_agent = DCAAgent(_exchanges, _price_service)
        executions = await dca_agent.execute_dca(dry_run=dry_run, assets=assets)

        return {
            "dry_run": dry_run,
            "executions": [
                {
                    "asset": e.asset,
                    "usd_amount": float(e.usd_amount),
                    "filled_amount": float(e.filled_amount) if e.filled_amount else None,
                    "filled_price": float(e.filled_price) if e.filled_price else None,
                    "status": e.status,
                    "error": e.error,
                }
                for e in executions
            ],
            "total_invested": sum(float(e.usd_amount) for e in executions if e.status in ("executed", "dry_run")),
        }

    elif name == "dca_performance":
        days = arguments.get("days")
        start_date = datetime.now() - timedelta(days=days) if days else None

        dca_agent = DCAAgent(_exchanges, _price_service)
        stats = await dca_agent.get_stats(start_date=start_date)

        return {
            "total_invested": float(stats.total_invested),
            "current_value": float(stats.total_value_now),
            "gain_loss": float(stats.total_gain_loss),
            "gain_loss_pct": float(stats.gain_loss_pct),
            "execution_count": stats.execution_count,
            "by_asset": {
                asset: {
                    "invested": float(data["invested"]),
                    "current_value": float(data["current_value"]),
                    "gain_loss": float(data["gain_loss"]),
                    "gain_loss_pct": float(data["gain_loss_pct"]),
                    "avg_cost": float(data["avg_cost"]),
                }
                for asset, data in stats.by_asset.items()
            },
        }

    elif name == "staking_rewards":
        days = arguments.get("days", 30)
        asset = arguments.get("asset")

        start_date = datetime.now() - timedelta(days=days)
        tracker = StakingTracker(_clients, _price_service)
        summary = tracker.get_summary(start_date=start_date)

        if asset:
            rewards = tracker.get_rewards(start_date=start_date, asset=asset)
            return {
                "asset": asset,
                "total_usd_value": float(summary.by_asset.get(asset, 0)),
                "reward_count": len(rewards),
                "rewards": [
                    {
                        "amount": float(r.amount),
                        "usd_value": float(r.usd_value_at_receipt),
                        "timestamp": r.timestamp.isoformat(),
                        "source": r.source,
                    }
                    for r in rewards[-20:]  # Last 20
                ],
            }

        return {
            "period_days": days,
            "total_usd_value": float(summary.total_usd_value),
            "reward_count": summary.reward_count,
            "by_asset": {asset: float(value) for asset, value in summary.by_asset.items()},
            "by_source": {source: float(value) for source, value in summary.by_source.items()},
        }

    elif name == "staking_sync":
        tracker = StakingTracker(_clients, _price_service)
        count = await tracker.sync_rewards()
        return {"new_rewards_added": count}

    elif name == "market_overview":
        assets = arguments.get("assets", ["BTC", "ETH", "SOL"])
        agent = MarketIntelAgent()

        try:
            overview = await agent.get_market_overview(assets)
            return {
                "timestamp": overview.timestamp.isoformat(),
                "fear_greed_index": overview.fear_greed_index,
                "fear_greed_label": overview.fear_greed_label,
                "btc_dominance": overview.btc_dominance,
                "total_market_cap": overview.total_market_cap,
                "total_volume_24h": overview.total_volume_24h,
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "change_24h": m.change_24h,
                        "signal": m.signal,
                    }
                    for m in overview.metrics
                ],
            }
        finally:
            await agent.close()

    elif name == "get_price":
        assets = arguments.get("assets", [])
        prices = await _price_service.get_prices(assets)
        return {asset: float(price) for asset, price in prices.items()}

    elif name == "target_allocation":
        return {
            "allocation": {asset: pct * 100 for asset, pct in TARGET_ALLOCATION.items()},
            "expected_blended_yield_pct": calculate_blended_yield() * 100,
        }

    elif name == "expected_yield":
        snapshot = await _portfolio.sync()
        return {
            "total_staked_value": float(snapshot.total_staked_value),
            "expected_annual_yield": float(snapshot.expected_annual_yield),
            "yield_pct": float(snapshot.expected_annual_yield / snapshot.total_staked_value * 100) if snapshot.total_staked_value > 0 else 0,
        }

    elif name == "portfolio_history":
        days = arguments.get("days", 7)
        limit = arguments.get("limit", 50)
        start_date = datetime.now() - timedelta(days=days)

        snapshots = db.get_snapshots(start_date=start_date, limit=limit)

        return {
            "period_days": days,
            "snapshot_count": len(snapshots),
            "snapshots": [
                {
                    "timestamp": s["timestamp"].isoformat(),
                    "total_usd_value": float(s["total_usd_value"]),
                    "total_staked_value": float(s["total_staked_value"]),
                }
                for s in snapshots
            ],
        }

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
