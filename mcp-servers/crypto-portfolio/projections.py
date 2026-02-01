"""
Portfolio Growth Projection Model

Aggressive Income Strategy - 4 Year Horizon
Initial: Variable | DCA: $40/day ($14,600/year) | Yield: 7.2% blended
"""

from dataclasses import dataclass
from typing import Dict, List


# =============================================================================
# ASSUMPTIONS
# =============================================================================

ALLOCATION = {
    "ETH": 0.18,
    "BTC": 0.12,
    "ATOM": 0.12,
    "DOT": 0.10,
    "TIA": 0.08,
    "INJ": 0.05,
    "SOL": 0.12,
    "AVAX": 0.06,
    "NEAR": 0.05,
    "SUI": 0.04,
    "CASH": 0.08,
}

# Net staking yields (after platform commission)
STAKING_YIELDS = {
    "ETH": 0.026,
    "BTC": 0.0,
    "ATOM": 0.14,
    "DOT": 0.10,
    "TIA": 0.11,
    "INJ": 0.13,
    "SOL": 0.055,
    "AVAX": 0.065,
    "NEAR": 0.075,
    "SUI": 0.03,
    "CASH": 0.0,
}

# Current approximate prices (Jan 2026)
CURRENT_PRICES = {
    "BTC": 104000,
    "ETH": 3300,
    "SOL": 260,
    "DOT": 7.50,
    "AVAX": 40,
    "ATOM": 10,
    "TIA": 5.50,
    "INJ": 25,
    "NEAR": 5.50,
    "SUI": 4.80,
}

# =============================================================================
# PRICE SCENARIOS (4-Year CAGR)
# =============================================================================

SCENARIOS = {
    "bear": {
        "name": "Bear Case",
        "description": "Extended bear market, regulatory pressure, slow adoption",
        "probability": 0.20,
        "cagr": {
            "BTC": -0.05,   # Flat to slightly down
            "ETH": -0.08,
            "SOL": -0.15,
            "DOT": -0.20,
            "AVAX": -0.18,
            "ATOM": -0.15,
            "TIA": -0.25,
            "INJ": -0.25,
            "NEAR": -0.20,
            "SUI": -0.30,
        }
    },
    "base": {
        "name": "Base Case",
        "description": "Moderate growth, continued institutional adoption, normal cycles",
        "probability": 0.50,
        "cagr": {
            "BTC": 0.20,    # ~2.1x over 4 years
            "ETH": 0.25,    # ~2.4x
            "SOL": 0.35,    # ~3.3x
            "DOT": 0.20,
            "AVAX": 0.25,
            "ATOM": 0.30,
            "TIA": 0.40,
            "INJ": 0.45,
            "NEAR": 0.35,
            "SUI": 0.50,
        }
    },
    "bull": {
        "name": "Bull Case",
        "description": "Mass adoption, ETF inflows, favorable regulation, AI/crypto convergence",
        "probability": 0.30,
        "cagr": {
            "BTC": 0.40,    # ~3.8x over 4 years
            "ETH": 0.50,    # ~5x
            "SOL": 0.60,    # ~6.5x
            "DOT": 0.45,
            "AVAX": 0.50,
            "ATOM": 0.55,
            "TIA": 0.70,
            "INJ": 0.75,
            "NEAR": 0.60,
            "SUI": 0.80,
        }
    }
}


@dataclass
class YearlySnapshot:
    year: int
    starting_value: float
    dca_contributions: float
    staking_income: float
    price_appreciation: float
    ending_value: float
    cumulative_invested: float
    total_return_pct: float


@dataclass
class ProjectionResult:
    scenario_name: str
    initial_investment: float
    final_value: float
    total_invested: float
    total_staking_income: float
    total_return: float
    total_return_pct: float
    annualized_return: float
    yearly_snapshots: List[YearlySnapshot]
    final_prices: Dict[str, float]
    final_holdings: Dict[str, float]


def project_growth(
    initial_investment: float,
    years: int,
    scenario_key: str,
    annual_dca: float = 14600,  # $40/day
    reinvest_staking: bool = True,
) -> ProjectionResult:
    """
    Project portfolio growth over time.

    Args:
        initial_investment: Starting portfolio value in USD
        years: Number of years to project
        scenario_key: "bear", "base", or "bull"
        annual_dca: Annual DCA contribution
        reinvest_staking: Whether to reinvest staking rewards
    """
    scenario = SCENARIOS[scenario_key]

    # Initialize holdings based on allocation
    holdings = {}  # asset -> quantity
    for asset, alloc in ALLOCATION.items():
        if asset == "CASH":
            holdings[asset] = initial_investment * alloc
        else:
            usd_value = initial_investment * alloc
            price = CURRENT_PRICES.get(asset, 1)
            holdings[asset] = usd_value / price

    yearly_snapshots = []
    total_staking_income = 0
    cumulative_invested = initial_investment

    for year in range(1, years + 1):
        # Starting value for the year
        starting_value = sum(
            holdings[asset] * CURRENT_PRICES.get(asset, 1) * ((1 + scenario["cagr"].get(asset, 0)) ** (year - 1))
            if asset != "CASH" else holdings[asset]
            for asset in holdings
        )

        # DCA contributions throughout the year
        # Spread across assets according to allocation (excluding cash)
        dca_allocation = {k: v for k, v in ALLOCATION.items() if k != "CASH"}
        total_alloc = sum(dca_allocation.values())

        for asset, alloc in dca_allocation.items():
            dca_usd = annual_dca * (alloc / total_alloc)
            # Average price during the year (midpoint assumption)
            avg_price = CURRENT_PRICES.get(asset, 1) * ((1 + scenario["cagr"].get(asset, 0)) ** (year - 0.5))
            holdings[asset] += dca_usd / avg_price

        cumulative_invested += annual_dca

        # Calculate staking income for the year
        year_staking_income = 0
        for asset, qty in holdings.items():
            if asset == "CASH":
                continue
            yield_rate = STAKING_YIELDS.get(asset, 0)
            # Price at end of year
            end_price = CURRENT_PRICES.get(asset, 1) * ((1 + scenario["cagr"].get(asset, 0)) ** year)
            staking_value = qty * end_price * yield_rate
            year_staking_income += staking_value

            if reinvest_staking:
                # Add staking rewards as new holdings
                staking_qty = (qty * yield_rate)
                holdings[asset] += staking_qty

        total_staking_income += year_staking_income

        # Ending value
        ending_value = sum(
            holdings[asset] * CURRENT_PRICES.get(asset, 1) * ((1 + scenario["cagr"].get(asset, 0)) ** year)
            if asset != "CASH" else holdings[asset]
            for asset in holdings
        )

        # Price appreciation (excluding DCA and staking)
        price_appreciation = ending_value - starting_value - annual_dca - (year_staking_income if reinvest_staking else 0)

        total_return_pct = ((ending_value - cumulative_invested) / cumulative_invested) * 100

        yearly_snapshots.append(YearlySnapshot(
            year=year,
            starting_value=starting_value,
            dca_contributions=annual_dca,
            staking_income=year_staking_income,
            price_appreciation=price_appreciation,
            ending_value=ending_value,
            cumulative_invested=cumulative_invested,
            total_return_pct=total_return_pct,
        ))

    # Final calculations
    final_value = yearly_snapshots[-1].ending_value
    total_return = final_value - cumulative_invested
    total_return_pct = (total_return / cumulative_invested) * 100
    annualized_return = ((final_value / initial_investment) ** (1 / years) - 1) * 100

    # Final prices and holdings
    final_prices = {
        asset: CURRENT_PRICES.get(asset, 1) * ((1 + scenario["cagr"].get(asset, 0)) ** years)
        for asset in CURRENT_PRICES
    }

    final_holdings = {
        asset: {
            "quantity": holdings[asset],
            "value": holdings[asset] * final_prices.get(asset, 1) if asset != "CASH" else holdings[asset],
        }
        for asset in holdings
    }

    return ProjectionResult(
        scenario_name=scenario["name"],
        initial_investment=initial_investment,
        final_value=final_value,
        total_invested=cumulative_invested,
        total_staking_income=total_staking_income,
        total_return=total_return,
        total_return_pct=total_return_pct,
        annualized_return=annualized_return,
        yearly_snapshots=yearly_snapshots,
        final_prices=final_prices,
        final_holdings=final_holdings,
    )


def format_projection(result: ProjectionResult) -> str:
    """Format projection results for display."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"  {result.scenario_name.upper()} SCENARIO")
    lines.append("=" * 70)
    lines.append("")

    lines.append(f"  Initial Investment:     ${result.initial_investment:>15,.0f}")
    lines.append(f"  Total DCA Contributions:${result.total_invested - result.initial_investment:>15,.0f}")
    lines.append(f"  Total Invested:         ${result.total_invested:>15,.0f}")
    lines.append("")
    lines.append(f"  Total Staking Income:   ${result.total_staking_income:>15,.0f}")
    lines.append(f"  Final Portfolio Value:  ${result.final_value:>15,.0f}")
    lines.append("")
    lines.append(f"  Total Return:           ${result.total_return:>+15,.0f}")
    lines.append(f"  Total Return %:         {result.total_return_pct:>+15.1f}%")
    lines.append(f"  Annualized Return:      {result.annualized_return:>+15.1f}%")
    lines.append("")

    lines.append("  Year-by-Year Breakdown:")
    lines.append("  " + "-" * 66)
    lines.append(f"  {'Year':<6} {'Start':>12} {'DCA':>10} {'Staking':>10} {'End':>14} {'Return':>10}")
    lines.append("  " + "-" * 66)

    for snap in result.yearly_snapshots:
        lines.append(
            f"  {snap.year:<6} ${snap.starting_value:>11,.0f} ${snap.dca_contributions:>9,.0f} "
            f"${snap.staking_income:>9,.0f} ${snap.ending_value:>13,.0f} {snap.total_return_pct:>+9.1f}%"
        )

    lines.append("")
    return "\n".join(lines)


def run_all_projections(initial_investment: float, years: int = 4) -> str:
    """Run projections for all scenarios."""
    output = []
    output.append("")
    output.append("╔" + "═" * 70 + "╗")
    output.append("║" + "  PORTFOLIO GROWTH PROJECTIONS".center(70) + "║")
    output.append("║" + f"  {years}-Year Horizon | Aggressive Income Strategy".center(70) + "║")
    output.append("╚" + "═" * 70 + "╝")
    output.append("")
    output.append(f"  Starting Investment: ${initial_investment:,.0f}")
    output.append("  Annual DCA: $14,600 ($40/day)")
    output.append("  Blended Staking Yield: ~7.2%")
    output.append("  Staking Rewards: Reinvested")
    output.append("")

    results = {}
    for scenario_key in ["bear", "base", "bull"]:
        result = project_growth(initial_investment, years, scenario_key)
        results[scenario_key] = result
        output.append(format_projection(result))

    # Summary comparison
    output.append("=" * 70)
    output.append("  SCENARIO COMPARISON SUMMARY")
    output.append("=" * 70)
    output.append("")
    output.append(f"  {'Scenario':<15} {'Final Value':>15} {'Total Return':>15} {'Probability':>12}")
    output.append("  " + "-" * 60)

    expected_value = 0
    for key, result in results.items():
        prob = SCENARIOS[key]["probability"]
        expected_value += result.final_value * prob
        output.append(
            f"  {result.scenario_name:<15} ${result.final_value:>14,.0f} "
            f"{result.total_return_pct:>+14.1f}% {prob*100:>11.0f}%"
        )

    output.append("  " + "-" * 60)
    output.append(f"  {'Expected Value':<15} ${expected_value:>14,.0f}")
    output.append("")

    # What the numbers mean
    output.append("=" * 70)
    output.append("  INTERPRETATION")
    output.append("=" * 70)
    output.append("")

    bear = results["bear"]
    base = results["base"]
    bull = results["bull"]

    output.append(f"  • WORST CASE (Bear): Your ${initial_investment:,.0f} + ${initial_investment + 14600*years - initial_investment:,.0f} DCA")
    output.append(f"    becomes ${bear.final_value:,.0f} ({bear.total_return_pct:+.0f}%)")
    output.append(f"    → You still earned ${bear.total_staking_income:,.0f} in staking income")
    output.append("")
    output.append(f"  • BASE CASE: Portfolio grows to ${base.final_value:,.0f} ({base.total_return_pct:+.0f}%)")
    output.append(f"    → {base.final_value/base.total_invested:.1f}x your total investment")
    output.append(f"    → ${base.total_staking_income:,.0f} from staking alone")
    output.append("")
    output.append(f"  • BEST CASE (Bull): Portfolio reaches ${bull.final_value:,.0f} ({bull.total_return_pct:+.0f}%)")
    output.append(f"    → {bull.final_value/bull.total_invested:.1f}x your total investment")
    output.append(f"    → ${bull.total_staking_income:,.0f} in staking income")
    output.append("")
    output.append(f"  • PROBABILITY-WEIGHTED: ${expected_value:,.0f} expected value")
    output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    # Run projections for different starting amounts
    for initial in [10000, 25000, 50000, 100000]:
        print(run_all_projections(initial, years=4))
        print("\n" + "=" * 70 + "\n")
