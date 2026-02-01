"""
Startup Validation and System Status Module.

Provides comprehensive validation of system configuration and
reports on available features at startup.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any
from enum import Enum


class FeatureStatus(Enum):
    """Status of a feature."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    PARTIAL = "partial"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"


@dataclass
class FeatureReport:
    """Report on a single feature."""
    name: str
    status: FeatureStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Complete system validation report."""
    timestamp: datetime = field(default_factory=datetime.now)
    exchanges: List[FeatureReport] = field(default_factory=list)
    features: List[FeatureReport] = field(default_factory=list)
    tools: List[FeatureReport] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        """Check if system is healthy (no critical errors)."""
        return len(self.errors) == 0

    @property
    def available_exchanges(self) -> List[str]:
        """Get list of available exchanges."""
        return [e.name for e in self.exchanges if e.status == FeatureStatus.AVAILABLE]

    @property
    def available_features(self) -> List[str]:
        """Get list of available features."""
        return [f.name for f in self.features if f.status in (FeatureStatus.AVAILABLE, FeatureStatus.PARTIAL)]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "is_healthy": self.is_healthy,
            "summary": {
                "exchanges_available": len(self.available_exchanges),
                "features_available": len(self.available_features),
                "warnings": len(self.warnings),
                "errors": len(self.errors),
            },
            "exchanges": [
                {
                    "name": e.name,
                    "status": e.status.value,
                    "message": e.message,
                    "details": e.details,
                }
                for e in self.exchanges
            ],
            "features": [
                {
                    "name": f.name,
                    "status": f.status.value,
                    "message": f.message,
                }
                for f in self.features
            ],
            "tools": [
                {
                    "name": t.name,
                    "status": t.status.value,
                }
                for t in self.tools
            ],
            "warnings": self.warnings,
            "errors": self.errors,
        }

    def to_markdown(self) -> str:
        """Convert to markdown format."""
        lines = []
        lines.append("# Crypto Portfolio Manager - System Status")
        lines.append(f"\n**Generated:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Health Status:** {'✅ Healthy' if self.is_healthy else '❌ Issues Detected'}")

        # Summary
        lines.append("\n## Summary")
        lines.append(f"- Exchanges Available: {len(self.available_exchanges)}")
        lines.append(f"- Features Available: {len(self.available_features)}")
        lines.append(f"- Warnings: {len(self.warnings)}")
        lines.append(f"- Errors: {len(self.errors)}")

        # Exchanges
        lines.append("\n## Exchanges")
        lines.append("| Exchange | Status | Notes |")
        lines.append("|----------|--------|-------|")
        for e in self.exchanges:
            status_icon = {
                FeatureStatus.AVAILABLE: "✅",
                FeatureStatus.PARTIAL: "⚠️",
                FeatureStatus.UNAVAILABLE: "❌",
                FeatureStatus.NOT_CONFIGURED: "⚙️",
                FeatureStatus.ERROR: "🔴",
            }.get(e.status, "❓")
            lines.append(f"| {e.name} | {status_icon} {e.status.value} | {e.message} |")

        # Features
        lines.append("\n## Features")
        lines.append("| Feature | Status | Notes |")
        lines.append("|---------|--------|-------|")
        for f in self.features:
            status_icon = {
                FeatureStatus.AVAILABLE: "✅",
                FeatureStatus.PARTIAL: "⚠️",
                FeatureStatus.UNAVAILABLE: "❌",
                FeatureStatus.NOT_CONFIGURED: "⚙️",
                FeatureStatus.ERROR: "🔴",
            }.get(f.status, "❓")
            lines.append(f"| {f.name} | {status_icon} {f.status.value} | {f.message} |")

        # MCP Tools
        if self.tools:
            lines.append("\n## MCP Tools")
            available_tools = [t.name for t in self.tools if t.status == FeatureStatus.AVAILABLE]
            lines.append(f"\n**Available Tools ({len(available_tools)}):**")
            for tool in available_tools[:20]:  # Show first 20
                lines.append(f"- `{tool}`")
            if len(available_tools) > 20:
                lines.append(f"- ... and {len(available_tools) - 20} more")

        # Warnings
        if self.warnings:
            lines.append("\n## ⚠️ Warnings")
            for w in self.warnings:
                lines.append(f"- {w}")

        # Errors
        if self.errors:
            lines.append("\n## ❌ Errors")
            for e in self.errors:
                lines.append(f"- {e}")

        return "\n".join(lines)


class SystemValidator:
    """Validates system configuration and reports status."""

    def __init__(self):
        self.report = ValidationReport()

    def validate_all(self) -> ValidationReport:
        """Run all validation checks."""
        self.report = ValidationReport()

        self._validate_exchanges()
        self._validate_features()
        self._validate_tools()
        self._validate_environment()

        return self.report

    def _validate_exchanges(self):
        """Validate exchange configurations."""
        exchanges = [
            ("Coinbase", ["COINBASE_API_KEY", "CDP_API_KEY_FILE"]),
            ("Kraken", ["KRAKEN_API_KEY", "KRAKEN_API_SECRET"]),
            ("Binance", ["BINANCE_API_KEY", "BINANCE_API_SECRET"]),
            ("Crypto.com", ["CRYPTO_COM_API_KEY", "CRYPTO_COM_API_SECRET", "CRYPTO_COM_API_KEY_FILE"]),
            ("Gemini", ["GEMINI_API_KEY", "GEMINI_API_SECRET"]),
        ]

        for name, env_vars in exchanges:
            has_config = any(os.getenv(var) for var in env_vars)

            # Check for file-based config
            config_files = {
                "Coinbase": "~/.config/coinbase/cdp_api_key.json",
                "Kraken": "~/.config/kraken/api_key.json",
                "Crypto.com": "~/.config/crypto_com/api_key.json",
            }

            if name in config_files:
                file_path = os.path.expanduser(config_files[name])
                if os.path.exists(file_path):
                    has_config = True

            if has_config:
                self.report.exchanges.append(FeatureReport(
                    name=name,
                    status=FeatureStatus.AVAILABLE,
                    message="Credentials configured",
                ))
            else:
                self.report.exchanges.append(FeatureReport(
                    name=name,
                    status=FeatureStatus.NOT_CONFIGURED,
                    message=f"Set one of: {', '.join(env_vars)}",
                ))

    def _validate_features(self):
        """Validate feature availability."""
        features = []

        # Portfolio Aggregator
        try:
            from portfolio_aggregator import PortfolioAggregator
            features.append(FeatureReport(
                name="Portfolio Aggregator",
                status=FeatureStatus.AVAILABLE,
                message="Multi-exchange portfolio tracking enabled",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="Portfolio Aggregator",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # Additional Tools
        try:
            from additional_tools import register_all_additional_tools
            features.append(FeatureReport(
                name="Trading Tools",
                status=FeatureStatus.AVAILABLE,
                message="Trading, DCA, alerts, and market data tools",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="Trading Tools",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # DeFi Tracker
        try:
            from defi_tracker import DeFiTracker
            features.append(FeatureReport(
                name="DeFi Tracking",
                status=FeatureStatus.AVAILABLE,
                message="Aave, Uniswap, Lido, Compound tracking",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="DeFi Tracking",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # On-chain Tracking
        try:
            from onchain_tracker import OnChainWalletManager
            features.append(FeatureReport(
                name="On-chain Wallet Tracking",
                status=FeatureStatus.AVAILABLE,
                message="EVM and Solana wallet monitoring",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="On-chain Wallet Tracking",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # Tax Tools
        try:
            from tax_loss_harvesting import TaxLossHarvester
            features.append(FeatureReport(
                name="Tax Loss Harvesting",
                status=FeatureStatus.AVAILABLE,
                message="TLH detection and optimization",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="Tax Loss Harvesting",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # Portfolio Optimization
        try:
            from portfolio_optimization import PortfolioOptimizer
            features.append(FeatureReport(
                name="Portfolio Optimization",
                status=FeatureStatus.AVAILABLE,
                message="MPT-based allocation optimization",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="Portfolio Optimization",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # AI Analysis
        try:
            from ai_enhancements import PricePredictionModel
            features.append(FeatureReport(
                name="AI Analysis",
                status=FeatureStatus.AVAILABLE,
                message="Price prediction, sentiment, anomaly detection",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="AI Analysis",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # Advanced Orders
        try:
            from advanced_orders import AdvancedOrderManager
            features.append(FeatureReport(
                name="Advanced Orders",
                status=FeatureStatus.AVAILABLE,
                message="TWAP, VWAP, Iceberg, Bracket orders",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="Advanced Orders",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # Real-time PnL
        try:
            from realtime_pnl import RealtimeStreamManager
            features.append(FeatureReport(
                name="Real-time PnL Streaming",
                status=FeatureStatus.AVAILABLE,
                message="WebSocket-based live updates",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="Real-time PnL Streaming",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # Web Dashboard
        try:
            from web_dashboard import create_dashboard_app
            features.append(FeatureReport(
                name="Web Dashboard",
                status=FeatureStatus.AVAILABLE,
                message="FastAPI-based web interface",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="Web Dashboard",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # Backtesting
        try:
            from agents.backtester import run_strategy_backtest
            features.append(FeatureReport(
                name="Backtesting Engine",
                status=FeatureStatus.AVAILABLE,
                message="Historical strategy testing with Monte Carlo",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="Backtesting Engine",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        # Signal Analysis
        try:
            from agents.unified_analyzer import UnifiedSignalAnalyzer
            features.append(FeatureReport(
                name="Signal Analysis (130+ signals)",
                status=FeatureStatus.AVAILABLE,
                message="Comprehensive market signal aggregation",
            ))
        except ImportError as e:
            features.append(FeatureReport(
                name="Signal Analysis",
                status=FeatureStatus.UNAVAILABLE,
                message=f"Import error: {str(e)[:50]}",
            ))

        self.report.features = features

    def _validate_tools(self):
        """Validate MCP tools availability."""
        # Core tools always available
        core_tools = [
            "crypto_portfolio_summary",
            "crypto_exchange_holdings",
            "crypto_staking_positions",
            "crypto_defi_positions",
            "crypto_ai_analysis",
            "crypto_cost_basis",
            "crypto_arbitrage_opportunities",
            "crypto_transaction_history",
            "crypto_alerts_status",
            "crypto_dca_bot_status",
            "crypto_system_status",
        ]

        for tool in core_tools:
            self.report.tools.append(FeatureReport(
                name=tool,
                status=FeatureStatus.AVAILABLE,
            ))

        # Additional tools if module is available
        try:
            from additional_tools import register_all_additional_tools
            additional_tools = [
                "crypto_place_order",
                "crypto_cancel_order",
                "crypto_open_orders",
                "crypto_stake_asset",
                "crypto_unstake_asset",
                "crypto_create_dca_bot",
                "crypto_manage_dca_bot",
                "crypto_create_alert",
                "crypto_manage_alert",
                "crypto_get_price",
                "crypto_get_market_data",
                "crypto_get_historical_prices",
                "crypto_get_order_book",
                "crypto_nft_holdings",
                "crypto_tax_report",
                "crypto_cost_basis_detail",
            ]
            for tool in additional_tools:
                self.report.tools.append(FeatureReport(
                    name=tool,
                    status=FeatureStatus.AVAILABLE,
                ))
        except ImportError:
            pass

    def _validate_environment(self):
        """Validate environment configuration."""
        # Check for common misconfigurations

        # Paper trading mode
        if os.getenv("PAPER_TRADING", "true").lower() != "true":
            self.report.warnings.append(
                "PAPER_TRADING is not set to 'true' - real trades may be executed"
            )

        # Database
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            self.report.warnings.append(
                "DATABASE_URL not set - using SQLite default (portfolio.db)"
            )

        # Redis cache
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            self.report.warnings.append(
                "REDIS_URL not set - caching disabled (may affect performance)"
            )

        # Notifications
        has_notifications = any([
            os.getenv("DISCORD_WEBHOOK_URL"),
            os.getenv("TELEGRAM_BOT_TOKEN"),
            os.getenv("SMTP_HOST"),
        ])
        if not has_notifications:
            self.report.warnings.append(
                "No notification channels configured - alerts will only be logged"
            )

        # Etherscan for DeFi
        if not os.getenv("ETHERSCAN_API_KEY"):
            self.report.warnings.append(
                "ETHERSCAN_API_KEY not set - DeFi tracking may be limited"
            )


def get_system_status() -> Dict:
    """Get system status as a dictionary."""
    validator = SystemValidator()
    report = validator.validate_all()
    return report.to_dict()


def get_system_status_markdown() -> str:
    """Get system status as markdown."""
    validator = SystemValidator()
    report = validator.validate_all()
    return report.to_markdown()


def print_startup_report():
    """Print startup validation report to console."""
    validator = SystemValidator()
    report = validator.validate_all()

    print("\n" + "=" * 70)
    print("CRYPTO PORTFOLIO MANAGER - STARTUP VALIDATION")
    print("=" * 70)
    print(f"\nHealth Status: {'✅ HEALTHY' if report.is_healthy else '❌ ISSUES DETECTED'}")
    print(f"Exchanges Available: {len(report.available_exchanges)}")
    print(f"Features Available: {len(report.available_features)}")

    if report.available_exchanges:
        print(f"\nConfigured Exchanges: {', '.join(report.available_exchanges)}")

    if report.warnings:
        print(f"\n⚠️  Warnings ({len(report.warnings)}):")
        for w in report.warnings:
            print(f"   - {w}")

    if report.errors:
        print(f"\n❌ Errors ({len(report.errors)}):")
        for e in report.errors:
            print(f"   - {e}")

    print("\n" + "=" * 70 + "\n")

    return report


if __name__ == "__main__":
    print_startup_report()
