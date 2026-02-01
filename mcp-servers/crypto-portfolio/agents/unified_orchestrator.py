"""
Unified Signal Orchestrator

Combines all 135+ signals into a single comprehensive analysis system.

SIGNAL CATEGORIES:
1. Technical Indicators (1-8)
2. Sentiment Indicators (9-16)
3. On-Chain Metrics (17-28)
4. Derivatives Data (29-36)
5. Macro & Cross-Market (37-44)
6. Network & Mining (45-50)
7. Institutional (51-55)
8. Additional Signals (56-60)
9. Cycle Indicators (61-70)
10. Advanced On-Chain (71-85)
11. Exchange & Flow Metrics (86-95)
12. Network Metrics (96-105)
13. Market Structure (106-115)
14. Macro Liquidity (116-125)
15. Derivatives Advanced (126-135)

COMPOSITE SCORING:
- Each signal produces a score from -2 (strong sell) to +2 (strong buy)
- Signals are weighted by reliability and relevance
- Category weights adjust based on market conditions
- Final composite score ranges from -100 to +100

RECOMMENDATIONS:
- Score < -60: EXTREME BUY (2.5x DCA + 75% buffer)
- Score -60 to -40: STRONG BUY (2.0x DCA + 50% buffer)
- Score -40 to -20: BUY (1.5x DCA + 25% buffer)
- Score -20 to 0: MILD BUY (1.25x DCA)
- Score 0 to 20: NEUTRAL (1.0x DCA)
- Score 20 to 40: CAUTION (0.75x DCA)
- Score 40 to 60: GREED (0.5x DCA)
- Score > 60: EXTREME GREED (0.25x DCA)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple, Any
from enum import Enum
import asyncio
import logging

from .extended_signals import ExtendedSignalsAnalyzer, SignalStrength, SignalResult
from .advanced_onchain import AdvancedOnChainAnalyzer, AdvancedSignalResult

logger = logging.getLogger(__name__)


class MarketPhase(Enum):
    """Current market cycle phase."""
    ACCUMULATION = "accumulation"
    EARLY_BULL = "early_bull"
    MID_BULL = "mid_bull"
    LATE_BULL = "late_bull"
    DISTRIBUTION = "distribution"
    EARLY_BEAR = "early_bear"
    MID_BEAR = "mid_bear"
    CAPITULATION = "capitulation"


@dataclass
class SignalCategory:
    """Category summary."""
    name: str
    signals: List[Any]
    available_count: int
    total_count: int
    avg_score: float
    weighted_score: float
    bullish_count: int
    bearish_count: int
    neutral_count: int
    confidence: float
    top_signals: List[str]


@dataclass
class UnifiedAnalysis:
    """Complete unified analysis with all signals."""
    timestamp: datetime
    asset: str

    # Category summaries
    categories: Dict[str, SignalCategory]

    # Signal counts
    total_signals: int
    available_signals: int

    # Scores
    composite_score: float  # -100 to +100
    confidence: float  # 0-1

    # Market assessment
    market_phase: MarketPhase
    phase_confidence: float

    # Recommendations
    dca_multiplier: float
    buffer_deployment: float
    recommendation: str
    action_items: List[str]

    # Risk assessment
    downside_risk: str  # low/medium/high/extreme
    upside_potential: str  # low/medium/high/extreme
    risk_reward_ratio: float

    # Key signals
    strongest_bullish: List[str]
    strongest_bearish: List[str]
    conflicting_signals: List[str]

    # Historical context
    similar_historical_periods: List[str]
    historical_outcome: str


class UnifiedSignalOrchestrator:
    """
    Master orchestrator that combines all signal sources.
    """

    # Category weights (adjust based on your preferences)
    CATEGORY_WEIGHTS = {
        "technical": 0.8,
        "sentiment": 0.7,
        "onchain": 1.2,
        "derivatives": 1.0,
        "macro": 0.6,
        "mining": 0.9,
        "institutional": 1.1,
        "additional": 0.5,
        "cycle": 1.3,  # Cycle indicators are important
        "onchain_advanced": 1.2,
        "exchange_flow": 1.0,
        "network_metrics": 0.7,
        "market_structure": 0.6,
        "macro_liquidity": 0.7,
        "derivatives_advanced": 0.8,
    }

    # Weights can be adjusted based on market phase
    PHASE_WEIGHT_ADJUSTMENTS = {
        MarketPhase.CAPITULATION: {
            "onchain": 1.5,
            "cycle": 1.5,
            "sentiment": 1.2,
        },
        MarketPhase.DISTRIBUTION: {
            "cycle": 1.4,
            "institutional": 1.3,
            "derivatives": 1.2,
        },
        MarketPhase.EARLY_BULL: {
            "onchain_advanced": 1.3,
            "institutional": 1.2,
        },
        MarketPhase.LATE_BULL: {
            "cycle": 1.5,
            "derivatives": 1.3,
            "sentiment": 1.2,
        },
    }

    def __init__(self):
        self._extended_analyzer = ExtendedSignalsAnalyzer()
        self._advanced_analyzer = AdvancedOnChainAnalyzer()

    async def close(self):
        """Close all analyzer connections."""
        await self._extended_analyzer.close()
        await self._advanced_analyzer.close()

    async def analyze(self, asset: str = "BTC") -> UnifiedAnalysis:
        """
        Run complete unified analysis with all 135+ signals.

        Args:
            asset: Asset to analyze (default: BTC)

        Returns:
            UnifiedAnalysis with all signal results and recommendations
        """
        logger.info(f"Starting unified analysis for {asset}")

        # Run both analyzers concurrently
        extended_task = self._extended_analyzer.analyze(asset)
        advanced_task = self._run_advanced_analysis(asset)

        extended_result, advanced_signals = await asyncio.gather(
            extended_task,
            advanced_task,
            return_exceptions=True
        )

        # Handle any errors
        if isinstance(extended_result, Exception):
            logger.error(f"Extended analysis error: {extended_result}")
            extended_result = None
        if isinstance(advanced_signals, Exception):
            logger.error(f"Advanced analysis error: {advanced_signals}")
            advanced_signals = []

        # Collect all signals
        all_signals = []
        categories = {}

        # Process extended signals
        if extended_result:
            for cat_name, cat_data in [
                ("technical", extended_result.technical),
                ("sentiment", extended_result.sentiment),
                ("onchain", extended_result.onchain),
                ("derivatives", extended_result.derivatives),
                ("macro", extended_result.macro),
                ("mining", extended_result.mining),
                ("institutional", extended_result.institutional),
                ("additional", extended_result.additional),
            ]:
                signals = cat_data.signals
                categories[cat_name] = self._summarize_category(cat_name, signals)
                all_signals.extend(signals)

        # Process advanced signals
        if advanced_signals:
            # Group advanced signals by category
            adv_categories: Dict[str, List[AdvancedSignalResult]] = {}
            for sig in advanced_signals:
                if sig.category not in adv_categories:
                    adv_categories[sig.category] = []
                adv_categories[sig.category].append(sig)

            for cat_name, signals in adv_categories.items():
                # Convert to standard format
                converted = [self._convert_advanced_signal(s) for s in signals]
                categories[cat_name] = self._summarize_category(cat_name, converted)
                all_signals.extend(converted)

        # Calculate totals
        total_signals = len(all_signals)
        available_signals = len([s for s in all_signals if s.signal != SignalStrength.UNAVAILABLE])
        confidence = available_signals / total_signals if total_signals > 0 else 0

        # Determine market phase
        market_phase, phase_confidence = self._determine_market_phase(categories, all_signals)

        # Adjust weights based on market phase
        adjusted_weights = self._get_adjusted_weights(market_phase)

        # Calculate composite score
        composite_score = self._calculate_composite_score(all_signals, adjusted_weights)

        # Generate recommendations
        dca_mult, buffer_deploy, recommendation = self._get_recommendations(composite_score)
        action_items = self._generate_action_items(composite_score, market_phase, categories)

        # Assess risk
        downside_risk, upside_potential, risk_reward = self._assess_risk(
            composite_score, market_phase, categories
        )

        # Find strongest signals
        strongest_bullish = self._get_top_signals(all_signals, bullish=True)
        strongest_bearish = self._get_top_signals(all_signals, bullish=False)
        conflicting = self._find_conflicting_signals(all_signals)

        # Historical context
        similar_periods, historical_outcome = self._find_historical_context(
            composite_score, market_phase
        )

        return UnifiedAnalysis(
            timestamp=datetime.utcnow(),
            asset=asset,
            categories=categories,
            total_signals=total_signals,
            available_signals=available_signals,
            composite_score=composite_score,
            confidence=confidence,
            market_phase=market_phase,
            phase_confidence=phase_confidence,
            dca_multiplier=dca_mult,
            buffer_deployment=buffer_deploy,
            recommendation=recommendation,
            action_items=action_items,
            downside_risk=downside_risk,
            upside_potential=upside_potential,
            risk_reward_ratio=risk_reward,
            strongest_bullish=strongest_bullish,
            strongest_bearish=strongest_bearish,
            conflicting_signals=conflicting,
            similar_historical_periods=similar_periods,
            historical_outcome=historical_outcome,
        )

    async def _run_advanced_analysis(self, asset: str) -> List[AdvancedSignalResult]:
        """Run all advanced signal analyses."""
        tasks = [
            # Cycle indicators
            self._advanced_analyzer.get_pi_cycle_top(asset),
            self._advanced_analyzer.get_golden_ratio_multiplier(asset),
            self._advanced_analyzer.get_2year_ma_multiplier(asset),
            self._advanced_analyzer.get_rainbow_chart(asset),
            self._advanced_analyzer.get_log_growth_curve(asset),
            self._advanced_analyzer.get_top_cap_model(asset),
            self._advanced_analyzer.get_delta_cap(asset),
            self._advanced_analyzer.get_terminal_price(asset),
            self._advanced_analyzer.get_balanced_price(asset),
            self._advanced_analyzer.get_cvdd(asset),

            # Advanced on-chain
            self._advanced_analyzer.get_rhodl_ratio(asset),
            self._advanced_analyzer.get_asopr(asset),
            self._advanced_analyzer.get_lth_sopr(asset),
            self._advanced_analyzer.get_sth_sopr(asset),
            self._advanced_analyzer.get_supply_in_profit(asset),
            self._advanced_analyzer.get_realized_losses(asset),
            self._advanced_analyzer.get_liveliness(asset),
            self._advanced_analyzer.get_dormancy_flow(asset),
            self._advanced_analyzer.get_illiquid_supply_change(asset),

            # Exchange flow
            self._advanced_analyzer.get_exchange_reserve_ratio(asset),
            self._advanced_analyzer.get_stablecoin_exchange_reserve(),
            self._advanced_analyzer.get_exchange_whale_ratio(asset),
            self._advanced_analyzer.get_fund_flow_ratio(asset),

            # Market structure
            self._advanced_analyzer.get_altcoin_season_index(),
            self._advanced_analyzer.get_btc_dominance(),
            self._advanced_analyzer.get_total_market_cap_trend(),

            # Macro liquidity
            self._advanced_analyzer.get_global_m2_change(),
            self._advanced_analyzer.get_real_interest_rate(),
            self._advanced_analyzer.get_global_liquidity_index(),

            # Derivatives advanced
            self._advanced_analyzer.get_perp_spot_volume_ratio(asset),
            self._advanced_analyzer.get_implied_vs_realized_vol(asset),
            self._advanced_analyzer.get_gamma_exposure(asset),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for r in results:
            if isinstance(r, AdvancedSignalResult):
                valid_results.append(r)
            elif isinstance(r, Exception):
                logger.error(f"Advanced signal error: {r}")

        return valid_results

    def _convert_advanced_signal(self, sig: AdvancedSignalResult) -> SignalResult:
        """Convert AdvancedSignalResult to standard SignalResult."""
        return SignalResult(
            name=sig.name,
            category=sig.category,
            value=sig.value,
            signal=sig.signal,
            score=sig.score,
            weight=sig.weight * sig.historical_accuracy,  # Weight by historical accuracy
            description=sig.description,
            details=sig.details,
        )

    def _summarize_category(self, name: str, signals: List[SignalResult]) -> SignalCategory:
        """Create category summary."""
        available = [s for s in signals if s.signal != SignalStrength.UNAVAILABLE]

        if not available:
            return SignalCategory(
                name=name,
                signals=signals,
                available_count=0,
                total_count=len(signals),
                avg_score=0,
                weighted_score=0,
                bullish_count=0,
                bearish_count=0,
                neutral_count=0,
                confidence=0,
                top_signals=[],
            )

        total_weight = sum(s.weight for s in available)
        weighted_score = sum(s.score * s.weight for s in available) / total_weight if total_weight > 0 else 0
        avg_score = sum(s.score for s in available) / len(available)

        bullish = [s for s in available if s.score > 0]
        bearish = [s for s in available if s.score < 0]
        neutral = [s for s in available if s.score == 0]

        # Top signals by weight * abs(score)
        sorted_signals = sorted(available, key=lambda s: abs(s.score) * s.weight, reverse=True)
        top_signals = [s.name for s in sorted_signals[:3]]

        return SignalCategory(
            name=name,
            signals=signals,
            available_count=len(available),
            total_count=len(signals),
            avg_score=avg_score,
            weighted_score=weighted_score,
            bullish_count=len(bullish),
            bearish_count=len(bearish),
            neutral_count=len(neutral),
            confidence=len(available) / len(signals) if signals else 0,
            top_signals=top_signals,
        )

    def _determine_market_phase(
        self, categories: Dict[str, SignalCategory], all_signals: List[SignalResult]
    ) -> Tuple[MarketPhase, float]:
        """Determine current market cycle phase."""
        # Collect relevant signals for phase detection
        cycle_cat = categories.get("cycle")
        onchain_cat = categories.get("onchain")
        sentiment_cat = categories.get("sentiment")

        scores = []

        if cycle_cat:
            scores.append(cycle_cat.weighted_score)
        if onchain_cat:
            scores.append(onchain_cat.weighted_score)
        if sentiment_cat:
            scores.append(sentiment_cat.weighted_score)

        if not scores:
            return MarketPhase.ACCUMULATION, 0.3

        avg_score = sum(scores) / len(scores)

        # Map score to phase
        if avg_score < -1.5:
            phase = MarketPhase.CAPITULATION
            confidence = min(0.9, abs(avg_score) / 2)
        elif avg_score < -0.8:
            phase = MarketPhase.MID_BEAR
            confidence = 0.7
        elif avg_score < -0.3:
            phase = MarketPhase.EARLY_BEAR
            confidence = 0.6
        elif avg_score < 0.3:
            phase = MarketPhase.ACCUMULATION
            confidence = 0.5
        elif avg_score < 0.8:
            phase = MarketPhase.EARLY_BULL
            confidence = 0.6
        elif avg_score < 1.2:
            phase = MarketPhase.MID_BULL
            confidence = 0.7
        elif avg_score < 1.5:
            phase = MarketPhase.LATE_BULL
            confidence = 0.8
        else:
            phase = MarketPhase.DISTRIBUTION
            confidence = min(0.9, avg_score / 2)

        return phase, confidence

    def _get_adjusted_weights(self, phase: MarketPhase) -> Dict[str, float]:
        """Get category weights adjusted for market phase."""
        weights = self.CATEGORY_WEIGHTS.copy()

        adjustments = self.PHASE_WEIGHT_ADJUSTMENTS.get(phase, {})
        for cat, mult in adjustments.items():
            if cat in weights:
                weights[cat] *= mult

        return weights

    def _calculate_composite_score(
        self, signals: List[SignalResult], weights: Dict[str, float]
    ) -> float:
        """Calculate composite score from all signals."""
        available = [s for s in signals if s.signal != SignalStrength.UNAVAILABLE]

        if not available:
            return 0

        total_weighted_score = 0
        total_weight = 0

        for sig in available:
            category_weight = weights.get(sig.category, 1.0)
            combined_weight = sig.weight * category_weight
            total_weighted_score += sig.score * combined_weight
            total_weight += combined_weight

        # Normalize to -100 to +100
        raw_score = total_weighted_score / total_weight if total_weight > 0 else 0
        composite = raw_score * 50  # Scale from [-2, +2] to [-100, +100]

        return max(-100, min(100, composite))

    def _get_recommendations(self, score: float) -> Tuple[float, float, str]:
        """Generate recommendations based on composite score."""
        if score <= -60:
            return 2.5, 0.75, "🟢🟢 EXTREME OPPORTUNITY: Maximum DCA + deploy 75% buffer"
        elif score <= -40:
            return 2.0, 0.50, "🟢 STRONG BUY: 2x DCA + deploy 50% buffer"
        elif score <= -20:
            return 1.5, 0.25, "🟢 BUY: 1.5x DCA + deploy 25% buffer"
        elif score <= 0:
            return 1.25, 0.10, "MILD OPPORTUNITY: Slight DCA increase"
        elif score <= 20:
            return 1.0, 0.0, "⚪ NEUTRAL: Continue normal DCA"
        elif score <= 40:
            return 0.75, 0.0, "🟡 CAUTION: Reduce DCA by 25%"
        elif score <= 60:
            return 0.5, 0.0, "🔴 GREED: Reduce DCA by 50%"
        else:
            return 0.25, 0.0, "🔴🔴 EXTREME GREED: Minimize DCA, consider profits"

    def _generate_action_items(
        self, score: float, phase: MarketPhase, categories: Dict[str, SignalCategory]
    ) -> List[str]:
        """Generate specific action items."""
        items = []

        if score < -40:
            items.append("✅ Increase DCA purchases")
            items.append("✅ Deploy cash buffer according to signal strength")
            items.append("✅ Consider adding to positions on further weakness")
        elif score < 0:
            items.append("✅ Maintain or slightly increase DCA")
            items.append("✅ Keep cash buffer ready for opportunities")
        elif score < 40:
            items.append("⚪ Continue normal DCA schedule")
            items.append("⚪ No urgent action required")
        else:
            items.append("⚠️ Consider reducing DCA amount")
            items.append("⚠️ Review portfolio for rebalancing")
            items.append("⚠️ Set stop-losses or profit targets")

        # Phase-specific items
        if phase == MarketPhase.CAPITULATION:
            items.append("🎯 Historical bottom zone - maximize accumulation")
        elif phase == MarketPhase.DISTRIBUTION:
            items.append("🎯 Late cycle - consider taking partial profits")
        elif phase == MarketPhase.LATE_BULL:
            items.append("🎯 Bull market maturing - tighten risk management")

        return items

    def _assess_risk(
        self, score: float, phase: MarketPhase, categories: Dict[str, SignalCategory]
    ) -> Tuple[str, str, float]:
        """Assess risk/reward profile."""
        # Downside risk assessment
        if score < -50:
            downside = "low"
        elif score < -20:
            downside = "medium"
        elif score < 20:
            downside = "medium"
        elif score < 50:
            downside = "high"
        else:
            downside = "extreme"

        # Upside potential
        if score < -50:
            upside = "extreme"
        elif score < -20:
            upside = "high"
        elif score < 20:
            upside = "medium"
        elif score < 50:
            upside = "low"
        else:
            upside = "low"

        # Risk/reward ratio
        upside_values = {"low": 1, "medium": 2, "high": 3, "extreme": 4}
        downside_values = {"low": 1, "medium": 2, "high": 3, "extreme": 4}

        risk_reward = upside_values[upside] / downside_values[downside]

        return downside, upside, risk_reward

    def _get_top_signals(self, signals: List[SignalResult], bullish: bool) -> List[str]:
        """Get top signals by strength."""
        available = [s for s in signals if s.signal != SignalStrength.UNAVAILABLE]

        if bullish:
            filtered = [s for s in available if s.score > 0]
        else:
            filtered = [s for s in available if s.score < 0]

        sorted_signals = sorted(filtered, key=lambda s: abs(s.score) * s.weight, reverse=True)

        return [f"{s.name}: {s.description}" for s in sorted_signals[:5]]

    def _find_conflicting_signals(self, signals: List[SignalResult]) -> List[str]:
        """Find signals that conflict with overall direction."""
        available = [s for s in signals if s.signal != SignalStrength.UNAVAILABLE]

        if not available:
            return []

        avg_score = sum(s.score for s in available) / len(available)

        conflicting = []
        for sig in available:
            # Strong signal in opposite direction
            if (avg_score > 0.5 and sig.score <= -1) or (avg_score < -0.5 and sig.score >= 1):
                conflicting.append(f"{sig.name}: {sig.description}")

        return conflicting[:5]

    def _find_historical_context(
        self, score: float, phase: MarketPhase
    ) -> Tuple[List[str], str]:
        """Find similar historical periods and their outcomes."""
        periods = []
        outcome = ""

        if score < -60 and phase in [MarketPhase.CAPITULATION, MarketPhase.MID_BEAR]:
            periods = [
                "March 2020 COVID crash",
                "December 2018 bear market bottom",
                "January 2015 capitulation",
            ]
            outcome = "Historical bottoms with 3-10x returns over following 2 years"
        elif score < -40:
            periods = [
                "May 2021 crash",
                "March 2020 recovery",
            ]
            outcome = "Strong recovery within 3-6 months historically"
        elif score > 60:
            periods = [
                "November 2021 top",
                "December 2017 top",
                "Late 2013 top",
            ]
            outcome = "Major corrections of 50-80% followed within 1-3 months"
        elif score > 40:
            periods = [
                "February 2021",
                "June 2019",
            ]
            outcome = "Volatility and potential near-term corrections"
        else:
            periods = []
            outcome = "Normal market conditions"

        return periods, outcome


def format_unified_analysis(analysis: UnifiedAnalysis) -> str:
    """Format unified analysis for CLI display."""
    lines = [
        "",
        "═" * 80,
        f"  UNIFIED MARKET ANALYSIS - {analysis.asset}",
        f"  {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "═" * 80,
        "",
        f"  📊 COMPOSITE SCORE: {analysis.composite_score:+.1f} / 100",
        f"  📈 Signals: {analysis.available_signals}/{analysis.total_signals} available ({analysis.confidence:.0%} confidence)",
        f"  🔄 Market Phase: {analysis.market_phase.value.replace('_', ' ').title()} ({analysis.phase_confidence:.0%} confidence)",
        "",
        "─" * 80,
        f"  💡 RECOMMENDATION: {analysis.recommendation}",
        f"  📈 DCA Multiplier: {analysis.dca_multiplier:.2f}x",
        f"  💰 Buffer Deployment: {analysis.buffer_deployment:.0%}",
        "─" * 80,
        "",
        "  📋 ACTION ITEMS:",
    ]

    for item in analysis.action_items:
        lines.append(f"     {item}")

    lines.extend([
        "",
        "  ⚖️ RISK ASSESSMENT:",
        f"     Downside Risk: {analysis.downside_risk.upper()}",
        f"     Upside Potential: {analysis.upside_potential.upper()}",
        f"     Risk/Reward Ratio: {analysis.risk_reward_ratio:.2f}",
        "",
    ])

    # Category summaries
    lines.append("  📊 CATEGORY BREAKDOWN:")
    for cat_name, cat_data in analysis.categories.items():
        indicator = "🟢" if cat_data.weighted_score > 0.3 else "🔴" if cat_data.weighted_score < -0.3 else "⚪"
        lines.append(
            f"     {indicator} {cat_name.upper()}: {cat_data.weighted_score:+.2f} "
            f"({cat_data.bullish_count}↑ {cat_data.bearish_count}↓ {cat_data.neutral_count}○)"
        )

    lines.extend([
        "",
        "  🟢 STRONGEST BULLISH SIGNALS:",
    ])
    for sig in analysis.strongest_bullish[:5]:
        lines.append(f"     • {sig}")

    lines.extend([
        "",
        "  🔴 STRONGEST BEARISH SIGNALS:",
    ])
    for sig in analysis.strongest_bearish[:5]:
        lines.append(f"     • {sig}")

    if analysis.conflicting_signals:
        lines.extend([
            "",
            "  ⚠️ CONFLICTING SIGNALS:",
        ])
        for sig in analysis.conflicting_signals:
            lines.append(f"     • {sig}")

    if analysis.similar_historical_periods:
        lines.extend([
            "",
            "  📜 SIMILAR HISTORICAL PERIODS:",
        ])
        for period in analysis.similar_historical_periods:
            lines.append(f"     • {period}")
        lines.append(f"     ➡️ Outcome: {analysis.historical_outcome}")

    lines.extend([
        "",
        "═" * 80,
    ])

    return "\n".join(lines)
