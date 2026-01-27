"""
Comprehensive Portfolio Projection Analysis

Variables:
- Starting amounts: $10k, $25k, $50k, $100k
- DCA amounts: $20/day, $40/day, $60/day, $100/day
- Time horizons: 2, 4, 6, 8 years
- Allocation strategies: Conservative, Balanced, Aggressive
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import math


# =============================================================================
# ALLOCATION STRATEGIES
# =============================================================================

STRATEGIES = {
    "conservative": {
        "name": "Conservative",
        "description": "BTC/ETH heavy, lower volatility",
        "allocation": {
            "BTC": 0.35, "ETH": 0.30, "SOL": 0.10, "DOT": 0.05,
            "AVAX": 0.05, "ATOM": 0.05, "CASH": 0.10,
        },
        "blended_yield": 0.032,  # 3.2%
        "volatility_factor": 0.7,  # Lower swings
    },
    "balanced": {
        "name": "Balanced",
        "description": "Mix of core and growth",
        "allocation": {
            "BTC": 0.25, "ETH": 0.25, "SOL": 0.12, "DOT": 0.08,
            "AVAX": 0.07, "ATOM": 0.08, "TIA": 0.05, "NEAR": 0.05, "CASH": 0.05,
        },
        "blended_yield": 0.052,  # 5.2%
        "volatility_factor": 1.0,
    },
    "aggressive": {
        "name": "Aggressive Income",
        "description": "High yield focus, more alts",
        "allocation": {
            "ETH": 0.18, "BTC": 0.12, "ATOM": 0.12, "DOT": 0.10,
            "TIA": 0.08, "INJ": 0.05, "SOL": 0.12, "AVAX": 0.06,
            "NEAR": 0.05, "SUI": 0.04, "CASH": 0.08,
        },
        "blended_yield": 0.072,  # 7.2%
        "volatility_factor": 1.4,  # Higher swings
    },
}

# Scenario CAGRs (base rates, adjusted by volatility factor)
BASE_SCENARIOS = {
    "bear": {"prob": 0.20, "cagr": -0.12},
    "base": {"prob": 0.50, "cagr": 0.28},
    "bull": {"prob": 0.30, "cagr": 0.52},
}


def project(
    initial: float,
    daily_dca: float,
    years: int,
    strategy: str,
    scenario: str,
) -> Dict:
    """Project portfolio growth."""
    strat = STRATEGIES[strategy]
    scen = BASE_SCENARIOS[scenario]
    
    # Adjust CAGR by volatility factor
    vol_factor = strat["volatility_factor"]
    if scen["cagr"] > 0:
        cagr = scen["cagr"] * vol_factor
    else:
        cagr = scen["cagr"] * vol_factor
    
    annual_dca = daily_dca * 365
    staking_yield = strat["blended_yield"]
    
    portfolio = initial
    total_staking = 0
    total_invested = initial
    
    for year in range(years):
        # Price appreciation
        portfolio *= (1 + cagr)
        
        # DCA (assume average price through year)
        dca_value = annual_dca * (1 + cagr * 0.5)  # Midpoint adjustment
        portfolio += dca_value
        total_invested += annual_dca
        
        # Staking rewards (reinvested)
        staking = portfolio * staking_yield
        portfolio += staking
        total_staking += staking
    
    return {
        "final_value": portfolio,
        "total_invested": total_invested,
        "total_staking": total_staking,
        "total_return": portfolio - total_invested,
        "return_pct": (portfolio - total_invested) / total_invested * 100,
        "multiple": portfolio / total_invested,
    }


def expected_value(initial: float, daily_dca: float, years: int, strategy: str) -> Dict:
    """Calculate probability-weighted expected outcome."""
    ev = 0
    results = {}
    
    for scenario, params in BASE_SCENARIOS.items():
        result = project(initial, daily_dca, years, strategy, scenario)
        results[scenario] = result
        ev += result["final_value"] * params["prob"]
    
    total_invested = initial + (daily_dca * 365 * years)
    
    return {
        "expected_value": ev,
        "total_invested": total_invested,
        "expected_return_pct": (ev - total_invested) / total_invested * 100,
        "expected_multiple": ev / total_invested,
        "scenarios": results,
    }


def analyze_dca_amounts():
    """Analyze different DCA amounts."""
    print("\n" + "=" * 80)
    print("  DCA AMOUNT ANALYSIS")
    print("  Finding the optimal daily investment amount")
    print("=" * 80)
    
    dca_amounts = [10, 20, 40, 60, 80, 100, 150, 200]
    initial = 25000
    years = 4
    strategy = "aggressive"
    
    print(f"\n  Assumptions: ${initial:,} initial | 4-year horizon | Aggressive strategy")
    print(f"\n  {'Daily DCA':>12} {'Monthly':>10} {'Yearly':>10} {'Total In':>12} {'Expected':>14} {'Return':>10}")
    print("  " + "-" * 72)
    
    results = []
    for daily in dca_amounts:
        monthly = daily * 30
        yearly = daily * 365
        total_in = initial + yearly * years
        ev = expected_value(initial, daily, years, strategy)
        
        results.append({
            "daily": daily,
            "monthly": monthly,
            "yearly": yearly,
            "total_invested": total_in,
            "expected_value": ev["expected_value"],
            "return_pct": ev["expected_return_pct"],
            "multiple": ev["expected_multiple"],
        })
        
        print(f"  ${daily:>10}/day ${monthly:>8}/mo ${yearly:>8}/yr ${total_in:>11,} ${ev['expected_value']:>13,.0f} {ev['expected_return_pct']:>+9.0f}%")
    
    print("\n  " + "-" * 72)
    print("  KEY INSIGHT: Higher DCA = more total invested = lower % return but higher absolute $")
    
    return results


def analyze_time_horizons():
    """Analyze different investment time horizons."""
    print("\n" + "=" * 80)
    print("  TIME HORIZON ANALYSIS")
    print("  How holding period affects outcomes")
    print("=" * 80)
    
    horizons = [1, 2, 3, 4, 5, 6, 8, 10]
    initial = 50000
    daily_dca = 40
    strategy = "aggressive"
    
    print(f"\n  Assumptions: ${initial:,} initial | $40/day DCA | Aggressive strategy")
    print(f"\n  {'Years':>8} {'Total In':>12} {'Bear':>14} {'Base':>14} {'Bull':>14} {'Expected':>14}")
    print("  " + "-" * 80)
    
    for years in horizons:
        total_in = initial + daily_dca * 365 * years
        ev = expected_value(initial, daily_dca, years, strategy)
        
        bear = ev["scenarios"]["bear"]["final_value"]
        base = ev["scenarios"]["base"]["final_value"]
        bull = ev["scenarios"]["bull"]["final_value"]
        
        print(f"  {years:>6} yr ${total_in:>11,} ${bear:>13,.0f} ${base:>13,.0f} ${bull:>13,.0f} ${ev['expected_value']:>13,.0f}")
    
    print("\n  " + "-" * 80)
    print("  KEY INSIGHT: Time in market dramatically improves outcomes due to compounding")


def analyze_strategies():
    """Compare allocation strategies."""
    print("\n" + "=" * 80)
    print("  STRATEGY COMPARISON")
    print("  Conservative vs Balanced vs Aggressive")
    print("=" * 80)
    
    initial = 50000
    daily_dca = 40
    years = 4
    
    print(f"\n  Assumptions: ${initial:,} initial | $40/day DCA | 4-year horizon")
    print(f"\n  {'Strategy':<20} {'Yield':>8} {'Bear':>14} {'Base':>14} {'Bull':>14} {'Expected':>14}")
    print("  " + "-" * 85)
    
    for strat_key, strat in STRATEGIES.items():
        ev = expected_value(initial, daily_dca, years, strat_key)
        yield_pct = strat["blended_yield"] * 100
        
        bear = ev["scenarios"]["bear"]["final_value"]
        base = ev["scenarios"]["base"]["final_value"]
        bull = ev["scenarios"]["bull"]["final_value"]
        
        print(f"  {strat['name']:<20} {yield_pct:>7.1f}% ${bear:>13,.0f} ${base:>13,.0f} ${bull:>13,.0f} ${ev['expected_value']:>13,.0f}")
    
    print("\n  " + "-" * 85)
    print("  KEY INSIGHT: Aggressive has higher expected value but wider bear/bull spread")


def analyze_starting_amounts():
    """Analyze different starting investment amounts."""
    print("\n" + "=" * 80)
    print("  STARTING AMOUNT ANALYSIS")
    print("  Impact of initial investment size")
    print("=" * 80)
    
    initials = [0, 5000, 10000, 25000, 50000, 100000, 250000]
    daily_dca = 40
    years = 4
    strategy = "aggressive"
    
    print(f"\n  Assumptions: $40/day DCA | 4-year horizon | Aggressive strategy")
    print(f"\n  {'Initial':>12} {'DCA Total':>12} {'Total In':>12} {'Expected':>14} {'Multiple':>10} {'Bear':>14}")
    print("  " + "-" * 80)
    
    dca_total = daily_dca * 365 * years
    
    for initial in initials:
        total_in = initial + dca_total
        ev = expected_value(initial, daily_dca, years, strategy)
        bear = ev["scenarios"]["bear"]["final_value"]
        
        print(f"  ${initial:>11,} ${dca_total:>11,} ${total_in:>11,} ${ev['expected_value']:>13,.0f} {ev['expected_multiple']:>9.1f}x ${bear:>13,.0f}")
    
    print("\n  " + "-" * 80)
    print("  KEY INSIGHT: Larger initial = better multiples but DCA alone still builds wealth")


def comprehensive_matrix():
    """Generate comprehensive projection matrix."""
    print("\n" + "=" * 80)
    print("  COMPREHENSIVE PROJECTION MATRIX")
    print("  Expected values across all combinations (4-year, Aggressive)")
    print("=" * 80)
    
    initials = [10000, 25000, 50000, 100000]
    dca_amounts = [20, 40, 60, 100]
    
    print(f"\n  Expected Portfolio Value (4-Year Horizon, Aggressive Strategy)")
    print(f"\n  {'Initial ↓ / DCA →':>20}", end="")
    for dca in dca_amounts:
        print(f"  ${dca}/day", end="")
    print()
    print("  " + "-" * 65)
    
    for initial in initials:
        print(f"  ${initial:>18,}", end="")
        for dca in dca_amounts:
            ev = expected_value(initial, dca, 4, "aggressive")
            print(f"  ${ev['expected_value']:>10,.0f}", end="")
        print()
    
    print("\n  Total Invested:")
    print(f"  {'':>20}", end="")
    for dca in dca_amounts:
        yearly = dca * 365
        print(f"  +${yearly*4:>7,}", end="")
    print()


def optimal_dca_recommendation():
    """Generate DCA recommendation."""
    print("\n" + "=" * 80)
    print("  DCA RECOMMENDATION ANALYSIS")
    print("=" * 80)
    
    # Analyze efficiency: return per dollar of DCA
    print("\n  Efficiency Analysis (Return per $1,000 of monthly DCA commitment)")
    print(f"\n  {'Monthly DCA':>12} {'4-Yr Invest':>12} {'Expected':>14} {'Gain':>14} {'Gain/$1k':>12}")
    print("  " + "-" * 68)
    
    initial = 25000
    base_ev = expected_value(initial, 0, 4, "aggressive")["expected_value"]
    
    monthly_amounts = [300, 600, 900, 1200, 1800, 2400, 3000, 4500, 6000]
    
    best_efficiency = 0
    best_amount = 0
    
    for monthly in monthly_amounts:
        daily = monthly / 30
        yearly = daily * 365
        total_dca = yearly * 4
        
        ev = expected_value(initial, daily, 4, "aggressive")
        gain_from_dca = ev["expected_value"] - base_ev
        efficiency = gain_from_dca / (monthly / 1000) if monthly > 0 else 0
        
        if efficiency > best_efficiency:
            best_efficiency = efficiency
            best_amount = monthly
        
        print(f"  ${monthly:>10,}/mo ${total_dca:>11,} ${ev['expected_value']:>13,.0f} ${gain_from_dca:>13,.0f} ${efficiency:>11,.0f}")
    
    print("\n  " + "-" * 68)
    print(f"  Most efficient: ~${best_amount:,}/month (${best_amount/30:.0f}/day)")
    
    # Affordability analysis
    print("\n\n  AFFORDABILITY GUIDELINES")
    print("  " + "-" * 50)
    print("  Rule of thumb: DCA should be 10-20% of disposable income")
    print("  (After taxes, rent/mortgage, necessities)")
    print()
    print(f"  {'Monthly Income':>16} {'10% DCA':>12} {'15% DCA':>12} {'20% DCA':>12}")
    print("  " + "-" * 55)
    
    incomes = [4000, 6000, 8000, 10000, 15000, 20000]
    for income in incomes:
        print(f"  ${income:>14,}/mo ${income*0.10:>11,.0f} ${income*0.15:>11,.0f} ${income*0.20:>11,.0f}")


def scenario_deep_dive():
    """Deep dive into specific scenarios."""
    print("\n" + "=" * 80)
    print("  SCENARIO DEEP DIVE: $40/day DCA ACROSS TIME HORIZONS")
    print("=" * 80)
    
    initial = 25000
    daily_dca = 40
    strategy = "aggressive"
    
    for years in [2, 4, 6, 8]:
        print(f"\n  ┌{'─' * 68}┐")
        print(f"  │  {years}-YEAR PROJECTION{' ' * (52 - len(str(years)))}│")
        print(f"  ├{'─' * 68}┤")
        
        total_invested = initial + daily_dca * 365 * years
        ev_data = expected_value(initial, daily_dca, years, strategy)
        
        print(f"  │  Initial Investment:      ${initial:>12,}{' ' * 26}│")
        print(f"  │  DCA Contributions:       ${daily_dca * 365 * years:>12,}{' ' * 26}│")
        print(f"  │  Total Invested:          ${total_invested:>12,}{' ' * 26}│")
        print(f"  ├{'─' * 68}┤")
        
        for scenario in ["bear", "base", "bull"]:
            result = ev_data["scenarios"][scenario]
            emoji = "🐻" if scenario == "bear" else "📊" if scenario == "base" else "🚀"
            prob = BASE_SCENARIOS[scenario]["prob"] * 100
            
            print(f"  │  {emoji} {scenario.upper():8} ({prob:.0f}%): ${result['final_value']:>12,.0f} ({result['return_pct']:>+7.1f}%) {result['multiple']:.1f}x{' ' * 8}│")
        
        print(f"  ├{'─' * 68}┤")
        print(f"  │  📈 EXPECTED VALUE:        ${ev_data['expected_value']:>12,.0f} ({ev_data['expected_return_pct']:>+7.1f}%){' ' * 11}│")
        print(f"  │  💰 Total Staking Income:  ${ev_data['scenarios']['base']['total_staking']:>12,.0f}{' ' * 26}│")
        print(f"  └{'─' * 68}┘")


def final_recommendation():
    """Print final DCA recommendation."""
    print("\n" + "=" * 80)
    print("  FINAL RECOMMENDATION")
    print("=" * 80)
    
    print("""
  Based on the analysis:

  ┌────────────────────────────────────────────────────────────────────────┐
  │                                                                        │
  │   RECOMMENDED DCA: $40-60/day ($1,200-1,800/month)                    │
  │                                                                        │
  │   Why this range:                                                      │
  │   • $40/day = $14,600/year - solid wealth building                    │
  │   • $60/day = $21,900/year - accelerated accumulation                 │
  │   • Sweet spot for return efficiency                                   │
  │   • Sustainable for most investors without lifestyle sacrifice        │
  │                                                                        │
  ├────────────────────────────────────────────────────────────────────────┤
  │                                                                        │
  │   TIERED RECOMMENDATION BY FINANCIAL SITUATION:                       │
  │                                                                        │
  │   💡 Just starting out / tight budget:     $20/day ($600/mo)          │
  │   📊 Comfortable / building wealth:        $40/day ($1,200/mo)        │
  │   🚀 Aggressive growth / high income:      $60-100/day ($1,800-3k/mo) │
  │   🏦 Maxing out / excess capital:          $100+/day ($3,000+/mo)     │
  │                                                                        │
  ├────────────────────────────────────────────────────────────────────────┤
  │                                                                        │
  │   TIMING CONSIDERATIONS:                                               │
  │                                                                        │
  │   • Weekly DCA (vs daily) reduces fees with minimal impact            │
  │   • Increase DCA during major corrections (>30% drawdown)             │
  │   • Consider lump sum for windfalls (bonus, tax refund)               │
  │   • Review and adjust annually based on income changes                │
  │                                                                        │
  └────────────────────────────────────────────────────────────────────────┘
""")


def main():
    """Run all analyses."""
    print("\n" * 2)
    print("╔" + "═" * 78 + "╗")
    print("║" + "  COMPREHENSIVE CRYPTO PORTFOLIO PROJECTION ANALYSIS".center(78) + "║")
    print("║" + "  All Variables • All Scenarios • All Time Horizons".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    
    analyze_dca_amounts()
    analyze_time_horizons()
    analyze_strategies()
    analyze_starting_amounts()
    comprehensive_matrix()
    scenario_deep_dive()
    optimal_dca_recommendation()
    final_recommendation()


if __name__ == "__main__":
    main()
