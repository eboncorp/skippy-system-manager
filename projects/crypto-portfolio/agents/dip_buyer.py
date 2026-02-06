"""
Dip Buying Agent

Automatically adjusts DCA amounts based on market conditions:
- Monitors price drawdowns from recent highs
- Uses Fear & Greed Index as confirmation
- Deploys cash buffer during significant dips
- Scales DCA multiplier based on dip severity

Strategy:
- Normal market: 1.0x DCA
- 10-20% dip: 1.25x DCA
- 20-30% dip: 1.5x DCA
- 30-40% dip: 2.0x DCA
- 40%+ dip: 2.5x DCA + deploy cash buffer
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from data.prices import PriceService
from agents.market_intel import MarketIntelAgent
from agents.alerts import alert_manager, AlertType, Alert
from agents.advanced_conditions import AdvancedMarketAnalyzer, ComprehensiveAnalysis
from config import TARGET_ALLOCATION, DCA_ALLOCATION

logger = logging.getLogger(__name__)


class MarketCondition(Enum):
    """Current market condition based on drawdown analysis."""
    EUPHORIA = "euphoria"       # Near ATH, reduce DCA
    NORMAL = "normal"           # Standard DCA
    MILD_DIP = "mild_dip"       # 10-20% down, slight increase
    MODERATE_DIP = "moderate"   # 20-30% down, notable increase
    SIGNIFICANT_DIP = "significant"  # 30-40% down, aggressive
    EXTREME_DIP = "extreme"     # 40%+ down, max aggression


@dataclass
class DipMultipliers:
    """DCA multipliers for each market condition."""
    euphoria: float = 0.75      # Reduce buying near highs
    normal: float = 1.0
    mild_dip: float = 1.25
    moderate_dip: float = 1.5
    significant_dip: float = 2.0
    extreme_dip: float = 2.5


@dataclass
class AssetDipAnalysis:
    """Dip analysis for a single asset."""
    asset: str
    current_price: Decimal
    high_30d: Decimal
    high_90d: Decimal
    drawdown_30d: float  # Percentage below 30-day high
    drawdown_90d: float  # Percentage below 90-day high
    condition: MarketCondition
    dca_multiplier: float
    
    @property
    def is_buying_opportunity(self) -> bool:
        return self.condition in (
            MarketCondition.MODERATE_DIP,
            MarketCondition.SIGNIFICANT_DIP,
            MarketCondition.EXTREME_DIP,
        )


@dataclass
class MarketDipAnalysis:
    """Complete market dip analysis."""
    timestamp: datetime
    fear_greed_index: int
    fear_greed_label: str
    btc_drawdown: float
    eth_drawdown: float
    avg_portfolio_drawdown: float
    overall_condition: MarketCondition
    overall_multiplier: float
    asset_analyses: Dict[str, AssetDipAnalysis]
    recommended_action: str
    deploy_cash_buffer: bool
    cash_buffer_deployment_pct: float


@dataclass 
class DipBuyerConfig:
    """Configuration for the dip buying agent."""
    # Drawdown thresholds (from recent high)
    mild_dip_threshold: float = 0.10      # 10%
    moderate_dip_threshold: float = 0.20  # 20%
    significant_dip_threshold: float = 0.30  # 30%
    extreme_dip_threshold: float = 0.40   # 40%
    
    # Fear & Greed thresholds
    extreme_fear_threshold: int = 25      # Below this = extreme fear
    fear_threshold: int = 40              # Below this = fear
    greed_threshold: int = 60             # Above this = greed
    extreme_greed_threshold: int = 75     # Above this = extreme greed
    
    # Cash buffer deployment
    deploy_buffer_at_significant: bool = True
    buffer_deployment_mild: float = 0.0       # Don't deploy in mild dip
    buffer_deployment_moderate: float = 0.25  # Deploy 25% of buffer
    buffer_deployment_significant: float = 0.50  # Deploy 50%
    buffer_deployment_extreme: float = 0.75   # Deploy 75%
    
    # Lookback periods (days)
    short_lookback: int = 30
    long_lookback: int = 90
    
    # Multipliers
    multipliers: DipMultipliers = field(default_factory=DipMultipliers)


class DipBuyingAgent:
    """Agent that monitors for dips and adjusts DCA accordingly."""
    
    def __init__(
        self,
        price_service: Optional[PriceService] = None,
        config: Optional[DipBuyerConfig] = None,
        storage_path: str = "./data/dip_buyer.json",
    ):
        self.price_service = price_service or PriceService()
        self.config = config or DipBuyerConfig()
        self.storage_path = Path(storage_path)
        
        self._price_history: Dict[str, List[Tuple[datetime, Decimal]]] = {}
        self._last_analysis: Optional[MarketDipAnalysis] = None
        self._market_intel = MarketIntelAgent()
        self._advanced_analyzer = AdvancedMarketAnalyzer(price_service)
        
        self._load_state()
    
    def _load_state(self):
        """Load historical price data."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    
                    for asset, history in data.get("price_history", {}).items():
                        self._price_history[asset] = [
                            (datetime.fromisoformat(h[0]), Decimal(str(h[1])))
                            for h in history
                        ]
            except Exception as e:
                logger.warning("Failed to load dip buyer state: %s", e)
    
    def _save_state(self):
        """Save state to disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to serializable format
        history_data = {}
        for asset, history in self._price_history.items():
            history_data[asset] = [
                [h[0].isoformat(), str(h[1])] for h in history
            ]
        
        with open(self.storage_path, "w") as f:
            json.dump({"price_history": history_data}, f)
    
    async def update_prices(self):
        """Fetch and store current prices."""
        assets = list(TARGET_ALLOCATION.keys())
        assets = [a for a in assets if a != "CASH"]
        
        prices = await self.price_service.get_prices(assets)
        now = datetime.now()
        
        for asset, price in prices.items():
            if asset not in self._price_history:
                self._price_history[asset] = []
            
            self._price_history[asset].append((now, price))
            
            # Keep only last 180 days of data
            cutoff = now - timedelta(days=180)
            self._price_history[asset] = [
                (dt, p) for dt, p in self._price_history[asset]
                if dt > cutoff
            ]
        
        self._save_state()
        return prices
    
    def _get_high_price(self, asset: str, days: int) -> Optional[Decimal]:
        """Get highest price in the last N days."""
        if asset not in self._price_history:
            return None
        
        cutoff = datetime.now() - timedelta(days=days)
        relevant = [p for dt, p in self._price_history[asset] if dt > cutoff]
        
        if not relevant:
            return None
        
        return max(relevant)
    
    def _calculate_drawdown(
        self,
        current_price: Decimal,
        high_price: Decimal,
    ) -> float:
        """Calculate percentage drawdown from high."""
        if high_price <= 0:
            return 0.0
        
        return float((high_price - current_price) / high_price)
    
    def _determine_condition(self, drawdown: float, fear_greed: int) -> MarketCondition:
        """Determine market condition based on drawdown and sentiment."""
        cfg = self.config
        
        # Use the worse of drawdown or sentiment
        # If price is down but sentiment is greedy, don't scale up as much
        
        if drawdown >= cfg.extreme_dip_threshold:
            return MarketCondition.EXTREME_DIP
        elif drawdown >= cfg.significant_dip_threshold:
            return MarketCondition.SIGNIFICANT_DIP
        elif drawdown >= cfg.moderate_dip_threshold:
            return MarketCondition.MODERATE_DIP
        elif drawdown >= cfg.mild_dip_threshold:
            return MarketCondition.MILD_DIP
        elif drawdown < 0.05 and fear_greed > cfg.extreme_greed_threshold:
            # Near highs AND extreme greed = euphoria
            return MarketCondition.EUPHORIA
        else:
            return MarketCondition.NORMAL
    
    def _get_multiplier(self, condition: MarketCondition) -> float:
        """Get DCA multiplier for a condition."""
        m = self.config.multipliers
        
        return {
            MarketCondition.EUPHORIA: m.euphoria,
            MarketCondition.NORMAL: m.normal,
            MarketCondition.MILD_DIP: m.mild_dip,
            MarketCondition.MODERATE_DIP: m.moderate_dip,
            MarketCondition.SIGNIFICANT_DIP: m.significant_dip,
            MarketCondition.EXTREME_DIP: m.extreme_dip,
        }.get(condition, 1.0)
    
    def _get_buffer_deployment(self, condition: MarketCondition) -> float:
        """Get cash buffer deployment percentage."""
        cfg = self.config
        
        if not cfg.deploy_buffer_at_significant:
            return 0.0
        
        return {
            MarketCondition.EUPHORIA: 0.0,
            MarketCondition.NORMAL: 0.0,
            MarketCondition.MILD_DIP: cfg.buffer_deployment_mild,
            MarketCondition.MODERATE_DIP: cfg.buffer_deployment_moderate,
            MarketCondition.SIGNIFICANT_DIP: cfg.buffer_deployment_significant,
            MarketCondition.EXTREME_DIP: cfg.buffer_deployment_extreme,
        }.get(condition, 0.0)
    
    async def analyze_market(self) -> MarketDipAnalysis:
        """Perform full market dip analysis."""
        # Get current prices
        current_prices = await self.update_prices()
        
        # Get Fear & Greed Index
        try:
            fg_data = await self._market_intel.get_fear_greed_index()
            fear_greed = fg_data.get("value", 50)
            fg_label = fg_data.get("label", "Neutral")
        except Exception as e:
            logger.warning("Failed to fetch Fear & Greed index: %s", e)
            fear_greed = None
            fg_label = "Unavailable"
        
        # Analyze each asset
        asset_analyses = {}
        total_drawdown = 0
        count = 0
        
        for asset, current_price in current_prices.items():
            if asset == "CASH":
                continue
            
            high_30d = self._get_high_price(asset, self.config.short_lookback)
            high_90d = self._get_high_price(asset, self.config.long_lookback)
            
            if high_30d is None:
                high_30d = current_price
            if high_90d is None:
                high_90d = current_price
            
            drawdown_30d = self._calculate_drawdown(current_price, high_30d)
            drawdown_90d = self._calculate_drawdown(current_price, high_90d)
            
            # Use the larger drawdown for condition
            max_drawdown = max(drawdown_30d, drawdown_90d)
            condition = self._determine_condition(max_drawdown, fear_greed)
            multiplier = self._get_multiplier(condition)
            
            asset_analyses[asset] = AssetDipAnalysis(
                asset=asset,
                current_price=current_price,
                high_30d=high_30d,
                high_90d=high_90d,
                drawdown_30d=drawdown_30d,
                drawdown_90d=drawdown_90d,
                condition=condition,
                dca_multiplier=multiplier,
            )
            
            # Weight by allocation
            weight = TARGET_ALLOCATION.get(asset, 0)
            total_drawdown += max_drawdown * weight
            count += weight
        
        # Calculate portfolio-weighted average drawdown
        avg_drawdown = total_drawdown / count if count > 0 else 0
        
        # Get BTC and ETH specific drawdowns
        btc_analysis = asset_analyses.get("BTC")
        eth_analysis = asset_analyses.get("ETH")
        
        btc_drawdown = max(btc_analysis.drawdown_30d, btc_analysis.drawdown_90d) if btc_analysis else 0
        eth_drawdown = max(eth_analysis.drawdown_30d, eth_analysis.drawdown_90d) if eth_analysis else 0
        
        # Overall condition based on BTC/ETH (market leaders)
        leader_drawdown = max(btc_drawdown, eth_drawdown)
        overall_condition = self._determine_condition(leader_drawdown, fear_greed)
        overall_multiplier = self._get_multiplier(overall_condition)
        
        # Cash buffer deployment
        buffer_pct = self._get_buffer_deployment(overall_condition)
        deploy_buffer = buffer_pct > 0
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            overall_condition, overall_multiplier, buffer_pct, fear_greed
        )
        
        analysis = MarketDipAnalysis(
            timestamp=datetime.now(),
            fear_greed_index=fear_greed,
            fear_greed_label=fg_label,
            btc_drawdown=btc_drawdown,
            eth_drawdown=eth_drawdown,
            avg_portfolio_drawdown=avg_drawdown,
            overall_condition=overall_condition,
            overall_multiplier=overall_multiplier,
            asset_analyses=asset_analyses,
            recommended_action=recommendation,
            deploy_cash_buffer=deploy_buffer,
            cash_buffer_deployment_pct=buffer_pct,
        )
        
        self._last_analysis = analysis
        return analysis
    
    def _generate_recommendation(
        self,
        condition: MarketCondition,
        multiplier: float,
        buffer_pct: float,
        fear_greed: int,
    ) -> str:
        """Generate human-readable recommendation."""
        
        if condition == MarketCondition.EUPHORIA:
            return (
                f"⚠️ EUPHORIA: Market near highs with Fear/Greed at {fear_greed}. "
                f"Reduce DCA to {multiplier:.0%}x normal. Consider taking some profits."
            )
        
        elif condition == MarketCondition.NORMAL:
            return (
                f"✅ NORMAL: Market conditions stable. "
                f"Continue standard DCA at {multiplier:.0%}x."
            )
        
        elif condition == MarketCondition.MILD_DIP:
            return (
                f"📉 MILD DIP: Market down 10-20%. "
                f"Slight DCA increase to {multiplier:.0%}x recommended."
            )
        
        elif condition == MarketCondition.MODERATE_DIP:
            return (
                f"📉 MODERATE DIP: Market down 20-30%. "
                f"Increase DCA to {multiplier:.0%}x. "
                f"Deploy {buffer_pct:.0%} of cash buffer."
            )
        
        elif condition == MarketCondition.SIGNIFICANT_DIP:
            return (
                f"🔥 SIGNIFICANT DIP: Market down 30-40%! "
                f"Aggressive DCA at {multiplier:.0%}x. "
                f"Deploy {buffer_pct:.0%} of cash buffer. This is an opportunity."
            )
        
        elif condition == MarketCondition.EXTREME_DIP:
            return (
                f"💎 EXTREME DIP: Market down 40%+! Capitulation zone. "
                f"Maximum DCA at {multiplier:.0%}x. "
                f"Deploy {buffer_pct:.0%} of cash buffer. Generational buying opportunity."
            )
        
        return "Continue normal DCA."
    
    def get_adjusted_dca_amounts(
        self,
        base_daily_amount: float,
        analysis: Optional[MarketDipAnalysis] = None,
    ) -> Dict[str, Decimal]:
        """
        Get adjusted DCA amounts based on current market conditions.
        
        Returns dict of asset -> USD amount to buy today.
        """
        if analysis is None:
            analysis = self._last_analysis
        
        if analysis is None:
            # No analysis available, use base amounts
            return {
                asset: Decimal(str(base_daily_amount * alloc))
                for asset, alloc in DCA_ALLOCATION.items()
            }
        
        adjusted_amounts = {}
        
        for asset, alloc in DCA_ALLOCATION.items():
            base_amount = base_daily_amount * alloc
            
            # Get asset-specific multiplier if available
            asset_analysis = analysis.asset_analyses.get(asset)
            if asset_analysis:
                multiplier = asset_analysis.dca_multiplier
            else:
                multiplier = analysis.overall_multiplier
            
            adjusted_amounts[asset] = Decimal(str(base_amount * multiplier))
        
        return adjusted_amounts
    
    def get_cash_buffer_deployment(
        self,
        total_cash_buffer: float,
        analysis: Optional[MarketDipAnalysis] = None,
    ) -> Dict[str, Decimal]:
        """
        Get amounts to deploy from cash buffer during dips.
        
        Returns dict of asset -> USD amount to deploy.
        """
        if analysis is None:
            analysis = self._last_analysis
        
        if analysis is None or not analysis.deploy_cash_buffer:
            return {}
        
        deploy_amount = total_cash_buffer * analysis.cash_buffer_deployment_pct
        
        if deploy_amount < 100:  # Minimum deployment
            return {}
        
        # Distribute according to DCA allocation
        deployment = {}
        for asset, alloc in DCA_ALLOCATION.items():
            deployment[asset] = Decimal(str(deploy_amount * alloc))
        
        return deployment
    
    async def send_dip_alert(self, analysis: MarketDipAnalysis):
        """Send alert about dip buying opportunity."""
        if analysis.overall_condition in (
            MarketCondition.MODERATE_DIP,
            MarketCondition.SIGNIFICANT_DIP,
            MarketCondition.EXTREME_DIP,
        ):
            emoji = {
                MarketCondition.MODERATE_DIP: "📉",
                MarketCondition.SIGNIFICANT_DIP: "🔥",
                MarketCondition.EXTREME_DIP: "💎",
            }[analysis.overall_condition]
            
            message = (
                f"{emoji} DIP BUYING OPPORTUNITY\n\n"
                f"Condition: {analysis.overall_condition.value.upper()}\n"
                f"BTC Drawdown: {analysis.btc_drawdown:.1%}\n"
                f"ETH Drawdown: {analysis.eth_drawdown:.1%}\n"
                f"Fear & Greed: {analysis.fear_greed_index} ({analysis.fear_greed_label})\n\n"
                f"DCA Multiplier: {analysis.overall_multiplier:.1f}x\n"
                f"Cash Buffer Deploy: {analysis.cash_buffer_deployment_pct:.0%}\n\n"
                f"{analysis.recommended_action}"
            )
            
            alert = Alert(
                type=AlertType.PRICE_ALERT,
                title=f"Dip Buying Alert: {analysis.overall_condition.value}",
                message=message,
                priority="high" if analysis.overall_condition == MarketCondition.EXTREME_DIP else "normal",
                data={
                    "condition": analysis.overall_condition.value,
                    "multiplier": analysis.overall_multiplier,
                    "btc_drawdown": analysis.btc_drawdown,
                    "eth_drawdown": analysis.eth_drawdown,
                    "fear_greed": analysis.fear_greed_index,
                },
            )
            
            await alert_manager.send_alert(alert)
    
    async def close(self):
        """Close connections."""
        await self._market_intel.close()
        await self._advanced_analyzer.close()
    
    async def get_enhanced_analysis(self, assets: List[str] = None) -> Tuple[MarketDipAnalysis, ComprehensiveAnalysis]:
        """
        Get enhanced analysis combining drawdown analysis with advanced signals.
        
        Returns both analyses so they can be combined for better decision making.
        """
        if assets is None:
            assets = [a for a in TARGET_ALLOCATION.keys() if a != "CASH"]
        
        # Run both analyses
        dip_analysis = await self.analyze_market()
        advanced_analysis = await self._advanced_analyzer.analyze(assets[:5])  # Top 5 assets
        
        return dip_analysis, advanced_analysis
    
    def get_combined_multiplier(
        self,
        dip_analysis: MarketDipAnalysis,
        advanced_analysis: ComprehensiveAnalysis,
    ) -> float:
        """
        Combine drawdown-based multiplier with advanced signals.
        
        Uses weighted average:
        - 60% weight on drawdown analysis (price-based)
        - 40% weight on advanced signals (technical + sentiment)
        """
        drawdown_mult = dip_analysis.overall_multiplier
        advanced_mult = advanced_analysis.recommended_multiplier
        
        # Weighted combination
        combined = (drawdown_mult * 0.6) + (advanced_mult * 0.4)
        
        # Apply confidence adjustment
        # If signals disagree significantly, reduce confidence
        if abs(drawdown_mult - advanced_mult) > 0.5:
            # Signals disagree - be more conservative
            combined = min(drawdown_mult, advanced_mult) + 0.25
        
        return round(combined, 2)


def format_dip_analysis(analysis: MarketDipAnalysis) -> str:
    """Format dip analysis for display."""
    lines = []
    
    # Header
    condition_emoji = {
        MarketCondition.EUPHORIA: "🎉",
        MarketCondition.NORMAL: "✅",
        MarketCondition.MILD_DIP: "📉",
        MarketCondition.MODERATE_DIP: "📉",
        MarketCondition.SIGNIFICANT_DIP: "🔥",
        MarketCondition.EXTREME_DIP: "💎",
    }
    
    lines.append("=" * 70)
    lines.append(f"  DIP ANALYSIS - {analysis.timestamp.strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 70)
    lines.append("")
    
    # Market sentiment
    lines.append(f"  Fear & Greed Index: {analysis.fear_greed_index} ({analysis.fear_greed_label})")
    lines.append(f"  BTC Drawdown from High: {analysis.btc_drawdown:.1%}")
    lines.append(f"  ETH Drawdown from High: {analysis.eth_drawdown:.1%}")
    lines.append(f"  Portfolio Avg Drawdown: {analysis.avg_portfolio_drawdown:.1%}")
    lines.append("")
    
    # Overall condition
    emoji = condition_emoji.get(analysis.overall_condition, "")
    lines.append(f"  {emoji} CONDITION: {analysis.overall_condition.value.upper()}")
    lines.append(f"  DCA Multiplier: {analysis.overall_multiplier:.2f}x")
    
    if analysis.deploy_cash_buffer:
        lines.append(f"  Cash Buffer Deployment: {analysis.cash_buffer_deployment_pct:.0%}")
    
    lines.append("")
    lines.append("  " + "-" * 66)
    lines.append(f"  {analysis.recommended_action}")
    lines.append("  " + "-" * 66)
    lines.append("")
    
    # Asset breakdown
    lines.append("  Asset Breakdown:")
    lines.append(f"  {'Asset':<8} {'Price':>12} {'30d High':>12} {'Drawdown':>10} {'Multiplier':>12}")
    lines.append("  " + "-" * 58)
    
    for asset, a in sorted(analysis.asset_analyses.items()):
        dd = max(a.drawdown_30d, a.drawdown_90d)
        lines.append(
            f"  {asset:<8} ${float(a.current_price):>11,.2f} ${float(a.high_30d):>11,.2f} "
            f"{dd:>9.1%} {a.dca_multiplier:>11.2f}x"
        )
    
    lines.append("")
    
    return "\n".join(lines)


# Convenience function
async def analyze_dip_opportunity() -> MarketDipAnalysis:
    """Quick function to analyze current dip opportunity."""
    agent = DipBuyingAgent()
    try:
        return await agent.analyze_market()
    finally:
        await agent.close()
