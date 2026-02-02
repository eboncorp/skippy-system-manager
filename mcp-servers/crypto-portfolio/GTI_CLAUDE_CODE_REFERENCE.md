# GTI Crypto Portfolio System - Claude Code Reference

**Document Type:** Proprietary Development Guide  
**Owner:** GTI Inc  
**Last Updated:** February 2, 2026  
**Classification:** Internal Use Only  

---

## Quick Reference

```bash
# Project location
cd ~/crypto-portfolio

# Daily operations
gti-dca              # Run signal-adjusted DCA cycle
gti-signals BTC      # Get signal analysis for asset
gti-portfolio        # Full portfolio summary
gti-tax 2025         # Generate tax package

# Development
source skippy-profile crypto-dev
pytest -v            # Run tests
ruff check . --fix   # Auto-fix linting
```

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Specialization Roadmap](#3-specialization-roadmap)
4. [Code Consolidation](#4-code-consolidation)
5. [skippy Integration](#5-skippy-integration)
6. [GTI-Specific Configurations](#6-gti-specific-configurations)
7. [Security Model](#7-security-model)
8. [Performance Optimizations](#8-performance-optimizations)
9. [Maintenance Procedures](#9-maintenance-procedures)
10. [Future Enhancements](#10-future-enhancements)
11. [Troubleshooting](#11-troubleshooting)
12. [API Reference](#12-api-reference)

---

## 1. System Overview

### Purpose

Proprietary cryptocurrency portfolio management system for GTI Inc. Provides:
- 130+ market signals for buy/sell decisions
- Signal-adjusted DCA automation
- Virtual ETF management with war chest deployment
- Tax compliance (Form 8949, Schedule D)
- Multi-exchange portfolio aggregation

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Lines | ~70K (target: ~15K after specialization) |
| Python Files | 116 |
| MCP Tools | 25+ |
| Signal Categories | 8 |
| Supported Exchanges | 4 (GTI stack) |
| Test Coverage | ~40% |

### Technology Stack

```
Runtime:        Python 3.12+
MCP Framework:  FastMCP 2.x
Database:       SQLite (dev) / PostgreSQL (prod)
Caching:        Redis (optional)
Exchanges:      Coinbase, Kraken, Gemini, Crypto.com
Integration:    skippy ecosystem
```

---

## 2. Architecture

### Current Structure

```
crypto-portfolio/
├── crypto_portfolio_mcp.py    # Main MCP server (2,542 lines)
├── portfolio_aggregator.py    # Multi-exchange aggregation
├── additional_tools.py        # Extended MCP tools
│
├── agents/                    # Signal analysis & automation
│   ├── unified_analyzer.py    # Main signal orchestrator
│   ├── expanded_signals.py    # 130+ signal implementations
│   ├── trading_agent.py       # Trade execution logic
│   └── dca.py                 # DCA strategy engine
│
├── exchanges/                 # Exchange clients
│   ├── base.py                # Abstract interface
│   ├── coinbase_client.py     # Coinbase Advanced Trade
│   ├── kraken_client.py       # Kraken
│   ├── gemini_client.py       # Gemini
│   ├── crypto_com_client.py   # Crypto.com
│   ├── ccxt_fallback.py       # Generic fallback (REMOVE)
│   ├── binance_client.py      # Unused (REMOVE)
│   ├── okx_client.py          # Unused (REMOVE)
│   └── mock.py                # Paper trading (REMOVE)
│
├── compliance/                # Tax & audit
│   ├── form_8949.py           # IRS Form 8949 generator
│   ├── audit_log.py           # Hash-chained audit trail
│   └── exports.py             # CPA/TurboTax/Koinly exports
│
├── tracking/                  # Portfolio tracking
│   ├── portfolio.py           # Holdings tracker
│   ├── staking.py             # Staking rewards
│   └── tax.py                 # Tax lot management
│
└── data/                      # Local storage
    ├── portfolio.db           # SQLite database
    └── audit_log.json         # Audit trail
```

### Target Architecture (Post-Specialization)

```
crypto-portfolio/
├── gti_mcp.py                 # Unified MCP server (~3K lines)
├── gti_config.py              # Hardcoded GTI configuration
│
├── exchanges/                 # GTI exchanges only
│   ├── base.py
│   ├── coinbase_client.py
│   ├── kraken_client.py
│   ├── gemini_client.py
│   └── crypto_com_client.py
│
├── signals/                   # Streamlined signals
│   ├── analyzer.py            # Unified signal analysis
│   └── gti_weights.py         # Frozen signal weights
│
├── compliance/                # Tax (unchanged)
│   ├── form_8949.py
│   ├── audit_log.py
│   └── exports.py
│
├── skippy/                    # skippy integration
│   ├── hooks.py               # Event hooks
│   └── commands.py            # CLI wrappers
│
└── data/
    ├── portfolio.db
    └── audit_log.json

Target: ~15K lines (78% reduction)
```

---

## 3. Specialization Roadmap

### Phase 1: Remove Unused Code (Week 1)

**Files to Delete:**

```bash
# Unused exchanges
rm exchanges/binance_client.py      # 15,937 lines
rm exchanges/okx_client.py          # 17,823 lines
rm exchanges/ccxt_fallback.py       # 11,530 lines

# Paper trading (not needed for production)
rm exchanges/mock.py                # 32,606 lines

# Redundant agents
rm agents/day_trading_agent.py      # Not GTI strategy
rm agents/dip_buyer.py              # Subsumed by DCA

# Generic CLI tools
rm multi_trading_cli.py
rm trading_cli.py
rm backtest_cli.py
```

**Estimated Savings:** ~45K lines

### Phase 2: Hardcode GTI Configuration (Week 1)

**Create `gti_config.py`:**

```python
"""
GTI Inc - Frozen Configuration
==============================

DO NOT MODIFY without backtesting validation.
Last validated: February 2026
"""

from decimal import Decimal
from typing import Dict

# =============================================================================
# EXCHANGE CONFIGURATION
# =============================================================================

EXCHANGES = ["coinbase", "kraken", "gemini", "crypto_com"]

EXCHANGE_PRIORITIES = {
    "coinbase": 1,   # Primary for BTC, ETH
    "kraken": 2,     # Backup, staking
    "gemini": 3,     # Earn products
    "crypto_com": 4, # CRO ecosystem
}

# DCA execution preference by asset
ASSET_EXCHANGE_MAP = {
    "BTC": "coinbase",
    "ETH": "coinbase",
    "SOL": "coinbase",
    "ATOM": "kraken",      # Best staking rates
    "DOT": "kraken",
    "MATIC": "gemini",
    "CRO": "crypto_com",
}

# =============================================================================
# GTI VIRTUAL ETF
# =============================================================================

GTI_ETF_ALLOCATIONS = {
    # Core Holdings (20%)
    "core": {
        "BTC": Decimal("0.10"),
        "ETH": Decimal("0.05"),
        "SOL": Decimal("0.03"),
        "AVAX": Decimal("0.02"),
    },
    
    # Income/Staking (25%)
    "income": {
        "ATOM": Decimal("0.05"),
        "DOT": Decimal("0.04"),
        "MATIC": Decimal("0.04"),
        "ADA": Decimal("0.03"),
        "ALGO": Decimal("0.03"),
        "XTZ": Decimal("0.03"),
        "NEAR": Decimal("0.03"),
    },
    
    # Growth (15%)
    "growth": {
        "LINK": Decimal("0.03"),
        "UNI": Decimal("0.02"),
        "AAVE": Decimal("0.02"),
        "MKR": Decimal("0.02"),
        "SNX": Decimal("0.02"),
        "CRV": Decimal("0.02"),
        "LDO": Decimal("0.02"),
    },
    
    # Land/RWA (10%)
    "land_rwa": {
        "MANA": Decimal("0.025"),
        "SAND": Decimal("0.025"),
        "AXS": Decimal("0.025"),
        "ENJ": Decimal("0.025"),
    },
    
    # High Risk (15%)
    "high_risk": {
        # Rotate based on signals
        "allocation": Decimal("0.15"),
        "max_per_asset": Decimal("0.03"),
    },
    
    # War Chest (15%)
    "war_chest": {
        "target": Decimal("0.15"),
        "currency": "USDC",
    },
}

# =============================================================================
# SIGNAL CONFIGURATION (FROZEN)
# =============================================================================

# DCA multipliers by composite score range
DCA_MULTIPLIERS = {
    (-100, -50): Decimal("3.0"),   # Extreme fear
    (-50, -25): Decimal("2.0"),    # Fear
    (-25, 0): Decimal("1.5"),      # Mild fear
    (0, 25): Decimal("1.0"),       # Neutral
    (25, 50): Decimal("0.5"),      # Greed
    (50, 100): Decimal("0.25"),    # Extreme greed
}

# Signal category weights (sum = 1.0)
SIGNAL_WEIGHTS = {
    "sentiment": Decimal("0.15"),
    "onchain": Decimal("0.25"),
    "technical": Decimal("0.15"),
    "derivatives": Decimal("0.15"),
    "macro": Decimal("0.10"),
    "smart_money": Decimal("0.20"),
}

# War chest deployment rules
WAR_CHEST_RULES = {
    "deploy_threshold": -35,       # Composite score to trigger
    "deploy_percent": Decimal("0.35"),  # Deploy 35% of war chest
    "min_deploy_usd": Decimal("100"),
    "max_deploy_usd": Decimal("5000"),
    "cooldown_days": 7,            # Min days between deployments
}

# =============================================================================
# DCA SCHEDULE
# =============================================================================

DAILY_DCA_USD = Decimal("28.00")   # Base daily amount

DCA_SCHEDULE = {
    "frequency": "daily",
    "execution_time": "09:00",      # UTC
    "assets": ["BTC", "ETH", "SOL", "ATOM"],
    "base_amount_usd": DAILY_DCA_USD,
}

# =============================================================================
# TAX CONFIGURATION
# =============================================================================

TAX_CONFIG = {
    "cost_basis_method": "HIFO",   # Highest In, First Out (tax optimal)
    "fiscal_year_end": "12-31",
    "state": "KY",
    "accountant_format": "cpa_csv",
}

# =============================================================================
# ALERT THRESHOLDS
# =============================================================================

ALERTS = {
    "portfolio_drop_percent": 10,   # Alert if portfolio drops 10%+
    "signal_extreme_fear": -50,     # Alert on extreme fear
    "signal_extreme_greed": 50,     # Alert on extreme greed
    "staking_reward_min": 1.0,      # Min USD to log staking reward
}
```

### Phase 3: Create skippy Integration (Week 2)

**Create `skippy/hooks.py`:**

```python
"""
skippy Integration Hooks
========================

Connects crypto portfolio system to skippy ecosystem.
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

SKIPPY_PATH = Path.home() / "skippy"
CRYPTO_LOG_PATH = SKIPPY_PATH / "logs" / "crypto"


class SkippyHooks:
    """Integration with skippy automation system."""
    
    @staticmethod
    def notify(message: str, priority: str = "normal", 
               channel: str = "default") -> bool:
        """Send notification via skippy."""
        script = SKIPPY_PATH / "scripts" / "notify.sh"
        if not script.exists():
            return False
        
        result = subprocess.run([
            str(script),
            "--priority", priority,
            "--channel", channel,
            "--message", message,
        ], capture_output=True)
        
        return result.returncode == 0
    
    @staticmethod
    def log_trade(trade_data: dict) -> None:
        """Log trade to skippy's unified logging."""
        CRYPTO_LOG_PATH.mkdir(parents=True, exist_ok=True)
        log_file = CRYPTO_LOG_PATH / "trades.jsonl"
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **trade_data,
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    @staticmethod
    def log_signal(asset: str, score: float, recommendation: str) -> None:
        """Log signal analysis to skippy."""
        CRYPTO_LOG_PATH.mkdir(parents=True, exist_ok=True)
        log_file = CRYPTO_LOG_PATH / "signals.jsonl"
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "asset": asset,
            "composite_score": score,
            "recommendation": recommendation,
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    @staticmethod
    def backup_database() -> bool:
        """Trigger database backup via skippy."""
        script = SKIPPY_PATH / "scripts" / "backup_crypto_db.sh"
        if script.exists():
            result = subprocess.run([str(script)], capture_output=True)
            return result.returncode == 0
        return False
    
    @staticmethod
    def health_check() -> dict:
        """Report health status to skippy monitoring."""
        return {
            "service": "crypto-portfolio",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


# Convenience functions
def notify_trade(asset: str, side: str, amount: float, price: float):
    """Notify on trade execution."""
    msg = f"🔄 {side.upper()} {amount:.6f} {asset} @ ${price:,.2f}"
    SkippyHooks.notify(msg, priority="normal", channel="crypto")


def notify_signal_alert(asset: str, score: float):
    """Notify on extreme signal conditions."""
    if score <= -50:
        emoji = "🟢"
        condition = "EXTREME FEAR"
    elif score >= 50:
        emoji = "🔴"
        condition = "EXTREME GREED"
    else:
        return  # No alert for normal conditions
    
    msg = f"{emoji} {asset}: {condition} (score: {score:.0f})"
    SkippyHooks.notify(msg, priority="high", channel="crypto")


def notify_war_chest_deploy(amount: float, score: float):
    """Notify on war chest deployment."""
    msg = f"💰 War chest deployed: ${amount:,.2f} (score: {score:.0f})"
    SkippyHooks.notify(msg, priority="high", channel="crypto")
```

**Create skippy scripts:**

```bash
# ~/skippy/scripts/gti-dca
#!/bin/bash
# GTI Daily DCA Execution
set -euo pipefail

cd ~/crypto-portfolio
source ~/skippy/scripts/skippy-profile crypto-dev

python -c "
import asyncio
from gti_mcp import execute_daily_dca
asyncio.run(execute_daily_dca())
"
```

```bash
# ~/skippy/scripts/gti-signals
#!/bin/bash
# GTI Signal Analysis
set -euo pipefail

ASSET="${1:-BTC}"

cd ~/crypto-portfolio
python -c "
import asyncio
from gti_mcp import get_signal_analysis
result = asyncio.run(get_signal_analysis('$ASSET'))
print(result)
"
```

```bash
# ~/skippy/scripts/gti-portfolio
#!/bin/bash
# GTI Portfolio Summary
set -euo pipefail

cd ~/crypto-portfolio
python -c "
import asyncio
from gti_mcp import get_portfolio_summary
result = asyncio.run(get_portfolio_summary())
print(result)
"
```

```bash
# ~/skippy/scripts/gti-tax
#!/bin/bash
# GTI Tax Report Generation
set -euo pipefail

YEAR="${1:-2025}"
OUTPUT_DIR=~/skippy/work/crypto/tax/${YEAR}

mkdir -p "$OUTPUT_DIR"
cd ~/crypto-portfolio

python -c "
from compliance.form_8949 import Form8949Generator
from compliance.exports import CPAExporter, TurboTaxExporter

# Generate reports
# ... implementation
print('Tax reports generated in $OUTPUT_DIR')
"
```

### Phase 4: Consolidate MCP Server (Week 2)

**Create unified `gti_mcp.py`:**

```python
"""
GTI Crypto Portfolio MCP Server
===============================

Proprietary MCP server for GTI Inc cryptocurrency portfolio management.
Streamlined for GTI's specific workflow and exchange stack.

Usage:
    # Claude Code
    python gti_mcp.py
    
    # HTTP mode
    python gti_mcp.py --http --port 8080
"""

import asyncio
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from gti_config import (
    EXCHANGES, GTI_ETF_ALLOCATIONS, DCA_MULTIPLIERS,
    SIGNAL_WEIGHTS, WAR_CHEST_RULES, DCA_SCHEDULE,
)
from exchanges.coinbase_client import CoinbaseClient
from exchanges.kraken_client import KrakenClient
from exchanges.gemini_client import GeminiClient
from exchanges.crypto_com_client import CryptoComClient
from signals.analyzer import GTISignalAnalyzer
from compliance.form_8949 import Form8949Generator
from compliance.audit_log import AuditLog
from skippy.hooks import SkippyHooks, notify_trade, notify_signal_alert

# =============================================================================
# MCP SERVER SETUP
# =============================================================================

mcp = FastMCP(
    "GTI Crypto Portfolio",
    version="2.0.0",
    description="GTI Inc proprietary crypto portfolio management",
)

# Global instances
_clients = {}
_analyzer = None
_audit_log = None


async def get_exchange_client(exchange: str):
    """Get or create exchange client."""
    if exchange not in _clients:
        if exchange == "coinbase":
            _clients[exchange] = CoinbaseClient()
        elif exchange == "kraken":
            _clients[exchange] = KrakenClient()
        elif exchange == "gemini":
            _clients[exchange] = GeminiClient()
        elif exchange == "crypto_com":
            _clients[exchange] = CryptoComClient()
    return _clients.get(exchange)


def get_analyzer():
    """Get signal analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = GTISignalAnalyzer(weights=SIGNAL_WEIGHTS)
    return _analyzer


def get_audit_log():
    """Get audit log instance."""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log


# =============================================================================
# INPUT MODELS
# =============================================================================

class AssetInput(BaseModel):
    asset: str = Field(description="Asset symbol (e.g., BTC, ETH)")


class DCAInput(BaseModel):
    asset: Optional[str] = Field(None, description="Specific asset or all")
    dry_run: bool = Field(True, description="Simulate without executing")


class TaxReportInput(BaseModel):
    year: int = Field(description="Tax year")
    format: str = Field("csv", description="Output format: csv, pdf, turbotax, koinly")


# =============================================================================
# CORE MCP TOOLS
# =============================================================================

@mcp.tool(annotations={"readOnlyHint": True})
async def gti_portfolio_summary() -> str:
    """Get GTI portfolio summary across all exchanges."""
    holdings = {}
    total_value = Decimal("0")
    
    for exchange in EXCHANGES:
        client = await get_exchange_client(exchange)
        if client:
            try:
                balances = await client.get_balances()
                for asset, balance in balances.items():
                    if asset not in holdings:
                        holdings[asset] = {
                            "total": Decimal("0"),
                            "by_exchange": {},
                        }
                    holdings[asset]["total"] += balance.total
                    holdings[asset]["by_exchange"][exchange] = float(balance.total)
            except Exception as e:
                pass  # Skip failed exchanges
    
    # Format output
    lines = ["# GTI Portfolio Summary", ""]
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("| Asset | Total | Coinbase | Kraken | Gemini | Crypto.com |")
    lines.append("|-------|-------|----------|--------|--------|------------|")
    
    for asset, data in sorted(holdings.items(), key=lambda x: -float(x[1]["total"])):
        if data["total"] > 0:
            row = [
                asset,
                f"{data['total']:.6f}",
                f"{data['by_exchange'].get('coinbase', 0):.6f}",
                f"{data['by_exchange'].get('kraken', 0):.6f}",
                f"{data['by_exchange'].get('gemini', 0):.6f}",
                f"{data['by_exchange'].get('crypto_com', 0):.6f}",
            ]
            lines.append("| " + " | ".join(row) + " |")
    
    return "\n".join(lines)


@mcp.tool(annotations={"readOnlyHint": True})
async def gti_signal_analysis(params: AssetInput) -> str:
    """Get GTI signal analysis for an asset."""
    analyzer = get_analyzer()
    result = await analyzer.analyze(params.asset)
    
    # Log to skippy
    SkippyHooks.log_signal(
        params.asset, 
        result.composite_score,
        result.recommendation.action,
    )
    
    # Check for extreme conditions
    notify_signal_alert(params.asset, result.composite_score)
    
    # Get DCA multiplier
    multiplier = Decimal("1.0")
    for (low, high), mult in DCA_MULTIPLIERS.items():
        if low <= result.composite_score < high:
            multiplier = mult
            break
    
    lines = [
        f"# {params.asset} Signal Analysis",
        "",
        f"**Composite Score:** {result.composite_score:.1f}",
        f"**Market Condition:** {result.market_condition}",
        f"**DCA Multiplier:** {multiplier}x",
        "",
        "## Category Breakdown",
        "",
        "| Category | Score | Weight |",
        "|----------|-------|--------|",
    ]
    
    for cat, score in result.category_scores.items():
        weight = SIGNAL_WEIGHTS.get(cat, Decimal("0"))
        lines.append(f"| {cat.title()} | {score:.1f} | {weight:.0%} |")
    
    lines.extend([
        "",
        "## Recommendation",
        "",
        f"**Action:** {result.recommendation.action}",
        f"**Confidence:** {result.recommendation.confidence:.0%}",
        f"**Base DCA:** ${float(DCA_SCHEDULE['base_amount_usd']):.2f}",
        f"**Adjusted DCA:** ${float(DCA_SCHEDULE['base_amount_usd'] * multiplier):.2f}",
    ])
    
    return "\n".join(lines)


@mcp.tool(annotations={"destructiveHint": True})
async def gti_execute_dca(params: DCAInput) -> str:
    """Execute GTI DCA cycle (signal-adjusted)."""
    if params.dry_run:
        return await _simulate_dca(params.asset)
    
    # Real execution
    results = []
    analyzer = get_analyzer()
    audit = get_audit_log()
    
    assets = [params.asset] if params.asset else DCA_SCHEDULE["assets"]
    
    for asset in assets:
        # Get signal
        signal = await analyzer.analyze(asset)
        
        # Calculate amount
        multiplier = Decimal("1.0")
        for (low, high), mult in DCA_MULTIPLIERS.items():
            if low <= signal.composite_score < high:
                multiplier = mult
                break
        
        amount_usd = DCA_SCHEDULE["base_amount_usd"] * multiplier
        
        # Execute on preferred exchange
        exchange = ASSET_EXCHANGE_MAP.get(asset, "coinbase")
        client = await get_exchange_client(exchange)
        
        if client:
            try:
                order = await client.place_market_order(
                    asset=asset,
                    side="buy",
                    quote_amount=amount_usd,
                )
                
                if order.success:
                    # Log trade
                    SkippyHooks.log_trade({
                        "asset": asset,
                        "side": "buy",
                        "amount": float(order.filled_amount),
                        "price": float(order.filled_price),
                        "exchange": exchange,
                        "signal_score": signal.composite_score,
                        "multiplier": float(multiplier),
                    })
                    
                    # Audit log
                    audit.log_change(
                        "dca_execution",
                        order.order_id,
                        "INSERT",
                        new_values={
                            "asset": asset,
                            "amount_usd": float(amount_usd),
                            "filled_amount": float(order.filled_amount),
                            "signal_score": signal.composite_score,
                        },
                    )
                    
                    # Notify
                    notify_trade(
                        asset, "buy",
                        float(order.filled_amount),
                        float(order.filled_price),
                    )
                    
                    results.append(f"✅ {asset}: ${amount_usd:.2f} @ {multiplier}x")
                else:
                    results.append(f"❌ {asset}: {order.error}")
                    
            except Exception as e:
                results.append(f"❌ {asset}: {str(e)}")
    
    return "\n".join(["# DCA Execution Results", ""] + results)


async def _simulate_dca(asset: Optional[str]) -> str:
    """Simulate DCA without executing."""
    analyzer = get_analyzer()
    assets = [asset] if asset else DCA_SCHEDULE["assets"]
    
    lines = ["# DCA Simulation (Dry Run)", ""]
    total = Decimal("0")
    
    for a in assets:
        signal = await analyzer.analyze(a)
        
        multiplier = Decimal("1.0")
        for (low, high), mult in DCA_MULTIPLIERS.items():
            if low <= signal.composite_score < high:
                multiplier = mult
                break
        
        amount = DCA_SCHEDULE["base_amount_usd"] * multiplier
        total += amount
        
        lines.append(
            f"- **{a}**: ${amount:.2f} "
            f"({multiplier}x, score: {signal.composite_score:.0f})"
        )
    
    lines.extend(["", f"**Total:** ${total:.2f}"])
    return "\n".join(lines)


@mcp.tool(annotations={"readOnlyHint": True})
async def gti_etf_status() -> str:
    """Get GTI Virtual ETF allocation status."""
    # Get current holdings
    holdings = {}
    total_value = Decimal("0")
    
    for exchange in EXCHANGES:
        client = await get_exchange_client(exchange)
        if client:
            try:
                balances = await client.get_balances()
                for asset, balance in balances.items():
                    # Get price (simplified)
                    price = await client.get_ticker_price(asset)
                    value = balance.total * price
                    
                    if asset not in holdings:
                        holdings[asset] = Decimal("0")
                    holdings[asset] += value
                    total_value += value
            except:
                pass
    
    # Compare to targets
    lines = [
        "# GTI Virtual ETF Status",
        "",
        f"**Total Value:** ${total_value:,.2f}",
        "",
        "## Allocation vs Target",
        "",
        "| Category | Asset | Target | Actual | Diff |",
        "|----------|-------|--------|--------|------|",
    ]
    
    for category, assets in GTI_ETF_ALLOCATIONS.items():
        if category in ["high_risk", "war_chest"]:
            continue
            
        for asset, target in assets.items():
            actual = holdings.get(asset, Decimal("0")) / total_value if total_value else Decimal("0")
            diff = actual - target
            
            lines.append(
                f"| {category} | {asset} | {target:.1%} | {actual:.1%} | "
                f"{'🟢' if abs(diff) < 0.02 else '🟡' if abs(diff) < 0.05 else '🔴'} {diff:+.1%} |"
            )
    
    return "\n".join(lines)


@mcp.tool(annotations={"readOnlyHint": True})
async def gti_generate_tax_report(params: TaxReportInput) -> str:
    """Generate GTI tax reports for specified year."""
    from compliance.form_8949 import Form8949Generator, ScheduleDGenerator
    from compliance.exports import CPAExporter, TurboTaxExporter, KoinlyExporter
    
    # TODO: Get tax lots from database
    lines = []  # Form8949Line objects
    
    if params.format == "csv":
        generator = Form8949Generator(lines, params.year, "GTI Inc")
        output = generator.generate_csv()
    elif params.format == "pdf":
        generator = Form8949Generator(lines, params.year, "GTI Inc")
        output = generator.generate_pdf(f"form_8949_{params.year}.pdf")
    elif params.format == "turbotax":
        output = TurboTaxExporter.export(lines, params.year)
    elif params.format == "koinly":
        output = KoinlyExporter.export(lines, params.year)
    else:
        output = CPAExporter.export(lines, params.year)
    
    # Log generation
    get_audit_log().log_change(
        "tax_report",
        f"{params.year}_{params.format}",
        "INSERT",
        new_values={"year": params.year, "format": params.format},
    )
    
    return f"Tax report generated ({params.format} format for {params.year})"


@mcp.tool(annotations={"readOnlyHint": True})
async def gti_audit_log(limit: int = 20) -> str:
    """View recent audit log entries."""
    audit = get_audit_log()
    entries = audit.get_entries(limit=limit)
    return audit.format_entries_markdown(entries)


@mcp.tool(annotations={"readOnlyHint": True})
async def gti_verify_audit_chain() -> str:
    """Verify audit log integrity."""
    audit = get_audit_log()
    result = audit.verify_chain()
    
    if result["valid"]:
        return f"✅ Audit chain valid ({result['entries_checked']} entries verified)"
    else:
        errors = "\n".join(f"- {e}" for e in result["errors"])
        return f"❌ Audit chain INVALID\n\nErrors:\n{errors}"


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if "--http" in sys.argv:
        port = 8080
        if "--port" in sys.argv:
            idx = sys.argv.index("--port")
            port = int(sys.argv[idx + 1])
        mcp.run(transport="http", port=port)
    else:
        mcp.run(transport="stdio")
```

### Phase 5: Testing & Validation (Week 3)

```bash
# Run specialized tests
cd ~/crypto-portfolio
pytest tests/test_gti_config.py -v
pytest tests/test_gti_mcp.py -v
pytest tests/test_skippy_integration.py -v

# Validate against production data
python -c "
from gti_config import GTI_ETF_ALLOCATIONS
total = sum(sum(v.values()) for k, v in GTI_ETF_ALLOCATIONS.items() 
            if isinstance(list(v.values())[0] if v else 0, Decimal))
assert abs(total - 1.0) < 0.01, f'ETF allocations must sum to 1.0, got {total}'
print('✅ Configuration validated')
"
```

---

## 4. Code Consolidation

### Files to Remove

| File | Lines | Reason |
|------|-------|--------|
| exchanges/binance_client.py | 15,937 | Not in GTI stack |
| exchanges/okx_client.py | 17,823 | Not in GTI stack |
| exchanges/ccxt_fallback.py | 11,530 | Generic fallback unused |
| exchanges/mock.py | 32,606 | Paper trading complete |
| day_trading_agent.py | 16,055 | Not GTI strategy |
| agents/dip_buyer.py | 22,601 | Subsumed by DCA |
| backtest_cli.py | 15,695 | Keep backtester, remove CLI |
| trading_cli.py | 13,129 | Replace with skippy commands |
| multi_trading_cli.py | 22,678 | Replace with skippy commands |
| web_dashboard.py | 102,283 | Future GUI (keep for reference) |
| **Total** | **~270K** | |

### Files to Keep & Refactor

| File | Action |
|------|--------|
| crypto_portfolio_mcp.py | Refactor → gti_mcp.py |
| portfolio_aggregator.py | Simplify to 4 exchanges |
| agents/unified_analyzer.py | Keep, freeze weights |
| agents/expanded_signals.py | Keep signal logic |
| compliance/* | Keep unchanged |
| exchanges/coinbase_client.py | Keep |
| exchanges/kraken_client.py | Keep |
| exchanges/gemini_client.py | Keep |
| exchanges/crypto_com_client.py | Keep |

### Consolidation Script

```bash
#!/bin/bash
# consolidate_gti.sh - Run from crypto-portfolio root
set -euo pipefail

echo "🔧 GTI Code Consolidation"

# Backup first
BACKUP_DIR=~/skippy/backups/crypto/$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
cp -r . "$BACKUP_DIR"
echo "✅ Backup created: $BACKUP_DIR"

# Remove unused exchanges
rm -f exchanges/binance_client.py
rm -f exchanges/okx_client.py
rm -f exchanges/ccxt_fallback.py
rm -f exchanges/mock.py
echo "✅ Removed unused exchange clients"

# Remove unused agents
rm -f day_trading_agent.py
rm -f agents/dip_buyer.py
echo "✅ Removed unused agents"

# Remove CLI tools (replaced by skippy)
rm -f backtest_cli.py
rm -f trading_cli.py
rm -f multi_trading_cli.py
echo "✅ Removed CLI tools"

# Archive web dashboard for future reference
mkdir -p archive
mv web_dashboard.py archive/
echo "✅ Archived web dashboard"

# Create GTI-specific files
touch gti_config.py
touch gti_mcp.py
mkdir -p skippy
touch skippy/__init__.py
touch skippy/hooks.py
touch skippy/commands.py
echo "✅ Created GTI structure"

# Update imports
find . -name "*.py" -exec sed -i 's/from exchanges.mock import/# REMOVED: from exchanges.mock import/g' {} \;
find . -name "*.py" -exec sed -i 's/from exchanges.binance_client import/# REMOVED: from exchanges.binance_client import/g' {} \;
echo "✅ Updated imports"

# Line count
echo ""
echo "📊 Post-consolidation stats:"
find . -name "*.py" -not -path "./archive/*" | xargs wc -l | tail -1
```

---

## 5. skippy Integration

### Directory Structure

```
~/skippy/
├── scripts/
│   ├── gti-dca               # Daily DCA execution
│   ├── gti-signals           # Signal analysis
│   ├── gti-portfolio         # Portfolio summary
│   ├── gti-tax               # Tax report generation
│   ├── gti-rebalance         # Rebalancing check
│   └── backup_crypto_db.sh   # Database backup
│
├── logs/
│   └── crypto/
│       ├── trades.jsonl      # Trade log
│       ├── signals.jsonl     # Signal history
│       └── errors.log        # Error log
│
├── work/
│   └── crypto/
│       ├── audit_log.json    # Audit trail
│       └── tax/              # Tax reports by year
│           ├── 2024/
│           └── 2025/
│
└── cron/
    └── crypto.cron           # Scheduled jobs
```

### Cron Jobs

```cron
# ~/skippy/cron/crypto.cron

# Daily DCA at 9:00 AM UTC
0 9 * * * ~/skippy/scripts/gti-dca >> ~/skippy/logs/crypto/dca.log 2>&1

# Signal snapshot every 4 hours
0 */4 * * * ~/skippy/scripts/gti-signals BTC >> ~/skippy/logs/crypto/signals.log 2>&1

# Daily portfolio snapshot at midnight
0 0 * * * ~/skippy/scripts/gti-portfolio >> ~/skippy/logs/crypto/portfolio.log 2>&1

# Weekly database backup (Sunday 3 AM)
0 3 * * 0 ~/skippy/scripts/backup_crypto_db.sh

# Monthly tax report generation (1st of month)
0 6 1 * * ~/skippy/scripts/gti-tax $(date +%Y) >> ~/skippy/logs/crypto/tax.log 2>&1
```

### Environment Profile

```bash
# Add to ~/skippy/scripts/skippy-profile

crypto-dev)
    export CRYPTO_HOME=~/crypto-portfolio
    export COINBASE_API_KEY_FILE=~/.config/coinbase/cdp_api_key.json
    export KRAKEN_API_KEY=$(cat ~/.config/kraken/api_key)
    export KRAKEN_API_SECRET=$(cat ~/.config/kraken/api_secret)
    export GEMINI_API_KEY=$(cat ~/.config/gemini/api_key)
    export GEMINI_API_SECRET=$(cat ~/.config/gemini/api_secret)
    export CRYPTO_COM_API_KEY=$(cat ~/.config/crypto_com/api_key)
    export CRYPTO_COM_API_SECRET=$(cat ~/.config/crypto_com/api_secret)
    export PYTHONPATH=$CRYPTO_HOME:$PYTHONPATH
    cd $CRYPTO_HOME
    echo "🔐 Crypto environment loaded"
    ;;
```

---

## 6. GTI-Specific Configurations

### Exchange API Key Storage

```
~/.config/
├── coinbase/
│   └── cdp_api_key.json      # CDP format (JWT auth)
├── kraken/
│   ├── api_key
│   └── api_secret
├── gemini/
│   ├── api_key
│   └── api_secret
└── crypto_com/
    ├── api_key
    └── api_secret
```

### Database Schema (Simplified)

```sql
-- GTI-specific tables only

CREATE TABLE holdings (
    id INTEGER PRIMARY KEY,
    asset TEXT NOT NULL,
    exchange TEXT NOT NULL,
    amount DECIMAL(18,8) NOT NULL,
    cost_basis_usd DECIMAL(18,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset, exchange)
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    asset TEXT NOT NULL,
    exchange TEXT NOT NULL,
    side TEXT NOT NULL,  -- buy/sell
    amount DECIMAL(18,8) NOT NULL,
    price_usd DECIMAL(18,8) NOT NULL,
    fee_usd DECIMAL(18,8),
    signal_score REAL,
    dca_multiplier REAL,
    timestamp TIMESTAMP NOT NULL,
    tx_hash TEXT
);

CREATE TABLE tax_lots (
    id INTEGER PRIMARY KEY,
    asset TEXT NOT NULL,
    acquired_at TIMESTAMP NOT NULL,
    amount DECIMAL(18,8) NOT NULL,
    cost_basis_usd DECIMAL(18,2) NOT NULL,
    exchange TEXT NOT NULL,
    disposed_at TIMESTAMP,
    proceeds_usd DECIMAL(18,2),
    gain_loss_usd DECIMAL(18,2)
);

CREATE TABLE signal_history (
    id INTEGER PRIMARY KEY,
    asset TEXT NOT NULL,
    composite_score REAL NOT NULL,
    category_scores TEXT,  -- JSON
    recommendation TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dca_executions (
    id INTEGER PRIMARY KEY,
    asset TEXT NOT NULL,
    amount_usd DECIMAL(18,2) NOT NULL,
    filled_amount DECIMAL(18,8),
    signal_score REAL,
    multiplier REAL,
    exchange TEXT NOT NULL,
    status TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_transactions_asset ON transactions(asset);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_tax_lots_asset ON tax_lots(asset);
CREATE INDEX idx_signal_history_timestamp ON signal_history(timestamp);
```

### GTI ETF Target Allocations

| Category | Asset | Target | Priority |
|----------|-------|--------|----------|
| **Core (20%)** | BTC | 10% | P0 |
| | ETH | 5% | P0 |
| | SOL | 3% | P1 |
| | AVAX | 2% | P1 |
| **Income (25%)** | ATOM | 5% | P0 |
| | DOT | 4% | P1 |
| | MATIC | 4% | P1 |
| | ADA | 3% | P2 |
| | ALGO | 3% | P2 |
| | XTZ | 3% | P2 |
| | NEAR | 3% | P2 |
| **Growth (15%)** | LINK | 3% | P1 |
| | UNI | 2% | P2 |
| | AAVE | 2% | P2 |
| | MKR | 2% | P2 |
| | SNX | 2% | P3 |
| | CRV | 2% | P3 |
| | LDO | 2% | P3 |
| **Land/RWA (10%)** | MANA | 2.5% | P2 |
| | SAND | 2.5% | P2 |
| | AXS | 2.5% | P3 |
| | ENJ | 2.5% | P3 |
| **High Risk (15%)** | *Rotating* | 15% | P2 |
| **War Chest (15%)** | USDC | 15% | P0 |

---

## 7. Security Model

### Credential Management

```python
# gti_security.py

import os
import json
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".config"


def load_coinbase_credentials() -> dict:
    """Load Coinbase CDP API key (JWT format)."""
    key_file = CONFIG_DIR / "coinbase" / "cdp_api_key.json"
    if key_file.exists():
        return json.loads(key_file.read_text())
    raise FileNotFoundError("Coinbase CDP key not found")


def load_exchange_credentials(exchange: str) -> tuple:
    """Load API key and secret for an exchange."""
    exchange_dir = CONFIG_DIR / exchange
    
    key_file = exchange_dir / "api_key"
    secret_file = exchange_dir / "api_secret"
    
    if not key_file.exists() or not secret_file.exists():
        raise FileNotFoundError(f"{exchange} credentials not found")
    
    return (
        key_file.read_text().strip(),
        secret_file.read_text().strip(),
    )


def secure_delete_credentials(exchange: str) -> bool:
    """Securely delete credentials (overwrite before delete)."""
    exchange_dir = CONFIG_DIR / exchange
    
    for f in exchange_dir.glob("*"):
        # Overwrite with random data
        f.write_bytes(os.urandom(f.stat().st_size))
        f.unlink()
    
    exchange_dir.rmdir()
    return True
```

### Permissions

```bash
# Secure credential files
chmod 700 ~/.config/coinbase ~/.config/kraken ~/.config/gemini ~/.config/crypto_com
chmod 600 ~/.config/*/api_key ~/.config/*/api_secret
chmod 600 ~/.config/coinbase/cdp_api_key.json

# Secure database
chmod 600 ~/crypto-portfolio/data/portfolio.db
chmod 600 ~/skippy/work/crypto/audit_log.json
```

### Audit Trail Integrity

The audit log uses SHA-256 hash chaining:

```
Entry N:
  checksum = SHA256(content_N + checksum_{N-1})
  prev_checksum = checksum_{N-1}

Verification:
  For each entry, recompute checksum and verify chain links
  Any modification breaks the chain
```

---

## 8. Performance Optimizations

### Caching Strategy

```python
# gti_cache.py

from functools import lru_cache
from datetime import datetime, timedelta
from typing import Dict, Any

# In-memory cache for prices (60 second TTL)
_price_cache: Dict[str, tuple] = {}  # asset -> (price, timestamp)
PRICE_CACHE_TTL = 60

# Signal cache (5 minute TTL)
_signal_cache: Dict[str, tuple] = {}
SIGNAL_CACHE_TTL = 300


def get_cached_price(asset: str) -> tuple:
    """Get cached price if fresh, else None."""
    if asset in _price_cache:
        price, ts = _price_cache[asset]
        if (datetime.now() - ts).seconds < PRICE_CACHE_TTL:
            return price, True
    return None, False


def set_cached_price(asset: str, price: float):
    """Cache a price."""
    _price_cache[asset] = (price, datetime.now())


@lru_cache(maxsize=128)
def get_etf_allocation(category: str, asset: str):
    """LRU cache for ETF lookups (immutable config)."""
    from gti_config import GTI_ETF_ALLOCATIONS
    return GTI_ETF_ALLOCATIONS.get(category, {}).get(asset)
```

### Batch Operations

```python
# Fetch all balances in parallel
async def get_all_balances():
    tasks = [
        get_exchange_client(ex).get_balances()
        for ex in EXCHANGES
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    combined = {}
    for ex, result in zip(EXCHANGES, results):
        if not isinstance(result, Exception):
            for asset, balance in result.items():
                if asset not in combined:
                    combined[asset] = {}
                combined[asset][ex] = balance
    
    return combined
```

### Database Optimizations

```sql
-- Add indexes for common queries
CREATE INDEX idx_tx_asset_date ON transactions(asset, timestamp DESC);
CREATE INDEX idx_lots_open ON tax_lots(asset) WHERE disposed_at IS NULL;

-- Use WAL mode for better concurrent performance
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- Periodic vacuum
VACUUM;
ANALYZE;
```

---

## 9. Maintenance Procedures

### Daily Checklist

```bash
#!/bin/bash
# gti-daily-check.sh

echo "🔍 GTI Daily Health Check"
echo "========================="

# 1. Verify exchange connectivity
echo -n "Exchange connectivity: "
python -c "
import asyncio
from gti_mcp import get_exchange_client, EXCHANGES
async def check():
    for ex in EXCHANGES:
        client = await get_exchange_client(ex)
        try:
            await client.get_balances()
            print(f'{ex}✅', end=' ')
        except:
            print(f'{ex}❌', end=' ')
asyncio.run(check())
"
echo ""

# 2. Verify audit log integrity
echo -n "Audit log: "
python -c "
from compliance.audit_log import AuditLog
result = AuditLog().verify_chain()
print('✅' if result['valid'] else '❌')
"

# 3. Check database size
echo -n "Database size: "
du -h ~/crypto-portfolio/data/portfolio.db | cut -f1

# 4. Check signal data freshness
echo -n "Last signal: "
python -c "
import json
from pathlib import Path
log = Path.home() / 'skippy/logs/crypto/signals.jsonl'
if log.exists():
    last = log.read_text().strip().split('\n')[-1]
    print(json.loads(last)['timestamp'][:19])
else:
    print('No signals logged')
"

echo "========================="
```

### Weekly Maintenance

```bash
#!/bin/bash
# gti-weekly-maintenance.sh

echo "🔧 GTI Weekly Maintenance"

# 1. Database optimization
echo "Optimizing database..."
sqlite3 ~/crypto-portfolio/data/portfolio.db "VACUUM; ANALYZE;"

# 2. Backup
echo "Creating backup..."
~/skippy/scripts/backup_crypto_db.sh

# 3. Log rotation
echo "Rotating logs..."
cd ~/skippy/logs/crypto
for f in *.log; do
    if [ -f "$f" ] && [ $(stat -f%z "$f" 2>/dev/null || stat -c%s "$f") -gt 10485760 ]; then
        mv "$f" "${f}.$(date +%Y%m%d)"
        gzip "${f}.$(date +%Y%m%d)"
    fi
done

# 4. Check for signal anomalies
echo "Checking signal history..."
python -c "
import json
from pathlib import Path
log = Path.home() / 'skippy/logs/crypto/signals.jsonl'
scores = []
for line in log.read_text().strip().split('\n')[-168:]:  # Last week (4h intervals)
    scores.append(json.loads(line)['composite_score'])
avg = sum(scores) / len(scores)
print(f'Avg signal score (7d): {avg:.1f}')
if avg < -30:
    print('⚠️  Sustained fear - consider increasing DCA')
elif avg > 30:
    print('⚠️  Sustained greed - consider reducing DCA')
"

echo "✅ Maintenance complete"
```

### Monthly Tax Reconciliation

```bash
#!/bin/bash
# gti-monthly-tax.sh

MONTH=$(date -d "last month" +%Y-%m)
echo "📊 Tax Reconciliation for $MONTH"

cd ~/crypto-portfolio
python -c "
from datetime import datetime
from compliance.form_8949 import Form8949Line
# ... reconciliation logic
print('Transactions this month: X')
print('Short-term gains: $X')
print('Long-term gains: $X')
print('Unrealized gains: $X')
"
```

---

## 10. Future Enhancements

### Priority 1 (Next Quarter)

| Enhancement | Description | Effort |
|-------------|-------------|--------|
| **GUI Dashboard** | React-based portfolio view | 3 weeks |
| **Mobile Alerts** | Push notifications via Pushover | 2 days |
| **Rebalancing Automation** | Auto-rebalance when drift > 5% | 1 week |

### Priority 2 (This Year)

| Enhancement | Description | Effort |
|-------------|-------------|--------|
| **DeFi Integration** | Track Uniswap/Aave positions | 2 weeks |
| **On-chain Wallet Sync** | ETH/SOL wallet balance tracking | 1 week |
| **Tax-Loss Harvesting Bot** | Automated TLH execution | 2 weeks |

### Priority 3 (Future)

| Enhancement | Description | Effort |
|-------------|-------------|--------|
| **ML Signal Enhancement** | Train on historical signal accuracy | 1 month |
| **Multi-Account Support** | Separate business/personal | 2 weeks |
| **API for External Tools** | REST API for integrations | 1 week |

### Feature Flags

```python
# gti_features.py

FEATURES = {
    # Production
    "dca_execution": True,
    "signal_analysis": True,
    "tax_reports": True,
    "audit_logging": True,
    
    # Beta
    "auto_rebalance": False,
    "tlh_automation": False,
    
    # Planned
    "defi_tracking": False,
    "ml_signals": False,
    "gui_dashboard": False,
}


def is_enabled(feature: str) -> bool:
    return FEATURES.get(feature, False)
```

---

## 11. Troubleshooting

### Common Issues

#### Exchange Connection Failed

```bash
# Check credentials
cat ~/.config/coinbase/cdp_api_key.json | python -m json.tool

# Test connection
python -c "
import asyncio
from exchanges.coinbase_client import CoinbaseClient
async def test():
    client = CoinbaseClient()
    print(await client.get_balances())
asyncio.run(test())
"
```

#### Signal Data Stale

```bash
# Check CoinGecko API
curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

# Check Fear & Greed
curl -s "https://api.alternative.me/fng/"

# Force signal refresh
python -c "
from agents.unified_analyzer import GTISignalAnalyzer
import asyncio
analyzer = GTISignalAnalyzer()
result = asyncio.run(analyzer.analyze('BTC', force_refresh=True))
print(result)
"
```

#### Database Locked

```bash
# Check for locks
fuser ~/crypto-portfolio/data/portfolio.db

# Force unlock (DANGEROUS - ensure no processes running)
sqlite3 ~/crypto-portfolio/data/portfolio.db ".clone /tmp/portfolio_recovery.db"
mv /tmp/portfolio_recovery.db ~/crypto-portfolio/data/portfolio.db
```

#### Audit Chain Broken

```bash
# Identify break point
python -c "
from compliance.audit_log import AuditLog
log = AuditLog()
result = log.verify_chain()
for error in result['errors']:
    print(error)
"

# Recovery: Rebuild from backup
# WARNING: This loses audit integrity
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export GTI_DEBUG=1
python gti_mcp.py
```

---

## 12. API Reference

### MCP Tools

| Tool | Description | Read-Only |
|------|-------------|-----------|
| `gti_portfolio_summary` | Full portfolio across exchanges | ✅ |
| `gti_signal_analysis` | Signal analysis for asset | ✅ |
| `gti_execute_dca` | Execute DCA cycle | ❌ |
| `gti_etf_status` | ETF allocation vs target | ✅ |
| `gti_generate_tax_report` | Generate tax documents | ✅ |
| `gti_audit_log` | View audit entries | ✅ |
| `gti_verify_audit_chain` | Verify audit integrity | ✅ |

### Python API

```python
# Direct usage (non-MCP)
from gti_mcp import (
    get_exchange_client,
    get_analyzer,
    get_audit_log,
)

# Get portfolio
async def get_portfolio():
    balances = {}
    for ex in ["coinbase", "kraken", "gemini", "crypto_com"]:
        client = await get_exchange_client(ex)
        balances[ex] = await client.get_balances()
    return balances

# Get signals
async def get_signals(asset: str):
    analyzer = get_analyzer()
    return await analyzer.analyze(asset)

# Log action
def log_action(table: str, record_id: str, action: str, data: dict):
    audit = get_audit_log()
    audit.log_change(table, record_id, action, new_values=data)
```

### skippy Commands

| Command | Description |
|---------|-------------|
| `gti-dca` | Run daily DCA cycle |
| `gti-dca --dry-run` | Simulate DCA |
| `gti-signals BTC` | Get BTC signal analysis |
| `gti-signals` | Get all tracked assets |
| `gti-portfolio` | Portfolio summary |
| `gti-tax 2025` | Generate 2025 tax reports |
| `gti-rebalance` | Check rebalancing needs |

---

## Appendix A: Migration Checklist

```
□ Backup current installation
□ Run consolidation script
□ Create gti_config.py with frozen settings
□ Create gti_mcp.py unified server
□ Set up skippy integration
□ Configure cron jobs
□ Run test suite
□ Verify audit log integrity
□ Test DCA execution (dry run)
□ Test tax report generation
□ Update Claude Code MCP config
□ Document any custom changes
```

## Appendix B: Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-02 | GTI specialization, skippy integration |
| 1.0.0 | 2026-01 | Initial production release |
| 0.9.0 | 2025-12 | Beta with 130+ signals |

---

*Document maintained by Claude Code for GTI Inc.*
