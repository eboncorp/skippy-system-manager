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
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

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

# Additional trading and management tools
try:
    from additional_tools import register_all_additional_tools
    ADDITIONAL_TOOLS_AVAILABLE = True
except ImportError:
    ADDITIONAL_TOOLS_AVAILABLE = False

# GTI Virtual ETF manager
try:
    from etf_manager import GTIVirtualETF
    from etf_config import ETF_ASSETS, ETF_DAILY_BUDGET, PERSONAL_DAILY_BUDGET, get_war_chest_rule
    ETF_AVAILABLE = True
except ImportError:
    ETF_AVAILABLE = False

# Paper trading agents
try:
    from day_trading_agent import PaperDayTrader
    DAY_TRADER_AVAILABLE = True
except ImportError:
    DAY_TRADER_AVAILABLE = False

try:
    from dca_agent import PaperDCAAgent
    DCA_AGENT_AVAILABLE = True
except ImportError:
    DCA_AGENT_AVAILABLE = False

# On-chain and DeFi trackers for real wallet data
try:
    from defi_tracker import DeFiTracker
    from onchain_tracker import OnChainWalletManager
    ONCHAIN_TRACKING_AVAILABLE = True
except ImportError:
    ONCHAIN_TRACKING_AVAILABLE = False

# Startup validation and system status
try:
    from startup_validation import get_system_status, get_system_status_markdown, print_startup_report
    STARTUP_VALIDATION_AVAILABLE = True
except ImportError:
    STARTUP_VALIDATION_AVAILABLE = False

# Transaction history with CSV/XLSX import
try:
    from transaction_history import TransactionHistory
    TRANSACTION_HISTORY_AVAILABLE = True
except ImportError:
    TRANSACTION_HISTORY_AVAILABLE = False

# Global instances for on-chain tracking
_defi_tracker: Optional["DeFiTracker"] = None
_onchain_manager: Optional["OnChainWalletManager"] = None

# Global aggregator instance (initialized in lifespan)
_aggregator: Optional["PortfolioAggregator"] = None

# Global transaction history instance (initialized in lifespan)
_transaction_history: Optional["TransactionHistory"] = None

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
    COINBASE_GTI = "coinbase_gti"
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


class ImportTransactionsInput(BaseModel):
    """Input for importing transaction history from CSV/XLSX files."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    file_paths: List[str] = Field(
        description="List of file paths to import (CSV or XLSX exchange exports)"
    )
    exchange: Optional[str] = Field(
        default=None,
        description="Force parser: 'coinbase', 'kraken', 'gemini', 'gemini_staking', 'crypto_com'. Auto-detected if omitted.",
        pattern=r"^(coinbase|kraken|gemini|gemini_staking|crypto_com)$"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
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


# -----------------------------------------------------------------------------
# Compliance Tools Input Models
# -----------------------------------------------------------------------------


class TaxExportFormat(str, Enum):
    """Supported tax export formats."""
    CPA_CSV = "cpa_csv"
    TURBOTAX_TXF = "turbotax_txf"
    KOINLY_CSV = "koinly_csv"


class TaxReportInput(BaseModel):
    """Input for generating Form 8949 and Schedule D tax reports."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    tax_year: int = Field(
        default=2025,
        description="Tax year to generate report for",
        ge=2010,
        le=2030
    )
    cost_basis_method: CostBasisMethod = Field(
        default=CostBasisMethod.FIFO,
        description="Cost basis method: 'fifo', 'lifo', 'hifo', or 'avg'"
    )
    format: str = Field(
        default="csv",
        description="Output format: 'csv' for data, 'pdf' for printable form",
        pattern=r"^(csv|pdf)$"
    )
    taxpayer_name: Optional[str] = Field(
        default=None,
        description="Taxpayer name for the form header",
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class TaxExportInput(BaseModel):
    """Input for exporting tax data in third-party formats."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    tax_year: int = Field(
        default=2025,
        description="Tax year to export",
        ge=2010,
        le=2030
    )
    export_format: TaxExportFormat = Field(
        default=TaxExportFormat.CPA_CSV,
        description="Export format: 'cpa_csv', 'turbotax_txf', or 'koinly_csv'"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class AuditLogInput(BaseModel):
    """Input for viewing the audit trail."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    table_name: Optional[str] = Field(
        default=None,
        description="Filter by table name (e.g., 'transactions', 'tax_lots')",
        max_length=50
    )
    record_id: Optional[str] = Field(
        default=None,
        description="Filter by specific record ID",
        max_length=100
    )
    since_date: Optional[str] = Field(
        default=None,
        description="Show entries since this ISO date (e.g., '2025-01-01')",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    limit: int = Field(
        default=DEFAULT_LIMIT,
        description="Maximum entries to return",
        ge=1,
        le=MAX_LIMIT
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
    """
    Consistent error formatting with sanitization.

    SECURITY: This function sanitizes error messages to prevent leaking
    sensitive internal details (file paths, stack traces, credentials).
    """
    import logging
    import re

    error_type = type(e).__name__
    error_msg = str(e)
    context_str = f" while {context}" if context else ""

    # Log the full error internally for debugging
    logging.error(f"API Error{context_str}: {error_type} - {error_msg}")

    # Sanitize: remove potential sensitive data from error messages
    # Remove file paths
    sanitized_msg = re.sub(r'[/\\][\w/\\.-]+\.(py|json|env|key|pem)', '[path]', error_msg)
    # Remove potential credentials/keys
    sanitized_msg = re.sub(r'[a-zA-Z0-9]{20,}', '[redacted]', sanitized_msg)
    # Remove IP addresses
    sanitized_msg = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '[ip]', sanitized_msg)

    # Return user-friendly messages for known error types
    if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
        return f"Error{context_str}: Authentication failed. Please verify your API keys are configured correctly in the .env file."
    elif "rate limit" in error_msg.lower():
        return f"Error{context_str}: Rate limit exceeded. Please wait a moment before retrying."
    elif "timeout" in error_msg.lower():
        return f"Error{context_str}: Request timed out. The exchange may be experiencing high load."
    elif "not found" in error_msg.lower():
        return f"Error{context_str}: Resource not found. Please verify the identifier is correct."
    elif "connection" in error_msg.lower():
        return f"Error{context_str}: Connection failed. Please check your network and try again."
    elif "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
        return f"Error{context_str}: Permission denied. Your API key may lack required permissions."
    else:
        # For unknown errors, return sanitized message (limit length)
        truncated_msg = sanitized_msg[:100] + "..." if len(sanitized_msg) > 100 else sanitized_msg
        return f"Error{context_str}: {error_type} - {truncated_msg}"


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

    # SECURITY: Default to paper trading mode for safety
    # Live trading requires explicit TRADING_MODE=live environment variable
    trading_mode = os.getenv("TRADING_MODE", "confirm").lower()
    is_live = trading_mode == "live"

    # If PAPER_TRADING is explicitly set to "false" AND TRADING_MODE is "live", allow live
    # Otherwise default to paper/confirm mode for safety
    paper_trading = True  # Safe default
    if trading_mode == "live" and os.getenv("PAPER_TRADING", "true").lower() == "false":
        paper_trading = False
    elif os.getenv("PAPER_TRADING", "true").lower() == "true":
        paper_trading = True

    config = {
        "paper_trading": paper_trading,
        "trading_mode": trading_mode,
        "exchanges_configured": [],
        "wallets_configured": [],
        "use_real_data": False
    }

    # Initialize portfolio aggregator with real exchange connections
    if PORTFOLIO_AGGREGATOR_AVAILABLE:
        try:
            _aggregator = PortfolioAggregator()
            config["exchanges_configured"] = list(_aggregator.exchanges.keys())
            config["wallets_configured"] = list(_aggregator.wallets.keys()) if _aggregator.wallets else []
            config["manual_sources_configured"] = list(_aggregator.manual_holdings.keys()) if _aggregator.manual_holdings else []
            config["use_real_data"] = len(_aggregator.exchanges) > 0
        except Exception as e:
            print(f"Warning: Failed to initialize portfolio aggregator: {e}")
            _aggregator = None

    # Fallback: Check environment variables and key files
    if not config["exchanges_configured"]:
        for exchange in SUPPORTED_EXCHANGES:
            key_var = f"{exchange.upper().replace('.', '_')}_API_KEY"
            if os.getenv(key_var):
                config["exchanges_configured"].append(exchange)

        # Check for Kraken key files if not already detected
        if "kraken" not in config["exchanges_configured"]:
            kraken_dir = Path.home() / ".config" / "kraken"
            if kraken_dir.is_dir() and any(kraken_dir.glob("*_api_key.json")):
                config["exchanges_configured"].append("kraken")

    # Initialize transaction history with cached data
    global _transaction_history
    if TRANSACTION_HISTORY_AVAILABLE:
        try:
            _transaction_history = TransactionHistory()
            loaded = _transaction_history.load()
            if loaded:
                config["transaction_history_loaded"] = len(_transaction_history.transactions)
            else:
                config["transaction_history_loaded"] = 0
        except Exception as e:
            print(f"Warning: Failed to initialize transaction history: {e}")
            _transaction_history = None

    yield {"config": config}


mcp = FastMCP("crypto_portfolio_mcp", lifespan=app_lifespan)

# Register additional trading and management tools
if ADDITIONAL_TOOLS_AVAILABLE:
    register_all_additional_tools(mcp)


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
            raw_data = await _aggregator.get_combined_portfolio()

            if params.response_format == ResponseFormat.JSON:
                raw_data['data_source'] = 'live'
                return json.dumps(raw_data, indent=2, default=str)

            # Format real data as markdown
            total_value = raw_data.get('total_value_usd', 0)
            total_staked = raw_data.get('total_staked_usd', 0)
            wallets_total = raw_data.get('wallets_total_usd', 0)
            manual_total = raw_data.get('manual_total_usd', 0)

            # Count data sources
            num_exchanges = len(raw_data.get('exchanges', {}))
            num_wallets = len(raw_data.get('wallets', {}))
            num_manual = len(raw_data.get('manual_sources', {}))
            source_parts = []
            if num_exchanges:
                source_parts.append(f"{num_exchanges} exchanges")
            if num_wallets:
                source_parts.append(f"{num_wallets} wallets")
            if num_manual:
                source_parts.append(f"{num_manual} manual sources")
            source_desc = ", ".join(source_parts) if source_parts else "no sources"

            md = f"""# Portfolio Summary (LIVE DATA)

**Last Updated:** {raw_data.get('timestamp', datetime.utcnow().isoformat())}
**Data Source:** Live from {source_desc}

## Total Value
- **Portfolio Value:** {format_currency(total_value)}
- **Total Staked:** {format_currency(total_staked)}

## Top Holdings by Asset
| Asset | Total Amount | Value (USD) | Sources |
|-------|--------------|-------------|---------|
"""
            # Show top 15 assets
            for asset in raw_data.get('assets_summary', [])[:15]:
                currency = asset.get('currency', 'UNK')
                total_bal = asset.get('total_balance', 0)
                total_val = asset.get('total_value_usd', 0)
                if total_val < 0.01:
                    continue
                sources = ", ".join([e.get('exchange', '')[:10] for e in asset.get('exchanges', [])])
                md += f"| {currency} | {total_bal:.6f} | {format_currency(total_val)} | {sources} |\n"

            md += """
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

            # On-chain wallets section
            wallets_data = raw_data.get('wallets', {})
            if wallets_data:
                md += f"""
## On-Chain Wallets ({format_currency(wallets_total)})
| Wallet | Value (USD) | Tokens |
|--------|-------------|--------|
"""
                for label, w_data in wallets_data.items():
                    w_value = w_data.get('total_value_usd', 0)
                    w_count = len(w_data.get('holdings', []))
                    if w_data.get('error'):
                        md += f"| {label} | Error | - |\n"
                    else:
                        md += f"| {label} | {format_currency(w_value)} | {w_count} |\n"

            # Manual holdings section
            manual_data = raw_data.get('manual_sources', {})
            if manual_data:
                md += f"""
## Manual Holdings ({format_currency(manual_total)})
| Source | Value (USD) | Assets | Last Updated |
|--------|-------------|--------|--------------|
"""
                for src_id, m_data in manual_data.items():
                    m_label = m_data.get('label', src_id)
                    m_value = m_data.get('total_value_usd', 0)
                    m_count = len(m_data.get('holdings', []))
                    m_updated = m_data.get('last_updated', 'unknown')
                    md += f"| {m_label} | {format_currency(m_value)} | {m_count} | {m_updated} |\n"

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

        md += """
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
            raw_data = await _aggregator.get_combined_portfolio()

            # Filter by exchange if specified
            if params.exchange != Exchange.ALL:
                exchange_key = params.exchange.value.replace('.', '_')
                # Match exact key or sub-accounts (e.g. "kraken" matches "kraken_business", "kraken_personal")
                exchanges_data = {
                    k: v for k, v in raw_data.get('exchanges', {}).items()
                    if k == exchange_key or k.startswith(exchange_key + "_")
                }
                if not exchanges_data:
                    return f"Exchange '{params.exchange.value}' not configured or has no holdings."
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
            raw_data = await _aggregator.get_combined_portfolio()

            # Extract staking positions from holdings
            staking_positions = []
            total_staked = 0

            for ex_id, ex_data in raw_data.get('exchanges', {}).items():
                ex_name = ex_data.get('exchange', ex_id)

                # Filter by exchange if specified
                if params.exchange != Exchange.ALL:
                    exchange_key = params.exchange.value.replace('.', '_')
                    if ex_id != exchange_key and not ex_id.startswith(exchange_key + "_"):
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
        # Try to get real data if wallet_address is provided and tracking is available
        if params.wallet_address and ONCHAIN_TRACKING_AVAILABLE:
            try:
                # Create a fresh tracker for this specific wallet
                tracker = DeFiTracker()
                tracker.add_wallet(params.wallet_address, ["ethereum"])

                # Get positions from all protocols
                all_pos = tracker.get_all_positions()

                # Flatten all position types into a single list
                positions = []
                for pos_type, pos_list in all_pos.items():
                    positions.extend(pos_list)

                if positions:
                    total_value = sum(p.usd_value for p in positions)
                    total_rewards = sum(getattr(p, 'rewards_usd', 0) for p in positions)
                    data = {
                        'total_value_usd': total_value,
                        'total_earnings_usd': total_rewards,
                        'positions': [
                            {
                                'protocol': p.protocol,
                                'type': getattr(p, 'position_type', 'unknown'),
                                'chain': p.chain,
                                'asset': getattr(p, 'asset', 'LP'),
                                'value_usd': p.usd_value,
                                'apy': getattr(p, 'apy', 0) or 0,
                                'health_factor': getattr(p, 'health_factor', None),
                                'impermanent_loss': getattr(p, 'impermanent_loss_pct', 0)
                            }
                            for p in positions
                        ],
                        'data_source': 'live'
                    }
                else:
                    # No positions found
                    data = {
                        'total_value_usd': 0,
                        'total_earnings_usd': 0,
                        'positions': [],
                        'data_source': 'live',
                        'message': f'No DeFi positions found for {params.wallet_address}'
                    }
            except Exception as e:
                # Fall back to mock on error
                data = get_mock_defi_data()
                data['data_source'] = 'mock'
                data['error'] = str(e)
        else:
            # Fallback to mock data
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
            md += "\n| Acquired | Amount | Cost |\n|----------|--------|------|\n"
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

    Retrieves real transaction records imported from exchange CSV/XLSX exports
    including buys, sells, transfers, staking operations, and rewards.

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
        if _transaction_history is None or not _transaction_history.transactions:
            return "No transaction history loaded. Use crypto_import_transactions to import exchange CSV/XLSX exports."

        # Filter transactions
        filtered = list(_transaction_history.transactions)

        if params.exchange != Exchange.ALL:
            exchange_name_map = {
                "coinbase": "Coinbase",
                "coinbase_gti": "Coinbase",
                "kraken": "Kraken",
                "crypto.com": "Crypto.com",
                "gemini": "Gemini",
            }
            target = exchange_name_map.get(params.exchange.value, params.exchange.value)
            filtered = [tx for tx in filtered if tx.exchange == target]

        if params.asset:
            asset_upper = params.asset.upper()
            filtered = [tx for tx in filtered if tx.asset == asset_upper]

        if params.tx_type:
            # Map MCP filter values to internal types
            type_aliases = {
                "buy": ("buy",),
                "sell": ("sell",),
                "transfer": ("transfer_in", "transfer_out"),
                "stake": ("stake",),
                "unstake": ("transfer_in",),
                "reward": ("staking_reward", "reward"),
            }
            allowed = type_aliases.get(params.tx_type, (params.tx_type,))
            filtered = [tx for tx in filtered if tx.type in allowed]

        if params.start_date:
            start = datetime.strptime(params.start_date, "%Y-%m-%d")
            filtered = [tx for tx in filtered if tx.timestamp >= start]

        if params.end_date:
            end = datetime.strptime(params.end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
            filtered = [tx for tx in filtered if tx.timestamp <= end]

        total = len(filtered)
        page = filtered[params.offset:params.offset + params.limit]

        transactions_out = []
        for tx in page:
            transactions_out.append({
                "id": tx.id,
                "type": tx.type,
                "asset": tx.asset,
                "amount": tx.amount,
                "price_usd": tx.price_usd,
                "total_usd": tx.total_usd,
                "fee_usd": tx.fee_usd,
                "exchange": tx.exchange,
                "timestamp": tx.timestamp.isoformat() + "Z",
            })

        data = {
            "total": total,
            "count": len(transactions_out),
            "offset": params.offset,
            "limit": params.limit,
            "has_more": total > params.offset + len(transactions_out),
            "next_offset": params.offset + len(transactions_out) if total > params.offset + len(transactions_out) else None,
            "transactions": transactions_out
        }

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        md = f"""# Transaction History

**Total:** {data['total']} transactions
**Showing:** {data['count']} (offset: {data['offset']})

| Date | Type | Asset | Amount | Price USD | Total USD | Exchange |
|------|------|-------|--------|-----------|-----------|----------|
"""
        for tx in transactions_out:
            date = tx['timestamp'][:10]
            price_str = f"${tx['price_usd']:,.2f}" if tx['price_usd'] else "N/A"
            total_str = f"${tx['total_usd']:,.2f}" if tx['total_usd'] else "N/A"
            md += f"| {date} | {tx['type']} | {tx['asset']} | {tx['amount']:.6f} | {price_str} | {total_str} | {tx['exchange']} |\n"

        if data['has_more']:
            md += f"\n*More transactions available. Use offset={data['next_offset']} to see next page.*\n"

        return md

    except Exception as e:
        return handle_api_error(e, "fetching transaction history")


@mcp.tool(
    name="crypto_import_transactions",
    annotations={
        "title": "Import Transaction History",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def crypto_import_transactions(params: ImportTransactionsInput) -> str:
    """Import transaction history from exchange CSV/XLSX export files.

    Parses export files from Coinbase, Kraken, Gemini, and Crypto.com,
    merges with existing data, deduplicates, and rebuilds tax lots.
    Data is persisted to ~/.crypto_portfolio/transaction_history.json.

    Args:
        params (ImportTransactionsInput): Import parameters including:
            - file_paths (list): Paths to CSV/XLSX files to import
            - exchange (str): Force parser type (auto-detected if omitted)
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Import summary with record counts per file and exchange
    """
    try:
        global _transaction_history

        if _transaction_history is None:
            if not TRANSACTION_HISTORY_AVAILABLE:
                return "Error: TransactionHistory module not available."
            _transaction_history = TransactionHistory()
            _transaction_history.load()

        # Validate files exist
        missing = [f for f in params.file_paths if not os.path.isfile(f)]
        if missing:
            return f"Error: Files not found: {', '.join(missing)}"

        summary = _transaction_history.import_from_files(
            params.file_paths,
            exchange_override=params.exchange
        )

        # Save after import
        _transaction_history.save()

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(summary, indent=2)

        md = "# Transaction Import Summary\n\n"
        md += f"**Files processed:** {summary['files_processed']}\n"
        md += f"**Total raw records:** {summary['total_raw']}\n"
        md += f"**After dedup:** {summary['total_deduped']}\n"
        md += f"**Newly added:** {summary.get('newly_added', 'N/A')}\n"
        md += f"**Total in database:** {summary.get('total_after_merge', 'N/A')}\n\n"

        if summary.get("date_range", {}).get("earliest"):
            md += f"**Date range:** {summary['date_range']['earliest'][:10]} to {summary['date_range']['latest'][:10]}\n\n"

        if summary.get("per_file"):
            md += "## Per File\n\n"
            md += "| File | Records |\n|------|--------|\n"
            for fname, count in summary["per_file"].items():
                md += f"| {fname} | {count:,} |\n"
            md += "\n"

        if summary.get("per_exchange"):
            md += "## Per Exchange\n\n"
            md += "| Exchange | Records |\n|----------|--------|\n"
            for exchange, count in summary["per_exchange"].items():
                md += f"| {exchange} | {count:,} |\n"
            md += "\n"

        if summary.get("per_type"):
            md += "## Per Type\n\n"
            md += "| Type | Records |\n|------|--------|\n"
            for tx_type, count in sorted(summary["per_type"].items()):
                md += f"| {tx_type} | {count:,} |\n"
            md += "\n"

        if summary.get("files_failed"):
            md += "## Failed Files\n\n"
            for fail in summary["files_failed"]:
                md += f"- **{fail['file']}**: {fail['error']}\n"

        return md

    except Exception as e:
        return handle_api_error(e, "importing transactions")


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
            return """# Crypto.com AI Agent Unavailable

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
            return """# Crypto.com AI Agent Misconfigured

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
# SYSTEM STATUS TOOL
# =============================================================================


class SystemStatusInput(BaseModel):
    """Input parameters for system status check."""
    model_config = ConfigDict(extra="forbid")

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable, 'json' for programmatic use"
    )
    include_tools: bool = Field(
        default=False,
        description="Include list of available MCP tools"
    )


@mcp.tool(
    name="crypto_system_status",
    annotations={
        "title": "Get System Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def crypto_system_status(params: SystemStatusInput) -> str:
    """Get comprehensive status of the crypto portfolio system.

    Reports on:
    - Available exchanges and their configuration status
    - Feature availability (DeFi, staking, trading, etc.)
    - Available MCP tools
    - System warnings and errors
    - Configuration recommendations

    Use this tool to understand what capabilities are available and
    diagnose configuration issues.

    Args:
        params (SystemStatusInput): Query parameters including:
            - response_format (str): 'markdown' or 'json'
            - include_tools (bool): Include tool availability list

    Returns:
        str: System status report in requested format
    """
    if not STARTUP_VALIDATION_AVAILABLE:
        return "System validation module not available. Check startup_validation.py."

    try:
        if params.response_format == ResponseFormat.JSON:
            status = get_system_status()
            if not params.include_tools:
                status.pop("tools", None)
            return json.dumps(status, indent=2, default=str)
        else:
            return get_system_status_markdown()

    except Exception as e:
        return f"Error getting system status: {str(e)}"


# =============================================================================
# GTI VIRTUAL ETF TOOLS
# =============================================================================


class ETFStatusInput(BaseModel):
    """Input for getting ETF status."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class ETFRebalanceInput(BaseModel):
    """Input for generating ETF rebalance orders."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    fear_greed_override: Optional[int] = Field(
        default=None,
        description="Override Fear & Greed index value (0-100). If not provided, fetches live.",
        ge=0,
        le=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class PaperDayTradeInput(BaseModel):
    """Input for running a paper day-trading session."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    hours: int = Field(
        default=4,
        description="Number of hourly cycles to run (1-24)",
        ge=1,
        le=24
    )
    assets: Optional[str] = Field(
        default=None,
        description="Comma-separated asset list (e.g. 'BTC,ETH,SOL'). Defaults to top 10 tradeable."
    )
    initial_cash: float = Field(
        default=1000,
        description="Initial paper cash in USD",
        gt=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class PaperDCAInput(BaseModel):
    """Input for running a paper DCA cycle."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    fear_greed_override: Optional[int] = Field(
        default=None,
        description="Override Fear & Greed index value (0-100). Fetches live if not provided.",
        ge=0,
        le=100
    )
    dry_run: bool = Field(
        default=False,
        description="If true, generate orders but don't execute them"
    )
    initial_cash: float = Field(
        default=5000,
        description="Initial paper cash in USD",
        gt=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


async def _get_fear_greed() -> int:
    """Fetch current Fear & Greed index."""
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.alternative.me/fng/",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                return int(data['data'][0]['value'])
    except Exception:
        return 50


async def _get_etf_portfolio_data():
    """Get holdings and prices from the portfolio aggregator for ETF calculations."""
    if not _aggregator or not _aggregator.exchanges:
        return {}, {}

    raw_data = await _aggregator.get_combined_portfolio()

    # Build holdings_by_symbol and prices from aggregator data
    holdings_by_symbol = {}
    for asset_data in raw_data.get('assets_summary', []):
        symbol = asset_data.get('currency', '')
        total_bal = asset_data.get('total_balance', 0)
        if total_bal > 0 and symbol:
            from decimal import Decimal as D
            holdings_by_symbol[symbol] = D(str(total_bal))

    # Fetch prices for ETF assets
    if PORTFOLIO_AGGREGATOR_AVAILABLE:
        etf_symbols = list(ETF_ASSETS.keys()) if ETF_AVAILABLE else []
        all_symbols = list(set(list(holdings_by_symbol.keys()) + etf_symbols))
        prices = await _aggregator._fetch_prices(all_symbols)
        from decimal import Decimal as D
        prices_decimal = {k: D(str(v)) for k, v in prices.items()}
        # Stablecoins
        for stable in ('USDC', 'USDT', 'DAI'):
            prices_decimal.setdefault(stable, D('1'))
    else:
        prices_decimal = {}

    return holdings_by_symbol, prices_decimal


@mcp.tool(
    name="crypto_etf_status",
    annotations={
        "title": "Get GTI Virtual ETF Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def crypto_etf_status(params: ETFStatusInput) -> str:
    """Get the current status of the GTI Virtual ETF (50+1 assets).

    Shows NAV, allocation drift per asset and category, war chest status,
    and performance metrics. Use this to understand how the ETF portfolio
    compares to target allocations.

    Args:
        params (ETFStatusInput): Query parameters including:
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: ETF status in requested format
    """
    if not ETF_AVAILABLE:
        return "ETF module not available. Check etf_config.py and etf_manager.py."

    try:
        etf = GTIVirtualETF()

        holdings, prices = await _get_etf_portfolio_data()
        fear_greed = await _get_fear_greed()

        if not holdings and not prices:
            return "No portfolio data available. Check exchange connections."

        status = etf.get_etf_status(holdings, prices, fear_greed)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(etf.format_status_json(status), indent=2, default=str)

        return etf.format_status_markdown(status)

    except Exception as e:
        return handle_api_error(e, "fetching ETF status")


@mcp.tool(
    name="crypto_etf_rebalance",
    annotations={
        "title": "Generate ETF Rebalance Orders",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def crypto_etf_rebalance(params: ETFRebalanceInput) -> str:
    """Generate recommended DCA orders to rebalance the GTI Virtual ETF.

    Analyzes current allocations vs targets and produces a list of buy orders
    prioritizing underweight assets. In fear conditions, also generates war
    chest deployment orders.

    Args:
        params (ETFRebalanceInput): Query parameters including:
            - fear_greed_override (int): Optional F&G override (0-100)
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Rebalance order list in requested format
    """
    if not ETF_AVAILABLE:
        return "ETF module not available. Check etf_config.py and etf_manager.py."

    try:
        etf = GTIVirtualETF()

        holdings, prices = await _get_etf_portfolio_data()
        fear_greed = params.fear_greed_override if params.fear_greed_override is not None else await _get_fear_greed()

        if not holdings and not prices:
            return "No portfolio data available. Check exchange connections."

        allocations = etf.calculate_allocations(holdings, prices)
        orders = etf.generate_dca_orders(allocations, fear_greed)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "fear_greed": fear_greed,
                "war_chest_rule": get_war_chest_rule(fear_greed).label,
                "total_order_usd": str(sum(o.amount_usd for o in orders)),
                "order_count": len(orders),
                "orders": [
                    {
                        "symbol": o.symbol,
                        "exchange": o.exchange.value,
                        "amount_usd": str(o.amount_usd),
                        "category": o.category.value,
                        "reason": o.reason,
                        "priority": o.priority,
                    }
                    for o in orders
                ],
            }, indent=2, default=str)

        return etf.format_orders_markdown(orders)

    except Exception as e:
        return handle_api_error(e, "generating ETF rebalance orders")


# =============================================================================
# PAPER TRADING TOOLS
# =============================================================================


@mcp.tool(
    name="crypto_run_paper_day_trade",
    annotations={
        "title": "Run Paper Day-Trading Session",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def crypto_run_paper_day_trade(params: PaperDayTradeInput) -> str:
    """Run a paper day-trading session using the adaptive strategy.

    Simulates hourly trading cycles using live signal data and prices.
    Switches between momentum and mean-reversion based on market conditions.
    Budget: $12/day personal allocation. All trades are simulated.

    Args:
        params (PaperDayTradeInput): Session parameters including:
            - hours (int): Number of hourly cycles (1-24)
            - assets (str): Comma-separated assets (default: top 10)
            - initial_cash (float): Starting paper cash
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Session summary with trades, P&L, and strategy switches
    """
    if not DAY_TRADER_AVAILABLE:
        return "Day trading agent not available. Check day_trading_agent.py."

    try:
        from decimal import Decimal as D

        assets = params.assets.split(",") if params.assets else None
        trader = PaperDayTrader(
            assets=assets,
            initial_cash=D(str(params.initial_cash)),
        )

        # Fetch live prices to seed
        prices = {}
        try:
            import aiohttp
            from etf_config import get_coingecko_ids
            cg_ids = get_coingecko_ids()
            id_to_symbol = {v: k for k, v in cg_ids.items()}
            ids_param = ",".join(cg_ids.values())

            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        target_assets = set(assets) if assets else set(trader.assets)
                        for cg_id, price_data in data.items():
                            sym = id_to_symbol.get(cg_id)
                            if sym and sym in target_assets and "usd" in price_data:
                                prices[sym] = D(str(price_data["usd"]))
        except Exception:
            pass

        await trader.initialize(prices=prices if prices else None)
        summary = await trader.run_paper_session(hours=params.hours)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(summary, indent=2, default=str)

        return trader.format_summary_markdown(summary)

    except Exception as e:
        return handle_api_error(e, "running paper day-trading session")


@mcp.tool(
    name="crypto_run_paper_dca",
    annotations={
        "title": "Run Paper DCA Cycle",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def crypto_run_paper_dca(params: PaperDCAInput) -> str:
    """Run a paper DCA cycle for the GTI Virtual ETF.

    Generates daily DCA orders based on ETF target allocations and current
    Fear & Greed index. Prioritizes underweight assets and handles war chest
    deployment in fear conditions. Budget: $28/day business allocation.

    Args:
        params (PaperDCAInput): Cycle parameters including:
            - fear_greed_override (int): Optional F&G override (0-100)
            - dry_run (bool): Generate orders without executing
            - initial_cash (float): Starting paper cash
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: DCA cycle report with orders, executions, and NAV
    """
    if not DCA_AGENT_AVAILABLE:
        return "DCA agent not available. Check dca_agent.py."

    if not ETF_AVAILABLE:
        return "ETF module not available. Check etf_config.py and etf_manager.py."

    try:
        from decimal import Decimal as D

        agent = PaperDCAAgent(initial_cash=D(str(params.initial_cash)))

        # Fetch live prices
        prices = await agent.fetch_live_prices()
        if prices:
            await agent.seed_prices(prices)

        result = await agent.run_daily_dca(
            fear_greed=params.fear_greed_override,
            dry_run=params.dry_run,
        )

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2, default=str)

        return agent.format_result_markdown(result)

    except Exception as e:
        return handle_api_error(e, "running paper DCA cycle")


# =============================================================================
# COMPLIANCE TOOLS
# =============================================================================


@mcp.tool(
    name="crypto_generate_tax_report",
    annotations={
        "title": "Generate Tax Report (Form 8949 / Schedule D)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def crypto_generate_tax_report(params: TaxReportInput) -> str:
    """Generate IRS Form 8949 and Schedule D tax reports for cryptocurrency transactions.

    Produces a capital gains report separating short-term and long-term dispositions.
    Supports CSV output for data analysis or PDF for printable IRS forms.

    Args:
        params (TaxReportInput): Report parameters including:
            - tax_year (int): Tax year (default: 2025)
            - cost_basis_method (str): 'fifo', 'lifo', 'hifo', or 'avg'
            - format (str): 'csv' or 'pdf'
            - taxpayer_name (str): Optional name for form header
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Tax report summary with Form 8949 and Schedule D data
    """
    try:
        from compliance.form_8949 import Form8949Line, Form8949Generator, ScheduleDGenerator
        from decimal import Decimal

        # Gather transaction data from transaction history
        lines = []

        if _transaction_history and hasattr(_transaction_history, 'transactions'):
            for tx in _transaction_history.transactions:
                # Filter to dispositions (sells) in the requested tax year
                tx_date = tx.get('date') or tx.get('timestamp')
                if isinstance(tx_date, str):
                    try:
                        tx_date = datetime.fromisoformat(tx_date.replace('Z', '+00:00'))
                    except (ValueError, TypeError):
                        continue
                elif not isinstance(tx_date, datetime):
                    continue

                if tx_date.year != params.tax_year:
                    continue

                tx_type = (tx.get('type') or tx.get('side', '')).lower()
                if tx_type not in ('sell', 'disposal', 'trade'):
                    continue

                # Build Form 8949 line
                asset = tx.get('asset', tx.get('currency', 'UNKNOWN'))
                amount = Decimal(str(tx.get('amount', tx.get('quantity', 0))))
                proceeds = Decimal(str(tx.get('proceeds', tx.get('total', 0))))
                cost_basis = Decimal(str(tx.get('cost_basis', 0)))

                acq_date_raw = tx.get('acquired_date', tx.get('date_acquired'))
                if isinstance(acq_date_raw, str):
                    try:
                        acq_date = datetime.fromisoformat(acq_date_raw.replace('Z', '+00:00'))
                    except (ValueError, TypeError):
                        acq_date = tx_date  # Fallback
                elif isinstance(acq_date_raw, datetime):
                    acq_date = acq_date_raw
                else:
                    acq_date = tx_date

                lines.append(Form8949Line(
                    description=f"{float(amount):.8f} {asset}",
                    date_acquired=acq_date,
                    date_sold=tx_date,
                    proceeds=proceeds,
                    cost_basis=cost_basis,
                    asset=asset,
                    exchange=tx.get('exchange', ''),
                    transaction_id=tx.get('id', tx.get('tx_id', '')),
                ))

        if not lines:
            no_data_msg = (
                f"No disposition transactions found for tax year {params.tax_year}. "
                "Import transaction history first using crypto_import_transactions, "
                "or ensure sell/disposal transactions are recorded."
            )
            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"status": "no_data", "message": no_data_msg})
            return no_data_msg

        # Generate Form 8949
        generator = Form8949Generator(
            lines=lines,
            tax_year=params.tax_year,
            taxpayer_name=params.taxpayer_name or "",
        )

        # Generate Schedule D
        schedule_d = ScheduleDGenerator(lines=lines, tax_year=params.tax_year)
        schedule_d_data = schedule_d.generate()

        result = {
            "tax_year": params.tax_year,
            "cost_basis_method": params.cost_basis_method.value,
            "transaction_count": len(lines),
            "schedule_d": schedule_d_data,
        }

        # Generate file if PDF requested
        if params.format == "pdf":
            output_dir = os.path.expanduser("~/skippy/work/crypto/tax_reports")
            os.makedirs(output_dir, exist_ok=True)
            pdf_path = os.path.join(
                output_dir,
                f"form_8949_{params.tax_year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            actual_path = generator.generate_pdf(pdf_path)
            result["file_path"] = actual_path
            result["format"] = "pdf" if actual_path.endswith(".pdf") else "csv (reportlab not available)"

        if params.response_format == ResponseFormat.JSON:
            # Include CSV data in JSON response
            result["form_8949_csv"] = generator.generate_csv()
            return json.dumps(result, indent=2, default=str)

        # Markdown response
        md = generator.generate_summary_markdown()
        md += "\n\n" + schedule_d.generate_markdown()

        if result.get("file_path"):
            md += f"\n\n**File saved:** `{result['file_path']}`"

        return md

    except Exception as e:
        return handle_api_error(e, "generating tax report")


@mcp.tool(
    name="crypto_export_tax_data",
    annotations={
        "title": "Export Tax Data (CPA/TurboTax/Koinly)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def crypto_export_tax_data(params: TaxExportInput) -> str:
    """Export cryptocurrency tax data in third-party formats for CPAs or tax software.

    Supports:
    - CPA CSV: Standard accountant-friendly spreadsheet
    - TurboTax TXF: Direct import into TurboTax
    - Koinly CSV: Import into Koinly crypto tax platform

    Args:
        params (TaxExportInput): Export parameters including:
            - tax_year (int): Tax year to export
            - export_format (str): 'cpa_csv', 'turbotax_txf', or 'koinly_csv'
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Exported data in the requested format
    """
    try:
        from compliance.form_8949 import Form8949Line
        from compliance.exports import CPAExporter, TurboTaxExporter, KoinlyExporter
        from decimal import Decimal

        # Gather transaction data (same logic as tax report)
        lines = []

        if _transaction_history and hasattr(_transaction_history, 'transactions'):
            for tx in _transaction_history.transactions:
                tx_date = tx.get('date') or tx.get('timestamp')
                if isinstance(tx_date, str):
                    try:
                        tx_date = datetime.fromisoformat(tx_date.replace('Z', '+00:00'))
                    except (ValueError, TypeError):
                        continue
                elif not isinstance(tx_date, datetime):
                    continue

                if tx_date.year != params.tax_year:
                    continue

                tx_type = (tx.get('type') or tx.get('side', '')).lower()
                if tx_type not in ('sell', 'disposal', 'trade'):
                    continue

                asset = tx.get('asset', tx.get('currency', 'UNKNOWN'))
                amount = Decimal(str(tx.get('amount', tx.get('quantity', 0))))
                proceeds = Decimal(str(tx.get('proceeds', tx.get('total', 0))))
                cost_basis = Decimal(str(tx.get('cost_basis', 0)))

                acq_date_raw = tx.get('acquired_date', tx.get('date_acquired'))
                if isinstance(acq_date_raw, str):
                    try:
                        acq_date = datetime.fromisoformat(acq_date_raw.replace('Z', '+00:00'))
                    except (ValueError, TypeError):
                        acq_date = tx_date
                elif isinstance(acq_date_raw, datetime):
                    acq_date = acq_date_raw
                else:
                    acq_date = tx_date

                lines.append(Form8949Line(
                    description=f"{float(amount):.8f} {asset}",
                    date_acquired=acq_date,
                    date_sold=tx_date,
                    proceeds=proceeds,
                    cost_basis=cost_basis,
                    asset=asset,
                    exchange=tx.get('exchange', ''),
                    transaction_id=tx.get('id', tx.get('tx_id', '')),
                ))

        if not lines:
            no_data_msg = (
                f"No disposition transactions found for tax year {params.tax_year}. "
                "Import transaction history first."
            )
            if params.response_format == ResponseFormat.JSON:
                return json.dumps({"status": "no_data", "message": no_data_msg})
            return no_data_msg

        # Export in requested format
        if params.export_format == TaxExportFormat.CPA_CSV:
            data = CPAExporter.export(lines, params.tax_year)
            format_label = "CPA CSV"
        elif params.export_format == TaxExportFormat.TURBOTAX_TXF:
            data = TurboTaxExporter.export(lines, params.tax_year)
            format_label = "TurboTax TXF"
        elif params.export_format == TaxExportFormat.KOINLY_CSV:
            data = KoinlyExporter.export(lines, params.tax_year)
            format_label = "Koinly CSV"
        else:
            return f"Unknown export format: {params.export_format}"

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "tax_year": params.tax_year,
                "format": format_label,
                "transaction_count": len(lines),
                "data": data,
            }, indent=2, default=str)

        # Markdown response with the data
        short = [l for l in lines if not l.is_long_term]
        long = [l for l in lines if l.is_long_term]
        st_gain = sum(l.gain_or_loss for l in short)
        lt_gain = sum(l.gain_or_loss for l in long)

        md = f"## Tax Export - {format_label} ({params.tax_year})\n\n"
        md += f"- **Transactions:** {len(lines)}\n"
        md += f"- **Short-term:** {len(short)} transactions, net ${st_gain:,.2f}\n"
        md += f"- **Long-term:** {len(long)} transactions, net ${lt_gain:,.2f}\n\n"
        md += f"```\n{data}\n```"

        return md

    except Exception as e:
        return handle_api_error(e, "exporting tax data")


@mcp.tool(
    name="crypto_audit_log",
    annotations={
        "title": "View Audit Trail",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def crypto_audit_log(params: AuditLogInput) -> str:
    """View the tamper-evident audit trail for portfolio data changes.

    Shows a hash-chained log of all INSERT, UPDATE, and DELETE operations
    on portfolio data. Supports filtering by table, record, and date range.
    Can also verify chain integrity.

    Args:
        params (AuditLogInput): Query parameters including:
            - table_name (str): Filter by table (e.g., 'transactions')
            - record_id (str): Filter by specific record ID
            - since_date (str): ISO date for start of range
            - limit (int): Max entries to return
            - response_format (str): 'markdown' or 'json'

    Returns:
        str: Audit log entries with chain verification status
    """
    try:
        from compliance.audit_log import AuditLog

        log = AuditLog()

        # Get filtered entries
        entries = log.get_entries(
            table_name=params.table_name,
            record_id=params.record_id,
            since=params.since_date + "T00:00:00Z" if params.since_date else None,
            limit=params.limit,
        )

        # Verify chain integrity
        verification = log.verify_chain()

        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "entries": [e.to_dict() for e in entries],
                "total_entries": verification["entries_checked"],
                "chain_valid": verification["valid"],
                "chain_errors": verification["errors"],
            }, indent=2, default=str)

        # Markdown response
        md = "## Audit Trail\n\n"

        # Chain status
        if verification["valid"]:
            md += f"**Chain Status:** Valid ({verification['entries_checked']} entries verified)\n\n"
        else:
            md += f"**Chain Status:** INTEGRITY ERROR - {len(verification['errors'])} issue(s) detected\n"
            for err in verification["errors"]:
                md += f"- {err}\n"
            md += "\n"

        if not entries:
            md += "No audit log entries match the filter criteria."
            return md

        md += f"**Showing:** {len(entries)} of {verification['entries_checked']} entries\n\n"
        md += log.format_entries_markdown(entries)

        return md

    except Exception as e:
        return handle_api_error(e, "reading audit log")


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
