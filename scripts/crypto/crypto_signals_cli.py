#!/usr/bin/env python3
"""
Crypto Portfolio Manager - Command Line Interface

Comprehensive CLI for 130+ market signal analysis.

Usage:
    python cli.py unified [ASSET]         # Full 130+ signal analysis (default)
    python cli.py base [ASSET]            # Base 60 signal analysis  
    python cli.py expanded [ASSET]        # Expanded 70 signal analysis
    python cli.py quick [ASSET]           # Quick summary only
    python cli.py recommendation [ASSET]  # DCA recommendation only
    python cli.py category [CAT] [ASSET]  # Single category analysis

Examples:
    python cli.py unified BTC
    python cli.py recommendation ETH
    python cli.py category smart_money BTC
"""

import asyncio
import argparse
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '/home/dave/skippy/lib/python/crypto_trading')

from agents import (
    # Unified (130+)
    UnifiedSignalAnalyzer,
    format_unified_analysis,
    quick_unified_analysis,
    MarketCondition,
    CyclePhase,
    
    # Base (60)
    ExtendedSignalsAnalyzer,
    format_extended_signals,
    
    # Expanded (70)
    ExpandedSignalsAnalyzer,
    format_expanded_signals,
)


async def run_unified_analysis(asset: str, verbose: bool = False):
    """Run full 130+ signal analysis."""
    print(f"\n⏳ Running unified analysis for {asset}...")
    print("   Gathering 130+ market signals...\n")
    
    analyzer = UnifiedSignalAnalyzer()
    try:
        analysis = await analyzer.analyze(asset)
        print(format_unified_analysis(analysis))
        
        if verbose:
            print("\n📊 DETAILED SIGNAL BREAKDOWN:\n")
            for signal in analysis.all_signals:
                status = "🟢" if signal.score > 0 else "🔴" if signal.score < 0 else "⚪"
                if signal.signal.value == "unavailable":
                    status = "❓"
                print(f"  {status} [{signal.category}] {signal.name}: {signal.description}")
    finally:
        await analyzer.close()


async def run_base_analysis(asset: str):
    """Run base 60 signal analysis."""
    print(f"\n⏳ Running base analysis for {asset}...")
    print("   Gathering 60 market signals...\n")
    
    analyzer = ExtendedSignalsAnalyzer()
    try:
        analysis = await analyzer.analyze(asset)
        print(format_extended_signals(analysis))
    finally:
        await analyzer.close()


async def run_expanded_analysis(asset: str):
    """Run expanded 70 signal analysis."""
    print(f"\n⏳ Running expanded analysis for {asset}...")
    print("   Gathering 70 additional signals...\n")
    
    analyzer = ExpandedSignalsAnalyzer()
    try:
        analysis = await analyzer.analyze(asset)
        print(format_expanded_signals(analysis))
    finally:
        await analyzer.close()


async def run_quick_analysis(asset: str):
    """Run quick summary analysis."""
    print(f"\n⏳ Quick analysis for {asset}...\n")
    
    analyzer = UnifiedSignalAnalyzer()
    try:
        analysis = await analyzer.analyze(asset)
        
        # Compact output
        rec = analysis.primary_recommendation
        
        print("=" * 60)
        print(f"  {asset} QUICK ANALYSIS - {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 60)
        print(f"""
  Composite Score:   {analysis.composite_score:+.1f}
  Market Condition:  {analysis.market_condition.value.upper()}
  Cycle Phase:       {analysis.cycle_phase.value.replace('_', ' ').title()}
  Trend:             {analysis.trend_direction.upper()}
  
  ┌─────────────────────────────────────┐
  │  RECOMMENDATION: {rec.action:<18}│
  │  DCA Multiplier:  {rec.dca_multiplier:.2f}x               │
  │  Buffer Deploy:   {rec.buffer_deployment:.0%}                │
  │  Confidence:      {rec.confidence:.0%}                │
  └─────────────────────────────────────┘
  
  Data Quality: {analysis.available_signals}/{analysis.total_signals} signals ({analysis.data_quality:.0%})
""")
        print("=" * 60)
        
    finally:
        await analyzer.close()


async def run_recommendation_only(asset: str):
    """Get just the DCA recommendation."""
    print(f"\n⏳ Getting recommendation for {asset}...\n")
    
    analyzer = UnifiedSignalAnalyzer()
    try:
        analysis = await analyzer.analyze(asset)
        rec = analysis.primary_recommendation
        
        print("╔" + "═" * 58 + "╗")
        print(f"║  {asset} DCA RECOMMENDATION".ljust(59) + "║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  Action:            {rec.action:<35}║")
        print(f"║  DCA Multiplier:    {rec.dca_multiplier:.2f}x{' '*32}║")
        print(f"║  Buffer Deployment: {rec.buffer_deployment:.0%}{' '*34}║")
        print(f"║  Confidence:        {rec.confidence:.0%}{' '*34}║")
        print(f"║  Time Horizon:      {rec.time_horizon.replace('_', ' ').title():<35}║")
        print("╟" + "─" * 58 + "╢")
        print(f"║  Composite Score:   {analysis.composite_score:+.1f}{' '*32}║")
        print(f"║  Market Condition:  {analysis.market_condition.value.upper():<35}║")
        print("╚" + "═" * 58 + "╝")
        
        # Print example calculation
        base_dca = 100  # Example $100 base DCA
        adjusted_dca = base_dca * rec.dca_multiplier
        
        print(f"""
  Example (with $100 base DCA):
    Adjusted DCA:    ${adjusted_dca:.2f}
    From buffer:     ${base_dca * rec.buffer_deployment:.2f} (if available)
    Total today:     ${adjusted_dca + base_dca * rec.buffer_deployment:.2f}
""")
        
    finally:
        await analyzer.close()


async def run_category_analysis(category: str, asset: str):
    """Run analysis for a specific category."""
    valid_categories = [
        "price_technical", "sentiment", "onchain", "derivatives",
        "macro_cross", "cycle_position", "smart_money", "institutional"
    ]
    
    if category not in valid_categories:
        print(f"Invalid category: {category}")
        print(f"Valid categories: {', '.join(valid_categories)}")
        return
    
    print(f"\n⏳ Analyzing {category.replace('_', ' ').title()} for {asset}...\n")
    
    analyzer = UnifiedSignalAnalyzer()
    try:
        analysis = await analyzer.analyze(asset)
        cat_summary = getattr(analysis, category)
        
        print("=" * 60)
        print(f"  {category.replace('_', ' ').upper()} ANALYSIS - {asset}")
        print("=" * 60)
        print(f"""
  Weighted Score: {cat_summary.weighted_score:+.2f}
  Average Score:  {cat_summary.avg_score:+.2f}
  
  Signals: {cat_summary.available_signals}/{cat_summary.total_signals}
  Bullish: {cat_summary.bullish_count} 🟢
  Bearish: {cat_summary.bearish_count} 🔴  
  Neutral: {cat_summary.neutral_count} ⚪
""")
        
        if cat_summary.top_bullish_signals:
            print("  TOP BULLISH:")
            for sig in cat_summary.top_bullish_signals:
                print(f"    🟢 {sig}")
        
        if cat_summary.top_bearish_signals:
            print("\n  TOP BEARISH:")
            for sig in cat_summary.top_bearish_signals:
                print(f"    🔴 {sig}")
        
        print("\n" + "=" * 60)
        
    finally:
        await analyzer.close()


def print_help():
    """Print detailed help."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           CRYPTO PORTFOLIO MANAGER - SIGNAL ANALYSIS CLI              ║
║                        130+ Market Signals                            ║
╚══════════════════════════════════════════════════════════════════════╝

COMMANDS:

  unified [ASSET]          Full 130+ signal analysis (default)
  base [ASSET]             Base 60 signal analysis only
  expanded [ASSET]         Expanded 70 signal analysis only
  quick [ASSET]            Quick summary output
  recommendation [ASSET]   DCA recommendation only
  rec [ASSET]              Alias for recommendation
  category [CAT] [ASSET]   Single category analysis

CATEGORIES:
  price_technical   Technical indicators + order flow
  sentiment         Market sentiment signals
  onchain           On-chain metrics
  derivatives       Derivatives/leverage data
  macro_cross       Macro conditions + cross-chain
  cycle_position    Cycle timing indicators
  smart_money       Smart money behavior
  institutional     Institutional metrics

SIGNAL COVERAGE (130+ Total):

  Base Signals (60):
    • Technical (8): RSI, MA, Bollinger, MACD, Volume, ATR, Fib, Ichimoku
    • Sentiment (8): Fear/Greed, Google Trends, Social, News, Influencers
    • On-Chain (12): Exchange flows, Whales, MVRV, SOPR, NUPL, Puell, NVT
    • Derivatives (8): Funding, OI, Liquidations, Options, Basis
    • Macro (8): DXY, S&P correlation, Gold, VIX, Premiums
    • Mining (6): Hash rate, Difficulty, Miner flows, Stock-to-Flow
    • Institutional (5): ETF flows, Grayscale, CME, MSTR

  Expanded Signals (70):
    • Smart Money (12): LTH/STH SOPR, Dormancy, Accumulation, Liveliness
    • DeFi/Altcoin (12): Gas, Burn rate, Staking, L2 TVL, DEX ratio
    • Order Flow (8): Spread, Depth, CVD, Taker ratio, Slippage
    • Calendar (8): FOMC, CPI, NFP, Options expiry, Halving
    • Cross-Chain (8): Arb spreads, Bridges, WBTC, Depeg risk
    • Cycle Position (8): Pi Cycle, Rainbow, Mayer, 4-Year phase
    • Advanced On-Chain (8): HODL waves, VDD, Velocity, Revived supply
    • Advanced Sentiment (6): Dev activity, Whale alerts, Regulatory

EXAMPLES:

  python cli.py                        # Full analysis for BTC (default)
  python cli.py unified ETH            # Full analysis for ETH
  python cli.py quick BTC              # Quick summary
  python cli.py rec BTC                # Just the recommendation
  python cli.py category smart_money   # Smart money signals only
  python cli.py base SOL               # Base 60 signals for SOL

COMPOSITE SCORE INTERPRETATION:

  -100 to -60  │ EXTREME FEAR    │ 3.0x DCA + 75% buffer deploy
   -60 to -40  │ FEAR            │ 2.5x DCA + 50% buffer deploy
   -40 to -20  │ MILD FEAR       │ 2.0x DCA + 35% buffer deploy
   -20 to   0  │ SLIGHT FEAR     │ 1.5x DCA + 20% buffer deploy
     0 to  20  │ NEUTRAL         │ 1.0x DCA (normal)
    20 to  40  │ MILD GREED      │ 0.75x DCA
    40 to  60  │ GREED           │ 0.5x DCA
    60 to 100  │ EXTREME GREED   │ 0.25x DCA / consider profits

""")


def main():
    parser = argparse.ArgumentParser(
        description="Crypto Portfolio Manager - 130+ Signal Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="unified",
        help="Command to run (unified, base, expanded, quick, recommendation, category)"
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Command arguments (asset, category name, etc.)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output with all signal details"
    )
    parser.add_argument(
        "--help-full",
        action="store_true",
        help="Show detailed help"
    )
    
    args = parser.parse_args()
    
    if args.help_full:
        print_help()
        return
    
    command = args.command.lower()
    cmd_args = args.args
    
    # Default asset
    asset = "BTC"
    
    if command in ["unified", "full", "all"]:
        if cmd_args:
            asset = cmd_args[0].upper()
        asyncio.run(run_unified_analysis(asset, args.verbose))
    
    elif command in ["base", "60"]:
        if cmd_args:
            asset = cmd_args[0].upper()
        asyncio.run(run_base_analysis(asset))
    
    elif command in ["expanded", "70", "extra"]:
        if cmd_args:
            asset = cmd_args[0].upper()
        asyncio.run(run_expanded_analysis(asset))
    
    elif command in ["quick", "q", "summary"]:
        if cmd_args:
            asset = cmd_args[0].upper()
        asyncio.run(run_quick_analysis(asset))
    
    elif command in ["recommendation", "rec", "dca"]:
        if cmd_args:
            asset = cmd_args[0].upper()
        asyncio.run(run_recommendation_only(asset))
    
    elif command in ["category", "cat"]:
        if len(cmd_args) < 1:
            print("Usage: python cli.py category [CATEGORY] [ASSET]")
            print("Categories: price_technical, sentiment, onchain, derivatives,")
            print("            macro_cross, cycle_position, smart_money, institutional")
            return
        category = cmd_args[0].lower()
        if len(cmd_args) > 1:
            asset = cmd_args[1].upper()
        asyncio.run(run_category_analysis(category, asset))
    
    elif command in ["help", "-h", "--help"]:
        print_help()
    
    else:
        # Assume it's an asset symbol
        asset = command.upper()
        asyncio.run(run_unified_analysis(asset, args.verbose))


if __name__ == "__main__":
    main()
