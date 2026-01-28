"""
Unified Signal Analyzer - 130+ Market Signals

Combines all signal sources into a single comprehensive analysis:
- Base Signals (1-60): extended_signals.py
- Expanded Signals (61-130): expanded_signals.py

Master Composite Score with weighted category analysis and
intelligent DCA/buffer deployment recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import asyncio
import logging

from .extended_signals import (
    ExtendedSignalsAnalyzer,
    ComprehensiveSignalAnalysis,
    SignalStrength,
    SignalResult,
    CategorySummary,
)
from .expanded_signals import (
    ExpandedSignalsAnalyzer,
    ExpandedSignalAnalysis,
    ExpandedCategorySummary,
)

logger = logging.getLogger(__name__)


class MarketCondition(Enum):
    """Overall market condition classification."""
    EXTREME_FEAR = "extreme_fear"          # Composite < -60
    FEAR = "fear"                           # -60 to -30
    MILD_FEAR = "mild_fear"                 # -30 to -10
    NEUTRAL = "neutral"                     # -10 to +10
    MILD_GREED = "mild_greed"              # +10 to +30
    GREED = "greed"                         # +30 to +60
    EXTREME_GREED = "extreme_greed"        # > +60


class CyclePhase(Enum):
    """Market cycle phase."""
    CAPITULATION = "capitulation"
    ACCUMULATION = "accumulation"
    EARLY_BULL = "early_bull"
    BULL_MARKET = "bull_market"
    EUPHORIA = "euphoria"
    DISTRIBUTION = "distribution"
    EARLY_BEAR = "early_bear"
    BEAR_MARKET = "bear_market"


@dataclass
class MasterCategorySummary:
    """Summary for a master category combining multiple sub-categories."""
    name: str
    sub_categories: List[str]
    total_signals: int
    available_signals: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    avg_score: float
    weighted_score: float
    top_bullish_signals: List[str]
    top_bearish_signals: List[str]


@dataclass
class ActionRecommendation:
    """Actionable recommendation based on analysis."""
    action: str
    dca_multiplier: float
    buffer_deployment: float
    confidence: float
    primary_reason: str
    supporting_signals: List[str]
    caution_signals: List[str]
    time_horizon: str  # "immediate", "short_term", "medium_term"


@dataclass
class UnifiedSignalAnalysis:
    """Complete unified analysis with all 130+ signals."""
    timestamp: datetime
    asset: str
    
    # Component analyses
    base_analysis: Optional[ComprehensiveSignalAnalysis]
    expanded_analysis: Optional[ExpandedSignalAnalysis]
    
    # Master category summaries
    price_technical: MasterCategorySummary      # Technical + Order Flow
    sentiment: MasterCategorySummary            # All sentiment sources
    onchain: MasterCategorySummary              # All on-chain metrics
    derivatives: MasterCategorySummary          # Derivatives + Leverage
    macro_cross: MasterCategorySummary          # Macro + Cross-chain
    cycle_position: MasterCategorySummary       # Cycle indicators
    smart_money: MasterCategorySummary          # Smart money behavior
    institutional: MasterCategorySummary        # Institutional metrics
    
    # Overall metrics
    total_signals: int
    available_signals: int
    data_quality: float  # 0-1 based on availability
    
    # Composite scores
    composite_score: float          # Master composite (-100 to +100)
    technical_score: float          # Technical sub-score
    fundamental_score: float        # On-chain/fundamental sub-score
    sentiment_score: float          # Sentiment sub-score
    timing_score: float             # Cycle/calendar timing score
    
    # Classifications
    market_condition: MarketCondition
    cycle_phase: CyclePhase
    trend_direction: str            # "bullish", "bearish", "sideways"
    
    # Recommendations
    primary_recommendation: ActionRecommendation
    alternative_recommendations: List[ActionRecommendation]
    
    # Risk assessment
    risk_level: str                 # "low", "medium", "high", "extreme"
    risk_factors: List[str]
    opportunity_factors: List[str]
    
    # All signals for reference
    all_signals: List[SignalResult] = field(default_factory=list)


class UnifiedSignalAnalyzer:
    """
    Master analyzer combining all 130+ signals into unified recommendations.
    
    Signal Categories:
    1. Price & Technical (16 signals)
    2. Sentiment (14 signals)
    3. On-Chain (24 signals)
    4. Derivatives (16 signals)
    5. Macro & Cross-Chain (16 signals)
    6. Cycle Position (16 signals)
    7. Smart Money (12 signals)
    8. Institutional (10 signals)
    9. Economic Calendar (8 signals)
    10. DeFi/Altcoin (12 signals)
    """
    
    # Master category weights (sum to 10 for easy mental math)
    MASTER_WEIGHTS = {
        "price_technical": 1.0,
        "sentiment": 0.8,
        "onchain": 1.5,          # On-chain is very reliable
        "derivatives": 1.0,
        "macro_cross": 0.7,
        "cycle_position": 1.2,   # Cycle is important for timing
        "smart_money": 1.5,      # Smart money is very reliable
        "institutional": 1.3,
    }
    
    def __init__(self):
        self.base_analyzer = ExtendedSignalsAnalyzer()
        self.expanded_analyzer = ExpandedSignalsAnalyzer()
    
    async def close(self):
        """Close all HTTP sessions."""
        await self.base_analyzer.close()
        await self.expanded_analyzer.close()
    
    async def analyze(self, asset: str = "BTC") -> UnifiedSignalAnalysis:
        """
        Run complete 130+ signal analysis.
        """
        # Run both analyzers concurrently
        base_task = self.base_analyzer.analyze(asset)
        expanded_task = self.expanded_analyzer.analyze(asset)
        
        base_result, expanded_result = await asyncio.gather(
            base_task, expanded_task, return_exceptions=True
        )
        
        # Handle potential errors
        if isinstance(base_result, Exception):
            logger.error(f"Base analysis failed: {base_result}")
            base_result = None
        if isinstance(expanded_result, Exception):
            logger.error(f"Expanded analysis failed: {expanded_result}")
            expanded_result = None
        
        # Collect all signals
        all_signals = []
        if base_result:
            all_signals.extend(base_result.all_signals)
        if expanded_result:
            all_signals.extend(expanded_result.all_signals)
        
        # Create master category summaries
        master_categories = self._create_master_categories(base_result, expanded_result, all_signals)
        
        # Calculate sub-scores
        technical_score = self._calculate_subscore(
            [master_categories["price_technical"], master_categories["derivatives"]]
        )
        fundamental_score = self._calculate_subscore(
            [master_categories["onchain"], master_categories["smart_money"]]
        )
        sentiment_score = self._calculate_subscore(
            [master_categories["sentiment"], master_categories["institutional"]]
        )
        timing_score = self._calculate_subscore(
            [master_categories["cycle_position"], master_categories["macro_cross"]]
        )
        
        # Calculate master composite
        composite_score = self._calculate_master_composite(master_categories)
        
        # Determine market condition
        market_condition = self._classify_market_condition(composite_score)
        
        # Determine cycle phase
        cycle_phase = self._determine_cycle_phase(
            master_categories["cycle_position"],
            master_categories["smart_money"],
            composite_score
        )
        
        # Determine trend
        trend = self._determine_trend(technical_score, fundamental_score)
        
        # Generate recommendations
        primary_rec = self._generate_primary_recommendation(
            composite_score, market_condition, cycle_phase, all_signals
        )
        alt_recs = self._generate_alternative_recommendations(
            composite_score, market_condition, master_categories
        )
        
        # Risk assessment
        risk_level, risk_factors, opps = self._assess_risk(
            composite_score, market_condition, all_signals
        )
        
        # Calculate totals
        total = len(all_signals)
        available = sum(1 for s in all_signals if s.signal != SignalStrength.UNAVAILABLE)
        data_quality = available / total if total > 0 else 0
        
        return UnifiedSignalAnalysis(
            timestamp=datetime.utcnow(),
            asset=asset,
            base_analysis=base_result,
            expanded_analysis=expanded_result,
            price_technical=master_categories["price_technical"],
            sentiment=master_categories["sentiment"],
            onchain=master_categories["onchain"],
            derivatives=master_categories["derivatives"],
            macro_cross=master_categories["macro_cross"],
            cycle_position=master_categories["cycle_position"],
            smart_money=master_categories["smart_money"],
            institutional=master_categories["institutional"],
            total_signals=total,
            available_signals=available,
            data_quality=data_quality,
            composite_score=composite_score,
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            sentiment_score=sentiment_score,
            timing_score=timing_score,
            market_condition=market_condition,
            cycle_phase=cycle_phase,
            trend_direction=trend,
            primary_recommendation=primary_rec,
            alternative_recommendations=alt_recs,
            risk_level=risk_level,
            risk_factors=risk_factors,
            opportunity_factors=opps,
            all_signals=all_signals,
        )
    
    def _create_master_categories(
        self,
        base: Optional[ComprehensiveSignalAnalysis],
        expanded: Optional[ExpandedSignalAnalysis],
        all_signals: List[SignalResult]
    ) -> Dict[str, MasterCategorySummary]:
        """Create master category summaries from component analyses."""
        
        # Define which component categories map to master categories
        category_mapping = {
            "price_technical": {
                "base": ["technical"],
                "expanded": ["order_flow"],
            },
            "sentiment": {
                "base": ["sentiment"],
                "expanded": ["advanced_sentiment"],
            },
            "onchain": {
                "base": ["onchain"],
                "expanded": ["advanced_onchain"],
            },
            "derivatives": {
                "base": ["derivatives"],
                "expanded": [],
            },
            "macro_cross": {
                "base": ["macro"],
                "expanded": ["cross_chain"],
            },
            "cycle_position": {
                "base": [],
                "expanded": ["cycle_position", "economic_calendar"],
            },
            "smart_money": {
                "base": [],
                "expanded": ["smart_money"],
            },
            "institutional": {
                "base": ["institutional"],
                "expanded": ["defi_altcoin"],
            },
        }
        
        summaries = {}
        
        for master_cat, mapping in category_mapping.items():
            signals = []
            sub_cats = []
            
            # Collect from base analysis
            if base:
                for cat_name in mapping["base"]:
                    cat_summary = getattr(base, cat_name, None)
                    if cat_summary and hasattr(cat_summary, 'signals'):
                        signals.extend(cat_summary.signals)
                        sub_cats.append(cat_name)
            
            # Collect from expanded analysis
            if expanded:
                for cat_name in mapping["expanded"]:
                    cat_summary = getattr(expanded, cat_name, None)
                    if cat_summary and hasattr(cat_summary, 'signals'):
                        signals.extend(cat_summary.signals)
                        sub_cats.append(cat_name)
            
            summaries[master_cat] = self._create_master_summary(
                master_cat.replace("_", " ").title(),
                sub_cats,
                signals
            )
        
        return summaries
    
    def _create_master_summary(
        self,
        name: str,
        sub_categories: List[str],
        signals: List[SignalResult]
    ) -> MasterCategorySummary:
        """Create a master category summary."""
        available = [s for s in signals if s.signal != SignalStrength.UNAVAILABLE]
        
        bullish = sum(1 for s in available if s.score > 0)
        bearish = sum(1 for s in available if s.score < 0)
        neutral = sum(1 for s in available if s.score == 0)
        
        if available:
            avg_score = sum(s.score for s in available) / len(available)
            total_weight = sum(s.weight for s in available)
            weighted_score = sum(s.score * s.weight for s in available) / total_weight if total_weight else 0
        else:
            avg_score = 0
            weighted_score = 0
        
        # Get top signals
        sorted_signals = sorted(available, key=lambda s: s.score * s.weight, reverse=True)
        top_bullish = [f"{s.name}: {s.description}" for s in sorted_signals[:3] if s.score > 0]
        
        sorted_signals = sorted(available, key=lambda s: s.score * s.weight)
        top_bearish = [f"{s.name}: {s.description}" for s in sorted_signals[:3] if s.score < 0]
        
        return MasterCategorySummary(
            name=name,
            sub_categories=sub_categories,
            total_signals=len(signals),
            available_signals=len(available),
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            avg_score=avg_score,
            weighted_score=weighted_score,
            top_bullish_signals=top_bullish,
            top_bearish_signals=top_bearish,
        )
    
    def _calculate_subscore(self, categories: List[MasterCategorySummary]) -> float:
        """Calculate sub-score from multiple categories."""
        total_weight = 0
        weighted_sum = 0
        
        for cat in categories:
            if cat.available_signals > 0:
                weight = cat.available_signals
                weighted_sum += cat.weighted_score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0
        
        # Normalize to -100 to +100 range
        raw_score = weighted_sum / total_weight
        return max(-100, min(100, raw_score * 50))
    
    def _calculate_master_composite(
        self,
        categories: Dict[str, MasterCategorySummary]
    ) -> float:
        """Calculate the master composite score."""
        total_weight = 0
        weighted_sum = 0
        
        for cat_name, summary in categories.items():
            if summary.available_signals > 0:
                weight = self.MASTER_WEIGHTS.get(cat_name, 1.0) * summary.available_signals
                weighted_sum += summary.weighted_score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0
        
        # Normalize to -100 to +100 range
        raw_score = weighted_sum / total_weight
        return max(-100, min(100, raw_score * 50))
    
    def _classify_market_condition(self, score: float) -> MarketCondition:
        """Classify overall market condition."""
        if score <= -60:
            return MarketCondition.EXTREME_FEAR
        elif score <= -30:
            return MarketCondition.FEAR
        elif score <= -10:
            return MarketCondition.MILD_FEAR
        elif score <= 10:
            return MarketCondition.NEUTRAL
        elif score <= 30:
            return MarketCondition.MILD_GREED
        elif score <= 60:
            return MarketCondition.GREED
        else:
            return MarketCondition.EXTREME_GREED
    
    def _determine_cycle_phase(
        self,
        cycle_summary: MasterCategorySummary,
        smart_money: MasterCategorySummary,
        composite: float
    ) -> CyclePhase:
        """Determine current market cycle phase."""
        cycle_score = cycle_summary.weighted_score
        smart_score = smart_money.weighted_score
        
        # Combined analysis
        if composite < -60 and smart_score > 0:
            return CyclePhase.CAPITULATION
        elif composite < -30 and smart_score > 0.5:
            return CyclePhase.ACCUMULATION
        elif -30 <= composite < 0 and cycle_score > 0:
            return CyclePhase.EARLY_BULL
        elif 0 <= composite < 30:
            return CyclePhase.BULL_MARKET
        elif 30 <= composite < 60:
            return CyclePhase.EUPHORIA
        elif composite >= 60 or (composite > 30 and smart_score < -0.5):
            return CyclePhase.DISTRIBUTION
        elif composite > 0 and cycle_score < -0.5:
            return CyclePhase.EARLY_BEAR
        else:
            return CyclePhase.BEAR_MARKET
    
    def _determine_trend(self, technical: float, fundamental: float) -> str:
        """Determine overall trend direction."""
        avg = (technical + fundamental) / 2
        
        if avg > 20:
            return "bullish"
        elif avg < -20:
            return "bearish"
        else:
            return "sideways"
    
    def _generate_primary_recommendation(
        self,
        composite: float,
        condition: MarketCondition,
        phase: CyclePhase,
        signals: List[SignalResult]
    ) -> ActionRecommendation:
        """Generate primary action recommendation."""
        
        # DCA multiplier and buffer deployment based on composite score
        if composite <= -60:
            dca_mult = 3.0
            buffer = 0.75
            action = "MAXIMUM ACCUMULATION"
            time_horizon = "immediate"
            reason = f"Extreme fear ({composite:.0f}) with {condition.value} conditions"
        elif composite <= -40:
            dca_mult = 2.5
            buffer = 0.50
            action = "AGGRESSIVE ACCUMULATION"
            time_horizon = "immediate"
            reason = f"Strong fear signals ({composite:.0f})"
        elif composite <= -20:
            dca_mult = 2.0
            buffer = 0.35
            action = "INCREASED DCA"
            time_horizon = "short_term"
            reason = f"Fear present ({composite:.0f})"
        elif composite <= 0:
            dca_mult = 1.5
            buffer = 0.20
            action = "MILD INCREASE"
            time_horizon = "short_term"
            reason = f"Slight fear ({composite:.0f})"
        elif composite <= 20:
            dca_mult = 1.0
            buffer = 0.0
            action = "CONTINUE NORMAL DCA"
            time_horizon = "medium_term"
            reason = f"Neutral market ({composite:.0f})"
        elif composite <= 40:
            dca_mult = 0.75
            buffer = 0.0
            action = "REDUCE DCA"
            time_horizon = "medium_term"
            reason = f"Mild greed present ({composite:.0f})"
        elif composite <= 60:
            dca_mult = 0.5
            buffer = 0.0
            action = "MINIMIZE DCA"
            time_horizon = "medium_term"
            reason = f"Greed elevated ({composite:.0f})"
        else:
            dca_mult = 0.25
            buffer = 0.0
            action = "PAUSE/TAKE PROFITS"
            time_horizon = "immediate"
            reason = f"Extreme greed ({composite:.0f}) - historically dangerous"
        
        # Get supporting and caution signals
        available = [s for s in signals if s.signal != SignalStrength.UNAVAILABLE]
        sorted_bull = sorted(available, key=lambda s: s.score * s.weight, reverse=True)
        sorted_bear = sorted(available, key=lambda s: s.score * s.weight)
        
        supporting = [s.name for s in sorted_bull[:5] if s.score > 0]
        caution = [s.name for s in sorted_bear[:5] if s.score < 0]
        
        # Adjust confidence based on data quality and signal agreement
        bullish_pct = sum(1 for s in available if s.score > 0) / len(available) if available else 0.5
        confidence = abs(bullish_pct - 0.5) * 2  # 0 at 50/50, 1 at 100/0
        
        return ActionRecommendation(
            action=action,
            dca_multiplier=dca_mult,
            buffer_deployment=buffer,
            confidence=confidence,
            primary_reason=reason,
            supporting_signals=supporting,
            caution_signals=caution,
            time_horizon=time_horizon,
        )
    
    def _generate_alternative_recommendations(
        self,
        composite: float,
        condition: MarketCondition,
        categories: Dict[str, MasterCategorySummary]
    ) -> List[ActionRecommendation]:
        """Generate alternative recommendations based on different scenarios."""
        alts = []
        
        # Conservative alternative
        if composite < 0:
            alts.append(ActionRecommendation(
                action="CONSERVATIVE: Standard DCA only",
                dca_multiplier=1.0,
                buffer_deployment=0.0,
                confidence=0.7,
                primary_reason="If uncertain about timing, stick to base DCA",
                supporting_signals=["Long-term DCA works regardless of timing"],
                caution_signals=["May miss opportunity in dips"],
                time_horizon="medium_term",
            ))
        
        # Aggressive alternative
        if composite < -30:
            smart_money_score = categories.get("smart_money", MasterCategorySummary(
                name="", sub_categories=[], total_signals=0, available_signals=0,
                bullish_count=0, bearish_count=0, neutral_count=0,
                avg_score=0, weighted_score=0, top_bullish_signals=[], top_bearish_signals=[]
            )).weighted_score
            
            if smart_money_score > 0.5:
                alts.append(ActionRecommendation(
                    action="AGGRESSIVE: Full buffer deployment",
                    dca_multiplier=3.0,
                    buffer_deployment=1.0,
                    confidence=0.6,
                    primary_reason="Smart money accumulating heavily",
                    supporting_signals=categories["smart_money"].top_bullish_signals,
                    caution_signals=["High risk if bottom not in"],
                    time_horizon="immediate",
                ))
        
        # Defensive alternative
        if composite > 30:
            alts.append(ActionRecommendation(
                action="DEFENSIVE: Pause and build cash",
                dca_multiplier=0.0,
                buffer_deployment=0.0,
                confidence=0.65,
                primary_reason="Build cash reserves for future opportunities",
                supporting_signals=["Patience rewarded in euphoric markets"],
                caution_signals=["May miss continued upside"],
                time_horizon="short_term",
            ))
        
        return alts
    
    def _assess_risk(
        self,
        composite: float,
        condition: MarketCondition,
        signals: List[SignalResult]
    ) -> tuple[str, List[str], List[str]]:
        """Assess overall risk and identify key factors."""
        risks = []
        opportunities = []
        
        # Analyze signals for risk factors
        for s in signals:
            if s.signal == SignalStrength.UNAVAILABLE:
                continue
            
            if s.score <= -2:
                risks.append(f"{s.name}: {s.description}")
            elif s.score >= 2:
                opportunities.append(f"{s.name}: {s.description}")
        
        # Determine risk level
        risk_signal_count = sum(1 for s in signals if s.score < 0 and s.signal != SignalStrength.UNAVAILABLE)
        total_available = sum(1 for s in signals if s.signal != SignalStrength.UNAVAILABLE)
        risk_pct = risk_signal_count / total_available if total_available else 0.5
        
        if risk_pct > 0.7 or composite > 60:
            risk_level = "extreme"
        elif risk_pct > 0.55 or composite > 40:
            risk_level = "high"
        elif risk_pct > 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return risk_level, risks[:10], opportunities[:10]


def format_unified_analysis(analysis: UnifiedSignalAnalysis) -> str:
    """Format the unified analysis for display."""
    lines = [
        "",
        "█" * 80,
        f"█  UNIFIED MARKET ANALYSIS - {analysis.asset}".ljust(79) + "█",
        f"█  {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}".ljust(79) + "█",
        f"█  {analysis.available_signals}/{analysis.total_signals} signals ({analysis.data_quality:.0%} data quality)".ljust(79) + "█",
        "█" * 80,
        "",
    ]
    
    # Market Overview
    lines.extend([
        "┌" + "─" * 78 + "┐",
        "│  MARKET OVERVIEW".ljust(79) + "│",
        "├" + "─" * 78 + "┤",
        f"│  Composite Score:  {analysis.composite_score:+6.1f}  │  Condition: {analysis.market_condition.value.upper()}".ljust(79) + "│",
        f"│  Cycle Phase:      {analysis.cycle_phase.value.replace('_', ' ').title()}".ljust(79) + "│",
        f"│  Trend:            {analysis.trend_direction.upper()}".ljust(79) + "│",
        f"│  Risk Level:       {analysis.risk_level.upper()}".ljust(79) + "│",
        "└" + "─" * 78 + "┘",
        "",
    ])
    
    # Sub-scores
    lines.extend([
        "┌" + "─" * 78 + "┐",
        "│  SUB-SCORES".ljust(79) + "│",
        "├" + "─" * 78 + "┤",
        f"│  Technical:    {analysis.technical_score:+6.1f}  │  Sentiment:   {analysis.sentiment_score:+6.1f}".ljust(79) + "│",
        f"│  Fundamental:  {analysis.fundamental_score:+6.1f}  │  Timing:      {analysis.timing_score:+6.1f}".ljust(79) + "│",
        "└" + "─" * 78 + "┘",
        "",
    ])
    
    # Primary Recommendation
    rec = analysis.primary_recommendation
    lines.extend([
        "╔" + "═" * 78 + "╗",
        f"║  RECOMMENDATION: {rec.action}".ljust(79) + "║",
        "╠" + "═" * 78 + "╣",
        f"║  DCA Multiplier:     {rec.dca_multiplier:.2f}x".ljust(79) + "║",
        f"║  Buffer Deployment:  {rec.buffer_deployment:.0%}".ljust(79) + "║",
        f"║  Confidence:         {rec.confidence:.0%}".ljust(79) + "║",
        f"║  Time Horizon:       {rec.time_horizon.replace('_', ' ').title()}".ljust(79) + "║",
        "╟" + "─" * 78 + "╢",
        f"║  Reason: {rec.primary_reason[:65]}".ljust(79) + "║",
        "╚" + "═" * 78 + "╝",
        "",
    ])
    
    # Category Summaries
    lines.extend([
        "┌" + "─" * 78 + "┐",
        "│  CATEGORY BREAKDOWN".ljust(79) + "│",
        "├" + "─" * 78 + "┤",
    ])
    
    categories = [
        ("Price/Technical", analysis.price_technical),
        ("Sentiment", analysis.sentiment),
        ("On-Chain", analysis.onchain),
        ("Derivatives", analysis.derivatives),
        ("Macro/Cross", analysis.macro_cross),
        ("Cycle Position", analysis.cycle_position),
        ("Smart Money", analysis.smart_money),
        ("Institutional", analysis.institutional),
    ]
    
    for name, cat in categories:
        score_bar = "█" * int(abs(cat.weighted_score) * 5) + "░" * (10 - int(abs(cat.weighted_score) * 5))
        direction = "+" if cat.weighted_score >= 0 else "-"
        line = f"│  {name:<15} [{score_bar}] {direction}{abs(cat.weighted_score):.2f}  ({cat.bullish_count}🟢 {cat.bearish_count}🔴 {cat.neutral_count}⚪)"
        lines.append(line.ljust(79) + "│")
    
    lines.append("└" + "─" * 78 + "┘")
    lines.append("")
    
    # Top Signals
    if rec.supporting_signals:
        lines.append("  TOP BULLISH SIGNALS:")
        for sig in rec.supporting_signals[:5]:
            lines.append(f"    🟢 {sig}")
        lines.append("")
    
    if rec.caution_signals:
        lines.append("  TOP BEARISH SIGNALS:")
        for sig in rec.caution_signals[:5]:
            lines.append(f"    🔴 {sig}")
        lines.append("")
    
    # Alternative Recommendations
    if analysis.alternative_recommendations:
        lines.append("  ALTERNATIVE STRATEGIES:")
        for alt in analysis.alternative_recommendations:
            lines.append(f"    • {alt.action}")
            lines.append(f"      DCA: {alt.dca_multiplier:.1f}x | Buffer: {alt.buffer_deployment:.0%} | {alt.primary_reason}")
        lines.append("")
    
    # Risk Factors
    if analysis.risk_factors:
        lines.append("  ⚠️  KEY RISK FACTORS:")
        for risk in analysis.risk_factors[:5]:
            lines.append(f"    • {risk}")
        lines.append("")
    
    if analysis.opportunity_factors:
        lines.append("  ✅ KEY OPPORTUNITIES:")
        for opp in analysis.opportunity_factors[:5]:
            lines.append(f"    • {opp}")
    
    lines.append("")
    lines.append("█" * 80)
    
    return "\n".join(lines)


# Quick analysis function for CLI
async def quick_unified_analysis(asset: str = "BTC") -> str:
    """Run unified analysis and return formatted output."""
    analyzer = UnifiedSignalAnalyzer()
    try:
        result = await analyzer.analyze(asset)
        return format_unified_analysis(result)
    finally:
        await analyzer.close()
