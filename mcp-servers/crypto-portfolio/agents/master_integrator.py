"""
Master Signal Integrator - 225+ Market Indicators

Combines all signal modules into one comprehensive analysis:

EXTENDED SIGNALS (1-60):
- Technical Indicators (1-8)
- Sentiment Indicators (9-16)
- On-Chain Metrics (17-28)
- Derivatives Data (29-36)
- Macro & Cross-Market (37-44)
- Network & Mining (45-50)
- Institutional (51-55)
- Additional Signals (56-60)

ADVANCED ON-CHAIN (61-135):
- Cycle Indicators (61-70)
- Advanced On-Chain (71-85)
- Exchange & Flow Metrics (86-95)
- Network Metrics (96-105)
- Market Structure (106-115)
- Macro Liquidity (116-125)
- Derivatives Advanced (126-135)

ULTRA SIGNALS (136-225):
- Behavioral Economics (136-145)
- Advanced Technical (146-160)
- Cross-Asset & Correlation (161-175)
- Regime Detection (176-185)
- Blockchain Specific (186-195)
- Extreme Indicators (196-205)
- Timing & Seasonality (206-215)
- ML-Derived Signals (216-225)

This provides the most comprehensive cryptocurrency market analysis available.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import logging

# Import all analyzers
try:
    from .extended_signals import ExtendedSignalsAnalyzer, ComprehensiveSignalAnalysis
except ImportError:
    ExtendedSignalsAnalyzer = None
    ComprehensiveSignalAnalysis = None

try:
    from .advanced_onchain import AdvancedOnChainAnalyzer
except ImportError:
    AdvancedOnChainAnalyzer = None

from .ultra_signals import (
    UltraSignalsAnalyzer,
    UltraAnalysis,
    RegimeState
)

logger = logging.getLogger(__name__)


@dataclass
class MasterSignalSummary:
    """Summary for a category across all modules."""
    name: str
    total_signals: int
    available_signals: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    weighted_score: float
    top_signals: List[Tuple[str, int, str]]  # (name, score, description)


@dataclass
class MasterAnalysis:
    """Complete 225+ signal analysis."""
    timestamp: datetime
    asset: str

    # Module results
    extended_analysis: Optional[Any]  # ComprehensiveSignalAnalysis
    onchain_analysis: Optional[Any]   # AdvancedOnChainAnalysis
    ultra_analysis: Optional[UltraAnalysis]

    # Aggregated metrics
    total_signals: int
    available_signals: int
    data_coverage: float

    # Category summaries (merged across modules)
    category_summaries: Dict[str, MasterSignalSummary]

    # Master scores
    master_composite_score: float  # -100 to +100
    confidence: float  # 0-1

    # Final recommendations
    recommended_dca_multiplier: float
    recommended_buffer_deployment: float
    risk_level: str  # "very_low", "low", "moderate", "high", "extreme"
    opportunity_level: str  # "exceptional", "strong", "moderate", "low", "none"

    # Action plan
    primary_action: str
    secondary_actions: List[str]
    risk_warnings: List[str]

    # Regime context
    current_regime: RegimeState
    regime_recommendation: str


class MasterSignalIntegrator:
    """
    Integrates all 225+ signals from three modules into unified analysis.
    """

    # Category mappings across modules
    CATEGORY_MAPPINGS = {
        "technical": ["technical", "advanced_technical"],
        "sentiment": ["sentiment", "behavioral"],
        "onchain": ["onchain", "advanced_onchain", "blockchain"],
        "derivatives": ["derivatives", "derivatives_advanced"],
        "macro": ["macro", "cross_asset", "macro_liquidity"],
        "mining": ["mining", "network"],
        "institutional": ["institutional"],
        "timing": ["timing", "cycle"],
        "regime": ["regime", "market_structure"],
        "extreme": ["extreme", "additional"],
    }

    # Category weights for final score
    CATEGORY_WEIGHTS = {
        "technical": 1.0,
        "sentiment": 0.8,
        "onchain": 1.3,  # On-chain is most reliable
        "derivatives": 1.1,
        "macro": 0.7,
        "mining": 0.8,
        "institutional": 1.2,
        "timing": 0.4,
        "regime": 1.4,  # Regime is critical context
        "extreme": 1.5,  # Extreme events matter most
    }

    def __init__(self):
        self._extended_analyzer = ExtendedSignalsAnalyzer() if ExtendedSignalsAnalyzer else None
        self._onchain_analyzer = AdvancedOnChainAnalyzer() if AdvancedOnChainAnalyzer else None
        self._ultra_analyzer = UltraSignalsAnalyzer()

    async def close(self):
        """Close all analyzers."""
        if self._extended_analyzer:
            await self._extended_analyzer.close()
        if self._onchain_analyzer:
            await self._onchain_analyzer.close()
        await self._ultra_analyzer.close()

    async def analyze(self, asset: str = "BTC",
                      include_extended: bool = True,
                      include_onchain: bool = True,
                      include_ultra: bool = True) -> MasterAnalysis:
        """
        Run comprehensive 225+ signal analysis.

        Args:
            asset: Asset to analyze (BTC, ETH, SOL, etc.)
            include_extended: Include signals 1-60
            include_onchain: Include signals 61-135
            include_ultra: Include signals 136-225

        Returns:
            MasterAnalysis with all results
        """
        tasks = []

        # Extended signals (1-60)
        if include_extended and self._extended_analyzer:
            tasks.append(("extended", self._extended_analyzer.analyze(asset)))
        else:
            tasks.append(("extended", asyncio.coroutine(lambda: None)()))

        # Advanced on-chain (61-135)
        if include_onchain and self._onchain_analyzer:
            tasks.append(("onchain", self._onchain_analyzer.analyze(asset)))
        else:
            tasks.append(("onchain", asyncio.coroutine(lambda: None)()))

        # Ultra signals (136-225)
        if include_ultra:
            tasks.append(("ultra", self._ultra_analyzer.analyze(asset)))
        else:
            tasks.append(("ultra", asyncio.coroutine(lambda: None)()))

        # Run all analyses in parallel
        results = {}
        for name, task in tasks:
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"Error in {name} analysis: {e}")
                results[name] = None

        extended_analysis = results.get("extended")
        onchain_analysis = results.get("onchain")
        ultra_analysis = results.get("ultra")

        # Aggregate all signals
        all_signals = self._collect_all_signals(
            extended_analysis, onchain_analysis, ultra_analysis
        )

        # Calculate totals
        total_signals = len(all_signals)
        available_signals = len([s for s in all_signals
                                if s.get("signal") != "unavailable"])
        data_coverage = available_signals / total_signals if total_signals > 0 else 0

        # Build category summaries
        category_summaries = self._build_category_summaries(all_signals)

        # Calculate master composite score
        master_score = self._calculate_master_score(all_signals, category_summaries)

        # Determine confidence
        confidence = self._calculate_confidence(all_signals, data_coverage)

        # Get regime from ultra analysis
        current_regime = ultra_analysis.current_regime if ultra_analysis else RegimeState(
            volatility_regime="unknown",
            trend_regime="unknown",
            liquidity_regime="unknown",
            correlation_regime="unknown",
            sentiment_regime="unknown",
            phase="unknown",
            confidence=0
        )

        # Generate final recommendations
        (dca_mult, buffer_deploy, risk_level, opportunity_level,
         primary_action, secondary_actions, risk_warnings, regime_rec) = \
            self._generate_recommendations(master_score, confidence, current_regime)

        return MasterAnalysis(
            timestamp=datetime.utcnow(),
            asset=asset,
            extended_analysis=extended_analysis,
            onchain_analysis=onchain_analysis,
            ultra_analysis=ultra_analysis,
            total_signals=total_signals,
            available_signals=available_signals,
            data_coverage=data_coverage,
            category_summaries=category_summaries,
            master_composite_score=master_score,
            confidence=confidence,
            recommended_dca_multiplier=dca_mult,
            recommended_buffer_deployment=buffer_deploy,
            risk_level=risk_level,
            opportunity_level=opportunity_level,
            primary_action=primary_action,
            secondary_actions=secondary_actions,
            risk_warnings=risk_warnings,
            current_regime=current_regime,
            regime_recommendation=regime_rec
        )

    def _collect_all_signals(self, extended, onchain, ultra) -> List[Dict]:
        """Collect all signals from all modules into unified format."""
        all_signals = []

        # From extended analysis (1-60)
        if extended and hasattr(extended, 'all_signals'):
            for sig in extended.all_signals:
                all_signals.append({
                    "id": getattr(sig, 'id', 0),
                    "name": sig.name,
                    "category": sig.category,
                    "score": sig.score,
                    "weight": sig.weight,
                    "signal": sig.signal.value if hasattr(sig.signal, 'value') else str(sig.signal),
                    "description": sig.description,
                    "confidence": getattr(sig, 'confidence', 0.7),
                    "module": "extended"
                })

        # From on-chain analysis (61-135)
        if onchain and hasattr(onchain, 'all_signals'):
            for sig in onchain.all_signals:
                all_signals.append({
                    "id": getattr(sig, 'id', 0),
                    "name": sig.name,
                    "category": sig.category,
                    "score": sig.score,
                    "weight": sig.weight,
                    "signal": sig.signal.value if hasattr(sig.signal, 'value') else str(sig.signal),
                    "description": sig.description,
                    "confidence": getattr(sig, 'confidence', 0.7),
                    "module": "onchain"
                })

        # From ultra analysis (136-225)
        if ultra:
            ultra_signals = (
                ultra.behavioral_signals +
                ultra.advanced_technical +
                ultra.cross_asset +
                ultra.regime_signals +
                ultra.blockchain_specific +
                ultra.extreme_indicators +
                ultra.timing_signals +
                ultra.ml_derived
            )
            for sig in ultra_signals:
                all_signals.append({
                    "id": sig.id,
                    "name": sig.name,
                    "category": sig.category,
                    "score": sig.score,
                    "weight": sig.weight,
                    "signal": sig.signal.value,
                    "description": sig.description,
                    "confidence": sig.confidence,
                    "module": "ultra"
                })

        return all_signals

    def _build_category_summaries(self, signals: List[Dict]) -> Dict[str, MasterSignalSummary]:
        """Build summary for each master category."""
        summaries = {}

        for master_cat, sub_cats in self.CATEGORY_MAPPINGS.items():
            cat_signals = [s for s in signals if s["category"] in sub_cats]
            available = [s for s in cat_signals if s["signal"] != "unavailable"]

            bullish = len([s for s in available if s["score"] > 0])
            bearish = len([s for s in available if s["score"] < 0])
            neutral = len([s for s in available if s["score"] == 0])

            # Calculate weighted score
            total_weight = sum(s["weight"] * s.get("confidence", 0.7) for s in available)
            weighted_score = sum(
                s["score"] * s["weight"] * s.get("confidence", 0.7)
                for s in available
            ) / total_weight if total_weight > 0 else 0

            # Top signals (sorted by absolute score * weight)
            sorted_signals = sorted(
                available,
                key=lambda x: abs(x["score"]) * x["weight"],
                reverse=True
            )[:5]
            top_signals = [(s["name"], s["score"], s["description"]) for s in sorted_signals]

            summaries[master_cat] = MasterSignalSummary(
                name=master_cat,
                total_signals=len(cat_signals),
                available_signals=len(available),
                bullish_count=bullish,
                bearish_count=bearish,
                neutral_count=neutral,
                weighted_score=weighted_score,
                top_signals=top_signals
            )

        return summaries

    def _calculate_master_score(self, signals: List[Dict],
                                summaries: Dict[str, MasterSignalSummary]) -> float:
        """Calculate the master composite score from all signals."""
        total_weighted_score = 0
        total_weight = 0

        for master_cat, summary in summaries.items():
            if summary.available_signals > 0:
                cat_weight = self.CATEGORY_WEIGHTS.get(master_cat, 1.0)
                # Weight by both category importance and data availability
                availability_factor = summary.available_signals / max(summary.total_signals, 1)
                combined_weight = cat_weight * availability_factor * summary.available_signals

                total_weighted_score += summary.weighted_score * combined_weight
                total_weight += combined_weight

        if total_weight == 0:
            return 0

        # Normalize to -100 to +100
        return (total_weighted_score / total_weight) * 50

    def _calculate_confidence(self, signals: List[Dict],
                              data_coverage: float) -> float:
        """Calculate overall confidence in the analysis."""
        if not signals:
            return 0

        # Factor 1: Data coverage
        coverage_factor = data_coverage

        # Factor 2: Signal agreement (how much do signals agree?)
        available = [s for s in signals if s["signal"] != "unavailable"]
        if available:
            avg_score = sum(s["score"] for s in available) / len(available)
            score_variance = sum((s["score"] - avg_score) ** 2 for s in available) / len(available)
            # High variance = less confidence
            agreement_factor = 1 / (1 + score_variance * 0.25)
        else:
            agreement_factor = 0

        # Factor 3: Individual signal confidence
        avg_confidence = sum(s.get("confidence", 0.7) for s in available) / len(available) if available else 0

        # Combine factors
        confidence = (coverage_factor * 0.4 + agreement_factor * 0.3 + avg_confidence * 0.3)

        return min(max(confidence, 0), 1)

    def _generate_recommendations(self, score: float, confidence: float,
                                  regime: RegimeState) -> Tuple:
        """Generate comprehensive recommendations."""

        # Base recommendations from score
        if score <= -60:
            dca_mult = 3.0
            buffer = 0.85
            risk_level = "very_low"
            opportunity = "exceptional"
            primary = "🚨 MAXIMUM ACCUMULATION: Deploy 3x DCA + 85% of cash buffer"
        elif score <= -40:
            dca_mult = 2.5
            buffer = 0.65
            risk_level = "low"
            opportunity = "strong"
            primary = "💎 STRONG BUY: 2.5x DCA + 65% buffer deployment"
        elif score <= -20:
            dca_mult = 2.0
            buffer = 0.45
            risk_level = "low"
            opportunity = "moderate"
            primary = "🟢 BUY: Double DCA + 45% buffer deployment"
        elif score <= 0:
            dca_mult = 1.5
            buffer = 0.25
            risk_level = "moderate"
            opportunity = "moderate"
            primary = "📈 OPPORTUNITY: 1.5x DCA + 25% buffer"
        elif score <= 20:
            dca_mult = 1.0
            buffer = 0.0
            risk_level = "moderate"
            opportunity = "low"
            primary = "⚖️ NEUTRAL: Continue standard DCA"
        elif score <= 40:
            dca_mult = 0.75
            buffer = 0.0
            risk_level = "high"
            opportunity = "none"
            primary = "⚠️ CAUTION: Reduce DCA by 25%"
        elif score <= 60:
            dca_mult = 0.5
            buffer = 0.0
            risk_level = "high"
            opportunity = "none"
            primary = "🔴 GREED DETECTED: Reduce DCA by 50%"
        else:
            dca_mult = 0.25
            buffer = 0.0
            risk_level = "extreme"
            opportunity = "none"
            primary = "🚨 EXTREME GREED: Minimize buying, consider taking profits"

        # Secondary actions based on regime
        secondary = []
        risk_warnings = []

        if regime.volatility_regime == "extreme":
            secondary.append("💥 Extreme volatility - consider smaller, more frequent buys")
            dca_mult *= 1.1  # Slightly increase for volatility opportunity

        if regime.phase == "accumulation":
            secondary.append("🏗️ Accumulation phase - smart money entering")
            dca_mult *= 1.1
        elif regime.phase == "distribution":
            secondary.append("📤 Distribution phase - smart money exiting")
            risk_warnings.append("Distribution phase often precedes significant declines")
            dca_mult *= 0.9

        if regime.trend_regime in ["strong_bear", "bear"]:
            secondary.append("📉 Bear market - excellent for long-term DCA")
        elif regime.trend_regime in ["strong_bull"]:
            secondary.append("📈 Strong bull - momentum favor but watch for exhaustion")
            risk_warnings.append("Extended bull runs increase correction risk")

        # Confidence adjustment
        if confidence < 0.5:
            risk_warnings.append(f"Low data confidence ({confidence:.0%}) - use smaller position sizes")
            dca_mult *= 0.8

        # Regime recommendation
        regime_rec = self._get_regime_recommendation(regime)

        return (dca_mult, buffer, risk_level, opportunity,
                primary, secondary, risk_warnings, regime_rec)

    def _get_regime_recommendation(self, regime: RegimeState) -> str:
        """Generate regime-specific recommendation."""
        recs = []

        if regime.volatility_regime in ["high", "extreme"]:
            recs.append("High volatility favors DCA over lump sum")

        if regime.phase == "accumulation":
            recs.append("Accumulation detected - ideal for aggressive buying")
        elif regime.phase == "markup":
            recs.append("Markup phase - trend following works well")
        elif regime.phase == "distribution":
            recs.append("Distribution - reduce exposure gradually")
        elif regime.phase == "markdown":
            recs.append("Markdown - wait for capitulation signs before heavy buying")

        if regime.trend_regime == "range":
            recs.append("Range-bound market - buy support, reduce at resistance")

        return " | ".join(recs) if recs else "No specific regime recommendation"


def format_master_analysis(analysis: MasterAnalysis) -> str:
    """Format master analysis for CLI output."""
    lines = [
        "",
        "═" * 90,
        f"  🎯 MASTER SIGNAL ANALYSIS - {analysis.asset}",
        f"  {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "═" * 90,
        "",
        "  ╔══════════════════════════════════════════════════════════════════════════════════╗",
        f"  ║  MASTER COMPOSITE SCORE: {analysis.master_composite_score:+6.1f} / 100                                  ║",
        f"  ║  Data Coverage: {analysis.available_signals:3d}/{analysis.total_signals:3d} signals ({analysis.data_coverage:.0%})                                   ║",
        f"  ║  Confidence: {analysis.confidence:.0%}                                                              ║",
        "  ╚══════════════════════════════════════════════════════════════════════════════════╝",
        "",
    ]

    # Opportunity and risk levels
    opp_emoji = {"exceptional": "💎", "strong": "🟢", "moderate": "📈", "low": "⚪", "none": "🔴"}
    risk_emoji = {"very_low": "🟢", "low": "🟡", "moderate": "🟠", "high": "🔴", "extreme": "🚨"}

    lines.extend([
        f"  Opportunity Level: {opp_emoji.get(analysis.opportunity_level, '⚪')} {analysis.opportunity_level.upper()}",
        f"  Risk Level:        {risk_emoji.get(analysis.risk_level, '⚪')} {analysis.risk_level.upper()}",
        "",
        "─" * 90,
        "  📋 PRIMARY ACTION:",
        f"     {analysis.primary_action}",
        "",
        "  💰 RECOMMENDED SETTINGS:",
        f"     DCA Multiplier:     {analysis.recommended_dca_multiplier:.2f}x",
        f"     Buffer Deployment:  {analysis.recommended_buffer_deployment:.0%}",
        "",
    ])

    # Secondary actions
    if analysis.secondary_actions:
        lines.append("  📝 SECONDARY ACTIONS:")
        for action in analysis.secondary_actions:
            lines.append(f"     • {action}")
        lines.append("")

    # Risk warnings
    if analysis.risk_warnings:
        lines.append("  ⚠️  RISK WARNINGS:")
        for warning in analysis.risk_warnings:
            lines.append(f"     • {warning}")
        lines.append("")

    # Current regime
    lines.extend([
        "─" * 90,
        "  📊 CURRENT MARKET REGIME:",
        f"     Volatility:   {analysis.current_regime.volatility_regime}",
        f"     Trend:        {analysis.current_regime.trend_regime}",
        f"     Phase:        {analysis.current_regime.phase}",
        f"     Liquidity:    {analysis.current_regime.liquidity_regime}",
        "",
        f"  💡 REGIME INSIGHT: {analysis.regime_recommendation}",
        "",
    ])

    # Category summaries
    lines.extend([
        "─" * 90,
        "  📈 CATEGORY BREAKDOWN:",
        ""
    ])

    for cat_name, summary in analysis.category_summaries.items():
        if summary.available_signals > 0:
            indicator = "🟢" if summary.weighted_score > 0.5 else "🔴" if summary.weighted_score < -0.5 else "⚪"
            lines.append(
                f"     {indicator} {cat_name.upper():15} Score: {summary.weighted_score:+5.2f}  "
                f"({summary.bullish_count}🟢 {summary.bearish_count}🔴 {summary.neutral_count}⚪)"
            )

            # Top signals in category
            for name, score, desc in summary.top_signals[:2]:
                sig_ind = "🟢" if score > 0 else "🔴" if score < 0 else "⚪"
                lines.append(f"        {sig_ind} {name}: {desc[:50]}...")
            lines.append("")

    lines.extend([
        "═" * 90,
        "  225+ SIGNAL ANALYSIS COMPLETE",
        "═" * 90,
        ""
    ])

    return "\n".join(lines)


async def run_master_analysis(asset: str = "BTC") -> MasterAnalysis:
    """Convenience function to run master analysis."""
    integrator = MasterSignalIntegrator()
    try:
        return await integrator.analyze(asset)
    finally:
        await integrator.close()
