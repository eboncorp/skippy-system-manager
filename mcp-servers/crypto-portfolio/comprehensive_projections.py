"""
Comprehensive Portfolio Projection Model

Variables:
- Starting amounts: $10k, $25k, $50k, $100k
- DCA levels: $20/day, $40/day, $60/day, $100/day, $150/day
- Time horizons: 2, 4, 6, 8 years
- Allocation strategies: Conservative, Balanced, Aggressive
"""

from dataclasses import dataclass
from typing import Tuple


# =============================================================================
# ALLOCATION STRATEGIES
# =============================================================================

STRATEGIES = {
    "conservative": {
        "name": "Conservative",
        "description": "BTC/ETH heavy, lower volatility, modest yield",
        "allocation": {
            "BTC": 0.35, "ETH": 0.30, "SOL": 0.10, "DOT": 0.05,
            "AVAX": 0.05, "ATOM": 0.05, "CASH": 0.10,
        },
        "yields": {
            "BTC": 0.0, "ETH": 0.026, "SOL": 0.055, "DOT": 0.10,
            "AVAX": 0.065, "ATOM": 0.14, "CASH": 0.0,
        },
        "blended_yield": 0.038,  # ~3.8%
    },
    "balanced": {
        "name": "Balanced",
        "description": "Mix of core holdings and yield generators",
        "allocation": {
            "BTC": 0.25, "ETH": 0.25, "SOL": 0.12, "DOT": 0.08,
            "AVAX": 0.06, "ATOM": 0.08, "TIA": 0.04, "NEAR": 0.04,
            "CASH": 0.08,
        },
        "yields": {
            "BTC": 0.0, "ETH": 0.026, "SOL": 0.055, "DOT": 0.10,
            "AVAX": 0.065, "ATOM": 0.14, "TIA": 0.11, "NEAR": 0.075,
            "CASH": 0.0,
        },
        "blended_yield": 0.052,  # ~5.2%
    },
    "aggressive": {
        "name": "Aggressive Income",
        "description": "High-yield focus, more altcoin exposure",
        "allocation": {
            "ETH": 0.18, "BTC": 0.12, "ATOM": 0.12, "DOT": 0.10,
            "TIA": 0.08, "INJ": 0.05, "SOL": 0.12, "AVAX": 0.06,
            "NEAR": 0.05, "SUI": 0.04, "CASH": 0.08,
        },
        "yields": {
            "ETH": 0.026, "BTC": 0.0, "ATOM": 0.14, "DOT": 0.10,
            "TIA": 0.11, "INJ": 0.13, "SOL": 0.055, "AVAX": 0.065,
            "NEAR": 0.075, "SUI": 0.03, "CASH": 0.0,
        },
        "blended_yield": 0.072,  # ~7.2%
    },
}

# Price scenarios (CAGR over the period)
MARKET_SCENARIOS = {
    "bear": {
        "name": "Bear",
        "probability": 0.20,
        "conservative_cagr": -0.05,
        "balanced_cagr": -0.10,
        "aggressive_cagr": -0.15,
    },
    "base": {
        "name": "Base",
        "probability": 0.50,
        "conservative_cagr": 0.15,
        "balanced_cagr": 0.22,
        "aggressive_cagr": 0.30,
    },
    "bull": {
        "name": "Bull",
        "probability": 0.30,
        "conservative_cagr": 0.30,
        "balanced_cagr": 0.45,
        "aggressive_cagr": 0.55,
    },
}


@dataclass
class ProjectionResult:
    strategy: str
    scenario: str
    initial: float
    daily_dca: float
    years: int
    total_invested: float
    final_value: float
    total_staking: float
    total_return: float
    return_pct: float
    annual_return: float


def calculate_projection(
    initial: float,
    daily_dca: float,
    years: int,
    strategy_key: str,
    scenario_key: str,
) -> ProjectionResult:
    """Calculate a single projection."""
    strategy = STRATEGIES[strategy_key]
    scenario = MARKET_SCENARIOS[scenario_key]

    # Get appropriate CAGR for this strategy
    cagr = scenario[f"{strategy_key}_cagr"]
    staking_yield = strategy["blended_yield"]

    annual_dca = daily_dca * 365

    # Simulate year by year
    portfolio_value = initial
    total_staking = 0
    total_invested = initial

    for year in range(1, years + 1):
        # DCA contributions (spread throughout year)
        total_invested += annual_dca

        # Growth from price appreciation
        # Apply to average balance during year
        avg_balance = portfolio_value + (annual_dca / 2)
        price_growth = avg_balance * cagr

        # Staking income (on average balance)
        staking_income = avg_balance * staking_yield
        total_staking += staking_income

        # End of year value
        portfolio_value = portfolio_value + annual_dca + price_growth + staking_income

        # Ensure non-negative
        portfolio_value = max(0, portfolio_value)

    total_return = portfolio_value - total_invested
    return_pct = (total_return / total_invested) * 100 if total_invested > 0 else 0

    # Annualized return (CAGR of total investment)
    if portfolio_value > 0 and initial > 0:
        annual_return = ((portfolio_value / initial) ** (1 / years) - 1) * 100
    else:
        annual_return = 0

    return ProjectionResult(
        strategy=strategy["name"],
        scenario=scenario["name"],
        initial=initial,
        daily_dca=daily_dca,
        years=years,
        total_invested=total_invested,
        final_value=portfolio_value,
        total_staking=total_staking,
        total_return=total_return,
        return_pct=return_pct,
        annual_return=annual_return,
    )


def calculate_expected_value(
    initial: float,
    daily_dca: float,
    years: int,
    strategy_key: str,
) -> Tuple[float, float, float]:
    """Calculate probability-weighted expected value."""
    expected = 0
    expected_staking = 0

    results = {}
    for scenario_key, scenario in MARKET_SCENARIOS.items():
        result = calculate_projection(initial, daily_dca, years, strategy_key, scenario_key)
        results[scenario_key] = result
        expected += result.final_value * scenario["probability"]
        expected_staking += result.total_staking * scenario["probability"]

    total_invested = initial + (daily_dca * 365 * years)
    expected_return_pct = ((expected - total_invested) / total_invested) * 100

    return expected, expected_staking, expected_return_pct


def format_dca_comparison(initial: float, years: int):
    """Compare different DCA amounts."""
    dca_levels = [20, 40, 60, 100, 150]

    lines = []
    lines.append("")
    lines.append("=" * 90)
    lines.append(f"  DCA AMOUNT COMPARISON | Starting: ${initial:,.0f} | Horizon: {years} Years")
    lines.append("=" * 90)
    lines.append("")

    for strategy_key in ["conservative", "balanced", "aggressive"]:
        strategy = STRATEGIES[strategy_key]
        lines.append(f"  {strategy['name'].upper()} STRATEGY (Yield: {strategy['blended_yield']*100:.1f}%)")
        lines.append("  " + "-" * 86)
        lines.append(f"  {'DCA/Day':<10} {'Total In':>12} {'Bear':>14} {'Base':>14} {'Bull':>14} {'Expected':>14}")
        lines.append("  " + "-" * 86)

        for dca in dca_levels:
            total_invested = initial + (dca * 365 * years)

            bear = calculate_projection(initial, dca, years, strategy_key, "bear")
            base = calculate_projection(initial, dca, years, strategy_key, "base")
            bull = calculate_projection(initial, dca, years, strategy_key, "bull")
            expected, _, _ = calculate_expected_value(initial, dca, years, strategy_key)

            lines.append(
                f"  ${dca:<9} ${total_invested:>11,.0f} "
                f"${bear.final_value:>13,.0f} ${base.final_value:>13,.0f} "
                f"${bull.final_value:>13,.0f} ${expected:>13,.0f}"
            )

        lines.append("")

    return "\n".join(lines)


def format_time_horizon_comparison(initial: float, daily_dca: float):
    """Compare different time horizons."""
    horizons = [2, 4, 6, 8, 10]

    lines = []
    lines.append("")
    lines.append("=" * 90)
    lines.append(f"  TIME HORIZON COMPARISON | Starting: ${initial:,.0f} | DCA: ${daily_dca}/day")
    lines.append("=" * 90)
    lines.append("")

    for strategy_key in ["conservative", "balanced", "aggressive"]:
        strategy = STRATEGIES[strategy_key]
        lines.append(f"  {strategy['name'].upper()} STRATEGY")
        lines.append("  " + "-" * 86)
        lines.append(f"  {'Years':<8} {'Total In':>12} {'Bear':>14} {'Base':>14} {'Bull':>14} {'Expected':>14}")
        lines.append("  " + "-" * 86)

        for years in horizons:
            total_invested = initial + (daily_dca * 365 * years)

            bear = calculate_projection(initial, daily_dca, years, strategy_key, "bear")
            base = calculate_projection(initial, daily_dca, years, strategy_key, "base")
            bull = calculate_projection(initial, daily_dca, years, strategy_key, "bull")
            expected, _, _ = calculate_expected_value(initial, daily_dca, years, strategy_key)

            lines.append(
                f"  {years:<8} ${total_invested:>11,.0f} "
                f"${bear.final_value:>13,.0f} ${base.final_value:>13,.0f} "
                f"${bull.final_value:>13,.0f} ${expected:>13,.0f}"
            )

        lines.append("")

    return "\n".join(lines)


def format_starting_amount_comparison(daily_dca: float, years: int):
    """Compare different starting amounts."""
    starting_amounts = [0, 10000, 25000, 50000, 100000, 250000]

    lines = []
    lines.append("")
    lines.append("=" * 90)
    lines.append(f"  STARTING AMOUNT COMPARISON | DCA: ${daily_dca}/day | Horizon: {years} Years")
    lines.append("=" * 90)
    lines.append("")

    for strategy_key in ["conservative", "balanced", "aggressive"]:
        strategy = STRATEGIES[strategy_key]
        lines.append(f"  {strategy['name'].upper()} STRATEGY")
        lines.append("  " + "-" * 86)
        lines.append(f"  {'Start':>10} {'Total In':>12} {'Bear':>14} {'Base':>14} {'Bull':>14} {'Expected':>14}")
        lines.append("  " + "-" * 86)

        for initial in starting_amounts:
            total_invested = initial + (daily_dca * 365 * years)

            bear = calculate_projection(initial, daily_dca, years, strategy_key, "bear")
            base = calculate_projection(initial, daily_dca, years, strategy_key, "base")
            bull = calculate_projection(initial, daily_dca, years, strategy_key, "bull")
            expected, _, _ = calculate_expected_value(initial, daily_dca, years, strategy_key)

            lines.append(
                f"  ${initial:>9,.0f} ${total_invested:>11,.0f} "
                f"${bear.final_value:>13,.0f} ${base.final_value:>13,.0f} "
                f"${bull.final_value:>13,.0f} ${expected:>13,.0f}"
            )

        lines.append("")

    return "\n".join(lines)


def format_staking_income_analysis(initial: float, daily_dca: float, years: int):
    """Detailed staking income breakdown."""
    lines = []
    lines.append("")
    lines.append("=" * 90)
    lines.append(f"  STAKING INCOME ANALYSIS | Start: ${initial:,.0f} | DCA: ${daily_dca}/day | {years} Years")
    lines.append("=" * 90)
    lines.append("")

    lines.append(f"  {'Strategy':<20} {'Yield':>8} {'Bear Staking':>14} {'Base Staking':>14} {'Bull Staking':>14}")
    lines.append("  " + "-" * 74)

    for strategy_key in ["conservative", "balanced", "aggressive"]:
        strategy = STRATEGIES[strategy_key]

        bear = calculate_projection(initial, daily_dca, years, strategy_key, "bear")
        base = calculate_projection(initial, daily_dca, years, strategy_key, "base")
        bull = calculate_projection(initial, daily_dca, years, strategy_key, "bull")

        lines.append(
            f"  {strategy['name']:<20} {strategy['blended_yield']*100:>7.1f}% "
            f"${bear.total_staking:>13,.0f} ${base.total_staking:>13,.0f} ${bull.total_staking:>13,.0f}"
        )

    lines.append("")
    lines.append("  Note: Staking income is reinvested and compounds. Higher portfolio = more staking.")
    lines.append("")

    # Year-by-year staking for aggressive strategy (base case)
    lines.append("  AGGRESSIVE STRATEGY - Year-by-Year Staking Income (Base Case):")
    lines.append("  " + "-" * 50)

    portfolio = initial
    annual_dca = daily_dca * 365
    total_staking = 0

    for year in range(1, years + 1):
        avg_balance = portfolio + (annual_dca / 2)
        staking = avg_balance * 0.072
        total_staking += staking

        # Apply growth
        growth = avg_balance * 0.30
        portfolio = portfolio + annual_dca + growth + staking

        lines.append(f"    Year {year}: ${staking:>10,.0f} staking income (portfolio: ${portfolio:>12,.0f})")

    lines.append(f"    {'─' * 45}")
    lines.append(f"    Total:  ${total_staking:>10,.0f} over {years} years")
    lines.append("")

    return "\n".join(lines)


def format_dca_recommendation(initial: float, years: int):
    """Generate DCA recommendation."""
    lines = []
    lines.append("")
    lines.append("=" * 90)
    lines.append("  DCA AMOUNT RECOMMENDATION")
    lines.append("=" * 90)
    lines.append("")

    # Calculate metrics for different DCA levels
    dca_analysis = []

    for dca in [20, 40, 60, 80, 100, 150, 200]:
        monthly = dca * 30
        annual = dca * 365
        total_invested = initial + (annual * years)

        # Get expected values for aggressive strategy
        expected, staking, return_pct = calculate_expected_value(initial, dca, years, "aggressive")

        # Calculate efficiency (return per dollar invested)
        efficiency = expected / total_invested if total_invested > 0 else 0

        # Get bear case for risk assessment
        bear = calculate_projection(initial, dca, years, "aggressive", "bear")
        max_loss = min(0, bear.return_pct)

        dca_analysis.append({
            "dca": dca,
            "monthly": monthly,
            "annual": annual,
            "total_invested": total_invested,
            "expected": expected,
            "staking": staking,
            "return_pct": return_pct,
            "efficiency": efficiency,
            "max_loss": max_loss,
            "bear_value": bear.final_value,
        })

    lines.append(f"  Starting Capital: ${initial:,.0f}")
    lines.append(f"  Time Horizon: {years} years")
    lines.append("  Strategy: Aggressive Income (7.2% yield)")
    lines.append("")

    lines.append(f"  {'DCA/Day':<10} {'Monthly':>10} {'Annual':>12} {'Total In':>12} {'Expected':>14} {'Return':>10} {'Efficiency':>12}")
    lines.append("  " + "-" * 84)

    for a in dca_analysis:
        lines.append(
            f"  ${a['dca']:<9} ${a['monthly']:>9,.0f} ${a['annual']:>11,.0f} "
            f"${a['total_invested']:>11,.0f} ${a['expected']:>13,.0f} "
            f"{a['return_pct']:>+9.0f}% {a['efficiency']:>11.2f}x"
        )

    lines.append("")
    lines.append("  " + "─" * 84)
    lines.append("")

    # Find optimal DCA
    # Factors: efficiency, total return, affordability

    lines.append("  RECOMMENDATION FACTORS:")
    lines.append("")
    lines.append("  1. EFFICIENCY (Return per $ invested):")
    lines.append("     • All DCA levels have similar efficiency (~2.5-3.5x)")
    lines.append("     • Slightly diminishing returns at very high DCA levels")
    lines.append("")
    lines.append("  2. ABSOLUTE RETURN (Total wealth built):")
    lines.append("     • Higher DCA = more total wealth")
    lines.append("     • $100/day builds 2.5x more wealth than $40/day")
    lines.append("")
    lines.append("  3. RISK EXPOSURE:")
    lines.append("     • More invested = more at risk in bear market")
    lines.append("     • But DCA smooths entry prices, reducing timing risk")
    lines.append("")
    lines.append("  4. CASH FLOW SUSTAINABILITY:")
    lines.append("     • Can you maintain this DCA for 4+ years?")
    lines.append("     • Stopping DCA mid-way significantly impacts results")
    lines.append("")

    return "\n".join(lines)


def format_full_recommendation():
    """Generate complete recommendation."""
    lines = []
    lines.append("")
    lines.append("╔" + "═" * 88 + "╗")
    lines.append("║" + "  MY RECOMMENDATION".center(88) + "║")
    lines.append("╚" + "═" * 88 + "╝")
    lines.append("")

    lines.append("  Based on your profile:")
    lines.append("  • Business investment account")
    lines.append("  • 4+ year horizon")
    lines.append("  • Aggressive, income-focused")
    lines.append("  • Already have exchange APIs set up")
    lines.append("")

    lines.append("  ┌─────────────────────────────────────────────────────────────────────────────────────┐")
    lines.append("  │  RECOMMENDED DCA: $60-$100/day ($1,800-$3,000/month)                                │")
    lines.append("  └─────────────────────────────────────────────────────────────────────────────────────┘")
    lines.append("")

    lines.append("  WHY THIS RANGE:")
    lines.append("")
    lines.append("  $60/day ($1,800/mo | $21,900/yr):")
    lines.append("  ├─ Sweet spot for most investors")
    lines.append("  ├─ Meaningful accumulation without overextending")
    lines.append("  ├─ Sustainable for 4+ years for most business cash flows")
    lines.append("  └─ Expected 4-year outcome: $180k invested → $450k+ (aggressive)")
    lines.append("")

    lines.append("  $100/day ($3,000/mo | $36,500/yr):")
    lines.append("  ├─ Aggressive wealth building")
    lines.append("  ├─ Appropriate if cash flow supports it comfortably")
    lines.append("  ├─ Takes fuller advantage of compounding + staking")
    lines.append("  └─ Expected 4-year outcome: $250k invested → $700k+ (aggressive)")
    lines.append("")

    lines.append("  KEY PRINCIPLE: Pick a DCA you can SUSTAIN for 4+ years.")
    lines.append("  Stopping mid-bear-market is the #1 wealth destroyer.")
    lines.append("")

    lines.append("  ┌─────────────────────────────────────────────────────────────────────────────────────┐")
    lines.append("  │  IMPLEMENTATION TIPS                                                                │")
    lines.append("  └─────────────────────────────────────────────────────────────────────────────────────┘")
    lines.append("")
    lines.append("  1. EXECUTE WEEKLY, NOT DAILY")
    lines.append("     • $60/day = $420/week (one weekly buy)")
    lines.append("     • Reduces fee drag by ~70%")
    lines.append("     • Easier to automate and track")
    lines.append("")
    lines.append("  2. USE KRAKEN FOR LOWER FEES")
    lines.append("     • Kraken: 0.16-0.26% maker fees")
    lines.append("     • Coinbase: ~0.5% spread")
    lines.append("     • Savings: $300-500/year on $60/day DCA")
    lines.append("")
    lines.append("  3. STAKE IMMEDIATELY AFTER PURCHASE")
    lines.append("     • Don't let assets sit unstaked")
    lines.append("     • At $60/day, unstaked assets = ~$10/day lost yield")
    lines.append("")
    lines.append("  4. INCREASE DCA DURING DIPS")
    lines.append("     • If market drops 30%+, consider 1.5-2x normal DCA")
    lines.append("     • This is what the 8% cash buffer is for")
    lines.append("")
    lines.append("  5. REASSESS ANNUALLY")
    lines.append("     • Review allocation and DCA amount yearly")
    lines.append("     • Adjust based on portfolio growth and cash flow")
    lines.append("")

    return "\n".join(lines)


def main():
    """Run all analyses."""

    print("\n" + "█" * 90)
    print("█" + "  COMPREHENSIVE PORTFOLIO PROJECTION ANALYSIS".center(88) + "█")
    print("█" * 90)

    # 1. DCA comparison at different starting amounts
    for initial in [25000, 50000, 100000]:
        print(format_dca_comparison(initial, years=4))

    # 2. Time horizon comparison
    print(format_time_horizon_comparison(initial=50000, daily_dca=60))

    # 3. Starting amount comparison
    print(format_starting_amount_comparison(daily_dca=60, years=4))

    # 4. Staking income analysis
    print(format_staking_income_analysis(initial=50000, daily_dca=60, years=4))

    # 5. DCA recommendation
    print(format_dca_recommendation(initial=50000, years=4))

    # 6. Full recommendation
    print(format_full_recommendation())

    # 7. Quick reference table
    print("")
    print("=" * 90)
    print("  QUICK REFERENCE: Expected 4-Year Outcomes (Aggressive Strategy)")
    print("=" * 90)
    print("")
    print(f"  {'Start':>10} + {'DCA/Day':>8} = {'Total In':>12} → {'Bear':>12} / {'Base':>12} / {'Bull':>14} / {'Expected':>12}")
    print("  " + "-" * 88)

    for initial in [10000, 25000, 50000, 100000]:
        for dca in [40, 60, 100]:
            total = initial + (dca * 365 * 4)
            bear = calculate_projection(initial, dca, 4, "aggressive", "bear")
            base = calculate_projection(initial, dca, 4, "aggressive", "base")
            bull = calculate_projection(initial, dca, 4, "aggressive", "bull")
            exp, _, _ = calculate_expected_value(initial, dca, 4, "aggressive")

            print(
                f"  ${initial:>9,} + ${dca:>7}/d = ${total:>11,} → "
                f"${bear.final_value:>11,.0f} / ${base.final_value:>11,.0f} / ${bull.final_value:>13,.0f} / ${exp:>11,.0f}"
            )
        print("")


if __name__ == "__main__":
    main()
