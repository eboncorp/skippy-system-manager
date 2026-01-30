"""
AI Enhancements for Crypto Portfolio Manager.

Implements:
- Machine Learning price prediction models
- Sentiment analysis from social media and news
- Natural language report generation
- Anomaly detection for unusual market conditions
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math
import asyncio
import re


class SentimentScore(Enum):
    """Sentiment classification levels."""
    VERY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    VERY_BULLISH = 2


@dataclass
class PricePrediction:
    """Price prediction result."""
    asset: str
    current_price: float
    predicted_price_24h: float
    predicted_price_7d: float
    predicted_price_30d: float
    confidence: float  # 0-1
    model_used: str
    prediction_timestamp: datetime = field(default_factory=datetime.now)

    @property
    def predicted_change_24h(self) -> float:
        """Predicted 24h change percentage."""
        if self.current_price == 0:
            return 0
        return ((self.predicted_price_24h - self.current_price) / self.current_price) * 100

    @property
    def predicted_change_7d(self) -> float:
        """Predicted 7d change percentage."""
        if self.current_price == 0:
            return 0
        return ((self.predicted_price_7d - self.current_price) / self.current_price) * 100


@dataclass
class SentimentAnalysis:
    """Sentiment analysis result for an asset."""
    asset: str
    overall_score: SentimentScore
    social_score: float  # -1 to 1
    news_score: float  # -1 to 1
    onchain_score: float  # -1 to 1
    sources_analyzed: int
    key_topics: List[str]
    analysis_timestamp: datetime = field(default_factory=datetime.now)

    @property
    def composite_score(self) -> float:
        """Weighted composite sentiment score."""
        return (
            self.social_score * 0.3 +
            self.news_score * 0.4 +
            self.onchain_score * 0.3
        )


@dataclass
class MarketAnomaly:
    """Detected market anomaly."""
    anomaly_type: str
    asset: str
    severity: str  # "low", "medium", "high"
    description: str
    metrics: Dict[str, float]
    detected_at: datetime = field(default_factory=datetime.now)


class SimplePricePredictor:
    """
    Simple price prediction using statistical methods.

    Note: This is a simplified implementation. Production systems should
    use proper ML frameworks like TensorFlow/PyTorch with trained models.
    """

    def __init__(self):
        self.model_name = "statistical_ensemble"

    def predict(
        self,
        prices: List[float],
        volumes: Optional[List[float]] = None,
    ) -> Tuple[float, float, float, float]:
        """
        Predict future prices based on historical data.

        Args:
            prices: Historical prices (most recent last)
            volumes: Optional volume data

        Returns:
            Tuple of (price_24h, price_7d, price_30d, confidence)
        """
        if len(prices) < 30:
            return prices[-1], prices[-1], prices[-1], 0.0

        current = prices[-1]

        # Calculate trends
        ma_7 = sum(prices[-7:]) / 7
        ma_30 = sum(prices[-30:]) / 30
        ma_90 = sum(prices[-90:]) / 90 if len(prices) >= 90 else ma_30

        # Trend direction
        short_trend = (current - ma_7) / ma_7 if ma_7 > 0 else 0
        medium_trend = (ma_7 - ma_30) / ma_30 if ma_30 > 0 else 0
        long_trend = (ma_30 - ma_90) / ma_90 if ma_90 > 0 else 0

        # Volatility (for confidence)
        returns = [
            (prices[i] - prices[i-1]) / prices[i-1]
            for i in range(1, len(prices))
            if prices[i-1] > 0
        ]
        volatility = self._calculate_volatility(returns) if returns else 0.1

        # Mean reversion factor
        distance_from_ma = (current - ma_30) / ma_30 if ma_30 > 0 else 0
        mean_reversion = -distance_from_ma * 0.1  # Pull towards mean

        # Momentum factor
        momentum = short_trend * 0.5 + medium_trend * 0.3 + long_trend * 0.2

        # Combined prediction
        daily_change = (momentum + mean_reversion) / 10  # Dampen predictions

        # Project forward
        price_24h = current * (1 + daily_change)
        price_7d = current * (1 + daily_change * 5)  # Not linear, dampened
        price_30d = current * (1 + daily_change * 15)  # Further dampened

        # Confidence based on volatility and data quality
        confidence = max(0.1, min(0.8, 1 - volatility * 2))

        return price_24h, price_7d, price_30d, confidence

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate annualized volatility."""
        if not returns:
            return 0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        daily_vol = math.sqrt(variance)
        return daily_vol * math.sqrt(365)  # Annualize


class SentimentAnalyzer:
    """
    Analyzes sentiment from various sources.

    Combines:
    - Social media sentiment (simulated)
    - News sentiment
    - On-chain metrics sentiment
    """

    # Keywords for basic sentiment analysis
    BULLISH_KEYWORDS = [
        "moon", "bullish", "buy", "accumulate", "breakout", "rally",
        "ath", "pump", "long", "hodl", "adoption", "institutional",
        "partnership", "upgrade", "etf", "approval"
    ]

    BEARISH_KEYWORDS = [
        "bear", "crash", "sell", "dump", "short", "correction",
        "bubble", "scam", "hack", "regulation", "ban", "fud",
        "liquidation", "bankruptcy", "fear", "panic"
    ]

    def __init__(self):
        self.cache: Dict[str, SentimentAnalysis] = {}
        self.cache_ttl = timedelta(minutes=15)

    async def analyze(
        self,
        asset: str,
        news_items: Optional[List[str]] = None,
        social_posts: Optional[List[str]] = None,
        onchain_metrics: Optional[Dict[str, float]] = None,
    ) -> SentimentAnalysis:
        """
        Analyze sentiment for an asset.

        Args:
            asset: Asset symbol
            news_items: List of news headlines/snippets
            social_posts: List of social media posts
            onchain_metrics: On-chain metrics dict

        Returns:
            SentimentAnalysis result
        """
        # Check cache
        if asset in self.cache:
            cached = self.cache[asset]
            if datetime.now() - cached.analysis_timestamp < self.cache_ttl:
                return cached

        # Analyze each source
        social_score = self._analyze_text_sentiment(social_posts or [])
        news_score = self._analyze_text_sentiment(news_items or [])
        onchain_score = self._analyze_onchain_sentiment(onchain_metrics or {})

        # Extract key topics
        all_text = " ".join((news_items or []) + (social_posts or []))
        key_topics = self._extract_topics(all_text, asset)

        # Determine overall score
        composite = social_score * 0.3 + news_score * 0.4 + onchain_score * 0.3

        if composite > 0.5:
            overall = SentimentScore.VERY_BULLISH
        elif composite > 0.2:
            overall = SentimentScore.BULLISH
        elif composite < -0.5:
            overall = SentimentScore.VERY_BEARISH
        elif composite < -0.2:
            overall = SentimentScore.BEARISH
        else:
            overall = SentimentScore.NEUTRAL

        sources_count = len(news_items or []) + len(social_posts or [])

        result = SentimentAnalysis(
            asset=asset,
            overall_score=overall,
            social_score=social_score,
            news_score=news_score,
            onchain_score=onchain_score,
            sources_analyzed=sources_count,
            key_topics=key_topics,
        )

        self.cache[asset] = result
        return result

    def _analyze_text_sentiment(self, texts: List[str]) -> float:
        """
        Simple keyword-based sentiment analysis.

        Returns score from -1 (very bearish) to 1 (very bullish).
        """
        if not texts:
            return 0.0

        total_score = 0
        for text in texts:
            text_lower = text.lower()

            bullish_count = sum(
                1 for kw in self.BULLISH_KEYWORDS if kw in text_lower
            )
            bearish_count = sum(
                1 for kw in self.BEARISH_KEYWORDS if kw in text_lower
            )

            if bullish_count + bearish_count > 0:
                text_score = (bullish_count - bearish_count) / (bullish_count + bearish_count)
                total_score += text_score

        return max(-1, min(1, total_score / max(1, len(texts))))

    def _analyze_onchain_sentiment(self, metrics: Dict[str, float]) -> float:
        """
        Analyze on-chain metrics for sentiment signals.

        Args:
            metrics: Dict with keys like "exchange_netflow", "active_addresses", etc.

        Returns:
            Score from -1 to 1
        """
        if not metrics:
            return 0.0

        score = 0.0
        signals = 0

        # Exchange netflow (negative = bullish, coins leaving exchanges)
        if "exchange_netflow" in metrics:
            netflow = metrics["exchange_netflow"]
            if netflow < -1000:
                score += 0.5
            elif netflow > 1000:
                score -= 0.5
            signals += 1

        # Active addresses (increasing = bullish)
        if "active_addresses_change" in metrics:
            change = metrics["active_addresses_change"]
            if change > 0.1:
                score += 0.3
            elif change < -0.1:
                score -= 0.3
            signals += 1

        # Whale transactions (context dependent)
        if "whale_transactions" in metrics:
            whales = metrics["whale_transactions"]
            if whales > 100:
                score += 0.2  # Accumulation signal
            signals += 1

        # MVRV ratio (Market Value to Realized Value)
        if "mvrv_ratio" in metrics:
            mvrv = metrics["mvrv_ratio"]
            if mvrv < 1:
                score += 0.4  # Undervalued
            elif mvrv > 3:
                score -= 0.4  # Overvalued
            signals += 1

        return score / max(1, signals)

    def _extract_topics(self, text: str, asset: str) -> List[str]:
        """Extract key topics from text."""
        topics = []

        # Check for common topic patterns
        topic_patterns = {
            "ETF": r"\b(etf|fund|grayscale)\b",
            "Regulation": r"\b(sec|regulation|lawsuit|legal)\b",
            "DeFi": r"\b(defi|yield|staking|lending)\b",
            "Adoption": r"\b(adoption|institutional|corporate)\b",
            "Technology": r"\b(upgrade|fork|scaling|layer\s*2)\b",
            "Market": r"\b(ath|bull|bear|crash|rally)\b",
        }

        text_lower = text.lower()
        for topic, pattern in topic_patterns.items():
            if re.search(pattern, text_lower):
                topics.append(topic)

        return topics[:5]  # Return top 5 topics


class AnomalyDetector:
    """
    Detects anomalies in market data.

    Identifies:
    - Unusual price movements
    - Volume spikes
    - Correlation breakdowns
    - Liquidity issues
    """

    def __init__(
        self,
        price_threshold: float = 3.0,  # Standard deviations
        volume_threshold: float = 3.0,
    ):
        self.price_threshold = price_threshold
        self.volume_threshold = volume_threshold

    def detect_anomalies(
        self,
        asset: str,
        prices: List[float],
        volumes: Optional[List[float]] = None,
        correlations: Optional[Dict[str, float]] = None,
    ) -> List[MarketAnomaly]:
        """
        Detect anomalies in market data.

        Args:
            asset: Asset symbol
            prices: Historical prices
            volumes: Historical volumes
            correlations: Current correlations vs historical

        Returns:
            List of detected MarketAnomaly objects
        """
        anomalies = []

        # Price anomaly detection
        if len(prices) >= 30:
            price_anomaly = self._detect_price_anomaly(asset, prices)
            if price_anomaly:
                anomalies.append(price_anomaly)

        # Volume anomaly detection
        if volumes and len(volumes) >= 30:
            volume_anomaly = self._detect_volume_anomaly(asset, volumes)
            if volume_anomaly:
                anomalies.append(volume_anomaly)

        # Correlation breakdown detection
        if correlations:
            corr_anomaly = self._detect_correlation_anomaly(asset, correlations)
            if corr_anomaly:
                anomalies.append(corr_anomaly)

        return anomalies

    def _detect_price_anomaly(
        self,
        asset: str,
        prices: List[float],
    ) -> Optional[MarketAnomaly]:
        """Detect unusual price movements."""
        # Calculate returns
        returns = [
            (prices[i] - prices[i-1]) / prices[i-1]
            for i in range(1, len(prices))
            if prices[i-1] > 0
        ]

        if not returns:
            return None

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        std = math.sqrt(variance) if variance > 0 else 0.01

        # Check latest return
        latest_return = returns[-1] if returns else 0
        z_score = abs((latest_return - mean) / std) if std > 0 else 0

        if z_score > self.price_threshold:
            direction = "spike" if latest_return > 0 else "crash"
            severity = "high" if z_score > 4 else "medium" if z_score > 3.5 else "low"

            return MarketAnomaly(
                anomaly_type=f"price_{direction}",
                asset=asset,
                severity=severity,
                description=f"Unusual price {direction}: {latest_return*100:.1f}% move ({z_score:.1f} std devs)",
                metrics={
                    "return_percent": latest_return * 100,
                    "z_score": z_score,
                    "historical_std": std * 100,
                },
            )

        return None

    def _detect_volume_anomaly(
        self,
        asset: str,
        volumes: List[float],
    ) -> Optional[MarketAnomaly]:
        """Detect unusual volume."""
        mean_vol = sum(volumes[:-1]) / len(volumes[:-1])
        std_vol = math.sqrt(
            sum((v - mean_vol) ** 2 for v in volumes[:-1]) / len(volumes[:-1])
        ) if len(volumes) > 1 else mean_vol * 0.5

        latest_vol = volumes[-1]
        z_score = abs((latest_vol - mean_vol) / std_vol) if std_vol > 0 else 0

        if z_score > self.volume_threshold:
            severity = "high" if z_score > 4 else "medium" if z_score > 3.5 else "low"

            return MarketAnomaly(
                anomaly_type="volume_spike",
                asset=asset,
                severity=severity,
                description=f"Unusual volume: {latest_vol/mean_vol:.1f}x average ({z_score:.1f} std devs)",
                metrics={
                    "volume_ratio": latest_vol / mean_vol if mean_vol > 0 else 0,
                    "z_score": z_score,
                    "average_volume": mean_vol,
                },
            )

        return None

    def _detect_correlation_anomaly(
        self,
        asset: str,
        correlations: Dict[str, float],
    ) -> Optional[MarketAnomaly]:
        """Detect correlation breakdowns."""
        # Check for unusual correlation changes
        # This would typically compare current vs historical correlations

        # Example: BTC-ETH correlation breakdown
        if "BTC" in correlations and asset != "BTC":
            btc_corr = correlations["BTC"]
            if abs(btc_corr) < 0.3:  # Historically high correlation broken
                return MarketAnomaly(
                    anomaly_type="correlation_breakdown",
                    asset=asset,
                    severity="medium",
                    description=f"Unusual decoupling from BTC (corr: {btc_corr:.2f})",
                    metrics={
                        "btc_correlation": btc_corr,
                    },
                )

        return None


class NaturalLanguageReporter:
    """
    Generates natural language reports from portfolio data.

    Creates human-readable summaries, insights, and recommendations.
    """

    def generate_portfolio_summary(
        self,
        portfolio_value: float,
        holdings: Dict[str, Dict],
        performance: Dict[str, float],
        predictions: Optional[List[PricePrediction]] = None,
        sentiment: Optional[Dict[str, SentimentAnalysis]] = None,
    ) -> str:
        """
        Generate a natural language portfolio summary.

        Args:
            portfolio_value: Total portfolio value in USD
            holdings: Dict of holdings with amounts and values
            performance: Performance metrics
            predictions: Optional price predictions
            sentiment: Optional sentiment analysis results

        Returns:
            Human-readable portfolio summary
        """
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append("PORTFOLIO SUMMARY REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        # Portfolio Value
        lines.append(f"📊 Total Portfolio Value: ${portfolio_value:,.2f}")
        lines.append("")

        # Performance Summary
        daily_change = performance.get("daily_change_pct", 0)
        weekly_change = performance.get("weekly_change_pct", 0)
        monthly_change = performance.get("monthly_change_pct", 0)

        daily_emoji = "📈" if daily_change >= 0 else "📉"
        lines.append("Performance:")
        lines.append(f"  {daily_emoji} 24h: {daily_change:+.2f}%")
        lines.append(f"  {'📈' if weekly_change >= 0 else '📉'} 7d:  {weekly_change:+.2f}%")
        lines.append(f"  {'📈' if monthly_change >= 0 else '📉'} 30d: {monthly_change:+.2f}%")
        lines.append("")

        # Top Holdings
        lines.append("Top Holdings:")
        sorted_holdings = sorted(
            holdings.items(),
            key=lambda x: x[1].get("value_usd", 0),
            reverse=True
        )

        for asset, data in sorted_holdings[:5]:
            value = data.get("value_usd", 0)
            weight = (value / portfolio_value * 100) if portfolio_value > 0 else 0
            pnl = data.get("unrealized_pnl_pct", 0)
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"

            lines.append(f"  • {asset}: ${value:,.2f} ({weight:.1f}%) {pnl_emoji} {pnl:+.1f}%")

        lines.append("")

        # AI Insights
        if predictions or sentiment:
            lines.append("AI Insights:")

            if predictions:
                bullish_count = sum(1 for p in predictions if p.predicted_change_24h > 0)
                lines.append(f"  • Price Outlook: {bullish_count}/{len(predictions)} assets bullish 24h")

            if sentiment:
                avg_sentiment = sum(
                    s.composite_score for s in sentiment.values()
                ) / len(sentiment) if sentiment else 0

                if avg_sentiment > 0.3:
                    lines.append("  • Market Sentiment: Bullish 🟢")
                elif avg_sentiment < -0.3:
                    lines.append("  • Market Sentiment: Bearish 🔴")
                else:
                    lines.append("  • Market Sentiment: Neutral 🟡")

            lines.append("")

        # Recommendations
        lines.append("Quick Actions:")
        if daily_change < -5:
            lines.append("  ⚠️ Significant daily drop - review positions")
        if monthly_change > 30:
            lines.append("  💡 Consider taking some profits")
        if len([h for h in holdings.values() if h.get("weight", 0) > 0.4]) > 0:
            lines.append("  ⚖️ Portfolio may need rebalancing - single asset > 40%")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_trade_recommendation(
        self,
        asset: str,
        current_price: float,
        prediction: PricePrediction,
        sentiment: SentimentAnalysis,
        current_holding: float,
    ) -> str:
        """Generate a trade recommendation narrative."""
        lines = []

        lines.append(f"Trade Analysis: {asset}")
        lines.append("-" * 40)
        lines.append(f"Current Price: ${current_price:,.2f}")
        lines.append(f"Current Holding: ${current_holding:,.2f}")
        lines.append("")

        # Price prediction
        lines.append("Price Outlook:")
        lines.append(f"  24h Prediction: ${prediction.predicted_price_24h:,.2f} ({prediction.predicted_change_24h:+.1f}%)")
        lines.append(f"  7d Prediction:  ${prediction.predicted_price_7d:,.2f} ({prediction.predicted_change_7d:+.1f}%)")
        lines.append(f"  Confidence: {prediction.confidence*100:.0f}%")
        lines.append("")

        # Sentiment
        lines.append("Sentiment Analysis:")
        lines.append(f"  Overall: {sentiment.overall_score.name}")
        lines.append(f"  Social: {sentiment.social_score:+.2f}")
        lines.append(f"  News: {sentiment.news_score:+.2f}")
        if sentiment.key_topics:
            lines.append(f"  Topics: {', '.join(sentiment.key_topics)}")
        lines.append("")

        # Recommendation
        lines.append("Recommendation:")
        if prediction.predicted_change_7d > 5 and sentiment.overall_score.value >= 1:
            lines.append("  📈 BULLISH - Consider accumulating")
        elif prediction.predicted_change_7d < -5 and sentiment.overall_score.value <= -1:
            lines.append("  📉 BEARISH - Consider reducing exposure")
        else:
            lines.append("  ➡️ NEUTRAL - Hold current position")

        return "\n".join(lines)

    def generate_anomaly_alert(self, anomalies: List[MarketAnomaly]) -> str:
        """Generate alert message for detected anomalies."""
        if not anomalies:
            return "No market anomalies detected."

        lines = ["⚠️ MARKET ANOMALY ALERT ⚠️", ""]

        for anomaly in anomalies:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            emoji = severity_emoji.get(anomaly.severity, "⚪")

            lines.append(f"{emoji} [{anomaly.severity.upper()}] {anomaly.asset}")
            lines.append(f"   Type: {anomaly.anomaly_type}")
            lines.append(f"   {anomaly.description}")
            lines.append("")

        return "\n".join(lines)


# Convenience functions for MCP integration

async def get_price_predictions(
    assets: List[str],
    price_history: Dict[str, List[float]],
) -> List[PricePrediction]:
    """Get price predictions for multiple assets."""
    predictor = SimplePricePredictor()
    predictions = []

    for asset in assets:
        if asset not in price_history or len(price_history[asset]) < 30:
            continue

        prices = price_history[asset]
        current = prices[-1]

        p_24h, p_7d, p_30d, confidence = predictor.predict(prices)

        predictions.append(PricePrediction(
            asset=asset,
            current_price=current,
            predicted_price_24h=p_24h,
            predicted_price_7d=p_7d,
            predicted_price_30d=p_30d,
            confidence=confidence,
            model_used=predictor.model_name,
        ))

    return predictions


async def analyze_market_sentiment(
    assets: List[str],
    news_by_asset: Optional[Dict[str, List[str]]] = None,
    social_by_asset: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, SentimentAnalysis]:
    """Analyze sentiment for multiple assets."""
    analyzer = SentimentAnalyzer()
    results = {}

    for asset in assets:
        news = (news_by_asset or {}).get(asset, [])
        social = (social_by_asset or {}).get(asset, [])

        results[asset] = await analyzer.analyze(asset, news, social)

    return results


async def detect_market_anomalies(
    market_data: Dict[str, Dict],  # asset -> {prices: [], volumes: []}
) -> List[MarketAnomaly]:
    """Detect anomalies across market data."""
    detector = AnomalyDetector()
    all_anomalies = []

    for asset, data in market_data.items():
        anomalies = detector.detect_anomalies(
            asset,
            data.get("prices", []),
            data.get("volumes"),
        )
        all_anomalies.extend(anomalies)

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_anomalies.sort(key=lambda x: severity_order.get(x.severity, 3))

    return all_anomalies
