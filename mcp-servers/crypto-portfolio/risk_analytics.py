"""
Risk Analytics Module
=====================

Portfolio risk analysis tools including:
- Value at Risk (VaR) - Historical, Parametric, Monte Carlo methods
- Conditional VaR (CVaR / Expected Shortfall)
- Portfolio stress testing (market crash, correlation spike, liquidity crisis)
- Risk-adjusted return ratios (Sharpe, Sortino, Calmar)
"""

import json
import math
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# INPUT MODEL
# =============================================================================


class RiskAnalysisInput(BaseModel):
    """Input for portfolio risk analysis."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    portfolio: Optional[Dict[str, float]] = Field(
        default=None,
        description=(
            "Portfolio weights as {asset: weight} (e.g., {'BTC': 0.5, 'ETH': 0.3, 'SOL': 0.2}). "
            "If not provided, uses current portfolio from exchange holdings."
        ),
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.9,
        le=0.99,
        description="Confidence level for VaR/CVaR (0.90-0.99, default 0.95)",
    )
    time_horizon_days: int = Field(
        default=1,
        ge=1,
        le=30,
        description="Time horizon in days for risk calculations (1-30)",
    )
    include_stress_tests: bool = Field(
        default=True,
        description="Include portfolio stress test scenarios",
    )
    include_ratios: bool = Field(
        default=True,
        description="Include risk-adjusted return ratios (Sharpe, Sortino, Calmar)",
    )
    monte_carlo_sims: int = Field(
        default=10000,
        ge=1000,
        le=100000,
        description="Number of Monte Carlo simulations for MC VaR",
    )
    response_format: str = Field(
        default="markdown",
        description="Output format: 'markdown' or 'json'",
        pattern=r"^(markdown|json)$",
    )


# =============================================================================
# RISK CALCULATION ENGINE
# =============================================================================


# Approximate annualized daily return stats for major crypto assets.
# In production, these would be fetched from a price history API.
ASSET_STATS = {
    "BTC": {"daily_return": 0.0003, "daily_vol": 0.035, "annual_return": 0.12},
    "ETH": {"daily_return": 0.0004, "daily_vol": 0.045, "annual_return": 0.15},
    "SOL": {"daily_return": 0.0006, "daily_vol": 0.065, "annual_return": 0.20},
    "BNB": {"daily_return": 0.0003, "daily_vol": 0.040, "annual_return": 0.10},
    "XRP": {"daily_return": 0.0002, "daily_vol": 0.050, "annual_return": 0.08},
    "ADA": {"daily_return": 0.0002, "daily_vol": 0.055, "annual_return": 0.06},
    "AVAX": {"daily_return": 0.0005, "daily_vol": 0.060, "annual_return": 0.18},
    "DOT": {"daily_return": 0.0003, "daily_vol": 0.055, "annual_return": 0.10},
    "MATIC": {"daily_return": 0.0004, "daily_vol": 0.060, "annual_return": 0.14},
    "LINK": {"daily_return": 0.0003, "daily_vol": 0.050, "annual_return": 0.12},
    "USDC": {"daily_return": 0.0, "daily_vol": 0.0005, "annual_return": 0.04},
    "USDT": {"daily_return": 0.0, "daily_vol": 0.0005, "annual_return": 0.04},
}

# Default correlation assumptions between major crypto assets
DEFAULT_CORRELATION = 0.65

# Stress test scenario definitions
STRESS_SCENARIOS = {
    "market_crash_2022": {
        "name": "2022 Crypto Winter",
        "description": "Extended bear market similar to 2022 (BTC -65%, alts -80%+)",
        "shocks": {
            "BTC": -0.65, "ETH": -0.72, "SOL": -0.90, "BNB": -0.55,
            "XRP": -0.60, "ADA": -0.85, "AVAX": -0.88, "DOT": -0.85,
            "MATIC": -0.82, "LINK": -0.75, "USDC": -0.005, "USDT": -0.005,
        },
    },
    "flash_crash": {
        "name": "Flash Crash (-30% in 24h)",
        "description": "Sudden market-wide deleveraging event",
        "shocks": {
            "BTC": -0.30, "ETH": -0.35, "SOL": -0.45, "BNB": -0.32,
            "XRP": -0.38, "ADA": -0.42, "AVAX": -0.45, "DOT": -0.40,
            "MATIC": -0.42, "LINK": -0.38, "USDC": -0.01, "USDT": -0.01,
        },
    },
    "correlation_spike": {
        "name": "Correlation Spike to 1.0",
        "description": "All assets move together during panic selling; effective portfolio diversification drops to zero",
        "shocks": {
            "BTC": -0.25, "ETH": -0.25, "SOL": -0.25, "BNB": -0.25,
            "XRP": -0.25, "ADA": -0.25, "AVAX": -0.25, "DOT": -0.25,
            "MATIC": -0.25, "LINK": -0.25, "USDC": -0.005, "USDT": -0.005,
        },
    },
    "stablecoin_depeg": {
        "name": "Stablecoin Depeg Event",
        "description": "Major stablecoin loses peg (similar to UST collapse), contagion across market",
        "shocks": {
            "BTC": -0.15, "ETH": -0.20, "SOL": -0.30, "BNB": -0.18,
            "XRP": -0.22, "ADA": -0.28, "AVAX": -0.30, "DOT": -0.28,
            "MATIC": -0.30, "LINK": -0.25, "USDC": -0.10, "USDT": -0.05,
        },
    },
    "regulatory_crackdown": {
        "name": "Major Regulatory Action",
        "description": "US or EU announces exchange bans or heavy taxation",
        "shocks": {
            "BTC": -0.20, "ETH": -0.25, "SOL": -0.35, "BNB": -0.40,
            "XRP": -0.50, "ADA": -0.35, "AVAX": -0.35, "DOT": -0.30,
            "MATIC": -0.35, "LINK": -0.30, "USDC": -0.02, "USDT": -0.02,
        },
    },
}


def _get_asset_stats(asset: str) -> Dict[str, float]:
    """Get stats for an asset, with sensible defaults for unknown assets."""
    return ASSET_STATS.get(
        asset.upper(),
        {"daily_return": 0.0003, "daily_vol": 0.055, "annual_return": 0.10},
    )


def _portfolio_daily_vol(weights: Dict[str, float]) -> float:
    """
    Estimate portfolio daily volatility using asset vols and a uniform
    pairwise correlation assumption.
    """
    assets = list(weights.keys())
    n = len(assets)
    if n == 0:
        return 0.0

    vols = [_get_asset_stats(a)["daily_vol"] for a in assets]
    w = [weights[a] for a in assets]

    # variance = sum_i sum_j w_i * w_j * vol_i * vol_j * corr_ij
    variance = 0.0
    for i in range(n):
        for j in range(n):
            corr = 1.0 if i == j else DEFAULT_CORRELATION
            variance += w[i] * w[j] * vols[i] * vols[j] * corr

    return math.sqrt(max(variance, 0.0))


def _portfolio_daily_return(weights: Dict[str, float]) -> float:
    """Weighted average daily return."""
    return sum(
        weights[a] * _get_asset_stats(a)["daily_return"]
        for a in weights
    )


def _z_score(confidence: float) -> float:
    """Approximate z-score for a given confidence level using rational approximation."""
    # Beasley-Springer-Moro approximation for inverse normal
    p = 1.0 - confidence
    if p <= 0 or p >= 1:
        return 2.326  # fallback for 99%

    t = math.sqrt(-2.0 * math.log(p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t * t * t)


def compute_parametric_var(
    weights: Dict[str, float],
    confidence: float,
    horizon_days: int,
) -> float:
    """
    Parametric VaR assuming normal distribution.
    Returns loss as a positive percentage.
    """
    daily_vol = _portfolio_daily_vol(weights)
    daily_mean = _portfolio_daily_return(weights)
    z = _z_score(confidence)

    # Scale to horizon
    horizon_vol = daily_vol * math.sqrt(horizon_days)
    horizon_mean = daily_mean * horizon_days

    return max(z * horizon_vol - horizon_mean, 0.0)


def compute_historical_var(
    weights: Dict[str, float],
    confidence: float,
    horizon_days: int,
    num_scenarios: int = 1000,
) -> Dict[str, float]:
    """
    Historical simulation VaR using synthetic returns based on asset statistics.
    Returns VaR and CVaR as positive percentages.
    """
    assets = list(weights.keys())
    w = [weights[a] for a in assets]
    stats = [_get_asset_stats(a) for a in assets]

    # Generate correlated returns using a simple factor model
    portfolio_returns = []
    for _ in range(num_scenarios):
        common_factor = random.gauss(0, 1)
        daily_returns = []
        for s in stats:
            # Correlated return: sqrt(corr)*common + sqrt(1-corr)*idiosyncratic
            idio = random.gauss(0, 1)
            r = s["daily_return"] + s["daily_vol"] * (
                math.sqrt(DEFAULT_CORRELATION) * common_factor
                + math.sqrt(1.0 - DEFAULT_CORRELATION) * idio
            )
            daily_returns.append(r)

        # Compound over horizon
        port_return = 0.0
        for _ in range(horizon_days):
            period_return = sum(
                w[i] * daily_returns[i] for i in range(len(assets))
            )
            port_return = (1.0 + port_return) * (1.0 + period_return) - 1.0

        portfolio_returns.append(port_return)

    portfolio_returns.sort()

    # VaR at the confidence percentile
    var_index = int((1.0 - confidence) * num_scenarios)
    var_index = max(0, min(var_index, num_scenarios - 1))
    var_value = -portfolio_returns[var_index]

    # CVaR = average of losses beyond VaR
    tail = portfolio_returns[: var_index + 1]
    cvar_value = -sum(tail) / len(tail) if tail else var_value

    return {"var": max(var_value, 0.0), "cvar": max(cvar_value, 0.0)}


def compute_monte_carlo_var(
    weights: Dict[str, float],
    confidence: float,
    horizon_days: int,
    num_sims: int = 10000,
) -> Dict[str, float]:
    """
    Monte Carlo VaR using geometric Brownian motion.
    Returns VaR and CVaR as positive percentages.
    """
    assets = list(weights.keys())
    w = [weights[a] for a in assets]
    stats = [_get_asset_stats(a) for a in assets]

    portfolio_returns = []
    for _ in range(num_sims):
        # Simulate each asset's path over the horizon
        asset_returns = []
        common_factor = random.gauss(0, 1)

        for s in stats:
            cumulative = 1.0
            for _ in range(horizon_days):
                idio = random.gauss(0, 1)
                z = (
                    math.sqrt(DEFAULT_CORRELATION) * common_factor
                    + math.sqrt(1.0 - DEFAULT_CORRELATION) * idio
                )
                daily_r = s["daily_return"] + s["daily_vol"] * z
                cumulative *= 1.0 + daily_r
            asset_returns.append(cumulative - 1.0)

        port_return = sum(w[i] * asset_returns[i] for i in range(len(assets)))
        portfolio_returns.append(port_return)

    portfolio_returns.sort()

    var_index = int((1.0 - confidence) * num_sims)
    var_index = max(0, min(var_index, num_sims - 1))
    var_value = -portfolio_returns[var_index]

    tail = portfolio_returns[: var_index + 1]
    cvar_value = -sum(tail) / len(tail) if tail else var_value

    return {"var": max(var_value, 0.0), "cvar": max(cvar_value, 0.0)}


def compute_stress_tests(
    weights: Dict[str, float],
) -> List[Dict[str, Any]]:
    """Apply predefined stress scenarios to the portfolio."""
    results = []

    for scenario_id, scenario in STRESS_SCENARIOS.items():
        portfolio_loss = 0.0
        asset_impacts = {}

        for asset, weight in weights.items():
            shock = scenario["shocks"].get(
                asset.upper(),
                -0.30,  # default shock for unknown assets
            )
            impact = weight * shock
            portfolio_loss += impact
            asset_impacts[asset] = {
                "weight": round(weight, 4),
                "shock_pct": round(shock * 100, 1),
                "contribution_pct": round(impact * 100, 2),
            }

        results.append(
            {
                "scenario_id": scenario_id,
                "name": scenario["name"],
                "description": scenario["description"],
                "portfolio_loss_pct": round(portfolio_loss * 100, 2),
                "asset_impacts": asset_impacts,
            }
        )

    # Sort by severity (most negative first)
    results.sort(key=lambda x: x["portfolio_loss_pct"])
    return results


def compute_ratios(
    weights: Dict[str, float],
    risk_free_rate: float = 0.045,
) -> Dict[str, float]:
    """
    Compute risk-adjusted return ratios.

    Args:
        weights: Portfolio weights
        risk_free_rate: Annual risk-free rate (default 4.5% for T-bills)
    """
    # Annualized figures
    annual_return = sum(
        weights[a] * _get_asset_stats(a)["annual_return"]
        for a in weights
    )
    daily_vol = _portfolio_daily_vol(weights)
    annual_vol = daily_vol * math.sqrt(365)

    # Sharpe Ratio = (Rp - Rf) / sigma_p
    sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0.0

    # Sortino approximation: assume downside vol ~ 70% of total vol for crypto
    downside_vol = annual_vol * 0.70
    sortino = (annual_return - risk_free_rate) / downside_vol if downside_vol > 0 else 0.0

    # Calmar approximation: use parametric VaR as drawdown proxy
    # For annual horizon, estimate max drawdown
    param_var = compute_parametric_var(weights, 0.95, 365)
    calmar = annual_return / param_var if param_var > 0 else 0.0

    return {
        "sharpe_ratio": round(sharpe, 3),
        "sortino_ratio": round(sortino, 3),
        "calmar_ratio": round(calmar, 3),
        "annual_return_pct": round(annual_return * 100, 2),
        "annual_volatility_pct": round(annual_vol * 100, 2),
        "risk_free_rate_pct": round(risk_free_rate * 100, 2),
    }


def _normalize_weights(portfolio: Dict[str, float]) -> Dict[str, float]:
    """Normalize portfolio weights to sum to 1.0."""
    total = sum(portfolio.values())
    if total <= 0:
        return portfolio
    return {k: v / total for k, v in portfolio.items()}


def run_risk_analysis(params: RiskAnalysisInput) -> Dict[str, Any]:
    """Run full risk analysis and return structured results."""
    # Use provided portfolio or a default demo portfolio
    if params.portfolio:
        weights = _normalize_weights(params.portfolio)
    else:
        weights = {"BTC": 0.45, "ETH": 0.30, "SOL": 0.15, "USDC": 0.10}

    result: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "portfolio": {k: round(v, 4) for k, v in weights.items()},
        "confidence_level": params.confidence_level,
        "time_horizon_days": params.time_horizon_days,
    }

    # Parametric VaR
    param_var = compute_parametric_var(
        weights, params.confidence_level, params.time_horizon_days
    )
    result["parametric_var"] = {
        "var_pct": round(param_var * 100, 2),
        "method": "Variance-Covariance (Normal)",
    }

    # Historical VaR + CVaR
    hist = compute_historical_var(
        weights, params.confidence_level, params.time_horizon_days
    )
    result["historical_var"] = {
        "var_pct": round(hist["var"] * 100, 2),
        "cvar_pct": round(hist["cvar"] * 100, 2),
        "method": "Historical Simulation (1000 scenarios)",
    }

    # Monte Carlo VaR + CVaR
    mc = compute_monte_carlo_var(
        weights,
        params.confidence_level,
        params.time_horizon_days,
        num_sims=params.monte_carlo_sims,
    )
    result["monte_carlo_var"] = {
        "var_pct": round(mc["var"] * 100, 2),
        "cvar_pct": round(mc["cvar"] * 100, 2),
        "method": f"Monte Carlo ({params.monte_carlo_sims:,} simulations)",
    }

    # Stress tests
    if params.include_stress_tests:
        result["stress_tests"] = compute_stress_tests(weights)

    # Risk-adjusted ratios
    if params.include_ratios:
        result["risk_ratios"] = compute_ratios(weights)

    return result


def format_risk_markdown(data: Dict[str, Any]) -> str:
    """Format risk analysis results as markdown."""
    md = "# Portfolio Risk Analysis\n\n"

    # Portfolio composition
    md += "## Portfolio Composition\n"
    md += "| Asset | Weight |\n|-------|--------|\n"
    for asset, weight in data["portfolio"].items():
        md += f"| {asset} | {weight:.1%} |\n"
    md += "\n"

    conf = data["confidence_level"]
    horizon = data["time_horizon_days"]
    horizon_label = f"{horizon}-day" if horizon > 1 else "1-day"

    # VaR Summary
    md += f"## Value at Risk ({conf:.0%} confidence, {horizon_label} horizon)\n\n"
    md += "| Method | VaR | CVaR (Expected Shortfall) |\n"
    md += "|--------|-----|---------------------------|\n"

    pvar = data["parametric_var"]
    md += f"| Parametric (Normal) | {pvar['var_pct']:.2f}% | - |\n"

    hvar = data["historical_var"]
    md += f"| Historical Simulation | {hvar['var_pct']:.2f}% | {hvar['cvar_pct']:.2f}% |\n"

    mcvar = data["monte_carlo_var"]
    md += f"| Monte Carlo | {mcvar['var_pct']:.2f}% | {mcvar['cvar_pct']:.2f}% |\n"
    md += "\n"

    md += (
        f"> **Interpretation:** There is a {conf:.0%} probability that portfolio losses "
        f"will not exceed ~{mcvar['var_pct']:.1f}% over the next {horizon_label} period. "
        f"In the worst {(1-conf)*100:.0f}% of scenarios, average losses are ~{mcvar['cvar_pct']:.1f}%.\n\n"
    )

    # Stress tests
    if "stress_tests" in data:
        md += "## Stress Test Scenarios\n\n"
        md += "| Scenario | Portfolio Loss |\n"
        md += "|----------|----------------|\n"
        for s in data["stress_tests"]:
            md += f"| {s['name']} | {s['portfolio_loss_pct']:.1f}% |\n"
        md += "\n"

    # Risk ratios
    if "risk_ratios" in data:
        r = data["risk_ratios"]
        md += "## Risk-Adjusted Return Ratios\n\n"
        md += "| Metric | Value |\n|--------|-------|\n"
        md += f"| Sharpe Ratio | {r['sharpe_ratio']:.3f} |\n"
        md += f"| Sortino Ratio | {r['sortino_ratio']:.3f} |\n"
        md += f"| Calmar Ratio | {r['calmar_ratio']:.3f} |\n"
        md += f"| Annual Return | {r['annual_return_pct']:.1f}% |\n"
        md += f"| Annual Volatility | {r['annual_volatility_pct']:.1f}% |\n"
        md += "\n"

        # Interpret Sharpe
        if r["sharpe_ratio"] >= 1.0:
            interpretation = "Good risk-adjusted returns"
        elif r["sharpe_ratio"] >= 0.5:
            interpretation = "Acceptable risk-adjusted returns"
        elif r["sharpe_ratio"] >= 0:
            interpretation = "Returns may not adequately compensate for risk"
        else:
            interpretation = "Risk-free rate exceeds expected returns"
        md += f"> **Sharpe interpretation:** {interpretation}\n"

    return md


# =============================================================================
# MCP TOOL REGISTRATION
# =============================================================================


def register_risk_analytics_tools(mcp: FastMCP):
    """Register risk analytics tools with the MCP server."""

    @mcp.tool(
        name="crypto_risk_analysis",
        annotations={
            "title": "Portfolio Risk Analysis",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def crypto_risk_analysis(params: RiskAnalysisInput) -> str:
        """Analyze portfolio risk using VaR, CVaR, stress tests, and risk ratios.

        Provides:
        - **Value at Risk (VaR)** via three methods: Parametric, Historical, Monte Carlo
        - **Conditional VaR (CVaR)** / Expected Shortfall for tail risk
        - **Stress testing** against 5 historical/hypothetical scenarios
        - **Risk ratios**: Sharpe, Sortino, Calmar

        Examples:
        - Analyze current portfolio: no portfolio param needed
        - Custom portfolio: {"BTC": 0.6, "ETH": 0.3, "SOL": 0.1}
        - Higher confidence: confidence_level=0.99
        - Weekly horizon: time_horizon_days=7

        Args:
            params: Risk analysis parameters

        Returns:
            Risk analysis results in markdown or JSON format
        """
        try:
            result = run_risk_analysis(params)

            if params.response_format == "json":
                return json.dumps(result, indent=2)

            return format_risk_markdown(result)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
