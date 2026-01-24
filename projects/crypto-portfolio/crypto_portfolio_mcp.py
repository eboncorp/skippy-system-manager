#!/usr/bin/env python3
"""
Crypto Portfolio MCP Server
===========================

An MCP server that enables Claude Code and other LLM clients to interact with
the multi-exchange cryptocurrency portfolio analyzer. Provides tools for
portfolio analysis, trading, staking, DeFi tracking, and AI-powered insights.

Usage:
    # stdio transport (for Claude Code local integration)
    python crypto_portfolio_mcp.py
    
    # HTTP transport (for remote access)
    python crypto_portfolio_mcp.py --http --port 8080

Author: Dave's Campaign Dev Team
License: MIT
"""

import json
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Crypto.com AI Agent SDK (optional - for Cronos blockchain operations)
try:
    from crypto_com_ai_agent_client import Agent as CryptoComAgent
    CRYPTO_COM_AGENT_AVAILABLE = True
except ImportError:
    CRYPTO_COM_AGENT_AVAILABLE = False

# Portfolio aggregator for real exchange data
try:
    from portfolio_aggregator import PortfolioAggregator
    PORTFOLIO_AGGREGATOR_AVAILABLE = True
except ImportError:
    PORTFOLIO_AGGREGATOR_AVAILABLE = False

# Global aggregator instance (initialized in lifespan)
_aggregator: Optional["PortfolioAggregator"] = None

# =============================================================================
# CONFIGURATION
# =============================================================================

# Supported exchanges
SUPPORTED_EXCHANGES = ["coinbase", "kraken", "crypto.com", "gemini"]

# Supported DeFi protocols
SUPPORTED_DEFI_PROTOCOLS = ["aave", "uniswap", "lido", "compound", "curve"]

# Cost basis methods
COST_BASIS_METHODS = ["fifo", "lifo", "hifo", "avg"]

# Default pagination
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# =============================================================================
# PYDANTIC MODELS FOR INPUT VALIDATION
# =============================================================================


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class Exchange(str, Enum):
    """Supported cryptocurrency exchanges."""
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    CRYPTO_COM = "crypto.com"
    GEMINI = "gemini"
    ALL = "all"


class CostBasisMethod(str, Enum):
    """Tax lot identification methods."""
    FIFO = "fifo"
    LIFO = "lifo"
    HIFO = "hifo"
    AVG = "avg"


class DeFiProtocol(str, Enum):
    """Supported DeFi protocols."""
    AAVE = "aave"
    UNISWAP = "uniswap"
    LIDO = "lido"
    COMPOUND = "compound"
    CURVE = "curve"
    ALL = "all"


# -----------------------------------------------------------------------------
# Portfolio Tools Input Models
# -----------------------------------------------------------------------------


class PortfolioSummaryInput(BaseModel):
    """Input for getting portfolio summary across all exchanges."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    include_staking: bool = Field(
        default=True,
        description="Include staking positions in summary"
    )
    include_defi: bool = Field(
        default=True,
        description="Include DeFi positions in summary"
    )
    include_nfts: bool = Field(
        default=False,
        description="Include NFT holdings in summary (slower)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for programmatic use"
    )


class ExchangeHoldingsInput(BaseModel):
    """Input for getting holdings from specific exchange(s)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    exchange: Exchange = Field(
        default=Exchange.ALL,
        description="Exchange to query: 'coinbase', 'kraken', 'crypto.com', 'gemini', or 'all'"
    )
    asset: Optional[str] = Field(
        default=None,
        description="Filter by specific asset symbol (e.g., 'BTC', 'ETH')",
        min_length=1,
        max_length=20
    )
    min_value_usd: Optional[float] = Field(
        default=None,
        description="Minimum USD value to include in results",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class StakingPositionsInput(BaseModel):
    """Input for getting staking positions."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    exchange: Exchange = Field(
        default=Exchange.ALL,
        description="Exchange to query for staking positions"
    )
    include_rewards: bool = Field(
        default=True,
        description="Include accumulated rewards data"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class DeFiPositionsInput(BaseModel):
    """Input for getting DeFi protocol positions."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    protocol: DeFiProtocol = Field(
        default=DeFiProtocol.ALL,
        description="DeFi protocol: 'aave', 'uniswap', 'lido', 'compound', 'curve', or 'all'"
    )
    wallet_address: Optional[str] = Field(
        default=None,
        description="Specific wallet address to query (uses configured wallets if not specified)",
        pattern=r"^0x[a-fA-F0-9]{40}$"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


# -----------------------------------------------------------------------------
# Analysis Tools Input Models
# -----------------------------------------------------------------------------


class AIAnalysisInput(BaseModel):
    """Input for running AI-powered portfolio analysis."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    analysis_type: str = Field(
        default="comprehensive",
        description="Type of analysis: 'comprehensive', 'risk', 'performance', 'rebalancing', 'tax_optimization'",
        pattern=r"^(comprehensive|risk|performance|rebalancing|tax_optimization)$"
    )
    time_range_days: int = Field(
        default=30,
        description="Number of days to analyze",
        ge=1,
        le=365
    )
    include_recommendations: bool = Field(
        default=True,
        description="Include actionable recommendations"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class CostBasisInput(BaseModel):
    """Input for calculating cost basis and tax lots."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    asset: Optional[str] = Field(
        default=None,
        description="Specific asset to calculate (all assets if not specified)",
        min_length=1,
        max_length=20
    )
    method: CostBasisMethod = Field(
        default=CostBasisMethod.FIFO,
        description="Tax lot identification method: 'fifo', 'lifo', 'hifo', or 'avg'"
    )
    tax_year: Optional[int] = Field(
        default=None,
        description="Tax year to calculate (current year if not specified)",
        ge=2010,
        le=2030
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class HistoricalSnapshotInput(BaseModel):
    """Input for retrieving historical portfolio snapshots."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in ISO format (e.g., '2024-01-01')",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in ISO format (e.g., '2024-12-31')",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    interval: str = Field(
        default="daily",
        description="Snapshot interval: 'hourly', 'daily', 'weekly', 'monthly'",
        pattern=r"^(hourly|daily|weekly|monthly)$"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'markdown' or 'json'"
    )


# -----------------------------------------------------------------------------
# Trading & Automation Tools Input Models
# -----------------------------------------------------------------------------


class ArbitrageOpportunitiesInput(BaseModel):
    """Input for finding cross-exchange arbitrage opportunities."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    min_spread_percent: float = Field(
        default=0.5,
        description="Minimum spread percentage to report",
        ge=0.1,
        le=10.0
    )
    assets: Optional[List[str]] = Field(
        default=None,
        description="Specific assets to check (all major assets if not specified)",
        max_length=20
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class DCABotStatusInput(BaseModel):
    """Input for getting DCA bot status and configuration."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    bot_id: Optional[str] = Field(
        default=None,
        description="Specific bot ID to query (all bots if not specified)",
        min_length=1,
        max_length=50
    )
    include_history: bool = Field(
        default=False,
        description="Include execution history"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class AlertsInput(BaseModel):
    """Input for managing price and portfolio alerts."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    
    action: str = Field(
        default="list",
        description="Action: 'list', 'triggered', 'summary'",
        pattern=r"^(list|triggered|summary)$"
    )
    limit: int = Field(
        default=DEFAULT_LIMIT,
        description="Maximum number of alerts to return",
        ge=1,
        le=MAX_LIMIT
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


# -----------------------------------------------------------------------------
# Transaction Tools Input Models
# -----------------------------------------------------------------------------


class TransactionHistoryInput(BaseModel):
    """Input for retrieving transaction history."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    exchange: Exchange = Field(
        default=Exchange.ALL,
        description="Exchange to query"
    )
    asset: Optional[str] = Field(
        default=None,
        description="Filter by specific asset",
        min_length=1,
        max_length=20
    )
    tx_type: Optional[str] = Field(
        default=None,
        description="Transaction type: 'buy', 'sell', 'transfer', 'stake', 'unstake', 'reward'",
        pattern=r"^(buy|sell|transfer|stake|unstake|reward)$"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in ISO format",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in ISO format",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    limit: int = Field(
        default=DEFAULT_LIMIT,
        description="Maximum transactions to return",
        ge=1,
        le=MAX_LIMIT
    )
    offset: int = Field(
        default=0,
        description="Offset for pagination",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'markdown' or 'json'"
    )


# -----------------------------------------------------------------------------
# Crypto.com AI Agent Input Models
# -----------------------------------------------------------------------------


class CronosChain(str, Enum):
    """Supported Cronos chains."""
    MAINNET = "mainnet"
    TESTNET = "testnet"


class CryptoComAIQueryInput(BaseModel):
    """Input for Crypto.com AI Agent blockchain queries."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        description="Natural language query for Cronos blockchain operations (e.g., 'What is the balance of 0x...?', 'Get the latest block number')",
        min_length=5,
        max_length=1000
    )
    chain: CronosChain = Field(
        default=CronosChain.MAINNET,
        description="Cronos chain to query: 'mainnet' or 'testnet'"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def format_currency(value: float, symbol: str = "$") -> str:
    """Format a number as currency."""
    if value >= 1_000_000:
        return f"{symbol}{value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{symbol}{value/1_000:.2f}K"
    else:
        return f"{symbol}{value:.2f}"


def format_percent(value: float) -> str:
    """Format a number as percentage."""
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def handle_api_error(e: Exception, context: str = "") -> str:
    """Consistent error formatting."""
    error_type = type(e).__name__
    context_str = f" while {context}" if context else ""
    
    if "authentication" in str(e).lower() or "api key" in str(e).lower():
        return f"Error{context_str}: Authentication failed. Please verify your API keys are configured correctly in the .env file."
    elif "rate limit" in str(e).lower():
        return f"Error{context_str}: Rate limit exceeded. Please wait a moment before retrying."
    elif "timeout" in str(e).lower():
        return f"Error{context_str}: Request timed out. The exchange may be experiencing high load."
    elif "not found" in str(e).lower():
        return f"Error{context_str}: Resource not found. Please verify the identifier is correct."
    else:
        return f"Error{context_str}: {error_type} - {str(e)}"


# =============================================================================
# MOCK DATA GENERATORS (Replace with real API calls in production)
# =============================================================================


def get_mock_portfolio_data() -> Dict[str, Any]:
    """Generate mock portfolio data for demonstration."""
    return {
        "total_value_usd": 127834.56,
        "total_cost_basis_usd": 98500.00,
        "unrealized_pnl_usd": 29334.56,
        "unrealized_pnl_percent": 29.78,
        "holdings": {
            "BTC": {"amount": 1.5234, "value_usd": 68553.00, "allocation": 53.6},
            "ETH": {"amount": 12.847, "value_usd": 35169.49, "allocation": 27.5},
            "SOL": {"amount": 125.5, "value_usd": 15187.50, "allocation": 11.9},
            "USDC": {"amount": 8924.57, "value_usd": 8924.57, "allocation": 7.0},
        },
        "by_exchange": {
            "coinbase": {"value_usd": 72450.23, "assets": 4},
            "kraken": {"value_usd": 35234.12, "assets": 3},
            "crypto.com": {"value_usd": 12150.21, "assets": 2},
            "gemini": {"value_usd": 8000.00, "assets": 1},
        },
        "staking_value_usd": 18234.56,
        "defi_value_usd": 12500.00,
        "last_updated": datetime.utcnow().isoformat()
    }


def get_mock_staking_data() -> Dict[str, Any]:
    """Generate mock staking data."""
    return {
        "total_staked_usd": 18234.56,
        "total_rewards_usd": 1245.67,
        "positions": [
            {
                "exchange": "coinbase",
                "asset": "ETH",
                "amount_staked": 5.5,
                "value_usd": 15070.00,
                "apy": 4.2,
                "rewards_earned": 0.231,
                "rewards_usd": 632.94,
                "lock_period": None,
                "status": "active"
            },
            {
                "exchange": "kraken",
                "asset": "SOL",
                "amount_staked": 25.0,
                "value_usd": 3025.00,
                "apy": 7.1,
                "rewards_earned": 1.775,
                "rewards_usd": 214.83,
                "lock_period": "unbonding",
                "status": "active"
            },
            {
                "exchange": "crypto.com",
                "asset": "ATOM",
                "amount_staked": 50.0,
                "value_usd": 475.00,
                "apy": 15.2,
                "rewards_earned": 7.6,
                "rewards_usd": 72.20,
                "lock_period": "21 days",
                "status": "active"
            }
        ]
    }


def get_mock_defi_data() -> Dict[str, Any]:
    """Generate mock DeFi positions data."""
    return {
        "total_value_usd": 12500.00,
        "total_earnings_usd": 856.23,
        "positions": [
            {
                "protocol": "aave",
                "type": "lending",
                "asset": "USDC",
                "amount": 5000.00,
                "value_usd": 5000.00,
                "apy": 4.8,
                "earnings_usd": 240.00,
                "health_factor": 2.5,
                "chain": "ethereum"
            },
            {
                "protocol": "lido",
                "type": "liquid_staking",
                "asset": "stETH",
                "amount": 2.0,
                "value_usd": 5480.00,
                "apy": 3.9,
                "earnings_usd": 213.72,
                "chain": "ethereum"
            },
            {
                "protocol": "uniswap",
                "type": "liquidity",
                "pair": "ETH/USDC",
                "value_usd": 2020.00,
                "apy": 18.5,
                "fees_earned_usd": 373.70,
                "impermanent_loss": -2.3,
                "chain": "ethereum"
            }
        ]
    }


def get_mock_ai_analysis() -> Dict[str, Any]:
    """Generate mock AI analysis results."""
    return {
        "analysis_type": "comprehensive",
        "generated_at": datetime.utcnow().isoformat(),
        "portfolio_health_score": 78,
        "risk_level": "moderate",
        "key_findings": [
            "Portfolio is 81% in large-cap assets (BTC, ETH), providing stability",
            "Staking positions generating estimated $1,245/year in passive income",
            "DeFi exposure is well-diversified across lending and liquidity",
            "High correlation (0.87) between BTC and ETH increases volatility risk"
        ],
        "recommendations": [
            {
                "priority": "high",
                "action": "Consider adding non-correlated assets to reduce portfolio volatility",
                "potential_impact": "Could reduce max drawdown by 15-20%"
            },
            {
                "priority": "medium", 
                "action": "Rebalance ETH staking across providers for better decentralization",
                "potential_impact": "Reduces counterparty risk"
            },
            {
                "priority": "low",
                "action": "Tax-loss harvest SOL position if price drops below cost basis",
                "potential_impact": "Potential tax savings of $500-800"
            }
        ],
        "performance_metrics": {
            "30d_return": 8.5,
            "90d_return": 24.3,
            "ytd_return": 67.2,
            "sharpe_ratio": 1.45,
            "max_drawdown": -18.7
        }
    }


# =============================================================================
# MCP SERVER INITIALIZATION
# =============================================================================


@asynccontextmanager
async def app_lifespan(app):
    """Manage resources that persist across requests."""
    global _aggregator

    config = {
        "paper_trading": os.getenv("PAPER_TRADING", "false").lower() == "true",
        "exchanges_configured": [],
        "wallets_configured": [],
        "use_real_data": False
    }

    # Initialize portfolio aggregator with real exchange connections
    if PORTFOLIO_AGGREGATOR_AVAILABLE:
        try:
            _aggregator = PortfolioAggregator()
            config["exchanges_configured"] = list(_aggregator.exchanges.keys())
            config["use_real_data"] = len(_aggregator.exchanges) > 0
        except Exception as e:
            print(f"Warning: Failed to initialize portfolio aggregator: {e}")
            _aggregator = None

    # Fallback: Check environment variables
    if not config["exchanges_configured"]:
        for exchange in SUPPORTED_EXCHANGES:
            key_var = f"{exchange.upper().replace('.', '_')}_API_KEY"
            if os.getenv(key_var):
                config["exchanges_configured"].append(exchange)

    yield {"config": config}


mcp = FastMCP("crypto_portfolio_mcp", lifespan=app_lifespan)


# =============================================================================
# PORTFOLIO TOOLS
# =============================================================================


@mcp.tool(
    name="crypto_portfolio_summary",
    annotations={
        "title": "Get Portfolio Summary",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crypto_portfolio_summary(params: PortfolioSummaryInput) -> str:
    """Get a comprehensive summary of the entire cryptocurrency portfolio.

    Returns aggregated data across all configured exchanges including total value,
    allocation breakdown, profit/loss, and optionally staking and DeFi positions.

    Args:
        params (PortfolioSummaryInput): Query parameters including:
            - include_staking (bool): Include staking positions
            - include_defi (bool): Include DeFi positions
            - include_nfts (bool): Include NFT holdings
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Portfolio summary in requested format
    """
    try:
        # Use real data if aggregator is available
        if _aggregator and _aggregator.exchanges:
            raw_data = _aggregator.get_combined_portfolio()

            if params.response_format == ResponseFormat.JSON:
                raw_data['data_source'] = 'live'
                return json.dumps(raw_data, indent=2, default=str)

            # Format real data as markdown
            total_value = raw_data.get('total_value_usd', 0)
            total_staked = raw_data.get('total_staked_usd', 0)

            md = f"""# Portfolio Summary (LIVE DATA)

**Last Updated:** {raw_data.get('timestamp', datetime.utcnow().isoformat())}
**Data Source:** Live from {len(raw_data.get('exchanges', {}))} exchanges

## Total Value
- **Portfolio Value:** {format_currency(total_value)}
- **Total Staked:** {format_currency(total_staked)}

## Top Holdings by Asset
| Asset | Total Amount | Value (USD) | Exchanges |
|-------|--------------|-------------|-----------|
"""
            # Show top 15 assets
            for asset in raw_data.get('assets_summary', [])[:15]:
                currency = asset.get('currency', 'UNK')
                total_bal = asset.get('total_balance', 0)
                total_val = asset.get('total_value_usd', 0)
                if total_val < 0.01:
                    continue
                exchanges = ", ".join([e.get('exchange', '')[:8] for e in asset.get('exchanges', [])])
                allocation = (total_val / total_value * 100) if total_value > 0 else 0
                md += f"| {currency} | {total_bal:.6f} | {format_currency(total_val)} | {exchanges} |\n"

            md += f"""
## Holdings by Exchange
| Exchange | Value (USD) | Holdings | Staked |
|----------|-------------|----------|--------|
"""
            for ex_id, ex_data in raw_data.get('exchanges', {}).items():
                name = ex_data.get('exchange', ex_id)
                value = ex_data.get('total_value_usd', 0)
                count = len(ex_data.get('holdings', []))
                staked = ex_data.get('total_staked_usd', 0)
                md += f"| {name} | {format_currency(value)} | {count} | {format_currency(staked)} |\n"

            if params.include_staking and total_staked > 0:
                md += f"\n## Staking Summary\n- **Total Staked:** {format_currency(total_staked)}\n"

            return md

        # Fallback to mock data
        data = get_mock_portfolio_data()

        if params.response_format == ResponseFormat.JSON:
            data['data_source'] = 'mock'
            return json.dumps(data, indent=2)

        # Markdown format for mock data
        md = f"""# Portfolio Summary (DEMO DATA)

**Last Updated:** {data['last_updated']}
**Data Source:** Mock data - configure exchange API keys for live data

## Total Value
- **Portfolio Value:** {format_currency(data['total_value_usd'])}
- **Cost Basis:** {format_currency(data['total_cost_basis_usd'])}
- **Unrealized P&L:** {format_currency(data['unrealized_pnl_usd'])} ({format_percent(data['unrealized_pnl_percent'])})

## Holdings by Asset
| Asset | Amount | Value (USD) | Allocation |
|-------|--------|-------------|------------|
"""
        for asset, info in data['holdings'].items():
            md += f"| {asset} | {info['amount']:.4f} | {format_currency(info['value_usd'])} | {info['allocation']:.1f}% |\n"

        md += f"""
## Holdings by Exchange
| Exchange | Value (USD) | Assets |
|----------|-------------|--------|
"""
        for exchange, info in data['by_exchange'].items():
            md += f"| {exchange.title()} | {format_currency(info['value_usd'])} | {info['assets']} |\n"

        if params.include_staking:
            md += f"\n## Staking\n- **Total Staked:** {format_currency(data['staking_value_usd'])}\n"

        if params.include_defi:
            md += f"\n## DeFi Positions\n- **Total DeFi Value:** {format_currency(data['defi_value_usd'])}\n"
        
        return md
        
    except Exception as e:
        return handle_api_error(e, "fetching portfolio summary")


@mcp.tool(
    name="crypto_exchange_holdings",
    annotations={
        "title": "Get Exchange Holdings",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crypto_exchange_holdings(params: ExchangeHoldingsInput) -> str:
    """Get detailed holdings from specific exchange(s).
    
    Retrieves balance information for all assets on the specified exchange,
    with optional filtering by asset and minimum value.
    
    Args:
        params (ExchangeHoldingsInput): Query parameters including:
            - exchange (str): Exchange name or 'all'
            - asset (str): Optional asset filter
            - min_value_usd (float): Optional minimum value filter
            - response_format (str): 'markdown' or 'json'
    
    Returns:
        str: Holdings data in requested format
    """
    try:
        # Use real data if aggregator is available
        if _aggregator and _aggregator.exchanges:
            raw_data = _aggregator.get_combined_portfolio()

            # Filter by exchange if specified
            if params.exchange != Exchange.ALL:
                exchange_key = params.exchange.value.replace('.', '_')
                if exchange_key not in raw_data.get('exchanges', {}):
                    return f"Exchange '{params.exchange.value}' not configured or has no holdings."
                exchanges_data = {exchange_key: raw_data['exchanges'][exchange_key]}
            else:
                exchanges_data = raw_data.get('exchanges', {})

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({
                    "data_source": "live",
                    "exchange": params.exchange.value,
                    "exchanges": exchanges_data
                }, indent=2, default=str)

            # Markdown format for real data
            md = f"# Holdings: {params.exchange.value.title()} (LIVE DATA)\n\n"

            for ex_id, ex_data in exchanges_data.items():
                ex_name = ex_data.get('exchange', ex_id)
                ex_value = ex_data.get('total_value_usd', 0)
                holdings = ex_data.get('holdings', [])

                # Apply filters
                if params.asset:
                    holdings = [h for h in holdings if h.get('currency', '').upper() == params.asset.upper()]
                if params.min_value_usd:
                    holdings = [h for h in holdings if h.get('value_usd', 0) >= params.min_value_usd]

                md += f"## {ex_name}\n"
                md += f"**Total Value:** {format_currency(ex_value)}\n\n"

                if holdings:
                    md += "| Asset | Balance | Value (USD) | Staked |\n"
                    md += "|-------|---------|-------------|--------|\n"
                    for h in sorted(holdings, key=lambda x: x.get('value_usd', 0), reverse=True):
                        currency = h.get('currency', 'UNK')
                        balance = h.get('balance', 0)
                        value = h.get('value_usd', 0)
                        staked = "Yes" if h.get('is_staked') else ""
                        md += f"| {currency} | {balance:.6f} | {format_currency(value)} | {staked} |\n"
                else:
                    md += "*No holdings matching filters*\n"
                md += "\n"

            return md

        # Fallback to mock data
        data = get_mock_portfolio_data()

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "data_source": "mock",
                "exchange": params.exchange.value,
                "holdings": data['holdings'],
                "by_exchange": data['by_exchange']
            }, indent=2)

        md = f"# Holdings: {params.exchange.value.title()} (DEMO DATA)\n\n"

        if params.exchange == Exchange.ALL:
            for exchange, info in data['by_exchange'].items():
                md += f"## {exchange.title()}\n"
                md += f"- **Total Value:** {format_currency(info['value_usd'])}\n"
                md += f"- **Number of Assets:** {info['assets']}\n\n"
        else:
            exchange_data = data['by_exchange'].get(params.exchange.value, {})
            md += f"- **Total Value:** {format_currency(exchange_data.get('value_usd', 0))}\n"

        return md

    except Exception as e:
        return handle_api_error(e, "fetching exchange holdings")


@mcp.tool(
    name="crypto_staking_positions",
    annotations={
        "title": "Get Staking Positions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crypto_staking_positions(params: StakingPositionsInput) -> str:
    """Get staking positions and rewards across exchanges.
    
    Retrieves all staking positions including staked amounts, APY rates,
    accumulated rewards, and lock periods.
    
    Args:
        params (StakingPositionsInput): Query parameters including:
            - exchange (str): Exchange name or 'all'
            - include_rewards (bool): Include accumulated rewards
            - response_format (str): 'markdown' or 'json'
    
    Returns:
        str: Staking positions data in requested format
    """
    try:
        # Use real data if aggregator is available
        if _aggregator and _aggregator.exchanges:
            raw_data = _aggregator.get_combined_portfolio()

            # Extract staking positions from holdings
            staking_positions = []
            total_staked = 0

            for ex_id, ex_data in raw_data.get('exchanges', {}).items():
                ex_name = ex_data.get('exchange', ex_id)

                # Filter by exchange if specified
                if params.exchange != Exchange.ALL:
                    exchange_key = params.exchange.value.replace('.', '_')
                    if ex_id != exchange_key:
                        continue

                for h in ex_data.get('holdings', []):
                    if h.get('is_staked'):
                        value = h.get('value_usd', 0)
                        total_staked += value
                        staking_positions.append({
                            'exchange': ex_name,
                            'asset': h.get('currency', 'UNK'),
                            'amount_staked': h.get('balance', 0),
                            'value_usd': value,
                            'apy': h.get('apy', 0),
                            'status': 'active'
                        })

            if params.response_format == ResponseFormat.JSON:
                return json.dumps({
                    "data_source": "live",
                    "total_staked_usd": total_staked,
                    "positions": staking_positions
                }, indent=2, default=str)

            # Markdown format
            md = f"""# Staking Positions (LIVE DATA)

**Total Staked Value:** {format_currency(total_staked)}
**Positions:** {len(staking_positions)}

"""
            if staking_positions:
                md += """## Active Positions
| Exchange | Asset | Staked | Value | Status |
|----------|-------|--------|-------|--------|
"""
                for pos in sorted(staking_positions, key=lambda x: x['value_usd'], reverse=True):
                    md += f"| {pos['exchange']} | {pos['asset']} | {pos['amount_staked']:.6f} | {format_currency(pos['value_usd'])} | {pos['status']} |\n"
            else:
                md += "*No staking positions found*\n"

            return md

        # Fallback to mock data
        data = get_mock_staking_data()

        if params.response_format == ResponseFormat.JSON:
            data['data_source'] = 'mock'
            return json.dumps(data, indent=2)

        md = f"""# Staking Positions (DEMO DATA)

**Total Staked Value:** {format_currency(data['total_staked_usd'])}
**Total Rewards Earned:** {format_currency(data['total_rewards_usd'])}

## Active Positions
| Exchange | Asset | Staked | Value | APY | Rewards | Status |
|----------|-------|--------|-------|-----|---------|--------|
"""
        for pos in data['positions']:
            if params.exchange != Exchange.ALL and pos['exchange'] != params.exchange.value:
                continue
            md += f"| {pos['exchange'].title()} | {pos['asset']} | {pos['amount_staked']:.4f} | {format_currency(pos['value_usd'])} | {pos['apy']:.1f}% | {format_currency(pos['rewards_usd'])} | {pos['status']} |\n"

        return md

    except Exception as e:
        return handle_api_error(e, "fetching staking positions")


@mcp.tool(
    name="crypto_defi_positions",
    annotations={
        "title": "Get DeFi Positions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crypto_defi_positions(params: DeFiPositionsInput) -> str:
    """Get DeFi protocol positions and earnings.
    
    Retrieves positions across DeFi protocols including lending, liquidity
    provision, and liquid staking with APY and earnings data.
    
    Args:
        params (DeFiPositionsInput): Query parameters including:
            - protocol (str): Protocol name or 'all'
            - wallet_address (str): Optional specific wallet
            - response_format (str): 'markdown' or 'json'
    
    Returns:
        str: DeFi positions data in requested format
    """
    try:
        data = get_mock_defi_data()
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        md = f"""# DeFi Positions

**Total DeFi Value:** {format_currency(data['total_value_usd'])}
**Total Earnings:** {format_currency(data['total_earnings_usd'])}

## Positions
"""
        for pos in data['positions']:
            if params.protocol != DeFiProtocol.ALL and pos['protocol'] != params.protocol.value:
                continue
            
            md += f"\n### {pos['protocol'].title()} - {pos['type'].replace('_', ' ').title()}\n"
            md += f"- **Chain:** {pos['chain'].title()}\n"
            md += f"- **Value:** {format_currency(pos['value_usd'])}\n"
            md += f"- **APY:** {pos['apy']:.1f}%\n"
            
            if pos['type'] == 'lending':
                md += f"- **Health Factor:** {pos.get('health_factor', 'N/A')}\n"
            elif pos['type'] == 'liquidity':
                md += f"- **Impermanent Loss:** {pos.get('impermanent_loss', 0):.1f}%\n"
        
        return md
        
    except Exception as e:
        return handle_api_error(e, "fetching DeFi positions")


# =============================================================================
# ANALYSIS TOOLS
# =============================================================================


@mcp.tool(
    name="crypto_ai_analysis",
    annotations={
        "title": "Run AI Portfolio Analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def crypto_ai_analysis(params: AIAnalysisInput) -> str:
    """Run AI-powered analysis on the portfolio.
    
    Generates insights, risk assessment, and actionable recommendations
    using AI analysis of portfolio composition, performance, and market conditions.
    
    Args:
        params (AIAnalysisInput): Analysis parameters including:
            - analysis_type (str): Type of analysis to run
            - time_range_days (int): Historical period to analyze
            - include_recommendations (bool): Include actionable recommendations
            - response_format (str): 'markdown' or 'json'
    
    Returns:
        str: AI analysis results in requested format
    """
    try:
        data = get_mock_ai_analysis()
        data['analysis_type'] = params.analysis_type
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        md = f"""# AI Portfolio Analysis

**Analysis Type:** {data['analysis_type'].replace('_', ' ').title()}
**Generated:** {data['generated_at']}

## Portfolio Health
- **Health Score:** {data['portfolio_health_score']}/100
- **Risk Level:** {data['risk_level'].title()}

## Key Findings
"""
        for finding in data['key_findings']:
            md += f"- {finding}\n"
        
        if params.include_recommendations:
            md += "\n## Recommendations\n"
            for rec in data['recommendations']:
                md += f"\n### [{rec['priority'].upper()}] {rec['action']}\n"
                md += f"*Potential Impact:* {rec['potential_impact']}\n"
        
        md += f"""
## Performance Metrics ({params.time_range_days} days)
| Metric | Value |
|--------|-------|
| 30-Day Return | {format_percent(data['performance_metrics']['30d_return'])} |
| 90-Day Return | {format_percent(data['performance_metrics']['90d_return'])} |
| YTD Return | {format_percent(data['performance_metrics']['ytd_return'])} |
| Sharpe Ratio | {data['performance_metrics']['sharpe_ratio']:.2f} |
| Max Drawdown | {format_percent(data['performance_metrics']['max_drawdown'])} |
"""
        return md
        
    except Exception as e:
        return handle_api_error(e, "running AI analysis")


@mcp.tool(
    name="crypto_cost_basis",
    annotations={
        "title": "Calculate Cost Basis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crypto_cost_basis(params: CostBasisInput) -> str:
    """Calculate cost basis and tax lots for holdings.
    
    Computes cost basis using specified accounting method (FIFO, LIFO, HIFO, AVG)
    for tax reporting purposes.
    
    Args:
        params (CostBasisInput): Calculation parameters including:
            - asset (str): Specific asset or all
            - method (str): Tax lot identification method
            - tax_year (int): Year for tax calculations
            - response_format (str): 'markdown' or 'json'
    
    Returns:
        str: Cost basis calculations in requested format
    """
    try:
        # Mock cost basis data
        data = {
            "method": params.method.value.upper(),
            "tax_year": params.tax_year or datetime.now().year,
            "assets": {
                "BTC": {
                    "total_cost_basis": 45000.00,
                    "current_value": 68553.00,
                    "unrealized_gain": 23553.00,
                    "lots": [
                        {"acquired": "2023-01-15", "amount": 0.5, "cost": 11500.00},
                        {"acquired": "2023-06-20", "amount": 0.5234, "cost": 15750.00},
                        {"acquired": "2024-02-10", "amount": 0.5, "cost": 17750.00}
                    ]
                },
                "ETH": {
                    "total_cost_basis": 28500.00,
                    "current_value": 35169.49,
                    "unrealized_gain": 6669.49,
                    "lots": [
                        {"acquired": "2023-03-01", "amount": 5.0, "cost": 8500.00},
                        {"acquired": "2023-09-15", "amount": 7.847, "cost": 20000.00}
                    ]
                }
            },
            "summary": {
                "total_cost_basis": 73500.00,
                "total_current_value": 103722.49,
                "total_unrealized_gain": 30222.49,
                "short_term_gains": 12500.00,
                "long_term_gains": 17722.49
            }
        }
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        md = f"""# Cost Basis Report

**Method:** {data['method']}
**Tax Year:** {data['tax_year']}

## Summary
| Metric | Value |
|--------|-------|
| Total Cost Basis | {format_currency(data['summary']['total_cost_basis'])} |
| Current Value | {format_currency(data['summary']['total_current_value'])} |
| Unrealized Gain | {format_currency(data['summary']['total_unrealized_gain'])} |
| Short-Term Gains | {format_currency(data['summary']['short_term_gains'])} |
| Long-Term Gains | {format_currency(data['summary']['long_term_gains'])} |

## Tax Lots by Asset
"""
        for asset, info in data['assets'].items():
            if params.asset and asset != params.asset.upper():
                continue
            md += f"\n### {asset}\n"
            md += f"- **Cost Basis:** {format_currency(info['total_cost_basis'])}\n"
            md += f"- **Current Value:** {format_currency(info['current_value'])}\n"
            md += f"- **Unrealized Gain:** {format_currency(info['unrealized_gain'])}\n"
            md += f"\n| Acquired | Amount | Cost |\n|----------|--------|------|\n"
            for lot in info['lots']:
                md += f"| {lot['acquired']} | {lot['amount']:.4f} | {format_currency(lot['cost'])} |\n"
        
        return md
        
    except Exception as e:
        return handle_api_error(e, "calculating cost basis")


@mcp.tool(
    name="crypto_arbitrage_opportunities",
    annotations={
        "title": "Find Arbitrage Opportunities",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def crypto_arbitrage_opportunities(params: ArbitrageOpportunitiesInput) -> str:
    """Find cross-exchange arbitrage opportunities.
    
    Scans configured exchanges for price discrepancies that could yield
    arbitrage profits after accounting for fees.
    
    Args:
        params (ArbitrageOpportunitiesInput): Search parameters including:
            - min_spread_percent (float): Minimum spread to report
            - assets (list): Specific assets to check
            - response_format (str): 'markdown' or 'json'
    
    Returns:
        str: Arbitrage opportunities in requested format
    """
    try:
        # Mock arbitrage data
        data = {
            "scan_time": datetime.utcnow().isoformat(),
            "opportunities": [
                {
                    "asset": "BTC",
                    "buy_exchange": "kraken",
                    "buy_price": 44850.00,
                    "sell_exchange": "coinbase",
                    "sell_price": 45125.00,
                    "spread_percent": 0.61,
                    "estimated_profit_usd": 275.00,
                    "fees_estimate_usd": 45.00,
                    "net_profit_usd": 230.00
                },
                {
                    "asset": "ETH",
                    "buy_exchange": "gemini",
                    "buy_price": 2735.00,
                    "sell_exchange": "crypto.com",
                    "sell_price": 2752.00,
                    "spread_percent": 0.62,
                    "estimated_profit_usd": 17.00,
                    "fees_estimate_usd": 5.50,
                    "net_profit_usd": 11.50
                }
            ]
        }
        
        # Filter by minimum spread
        data['opportunities'] = [
            opp for opp in data['opportunities'] 
            if opp['spread_percent'] >= params.min_spread_percent
        ]
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        md = f"""# Arbitrage Opportunities

**Scan Time:** {data['scan_time']}
**Minimum Spread:** {params.min_spread_percent}%

"""
        if not data['opportunities']:
            md += "*No opportunities found meeting the minimum spread criteria.*\n"
        else:
            md += "| Asset | Buy @ | Sell @ | Spread | Net Profit |\n"
            md += "|-------|-------|--------|--------|------------|\n"
            for opp in data['opportunities']:
                md += f"| {opp['asset']} | {opp['buy_exchange']} ({format_currency(opp['buy_price'])}) | {opp['sell_exchange']} ({format_currency(opp['sell_price'])}) | {opp['spread_percent']:.2f}% | {format_currency(opp['net_profit_usd'])} |\n"
        
        return md
        
    except Exception as e:
        return handle_api_error(e, "scanning for arbitrage")


@mcp.tool(
    name="crypto_transaction_history",
    annotations={
        "title": "Get Transaction History",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crypto_transaction_history(params: TransactionHistoryInput) -> str:
    """Get transaction history with filtering and pagination.
    
    Retrieves transaction records including buys, sells, transfers, staking
    operations, and rewards with optional filtering.
    
    Args:
        params (TransactionHistoryInput): Query parameters including:
            - exchange (str): Exchange filter
            - asset (str): Asset filter
            - tx_type (str): Transaction type filter
            - start_date/end_date (str): Date range
            - limit/offset (int): Pagination
            - response_format (str): 'markdown' or 'json'
    
    Returns:
        str: Transaction history in requested format with pagination info
    """
    try:
        # Mock transaction data
        transactions = [
            {"id": "tx001", "type": "buy", "asset": "BTC", "amount": 0.5, "price": 45000.00, "total_usd": 22500.00, "exchange": "coinbase", "timestamp": "2024-01-15T10:30:00Z"},
            {"id": "tx002", "type": "stake", "asset": "ETH", "amount": 5.0, "exchange": "coinbase", "timestamp": "2024-01-20T14:00:00Z"},
            {"id": "tx003", "type": "reward", "asset": "ETH", "amount": 0.05, "value_usd": 137.50, "exchange": "coinbase", "timestamp": "2024-02-01T00:00:00Z"},
            {"id": "tx004", "type": "buy", "asset": "SOL", "amount": 50.0, "price": 98.00, "total_usd": 4900.00, "exchange": "kraken", "timestamp": "2024-02-10T09:15:00Z"},
            {"id": "tx005", "type": "transfer", "asset": "USDC", "amount": 5000.00, "from": "coinbase", "to": "0x742d...f8e2", "timestamp": "2024-02-15T16:45:00Z"},
        ]
        
        # Apply filters
        if params.tx_type:
            transactions = [tx for tx in transactions if tx['type'] == params.tx_type]
        if params.asset:
            transactions = [tx for tx in transactions if tx['asset'] == params.asset.upper()]
        if params.exchange != Exchange.ALL:
            transactions = [tx for tx in transactions if tx.get('exchange') == params.exchange.value]
        
        total = len(transactions)
        transactions = transactions[params.offset:params.offset + params.limit]
        
        data = {
            "total": total,
            "count": len(transactions),
            "offset": params.offset,
            "limit": params.limit,
            "has_more": total > params.offset + len(transactions),
            "next_offset": params.offset + len(transactions) if total > params.offset + len(transactions) else None,
            "transactions": transactions
        }
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        md = f"""# Transaction History

**Total:** {data['total']} transactions
**Showing:** {data['count']} (offset: {data['offset']})

| Date | Type | Asset | Amount | Exchange |
|------|------|-------|--------|----------|
"""
        for tx in transactions:
            date = tx['timestamp'][:10]
            md += f"| {date} | {tx['type']} | {tx['asset']} | {tx['amount']:.4f} | {tx.get('exchange', 'N/A')} |\n"
        
        if data['has_more']:
            md += f"\n*More transactions available. Use offset={data['next_offset']} to see next page.*\n"
        
        return md
        
    except Exception as e:
        return handle_api_error(e, "fetching transaction history")


@mcp.tool(
    name="crypto_alerts_status",
    annotations={
        "title": "Get Alerts Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crypto_alerts_status(params: AlertsInput) -> str:
    """Get status of price and portfolio alerts.
    
    Retrieves configured alerts, recently triggered alerts, or alert summary.
    
    Args:
        params (AlertsInput): Query parameters including:
            - action (str): 'list', 'triggered', or 'summary'
            - limit (int): Maximum alerts to return
            - response_format (str): 'markdown' or 'json'
    
    Returns:
        str: Alerts data in requested format
    """
    try:
        data = {
            "active_alerts": [
                {"id": "alert001", "type": "price_above", "asset": "BTC", "threshold": 50000.00, "created": "2024-01-01"},
                {"id": "alert002", "type": "price_below", "asset": "ETH", "threshold": 2500.00, "created": "2024-01-15"},
                {"id": "alert003", "type": "portfolio_change", "threshold_percent": -10.0, "created": "2024-02-01"},
            ],
            "triggered_recently": [
                {"id": "alert004", "type": "price_above", "asset": "SOL", "threshold": 100.00, "triggered_at": "2024-02-10T14:30:00Z"}
            ],
            "summary": {
                "total_active": 3,
                "triggered_24h": 1,
                "triggered_7d": 2
            }
        }
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        md = "# Alerts Status\n\n"
        
        if params.action == "summary":
            md += f"- **Active Alerts:** {data['summary']['total_active']}\n"
            md += f"- **Triggered (24h):** {data['summary']['triggered_24h']}\n"
            md += f"- **Triggered (7d):** {data['summary']['triggered_7d']}\n"
        elif params.action == "triggered":
            md += "## Recently Triggered\n"
            for alert in data['triggered_recently'][:params.limit]:
                md += f"- **{alert['asset']}** {alert['type']}: {alert['threshold']} @ {alert['triggered_at']}\n"
        else:  # list
            md += "## Active Alerts\n"
            for alert in data['active_alerts'][:params.limit]:
                if alert['type'] == 'portfolio_change':
                    md += f"- Portfolio change > {alert['threshold_percent']}%\n"
                else:
                    md += f"- **{alert['asset']}** {alert['type'].replace('_', ' ')}: ${alert['threshold']:,.2f}\n"
        
        return md
        
    except Exception as e:
        return handle_api_error(e, "fetching alerts")


@mcp.tool(
    name="crypto_dca_bot_status",
    annotations={
        "title": "Get DCA Bot Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crypto_dca_bot_status(params: DCABotStatusInput) -> str:
    """Get status and configuration of DCA bots.
    
    Retrieves Dollar Cost Averaging bot configurations, execution history,
    and performance metrics.
    
    Args:
        params (DCABotStatusInput): Query parameters including:
            - bot_id (str): Specific bot or all
            - include_history (bool): Include execution history
            - response_format (str): 'markdown' or 'json'
    
    Returns:
        str: DCA bot status in requested format
    """
    try:
        data = {
            "bots": [
                {
                    "id": "dca_btc_weekly",
                    "asset": "BTC",
                    "exchange": "coinbase",
                    "amount_usd": 100.00,
                    "frequency": "weekly",
                    "next_execution": "2024-02-19T10:00:00Z",
                    "status": "active",
                    "total_invested": 2600.00,
                    "total_acquired": 0.0578,
                    "avg_price": 44982.70,
                    "executions": 26
                },
                {
                    "id": "dca_eth_biweekly",
                    "asset": "ETH",
                    "exchange": "kraken",
                    "amount_usd": 200.00,
                    "frequency": "biweekly",
                    "next_execution": "2024-02-26T10:00:00Z",
                    "status": "active",
                    "total_invested": 2400.00,
                    "total_acquired": 0.89,
                    "avg_price": 2696.63,
                    "executions": 12
                }
            ]
        }
        
        if params.bot_id:
            data['bots'] = [b for b in data['bots'] if b['id'] == params.bot_id]
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        
        md = "# DCA Bot Status\n\n"
        
        for bot in data['bots']:
            md += f"""## {bot['id']}
- **Asset:** {bot['asset']}
- **Exchange:** {bot['exchange'].title()}
- **Amount:** {format_currency(bot['amount_usd'])} / {bot['frequency']}
- **Status:** {bot['status'].upper()}
- **Next Execution:** {bot['next_execution']}

### Performance
- **Total Invested:** {format_currency(bot['total_invested'])}
- **Total Acquired:** {bot['total_acquired']:.4f} {bot['asset']}
- **Average Price:** {format_currency(bot['avg_price'])}
- **Executions:** {bot['executions']}

"""
        
        return md
        
    except Exception as e:
        return handle_api_error(e, "fetching DCA bot status")


# =============================================================================
# CRYPTO.COM AI AGENT TOOLS
# =============================================================================


def get_crypto_com_agent(chain: str = "mainnet") -> Optional[Any]:
    """Initialize Crypto.com AI Agent if credentials are available."""
    if not CRYPTO_COM_AGENT_AVAILABLE:
        return None

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return None

    try:
        # Chain configuration
        if chain == "mainnet":
            chain_id = 25  # Cronos Mainnet
            explorer_api_key = os.getenv("CRONOSCAN_API_KEY", "")
        else:
            chain_id = 338  # Cronos Testnet
            explorer_api_key = os.getenv("CRONOSCAN_TESTNET_API_KEY", "")

        agent = CryptoComAgent(
            openai_api_key=openai_api_key,
            chain_id=chain_id,
            explorer_api_key=explorer_api_key if explorer_api_key else None
        )
        return agent
    except Exception:
        return None


@mcp.tool(
    name="crypto_cronos_ai_query",
    annotations={
        "title": "Cronos Blockchain AI Query",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def crypto_cronos_ai_query(params: CryptoComAIQueryInput) -> str:
    """Execute natural language queries against the Cronos blockchain.

    Uses Crypto.com AI Agent SDK to translate natural language into blockchain
    operations. Supports balance queries, transaction lookups, contract
    interactions, and more on Cronos mainnet or testnet.

    Args:
        params (CryptoComAIQueryInput): Query parameters including:
            - query (str): Natural language query
            - chain (str): 'mainnet' or 'testnet'
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Query results in requested format

    Examples:
        - "What is the balance of 0x742d35Cc6634C0532925a3b844Bc9e7595f8fE2?"
        - "Get the latest block number"
        - "Show recent transactions for address 0x..."
        - "What is the current gas price?"
    """
    try:
        # Check if SDK is available
        if not CRYPTO_COM_AGENT_AVAILABLE:
            error_msg = {
                "error": "Crypto.com AI Agent SDK not installed",
                "solution": "Install with: pip install crypto_com_ai_agent_client",
                "status": "unavailable"
            }
            if params.response_format == ResponseFormat.JSON:
                return json.dumps(error_msg, indent=2)
            return f"""# Crypto.com AI Agent Unavailable

**Error:** SDK not installed

**Solution:** Install the SDK:
```bash
pip install crypto_com_ai_agent_client
```
"""

        # Check for required API key
        if not os.getenv("OPENAI_API_KEY"):
            error_msg = {
                "error": "OpenAI API key not configured",
                "solution": "Set OPENAI_API_KEY environment variable",
                "status": "misconfigured"
            }
            if params.response_format == ResponseFormat.JSON:
                return json.dumps(error_msg, indent=2)
            return f"""# Crypto.com AI Agent Misconfigured

**Error:** OpenAI API key required

**Solution:** Set environment variable:
```bash
export OPENAI_API_KEY="your-api-key"
```
"""

        # Initialize agent
        agent = get_crypto_com_agent(params.chain.value)
        if not agent:
            error_msg = {
                "error": "Failed to initialize Crypto.com AI Agent",
                "chain": params.chain.value,
                "status": "initialization_failed"
            }
            if params.response_format == ResponseFormat.JSON:
                return json.dumps(error_msg, indent=2)
            return "# Error\n\nFailed to initialize Crypto.com AI Agent. Check logs for details."

        # Execute query
        result = agent.generate_query(params.query)

        # Format response
        data = {
            "query": params.query,
            "chain": params.chain.value,
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2, default=str)

        # Markdown format
        md = f"""# Cronos Blockchain Query

**Query:** {params.query}
**Chain:** {params.chain.value.title()}
**Timestamp:** {data['timestamp']}

## Result

{result if isinstance(result, str) else json.dumps(result, indent=2, default=str)}
"""
        return md

    except Exception as e:
        return handle_api_error(e, f"executing Cronos query on {params.chain.value}")


# =============================================================================
# SERVER ENTRY POINT
# =============================================================================


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crypto Portfolio MCP Server")
    parser.add_argument("--http", action="store_true", help="Use HTTP transport instead of stdio")
    parser.add_argument("--port", type=int, default=8080, help="HTTP port (default: 8080)")
    args = parser.parse_args()
    
    if args.http:
        mcp.run(transport="streamable_http", port=args.port)
    else:
        mcp.run()  # Default: stdio transport for Claude Code
