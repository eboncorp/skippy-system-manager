"""
Market intelligence agent.

Gathers and analyzes market data including:
- On-chain metrics (active addresses, transaction volume)
- Exchange flows (inflows/outflows)
- Whale movements
- Fear & Greed Index
- Funding rates
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
import aiohttp

from config import settings


@dataclass
class MarketMetric:
    """A market metric data point."""
    name: str
    value: float
    timestamp: datetime
    change_24h: Optional[float] = None
    signal: str = "neutral"  # bullish, bearish, neutral
    source: str = ""


@dataclass
class WhaleAlert:
    """A large transaction alert."""
    asset: str
    amount: Decimal
    usd_value: Decimal
    from_address: str
    to_address: str
    timestamp: datetime
    tx_hash: str
    flow_type: str  # exchange_inflow, exchange_outflow, whale_transfer


@dataclass
class MarketOverview:
    """Complete market overview."""
    timestamp: datetime
    fear_greed_index: int
    fear_greed_label: str
    btc_dominance: float
    total_market_cap: float
    total_volume_24h: float
    metrics: List[MarketMetric]
    whale_alerts: List[WhaleAlert]


class MarketIntelAgent:
    """Agent for gathering market intelligence."""

    COINGECKO_URL = "https://api.coingecko.com/api/v3"
    ALTERNATIVE_ME_URL = "https://api.alternative.me"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self.coingecko_api_key = settings.market_data.coingecko_api_key

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """Get the Fear & Greed Index."""
        session = await self._get_session()

        url = f"{self.ALTERNATIVE_ME_URL}/fng/"

        try:
            async with session.get(url) as resp:
                data = await resp.json()

                if data.get("data"):
                    latest = data["data"][0]
                    return {
                        "value": int(latest["value"]),
                        "label": latest["value_classification"],
                        "timestamp": datetime.fromtimestamp(int(latest["timestamp"])),
                    }
        except Exception as e:
            print(f"Failed to get Fear & Greed Index: {e}")

        return {"value": 50, "label": "Neutral", "timestamp": datetime.now()}

    async def get_global_metrics(self) -> Dict[str, Any]:
        """Get global market metrics from CoinGecko."""
        session = await self._get_session()

        headers = {}
        if self.coingecko_api_key:
            headers["x-cg-demo-api-key"] = self.coingecko_api_key

        url = f"{self.COINGECKO_URL}/global"

        try:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()

                global_data = data.get("data", {})

                return {
                    "total_market_cap": global_data.get("total_market_cap", {}).get("usd", 0),
                    "total_volume_24h": global_data.get("total_volume", {}).get("usd", 0),
                    "btc_dominance": global_data.get("market_cap_percentage", {}).get("btc", 0),
                    "eth_dominance": global_data.get("market_cap_percentage", {}).get("eth", 0),
                    "market_cap_change_24h": global_data.get("market_cap_change_percentage_24h_usd", 0),
                    "active_cryptocurrencies": global_data.get("active_cryptocurrencies", 0),
                }
        except Exception as e:
            print(f"Failed to get global metrics: {e}")

        return {}

    async def get_trending_coins(self) -> List[Dict[str, Any]]:
        """Get trending coins from CoinGecko."""
        session = await self._get_session()

        headers = {}
        if self.coingecko_api_key:
            headers["x-cg-demo-api-key"] = self.coingecko_api_key

        url = f"{self.COINGECKO_URL}/search/trending"

        try:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()

                coins = []
                for item in data.get("coins", [])[:10]:
                    coin = item.get("item", {})
                    coins.append({
                        "symbol": coin.get("symbol", "").upper(),
                        "name": coin.get("name", ""),
                        "market_cap_rank": coin.get("market_cap_rank"),
                        "price_btc": coin.get("price_btc", 0),
                    })

                return coins
        except Exception as e:
            print(f"Failed to get trending coins: {e}")

        return []

    async def get_asset_metrics(self, asset: str) -> Dict[str, Any]:
        """Get detailed metrics for a specific asset."""
        session = await self._get_session()

        headers = {}
        if self.coingecko_api_key:
            headers["x-cg-demo-api-key"] = self.coingecko_api_key

        # Map common symbols to CoinGecko IDs
        symbol_to_id = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "DOT": "polkadot",
            "AVAX": "avalanche-2",
            "ATOM": "cosmos",
            "ADA": "cardano",
            "NEAR": "near",
            "SUI": "sui",
        }

        coin_id = symbol_to_id.get(asset.upper(), asset.lower())
        url = f"{self.COINGECKO_URL}/coins/{coin_id}"

        try:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()

                market_data = data.get("market_data", {})

                return {
                    "symbol": asset.upper(),
                    "name": data.get("name"),
                    "price_usd": market_data.get("current_price", {}).get("usd", 0),
                    "price_change_24h": market_data.get("price_change_percentage_24h", 0),
                    "price_change_7d": market_data.get("price_change_percentage_7d", 0),
                    "price_change_30d": market_data.get("price_change_percentage_30d", 0),
                    "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                    "market_cap_rank": data.get("market_cap_rank"),
                    "volume_24h": market_data.get("total_volume", {}).get("usd", 0),
                    "ath": market_data.get("ath", {}).get("usd", 0),
                    "ath_change": market_data.get("ath_change_percentage", {}).get("usd", 0),
                    "ath_date": market_data.get("ath_date", {}).get("usd"),
                    "atl": market_data.get("atl", {}).get("usd", 0),
                    "circulating_supply": market_data.get("circulating_supply", 0),
                    "total_supply": market_data.get("total_supply", 0),
                    "max_supply": market_data.get("max_supply"),
                }
        except Exception as e:
            print(f"Failed to get metrics for {asset}: {e}")

        return {}

    async def get_market_overview(
        self,
        assets: Optional[List[str]] = None,
    ) -> MarketOverview:
        """Get complete market overview."""
        # Gather all data concurrently
        fear_greed_task = self.get_fear_greed_index()
        global_task = self.get_global_metrics()
        trending_task = self.get_trending_coins()

        results = await asyncio.gather(
            fear_greed_task,
            global_task,
            trending_task,
            return_exceptions=True,
        )

        fear_greed = results[0] if not isinstance(results[0], Exception) else {"value": 50, "label": "Neutral"}
        global_metrics = results[1] if not isinstance(results[1], Exception) else {}
        # trending = results[2] if not isinstance(results[2], Exception) else []

        # Create metrics list
        metrics = []

        if global_metrics:
            metrics.append(MarketMetric(
                name="Total Market Cap",
                value=global_metrics.get("total_market_cap", 0),
                timestamp=datetime.now(),
                change_24h=global_metrics.get("market_cap_change_24h"),
                signal="bullish" if global_metrics.get("market_cap_change_24h", 0) > 0 else "bearish",
                source="coingecko",
            ))

            metrics.append(MarketMetric(
                name="BTC Dominance",
                value=global_metrics.get("btc_dominance", 0),
                timestamp=datetime.now(),
                source="coingecko",
            ))

        # Get metrics for specified assets
        if assets:
            asset_tasks = [self.get_asset_metrics(asset) for asset in assets[:5]]  # Limit to 5
            asset_results = await asyncio.gather(*asset_tasks, return_exceptions=True)

            for asset, result in zip(assets[:5], asset_results):
                if isinstance(result, dict) and result:
                    change_24h = result.get("price_change_24h", 0)
                    metrics.append(MarketMetric(
                        name=f"{asset} Price",
                        value=result.get("price_usd", 0),
                        timestamp=datetime.now(),
                        change_24h=change_24h,
                        signal="bullish" if change_24h > 2 else "bearish" if change_24h < -2 else "neutral",
                        source="coingecko",
                    ))

        return MarketOverview(
            timestamp=datetime.now(),
            fear_greed_index=fear_greed.get("value", 50),
            fear_greed_label=fear_greed.get("label", "Neutral"),
            btc_dominance=global_metrics.get("btc_dominance", 0),
            total_market_cap=global_metrics.get("total_market_cap", 0),
            total_volume_24h=global_metrics.get("total_volume_24h", 0),
            metrics=metrics,
            whale_alerts=[],  # Would need a separate service for whale tracking
        )

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()

    def format_overview(self, overview: MarketOverview) -> str:
        """Format market overview for display."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"Market Overview - {overview.timestamp.strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)

        # Fear & Greed
        fg_emoji = "😱" if overview.fear_greed_index < 25 else "😰" if overview.fear_greed_index < 45 else "😐" if overview.fear_greed_index < 55 else "😊" if overview.fear_greed_index < 75 else "🤑"
        lines.append(f"\n{fg_emoji} Fear & Greed Index: {overview.fear_greed_index} ({overview.fear_greed_label})")

        # Global metrics
        lines.append("\n📊 Global Metrics:")
        lines.append(f"   Total Market Cap: ${overview.total_market_cap/1e12:.2f}T")
        lines.append(f"   24h Volume: ${overview.total_volume_24h/1e9:.1f}B")
        lines.append(f"   BTC Dominance: {overview.btc_dominance:.1f}%")

        # Asset metrics
        if overview.metrics:
            lines.append("\n📈 Asset Metrics:")
            for metric in overview.metrics:
                if "Price" in metric.name:
                    signal_emoji = "🟢" if metric.signal == "bullish" else "🔴" if metric.signal == "bearish" else "⚪"
                    change_str = f"({metric.change_24h:+.1f}%)" if metric.change_24h else ""
                    lines.append(f"   {signal_emoji} {metric.name}: ${metric.value:,.2f} {change_str}")

        return "\n".join(lines)


# Convenience function
async def get_market_overview(assets: Optional[List[str]] = None) -> MarketOverview:
    """Quick function to get market overview."""
    agent = MarketIntelAgent()
    try:
        return await agent.get_market_overview(assets)
    finally:
        await agent.close()
